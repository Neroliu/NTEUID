from __future__ import annotations

from datetime import datetime
from collections import OrderedDict

from PIL import Image, ImageDraw

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img

from ..utils.msgs import SignRecordMsg, send_nte_notify
from ..utils.image import (
    COLOR_BG,
    COLOR_BLUE,
    COLOR_GRAY,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_TITLE,
    draw_card,
    cache_name,
    draw_page_header,
    paste_rounded_image,
    download_pic_from_url,
)
from ..utils.session import ensure_tajiduo_client
from ..utils.database import NTEUser
from ..utils.constants import GAME_ID_YIHUAN
from ..utils.fonts.nte_fonts import (
    nte_font_18,
    nte_font_20,
    nte_font_22,
    nte_font_24,
    nte_font_26,
    nte_font_28,
    nte_font_42,
)
from ..utils.sdk.tajiduo_model import TajiduoError, SignRewardRecord
from ..utils.resource.RESOURCE_PATH import SIGN_RECORD_PATH

WIDTH = 1080
PADDING = 36
CARD_GAP = 20
CARD_RADIUS = 22
HEADER_HEIGHT = 188

SUMMARY_HEIGHT = 156
SECTION_HEAD_HEIGHT = 60
ROW_HEIGHT = 82
ICON_SIZE = 58
MAX_ROWS = 40


async def run_sign_records(bot: Bot, ev: Event) -> None:
    user = await NTEUser.get_active(ev.user_id, ev.bot_id)
    if user is None:
        return await send_nte_notify(bot, ev, SignRecordMsg.NOT_LOGGED_IN)

    try:
        client = await ensure_tajiduo_client(user)
    except TajiduoError as error:
        await NTEUser.mark_invalid_by_cookie(user.cookie, "refresh 失败")
        logger.warning(f"[NTE签到记录] 账号 {user.center_uid} 刷新失败: {error.message}")
        return await send_nte_notify(bot, ev, SignRecordMsg.LOGIN_EXPIRED)

    try:
        records = await client.get_sign_reward_records(GAME_ID_YIHUAN)
    except TajiduoError as error:
        logger.warning(f"[NTE签到记录] 账号 {user.center_uid} 拉取失败: {error.message}")
        return await send_nte_notify(bot, ev, SignRecordMsg.LOAD_FAILED)

    if not records:
        return await send_nte_notify(bot, ev, SignRecordMsg.EMPTY)

    await bot.send(await _draw_sign_records_img(records, user.center_uid))


async def _load_icon(url: str) -> Image.Image | None:
    if not url:
        return None
    try:
        return await download_pic_from_url(
            SIGN_RECORD_PATH,
            url,
            name=cache_name("reward-icon", url),
        )
    except OSError:
        return None


def _format_time(ts_ms: int) -> str:
    if ts_ms <= 0:
        return "未知时间"
    return datetime.fromtimestamp(ts_ms / 1000).strftime("%H:%M")


def _format_date(ts_ms: int) -> str:
    if ts_ms <= 0:
        return "未知日期"
    return datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")


