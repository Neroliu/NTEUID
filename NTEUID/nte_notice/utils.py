import re
import json
from html import unescape
from datetime import datetime

from ..utils.sdk.tajiduo_model import NoticePost

TAG_RE = re.compile(r"<[^>]+>")

_TAJIDUO_POST_URL = "https://www.tajiduo.com/bbs/index.html#/post"


def format_post_time(timestamp: int) -> str:
    if timestamp <= 0:
        return "未知时间"
    return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")


def get_post_url(post: NoticePost) -> str:
    return f"{_TAJIDUO_POST_URL}?postId={post.post_id}&id={post.community_id}"


def get_post_summary(post: NoticePost) -> str:
    structured = _structured_content_to_text(post.structured_content)
    if structured:
        return structured
    return _html_to_text(post.content)


def _structured_content_to_text(content: str) -> str:
    if not content:
        return ""

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return ""

    if not isinstance(payload, list):
        return ""

    parts = [item["txt"] for item in payload if isinstance(item, dict) and isinstance(item.get("txt"), str)]
    return _normalize_text("".join(parts))


def _html_to_text(content: str) -> str:
    if not content:
        return ""
    return _normalize_text(unescape(TAG_RE.sub("", content)))


def _normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
