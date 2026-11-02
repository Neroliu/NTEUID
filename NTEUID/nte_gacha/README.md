# NTEUID 抽卡存档格式 v1

官方接口数据转换成 NTEUID 存档模型后，统一去重、合并并保存。展示从合并后的存档生成。接口或令牌刷新失败时读取本地存档；没有本地记录时返回原错误。

## 文件格式

每个游戏 UID 保存为 `data/NTEUID/gacha/<uid>.json`。v1 接收塔吉多官方源，只记录已出 S 的物品及对应抽数。

```json
{
  "format": "nteuid-gacha",
  "version": 1,
  "uid": "123456789012",
  "source": "tajiduo",
  "updated_at": 1793605628,
  "pools": {
    "permanent": {
      "records": [
        {"item_id": "1039", "time_ms": 1787317673012, "pity": 1},
        {"item_id": "1039", "time_ms": 1787317673012, "pity": 54}
      ]
    }
  }
}
```

| 字段 | 约定 |
|---|---|
| `format` / `version` | 固定为 `nteuid-gacha` / `1` |
| `uid` | 游戏 UID，数字字符串 |
| `source` | 固定为 `tajiduo` |
| `updated_at` | 最近一次成功获取接口数据的 Unix 秒时间戳；读取本地时保持原值 |
| `pools` | 卡池标识到明细的映射；`limited` 为限定池，`permanent` 为常驻池，`weapon` 为弧盘池 |
| `item_id` | 官方物品 ID，角色为数字字符串，弧盘为 `fork_*` |
| `time_ms` | 抽中时间的 Unix 毫秒时间戳，必须保留毫秒精度 |
| `pity` | 本次出 S 所用抽数，至少为 1 |

## 合并与统计

- 同一 UID、同一卡池内，以 `(item_id, time_ms, pity)` 作为去重键。
- 新记录与本地记录取并集，按 `time_ms` 降序排列。接口缺少某条记录或整个卡池时保留本地记录。
- 本地记录不按时间过期。只有保存过的记录能在官方过期后继续保留。
- JSON 只存明细。池级 `draw_count` 为全部 `pity` 之和，`s_count` 为记录数，`average` 为 `draw_count / s_count`；空池平均值为 0。
- 总抽数只覆盖已出 S 的区间，不包含当前未出 S 的垫抽。展示的平均抽数取整数部分，运气称号由累计抽数和 S 数计算。
- 物品名称从资源表查询。`playerOver`、官方运气称号、头像、登录凭据等不写入标准存档。
- 同一 UID 的合并写入串行执行，文件采用原子替换。

## 读取与迁移

读取时优先使用标准存档。标准存档不存在时，读取 `data/NTEUID/gacha/tajiduo/<uid>.json` 并转换成标准模型；下次接口查询成功后保存到标准路径，原文件保留。UID 不匹配或文件格式错误时停止处理，不覆盖文件。

文件格式和字段语义由本协议确定。当前入口为官方源查询，本模块暂不提供导入导出命令。
