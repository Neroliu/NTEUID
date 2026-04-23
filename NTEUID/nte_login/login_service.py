from __future__ import annotations

import asyncio
import hashlib
from typing import List, Tuple, Optional, TypedDict
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from gsuid_core.bot import Bot
from gsuid_core.config import core_config
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.cookie_manager.qrlogin import get_qrcode_base64

from ..utils.msgs import LoginMsg, send_nte_notify
from ..utils.cache import TimedCache
from ..utils.utils import get_public_ip
from ..utils.database import NTEUser
from ..utils.constants import LAOHU_APP_ID, LAOHU_APP_KEY, GAME_ID_YIHUAN
from ..utils.sdk.laohu import LaohuClient, LaohuDevice
from ..utils.sdk.tajiduo import TajiduoClient
from ..nte_config.nte_config import NTEConfig
from ..utils.sdk.tajiduo_model import GameRoleList, TajiduoError

LOGIN_CACHE: TimedCache = TimedCache(timeout=600, maxsize=32)
LOGIN_WAIT_SECONDS = 600
LOGIN_POLL_INTERVAL = 2.0


class _LoginFields(TypedDict):
    """`perform_login` 落库时 upsert 的账号级字段（同 center_uid 的多角色共享这些值）。"""

    dev_code: str
    cookie: str
    access_token: str
    access_token_updated_at: datetime
    laohu_token: str
    laohu_user_id: str


@dataclass
class LoginState:
    user_id: str
    bot_id: str
    group_id: Optional[str]
    device: LaohuDevice
    status: str = "pending"  # pending | success | failed
    ok: bool = False
    roles: Tuple[Tuple[str, str], ...] = ()  # ((role_id, role_name), ...)
    msg: Optional[str] = None


@dataclass
class LoginResult:
    ok: bool
    msg: str = ""
    uid: str = ""

    @classmethod
    def fail(cls, msg: str) -> "LoginResult":
        return cls(ok=False, msg=msg)

    @classmethod
    def success(cls, uid: str = "", msg: str = "") -> "LoginResult":
        return cls(ok=True, uid=uid, msg=msg)


async def _login_page_url() -> str:
    url = NTEConfig.get_config("NTELoginUrl").data.strip()
    if url:
        return url if url.startswith("http") else f"https://{url}"

    host = core_config.get_config("HOST")
    port = core_config.get_config("PORT")
    if host in {"localhost", "127.0.0.1"}:
        host = "localhost"
    else:
        host = await get_public_ip(host)
    return f"http://{host}:{port}"


async def request_login(bot: Bot, ev: Event) -> None:
    auth_token = _auth_token(ev.user_id)
    login_url = f"{await _login_page_url()}/nte/i/{auth_token}"
    await _send_login_link(bot, ev, login_url)

    # 已有进行中的登录：复用同一个链接，不另开 wait 循环
    if LOGIN_CACHE.get(auth_token):
        return

    LOGIN_CACHE.set(auth_token, LoginState(
        user_id=ev.user_id,
        bot_id=ev.bot_id,
        group_id=ev.group_id,
        device=LaohuDevice(),
    ))

    result = await _wait(auth_token)
    if not result:
        return await send_nte_notify(bot, ev, LoginMsg.TIMEOUT)
    if not result.ok:
        if result.msg is None:
            raise RuntimeError("登录失败状态缺少用户提示")
        return await send_nte_notify(bot, ev, result.msg)
    await send_nte_notify(bot, ev, _format_login_success(result.roles))


def _format_login_success(roles: Tuple[Tuple[str, str], ...]) -> str:
    if not roles:
        return LoginMsg.SUCCESS_NO_ROLE
    lines = [LoginMsg.SUCCESS_ROLES_TITLE]
    lines.extend(f"· {name}（{uid}）" for uid, name in roles)
    return "\n".join(lines)


def _auth_token(user_id: str) -> str:
    """按 user_id 生成稳定的登录 token，同一个 QQ 永远映射到同一个登录页。"""
    return hashlib.sha256(user_id.encode()).hexdigest()[:8]


async def send_login_sms(auth_token: str, mobile: str) -> LoginResult:
    state: Optional[LoginState] = LOGIN_CACHE.get(auth_token)
    if not state:
        return LoginResult.fail(LoginMsg.SESSION_EXPIRED)
    await LaohuClient(LAOHU_APP_ID, LAOHU_APP_KEY, device=state.device).send_sms_code(mobile)
    return LoginResult.success(msg=LoginMsg.SMS_SENT)


