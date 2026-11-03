# 2026-10-27 Hanzo：散射箭在当前基础上再 ×2

按用户第二次试玩反馈，将 E 散射箭的**总倍率从原版基础 ×2 改为 ×4**，统一标注 **MC 适配：用户要求**。原版参数路径与 MC fallback 同步生效；六支子箭及反弹沿用一次计算后的伤害，不按反弹次数继续叠乘。

| 路径 | 此前 ×2（OW HP） | 当前 ×4（OW HP） | 当前 MC HP（现有比例 0.1） |
|---|---|---|---|
| 原版参数母箭 `1dc` | 50–250 | 100–500，即 `4*1dc` | 10–50 |
| 原版参数子箭 `980` | 30–150 | 60–300，即 `4*(15+60*q)` | 6–30 |
| fallback 母箭/子箭 | 各 150 | 各 300，即 `75*4` | 各 30 |

原版 raw q/1dc/980 的身份、范围与表达式校验保留，翻倍发生在通过校验之后。诊断 `hanzoSkills.scatterContext.damageMultiplier=4`，`damageAdaptation="MC 适配：用户要求"`；`baseParentDamage/baseChildDamage` 仍为适配前数值，`parentDamage/childDamage` 为实际施加值。

## 修改文件

- `guest/src/main/java/lab/owmcguest/HanzoScatterContext.java`：总倍率 2→4，两条参数路径与 reason 同步；fallback 由常量自动更新为 300。
- `guest/src/main/java/lab/owmcguest/NativeHanzoSkillRuntime.java`：散射说明及 fallback 诊断更新为 `75×4=300`；散射默认伤害仍引用统一常量。未改龙击逻辑。
- `guest/src/test/java/lab/owmcguest/HanzoScatterContextCheck.java`：q=0/.5/1 的母/子箭期望改为 ×4，满值为 500/300，fallback 为 300/300；仍拒绝把适配后的值当作 raw 原版读数输入。
- `research/sprint-20261024/verify_hanzo_arrows_visual.py`：同步总倍率 4、母箭 100–500、子箭 `4*(15+60*q)` 和 fallback 300/300 的断言；诊断倍率须为 4，合法 fallback 仍为 BLOCKED，不冒充原版参数 PASS。
- `tools/test_hanzo_b01b.py`：同步当前 ×4 正例；旧 ×2 fallback/子箭与重复叠乘结果均不能通过当前期望。历史实测 JSON 未改。

## 接线、打包与验证

- 无新增共享行、场景、素材包或打包命令；不改共享文件。 [已集成 integrator]（核对既有六个键及诊断，未重复登记）未开游戏、未构建/部署 JAR、未运行实机脚本。原版触发、弹道、反弹、左键、音波箭及龙击保留原行为。
- 环境检查、`compileClientJava`、`HanzoScatterContextCheck` 与 10 项 Python 回归通过；共享文件、龙击逻辑及原版 raw 数值守卫对照一致。离线验证与源码保护结果：`research/hanzo-damage4-20261027/checks.json`；编译日志 `compile.log`，Python 日志 `python-tests.log`，修改前文件在 `source-before/`。
- Claude 统一部署后重跑 `hanzo-visual,hanzo-scatter-weak,hanzo-scatter-medium,hanzo-scatter-strong`，并用 `hanzo,hanzo-full` 回归。检查母/子箭 actual=base×4、fallback=300/300，反弹后倍率仍为 4。实机 HP 检查应使用足够血量的无护甲目标，区分伤害值和击杀时剩余血量截断。
- 未解决项：本轮只有离线代码/断言验证，实机伤害与原版参数采证仍由 Claude 验收；缺原版读数时继续明确 fallback/BLOCKED。

## r27-H01：16m 战斗通道自愈（同日追加）

`r27-H01-hanzo` 与 `hanzo-full` 的旧 `far-lab` 在施放前即报 `target corridor is obstructed; no blocks changed`。该场景仅寻找玩家自身 3×3×2 站立空间，地板半径 12，16m 目标位置未纳入完整预检。已通过的 10m `hanzo-visual` 和 ×4 伤害实现不改；本轮不宣称解决 medium 的原版参数 BLOCKED，也未追认障碍来自狂鼠或人工改动。

### 已落地的 Hanzo 文件

- 新增 `HanzoCombatSite.java`：只读搜索半径 18、净高 5 的完整候选区域（覆盖 16m 目标）；当前中心及附近 8 个中心（横向偏移 24 格），向上最多 40 格，最多 369 个候选。检查维度高度、已加载区块、世界边界、方块实体、地板承托、通道空气及活体占用。不加载新区块，不清除障碍；失败给出分类计数和首批/最后一次具体坐标与 block state。
- 新增 `HanzoLabBlocks.java`：37×37 的单层地板归属日志，只把原空气改为临时石头。原有天然方块不替换、不纳入所有权。回滚仅处理日志中的格子，当前仍为自己的石头才恢复原状态；外部改动保留，未加载/写入拒绝保留 pending 与具体原因，部分构建异常也可回滚。
- 新增 `HanzoCombatLab.java`：同时要求 `owmc.twilightTrial`、配置世界名前缀、**实际服务端存档名**前缀 `Overwatch Twilight Switch ` 与存活创造玩家；不合条件在任何方块变更前拒绝。选址后补自有地板，沿用现有 `meiLab(...,16)` 的真实村民目标，再检查实际目标包围盒和瞄准通道。`lastStart` 留搜索、坐标、填补空气数、保留原块数、`terrainCleared=0`；`lastCleanup` 留恢复数、外部改动数、pending 和原因。类首次加载自动注册 `SERVER_STOPPING` 回收，不需要新增 GuestMod 行。
- 新增 `tools/hanzo_live_lab.py`：新 `HanzoCombatSuite`，等待新 startSerial/cleanupSerial 及两次稳定清理回执；保存 `labPreparations[]`、`cleanupReceipt`，拒绝、超时或未接线均带最后状态，绝不带错继续施放。
- 修改 `verify_hanzo_full.py`：primary/sonic、scatter、dragon 各次场景改为新安全通道；Q 的测试充能放在准备完成之后。修改 `verify_junk_hanzo.py` **仅 Hanzo 的 Suite 选择与准备分支**；Junkrat 仍走原 Suite/run_cases，不改变狂鼠测试行为。

