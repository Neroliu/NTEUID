from ..utils.constants import (
    XIAOHEIHE_WEB_URL,
    TAPTAP_BIND_GUIDE_URL,
    TAPTAP_PERSONAL_INFO_URL,
)
from ..nte_config.prefix import nte_prefix


async def draw_gacha_help() -> list[str]:
    p = nte_prefix()

    return [
        "\n".join(
            [
                "⚠️ 前置条件（二选一，必须先完成）",
                "",
                f"· TapTap：需先在战绩页绑定异环角色（{TAPTAP_BIND_GUIDE_URL}）",
                "· 小黑盒：需先在小黑盒内绑定异环角色",
            ]
        ),
        "\n".join(
            [
                "1. 绑定 TapTap（推荐，操作简单，支持换绑）",
                "",
                f"① 在 TapTap 绑定异环角色：{TAPTAP_BIND_GUIDE_URL}",
                "",
                f"② 获取 TapTap user_id：{TAPTAP_PERSONAL_INFO_URL}",
                "",
                f"③ 发送：{p}绑定tap <tapid>",
                "",
                "④ 刷新数据：回到战绩页点击『更新数据』按钮",
            ]
        ),
        "\n".join(
            [
                "2. 绑定小黑盒（备选，pkey 会过期）",
                "",
                f"① 网页登录小黑盒：{XIAOHEIHE_WEB_URL}",
                "",
                "② 按 F12 打开开发者工具 → Application/Storage → Cookies → api.xiaoheihe.cn",
                "   （中文浏览器：应用程序/存储 → Cookie → api.xiaoheihe.cn）",
                "   找到 user_pkey 的值并完整复制",
                "",
                f"③ 发送：{p}绑定小黑盒 <user_pkey>",
            ]
        ),
        "\n".join(
            [
                "3. 查询抽卡记录",
                "",
                f"发送：{p}抽卡记录",
            ]
        ),
    ]
