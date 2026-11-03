# builders 第三轮交接（2026-10-27）

范围：用户第二次试玩反馈 8 / 9b。只改 builders 文件及对应验证，未改共享文件、rockets 文件或其他英雄。
未开游戏、未构建/部署 JAR；下述为源码和离线检查结果，实机手感待集成端验收。

## 改动与 MC 适配

### 狂鼠左键手雷

- 发射时不再启动 1.5 秒引信；第一次碰到向上的实体碰撞面才记下 `firstGroundAge`，30 个 MC tick 后引爆（20 TPS 时 1.5 秒）。
- 墙壁、天花板不启动计时；后续地面/墙面反弹不重置计时。直击敌人仍立即施加直击伤害并爆炸。
- 空中未触地的孤立手雷仍在超过 200 tick 时回收，不会在空中按旧的发射引信自动爆炸；晚于 170 tick 触地的手雷也有完整 30 tick 地面引信。
- 用户要求的双倍威力只作用于左键：直击 40→80，爆炸 80→160（换算 MC 满额分别为 8 / 16 HP；爆炸仍按原两环衰减/遮挡）。显示仍为上一轮的 2 倍。
- 地形强度由上一轮 `Helix(1.5)+.25=1.75` 改为 `3.5`，继续调用同一个 `NativeTerrainBurst`，沿用原生抗爆、不可破坏方块及已加载范围检查。
  伤害和遮挡判断先于破坏地形；没有重复破坏实现、额外地形伤害或击退。强度翻倍并不表示实际破坏方块数量必为两倍。
- 地雷、夹子、死亡炸弹的伤害及死亡炸弹引信沿用原值。原版左键 WeaponVolley 新 tick 的基线/认证门禁不变。

### 狂鼠 Shift 地雷自身击退

已接入 [rockets 第三轮接口](_archive/2026-10/handoff-20261027-rockets.md)，替换旧 `p.addVelocity(...);p.velocityModified=true`，没有叠加旧击退：

```java
NativeRocketSelfImpulse.INSTANCE.concussiveMine(
    w,p,b.nativePid,b.scope.source(),b.scope.model(),b.nativeTick,b.pos,3.0)
```

[已集成 integrator]

- `NativeJunkratController.poll` 在原版 `096a:12` 投掷新 tick 准入时捕获 `HostPoseReader.Pose.pid()` 与节点 uint32 tick，服务端校验 PID>0、0<tick≤0xffffffff，并存入该地雷 Body。
- 延迟引爆时原样传递这份投掷证据及 owner/world/source/model，既不把 MC 时间或右键沿当作原版 tick，也不借用另一颗地雷的执行令牌。
- 原版地雷实体缺失导致右键没有可读引爆提交的既有证据/适配保持：前台有效输入的右键沿只消耗当前完整 Scope 已认证投掷产生的 MC 地雷。
  `detonateMine` 从仅 UUID 改为完整 `Scope` 校验，跨世界/英雄/来源的旧请求不能消费当前地雷。不是声称已经接通原版引爆节点。
- 共用辅助负责同一 Scope/nativeTick 仅一次、实际发布本地击退 cue、会话与加载/遮挡检查。builders 不再自行写第二次速度，也没有检查必须先跳起。
- 爆心保留 MC 地雷实际位置 `b.pos`，未搬到玩家脚下。脚边地面地雷爆心低于玩家中心，会产生正 Y，站地/空中走同一辅助；3 格范围、实际遮挡及方向仍生效，远处/隔墙爆炸不成为远程强制跳跃。
- 共用击退当前系数归 rockets 管理，本线程没有修改它的文件、Pharah 飞行逻辑或共享模块注册。

## 改动文件

- `guest/src/main/java/lab/owmcguest/NativeJunkratGrenadeTuning.java`
- `guest/src/main/java/lab/owmcguest/NativeJunkratRuntime.java`
- `guest/src/client/java/lab/owmcguest/NativeJunkratController.java`
- `guest/src/test/java/lab/owmcguest/NativeBuildersTuningCheck.java`
- `tools/junkrat_live_verification.py`