async def perform_login(auth_token: str, mobile: str, code: str) -> LoginResult:
    state: Optional[LoginState] = LOGIN_CACHE.get(auth_token)
    if not state:
        return LoginResult.fail(LoginMsg.SESSION_EXPIRED)

    laohu = LaohuClient(LAOHU_APP_ID, LAOHU_APP_KEY, device=state.device)
    account = await laohu.login_by_sms(mobile, code)
    tajiduo = TajiduoClient(device_id=state.device.device_id)
    tj_session = await tajiduo.user_center_login(account.token, str(account.user_id))
    roles = await _collect_roles(tajiduo, GAME_ID_YIHUAN)

    await _persist(
        user_id=state.user_id,
        bot_id=state.bot_id,
        center_uid=tj_session.center_uid,
        game_id=GAME_ID_YIHUAN,
        roles=roles,
        fields={
            "dev_code": state.device.device_id,
            "cookie": tj_session.refresh_token,
            "access_token": tj_session.access_token,
            "access_token_updated_at": datetime.now(),
            "laohu_token": account.token,
            "laohu_user_id": str(account.user_id),
        },
    )

    state.status = "success"
    state.roles = tuple((rid, name) for rid, name, _ in roles)
    state.ok = True
    LOGIN_CACHE.set(auth_token, state)
    logger.info(
        f"[NTE登录] user_id={state.user_id} center_uid={tj_session.center_uid} "
        f"roles={[rid for rid, _, _ in roles]} 登录完成"
    )
    primary_uid = roles[0][0] if roles else ""
    return LoginResult.success(uid=primary_uid)


async def _collect_roles(tajiduo: TajiduoClient, game_id: str) -> List[Tuple[str, str, str]]:
    """get_bind_role + get_game_roles 双路合并，按 roleId 去重，主绑定排第一。

    返回 (role_id, role_name, game_id) 三元组。game_id 由查询参数兜定——查的是什么游戏，
    落盘就是什么游戏，不依赖 API 返回体的 gameId 字段（存在性不稳定）。
    """
    collected: List[Tuple[str, str, str]] = []
    seen: set[str] = set()

    bind = await tajiduo.get_bind_role(game_id)
    if bind.uid:
        collected.append((bind.uid, bind.role_name.strip(), game_id))
        seen.add(bind.uid)

    extras = await tajiduo.get_game_roles(game_id)
    for item in extras.roles:
        if item.uid and item.uid not in seen:
            collected.append((item.uid, item.role_name.strip(), game_id))
            seen.add(item.uid)

    await _ensure_bind_role(tajiduo, game_id, extras)
    return collected


async def _ensure_bind_role(tajiduo: TajiduoClient, game_id: str, roles: GameRoleList) -> None:
    """账号下还没设主绑定角色时自动绑第一个——为了顺手拿 `bind_role` 成就任务 70 金币。
    绑定失败不阻塞登录；下次登录还会再试一次。"""
    if roles.bind_role_id != 0 or not roles.roles:
        return
    first_role_id = roles.roles[0].uid
    if not first_role_id:
        return
    try:
        await tajiduo.bind_game_role(game_id, first_role_id)
    except TajiduoError as error:
        logger.warning(f"[NTE登录] 自动绑定主角色失败 roleId={first_role_id}: {error.message}")
        return
    logger.info(f"[NTE登录] 自动绑定主角色 roleId={first_role_id}")


async def _send_login_link(bot: Bot, ev: Event, url: str) -> None:
    at_sender = bool(ev.group_id)
    forward = bool(NTEConfig.get_config("NTELoginForward").data)
    private_onebot = not ev.group_id and ev.bot_id == "onebot"

    if NTEConfig.get_config("NTEQRLogin").data:
        path = Path(__file__).parent / f"{ev.user_id}.gif"
        im = [
            f"[异环] 您的id为【{ev.user_id}】\n",
            LoginMsg.LINK_QR,
            MessageSegment.image(await get_qrcode_base64(url, path, ev.bot_id)),
        ]
        try:
            if forward and not private_onebot:
                await bot.send(MessageSegment.node(im))
            elif forward:
                await bot.send(im)
            else:
                await bot.send(im, at_sender=at_sender)
        finally:
            if path.exists():
                path.unlink()
        return

    if NTEConfig.get_config("NTETencentWord").data:
        url = f"https://docs.qq.com/scenario/link.html?url={url}"
    lines = [
        f"[异环] 您的id为【{ev.user_id}】",
        LoginMsg.LINK_COPY,
        f" {url}",
        LoginMsg.LINK_TTL,
    ]
    if forward and not private_onebot:
        await bot.send(MessageSegment.node(lines))
    else:
        await bot.send("\n".join(lines), at_sender=at_sender)


