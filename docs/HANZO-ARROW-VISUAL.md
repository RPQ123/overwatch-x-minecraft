# 半藏箭矢可见性、蓝光与近距离取帧（2026-10-25）

本轮延续已由 Claude 接好的 `NativeCombatRuntime present/publish/reset`。未开游戏、未构建部署 JAR、未安装素材。
`compileClientJava` 和两个呈现生命周期 fixture 的结果写在 `research/hanzo-arrows-visual-20261025/checks.json`。
普通箭/音波箭/散射母子箭的实际合成画面仍需 Claude 运行下述脚本核验；数值/编译通过不能替代用户可见性验收。

## 已核对的问题

`batch-hanzo2-hanzo-full/result.json` 中：普通箭主体累计18帧，音波主体38帧，散射子箭在 Scatter 步累计2508帧；全部 renderer errors=0。
普通/音波的 `hanzoArrowEmbedded=0`，散射 `embeddedArrows=0`，因此那次 `stuckFrames=0` 没有证明插墙渲染坏了。
旧脚本在目标正中射击后才启动独立截图命令，近距离箭早已撞到实体；真实飞行只有约十分之一秒，后截图不能用于判断飞行箭是否清楚。

实际原版 b8d 选定部件与试打包数据尺寸一致：

| 箭 | 原版长度（m） | 最大横向尺寸 | 选定三角形 | 本轮主体缩放 |
|---|---:|---:|---:|---:|
| 普通 | 0.951061 | 约0.063m | 1390 | 1 |
| 音波 | 0.900803 | 约0.069m | 1748 | 1 |
| 散射母/子 | 0.881597 | 约0.063m | 1312 | 1 |

不是只画了箭杆：普通/音波/散射分别保留头部0/3/2，加共用箭杆1、尾羽4。
长轴仍为 +Z，按实际扫段/散射 velocity 旋转，箭尖贴实际接触点；主体仍是 `getEntityCutoutNoCull`，并未引入背面剔除或扩大模型。
顺着射击轴观察，约6厘米尾羽会只有数像素；原版的可读性还依赖发光/拖尾，不能只用不发光的棕色主体代替。
主体保留真实世界 lightmap；新光迹用已有原版火箭也采用的 `RenderLayer.getEyes` 加色、非 lightmap 光照层，满光 `0x00f000f0`。
新增诊断保留 `lastBodyLight`、`fxLight`、各箭长度与 `bodyScale=1`，供实测检查。

本轮还修正 UV：原版 0801 星芒片的4个 UV 角都是0/1，原先通用 `fract` 操作会把四角全部变成(0,0)。
新 FX 加载器和箭主体都保留原始 UV，不能把粒子片取到透明角落后再用增大模型补救。

## 原版光效来源

使用本机已修好的 `ow_asset_chain.py` 重新提取6个强/弱箭实体；新版 flat-effect 解析已能读出原先标 unsupported 的 trail 表。

| 呈现 | 原版来源 | 模型 / 材质 | 实际贴图与处理 |
|---|---|---|---|
| 普通箭星芒 | 0144 → 024c | 0801 / `0e0000009537fc6e` | `0c000000000012d1`，原版RGBA蓝星芒 |
| 普通箭拖尾 | 0144/020b → 02db | 075d / `0e00000098d4b643` | `0c00000000000ac4`，BC4强度，颜色变量 `b607dd55` 未解 |
| 音波箭星芒/粒子尾迹 | 0149/020d → 01b9 → 0244 | 0801 / `0e0000006966f477` | `0c00000000000242`，BC4强度，颜色变量 `293f6f18` 未解 |
| 散射母/子星芒 | 01a4 → 024f、020c → 0252 | 0801 / `0e0000002ded6c3b` | 原版RGBA蓝星芒12d1，强/弱共同拥有此材质；母箭与六子箭都画 |
| 散射母/子拖尾 | 01a4/020c → 0246 | 075d / `0e000000181b690c` | 原版BC4强度0ac4，颜色变量 `559bf044` 未解 |

上表模型完整 GUID：0801=`0d00000000000801`（8顶点/4三角形原版双面片），075d=`0d0000000000075d`（18顶点/16三角形原版交叉拖尾网格）。
0246 另有075d/5131665d与099f/c41c6344；099f的0c96为BC5法线/数据图，本轮没有把它冒充颜色或强度图。
024f/0252 还携带红色2dad星芒，本机玩家自己的箭选蓝色12d1，不把红贴图涂成蓝色再声称原样提取。

