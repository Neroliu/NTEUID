from __future__ import annotations

import asyncio
from io import BufferedIOBase
from typing import Literal
from pathlib import Path
from threading import Lock
from collections import defaultdict

from pydantic import BaseModel, ConfigDict
from boltons.fileutils import atomic_save

from .adapters import tjd_to_archive
from .archive_model import NTEGachaPool, NTEGachaArchive
from ..utils.sdk.tajiduo_model import TajiduoGachaPool


class _LegacyArchive(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    uid: str
    updated_at: int
    pools: dict[str, TajiduoGachaPool]


class NTEGachaHistory:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._locks: defaultdict[str, Lock] = defaultdict(Lock)

    async def load(self, uid: str) -> NTEGachaArchive | None:
        return await asyncio.to_thread(self._read, uid)

    def _read(self, uid: str) -> NTEGachaArchive | None:
        if not uid.isascii() or not uid.isdecimal():
            raise ValueError("无效的游戏 UID")
        path = self._directory / f"{uid}.json"
        if path.exists():
            archive = NTEGachaArchive.model_validate_json(path.read_bytes())
        else:
            legacy_path = self._directory / "tajiduo" / f"{uid}.json"
            if not legacy_path.exists():
                return None
            legacy = _LegacyArchive.model_validate_json(legacy_path.read_bytes())
            archive = tjd_to_archive(legacy.uid, legacy.pools.values(), legacy.updated_at)
        if archive.uid != uid:
            raise ValueError("本地抽卡存档的 UID 不一致")
        return archive

    async def merge(self, snapshot: NTEGachaArchive) -> NTEGachaArchive:
        lock = self._locks[snapshot.uid]
        return await asyncio.to_thread(self._merge, snapshot, lock)

    def _merge(self, snapshot: NTEGachaArchive, lock: Lock) -> NTEGachaArchive:
        # 锁在工作线程内持有，查询协程取消后仍保护完整的读写事务。
        with lock:
            path = self._directory / f"{snapshot.uid}.json"
            stored = self._read(snapshot.uid)
            archive = snapshot.model_copy()
            archive.pools = stored.pools if stored is not None else {}

            for pool_type, pool in snapshot.pools.items():
                records = {record.key: record for record in pool.records}
                if pool_type in archive.pools:
                    for record in archive.pools[pool_type].records:
                        records.setdefault(record.key, record)
                archive.pools[pool_type] = NTEGachaPool(
                    records=sorted(records.values(), key=lambda record: record.time_ms, reverse=True)
                )

            self._directory.mkdir(parents=True, exist_ok=True)
            with atomic_save(str(path), overwrite_part=True) as output:
                assert isinstance(output, BufferedIOBase)
                output.write(archive.model_dump_json(indent=2).encode("utf-8"))

            return archive
