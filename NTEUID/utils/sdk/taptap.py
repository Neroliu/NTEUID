from __future__ import annotations

from typing import Any

from .base import BaseSdkClient
from ..constants import (
    TAPTAP_BASE_URL,
    TAPTAP_USER_AGENT,
    TAPTAP_APP_ID_YIHUAN,
    TAPTAP_GAME_RECORD_PATH,
    TAPTAP_DEFAULT_DEVICE_UID,
)
from .taptap_model import (
    TaptapError,
    GachaSummary,
    TaptapBinding,
    _parse,
    _expect_dict,
)


class TaptapPosterClient(BaseSdkClient):
    """异环 TapTap 战绩抽卡数据客户端。

    所有端点都是匿名 GET，不需要 Cookie / token；公共 query 里必须带 `X-UA`，
    Referer 必须是 taptap.cn 同源 poster 路径。
    """

    BASE_URL = TAPTAP_BASE_URL
    USER_AGENT = TAPTAP_USER_AGENT
    error_cls = TaptapError

    def __init__(
        self,
        *,
        app_id: str = TAPTAP_APP_ID_YIHUAN,
        device_uid: str = TAPTAP_DEFAULT_DEVICE_UID,
    ) -> None:
        self.app_id = app_id
        self.device_uid = device_uid

    def _extract_data(self, payload: dict[str, Any], path: str) -> Any:
        if not payload.get("success"):
            raise self.error_cls(f"[{path}] success=false", payload)
        data = payload.get("data")
        return data if data is not None else {}

    def _build_x_ua(self, user_id: int) -> str:
        return (
            f"V=1&PN=WebActivity&LANG=zh_CN&VN_CODE=1&LOC=CN&PLT=iOS&DS=iOS"
            f"&UID={self.device_uid}&OS=iOS&OSV=18.7&VID={user_id}"
        )

    def _query(self, user_id: int, **extra: Any) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "app_id": self.app_id,
            "is_preview": "false",
            **extra,
            "X-UA": self._build_x_ua(user_id),
        }

    async def check_binding(self, user_id: int) -> TaptapBinding:
        """前置 gate：判断该 TapTap user_id 是否已绑定异环游戏角色。

        TapTap 网页就用本接口的 `is_bind` 字段决定要不要显示『未查到游戏角色』。
        gacha-record-summary 单独看分不清『没绑』和『绑了但没抽过』，必须先过这个 gate。
        """
        err = "TapTap 绑定信息格式错误"
        data = await self._request(
            f"{TAPTAP_GAME_RECORD_PATH}/role-profile",
            method="GET",
            query=self._query(user_id),
        )
        return _parse(TaptapBinding, _expect_dict(data, err), err)

    async def gacha_summary(self, user_id: int) -> GachaSummary:
        """抽卡总览：总抽数 / 每池保底 / 每池 S 命中明细带时间戳。"""
        err = "TapTap 抽卡总览格式错误"
        data = await self._request(
            f"{TAPTAP_GAME_RECORD_PATH}/gacha-record-summary",
            method="GET",
            query=self._query(user_id),
        )
        wrapper = _expect_dict(data, err)
        summary = wrapper.get("summary")
        if summary is None:
            raise self.error_cls(
                f"TapTap 抽卡总览缺少 summary 字段（user_id={user_id}）",
                wrapper,
            )
        return _parse(GachaSummary, _expect_dict(summary, err), err)


taptap = TaptapPosterClient()