这是显式 MC 实验场景适配。损坏地面/坑洞以临时自有地板支撑，结束恢复到建场前状态；原地形、未知旧结构、外部新方块和生物均保留。无合适位置时明确失败，不清空天然通道强行通过。

### Claude 必须补的共享接线（本线程未改共享文件）

在 `WorldFrameExporter` 对测试 action 的 allowlist 增加：

```java
"hanzo-combat-lab",
```

[已集成 integrator]

在既有 server.execute 中的测试 action switch 增加：

```java
case "hanzo-combat-lab" -> HanzoCombatLab.start(server, owner, forward);
```

[已集成 integrator]

在 `/combat` 诊断组装处增加：

```java
diagnostic.add("hanzoCombatLab", com.google.gson.JsonParser.parseString(HanzoCombatLab.status));
```

[已集成 integrator]

在该 switch 的 `case "cleanup"` 内、现有 `HanzoArrowVisualLab.cleanup()` / `NativeCombatScene.cleanup()` **之前**增加：

```java
HanzoCombatLab.cleanup();
```

[已集成 integrator]

这条清理调用只接在外部 HTTP cleanup 路径。**不要插入 NativeCombatScene.cleanup() 本体**：`meiLab` 内部会调用它；若在其中回收本场景地板，会在构建目标时撤掉刚建的支撑。停止服务端已由 HanzoCombatLab 自己的生命周期回调处理。若缺诊断或 cleanup 接线，Python 会在新场景构建前拒绝，留明确接线错误。

### 验证与重跑

- 环境检查、`compileClientJava`、`HanzoCombatLabCheck`、既有 `HanzoScatterContextCheck` 通过；16 项 Hanzo Python 回归通过。新安全 fixture 实际覆盖隔离存档拒绝、16m 障碍改选位置、369 次有界拒绝、天花板/活体占用、归属越界拒写、外部 CHEST/天然 DIRT 保留、未加载待恢复重试、部分写入回滚；不启动游戏。
- 证据与修改前备份在 `research/hanzo-corridor-20261027/`（`compile.log`、`python-tests.log`、`checks.json`、`source-before/`）。共享文件与伤害/视觉实现保持本轮修改前内容，未构建/部署 JAR、无素材打包要求。
- 接线并部署后优先重跑现有 `run_batch --only hanzo,hanzo-full`；新 result 中检查三项回执：`lastStart.search.floor`、`terrainCleared=0`、最终 `lastCleanup.pending=0` 且 `ownedBlocks=0`。建议再以受损地面/16m 障碍预置重跑，以及一次无法选址的拒绝检查。`hanzo-visual` 和弱/强已通过的证据保留，medium 的参数缺证仍单独 BLOCKED。

第三轮集成索引：[INTEGRATION-20261027.md](INTEGRATION-20261027.md)。上述标记只指源码接线/删除旧行/既有接线核对，不表示实机验收。全量compileClientJava --rerun-tasks通过（27秒，3任务实际执行），未遇Loom锁、未删锁文件；未开游戏、打包JAR/DLL或部署。原“待接线”段落保留交接时历史，最新结果以本补记为准。

## 第五次反馈：半藏 Q 的移动与视角接续（2026-10-27）

### 原因与证据边界

- `NativeHanzoSkillController` 只把原版 b9:76 新 tick 交给服务端；`NativeHanzoSkillRuntime` 的固定 `d.dir` 属于已发出龙的方向，没有玩家旋转/移动锁。**本轮没有编辑该 Runtime 或 HanzoDragonRenderer**；Claude 最新 `DRAGON_RANGE=120`、`DRAGON_DEVOUR` 秒杀、清方块完整保留，并做文件 SHA256 对照。
- 共享链路存在确定的缺口：原版相机不是普通第一人称时，`pose_observer.cpp::slotInputScope()` 令 `inputActive=0`；`HostPoseReader` 随即清 movementBits；`HostMovementMixin`、`NativeLocomotionController.baseMovement` 和 Motor 均据此变成无输入。Motor 的 cinematic 注释没有实施半藏例外，当前仅 Reaper 有同域回补。另一个独立阻断是原版 computed run limits 可合法为全零，旧代码直接把它当成 MC 零速度。
- `HostCameraMixin` 没有按 Q 键或龙视图锁转向，它一直使用原版已观测相机；因此仅修改 Motor/WASD 不能修复固定原版相机。新接线同时恢复原版现有第一人称相机的选择，让实际原版旋转继续产生 GPU pose，MC 继续消费真实 pose；没有在 MC 虚构另一套视角矩阵。
- 本轮未按 Q、未开游戏或实测新逻辑。只读查看已有会话时 `/combat` 尚未绑定英雄，原版进程内存访问被系统拒绝，**没有得到本次 Q 的相机类型现场证据**。上述是源码可导致症状的机制与修复候选，不把注释、只读查询或 fixture 当成本次实机根因证明；具体选中的原版相机类型与 Q 动画/控制效果须按下述专项验证。

### 已实现的本线程代码