async def _draw_sign_records_img(records: list[SignRewardRecord], center_uid: str):
    sorted_records = sorted(records, key=lambda item: item.create_time, reverse=True)
    truncated = sorted_records[:MAX_ROWS]
    overflow = max(0, len(sorted_records) - MAX_ROWS)

    grouped: OrderedDict[str, list[SignRewardRecord]] = OrderedDict()
    for record in truncated:
        grouped.setdefault(_format_date(record.create_time), []).append(record)

    list_height = 0
    for items in grouped.values():
        list_height += SECTION_HEAD_HEIGHT + len(items) * ROW_HEIGHT
    list_height += max(0, len(grouped) - 1) * CARD_GAP
    total_height = HEADER_HEIGHT + PADDING + SUMMARY_HEIGHT + CARD_GAP + list_height + PADDING

    canvas = Image.new("RGBA", (WIDTH, total_height), COLOR_BG)
    latest_time = _format_date(sorted_records[0].create_time)
    draw_page_header(
        canvas,
        "异环 · 签到奖励记录",
        f"账号 {center_uid}  ·  共 {len(sorted_records)} 条",
        height=HEADER_HEIGHT,
        title_xy=(PADDING, 38),
        subtitle_y=116,
        title_font=nte_font_42,
        subtitle_font=nte_font_22,
    )
    draw = ImageDraw.Draw(canvas)
    y = HEADER_HEIGHT + PADDING

    draw_card(draw, (PADDING, y, WIDTH - PADDING, y + SUMMARY_HEIGHT), radius=CARD_RADIUS)
    draw.text((PADDING + 24, y + 18), "记录概览", font=nte_font_24, fill=COLOR_TITLE)
    unique_rewards = len({record.name for record in sorted_records})
    stats = [
        ("最近领奖", latest_time),
        ("覆盖天数", str(len(grouped))),
        ("奖励种类", str(unique_rewards)),
    ]
    inner_width = WIDTH - PADDING * 2 - 48
    cell_width = (inner_width - 2 * 16) // 3
    for index, (title, value) in enumerate(stats):
        left = PADDING + 24 + index * (cell_width + 16)
        draw.rounded_rectangle(
            (left, y + 58, left + cell_width, y + SUMMARY_HEIGHT - 24),
            radius=18,
            fill=(255, 255, 255, 88),
        )
        draw.text((left + 16, y + 74), title, font=nte_font_18, fill=COLOR_MUTED)
        draw.text((left + 16, y + 108), value, font=nte_font_28, fill=COLOR_BLUE)
    y += SUMMARY_HEIGHT + CARD_GAP

    for date, items in grouped.items():
        section_height = SECTION_HEAD_HEIGHT + len(items) * ROW_HEIGHT
        draw_card(draw, (PADDING, y, WIDTH - PADDING, y + section_height), radius=CARD_RADIUS)
        draw.text((PADDING + 24, y + 18), date, font=nte_font_24, fill=COLOR_TITLE)
        draw.text((WIDTH - PADDING - 24, y + 20), f"{len(items)} 条", font=nte_font_20, fill=COLOR_MUTED, anchor="ra")

        row_top = y + SECTION_HEAD_HEIGHT
        for record in items:
            draw.rounded_rectangle(
                (PADDING + 24, row_top, WIDTH - PADDING - 24, row_top + ROW_HEIGHT - 12),
                radius=18,
                fill=COLOR_PANEL,
            )
            icon = await _load_icon(record.icon)
            if icon is not None:
                paste_rounded_image(canvas, icon, (PADDING + 38, row_top + 6), (ICON_SIZE, ICON_SIZE), 14)
            else:
                draw.rounded_rectangle(
                    (PADDING + 38, row_top + 6, PADDING + 38 + ICON_SIZE, row_top + 6 + ICON_SIZE),
                    radius=14,
                    fill=COLOR_GRAY,
                )

            left = PADDING + 38 + ICON_SIZE + 18
            draw.text((left, row_top + 14), record.name, font=nte_font_24, fill=COLOR_TITLE)
            draw.text((left, row_top + 42), _format_time(record.create_time), font=nte_font_20, fill=COLOR_MUTED)
            draw.text(
                (WIDTH - PADDING - 40, row_top + 30),
                f"×{record.num}",
                font=nte_font_26,
                fill=COLOR_BLUE,
                anchor="rm",
            )
            row_top += ROW_HEIGHT

        y += section_height + CARD_GAP

    if overflow:
        draw.text(
            (WIDTH - PADDING, total_height - 26),
            f"另有 {overflow} 条历史记录未展示",
            font=nte_font_20,
            fill=COLOR_MUTED,
            anchor="ra",
        )

    return await convert_img(canvas)
