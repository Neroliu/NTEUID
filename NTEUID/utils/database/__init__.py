import json
from typing import Any, Dict, List, Type, TypeVar, Optional, cast
from datetime import datetime

from sqlmodel import Field, col, select
from sqlalchemy import delete, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from gsuid_core.webconsole.mount_app import PageSchema, GsAdminModel, site
from gsuid_core.utils.database.base_models import User, BaseIDModel, with_session

T_NTEUser = TypeVar("T_NTEUser", bound="NTEUser")
T_NTESignRecord = TypeVar("T_NTESignRecord", bound="NTESignRecord")

SIGN_KIND_APP = "app"
SIGN_KIND_GAME = "game"
SIGN_KIND_TASK_PREFIX = "task_"


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class NTEUser(User, table=True):
    """一行 = 塔吉多账号(center_uid) × 异环角色(uid) 的组合。

    同一个塔吉多账号有多个异环角色时存多行，`cookie` / `center_uid` / `dev_code`
    在同账号内是冗余相同的——签到时按 center_uid 分组，一次 refresh 复用于全部角色。
    账号尚未创建异环角色时允许 `uid=""` 占位，下次登录拉到真角色后会被清理。
    """

    __table_args__: Dict[str, Any] = {"extend_existing": True}
    cookie: str = Field(default="", title="refreshToken")
    uid: str = Field(default="", title="异环roleId")
    center_uid: str = Field(default="", title="塔吉多用户中心uid")
    role_name: str = Field(default="", title="角色名")
    game_id: str = Field(default="", title="游戏ID")
    dev_code: str = Field(default="", title="设备ID")
    laohu_token: str = Field(default="", title="laohuToken")
    laohu_user_id: str = Field(default="", title="laohu userId")
    auto_sign: str = Field(default="off", title="是否参与定时签到")
    access_token: str = Field(default="", title="accessToken 缓存")
    access_token_updated_at: Optional[datetime] = Field(default=None, title="accessToken 更新时间")
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
        title="更新时间",
    )

    @classmethod
    @with_session
    async def get_active(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ) -> Optional[T_NTEUser]:
        result = await session.execute(
            select(cls)
            .where(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                col(cls.cookie) != "",
                (col(cls.status).is_(None)) | (col(cls.status) == ""),
            )
            .order_by(col(cls.updated_at).desc())
            .limit(1)
        )
        return result.scalars().first()

    @classmethod
    @with_session
    async def list_latest_per_account(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ) -> List[T_NTEUser]:
        """每个 center_uid 只保留 updated_at 最新的一行（忽略 status）。
        "刷新全部令牌"用——同 center_uid 多角色共享 cookie/laohu_token，
        刷一次就够了，不用每个角色都跑一遍。"""
        result = await session.execute(
            select(cls)
            .where(cls.user_id == user_id, cls.bot_id == bot_id, col(cls.cookie) != "")
            .order_by(col(cls.updated_at).desc())
        )
        seen: set[str] = set()
        unique: List[T_NTEUser] = []
        for row in result.scalars().all():
            if row.center_uid not in seen:
                seen.add(row.center_uid)
                unique.append(row)
        return unique

    @classmethod
    @with_session
    async def list_active(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ) -> List[T_NTEUser]:
        result = await session.execute(
            select(cls)
            .where(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                col(cls.cookie) != "",
                (col(cls.status).is_(None)) | (col(cls.status) == ""),
            )
            .order_by(col(cls.updated_at).desc())
        )
        return list(result.scalars().all())

    @classmethod
    @with_session
    async def list_active_all(cls: Type[T_NTEUser], session: AsyncSession) -> List[T_NTEUser]:
        result = await session.execute(
            select(cls).where(
                col(cls.cookie) != "",
                (col(cls.status).is_(None)) | (col(cls.status) == ""),
            )
        )
        return list(result.scalars().all())

    @classmethod
    @with_session
    async def get_row(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        center_uid: str,
        uid: str,
    ) -> Optional[T_NTEUser]:
        result = await session.execute(
            select(cls).where(
                cls.user_id == user_id,
                cls.bot_id == bot_id,
                cls.center_uid == center_uid,
                cls.uid == uid,
            )
        )
        return result.scalars().first()

    @classmethod
    @with_session
    async def update_tokens(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        center_uid: str,
        refresh_token: str,
        access_token: str,
    ) -> None:
        """refresh 成功后写回两种 token + 更新 access_token_updated_at + 清空 status。
        `access_token_updated_at` 用来算 TTL 决定下次要不要再 refresh。"""
        await session.execute(
            update(cls)
            .where(col(cls.center_uid) == center_uid)
            .values(
                cookie=refresh_token,
                access_token=access_token,
                access_token_updated_at=datetime.now(),
                status="",
            )
        )

    @classmethod
    @with_session
    async def list_auto_sign(
        cls: Type[T_NTEUser],
        session: AsyncSession,
    ) -> List[T_NTEUser]:
        result = await session.execute(
            select(cls).where(
                col(cls.cookie) != "",
                (col(cls.status).is_(None)) | (col(cls.status) == ""),
                col(cls.auto_sign) == "on",
            )
        )
        return list(result.scalars().all())

    @classmethod
    @with_session
    async def set_auto_sign(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        on: bool,
    ) -> int:
        result = cast(
            CursorResult,
            await session.execute(
                update(cls)
                .where(col(cls.user_id) == user_id, col(cls.bot_id) == bot_id)
                .values(auto_sign="on" if on else "off")
            ),
        )
        return result.rowcount

    @classmethod
    @with_session
    async def delete_placeholders(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
        center_uid: str,
    ) -> int:
        result = cast(
            CursorResult,
            await session.execute(
                delete(cls).where(
                    col(cls.user_id) == user_id,
                    col(cls.bot_id) == bot_id,
                    col(cls.center_uid) == center_uid,
                    col(cls.uid) == "",
                )
            ),
        )
        return result.rowcount

    @classmethod
    @with_session
    async def delete_all(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        user_id: str,
        bot_id: str,
    ) -> int:
        result = cast(
            CursorResult,
            await session.execute(
                delete(cls).where(col(cls.user_id) == user_id, col(cls.bot_id) == bot_id),
            ),
        )
        return result.rowcount

    @classmethod
    @with_session
    async def mark_invalid_by_cookie(
        cls: Type[T_NTEUser],
        session: AsyncSession,
        cookie: str,
        reason: str,
    ) -> None:
        await session.execute(update(cls).where(col(cls.cookie) == cookie).values(status=reason))


