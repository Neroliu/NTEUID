from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .team_service import run_team
from ..utils.constants import COMMAND_NAME_PATTERN

sv_nte_team = SV("nte配队推荐")


@sv_nte_team.on_regex(
    rf"^(?P<char_name>{COMMAND_NAME_PATTERN})(配队推荐|配队)$",
    block=True,
)
async def nte_team_rec(bot: Bot, ev: Event):
    await run_team(bot, ev, ev.regex_dict["char_name"])
