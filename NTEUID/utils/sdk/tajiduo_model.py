from __future__ import annotations

from enum import IntEnum
from typing import Any, List, Optional
from dataclasses import dataclass

from pydantic import Field, BaseModel, ConfigDict, ValidationError

from .base import SdkError


class TajiduoError(SdkError):
    pass


@dataclass
class TajiduoSession:
    access_token: str
    refresh_token: str
    center_uid: str
    raw: dict


class _TajiduoModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class TajiduoRoleRef(_TajiduoModel):
    """`getGameBindRole` / `getGameRoles` 共用的角色引用；`role_id=0` 代表该位未绑定。"""

    role_id: int = Field(0, alias="roleId")
    role_name: str = Field("", alias="roleName")

    @property
    def uid(self) -> str:
        return str(self.role_id) if self.role_id else ""


class _GameRolesPayload(_TajiduoModel):
    bind_role: int = Field(0, alias="bindRole")
    roles: List[TajiduoRoleRef] = Field(default_factory=list)


@dataclass(frozen=True)
class GameRoleList:
    """`bind_role_id=0` 代表账号在该游戏下未设主绑定角色——触发 `bind_role` 日任务的信号。"""

    bind_role_id: int
    roles: list[TajiduoRoleRef]


class CommunitySignResult(_TajiduoModel):
    exp: int = 0
    gold_coin: int = Field(0, alias="goldCoin")


class TeamRecommendation(_TajiduoModel):
    id: str
    name: str
    icon: str = ""
    desc: str = ""
    imgs: List[str] = Field(default_factory=list)


class GameRecordRoleInfo(_TajiduoModel):
    account: str = ""
    game_id: int = Field(0, alias="gameId")
    gender: int = -1
    lev: int = 0
    role_id: int = Field(0, alias="roleId")
    role_name: str = Field("", alias="roleName")
    server_id: int = Field(0, alias="serverId")
    server_name: str = Field("", alias="serverName")


class GameRecordCard(_TajiduoModel):
    game_id: int = Field(0, alias="gameId")
    game_name: str = Field("", alias="gameName")
    game_icon: str = Field("", alias="gameIcon")
    background_image: str = Field("", alias="backgroundImage")
    bind_role_info: Optional[GameRecordRoleInfo] = Field(None, alias="bindRoleInfo")
    link: str = ""


class SignRewardRecord(_TajiduoModel):
    create_time: int = Field(0, alias="createTime")
    icon: str = ""
    name: str = ""
    num: int = 0


class RoleHomeAchieveProgress(_TajiduoModel):
    achievement_cnt: int = Field(0, alias="achievementCnt")
    total: int = 0


class RoleHomeAreaProgress(_TajiduoModel):
    id: str
    name: str
    total: int = 0


class RoleHomeRealEstate(_TajiduoModel):
    show_id: str = Field("", alias="showId")
    show_name: str = Field("", alias="showName")
    total: int = 0


class RoleHomeVehicle(_TajiduoModel):
    own_cnt: int = Field(0, alias="ownCnt")
    show_id: str = Field("", alias="showId")
    show_name: str = Field("", alias="showName")
    total: int = 0


class RoleHomeCharacter(_TajiduoModel):
    id: str
    name: str
    alev: int = 0
    awaken_lev: int = Field(0, alias="awakenLev")
    awaken_effect: List[str] = Field(default_factory=list, alias="awakenEffect")
    element_type: str = Field("", alias="elementType")
    group_type: str = Field("", alias="groupType")
    quality: str = ""
    slev: int = 0


class RoleHome(_TajiduoModel):
    role_id: str = Field("", alias="roleid")
    role_name: str = Field("", alias="rolename")
    server_id: str = Field("", alias="serverid")
    server_name: str = Field("", alias="servername")
    avatar: str = ""
    lev: int = 0
    world_level: int = Field(0, alias="worldlevel")
    tycoon_level: int = Field(0, alias="tycoonLevel")
    role_login_days: int = Field(0, alias="roleloginDays")
    charid_cnt: int = Field(0, alias="charidCnt")
    achieve_progress: Optional[RoleHomeAchieveProgress] = Field(None, alias="achieveProgress")
    area_progress: List[RoleHomeAreaProgress] = Field(default_factory=list, alias="areaProgress")
    realestate: Optional[RoleHomeRealEstate] = None
    vehicle: Optional[RoleHomeVehicle] = None
    characters: List[RoleHomeCharacter] = Field(default_factory=list)


class CharacterProperty(_TajiduoModel):
    id: str
    name: str
    value: str = ""


class CharacterSkillItem(_TajiduoModel):
    title: str = ""
    desc: str = ""


class CharacterSkill(_TajiduoModel):
    id: str
    name: str = ""
    type: str = ""
    level: int = 0
    items: List[CharacterSkillItem] = Field(default_factory=list)


class CharacterFork(_TajiduoModel):
    id: str = ""
    alev: str = ""
    blev: str = ""
    slev: str = ""
    properties: List[CharacterProperty] = Field(default_factory=list)


class CharacterSuit(_TajiduoModel):
    suit_activate_num: int = Field(0, alias="suitActivateNum")


