from __future__ import annotations

import asyncio

from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.msgs import SignMsg, send_nte_notify
from ..utils.session import open_session, report_call_error
from .sign_calendar_card import draw_sign_calendar_img
from ..utils.sdk.tajiduo_model import TajiduoError

TAG = "签到日历"


async def run_sign_calendar(bot: Bot, ev: Event, game_id: str) -> None:
    session = await open_session(
        bot,
        ev,
        tag=TAG,
        not_logged_in_msg=SignMsg.not_logged_in(),
        login_expired_msg=SignMsg.login_expired(),
        game_id=game_id,
    )
    if session is None:
        return
    user, client = session

    try:
        state, rewards = await asyncio.gather(
            client.get_game_sign_state(game_id),
            client.get_game_sign_rewards(game_id),
        )
    except TajiduoError as error:
        return await report_call_error(
            bot,
            ev,
            user,
            error,
            tag=TAG,
            login_expired_msg=SignMsg.login_expired(),
            load_failed_msg=SignMsg.CALENDAR_LOAD_FAILED,
        )

    if not rewards:
        return await send_nte_notify(bot, ev, SignMsg.CALENDAR_EMPTY)

    await bot.send(await draw_sign_calendar_img(ev, state, rewards, user.role_name, user.uid, game_id))