无需新增共享登记行；沿用已集成的 `NativeRocketSelfImpulse` / client 注册及 `/combat` 状态汇出。

## 数值诊断与建议实机检查

`/combat` 的 junkrat 新增/更新：

```text
grenadeFuseStarts = first-ground-contact
grenadeFuseTicks = 30, grenadeFuseSeconds = 1.5
grenadeGroundContacts, grenadeFuseExplosions, lastGrenadeFuseElapsedTicks
grenadeDirectDamage = 80, grenadeBlastDamage = 160, grenadeDamageMultiplier = 2
grenadeTerrainStrength = 3.5
mineImpulseRequests, mineImpulses, lastMineNativePid, lastMineNativeTick, mineImpulsePolicy
```

`tools/junkrat_live_verification.py` 会把新引信/威力/地形参数、地雷令牌和共用 `rocketSelfImpulse` 状态写入现有 base 结果。
该 base 只是基础回归；没有把一次基础射击自动提升为全部手感/火箭跳验收。

集成端在备份世界、部署合并 JAR 后：

1. 发射向空中的手雷，确认超过发射后 30 tick 仍未定时爆炸；先碰墙/顶面再触地，确认只有首次向上地面碰撞启动引信。
2. 在可见地面反弹多次，记录 `grenadeGroundContacts` / `grenadeFuseExplosions` 增量和 `lastGrenadeFuseElapsedTicks=30`；反弹不能延长引信，直击应立即爆。
3. 用足够 HP 的目标区分直击与范围伤害，避免 20 HP 目标死亡截断掩盖倍率；确认 80/160 的原版单位适配，地形 1.75→3.5 的实际破坏更强且不绕过硬度/遮挡规则。
4. 关闭创造飞行，在脚边地面投掷地雷，保持站地不按跳跃再右键；应见 `mineImpulses` / 共用 `minePushes` 各增一、正 Y 和实际离地。另测空中引爆、落地恢复移动。
5. 重复右键不得二次 kick；远处/隔墙没有强制 kick。切世界/英雄后旧地雷请求不得消费新 Scope；核对 PID/tick 来自实际投掷记录。
6. 基础手雷/地雷/夹子及死亡被动独立回归。轮胎引爆仍为既有 DEFERRED，没有趁本轮启用或伪造。

## 离线检查与统一打包

已通过 18 项离线测试：`test_builders_tuning` 1 项（268 个 Java 断言）、`test_native_builders` 9 项、`test_junkrat_verification` 8 项。
覆盖首次触地/墙顶面/反弹/晚落地、数值倍率、实际编译字节码的即时直击/共享破坏顺序/单次共用击退/真实投掷令牌/完整 Scope 消费；保留既有托比昂升级与拒拾检查。
16 个 builders Java 源文件显式类型检查通过；最终修改后的 `compileClientJava` **BUILD SUCCESSFUL**（21 秒，任务 UP-TO-DATE；另以显式 javac 检查了本线程当前源码）。
前提检查 `tools/check_environment.py` 通过（Python 3.13.13）；本线程文件无冲突标记/尾随空白，Python AST 解析通过。
数值及源码哈希证据：`research/sprint-20261024/builders-20261027-offline/verification.json` / `source-hashes.json`，均为本地离线证据。

```powershell
.venv/Scripts/python.exe tools/verify_native_builders_compile.py
.venv/Scripts/python.exe -m unittest discover -s tools -p test_builders_tuning.py -q
.venv/Scripts/python.exe -m unittest discover -s tools -p test_native_builders.py -q
.venv/Scripts/python.exe -m unittest discover -s tools -p test_junkrat_verification.py -q
cmd /c "set GRADLE_USER_HOME=%CD%\tools\gradle-cache&& tools\gradle\gradle-8.10.2\bin\gradle.bat -p guest --console=plain --no-daemon compileClientJava"
# 以下仅供 Claude 统一打包部署，本线程未执行：
./tools/build_guest.ps1
```