蓝星芒直接使用原版颜色。BC4强度图需动态颜色，本轮未解这些变量：
采用12d1可见蓝色像素的RGB均值约(13.4,23.0,195.3)，归一化为(18,30,255)，明确标**颜色近似**。
BC4的R同时用于alpha与预乘RGB，加色时黑背景不发光；不画铁块/灰色回退材质。
075d沿实际已扫过的段映射，不产生第二套弹道。音波链没有确认独立075d拖尾，故在真实历史采样点画其原版0244粒子片。
发光片宽 .16/.20m、尾迹宽 .045m及.12m淡外晕、120ms尾迹、80ms接触余辉均为显式呈现近似；原版emitter尺寸曲线/时序未执行。
反弹只由真实加载方块接触产生短蓝星芒余辉；尚未确认独立“反弹闪光”原版renderer，不声称复刻了原版完整撞击effect。
相机附近 .5m 只裁剪光迹几何，避免在眼点生成覆盖视野的星芒；箭矢物理/伤害不变。

## 打包（Claude）

```powershell
.venv/Scripts/python.exe tools/assets/prepare_hanzo_arrow_assets.py --extract
.venv/Scripts/python.exe tools/build_mesh_pack.py --batch research/hanzo-arrows-20261025/mesh-jobs.json
```

当前本机原始链已重新提取，第一条可省 `--extract`。
batch现在含原先5包与新增5包：`hanzo-arrow-primary-glow`、`hanzo-arrow-primary-trail`、`hanzo-arrow-sonic-glow`、`hanzo-arrow-scatter-glow`、`hanzo-arrow-scatter-trail`。
对应单包命令：

```powershell
.venv/Scripts/python.exe tools/build_mesh_pack.py hanzo-arrow-primary-glow 0400000000000144 --model 0d00000000000801 --material 0e0000009537fc6e
.venv/Scripts/python.exe tools/build_mesh_pack.py hanzo-arrow-primary-trail 0400000000000144 --model 0d0000000000075d --material 0e00000098d4b643
.venv/Scripts/python.exe tools/build_mesh_pack.py hanzo-arrow-sonic-glow 0400000000000149 --model 0d00000000000801 --material 0e0000006966f477
.venv/Scripts/python.exe tools/build_mesh_pack.py hanzo-arrow-scatter-glow 04000000000001a4 --model 0d00000000000801 --material 0e0000002ded6c3b
.venv/Scripts/python.exe tools/build_mesh_pack.py hanzo-arrow-scatter-trail 04000000000001a4 --model 0d0000000000075d --material 0e000000181b690c
```

本轮只在 `research/hanzo-arrows-visual-20261025/validation-packs` 试打包10包；全部数组/索引/PNG/文件哈希通过。
`asset-validation.json` 保存尺寸、材质、PNG统计与UV退化对照。游戏素材、视频、图片和试包继续留在忽略目录，不提交。

## 源码与共享登记

新增 `HanzoArrowEffects`、`HanzoArrowFxMesh`、`HanzoArrowVisualLab`、`HanzoArrowEffectsCheck`。
更新自己的 `HanzoArrowPresentation`/`HanzoArrowRenderer`/`HanzoArrowMesh` 与素材准备脚本；仅在 `NativeHanzoSkillRuntime` 的散射段加真实扫段/反弹呈现回执。
龙tick与三个共享类的备份哈希比较通过；不改 `NativeCombatRuntime`、`NativeShotSimulation`、`WorldFrameExporter`。
已有的 `HanzoArrowRenderer.register()` 和 present/publish/reset 接线继续使用，**不需要再加一套 combat 回调**。

Claude 在 `WorldFrameExporter` 原诊断区加：

```java
diagnostic.add("hanzoArrowFx",HanzoArrowRenderer.diagnostics());
diagnostic.add("hanzoArrowVisualLab",com.google.gson.JsonParser.parseString(HanzoArrowVisualLab.status));
```

在现有 `combat/test` switch 增加：

```java
case "hanzo-arrows-visual" -> HanzoArrowVisualLab.start(server,owner,forward);
```

在现有 `cleanup` 分支中、`NativeCombatScene.cleanup()` **之前**调用 `HanzoArrowVisualLab.cleanup();`；
现有 server-stopping 清理分支也调用同一方法，以便正常停止时先撤回测试墙。
场景复用原有 ground/mei lab 的地板与普通村民；只在原为空气的位置添加自有石墙。
墙10m，目标约11.02m且偏离射线中心，在墙后侧；不会让实体先吃掉中心箭而伪装成“插墙失败”。
场景准备会清空此前私有音波视觉状态，避免上一行的球体遮住下一行散射截图；不改原版冷却或任何真实伤害。

