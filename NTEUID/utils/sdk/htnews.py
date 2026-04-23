from __future__ import annotations

import json
import time
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .base import SdkError, BaseSdkClient


class HtNewsError(SdkError):
    pass


class CodeItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    order: str = ""
    reward: str = ""
    label: str = ""
    is_fail: str = ""


class HtNewsClient(BaseSdkClient):
    BASE_URL = "https://newsimg.5054399.com"
    USER_AGENT = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
    )

    error_cls = HtNewsError

    def _default_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.USER_AGENT,
            "Referer": "https://www.onebiji.com/",
            "Accept": "*/*",
        }

    async def fetch_code_list(self) -> list[CodeItem]:
        now = datetime.now()
        ts = f"{now.year - 1900}{now.month - 1}{now.day}{now.hour}{now.minute}"
        ms = int(time.time() * 1000)
        text = await self._request(f"/comm/mlcxqcommon/static/wap/js/data_173.js?{ts}&callback=?&_={ms}")
        if not isinstance(text, str):
            raise HtNewsError("兑换码响应格式异常", {"raw": text})
        try:
            data = json.loads(text.split("=", 1)[1].rstrip().rstrip(";"))
        except (IndexError, json.JSONDecodeError) as err:
            raise HtNewsError("兑换码响应解析失败", {"raw": text}) from err
        return [CodeItem.model_validate(c) for c in data if isinstance(c, dict)]


ht_news = HtNewsClient()