class CharacterDetail(_TajiduoModel):
    id: str
    name: str
    alev: int = 0
    awaken_lev: int = Field(0, alias="awakenLev")
    awaken_effect: List[str] = Field(default_factory=list, alias="awakenEffect")
    element_type: str = Field("", alias="elementType")
    group_type: str = Field("", alias="groupType")
    quality: str = ""
    properties: List[CharacterProperty] = Field(default_factory=list)
    skills: List[CharacterSkill] = Field(default_factory=list)
    city_skills: List[CharacterSkill] = Field(default_factory=list, alias="citySkills")
    fork: CharacterFork = Field(default_factory=CharacterFork)
    suit: CharacterSuit = Field(default_factory=lambda: CharacterSuit(suitActivateNum=0))


class AchievementCategory(_TajiduoModel):
    id: str
    name: str
    progress: int = 0
    total: int = 0


class AchievementProgress(_TajiduoModel):
    achievement_cnt: int = Field(0, alias="achievementCnt")
    total: int = 0
    bronze_umd_cnt: int = Field(0, alias="bronzeUmdCnt")
    silver_umd_cnt: int = Field(0, alias="silverUmdCnt")
    gold_umd_cnt: int = Field(0, alias="goldUmdCnt")
    detail: List[AchievementCategory] = Field(default_factory=list)


class AreaDetailItem(_TajiduoModel):
    id: str
    name: str
    total: int = 0


class AreaProgress(_TajiduoModel):
    id: str
    name: str
    total: int = 0
    detail: List[AreaDetailItem] = Field(default_factory=list)


class Furniture(_TajiduoModel):
    id: str
    name: str
    own: bool = False


class House(_TajiduoModel):
    id: str
    name: str
    own: bool = False
    fdetail: List[Furniture] = Field(default_factory=list)


class Vehicle(_TajiduoModel):
    id: str
    name: str
    own: bool = False


class VehicleList(_TajiduoModel):
    detail: List[Vehicle] = Field(default_factory=list)
    own_cnt: int = Field(0, alias="ownCnt")
    show_id: str = Field("", alias="showId")
    show_name: str = Field("", alias="showName")
    total: int = 0


class GameSignState(_TajiduoModel):
    day: int
    days: int
    month: int
    re_sign_cnt: int = Field(0, alias="reSignCnt")
    today_sign: bool = Field(False, alias="todaySign")


class GameSignReward(_TajiduoModel):
    icon: str
    name: str
    num: int


class PostShareData(_TajiduoModel):
    title: str = ""
    content: str = ""
    image: str = ""


class NoticeImageRef(_TajiduoModel):
    url: str = ""


class NoticeVodRef(_TajiduoModel):
    cover: str = ""


class NoticePost(_TajiduoModel):
    post_id: int = Field(0, alias="postId")
    community_id: int = Field(0, alias="communityId")
    subject: str = ""
    create_time: int = Field(0, alias="createTime")
    author_name: str = Field("", alias="authorName")
    author_avatar: str = Field("", alias="authorAvatar")
    structured_content: str = Field("", alias="structuredContent")
    content: str = ""
    images: List[NoticeImageRef] = Field(default_factory=list)
    vods: List[NoticeVodRef] = Field(default_factory=list)


class _PostAuthor(_TajiduoModel):
    uid: int = 0
    nickname: str = ""
    avatar: str = ""


_EMPTY_POST_AUTHOR = _PostAuthor()


class RecommendPostList(_TajiduoModel):
    has_more: bool = Field(False, alias="hasMore")
    page: int = 0
    posts: List[NoticePost] = Field(default_factory=list)


class UserCoinTaskState(_TajiduoModel):
    today_get: int = Field(0, alias="todayGet")
    today_total: int = Field(0, alias="todayTotal")
    total: int = 0


class UserTask(_TajiduoModel):
    task_key: str = Field(alias="taskKey")
    title: str
    coin: int = 0
    exp: int = 0
    complete_times: int = Field(0, alias="completeTimes")
    cont_times: int = Field(0, alias="contTimes")
    limit_times: int = Field(0, alias="limitTimes")
    target_times: int = Field(1, alias="targetTimes")
    period: int = 0
    uid: int = 0

    @property
    def finished(self) -> bool:
        """已达当日上限。`limit_times` 是每日封顶次数，completeTimes 到此即停。"""
        return self.limit_times > 0 and self.complete_times >= self.limit_times

    @property
    def remaining(self) -> int:
        return max(0, self.limit_times - self.complete_times)


class UserTasks(_TajiduoModel):
    daily: List[UserTask] = Field(default_factory=list, alias="task_list1")
    achievement: List[UserTask] = Field(default_factory=list, alias="task_list2")

    def find_daily(self, task_key: str) -> UserTask | None:
        for task in self.daily:
            if task.task_key == task_key:
                return task
        return None


class NTENoticeType(IntEnum):
    INFO = 1
    ACTIVITY = 2
    NOTICE = 3

    @property
    def label(self) -> str:
        return {
            NTENoticeType.INFO: "资讯",
            NTENoticeType.ACTIVITY: "活动",
            NTENoticeType.NOTICE: "公告",
        }[self]


def _parse(model: type[BaseModel], data: Any, message: str) -> Any:
    try:
        if isinstance(data, list):
            return [model.model_validate(item) for item in data]
        return model.model_validate(data)
    except ValidationError as err:
        raise TajiduoError(f"{message}: {err}", data if isinstance(data, dict) else {}) from err


def _expect_dict(data: Any, message: str) -> dict:
    if not isinstance(data, dict):
        raise TajiduoError(message)
    return data


def _expect_dict_list(data: Any, message: str) -> list[dict]:
    if not isinstance(data, list):
        raise TajiduoError(message)
    result: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            raise TajiduoError(message)
        result.append(item)
    return result
