from __future__ import annotations

import json
from typing import Any
from pathlib import Path

import aiofiles

from gsuid_core.logger import logger

from ..utils.resource.RESOURCE_PATH import PLAYERINFO_PATH


def get_role_cache_path(role_id: str) -> Path:
    return PLAYERINFO_PATH / f"{role_id}.json"


async def save_role_characters_cache(role_id: str, payload: list[dict[str, Any]]) -> Path:
    path = get_role_cache_path(role_id)
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(json.dumps(payload, ensure_ascii=False, indent=2))
    return path


async def load_role_characters_cache(role_id: str) -> list[dict[str, Any]] | None:
    path = get_role_cache_path(role_id)
    if not path.exists():
        return None

    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as file:
            payload = json.loads(await file.read())
    except (OSError, json.JSONDecodeError) as error:
        logger.warning(f"[NTE角色详情] 读取角色缓存失败 {path}: {error!r}")
        return None

    if not isinstance(payload, list):
        return None
    return [item for item in payload if isinstance(item, dict)]
