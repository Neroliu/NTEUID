import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .resource.RESOURCE_PATH import ROLE_META_PATH


class RoleMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = ""
    aliases: list[str] = []
    avatar: str = ""


role_alias_data: dict[str, list[str]] = {}
role_id_to_name_data: dict[str, str] = {}
role_id_to_avatar_data: dict[str, str] = {}


def _load_meta(path: Path) -> dict[str, RoleMeta]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(role_id): RoleMeta.model_validate(entry) for role_id, entry in raw.items() if isinstance(entry, dict)}


def load_role_meta() -> None:
    global role_alias_data, role_id_to_name_data, role_id_to_avatar_data

    role_alias_data = {}
    role_id_to_name_data = {}
    role_id_to_avatar_data = {}

    for role_id, meta in _load_meta(ROLE_META_PATH).items():
        if not meta.name:
            continue

        role_id_to_name_data[role_id] = meta.name
        if meta.avatar:
            role_id_to_avatar_data[role_id] = meta.avatar

        aliases: list[str] = []
        for alias in [*meta.aliases, meta.name]:
            if not alias or alias.isdigit() or alias in aliases:
                continue
            aliases.append(alias)
        if meta.name not in role_alias_data:
            role_alias_data[meta.name] = aliases


load_role_meta()


def alias_to_role_name(role_name: str | None) -> str | None:
    if not role_name:
        return None
    for name, aliases in role_alias_data.items():
        if role_name in name or role_name in aliases:
            return name
    return None


def alias_to_role_name_list(role_name: str) -> list[str]:
    for name, aliases in role_alias_data.items():
        if role_name in name or role_name in aliases:
            return aliases
    return []


def role_name_to_role_id(role_name: str | None) -> str | None:
    role_name = alias_to_role_name(role_name)
    if not role_name:
        return None
    for role_id, name in role_id_to_name_data.items():
        if name == role_name:
            return role_id
    return None


def alias_to_role_id(role_name: str | None) -> str:
    return role_name_to_role_id(role_name) or ""


def role_id_to_avatar_url(role_id: str) -> str:
    return role_id_to_avatar_data.get(role_id, "")
