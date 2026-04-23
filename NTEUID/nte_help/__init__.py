from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.help.utils import register_help

from ..utils.msgs import send_nte_notify
from ..nte_config.prefix import NTE_PREFIX

sv_nte_help = SV("nte帮助")


@sv_nte_help.on_fullmatch("帮助")
async def send_nte_help(bot: Bot, ev: Event):
    await send_nte_notify(bot, ev, "暂无帮助，请等待后续更新")


register_help("NTEUID", f"{NTE_PREFIX}帮助")
