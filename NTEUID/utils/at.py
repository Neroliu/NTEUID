from __future__ import annotations

from dataclasses import dataclass

from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .msgs import CommonMsg, send_nte_notify
from ..nte_config.nte_config import NTEConfig


@dataclass(frozen=True)
class AtTarget:
    user_id: str
    is_other: bool


def _at_other_user_id(ev: Event) -> str | None:
    """提取 @ 的真实他人 QQ；@ 自己 / @ Bot / 没 @ / @ 平台占位时返回 None。"""
    at = ev.at
    if not at:
        return None
    if at == ev.bot_id or at == ev.real_bot_id:
        return None
    if at == ev.user_id:
        return None
    return at


async def resolve_at_target(bot: Bot, ev: Event) -> AtTarget | None:
    """统一解析查询目标用户。

    - 没 @ / @ 自己 / @ Bot：返回 `AtTarget(ev.user_id, is_other=False)`。
    - @ 他人 + 配置开启：返回 `AtTarget(ev.at, is_other=True)`。
    - @ 他人 + 配置关闭：发送提示并返回 `None`，调用方直接 `return`。
    """
    other = _at_other_user_id(ev)
    if other is None:
        return AtTarget(user_id=ev.user_id, is_other=False)

    if not NTEConfig.get_config("NTEAllowAtQuery").data:
        await send_nte_notify(bot, ev, CommonMsg.AT_QUERY_DISABLED)
        return None
    return AtTarget(user_id=other, is_other=True)
