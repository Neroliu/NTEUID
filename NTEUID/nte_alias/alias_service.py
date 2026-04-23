import json

from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.msgs import RoleMsg, send_nte_notify
from ..utils.name_convert import (
    load_role_meta,
    alias_to_role_name,
    role_name_to_role_id,
    alias_to_role_name_list,
)
from ..utils.resource.RESOURCE_PATH import ROLE_META_PATH


def _load_role_meta_json() -> dict[str, dict]:
    try:
        raw = json.loads(ROLE_META_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _save_role_meta_json(data: dict[str, dict]) -> None:
    ROLE_META_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


async def run_role_alias_action(
    bot: Bot,
    ev: Event,
    action: str,
    char_name: str,
    new_alias: str,
) -> None:
    if not char_name or not new_alias:
        return await send_nte_notify(bot, ev, "名称或别名不能为空")
    if new_alias.isdigit():
        return await send_nte_notify(bot, ev, "别名不能是纯数字")

    role_name = alias_to_role_name(char_name)
    if not role_name:
        return await send_nte_notify(bot, ev, f"角色【{char_name}】不存在，请检查名称")
    role_id = role_name_to_role_id(role_name)
    if not role_id:
        return await send_nte_notify(bot, ev, f"角色【{char_name}】不存在，请检查名称")

    data = _load_role_meta_json()
    role_meta = data.get(role_id)
    if not isinstance(role_meta, dict):
        return await send_nte_notify(bot, ev, f"角色【{char_name}】不存在，请检查名称")

    aliases_raw = role_meta.get("aliases", [])
    aliases = aliases_raw if isinstance(aliases_raw, list) else []
    check_new_alias = alias_to_role_name(new_alias)

    if action == "添加":
        if check_new_alias:
            return await send_nte_notify(
                bot,
                ev,
                f"别名【{new_alias}】已被角色【{check_new_alias}】占用",
            )

        aliases.append(new_alias)
        role_meta["aliases"] = aliases
        _save_role_meta_json(data)
        load_role_meta()
        return await send_nte_notify(
            bot,
            ev,
            f"成功为角色【{role_name}】添加别名【{new_alias}】",
        )

    if action == "删除":
        if new_alias not in aliases:
            return await send_nte_notify(
                bot,
                ev,
                f"别名【{new_alias}】不存在，无法删除",
            )

        aliases.remove(new_alias)
        role_meta["aliases"] = aliases
        _save_role_meta_json(data)
        load_role_meta()
        return await send_nte_notify(
            bot,
            ev,
            f"成功为角色【{role_name}】删除别名【{new_alias}】",
        )

    return await send_nte_notify(bot, ev, "无效的操作，请检查操作")


async def run_role_alias_list(bot: Bot, ev: Event, char_name: str) -> None:
    if not char_name:
        return await send_nte_notify(bot, ev, RoleMsg.USAGE_DETAIL)

    role_name = alias_to_role_name(char_name)
    if not role_name:
        return await send_nte_notify(bot, ev, RoleMsg.CHAR_NOT_FOUND)

    alias_list = alias_to_role_name_list(char_name)
    if not alias_list:
        return await send_nte_notify(bot, ev, RoleMsg.CHAR_NOT_FOUND)

    await send_nte_notify(
        bot,
        ev,
        f"角色【{role_name}】别名列表：\n" + "\n".join(alias_list),
    )
