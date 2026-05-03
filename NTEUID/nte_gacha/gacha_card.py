from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, ImageDraw

from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import get_event_avatar

from .gacha_model import NTEGachaSection, NTEGachaSummary
from ..utils.image import (
    add_footer,
    get_nte_bg,
    open_texture,
    rounded_mask,
    char_img_ring,
    make_nte_role_title,
)
from ..utils.resource.cdn import get_avatar_img, get_weapon_img
from ..utils.fonts.nte_fonts import nte_font_bold, nte_font_origin

_TEX = Path(__file__).parent / "texture2d"
_WHITE = (255, 255, 255)
_SUB = (210, 215, 230)

_BANNER_RANK = {"限定卡池": 0, "弧盘池": 1, "常驻卡池": 2}
_COST_PER_PULL = 160


def _grid(inner_w: int) -> tuple[int, int, int]:
    """每行 6 张 char_bg 卡（原比例 240:340），行间叠 50/340 留紧凑感。"""
    w = (inner_w - 20) // 6
    h = w * 340 // 240
    return w, h, h * 290 // 340


def _rating(total: int, ssr: int) -> str:
    # i_api23try.gacha_basic.constant 内嵌：SSR 走 总抽/总S，无 SSR 走 总抽数
    if ssr > 0:
        table, metric = (
            (
                (15, "欧气附体天选人"),
                (40, "协议签订幸运儿"),
                (60, "普普通通路人王"),
                (75, "伊波恩打工仔"),
                (10**9, "异象重点关照对象"),
            ),
            total / ssr,
        )
    else:
        table, metric = ((50, "囤囤鼠"), (10**9, "薛定谔的抽卡人")), total
    return next(label for thr, label in table if metric <= thr)


def _draw_title_stats(canvas: Image.Image, title_y: int, total: int, ssr: int) -> None:
    right = 1080 - 21 - 75
    mid = title_y + 108 + 30
    draw = ImageDraw.Draw(canvas)
    f_num, f_unit, f_tier = nte_font_bold(48), nte_font_origin(24), nte_font_bold(30)
    sk = (0, 0, 0, 230)
    unit_w = draw.textlength("抽", font=f_unit)
    row1_b = mid - 6
    draw.text((right, row1_b), "抽", font=f_unit, fill=_SUB, anchor="rb", stroke_width=2, stroke_fill=sk)
    draw.text(
        (right - unit_w - 6, row1_b), str(total), font=f_num, fill=_WHITE, anchor="rb", stroke_width=2, stroke_fill=sk
    )
    draw.text(
        (right, mid + 12), _rating(total, ssr), font=f_tier, fill=_WHITE, anchor="rt", stroke_width=2, stroke_fill=sk
    )


def _draw_banner(canvas: Image.Image, xy: tuple[int, int], inner_w: int, section: NTEGachaSection) -> None:
    H, pad = 147, 24
    bg = ImageOps.fit(
        open_texture(_TEX / "banner_nte.png").convert("RGBA"), (inner_w, H), method=Image.Resampling.LANCZOS
    )
    canvas.paste(bg, xy, rounded_mask((inner_w, H), 15))

    cx, cy = xy
    draw = ImageDraw.Draw(canvas)
    f_lbl = nte_font_origin(18)

    draw.text((cx + pad, cy + pad - 3), section.banner_name, font=nte_font_bold(42), fill=_WHITE, anchor="lt")
    sub_y = cy + pad + 54
    draw.text((cx + pad, sub_y), "本轮消耗", font=f_lbl, fill=_SUB, anchor="lt")
    draw.text(
        (cx + pad + draw.textlength("本轮消耗", font=f_lbl) + 9, sub_y - 2),
        str(section.total_pull_count * _COST_PER_PULL),
        font=nte_font_bold(21),
        fill=_WHITE,
        anchor="lt",
    )

    avg = str(section.avg_pity) if section.ssr_count > 0 else "—"
    stats = ((str(section.total_pull_count), "总抽数"), (str(section.ssr_count), "S 命中"), (avg, "平均抽数"))
    block_w = 660
    col_w = block_w // 3
    block_x = cx + inner_w - pad - block_w
    f_stat = nte_font_bold(39)
    sy = cy + (H - 69) // 2
    for i, (val, lbl) in enumerate(stats):
        ccx = block_x + col_w * i + col_w // 2
        draw.text((ccx, sy), val, font=f_stat, fill=_WHITE, anchor="mt")
        draw.text((ccx, sy + 48), lbl, font=f_lbl, fill=_SUB, anchor="mt")
    for i in (1, 2):
        sx = block_x + col_w * i
        draw.line([(sx, cy + 33), (sx, cy + H - 33)], fill=(255, 255, 255, 60), width=2)


