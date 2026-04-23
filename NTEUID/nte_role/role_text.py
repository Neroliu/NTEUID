from __future__ import annotations

from typing import TYPE_CHECKING

from .role_meta import ELEMENT_META, QUALITY_RANK, QUALITY_LABEL
from ..nte_config.prefix import NTE_PREFIX

if TYPE_CHECKING:
    from ..utils.sdk.tajiduo_model import (
        House,
        RoleHome,
        VehicleList,
        AreaProgress,
        CharacterDetail,
        AchievementProgress,
    )


_LIST_CAP = 10
_INDENT = "  "


def _cap_list(lines: list[str], total: int) -> list[str]:
    if total <= _LIST_CAP:
        return lines
    return [*lines[:_LIST_CAP], f"{_INDENT}...共 {total}"]


def format_role_home(home: "RoleHome") -> str:
    header = " · ".join(part for part in (home.role_name, home.server_name) if part)
    lines: list[str] = []
    if header:
        lines.append(header)
    lines.append(f"Lv{home.lev} · 世界 {home.world_level} · 大亨 {home.tycoon_level}")
    lines.append(f"登录 {home.role_login_days} 天 · 角色 {home.charid_cnt}")

    summary_parts: list[str] = []
    if home.achieve_progress is not None:
        summary_parts.append(f"成就 {home.achieve_progress.achievement_cnt}/{home.achieve_progress.total}")
    summary_parts.append(f"区域 {len(home.area_progress)}")
    if home.realestate is not None:
        summary_parts.append(f"房产 {home.realestate.total}")
    if home.vehicle is not None:
        summary_parts.append(f"载具 {home.vehicle.own_cnt}/{home.vehicle.total}")
    if summary_parts:
        lines.append(" · ".join(summary_parts))
    return "\n".join(lines)


def format_refresh_summary(characters: list["CharacterDetail"]) -> str:
    total = len(characters)
    lines = [f"已刷新 {total} 个角色"]
    if total:
        buckets: dict[str, int] = {}
        for character in characters:
            label = QUALITY_LABEL.get(character.quality, "其它")
            buckets[label] = buckets.get(label, 0) + 1
        ordered_keys = sorted(
            QUALITY_LABEL.keys(),
            key=lambda key: QUALITY_RANK.get(key, -1),
            reverse=True,
        )
        seen_labels: set[str] = set()
        parts: list[str] = []
        for quality_key in ordered_keys:
            label = QUALITY_LABEL[quality_key]
            if label in seen_labels:
                continue
            seen_labels.add(label)
            count = buckets.get(label, 0)
            if count:
                parts.append(f"{label} {count}")
        other = buckets.get("其它", 0)
        if other:
            parts.append(f"其它 {other}")
        if parts:
            lines.append("品质 " + " · ".join(parts))
    lines.append(f"使用 `{NTE_PREFIX}<角色名>面板` 查看详情")
    return "\n".join(lines)


def format_character_detail(character: "CharacterDetail") -> str:
    header_parts: list[str] = [character.name]
    quality_label = QUALITY_LABEL.get(character.quality, "")
    if quality_label:
        header_parts.append(quality_label)
    element_meta = ELEMENT_META.get(character.element_type)
    if element_meta:
        header_parts.append(element_meta[0])
    lines = [" · ".join(header_parts)]
    lines.append(f"进阶 Lv{character.alev} · 觉醒 {character.awaken_lev}")
    if character.properties:
        prop_parts = [f"{prop.name} {prop.value}" for prop in character.properties[:6] if prop.name]
        if prop_parts:
            lines.append(" · ".join(prop_parts))
    all_skills = [*character.skills, *character.city_skills]
    skill_parts = [f"{skill.name}Lv{skill.level}" for skill in all_skills if skill.name]
    if skill_parts:
        lines.append("技能: " + " · ".join(skill_parts))
    return "\n".join(lines)


def format_achievement(progress: "AchievementProgress") -> str:
    head_parts = [f"成就 {progress.achievement_cnt}/{progress.total}"]
    if progress.gold_umd_cnt:
        head_parts.append(f"金 {progress.gold_umd_cnt}")
    if progress.silver_umd_cnt:
        head_parts.append(f"银 {progress.silver_umd_cnt}")
    if progress.bronze_umd_cnt:
        head_parts.append(f"铜 {progress.bronze_umd_cnt}")
    lines = [" · ".join(head_parts)]
    categories = progress.detail
    detail_lines = [f"{_INDENT}{cat.name} {cat.progress}/{cat.total}" for cat in categories]
    lines.extend(_cap_list(detail_lines, len(categories)))
    return "\n".join(lines)


def format_area_progress(areas: list["AreaProgress"]) -> str:
    lines = [f"区域探索 · {len(areas)} 个地图"]
    detail_lines = [f"{_INDENT}{area.name} {area.total}" for area in areas]
    lines.extend(_cap_list(detail_lines, len(areas)))
    return "\n".join(lines)


def format_realestate(houses: list["House"]) -> str:
    owned = sum(1 for house in houses if house.own)
    lines = [f"房产 · 已购 {owned}/{len(houses)}"]
    detail_lines: list[str] = []
    for house in houses:
        status = "已购" if house.own else "未购"
        furniture_total = len(house.fdetail)
        if furniture_total:
            furniture_own = sum(1 for item in house.fdetail if item.own)
            detail_lines.append(f"{_INDENT}{house.name} {status} · 家具 {furniture_own}/{furniture_total}")
        else:
            detail_lines.append(f"{_INDENT}{house.name} {status}")
    lines.extend(_cap_list(detail_lines, len(houses)))
    return "\n".join(lines)


def format_vehicles(vehicles: "VehicleList") -> str:
    lines = [f"载具 · 已购 {vehicles.own_cnt}/{vehicles.total}"]
    detail_lines = [f"{_INDENT}{vehicle.name} {'已购' if vehicle.own else '未购'}" for vehicle in vehicles.detail]
    lines.extend(_cap_list(detail_lines, len(vehicles.detail)))
    return "\n".join(lines)
