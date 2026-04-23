from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.msgs import send_nte_notify
from ..utils.sdk.htnews import HtNewsError, ht_news

# 接口仍下发、但实测已失效的兑换码：直接在这里加 order 即可屏蔽
INVALID_CODES: tuple[str, ...] = ()

sv_nte_code = SV("nte兑换码")


@sv_nte_code.on_fullmatch(("兑换码", "code"))
async def nte_get_code(bot: Bot, ev: Event):
    try:
        items = await ht_news.fetch_code_list()
    except HtNewsError as err:
        logger.warning(f"[NTE兑换码] 拉取失败: {err.message}")
        return await send_nte_notify(bot, ev, "获取兑换码失败，请稍后再试")

    msgs = []
    for c in items:
        if c.is_fail == "1":
            continue
        if not c.order or c.order in INVALID_CODES:
            continue
        msgs.append("\n".join([f"兑换码: {c.order}", f"奖励: {c.reward}", c.label]))

    await bot.send(msgs)