async def _draw_item(
    canvas: Image.Image, xy: tuple[int, int], w: int, h: int, item_id: str, item_name: str, pity: int
) -> None:
    cell = open_texture(_TEX / "char_bg.png", size=(w, h)).convert("RGBA")
    if item_id.startswith("fork_"):
        avatar = await get_weapon_img(item_id)
    elif item_id.isdigit():
        avatar = await get_avatar_img(item_id)
    else:
        avatar = None
    if avatar is not None:
        rs = w * 230 // 240
        cell.alpha_composite(char_img_ring(avatar.convert("RGBA"), rs), ((w - rs) // 2, h * 48 // 340))

    draw = ImageDraw.Draw(cell)
    f_name = nte_font_origin(16)
    name = item_name.removesuffix("角色卡")
    suffix = ""
    while draw.textlength(name + suffix, font=f_name) > w - 30 and len(name) > 1:
        name, suffix = name[:-1], "…"
    draw.text((w // 2, h * 292 // 340), name + suffix, font=f_name, fill=_WHITE, anchor="mm")

    f_pull = nte_font_bold(16)
    pull_text = f"{pity}抽"
    pw = int(draw.textlength(pull_text, font=f_pull)) + 21
    ph = 28
    px, py = w - pw - 15, h * 200 // 340
    # ≤30 欧 / ≤80 平稳 / 其余 非
    color = (26, 191, 76) if pity <= 30 else (234, 129, 59) if pity <= 80 else (250, 58, 61)
    cell.paste(Image.new("RGBA", (pw, ph), (*color, 235)), (px, py), rounded_mask((pw, ph), ph // 2))
    draw.text((px + pw // 2, py + ph // 2), pull_text, font=f_pull, fill=_WHITE, anchor="mm")
    canvas.alpha_composite(cell, xy)


async def _draw_section(canvas: Image.Image, top_y: int, inner_w: int, section: NTEGachaSection) -> int:
    _draw_banner(canvas, (21, top_y), inner_w, section)
    items_top = top_y + 147
    items = sorted(section.items, key=lambda i: i.pull_time_ts, reverse=True)[:12]
    w, h, stride = _grid(inner_w)
    for idx, item in enumerate(items):
        row, col = divmod(idx, 6)
        await _draw_item(
            canvas, (21 + col * (w + 4), items_top + row * stride), w, h, item.item_id, item.item_name, item.pity
        )
    return items_top + ((len(items) - 1) // 6) * stride + h


async def draw_gacha_summary_img(
    ev: Event,
    summary: NTEGachaSummary,
    *,
    role_name: str,
    role_id: str,
) -> bytes:
    inner_w = 1080 - 42
    _, h, stride = _grid(inner_w)

    sections = sorted(
        (s for s in summary.sections if s.ssr_count > 0),
        key=lambda s: _BANNER_RANK.get(s.banner_name, 99),
    )

    def section_h(n: int) -> int:
        return 147 + ((max(min(n, 12), 1) - 1) // 6) * stride + h

    total_h = 12 + 216 + 9 + sum(section_h(len(s.items)) for s in sections) + max(0, len(sections) - 1) * 12 + 24 + 60

    canvas = get_nte_bg(1080, total_h)
    title_y = 12
    canvas.alpha_composite(
        make_nte_role_title(await get_event_avatar(ev), role_name, role_id),
        (3, title_y),
    )

    o = summary.overview
    assert o is not None  # 调用方已用 summary.is_empty 过滤
    _draw_title_stats(canvas, title_y, o.total_pull_count, o.total_ssr_count)

    cursor = title_y + 216 + 9
    for idx, section in enumerate(sections):
        cursor = await _draw_section(canvas, cursor, inner_w, section)
        if idx < len(sections) - 1:
            cursor += 12

    return await convert_img(add_footer(canvas))
