from __future__ import annotations

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.msgs import GachaMsg, CommonMsg, send_nte_notify
from .tap_service import send_tap_summary, _normalize_tap_id
from .xhh_service import send_xhh_summary
from ..utils.database import NTEUser
from ..nte_config.nte_config import NTEConfig


async def run_my_gacha(bot: Bot, ev: Event, arg: str = "") -> None:
    arg = arg.strip()
    if arg and bool(NTEConfig.get_config("NTEGachaUnsafeQuery").data):
        tap_id = _normalize_tap_id(arg)
        if tap_id is None:
            return await send_nte_notify(bot, ev, GachaMsg.INVALID_TAP_ID)
        return await send_tap_summary(bot, ev, tap_id=tap_id, fallback_role_name="")

    user = await NTEUser.get_active(ev.user_id, ev.bot_id)
    if user is None:
        has_history = await NTEUser.has_logged_in_history(ev.user_id, ev.bot_id)
        return await send_nte_notify(bot, ev, CommonMsg.not_logged_in(has_history=has_history))

    # 优先 TapTap
    if user.tap_id:
        tap_id = _normalize_tap_id(user.tap_id)
        if tap_id is not None:
            return await send_tap_summary(bot, ev, tap_id=tap_id, fallback_role_name=user.role_name)
        logger.warning(f"[NTE抽卡] DB 中 tap_id 非数字 user_id={ev.user_id} tap_id={user.tap_id!r}")

    # fallback 小黑盒
    if user.xhh_pkey:
        return await send_xhh_summary(bot, ev, user)

    return await send_nte_notify(bot, ev, GachaMsg.bind_required())
