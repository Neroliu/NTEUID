from __future__ import annotations

import re

from .gacha_model import (
    NTEGachaItem,
    NTEGachaSection,
    NTEGachaSummary,
    NTEGachaOverview,
)
from ..utils.sdk.taptap_model import GachaSummary as TaptapGachaSummary
from ..utils.sdk.xiaoheihe_model import LotteryAnalysis

_IMG_ID_RE = re.compile(r"/icon/(\d+)\.png$")


def tap_to_nte(summary: TaptapGachaSummary) -> NTEGachaSummary:
    overview = (
        NTEGachaOverview(
            total_pull_count=summary.overview.total_pull_count,
            total_ssr_count=summary.overview.total_ssr_count,
            banner_count=summary.overview.banner_count,
            banner_type_count=summary.overview.banner_type_count,
        )
        if summary.overview is not None
        else None
    )

    sections = [
        NTEGachaSection(
            banner_id=sec.banner_id,
            banner_name=sec.banner_name,
            total_pull_count=sec.total_pull_count,
            ssr_count=sec.ssr_count,
            avg_pity=sec.avg_pity,
            items=[
                NTEGachaItem(
                    item_id=item.item_id,
                    item_name=item.item_name,
                    # TapTap 不提供单 item 保底差值，用 section 平均值兜底
                    pity=sec.avg_pity,
                    pull_time_ts=item.pull_time_ts,
                )
                for item in sec.items
            ],
        )
        for sec in summary.sections
    ]

    return NTEGachaSummary(
        overview=overview,
        sections=sections,
        last_updated_ts=summary.last_updated_ts,
    )


def xhh_to_nte(analysis: LotteryAnalysis) -> NTEGachaSummary:
    si = analysis.statistic_info
    total_ssr = sum(p.ssr for p in si.pool_stats)
    total_pull = si.total_limit_cost + si.total_permanent_cost + si.total_fork_cost

    overview = NTEGachaOverview(
        total_pull_count=total_pull,
        total_ssr_count=total_ssr,
        banner_count=sum(1 for p in si.pool_stats if p.cost > 0),
        banner_type_count=len(si.pool_stats),
    )

    pool_cost_map: dict[str, int] = {}
    for p in si.pool_stats:
        pool_cost_map[p.pool] = p.cost
        pool_cost_map[p.pool.strip()] = p.cost

    sections = [
        NTEGachaSection(
            banner_id=str(pool.pool_key),
            banner_name=pool.pool_type,
            total_pull_count=pool_cost_map.get(pool.pool_type, pool_cost_map.get(pool.pool_type.strip(), 0)),
            ssr_count=len(pool.records),
            avg_pity=int(
                float(pool_cost_map.get(pool.pool_type, pool_cost_map.get(pool.pool_type.strip(), 0)))
                / max(len(pool.records), 1)
            ),
            items=[
                NTEGachaItem(
                    item_id=(m.group(1) if (m := _IMG_ID_RE.search(r.img)) else r.name),
                    item_name=r.name,
                    pity=r.diff,
                    pull_time_ts=r.timestamp,
                )
                for r in pool.records
            ],
        )
        for pool in analysis.gacha_record
    ]

    return NTEGachaSummary(
        overview=overview,
        sections=sections,
        last_updated_ts=analysis.update_time,
    )
