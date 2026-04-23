from __future__ import annotations

from datetime import datetime

from .database import NTEUser
from .constants import ACCESS_TOKEN_TTL_SECONDS
from .sdk.tajiduo import TajiduoClient


async def ensure_tajiduo_client(user: NTEUser) -> TajiduoClient:
    """返回已带可用 access_token 的 TajiduoClient。
    DB 里 `access_token` 未过 TTL 时直接复用，零网络；超 TTL 或无缓存时
    调一次 `refresh_session` 并把新 token 落库。refresh 失败（TajiduoError）
    透传给调用方——业务层决定 mark_invalid + LOGIN_EXPIRED 的处理。"""
    client = TajiduoClient.from_user(user)
    if _access_token_fresh(user):
        client.access_token = user.access_token
        return client

    session = await client.refresh_session()
    await NTEUser.update_tokens(
        center_uid=user.center_uid,
        refresh_token=session.refresh_token,
        access_token=session.access_token,
    )
    return client


def _access_token_fresh(user: NTEUser) -> bool:
    if not user.access_token or user.access_token_updated_at is None:
        return False
    age = (datetime.now() - user.access_token_updated_at).total_seconds()
    return age < ACCESS_TOKEN_TTL_SECONDS
