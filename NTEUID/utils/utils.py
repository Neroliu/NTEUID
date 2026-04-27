from __future__ import annotations

import httpx

from .cache import timed_async_cache


@timed_async_cache(86400)
async def get_public_ip(host="127.127.127.127"):
    # 尝试从 kurobbs 获取 IP 地址
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://event.kurobbs.com/event/ip", timeout=4)
            ip = r.text
            return ip
    except Exception:
        pass

    # 尝试从 ipify 获取 IP 地址
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://api.ipify.org/?format=json", timeout=4)
            ip = r.json()["ip"]
            return ip
    except Exception:
        pass

    # 尝试从 httpbin.org 获取 IP 地址
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://httpbin.org/ip", timeout=4)
            ip = r.json()["origin"]
            return ip
    except Exception:
        pass

    return host