async def _wait(auth_token: str) -> Optional[LoginState]:
    waited = 0.0
    while waited < LOGIN_WAIT_SECONDS:
        state: Optional[LoginState] = LOGIN_CACHE.get(auth_token)
        if not state:
            return None
        if state.status in {"success", "failed"}:
            LOGIN_CACHE.pop(auth_token)
            return state
        await asyncio.sleep(LOGIN_POLL_INTERVAL)
        waited += LOGIN_POLL_INTERVAL
    LOGIN_CACHE.pop(auth_token)
    return None


async def refresh_all_user_tokens(user_id: str, bot_id: str) -> List[Tuple[str, bool, str]]:
    """按 center_uid 去重后，对每个账号各刷新一次 session。
    返回 [(center_uid, success, reason)]。reason 只在失败时有值。"""
    users = await NTEUser.list_latest_per_account(user_id, bot_id)
    logger.info(f"[NTE刷新令牌] user_id={user_id} bot_id={bot_id} 取到 {len(users)} 个账号")
    results: List[Tuple[str, bool, str]] = []
    for user in users:
        if not user.laohu_token or not user.laohu_user_id:
            results.append((user.center_uid, False, "登录信息不完整"))
            continue
        ok = await refresh_user_token(user)
        results.append((user.center_uid, ok, "" if ok else "凭证已失效"))
    return results


async def refresh_user_token(user: NTEUser) -> bool:
    """用库里存着的 laohu_token + laohu_user_id 直接重新走 user_center_login，
    拿一对全新 access_token / refresh_token 写回 DB。返回 True = 成功刷新。

    适用场景：refresh_token 死了（HTTP 402）但 laohu_token 还活着时，
    不用再发短信验证码就能把会话"续命"。注意：会把服务端同 center_uid 的
    其它活跃会话（比如手机 APP 那端）顶掉。"""
    if not user.laohu_token or not user.laohu_user_id:
        return False

    tajiduo = TajiduoClient(device_id=user.dev_code)
    try:
        session = await tajiduo.user_center_login(user.laohu_token, user.laohu_user_id)
    except TajiduoError as error:
        logger.warning(f"[NTE刷新令牌] 账号 {user.center_uid} 重新登录失败: {error.message}")
        return False

    await NTEUser.update_tokens(
        center_uid=session.center_uid,
        refresh_token=session.refresh_token,
        access_token=session.access_token,
    )
    logger.info(f"[NTE刷新令牌] 账号 {session.center_uid} 已刷新")
    return True


def mark_login_failed(auth_token: str, msg: str) -> None:
    state: Optional[LoginState] = LOGIN_CACHE.get(auth_token)
    if not state:
        return
    state.status = "failed"
    state.ok = False
    state.msg = msg
    LOGIN_CACHE.set(auth_token, state)


async def _persist(
    *,
    user_id: str,
    bot_id: str,
    center_uid: str,
    game_id: str,
    roles: List[Tuple[str, str, str]],
    fields: _LoginFields,
) -> None:
    """为每个角色 upsert 一行；没有任何角色时写一行占位（uid=""）。

    登录拉到真角色后会清掉同账号的占位行——避免「先登录(无角色) → 再登录(有角色)」
    后库里留一条僵尸占位。
    """
    entries: List[Tuple[str, str, str]] = roles if roles else [("", "", game_id)]
    shared = {**fields, "center_uid": center_uid, "status": ""}

    for role_uid, role_name, role_game_id in entries:
        row_data = {**shared, "uid": role_uid, "role_name": role_name, "game_id": role_game_id}
        if await NTEUser.get_row(user_id, bot_id, center_uid, role_uid):
            await NTEUser.update_data_by_data(
                select_data={
                    "user_id": user_id, "bot_id": bot_id,
                    "center_uid": center_uid, "uid": role_uid,
                },
                update_data=row_data,
            )
        else:
            await NTEUser.insert_data(user_id=user_id, bot_id=bot_id, **row_data)

    if roles:
        await NTEUser.delete_placeholders(user_id, bot_id, center_uid)
