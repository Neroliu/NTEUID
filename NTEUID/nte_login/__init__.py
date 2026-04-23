from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from . import login_router
from ..utils.msgs import LoginMsg, send_nte_notify
from .login_service import request_login, refresh_all_user_tokens
from ..utils.database import NTEUser

_ = login_router  # 纯副作用 import：FastAPI 路由在模块加载时注册

sv_nte_login = SV("nte登录")


@sv_nte_login.on_fullmatch(("登录", "login"))
async def nte_login_cmd(bot: Bot, ev: Event):
    await request_login(bot, ev)


@sv_nte_login.on_fullmatch(("退出登录", "登出", "logout"))
async def nte_logout_cmd(bot: Bot, ev: Event):
    deleted = await NTEUser.delete_all(ev.user_id, ev.bot_id)
    if not deleted:
        return await send_nte_notify(bot, ev, LoginMsg.NOT_LOGGED_IN)
    await send_nte_notify(bot, ev, LoginMsg.LOGOUT_DONE)


@sv_nte_login.on_fullmatch(("刷新令牌", "刷新token", "续签"))
async def nte_refresh_token_cmd(bot: Bot, ev: Event):
    results = await refresh_all_user_tokens(ev.user_id, ev.bot_id)
    if not results:
        return await send_nte_notify(bot, ev, LoginMsg.REFRESH_NO_ACCOUNT)
    ok = sum(1 for _, success, _ in results if success)
    lines = [f"已刷新 {ok} / {len(results)} 个塔吉多账号"]
    for center_uid, success, reason in results:
        mark = "✅" if success else "❌"
        line = f"  · {mark} {center_uid}"
        if reason:
            line += f"（{reason}）"
        lines.append(line)
    await send_nte_notify(bot, ev, "\n".join(lines))
