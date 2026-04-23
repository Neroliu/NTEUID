from pathlib import Path

from PIL import ImageFont

from gsuid_core.utils.fonts.fonts import core_font

EMOJI_ORIGIN_PATH = Path(__file__).parent / "NotoColorEmoji.ttf"


def nte_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return core_font(size)


def emoji_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(EMOJI_ORIGIN_PATH), size=size)


nte_font_10 = nte_font_origin(10)
nte_font_12 = nte_font_origin(12)
nte_font_14 = nte_font_origin(14)
nte_font_15 = nte_font_origin(15)
nte_font_16 = nte_font_origin(16)
nte_font_18 = nte_font_origin(18)
nte_font_20 = nte_font_origin(20)
nte_font_22 = nte_font_origin(22)
nte_font_23 = nte_font_origin(23)
nte_font_24 = nte_font_origin(24)
nte_font_25 = nte_font_origin(25)
nte_font_26 = nte_font_origin(26)
nte_font_28 = nte_font_origin(28)
nte_font_30 = nte_font_origin(30)
nte_font_32 = nte_font_origin(32)
nte_font_34 = nte_font_origin(34)
nte_font_36 = nte_font_origin(36)
nte_font_38 = nte_font_origin(38)
nte_font_40 = nte_font_origin(40)
nte_font_42 = nte_font_origin(42)
nte_font_44 = nte_font_origin(44)
nte_font_50 = nte_font_origin(50)
nte_font_58 = nte_font_origin(58)
nte_font_60 = nte_font_origin(60)
nte_font_62 = nte_font_origin(62)
nte_font_70 = nte_font_origin(70)
nte_font_84 = nte_font_origin(84)

emoji_font = emoji_font_origin(109)
