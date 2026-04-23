from __future__ import annotations

from ..utils.image import (
    COLOR_BLUE,
    COLOR_GRAY,
    COLOR_GREEN,
    COLOR_ORANGE,
)

ELEMENT_META: dict[str, tuple[str, tuple[int, int, int]]] = {
    "CHARACTER_ELEMENT_TYPE_PSYCHE": ("魂", (180, 110, 220)),
    "CHARACTER_ELEMENT_TYPE_COSMOS": ("光", (245, 190, 80)),
    "CHARACTER_ELEMENT_TYPE_NATURE": ("灵", (95, 200, 150)),
    "CHARACTER_ELEMENT_TYPE_INCANTATION": ("咒", (110, 145, 220)),
    "CHARACTER_ELEMENT_TYPE_CHAOS": ("暗", (90, 90, 120)),
    "CHARACTER_ELEMENT_TYPE_LAKSHANA": ("相", (220, 110, 110)),
}

QUALITY_COLOR: dict[str, tuple[int, int, int]] = {
    "ITEM_QUALITY_ORANGE": COLOR_ORANGE,
    "ITEM_QUALITY_PURPLE": (160, 110, 220),
    "ITEM_QUALITY_BLUE": COLOR_BLUE,
    "ITEM_QUALITY_GREEN": COLOR_GREEN,
    "ITEM_QUALITY_WHITE": COLOR_GRAY,
}

QUALITY_RANK = {
    "ITEM_QUALITY_ORANGE": 4,
    "ITEM_QUALITY_PURPLE": 3,
    "ITEM_QUALITY_BLUE": 2,
    "ITEM_QUALITY_GREEN": 1,
    "ITEM_QUALITY_WHITE": 0,
}

QUALITY_LABEL = {
    "ITEM_QUALITY_ORANGE": "SSR",
    "ITEM_QUALITY_PURPLE": "SR",
    "ITEM_QUALITY_BLUE": "R",
    "ITEM_QUALITY_GREEN": "N",
    "ITEM_QUALITY_WHITE": "N",
}

SKILL_TYPE_LABEL = {
    "Proactive": "主动",
    "Passive": "被动",
    "City": "城市",
}