- `HanzoControlProof`：先观察真实原版第一人称输入才建立普通控制权限；只在同一 owner/native PID/source/world/model、已认证 Hanzo b9 绑定、持续新 host 帧（≤150ms）、前台原版窗口与隐藏鼠标下接续。菜单、失焦、死亡、换英雄/世界、绑定失败或帧停滞撤销；初始 cinematic/menu 样本不能自行准入。**没有读 Q 键生成攻击或延长龙寿命**，控制许可与原版 b9:76 攻击准入分开。
- `HanzoControlController`：由现有 NativeHanzoSkillController 刷新/复位；需要时只采样该原版窗口的真实 WASD/Space/Ctrl，不发模拟按键。对已认证半藏的 computed 三个 run limits 全零情况，取同次读取的原版 base directional limits；部分速度限制和无许可情形保留原数值。MC 原有碰撞/重力及其余锁定检查仍运行。
- `HanzoControlCapability`：只在 HostPoseReader 完成原包验证后读取 HNZ1 能力；新 JAR 遇旧 DLL 不会单独放开移动。原版 pose 的 `336` 写固定 HNZ1 能力标记；256B body 的未用尾部 `232..255` 写 HNZ1/model/observed/frame。既有 body、CLM2/FLY1/DEY1 内容不改。
- `native-host/src/hanzo_control.hpp`：现有合成器的同一个 render owner 消费新请求；核对真实 NativeLocalHero=Hanzo/current model、双端进程/代次/世界、150ms body/请求与当前 pose、原版窗口前台/隐藏鼠标、唯一 0x4f 相机组件及原版 normal camera vtable `base+0x15c7000`。若选中另一个原版相机，且其 vtable/入口在同一执行映像、字段二次读取稳定，选择该组件**已有的 normal camera**。picker vtable `base+0x15f2cf8`、菜单/失焦/过期/异域均拒绝。
- 这是半藏控制的 **MC 适配：用户要求**。相机处只进行有当前许可的 runtime 选择；不改 vtable/config、不替换矩阵、不创建第二个 callback/hook owner，也不保留旧 Q 相机指针在施法结束后做延迟回写。原版自己的后续相机状态仍可正常选择；每个 render frame 最多处理一次。新的相机选择行为需 Claude 验收，不能把“能正常选择该字段”的假内存 fixture 等同于原版 Q 生命周期已通过。

### Claude 需落地的共享接线

完整精确补丁：`research/hanzo-q-control-20261027/integration.patch`；生成器 `prepare_integration.py` **只写 research 的接线副本，不改共享源码**。已用该副本验证 Java 编译和整个 `pose_observer.cpp` 的 C++17 语法。应用时按当前共享源码审阅这 7 个文件的 hunks；不要覆盖其他线程新内容。

Java 原样接线（见补丁中的精确位置）：

```java
// HostPoseReader.decode：所有原包校验通过后，return new Pose 之前。
HanzoControlCapability.observe(data,now);

// WorldFrameMapping.publishBody：现有 NativeDeadeyeInputLock.write 之后。
HanzoControlProof.write(b,HanzoControlController.current(client,host));

// NativeLocomotionController.baseMovement：原 bits 计算后、directionalMovement 前。
bits=HanzoControlController.movementBits(MinecraftClient.getInstance(),host,bits);
// NativeLocomotionController.directionalMovement：替换原 NativeWalkSpeed.local(bits,speeds)。
var local=NativeWalkSpeed.local(bits,HanzoControlController.movementSpeeds(MinecraftClient.getInstance(),host,speeds,reader.baseSpeeds()));

// NativeMotorController.movement：原 bits 计算后，Reaper 分支之前。
bits=HanzoControlController.movementBits(client,host,bits);

// HostMovementMixin：原 bits 计算后、Deadeye 等原有锁判断之前。
bits=lab.owmcguest.HanzoControlController.movementBits(net.minecraft.client.MinecraftClient.getInstance(),pose,bits);

// WorldFrameExporter /combat 诊断。
diagnostic.add("hanzoControls",com.google.gson.JsonParser.parseString(HanzoControlController.status));
```

[已集成 integrator] 上述 Java 六文件接线已落地，保留原包验证、Deadeye 和其他英雄锁。

原版侧接线在同一补丁的 `pose_observer.cpp` hunk 中，核心原样行如下；完整 `continueHanzoControls()` 函数与所有上下文均已写入补丁，不需要猜接线点：

```cpp
#include "hanzo_control.hpp"
// OWMC_LIVE_BLEND 内，viewLightBody 旁。
std::shared_ptr<const HanzoControlRequest> latestHanzoControl;
HanzoGameplayCamera hanzoGameplayCamera;NativeLocalHero hanzoControlHero;uint64_t hanzoControlDecisionFrame=UINT64_MAX;

// 创建 PosePublisher 后、首次 publication 前；仅非 fixture 的 live compositor。
if(!fixture)publisher->put(336,uint32_t(0x315a4e48));

// 现有 worker 的 decodeGuestBody 成功后，从同一个已验证 body packet 解码。
auto hanzo=decodeHanzoControl(packet.data());
std::atomic_store(&latestHanzoControl,hanzo.model?std::make_shared<const HanzoControlRequest>(hanzo):std::shared_ptr<const HanzoControlRequest>{});

// nativeViewMode() 开头；函数自身严格限制现有 renderThread，无新线程/回调。
continueHanzoControls();

// stop() 开头，OWMC_LIVE_BLEND 内撤销请求。
std::atomic_store(&latestHanzoControl,std::shared_ptr<const HanzoControlRequest>{});

// report() 的 live 诊断。
out<<",\"hanzoCameraSelections\":"<<hanzoGameplayCamera.selected.load()<<",\"hanzoCameraRefusals\":"<<hanzoGameplayCamera.refused.load()<<",\"hanzoCameraReason\":"<<std::quoted(hanzoGameplayCamera.reason.load());
```

[已集成 integrator] 上述 native/C++ 接线及完整 `continueHanzoControls()` 已落地；report 新诊断加 `OWMC_LIVE_BLEND` 条件，避免破坏普通 pose-only 构建。新冷启动身份 v45，构建命令见 INTEGRATION-20261027.md；未构建或部署 DLL。

既有 `HostCameraMixin`、HostPose 的 inputActive/flags 解码、NativeSlotFilter/Deadeye 锁逻辑不改，避免全局放松所有英雄的 cinematic/menu。相机继续使用原版 normal camera 的实际旋转，而不是把 `inputActive` 直接改成 true。**这次需要 Guest JAR 与合成器 DLL 两端同时构建部署**；只装 JAR 时 `hanzoControls.nativeCapability=false`，保持旧路线。构建部署仍由 Claude 正常停机后执行，本线程未打包 JAR/DLL。

### 验证、实机脚本与未解决项

