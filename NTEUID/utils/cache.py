import time
import asyncio
import inspect
from typing import Any, TypeVar, ParamSpec
from weakref import WeakValueDictionary
from functools import wraps
from collections import OrderedDict
from collections.abc import Callable, Awaitable, MutableMapping

P = ParamSpec("P")
R = TypeVar("R")

AsyncCacheKey = tuple[tuple[str, str], ...]


def _now() -> float:
    # 单调时钟不受系统时间校准影响，适合做 TTL 判断。
    return time.monotonic()


class TimedCache:
    def __init__(self, timeout: float = 300.0, maxsize: int = 32) -> None:
        if timeout < 0:
            raise ValueError("TimedCache timeout must be >= 0")
        if maxsize <= 0:
            raise ValueError("TimedCache maxsize must be > 0")

        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._timeout = timeout
        self._maxsize = maxsize

    def set(self, key: str, value: Any) -> None:
        self._sweep()

        if key in self._store:
            # 更新已有 key 不会增加容量，不应该触发 LRU 淘汰。
            self._store.move_to_end(key)
        else:
            while len(self._store) >= self._maxsize:
                self._store.popitem(last=False)

        self._store[key] = (value, _now() + self._timeout)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None

        value, expire_at = entry
        if expire_at <= _now():
            self._store.pop(key, None)
            return None

        self._store.move_to_end(key)
        return value

    def pop(self, key: str) -> Any | None:
        entry = self._store.pop(key, None)
        if entry is None:
            return None

        value, expire_at = entry
        if expire_at <= _now():
            return None
        return value

    def _sweep(self) -> None:
        now = _now()
        expired_keys = [key for key, (_, expire_at) in self._store.items() if expire_at <= now]
        for key in expired_keys:
            self._store.pop(key, None)


def timed_async_cache(
    expiration: float,
    condition: Callable[[R], bool] = bool,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    if expiration < 0:
        raise ValueError("timed_async_cache expiration must be >= 0")

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        sig = inspect.signature(func)
        cache: dict[AsyncCacheKey, tuple[R, float]] = {}
        locks: MutableMapping[AsyncCacheKey, asyncio.Lock] = WeakValueDictionary()

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # key 绑定完整调用参数，避免同一函数不同参数串用缓存。
            key = _async_cache_key(sig, args, kwargs)
            now = _now()

            hit = cache.get(key)
            if hit is not None and now - hit[1] < expiration:
                return hit[0]

            lock = locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                locks[key] = lock

            async with lock:
                # 进入锁后重新取时间，避免排队期间用旧时间判断缓存有效期。
                now = _now()
                hit = cache.get(key)
                if hit is not None and now - hit[1] < expiration:
                    return hit[0]

                value = await func(*args, **kwargs)
                if condition(value):
                    cache[key] = (value, now)
                return value

        return wrapper

    return decorator


def _async_cache_key(sig: inspect.Signature, args: tuple[Any, ...], kwargs: dict[str, Any]) -> AsyncCacheKey:
    # bind 让 f(1) 和 f(x=1) 得到同一个 key；repr 让 list/dict 这类不可哈希参数也能参与 key。
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return tuple((name, repr(value)) for name, value in bound.arguments.items())