离线检查不证明站地实际离地、用户手感或完整游戏验收；这些仍待上述实机复测。

## R27-TC / R27-TT 托比昂复核（2026-10-27）

本次只读既有实机结果，没有开游戏或改 Java / 共享文件；`junkrat-base` 通过为集成端本轮实机结论。

### calibrate 的 Map cycle 定位

- 原始证据：`research/sprint-20261027/r27-TC-torb-calibrate/result.json`，`passed=false`、`cleaned=true`。
- Shift、E、2、M1、1 五阶段均已完成，各有 `factoryAfter-*`；Q 授能已完成，原版 Q 已正常发送。
  Q 阶段留下两条 trace，最后一条 wall=1793034409061；没有 `factoryAfter-Q-core`，因此在该阶段 22 秒观测窗内中断，而非放置/锤击步骤中断。
- 错误文本只在 `tools/native_map_snapshot.py:50` 产生：`node` 越界、节点重复，或遍历数超过初读 header count，三者共用 `Map cycle or count mismatch`。
  `WeaponStates.sample_weapon(False,True)` 遍历原版 `statescript_logger::s_scriptStates` 外层 Map 及其逐实例内层 Map；旧 calibrate 未重试失败的整帧读取，任一此类错误立即结束全部采证。
- **能确认的是只读 logger Map 快照被一致性门禁拒绝。** Q 刚开始时 Map 并发变化可产生这种错误；旧结果没有堆栈、Map 地址/header 或重读结果，无法确定是临时并发变化、外层/哪个内层 Map，还是持续坏树，不能把后者或前者写成已证实。
- 放置独测前移只在 `verify_torb_kit.py`，calibrate 不调用该脚本；calibrate 原有 Shift→E→2→M1→1→Q 顺序未改。
  本轮诊断和 Python logger 观测均只读原版 Map，没有写树；缺乏证据将此错误归因于 MC 放置前移或诊断改动。采样时机影响并发窗口仍无法靠旧结果排除。
- Q trace 已出现 `01c2:19` 等 Begin（tick=30288，finished=false），所以不是“Q 根本没有原版激活”；本次缺的是后续完整结束窗口，不能认证该次完整 Core 生命周期。

### 采证脚本补强（无需新 JAR）

- `tools/torbjorn_verification.py` 新增 `calibration_snapshot`；仅对这个精确 Map 错误重读**整个** `sample_weapon`，至多 3 次、间隔 .04 秒，不重发动作或授能。
- 每次先验证实机身份/前台；返回样本再核对 model/local controller。其他读错或身份变化立即失败，不放宽 ABI/身份门禁、不发布半帧。
- 保存 `readFailures` 的 phase/attempt/堆栈；如果失败来自 `snapshot_map`，另存 address/key_format/head/count/root/node/visited，下一次可区分错误条件和 Map 层次。
- 发生重读缺口后重建变化基线，避免把缺口后的样本合成为新 Begin/End。即使恢复并采完，`captureCompleted=true` 但 `captureQualityPassed=false,passed=false`；持续失败仍原异常退出。
- `calibrate_torb_kit.py` 在失败清理时也保存部分 `changed-definitions.json` / `changedNodesByPhase` / 信号标志，另存 `failurePhase,errorTraceback`，不再因 Q 读错丢掉锤击阶段摘要。
- 没有修改共享 Map reader、capture 工具或 production bindings；原始 TC/TT 结果保持原样。

### TT BLOCKED 的具体缺口