- `compileClientJava`、`HanzoControlProofCheck`、7 文件共享接线副本的 `HanzoControlOverlayCompile` 通过；Native HNZ1/camera fake-memory fixture 通过；接线副本完整原版 C++17 `-fsyntax-only` 通过（无 DLL 输出）；21 项 Hanzo Python 回归通过。证据 `research/hanzo-q-control-20261027/checks.json`，日志同目录。源文件保护检查包括 Claude 最新 Runtime、龙渲染器和本轮全部共享文件。
- 新 `verify_hanzo_q_controls.py` 使用既有隔离场景/身份/存档备份，真实按一次 Q 并要求新的 b9:76 产生一次 dragonCasts；在释放前区间、原版双龙真正绘制后的早期、约四秒后的晚期分别做短侧移/转向，避开用户设定的龙吞噬地板方向。断言每阶段实际 MC 水平位移≥0.4m、**原版 pose** yaw 变化≥2°、MC yaw 跟随原版且龙在飞行期仍存在；原版相机冻结、只有输入位、只有 MC 旋转、无实际 native cast 或晚期已无龙都失败。释放前区间尚无独立认证的 windup 根节点，所以报告明确为 Q input→新 b9:76 回执区间，不伪称精确原版 cast phase。
- 可在 `run_batch.TESTS` 追加：`('hanzo-q-controls', ['verify_hanzo_q_controls.py'])`；沿用现有全部进程/创建时间/world/JAR 参数。优先新键，随后 `hanzo-full`。[已集成 integrator] 已登记 `hanzo-q-controls`，两键按此顺序各用新会话；不把 `--only` 参数顺序当作执行顺序。结果同时记录 `hanzoControls`、Motor、原版 `world-live-PID.json` 的 camera 选择/拒绝原因与龙的 range/devour/击杀/清方块计数。
- 重点复核原版 Q 手部动画/发射回执持续正常、施法及龙飞行中可转向并移动、Q 结束后不跳回旧相机、菜单/失焦/换人/换世界撤销、Reaper/Deadeye 控制没有回归。**本轮没有 Q 实机通过证据**；原版 Q 实际相机类型及 runtime 选择的生命周期效果仍须专项脚本和用户游玩验收，不能仅以 HNZ1 ready 或 cameraSelections 增量宣布完成。若拒绝因 picker/组件不唯一/相机 identity，保留具体原因再采证，不能删掉校验强行接管。

## feedback5-hanzo-controls-live：龙体绘制门槛误读修复（同日追加）

**已确认本次异常的直接原因是脚本读了未导出的诊断键；不是已经证实的 2 秒窗口不足、未 released 或 DRAGON_DEVOUR 物理故障。**

- 原结果 `research/sprint-20261027/feedback5-hanzo-controls-live-hanzo-q-controls/result.json` 共 33 个样本；对该测试的 profile-backup JAR 做只读检查，SHA256 与 `identity.guestSha256` 相符。实际部署的 `WorldFrameExporter.class` **没有**字符串 `hanzoDragonDraws` 和 `hanzoDragonArrowFrames`，但有 `hanzoDragonSkinDraws`、`hanzoDragonSkinFallbackDraws`。旧脚本 `get('hanzoDragonDraws',0)` 将缺失键永久当作 0；baseline 与每个样本都为 0，因此 `> before_draws` 必败，即使龙体确实已经提交绘制。
- 已导出的两项 skin 计数只在 **released 且 travelled>0** 的龙体分支、每个 twin 提交后累计；起始箭的 `arrowFrames` 不增加它们。当前修复优先读取明确注册的 `hanzoDragonDraws`，没有该键时使用这两项之和作为等价龙体提交计数。若三者都无有效读数，在按 Q **之前**明确报诊断缺失；不再用 0 代替未知值。
- 保留原有 **2 秒**等待窗口、活着的 `dragons>0` 与龙体计数**相对本次 baseline 新增**的条件；历史绘制次数、起始箭帧数、单独的 dragonCasts 都不能冒充龙体阶段。新 renderer 错误、计数复位或计数来源变化单独报错。没有延长窗口来掩盖失败，也没有放松移动/转向断言。
- 新 trace 保存 `dragonRender` 的真实计数来源、原始 skin/body/arrow 字段、缺失键、总帧、错误增量/文本；保存 `dragonRuntime` 的 range/devour/命中/击杀/清块计数与 native 输入过滤计数。失败时可以直接区分“字段缺失”“只有起始箭提交”“新渲染异常”“龙还活着但无新 body 提交”。旧 trace 没保存两项 skin 计数，**不能追认旧跑的龙体到底画了还是没画**；不把修复后的兼容规则倒填旧记录。

物理/输入核对：

- `NativeHanzoSkillRuntime` 的起始箭阶段只按方向积分位移，**没有方块 raycast 或碰撞分支**；到距起点约 10m 转 released，按正常 20TPS 约 10–11 个 server tick。`devourBlocks` 在已 released 的龙体分支末尾才执行，不能在起始箭阶段把它自己拦住/清掉。本轮保持整个 Runtime、Renderer、HanzoControlController、合成器与共享字段的 SHA256 不变。
- 这次所有样本 `inputActive=true`，`continuedFrames=0`、`zeroSpeedRecoveries=0`、`hanzoCameraSelections=0`，原版相机报告 `already-first-person`；因此这次没有证据表明新相机选择/输入接续触发并令龙消失。
- **仍未证明 Q 控制通过**：旧 cast 样本实际水平移动约 **2.75m**，但原版 yaw 变化仅 **0.01364°**，达不到原有 ≥2° 转向断言。绘制门槛错误提前终止了测试，尚未取得飞行早/晚期控制结果。修复只消除错误诊断门槛，保留该真实转向失败的可见性；新脚本已补 native 输入过滤计数以继续定位，不能把本次脚本修复宣称为施法转向已修复。

修改仅为 `tools/hanzo_q_controls.py`、`tools/test_hanzo_q_controls.py`、`verify_hanzo_q_controls.py`；27 项 Python 回归与 `py_compile` 通过。证据 `research/hanzo-q-draw-diagnostic-20261027/checks.json`，包含实际部署 JAR 字符串/哈希检查、旧 trace 数值、源码保护对照。未开游戏、未构建/部署 JAR/DLL；**本次可直接用当前 v45/现有 JAR 重跑 `hanzo-q-controls`，不必重打包**。

无需共享接线。Claude 若希望统一顶层别名，以下仅为可选诊断（兼容修复不依赖它们）：