`hanzoArrowFx` 关键诊断：`glowFrames`、`trailFrames`、`scatterParentGlowFrames`、`scatterChildGlowFrames`、`bounceGlowFrames`、`bounces`、`contacts`、`errors/error`。
另有当前帧在飞/插墙模型数量、当前帧时间、各箭最后一次真实飞行渲染时间、最后反弹余辉时间、主体长度/光照。
这些时间来自成功绘制主体/真实接触余辉，避免把过去累计帧数误当作当前仍在飞行。

## 近距离验证脚本

`research/sprint-20261024/verify_hanzo_arrows_visual.py` 已写入并做语法、CLI检查；本轮没有运行实机部分。
Claude 完成上述登记、部署后，用新的实际身份运行：

```powershell
.venv/Scripts/python.exe research/sprint-20261024/verify_hanzo_arrows_visual.py --pid <原版PID> --created <原版创建时间> --mc-pid <MC_PID> --mc-created <MC创建时间> --world "<实际独立世界名>" --guest-sha256 <安装JAR_SHA256> --output research/sprint-20261024/hanzo-arrows-visual-live1
```

不启动游戏、不发Q、不补造攻击。使用现有Suite的进程身份/SHA/六owner/前台干扰检查，先复制实际 `--gameDir` 的配置、JAR和当前磁盘存档。
每一行重新准备10m场景，先连续WGC120fps录制，再由真实普通蓄力释放/Shift释放/E释放产生箭。
原版普通/音波行取flight、impact、stuck；散射行取flight、bounce、stuck，共9张中心裁剪图，JPEG quality80、长边≤768。
插墙时短暂侧移250ms，以观察原长箭杆，不放大模型；墙与目标仍在8–12m量级。
最终 `hanzo-arrows-visual-sheet.jpg` 为1020×630；临时拆帧图在脚本结束自动回收，原视频与选定9图留作证据。
选帧参考真实客户端阶段时间、蓝色像素变化；Recorder起帧时间仍有测量误差，result里保留这一限制，必须人工检查选中阶段。
没有对应真实阶段计数时输出缺失格，不用事后空场景替代“飞行图”。`visualAccepted` 永远不会由计数自动设为true。
现有 finally 路径撤墙/目标/地板；恢复时保留外部修改的方块，并报告未恢复的已卸载块，不能把未清理标成功。

## 2026-10-26 第二轮 hanzo：原版蓄力上下文与插墙/反弹断言

本节为本轮新增交接。Claude 已接好旧版视觉、10包、场景、诊断和 `hanzo-visual` 键；本轮不重复登记它们。
不开游戏、不运行实机脚本、不构建部署JAR。只读环境检查通过；编译、离线fixture结果见 `research/hanzo-scatter-context-20261026/checks.json`。

### 原版证据与可用性边界

找到 `hanzo-scatter-calibration1/result.json` 同一次出手中的真实记录：

- b9已构造bag：typed `2a5=1`、`1dc=125`、`980=75`，均为numeric vtable RVA1608248、type3。
- 同owner的原版01a4工厂：90m/s、10s、300m、status8/type1/result0；factory tick1286。
- 同一b9:26节点：logger nativeTick20576，恰好等于1286×16。
- `final-secondary-expressions.json` 的**另一份空闲快照**确实曾读不到980，不能据此把所有出手都判为无980；也不能把这份成功历史数据用作新会话常量。

这些是历史原版证据，本轮没有实时读游戏。原版子箭服务端轨迹/表面响应oracle仍未完成。
`evaluatedDamage=0` 继续完全不采用；它来自未绑定Scatter的诊断行，不是伤害值。

### 条件参数接线

新增 `HanzoScatterContext`、`HanzoScatterContextReader`、`tools/prepare_hero_hanzo_scatter.py`。
现有启动器会自动发现 `HERO + prepare(process,pid)`，无需改launcher；准备脚本只写本机read-only request，**不会启用校准或加载native owner**。
它复用原来的hanzoSkills owner binding，核对parent/child资源、重力/寿命/范围、原版表达式字节码/常量/变量路径及b9:84赋值目标980。
准备时读到的数值仅作 `prepareSample`，标 `runtimeReuse=false`；每次实际出手必须重新读取。

仅在原有b9:26新tick已经触发时读取参数：

1. 核对当前PID、创建时间、host generation、model、script/graph/bag与原版声明字节；只读句柄无写内存权限。
2. 原始logger tick须稳定，匹配工厂tick×16和本次Volley token；工厂header/行≤150ms、status8/type1/result0、10s/300m。
3. 从当前bag重扫16个bucket，唯一typed读取原版2a5、1dc、980；两次采样的值和对象地址必须相同，前后再核owner/node/声明。
4. 检查q∈[0,1]、工厂speed≈25+65q、980≈15+60q；**不从speed、蓄力按键时长或过去工厂反推q**。
5. 使用工厂真实direction×speed作为母箭velocity，typed1dc作为母箭伤害；按锁定字节码求子速 `.800000011920929*(20+65*q)`，typed980作为子伤害。六支子箭继承同次参数。

