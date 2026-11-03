# 黑百合 Shift 抓钩与 E 剧毒诡雷（2026-10-24）

原版负责按键判定、手部动画、冷却与 HUD；原版里本该由服务端处理的钩索判定、诡雷飞行/黏附/触发/毒伤，
这里没有服务端，由 MC 补上。只读取原版状态，不新增原生 hook、回调或写内存。

## 原版校准

- 校准脚本 `research/sprint-20261024/calibrate_widow_kit.py`，结果 `widow-kit-calibration2`、`-calibration5`。
- 抓钩：graph `058000000000005a`（91 节点）。StateStack81 开始施放；DataFlowMapping57 覆盖整个施放（约 1.26 s）；
  StateAnim61 在 +150 ms 开始发射动画。MC 以 61 的新 Begin 作为一次施放。
- 诡雷：graph `0580000000000056`（27 节点）。State24 覆盖施放（约 1 s）；WeaponVolley1 在 +200 ms 同一 tick 开始并结束，
  即投掷瞬间。节点13 是发给服务端的游戏消息。发射物工厂没有捕获（0 个），所以诡雷本体由 MC 生成。
- 原版齐射声明（`tools/verify/inspect_native_venom.py` → `widow-venom-declarations.json`）：投射物实体 `04000000000000af`，
  速度 20 m/s，寿命 5 s，射程 100，重力 9.8 m/s²。伤害不在齐射节点上（在诡雷实体自身逻辑里）。

## MC 实现

- 绑定：`tools/prepare_native_grapple.py` 为当前黑百合写出 `native-grapple-request-PID.json` 与
  `native-venom-request-PID.json`；`launch_passthrough_session.py` 在英雄为黑百合时调用。
- 抓钩：`NativeGrappleController` + `WidowGrapplePull`。20 格内真实方块射线；命中则每 tick 1.1 格拉向锚点，
  1.4 格内到达、1.6 s 超时或连续 3 tick 卡住即松开并保留部分动量；勾到可翻越的边缘时给一个上翻速度。未命中不拉。
- 诡雷：`NativeVenomRuntime`（服务端）。按原版 20 m/s 与 9.8 m/s² 抛物线飞行，5 s 未粘住则消失；粘到方块后，
  3 格内有视线的非玩家生物触发引爆；毒伤按 2015 测试版 75 伤害 / 5 秒，乘项目 `HP_SCALE` 0.1，即每秒 1.5、共 7.5。
  每人只保留一颗，再扔替换旧的。
- 原版模型：`tools/venom_mine_assets.py` 从本机离线 24919 档案提取网格 `0d000000000006f2`（1079 顶点 / 1236 三角，
  多个刚性单骨骼部件，按绑定姿态绘制）、Look `0980000000000605` → 材质 `0e00000000001b37` → 颜色贴图 `0c…1427`
  （BC3 sRGB）与发光遮罩 `0c…1428`（BC4）。档案读取链见 `research/sprint-20261024/read_venom_assets.py`；
  通用贴图解码 `tools/ow_beta_texture.py`（BC1 4+4、BC3 2+6+4+4、BC4 2+6 平面布局，按邻域平滑度实测确定）。
  发光遮罩的紫色是 MC 呈现用的着色，原版着色器颜色未解码。原始素材与产物只在 `~/.universal-modder/assets/` 私有目录。
  `VenomMineRenderer` 校验哈希后绘制，底面贴合命中面。

## 实测（`research/sprint-20261024/widow-live3`）

`tools/dev_cycle.sh` 冷构建安装 `c40a27ee…` 后运行 `verify_widow_kit.py`，通过并清理干净：
- 诡雷：扔 1、粘住 1、引爆 1、毒伤 5 次，村民 20 → 12.5（−7.5）；渲染器 335 帧，无错误。
- 抓钩：施放 1、命中 1、到达 1，玩家移动 9.23 格。原版 HUD 显示 15 秒 Shift 冷却。
- 截图 `venom-stuck.jpg` 中 10 格外的诡雷只有几个像素，近距离外观尚未目视确认。

## 未完成

- 抓钩没有 MC 侧的绳索/钩爪画面（原版世界里的绳索在隐藏的 OW 地图中）；翻越边缘未专门测试。
- 诡雷近距离外观、多维度、换英雄中途、死亡时清理仍待单独验证。