TT 的 `cases.placement=PASS`：`deployRequests/deployAttempts/deploys` 均 0→1，`turret=true`、1 级/150 HP。
后续炮台真实射击 11→22、命中 11→22，`scrapDrops=3,scrapTaken=2,scrap=50`；所以本次不是“炮台仍没放出来”，也不是废料计数全失效。

阻塞在 `hammer`：两次原版 M1 后，`hammerRequests=hammerSwings=hammerHits=0`；原版前后同 model=2147485791、`strikeTick=0→0`，只见 `00f3:34` tick=23408 且没有新变化。
当前准入必须是 **`05800000000000f3:24` 新 tick，且 `00f3:29`（swing）或 `00f3:10`（repair）同源 active**。
本次三个节点的 MC 只读诊断均 tick=0/active=false；原版 logger 也没有新 strike24，故保持 BLOCKED，不能从“按过2”、节点34或炮台击杀替代锤击提交。
TC 同样在 `hammer-swing` 阶段没有任何变化，之前 V3 的校准通过也未证明 hammer24 可用。

### 对应 capture 组与采集前提

复用 `docs/INTEGRATION-20261026.md` **C08 / group=`torbjorn`**，仅这组，冷启动隔离；不跑其他坦克/辅助组。
入口与身份/备份流程详见 [capture 交接](_archive/2026-10/handoff-20261026-capture.md)，准备/采集入口为 `research/sprint-20261024/capture_blocked_skills.py`。

| 顺序 / case | 本次对应缺口 / 重点 | 必要原版前提 |
|---|---|---|
| `torbjorn-hammer-select` | 2 是否真正切锤；采全部 controller/model graph、00f3 变量，节点34单独不足为证 | 集成的 Torb 1/2 专属守卫例外；正常第一人称、前台；先记录空闲基线 |
| `torbjorn-hammer-strike` | **当前直接 BLOCKED 项**：M1 后 00f3:24 新 tick 与 29/10 active 的先后关系；同时看23及全图 | 已确认真正切锤，面向原版接触距离内目标；prepare 强制 `--keep-selected`，不能重新选人丢武器状态 |
| `torbjorn-hammer-repair` | 修理/升级分支缺口：00f3:10/24/29 及目标身份 | 原版已损坏炮台、切锤且在接触距离；MC 炮台不能满足原版修理目标；同样 `--keep-selected` |
| `torbjorn-scrap` | 可选资源语义追踪；本次已有 MC 废料掉落/拾取证据，不是当前 blocker | 近前真实原版死亡掉落废料；MC 账本入账不能当原版资源信号 |
| `torbjorn-core` | TC 的 Begin 已见，但需无缺口窗口与原版护甲/炮台/攻速语义 | prepare 后由既有控制器/自然充能使当前原版 Q 真正可用；采证本身不授能；重点 01c2:17/19/20/21/30、00f3 |
| `torbjorn-core-end` | 本次 TC 未采完的结束阶段；观察 End，不重放首次已 active 样本 | 同 model 的 Core 已 active，临近真实结束再 prepare/capture，`--keep-selected`，可用 .5 秒基线 |

所有 case 都采当前拥有的全图，不把 watchHints 当节点白名单；默认 3 秒基线+3 秒动作窗、100 Hz。
原版目标/损坏炮台等前提不具备时保持 BLOCKED，不用 MC 场景、按键或静态声明补造原版提交。
每次失败另开新证据目录重新 prepare，保留同组同会话阶段身份；同一进程不切到别的 capture 组。
首选先完成 hammer-select→hammer-strike，确认实际提交，再运行完整 torb 验收；若 strike24 实际出现但 MC 不准入，应判 FAIL，届时检查 29/10 同源 active 的窗口，不能继续归类为缺信号。

### 本次离线验证

13 项 `test_torbjorn_verification` 与 9 项 `test_native_builders` 全通过，无 skip；新增真实 TC/TT 回放、C08 对应、真实 snapshot_map 计数撕裂 fixture、整帧恢复/三次上限/身份拒绝检查。
Python AST 检查通过；本次未改 Java，不需要构建 JAR。没有实机重试或将 TC 的失败改为通过。