```java
diagnostic.addProperty("hanzoDragonDraws",HanzoDragonRenderer.dragonDraws);
diagnostic.addProperty("hanzoDragonArrowFrames",HanzoDragonRenderer.arrowFrames);
```


## ?????Q ????????????2026-10-27??????????????

**?????? HNZ1 / Q ?????????MC ????????** ???????? Q Begin ???? `max(????? released, ???? End)` ???????? 120m ?????????Java ??? Begin ???????? yaw/pitch???????????? `HanzoQTravelMixin` ?? travel/??/??/??????????? travel?????????????End ? released ??????????????????????????/???????????/model/source/world?????????? reset???? `NativeHanzoSkillRuntime.resetSession()` epoch ???????????? idle ???????????????

### ?????????????????????????

- ?? graph `0580000000000101`?`StateStack19` (`f7d6498c`) ??? logger Begin/End ???????`StateAnim27/28` ???????? graph b9 ? `WeaponVolley76`????????? Q logical-button literal `0x79`?Stack ? `entity.21` ???SetVar17 ? `entity.156` ??????????? 1.4s/1.1s ???????????? Q ??????? MC ???? Begin?
- ???? dump `research/hanzo-skills-20261021/graphs.json` ????? Q logger `research/sprint-20261024/hanzo-dragon-calibration1/result.json`?Q dispatch=18928?b9:76=20328?0101:19 End=21428????? dispatch??? **1.40s**?dispatch??? **2.50s**?????? 10m / 20m/s ? **0.50?0.55s**?10?11 MC tick????????????????? Begin ? **1.90?1.95s**?????? **2.50s**?
- **????????????????????????** ??? `hanzoControls.nativeBegin/nativeEnd/nativeCastMillis` ?????????????`startedWall/nativeEndWall/releasedWall/lockMillis` ??????????????????????????????????? 2.50s ???????????????????????????????

### ?????????

- `HanzoControlProof` ????????????????`HanzoControlController` ?? WASD ????????????????????`HanzoControlCapability` ?? magic **HNZ2 `0x325a4e48`** ??? HNZ1 DLL??? body tail 232..255 ?? 24 bytes??????? native Begin?0..231?? Deadeye????
- ? `HanzoQCastReader` ????? `hanzoQCast` spec?`prepare_native_hanzo.py` ?? `hanzoSkills` ?????? `native-hanzoQCast-request-PID.json`?????????? hero binding worker ??????????????????????? model ??????????????
- `NativeHanzoSkillController` ???? Begin ???? Dragon?`NativeHanzoSkillRuntime` ?? `DragonFlight` released ??? reset epoch?**released ??????/????? helper ???????`DRAGON_RANGE=120`?`DRAGON_DEVOUR=true`?????/??????** `HanzoDragonRenderer` ? colors/?????????
- ?? `native-host/src/hanzo_control.hpp` ??? HNZ2 scope ???? camera pointer ?? API??????????? `NativeSlotFilter` ?????????? WASD/??/F6 ?????????????? key-up?`WM_KILLFOCUS` ???????? Begin ????????????????? 150ms ??????? hook/callback owner???? host `inputActive`?

### Claude ???????/native ?????????????

????????????? `research/hanzo-q-lock-20261027/integration.patch`?????? research ????? `HostPoseReader` ? capability.observe?`WorldFrameMapping` ? tail write?WorldFrameExporter ? `hanzoControls`?NativeMotorController/HostMovementMixin ? movementBits ?????????????????? travel mixin ???????? `continueHanzoControls()` / `HanzoGameplayCamera` ??? normal-camera selection??????????????

本段集成说明（第六次反馈）：交接本段部分中文原文已为问号，按用户明确的 Q Begin 起锁、施法 End 与同次龙 released 后解锁要求及下列可读精确补丁接线；覆盖前轮 HNZ1 自由移动/相机选择方案。

