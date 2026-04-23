import asyncio

from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .utils import format_post_time
from ..utils.msgs import NoticeMsg, send_nte_notify
from .notice_card import draw_notice_list_img, draw_notice_detail_img
from ..utils.sdk.tajiduo import tajiduo_web
from ..utils.sdk.tajiduo_model import NoticePost, TajiduoError, NTENoticeType

LIST_COUNT = 4
FETCH_COUNT = 4
NOTICE_TYPES = (NTENoticeType.INFO, NTENoticeType.ACTIVITY, NTENoticeType.NOTICE)

_NOTICE_ID_MAP: dict[int, NTENoticeType] = {}


async def get_notice(bot: Bot, ev: Event):
    text = ev.text.strip().replace("#", "")

    try:
        if not text:
            columns = await get_all_notice_list()
            if not any(columns.values()):
                return await send_nte_notify(bot, ev, NoticeMsg.EMPTY)

            _refresh_notice_id_map(columns)
            return await bot.send(await draw_notice_list_img(render_notice_list(columns)))

        if not text.isdigit():
            return await send_nte_notify(bot, ev, NoticeMsg.INVALID_POST_ID)
        post_id, notice_type = _parse_notice_target(text)
        post = await tajiduo_web.get_notice_detail(post_id)
        img = await draw_notice_detail_img(*render_notice_detail(post, notice_type))
        return await bot.send(img)  # pyright: ignore[reportArgumentType]
    except TajiduoError as error:
        logger.warning(f"[异环公告] 拉取公告失败: {error.message}")
        return await send_nte_notify(bot, ev, NoticeMsg.LOAD_FAILED)


async def get_all_notice_list() -> dict[NTENoticeType, list[NoticePost]]:
    tasks = [tajiduo_web.get_notice_list(notice_type, count=FETCH_COUNT) for notice_type in NOTICE_TYPES]
    results = await asyncio.gather(*tasks)
    return {notice_type: posts[:LIST_COUNT] for notice_type, posts in zip(NOTICE_TYPES, results)}


def render_notice_list(columns: dict[NTENoticeType, list[NoticePost]]) -> dict[str, list[tuple[str, str, str, str]]]:
    return {
        notice_type.label: [_to_list_item(post) for post in columns.get(notice_type, [])]
        for notice_type in NOTICE_TYPES
    }


def render_notice_detail(post: NoticePost, notice_type: NTENoticeType | None) -> tuple[str, NoticePost]:
    return (notice_type.label if notice_type else "公告"), post


def _refresh_notice_id_map(columns: dict[NTENoticeType, list[NoticePost]]) -> None:
    _NOTICE_ID_MAP.clear()
    for notice_type, posts in columns.items():
        for post in posts:
            _NOTICE_ID_MAP[post.post_id] = notice_type


def _parse_notice_target(text: str) -> tuple[int, NTENoticeType | None]:
    post_id = int(text)
    return post_id, _NOTICE_ID_MAP.get(post_id)


def _to_list_item(post: NoticePost) -> tuple[str, str, str, str]:
    return (
        str(post.post_id),
        post.subject,
        format_post_time(post.create_time),
        _pick_preview(post),
    )


def _pick_preview(post: NoticePost) -> str:
    if post.images:
        return post.images[0].url
    if post.vods:
        return post.vods[0].cover
    return ""