## 用户第五次试玩反馈：常规炮台恢复 1→2，Core 临时 3 级（2026-10-27）

本段为当前炮台等级规则，取代前文历史轮次的“锤子永久 1→2→3”。

- `NativeTorbjornTuning.MAX_LEVEL` 改为 **2**，新增 `CORE_LEVEL=3`。两次有效、满血锤击仍可 1→2；2 级满血继续敲击不累计升级进度、不升 3。受损炮台仍优先修理。
- 炮台保存的基础等级只有 1/2；2 级在真实 Core 生命周期 active 时显示/作战为 3 级，结束恢复 2 级及 300 原版单位 HP 上限（30 MC HP）。Core 期间 800 单位上限、火箭、攻速及护甲沿用现有实现；Core 期间从 1 级锤到 2 级也只临时显示 3，结束保存 2。
- 原版放置/hammer24/29/10/Core19 等认证门禁、Core Begin 去重与 End 撤销未改；模型继续复用现有 1/2/3 级原版模型件，无需重打模型包。
- **护甲包本人不能拾取保留**：UUID 排除、本人拒拾计数、其他合格玩家/村民拾取规则及消耗均未改。
- `/combat.torb.maxLevel=2,coreLevel=3`；`baseLevel` 表示常规等级，`level` 表示当前有效等级。复用已有状态汇出，无共享文件/注册行变更。[已集成 integrator] 已核对既有 torb 状态导出、server/client 登记及 `torb` 测试键，无重复接线；本轮 1/2 基础等级、Core 临时 3 及本人拒拾由原运行时实现。

改动文件：`NativeTorbjornTuning.java`、`NativeTorbjornRuntime.java`、`NativeBuildersTuningCheck.java`、`research/sprint-20261024/verify_torb_kit.py`。
实机脚本已移除“永久 2→3 / Core End 保留 3”的旧断言，改为真实继续锤击仍封顶 2、Core 临时 3、End 回 2 且 HP≤300；本人拒拾与他人拾取断言保留。

离线验证：**23 项通过，无 skip**（tuning 1 / native builders 9 / torbjorn verification 13），其中 Java tuning **291 个断言**覆盖 2 级封顶、重复 Core 来回、Core 内升级后结束恢复 2 及本人拒拾。
16 个 builders Java 文件显式类型检查通过；完整 `compileClientJava` **BUILD SUCCESSFUL，37 秒，compileJava/compileClientJava 均实际执行**。
前提检查、Python AST 与本次文件空白/冲突检查通过。本线程未开游戏、未构建/部署 JAR；统一打包命令仍为前文的 `./tools/build_guest.ps1`，由集成端执行。

建议实机：正常升到 2 后继续锤击确认不升 3；开 Core 确认临时 3/火箭，真实 End 后回 2/上限 300，重复一轮确认不累计永久等级；同时验证自己的包留在地上、其他合格对象可拾取。
原版锤击信号仍须按前节 C08 满足前提，缺提交时维持 BLOCKED；本次离线数值检查不代替该实机验收。
本地源码哈希和验证摘要：`research/sprint-20261027/builders-feedback5-offline/verification.json`。

Integrator 补记：现有共用server/client登记及原生矿雷PID/tick/Scope调用已核对；本轮rockets两处共享movement叠加已接，未再加本人速度或重复×1.5。[已集成 integrator]

第三轮集成索引：[INTEGRATION-20261027.md](INTEGRATION-20261027.md)。上述标记只指源码接线/删除旧行/既有接线核对，不表示实机验收。全量compileClientJava --rerun-tasks通过（27秒，3任务实际执行），未遇Loom锁、未删锁文件；未开游戏、打包JAR/DLL或部署。原“待接线”段落保留交接时历史，最新结果以本补记为准。