class NTESignRecord(BaseIDModel, table=True):
    """签到明细 + 当日幂等。

    一次成功签到插入一行；存在即视为已签，避免重复调 API。`payload` 原样
    保留服务端返回的 JSON——关心"这次签了哪一项/拿到哪几样奖励"时读这里，
    不要在写入前把结构压平成几个数字字段。

    `ref_id` 对 App 签到是 `center_uid`，对游戏签到是 `roleId`；`kind` 取
    `SIGN_KIND_APP` / `SIGN_KIND_GAME`。社区子任务 `kind` 统一用
    `SIGN_KIND_TASK_PREFIX + task_key`（如 `task_like_post_c`），`ref_id` 仍是
    `center_uid`——落库后同日内整段短路，不再走远程 task 列表校验。
    """

    __table_args__: Dict[str, Any] = {"extend_existing": True}
    ref_id: str = Field(title="center_uid(app) 或 roleId(game)")
    kind: str = Field(title="签到类型")
    date: str = Field(default_factory=_today, title="签到日期")
    payload: str = Field(default="", title="签到返回原文(JSON)")

    @classmethod
    @with_session
    async def is_signed(
        cls: Type[T_NTESignRecord],
        session: AsyncSession,
        ref_id: str,
        kind: str,
        date: Optional[str] = None,
    ) -> bool:
        day = _today() if date is None else date
        result = await session.execute(
            select(cls).where(
                col(cls.ref_id) == ref_id,
                col(cls.kind) == kind,
                col(cls.date) == day,
            )
        )
        return bool(result.scalars().first())

    @classmethod
    @with_session
    async def get_record(
        cls: Type[T_NTESignRecord],
        session: AsyncSession,
        ref_id: str,
        kind: str,
        date: Optional[str] = None,
    ) -> Optional[T_NTESignRecord]:
        day = _today() if date is None else date
        result = await session.execute(
            select(cls).where(
                col(cls.ref_id) == ref_id,
                col(cls.kind) == kind,
                col(cls.date) == day,
            )
        )
        return result.scalars().first()

    @classmethod
    @with_session
    async def record(
        cls: Type[T_NTESignRecord],
        session: AsyncSession,
        ref_id: str,
        kind: str,
        payload: Optional[dict] = None,
        date: Optional[str] = None,
    ) -> None:
        day = _today() if date is None else date
        raw_payload = {} if payload is None else payload
        exists = await session.execute(
            select(cls).where(
                col(cls.ref_id) == ref_id,
                col(cls.kind) == kind,
                col(cls.date) == day,
            )
        )
        if exists.scalars().first():
            return
        session.add(
            cls(
                ref_id=ref_id,
                kind=kind,
                date=day,
                payload=json.dumps(raw_payload, ensure_ascii=False),
            )
        )

    @classmethod
    @with_session
    async def purge_before(
        cls: Type[T_NTESignRecord],
        session: AsyncSession,
        date: str,
    ) -> int:
        result = cast(
            CursorResult,
            await session.execute(delete(cls).where(col(cls.date) < date)),
        )
        return result.rowcount


@site.register_admin
class NTEUserAdmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(label="异环用户管理", icon="fa fa-users")  # type: ignore
    model = NTEUser


@site.register_admin
class NTESignRecordAdmin(GsAdminModel):
    pk_name = "id"
    page_schema = PageSchema(label="异环签到记录", icon="fa fa-calendar-check")  # type: ignore
    model = NTESignRecord