离线fixture覆盖q=0/.5/1：母速25/57.5/90、子速约16/42/68，子伤害15/45/75；母伤害直接读1dc，不由速度推算。
新参数只是丰富既有节点准入，不从factoryObservations额外制造攻击，不向共用armory增加Scatter伤害准入。
分布20°环、反弹、碰撞策略和现有重力积分仍沿用此前MC适配；字节码求值不等于子箭轨迹已实机还原。

缺任一字段、scope/新鲜度不符、数值不一致、同tick工厂不唯一或参数transport关闭时，**整组保留现值**：
母速90、子速52m/s、母/子伤害75HP，q缺失，`scatterContext.nativeValues=false`，附具体 `reason`。
不回填历史q，不把0伤害代入，不在已经飞行/分裂后补改参数。
现有emission16只在 `factoryCalibration` 开启时写工厂观察行；普通生产通道默认关闭时预期回退，这一点没有暗中改变。
若后续要求普通游玩始终采用原版上下文，主线程仍需决定如何在现有认证提交中长期发布这些参数；本轮不改native DLL、journal或共用模拟器。

`hanzoSkills` 新诊断无需共享登记：`scatterNativeContexts`、`scatterFallbackContexts`、`scatterContext`（q、原始velocity、母/子速度伤害、factory identity、reason）、`scatterChildrenCreated`。

### 插墙与反弹实测路径

更新 `HanzoArrowVisualLab`：保留10m墙与约11.02m偏心目标，在前方4–10m、7格宽、脚底高度补真实接箭地板。
旧场景仅玩家脚下有地板，朝下子箭可能直接飞入空中，不能保证近距离反弹；新地板用于让两支朝下子箭产生真实扫碰撞。
地板低于母箭路径，不把慢速母箭提前挡成插地；只补空气，保留已有实体方块；新增部分同墙一起按原状态回收。

`verify_hanzo_arrows_visual.py` 已加入：

- 墙面锚点实际坐标、成功绘制≥3帧、跨≥10个server tick仍原地，expiresTick恒定且剩余≤200tick。
- 普通/音波用真实wall-impact锚点；散射只取母箭墙面锚点，不拿子箭插地冒充插墙。
- Scatter必须一cast、一split、恰好六个子箭，母/子蓝光均有frames；真实bounce及余辉frames必须增加，随后activeBounceAfterglows归零。
- 原有journal replay后不能新增Scatter cast/split，不能移动锚点或延长expiry。
- 参数模式单独验收：native模式核实际q与速度/980关系；回退模式核90/52/75原值和非空reason，绝不把回退称为native通过。

现有 `run_batch --only hanzo-visual` 继续使用默认快速路径；参数缺失时允许明确的旧值回退。
新增可选参数：

```powershell
# 使用同一套现有 --pid/--created/--mc-pid/--mc-created/--world/--guest-sha256 参数
.venv/Scripts/python.exe research/sprint-20261024/verify_hanzo_arrows_visual.py <现有身份参数> --output research/sprint-20261024/hanzo-context-strong --require-native-scatter --scatter-hold-ms 1100 --verify-expiry
```

`--require-native-scatter` 仅为本次Scatter take打开/恢复现有 `native_factory_calibration.enabled` 有界采证窗口；不新建hook/owner，回退将令该模式失败。
`--scatter-hold-ms 150/400/1100` 可分别跑弱/中/强不同轮次，间隔仍遵守原版真实冷却；输入时长只用于测试动作，不是q数据源。
`--verify-expiry` 另观察真实200-server-tick留存后移除，单段最长14秒；缺锚点/服务器未到期会如实失败，不以等待时间替代tick。
普通默认路径只验证短期留存和余辉消退；完整到期验收须带此开关。WGC小图/拼图规则不变，`visualAccepted`仍需人工确认。

### 文件与集成结论

新增上述context三个文件、`HanzoScatterContextCheck.java`；修改NativeHanzoSkillController/Runtime、HanzoArrowRenderer、HanzoArrowVisualLab及本verify脚本。
context预备由现有启动器自动发现；新状态由已集成的hanzoSkills/hanzoArrowFx/hanzoArrowVisualLab诊断自然输出。
**本轮没有需Claude新增的共享行，没有新增打包命令，未改run_batch键名。** 保留现有10包和接线即可。
未编辑 `HanzoDragonRenderer`、`HanzoSonicPulseMesh`；NativeHanzoSkillRuntime只改散射/诊断部分，龙段以colors线程为准。
离线证据、源码备份与检查在 `research/hanzo-scatter-context-20261026/`；不把本轮编译/fixture写成实机接受。
