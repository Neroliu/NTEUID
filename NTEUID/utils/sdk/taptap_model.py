from __future__ import annotations

from typing import Any

from pydantic import Field, BaseModel, ConfigDict, ValidationError

from .base import SdkError


class TaptapError(SdkError):
    """TapTap 战绩接口失败的基类。"""


class _TaptapModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class TaptapBinding(_TaptapModel):
    """`role-profile` 接口里能反映 TapTap 账号绑定状态的精简字段。

    TapTap 网页就用 `is_bind` 当 gate 决定要不要显示『未查到游戏角色』；
    本插件同样用它做绑定有效性校验。
    """

    role_id: str = Field(default="", description="游戏内角色 ID；未绑定时为空串")
    name: str = Field(default="", description="游戏内角色昵称；未绑定时为空串")
    is_bind: bool = Field(default=False, description="该 TapTap 账号是否已绑定异环角色")
    is_data_loaded: bool = Field(default=False, description="TapTap 是否已同步过游戏侧数据")
    show_bind_button: bool = Field(default=False, description="网页是否展示『绑定角色』按钮")
    level_rank: int = Field(default=0, description="角色等级排名（0 = 未上榜或无数据）")


class GachaOverview(_TaptapModel):
    total_pull_count: int = Field(description="总抽数（所有池子加起来）")
    total_ssr_count: int = Field(description="总 S 级抽中次数（含重复）")
    banner_count: int = Field(description="出现过抽卡的池子数")
    banner_type_count: int = Field(description="池子类型数")


class GachaPoolStats(_TaptapModel):
    key: str = Field(description="池子稳定 ID")
    title: str = Field(description="池子展示名")
    total_pull_count: int = Field(description="本池累计抽数")
    avg_pity: int = Field(description="本池平均出 S 抽数")
    min_pity: int = Field(description="本池最少出 S 抽数")
    max_pity: int = Field(description="本池最多出 S 抽数")


class GachaSSRItem(_TaptapModel):
    item_id: str = Field(description="物品 ID（角色用数字串、道具用字符串）")
    item_name: str = Field(description="物品名")
    item_icon: str = Field(description="缩略图 ID（与 item_id 一致）")
    item_rarity: str = Field(description="稀有度：S/A/B")
    item_count: int = Field(description="该次 S 命中的具体抽数（即保底差值 / pity）")
    pull_time_ts: int = Field(alias="pull_time", description="最近一次抽中 unix 秒")


class GachaSection(_TaptapModel):
    banner_id: str
    banner_name: str
    banner_type: str
    banner_image: str = Field(description="池子代表图 ID（角色 id 或道具 id）")
    begin_time_ts: int = Field(alias="begin_time", description="池子起始时间，0=长期池")
    end_time_ts: int = Field(alias="end_time", description="池子结束时间，0=长期池")
    up_character: str = Field(default="", description="UP 角色名（限时池才填）")
    total_pull_count: int
    ssr_count: int = Field(description="本池 S 命中次数")
    avg_pity: int
    min_pity: int
    max_pity: int
    pity_range_text: str = Field(description="保底范围文案，如 '1-5抽'")
    latest_pull_time_ts: int = Field(alias="latest_pull_time", description="本池最近一次 S 抽中 unix 秒")
    items: list[GachaSSRItem] = Field(default_factory=list, description="本池抽到过的所有 S 卡明细")

    @property
    def is_limited(self) -> bool:
        return self.begin_time_ts != 0 or self.end_time_ts != 0


class GachaSummary(_TaptapModel):
    overview: GachaOverview | None = Field(
        default=None,
        description="总览。**未抽过卡 / 未绑游戏角色**时 TapTap 直接不返这个字段",
    )
    stats: list[GachaPoolStats] = Field(default_factory=list)
    sections: list[GachaSection] = Field(default_factory=list)
    last_updated_ts: int = Field(alias="last_updated", description="TapTap 上次同步游戏侧数据 unix 秒")

    @property
    def is_empty(self) -> bool:
        """没有任何抽卡数据：要么没绑游戏角色，要么绑了但还没抽过 / 还没同步。"""
        return self.overview is None or self.overview.total_pull_count == 0


def _parse(model: type[BaseModel], data: Any, message: str) -> Any:
    try:
        if isinstance(data, list):
            return [model.model_validate(item) for item in data]
        return model.model_validate(data)
    except ValidationError as err:
        raise TaptapError(f"{message}: {err}", data if isinstance(data, dict) else {}) from err


def _expect_dict(data: Any, message: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TaptapError(message)
    return data