```diff
--- a/guest/src/client/java/lab/owmcguest/NativeLocomotionController.java
+++ b/guest/src/client/java/lab/owmcguest/NativeLocomotionController.java
@@ -32,6 +32,10 @@
         if(p==null||!Boolean.getBoolean("owmc.hostMovement")||!Boolean.getBoolean("owmc.frameExport"))return vanilla;
         var host=HostPoseReader.INSTANCE.latest();
         tick(client);
+        if(HanzoControlController.movementLocked()){
+            NativeRollController.INSTANCE.discardMotion();NativeMotorController.INSTANCE.discardMotion();
+            p.setVelocity(Vec3d.ZERO);return Vec3d.ZERO;
+        }
         if(NativeDeadeyeController.movementLocked()){
             NativeRollController.INSTANCE.discardMotion();NativeMotorController.INSTANCE.discardMotion();
             return new Vec3d(0,p.getAbilities().flying?0:vanilla.y,0);
@@ -50,7 +54,7 @@
     }
     Vec3d directionalMovement(Vec3d vanilla,int bits){
         var host=HostPoseReader.INSTANCE.latest();
-        var local=NativeWalkSpeed.local(bits,HanzoControlController.movementSpeeds(MinecraftClient.getInstance(),host,speeds,reader.baseSpeeds()));
+        var local=NativeWalkSpeed.local(bits,speeds);
         if(host==null)return new Vec3d(0,vanilla.y,0);
         var f=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());
         var forward=new Vec3d(f.x,0,f.z).normalize();var right=new Vec3d(-forward.z,0,forward.x);
--- a/guest/src/main/resources/owmcguest.mixins.json
+++ b/guest/src/main/resources/owmcguest.mixins.json
@@ -3,6 +3,7 @@
   "package": "lab.owmcguest.mixin",
   "compatibilityLevel": "JAVA_21",
   "refmap": "client-owmc-guest-refmap.json",
-  "client": ["HostCameraMixin", "HostLensMixin", "HostMovementMixin", "HostFlightMixin", "HostMouseCaptureMixin", "FullBrightMixin", "NativeDashTravelMixin", "FinalWorldCaptureMixin", "BossBarHudAccessor", "BossBarTravelMixin", "HanzoSonicGlowMixin", "MeiFrozenMobMixin", "MeiFrozenTravelMixin", "NativeJunkratCameraMixin", "NativeJunkratControlMixin", "HeroVoiceMovementSoundMixin", "HeroVoicePlayerFallSoundMixin"],
+  "client": ["HostCameraMixin", "HostLensMixin", "HostMovementMixin",
+    "HanzoQTravelMixin", "HostFlightMixin", "HostMouseCaptureMixin", "FullBrightMixin", "NativeDashTravelMixin", "FinalWorldCaptureMixin", "BossBarHudAccessor", "BossBarTravelMixin", "HanzoSonicGlowMixin", "MeiFrozenMobMixin", "MeiFrozenTravelMixin", "NativeJunkratCameraMixin", "NativeJunkratControlMixin", "HeroVoiceMovementSoundMixin", "HeroVoicePlayerFallSoundMixin"],
   "injectors": {"defaultRequire": 1}
 }
--- a/guest/src/client/java/lab/owmcguest/mixin/HostCameraMixin.java
+++ b/guest/src/client/java/lab/owmcguest/mixin/HostCameraMixin.java
@@ -29,7 +29,7 @@
         var pose=HostPoseReader.INSTANCE.latest();if(pose==null) return;
         // Camera's local axes in the original MC 1.21.1 implementation:
         // forward (0,0,-1), up (0,1,0), left (-1,0,0).
-        rotation.set(pose.rotation());
+        rotation.set(lab.owmcguest.HanzoControlController.cameraRotation(pose));
         horizontalPlane.set(0,0,-1).rotate(rotation);
         verticalPlane.set(0,1,0).rotate(rotation);
         diagonalPlane.set(-1,0,0).rotate(rotation);
--- a/native-host/src/pose_observer.cpp
+++ b/native-host/src/pose_observer.cpp
@@ -1,6 +1,6 @@
 // Original camera observation and MC composition; optional Kyoto light direction
-// is camera-relative. HNZ1 can select the existing Hanzo gameplay camera;
-// all other original camera/gameplay values retain the observation-only route.
+// is camera-relative. HNZ2 suppresses Hanzo cast input through the existing
+// input owner; original camera pointers and gameplay values remain untouched.
 #include "host_pose.hpp"
 #include <d3d11_4.h>
 #include <wrl/client.h>
@@ -66,19 +66,23 @@
 HWND inputWindow=nullptr;WNDPROC originalWindowProc=nullptr;MovementIntent movementIntent;std::atomic<unsigned> flightKey{VK_F6};
 NativeSlotFilter nativeSlotFilter;
 bool deadeyeMotionScope();
+bool hanzoMotionScope();
+bool controlMotionScope();
+bool slotFilterScope();
+void revokeHanzoControls();
 bool torbWeaponSelectionScope();
 unsigned nativeViewMode();
 bool slotInputScope(){CURSORINFO cursor{sizeof(CURSORINFO),0,nullptr,{0,0}};return active&&viewMode==1&&GetForegroundWindow()==inputWindow&&GetCursorInfo(&cursor)&&!(cursor.flags&CURSOR_SHOWING);}
 LRESULT CALLBACK movementMessages(HWND w,UINT message,WPARAM key,LPARAM data) {
     if(active) {
-        if(slotInputScope()){
+        if(slotFilterScope()){
             if((message==WM_KEYDOWN||message==WM_KEYUP||message==WM_SYSKEYDOWN||message==WM_SYSKEYUP)&&nativeSlotFilter.blocksSlotKey(unsigned(key))){nativeSlotFilter.filteredKeys++;return 0;}
             if(weaponSlotMouse(message)){nativeSlotFilter.filteredMouse++;return 0;}
-            if(deadeyeMotionScope()&&deadeyeMotionMessage(message,unsigned(key))){
+            if(controlMotionScope()&&deadeyeMotionMessage(message,unsigned(key))){
                 if(message==WM_MOUSEMOVE)nativeSlotFilter.motionMouse++;else nativeSlotFilter.motionKeys++;return 0;
             }
         }
-        if(message==WM_KILLFOCUS)movementIntent.release();
+        if(message==WM_KILLFOCUS){movementIntent.release();revokeHanzoControls();}
         if(message==WM_KEYDOWN||message==WM_KEYUP||message==WM_SYSKEYDOWN||message==WM_SYSKEYUP) {
             const WPARAM keys[]{'W','S','A','D',VK_SPACE,VK_CONTROL,flightKey.load(),'V',VK_F7,VK_F8};
             for(unsigned i=0;i<10;i++)if(key==keys[i])movementIntent.key(i,message==WM_KEYDOWN||message==WM_SYSKEYDOWN,GetTickCount64());
@@ -112,7 +116,8 @@
 std::shared_ptr<const LightCandidate> viewLightCandidate;
 std::shared_ptr<const GuestBody> viewLightBody;
 std::shared_ptr<const HanzoControlRequest> latestHanzoControl;
-HanzoGameplayCamera hanzoGameplayCamera;NativeLocalHero hanzoControlHero;uint64_t hanzoControlDecisionFrame=UINT64_MAX;
+std::shared_ptr<const HanzoControlRequest> revokedHanzoControl;
+std::atomic<uint64_t> hanzoMotionFrames{0};
 struct DeadeyeInputSnapshot{uint64_t wall,observed,generation,hostGeneration,world,begin;uint32_t sourcePid,model;};
 std::shared_ptr<const DeadeyeInputSnapshot> deadeyeInputSnapshot;
 NativeLocalHero deadeyeInputHero; // Used only by the existing render owner.
@@ -232,33 +237,40 @@
     }else lightVerifiedEpoch=lightScope.epoch;
 }
 #endif
-// Runs only on the existing render owner; no extra hook/callback or camera patch.
-void continueHanzoControls() {
-#ifdef OWMC_LIVE_BLEND
-    if(fixture||!active||!renderThread.load()||renderThread.load()!=GetCurrentThreadId())return;
-    auto frame=frames.load();if(hanzoControlDecisionFrame==frame)return;hanzoControlDecisionFrame=frame;
-    auto r=std::atomic_load(&latestHanzoControl);auto pose=std::atomic_load(&latestPose);auto image=std::atomic_load(&latestWorld);auto body=std::atomic_load(&viewLightBody);
-    if(!r||!pose||!image||!body)return;
-    auto now=unixMillis();if(pose->wallMs>now||now-pose->wallMs>150||image->publishMs>now||now-image->publishMs>300
-        ||body->wallMs>now||now-body->wallMs>150||r->guestPid!=image->sourcePid||r->generation!=image->generation||r->hostGeneration!=pose->generation
-        ||r->guestPid!=body->sourcePid||r->generation!=body->generation||r->hostGeneration!=body->hostGeneration||r->world!=body->worldId)return;
+// Reuses the existing input-filter owner. HNZ2 never changes camera pointers.
+void revokeHanzoControls(){
+#ifdef OWMC_LIVE_BLEND
+    auto r=std::atomic_load(&latestHanzoControl);
+    if(r)std::atomic_store(&revokedHanzoControl,r);
+    std::atomic_store(&latestHanzoControl,std::shared_ptr<const HanzoControlRequest>{});
+#endif
+}
+bool hanzoMotionScope(){
+#ifdef OWMC_LIVE_BLEND
+    if(fixture||!active)return false;
+    auto r=std::atomic_load(&latestHanzoControl);auto revoked=std::atomic_load(&revokedHanzoControl);
+    auto p=std::atomic_load(&latestPose);auto image=std::atomic_load(&latestWorld);auto body=std::atomic_load(&viewLightBody);
+    if(!r||!p||!image||!body||(revoked&&sameHanzoCast(*r,*revoked)))return false;
     CURSORINFO cursor{sizeof(CURSORINFO),0,nullptr,{0,0}};
-    bool foreground=GetForegroundWindow()==inputWindow;
-    bool hidden=GetCursorInfo(&cursor)&&!(cursor.flags&CURSOR_SHOWING);
-    if(!foreground||!hidden)return;
-    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointer(base+0x17b7f90);
-    if(!hanzoControlHero.refresh(admin,lightRead))return;
-    IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};
-    if(!lightRead(base,&dos,sizeof dos)||dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<0||dos.e_lfanew>4096
-        ||!lightRead(base+dos.e_lfanew,&nt,sizeof nt)||nt.Signature!=IMAGE_NT_SIGNATURE||nt.OptionalHeader.SizeOfImage<0x1600000
-        ||nt.OptionalHeader.SizeOfImage>0x10000000)return;
-    HanzoControlContext c{GetCurrentProcessId(),image->sourcePid,hanzoControlHero.modelId,image->generation,pose->generation,
-        body->worldId,pose->frame,now,hanzoControlHero.hero,base,base+nt.OptionalHeader.SizeOfImage,admin,foreground,hidden};
-    hanzoGameplayCamera.update(*r,c,lightRead,lightWrite);
-#endif
-}
+    bool foreground=GetForegroundWindow()==inputWindow,hidden=GetCursorInfo(&cursor)&&!(cursor.flags&CURSOR_SHOWING);
+    if(!foreground||!hidden){std::atomic_store(&revokedHanzoControl,r);return false;}
+    auto now=unixMillis();
+    if(p->wallMs>now||now-p->wallMs>150||image->publishMs>now||now-image->publishMs>300
+        ||body->wallMs>now||now-body->wallMs>150||r->guestPid!=image->sourcePid||r->generation!=image->generation
+        ||r->hostGeneration!=p->generation||r->guestPid!=body->sourcePid||r->generation!=body->generation
+        ||r->hostGeneration!=body->hostGeneration||r->world!=body->worldId)return false;
+    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));NativeLocalHero hero;
+    if(!hero.refresh(pointer(base+0x17b7f90),lightRead))return false;
+    HanzoControlContext c{GetCurrentProcessId(),image->sourcePid,hero.modelId,image->generation,p->generation,
+        body->worldId,now,hero.hero,foreground,hidden};
+    return hanzoMotionActive(*r,c);
+#else
+    return false;
+#endif
+}
+bool controlMotionScope(){return deadeyeMotionScope()||hanzoMotionScope();}
+bool slotFilterScope(){return slotInputScope()||hanzoMotionScope();}
 unsigned nativeViewMode() {
-    continueHanzoControls();
     auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
     auto admin=pointer(base+0x17b7f90),iterators=pointer(admin+0xb0);
     auto component=pointer(pointer(iterators+0x4f*24));
@@ -340,7 +352,8 @@
         if(pose.inputActive) {const int keys[]{'W','S','A','D',VK_SPACE,VK_CONTROL,int(flightKey.load()),'V',VK_F7,VK_F8};for(unsigned i=0;i<10;i++)if(GetAsyncKeyState(keys[i])&0x8000)pose.movementBits|=1u<<i;}
 #ifdef OWMC_LIVE_BLEND
         pose.inputCapabilities=nativeSlotFilter.enabled&&!nativeSlotFilter.restored?0x31594544u:0u;updateDeadeyeInput(pose);
-        if(deadeyeMotionScope())pose.movementBits&=~0x7fu;
+        if(controlMotionScope())pose.movementBits&=~0x7fu;
+        if(hanzoMotionScope())++hanzoMotionFrames;
 #endif
     }
     publisher->publish(pose);std::shared_ptr<const HostPose> snapshot=std::make_shared<HostPose>(pose);std::atomic_store(&latestPose,snapshot);poses++;captured=true;
@@ -458,6 +471,7 @@
 void stop() {
 #ifdef OWMC_LIVE_BLEND
     std::atomic_store(&latestHanzoControl,std::shared_ptr<const HanzoControlRequest>{});
+    std::atomic_store(&revokedHanzoControl,std::shared_ptr<const HanzoControlRequest>{});
 #endif
     active=false;InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),oldContext,newContext);InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),oldSwap,newSwap);
     restored=*reinterpret_cast<void***>(context)==oldContext&&*reinterpret_cast<void***>(swap)==oldSwap;
@@ -567,7 +581,7 @@
     D3D11_TEXTURE2D_DESC d{};buffer->GetDesc(&d);width=d.Width;height=d.Height;
     publisher=std::make_unique<PosePublisher>(fixture?L"Local\\OWMCHostPoseTest":L"Local\\OWMCHostPose");
 #ifdef OWMC_LIVE_BLEND
-    if(!fixture)publisher->put(336,uint32_t(0x315a4e48)); // HNZ1 capability, fixed before first publication.
+    if(!fixture)publisher->put(336,uint32_t(0x325a4e48)); // HNZ2 suppression capability; rejects old free-control Guest.
 #endif
     newContext=new void*[traceContextCount(version)];newSwap=new void*[traceSwapCount()];SIZE_T bytes=0;
     if(!ReadProcessMemory(GetCurrentProcess(),oldContext,newContext,traceContextCount(version)*sizeof(void*),&bytes)||bytes!=traceContextCount(version)*sizeof(void*)) return reject("copy context table");
@@ -592,7 +606,7 @@
     if(!fixture){viewLightMapId=lightBackingScene();fixedViewLight=viewLightMapId!=0;}
 #endif
     if(!fixture){auto library=GetModuleHandleW(L"minhook.x64.dll");wchar_t location[32768]{},exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);
-        if(!library||!GetModuleFileNameW(library,location,32768)||_wcsicmp(location,(std::filesystem::path(exe).parent_path()/L"minhook.x64.dll").c_str())||!nativeSlotFilter.start(slotInputScope,library,deadeyeMotionScope,torbWeaponSelectionScope)){stop();return reject("native slot input filter");}}
+        if(!library||!GetModuleFileNameW(library,location,32768)||_wcsicmp(location,(std::filesystem::path(exe).parent_path()/L"minhook.x64.dll").c_str())||!nativeSlotFilter.start(slotFilterScope,library,controlMotionScope,torbWeaponSelectionScope)){stop();return reject("native slot input filter");}}
 #ifdef OWMC_LIVE_BLEND
     std::error_code traceError;wchar_t tracePath[32768]{};bool traceRequested=false;
     if(!fixture&&GetModuleFileNameW(moduleHandle,tracePath,32768)){
@@ -641,7 +655,7 @@
     out<<",\"slotInputFilter\":"<<(nativeSlotFilter.enabled?"true":"false")<<",\"slotInputRestored\":"<<(nativeSlotFilter.restored?"true":"false")<<",\"slotFilteredKeys\":"<<nativeSlotFilter.filteredKeys<<",\"slotFilteredMouse\":"<<nativeSlotFilter.filteredMouse<<",\"slotBufferCalls\":"<<nativeSlotFilter.bufferCalls<<",\"slotDataCalls\":"<<nativeSlotFilter.dataCalls<<",\"slotKeyQueries\":"<<nativeSlotFilter.keyQueries<<",\"slotMessageCalls\":"<<nativeSlotFilter.messageCalls;
 #ifdef OWMC_LIVE_BLEND
     // HNZ1 diagnostics exist only with the live compositor camera owner.
-    out<<",\"hanzoCameraSelections\":"<<hanzoGameplayCamera.selected.load()<<",\"hanzoCameraRefusals\":"<<hanzoGameplayCamera.refused.load()<<",\"hanzoCameraReason\":"<<std::quoted(hanzoGameplayCamera.reason.load());
+    out<<",\"hanzoControlProtocol\":2,\"hanzoCameraSelections\":0,\"hanzoMotionLocked\":"<<(hanzoMotionScope()?"true":"false")<<",\"hanzoMotionFrames\":"<<hanzoMotionFrames.load();
 #endif
     out<<",\"deadeyeInputProtocol\":1,\"deadeyeInputGuardAvailable\":"<<(active&&nativeSlotFilter.enabled&&!nativeSlotFilter.restored?"true":"false")<<",\"deadeyeMotionLocked\":"<<(deadeyeMotionScope()?"true":"false")<<",\"deadeyeMotionKeys\":"<<nativeSlotFilter.motionKeys<<",\"deadeyeMotionMouse\":"<<nativeSlotFilter.motionMouse;
 #ifdef OWMC_LIVE_BLEND
```

