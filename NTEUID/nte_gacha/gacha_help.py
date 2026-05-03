from __future__ import annotations

from ..utils.constants import TAPTAP_BIND_GUIDE_URL
from ..nte_config.prefix import nte_prefix


async def draw_gacha_help() -> list[str]:
    """异环抽卡记录帮助；简洁分块返回。"""
    p = nte_prefix()

    notice = "\n".join(
        [
            "⚠️⚠️⚠️ 重要警告（TapTap 侧限制，非本插件问题）",
            "",
            "· 异环角色一旦在 TapTap 绑定到某个 TapTap 账号，基本上就【永久绑死】在那个账号上",
            "· TapTap 不提供解绑、也不提供换绑，相当于这个异环角色与该 TapTap 账号一对一锁死；",
            "· 务必、务必、务必想清楚再绑。一旦绑下去无法回头，损失自负。",
        ]
    )

    get_uid = "\n".join(
        [
            "1. 获取 TapTap user_id",
            "",
            "网页登录后访问：",
            "https://accounts.taptap.cn/personal-info",
        ]
    )

    bind_game = "\n".join(
        [
            "2. 在 TapTap 绑定异环角色",
            "",
            TAPTAP_BIND_GUIDE_URL,
            "（按页面提示完成绑定并分享一次战绩）",
        ]
    )

    refresh = "\n".join(
        [
            "3. 刷新数据",
            "",
            "登录 TapTap 后访问同上链接，点击『更新数据』按钮。",
        ]
    )

    bind_bot = "\n".join(
        [
            "4. 绑定到 Bot",
            "",
            f"发送：{p}绑定tap<tapid>",
            f"例如：{p}绑定tap12345",
        ]
    )

    query = "\n".join(
        [
            "5. 查询抽卡记录",
            "",
            f"发送：{p}抽卡记录",
        ]
    )

    return [notice, get_uid, bind_game, refresh, bind_bot, query]
