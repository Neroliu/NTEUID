from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from PIL import Image, ImageOps, ImageDraw

from gsuid_core.utils.image.convert import convert_img

from ..utils.image import (
    COLOR_BG,
    COLOR_BLUE,
    COLOR_GRAY,
    COLOR_NAVY,
    COLOR_MUTED,
    COLOR_TITLE,
    COLOR_WHITE,
    COLOR_OVERLAY,
    COLOR_SUBTEXT,
    draw_card,
    cache_name,
    rounded_mask,
    shrink_to_width,
    paste_circle_image,
    download_pic_from_url,
)
from ..utils.fonts.nte_fonts import (
    nte_font_18,
    nte_font_20,
    nte_font_22,
    nte_font_28,
    nte_font_42,
)
from ..utils.sdk.tajiduo_model import TeamRecommendation
from ..utils.resource.RESOURCE_PATH import TEAM_PATH

WIDTH = 1080
PADDING = 36
CARD_GAP = 20
CARD_RADIUS = 22
HEADER_HEIGHT = 152
CARD_INNER_PADDING = 24

ICON_SIZE = 110
CONTENT_WIDTH = WIDTH - PADDING * 2 - CARD_INNER_PADDING * 2
IMAGE_GAP = 12
TITLE_BG_PATH = Path(__file__).parent.parent / "nte_notice" / "texture2d" / "home-yihuan.webp"


@dataclass(slots=True)
class PreparedRecommendation:
    recommendation: TeamRecommendation
    icon: Image.Image | None
    images: list[Image.Image]
    header_height: int
    card_height: int
    has_image_error: bool


async def _load_remote(url: str, cache_key: str) -> Image.Image | None:
    if not url:
        return None
    try:
        return await download_pic_from_url(
            TEAM_PATH,
            url,
            name=cache_name(cache_key, url),
        )
    except OSError:
        return None


def _load_title_bg(width: int, height: int) -> Image.Image:
    try:
        image = Image.open(TITLE_BG_PATH).convert("RGB")
    except OSError:
        return Image.new("RGB", (width, height), COLOR_NAVY)
    return ImageOps.fit(
        image,
        (width, height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.0),
    )


async def _prepare_recommendation(
    recommendation: TeamRecommendation,
) -> PreparedRecommendation:
    icon = await _load_remote(recommendation.icon, "team-icon")

    images: list[Image.Image] = []
    for image_url in recommendation.imgs:
        image = await _load_remote(image_url, "team-gallery")
        if image is None:
            continue
        images.append(shrink_to_width(image.convert("RGBA"), CONTENT_WIDTH))

    header_height = 24 + ICON_SIZE + 24
    card_height = header_height
    has_image_error = bool(recommendation.imgs) and not images

    if images:
        card_height += IMAGE_GAP
        card_height += sum(image.height for image in images)
        card_height += IMAGE_GAP * (len(images) - 1)
        card_height += 24
    elif has_image_error:
        card_height += 72

    return PreparedRecommendation(
        recommendation=recommendation,
        icon=icon,
        images=images,
        header_height=header_height,
        card_height=card_height,
        has_image_error=has_image_error,
    )


async def draw_team_img(
    recommendations: list[TeamRecommendation],
    role_name: str,
):
    ordered = list(recommendations)
    prepared = [await _prepare_recommendation(item) for item in ordered]
    total_height = (
        HEADER_HEIGHT
        + PADDING
        + sum(item.card_height for item in prepared)
        + max(0, len(prepared) - 1) * CARD_GAP
        + PADDING
    )

    subtitle = f"{role_name}  ·  官方推荐"
    if len(ordered) > 1:
        subtitle = f"{role_name}  ·  共 {len(ordered)} 套方案"

    canvas = Image.new("RGBA", (WIDTH, total_height), COLOR_BG)
    title_bg = _load_title_bg(WIDTH, HEADER_HEIGHT)
    canvas.paste(title_bg, (0, 0))
    canvas.alpha_composite(Image.new("RGBA", (WIDTH, HEADER_HEIGHT), COLOR_OVERLAY), (0, 0))
    draw = ImageDraw.Draw(canvas)
    title_right = WIDTH - PADDING
    draw.text((title_right, 34), "异环配队", font=nte_font_42, fill=COLOR_WHITE, anchor="ra")
    draw.text((title_right, 96), subtitle, font=nte_font_22, fill=COLOR_SUBTEXT, anchor="ra")
    y = HEADER_HEIGHT + PADDING

    for index, item in enumerate(prepared, start=1):
        recommendation = item.recommendation
        card_height = item.card_height
        draw_card(draw, (PADDING, y, WIDTH - PADDING, y + card_height), radius=CARD_RADIUS)
        if item.icon is not None:
            paste_circle_image(canvas, item.icon, (PADDING + 24, y + 24), ICON_SIZE)
        else:
            draw.ellipse(
                (PADDING + 24, y + 24, PADDING + 24 + ICON_SIZE, y + 24 + ICON_SIZE),
                fill=COLOR_GRAY,
            )

        text_left = PADDING + 24 + ICON_SIZE + 24
        draw.text((text_left, y + 26), recommendation.name, font=nte_font_28, fill=COLOR_TITLE)
        draw.rounded_rectangle(
            (text_left, y + 64, text_left + 112, y + 94),
            radius=12,
            fill=(232, 240, 250),
        )
        draw.text(
            (text_left + 56, y + 79), f"角色 #{recommendation.id}", font=nte_font_18, fill=COLOR_BLUE, anchor="mm"
        )
        if len(prepared) > 1:
            tag_right = WIDTH - PADDING - 24
            tag_left = tag_right - 112
            draw.rounded_rectangle(
                (tag_left, y + 28, tag_right, y + 60),
                radius=14,
                fill=(244, 246, 248),
            )
            draw.text(
                ((tag_left + tag_right) // 2, y + 44),
                f"方案 {index}",
                font=nte_font_20,
                fill=COLOR_MUTED,
                anchor="mm",
            )

        content_top = y + item.header_height
        if item.images:
            image_y = content_top + IMAGE_GAP
            for image in item.images:
                image_left = PADDING + CARD_INNER_PADDING + (CONTENT_WIDTH - image.width) // 2
                canvas.paste(image, (image_left, image_y), rounded_mask((image.width, image.height), 18))
                image_y += image.height + IMAGE_GAP
        elif item.has_image_error:
            draw.text(
                (PADDING + 24, content_top + 20),
                "配图加载失败",
                font=nte_font_20,
                fill=COLOR_MUTED,
            )

        y += card_height + CARD_GAP

    return await convert_img(canvas)