- NativeLocomotionController：真实锁期丢弃旧位移、速度归零并中止移动，移除 HNZ1 全零速度恢复；保留其他英雄/Deadeye 分支。[已集成 integrator]
- client Mixin 配置登记 HanzoQTravelMixin 一次，HostCameraMixin 使用 cameraRotation 冻结朝向；原 travel/movement/collision 注册保留。[已集成 integrator]
- pose_observer.cpp：完整替换 HNZ1 相机选择为 HNZ2，同一输入 owner 的 slot/motion scope、失焦撤销、同次施法拒重入、采样抑制、stop 清理及 live 诊断均已接入。[已集成 integrator]
- 核对既有 HostPoseReader 能力验证、WorldFrameMapping 尾部写入、WorldFrameExporter hanzoControls 诊断、Motor/Input movementBits；无需重复添加。保留现有 hanzo-q-controls，脚本已改为锁期/解锁专项；冷启动选择 v46、构建支持列表已扩展，命令见 INTEGRATION-20261027.md。[已集成 integrator]

**????/?????Guest JAR + ??? DLL?** ? v45 HNZ1 ??????????? Guest ????????????DLL ??????? allowlist ? Claude ?????????????????????? `tools/build_live_passthrough.ps1`????????????/???? owner?????????? JAR/DLL?

### ?????

`verify_hanzo_q_controls.py` ???????? Q???????????? D ?????/?????????????????????? 3D ?? ?0.06m??? ?0.001?MC yaw/pitch ?0.25???? yaw/pitch ?0.3??????? ?0.4m??? yaw ?2?/pitch ?1?? MC ???????????????300ms ????????HNZ2 ??? native motion-filter frames ????????? Volley76????? body draw ??????????? skinDraws+fallbackDraws????????? MC ???? native ????? PASS??? capability/???????? BLOCKED??????Q ???????

?????`compileClientJava`?`HanzoControlProofCheck`????????????/??????????/world???/???????????? Java ????????????? C++17 `-fsyntax-only`??? scope fixture?33 ? Hanzo Python ????? `research/hanzo-q-lock-20261027/checks.json`?`final-java.log`?`native-syntax.log`?`original-q-evidence.json`??????mixin ?????colors renderer ? SHA256 ????

Claude ?????????????? **`hanzo-q-controls`**??????? `nativeCastMillis/lockMillis`????? `hanzo-full,hanzo`??????? Q ?? F6/???????????/??/??/cleanup ???????????????????????????
