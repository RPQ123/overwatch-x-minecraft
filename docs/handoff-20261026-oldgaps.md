# oldgaps 交接（2026-10-26）

本线程只做原有英雄缺口审计、代码和离线验证；**没有启动游戏、运行实机脚本、构建/部署 JAR、修改共享文件或提升矩阵验收状态**。下文状态以本轮读取的 `docs/HERO-MATRIX.md` 为准；该文件“Suggested order”中的旧 Genji PARTIAL 建议不覆盖表内较新的 ACCEPTED-live。

## 改动文件

| 文件 | 内容 |
|---|---|
| `guest/src/main/java/lab/owmcguest/NativeSustainRuntime.java` | 用完整 owner/world/source/model/hero 身份区分治疗执行；拒绝倒退快照及 End 后的同执行重开；相同执行重读不重置 Cryo 总额；新增数值诊断。 |
| `guest/src/main/java/lab/owmcguest/NativeSustainPhase.java`（新） | 可独立离线验证的原版 Begin/End 治疗预算与终止状态；只消费已认证快照，不监听按键。 |
| `guest/src/test/java/lab/owmcguest/NativeSustainPhaseCheck.java`（新） | 20 项断言：原版声明的 150 HP 总额、读取空档不补发/补预算、乱序和终止、相同 tick 的 model 更换、world/source 更换、Bastion 连续治疗及无效输入。 |
| `tools/verify/verify_oldgaps_offline.py`（新） | javac Java21 独立断言和现有 named cache 类型检查；Python AST 语法检查。产物只在 `research/asset-cache/oldgaps-typecheck/`。 |
| `research/sprint-20261024/verify_oldgaps.py`（新） | 仅 `/combat` 数字和真实 MC HP；三个独立用例，见下文。沿用 Suite 的确切进程身份、离线 EXE SHA256、六适配器及 foreground 约束。 |

只修改上述范围；未改 NativeSkillReader、任何 Renderer、Hanzo*/NativeHanzo*、Junkrat*/Torbjorn*/IceWall*，也未改 HERO-MATRIX。

## PARTIAL / DEFERRED 逐行结论

矩阵在本范围内有 **11 个空槽 DEFERRED + 美 Shift 1 个 PARTIAL**；温斯顿段另外明确近战 PARTIAL，且未证明 Shift/E/Q 适配。没有把 ACCEPTED-live 的完整保真限制自动扩成此次开发任务。

| 英雄 | 矩阵技能行 | 判断、证据与处理 |
|---|---|---|
| 源氏 | 无 PARTIAL/DEFERRED 行 | 三个历史缺口现已按用户游玩确认 ACCEPTED-live；本轮不改已有接线，不声称补足其余墙体/路径伤害验收。 |
| 麦克雷 | passive — DEFERRED | 明确 `No separate hero passive in scope`；非待实现技能；不造被动、不申请该空槽采证。 |
| 法老之鹰 | secondary — DEFERRED | 无独立副攻击；hover 已在 passive ACCEPTED-live；不重复实现或采证。 |
| 死神 | secondary — DEFERRED | 无独立副攻击；不实现。灵魂球 passive 已 ACCEPTED-live，不属于本轮行。 |
| 士兵76 | passive — DEFERRED | 无独立被动；共享充能另列，不把它当缺失触发。 |
| 猎空 | secondary — DEFERRED | 无独立副攻击；Blink 已归 Shift，不另接。 |
| 猎空 | passive — DEFERRED | 无独立被动；不另接。 |
| 堡垒 | secondary — DEFERRED | 无独立副攻击；Self-Repair 已归 E。只对共用 sustain 路径做预算/终止回归。 |
| 堡垒 | passive — DEFERRED | 无独立被动；不另接。 |
| 半藏 | secondary — DEFERRED | 无独立副攻击；蓄力释放归 primary；不改任何 Hanzo* 文件。 |
| 美 | Shift — Cryo-Freeze — PARTIAL | `NATIVE-MEI-DETAILS.md`、`ASSAULT-DEFENSE.md` 已证明 `05800000000005fe:30` ModifyHealth Begin/End、150 原版 HP / (237−.1)=3.9s；治疗、灭火、root 已接受。`GuestMod.java` 已用 `ALLOW_DAMAGE` 调 `NativeSustainRuntime.protects`，并非完全漏接保护。本轮补完整身份预算及乱序终止，加入真正命中保护钩子的计数，准备保护/中途换英雄验证。可见冰壳属 models 范围，原版 effect 提交/模型还缺证；见采证表。 |
| 美 | passive — DEFERRED | 无独立被动；不另接。IceWall 不在本线程范围。 |
| 黑百合 | passive — DEFERRED | 无独立被动；不另接。 |
| 温斯顿 | melee — PARTIAL（矩阵附加英雄段） | `prepare_native_melee.py` 已含 0009；`NativeMeleeController/Runtime` 已接原版 `0580000000000043:13` TrackTargets 与 node12 的动态 `1dc` 伤害。无需重复实现，缺的是专属 live 验收；新增 cover/open/idle 数值用例。 |
| 温斯顿 | Shift — Jump Pack — 无已证适配 | 旧机 `research/_archive/2026-10/winston-native-scripts.json` 有 010a 移动/目标/伤害声明；没有本机真实提交和起飞/落地对应证据，不能把动画或按键当起跳。追加采证行。 |
| 温斯顿 | E — Barrier — 无已证适配 | 旧机 00fa 有 CreateEntity/CosmeticEntity/Ability 声明，不能直接认定成功放置。追加采证行；不造屏障。 |
| 温斯顿 | Q — Primal Rage — 无已证适配 | 0109 有动画/HealthPool/ModifyHealth/MovementMod 声明，2000 原版充能值不等于已提交变身。追加采证行；不靠 Q 或满能量造效果。 |

## 本次逻辑补齐与诊断

原实现只比较 `phase.tick()!=tick`：同 tick 的 model 更换会错误共用已消耗预算；同一执行的较旧快照可以反复改写 phase/预算，End 也可能被较旧 active 覆盖。现按完整 Scope 检查，并保留已观察到的终止；原版新 Begin 的更大 tick 才能在同一 Scope 重开。新 Scope 仍需 `NativeEliminationRuntime.sessionMatches` 认证，不能单凭传入身份换作用域。

`/combat.sustain` 在原有字段外增加 `casts`、`protectedDamageEvents`、`rejected`、`source`、`model`、`world`。`protectedDamageEvents` 只在已有 `ALLOW_DAMAGE` 回调确实调用 `protects` 并拒绝伤害时增加；它不代表测试已运行。伤害钩子和 `WorldFrameExporter` 的 sustain JSON 导出原本已存在，无需再登记一遍。

## Claude / integrator 需加的共享行

**无需新运行时注册、伤害钩子、场景或素材打包。** 原有 `NativeSustainRuntime::tick`、`ALLOW_DAMAGE`、`/combat.sustain` 导出全部复用。不要加载任何新的原版回调所有者。 [已集成 integrator]（核对既有接线，未重复登记）

在 `research/sprint-20261024/run_batch.py` 的 `TESTS` 赋值后添加：

```python
TESTS += [
    ('oldgaps-mei-protection', ['verify_oldgaps.py', '--case', 'mei-protection']),
    ('oldgaps-mei-switch', ['verify_oldgaps.py', '--case', 'mei-switch']),
    ('oldgaps-winston-melee', ['verify_oldgaps.py', '--case', 'winston-melee']),
]
```

[已集成 integrator]

可选：若统一 `guest check` 也要包含本次纯 Java 断言，在 `guest/build.gradle` 增加（本线程未改该共享配置）：

```groovy
tasks.register('verifyNativeSustainPhase', JavaExec) {
    dependsOn tasks.named('testClasses')
    classpath = sourceSets.test.runtimeClasspath
    mainClass = 'lab.owmcguest.NativeSustainPhaseCheck'
}
tasks.named('check') { dependsOn tasks.named('verifyNativeSustainPhase') }
```

[已集成 integrator]

## 验证与运行参数

已运行：`.venv/Scripts/python.exe tools/check_environment.py`，所有只读前置检查通过；`.venv/Scripts/python.exe tools/verify/verify_oldgaps_offline.py`，20 断言、3 个 Java 源文件类型检查和 Python AST 检查通过。这不是完整 Gradle、MC 实机、融合画面或用户游玩验收。独立编译未生成/部署 JAR。

实机用例 **尚未运行**：

| run_batch 键 | 场景与数值断言 |
|---|---|
| `oldgaps-mei-protection` | 原有 `cleanup` / `wraith-hit`：真实伤害在 Cryo 前减 2 HP；实际新 05fe:30 Begin 后，同一路伤害使 `protectedDamageEvents` 增加且 HP 不降；原版 End 后再次伤害真实减血，随后不再治疗。保护中伤害不使用直接 setHealth。 |
| `oldgaps-mei-switch` | 实际新 Cryo Begin 后立即 H 选麦克雷，必须在 Shift 输入后 3s 内完成真正 model/hero 更换，否则判失败，不把自然 End 后换英雄算通过；新英雄没有持续治疗/保护，wraith-hit 真正减血。若原版禁止中途 H，这个用例应失败并保留证据。 |
| `oldgaps-winston-melee` | 原有 `flight-open`、`melee`、`wall`、`open`：原版 V 的 `accepted/blocked` 增长且墙后目标不掉血；移墙后 `heroId=0009`、`hits/damageApplied` 与目标 HP 一致；空闲不追加命中。不是重放传输验收。 |

上述脚本会在首个选人/fixture 输入前备份现有配置、options、JAR 到私有 `research/oldgaps-profile-*`。协调者仍须在开游戏前备份隔离 profile/save；脚本不把对活跃 save 的文件复制称作一致性存档备份。

参数沿用 `verify_junk_hanzo.py`：`--pid --created --mc-pid --mc-created --world --guest-sha256 --output`，另传 `--case`。当前 Suite 的身份限制仍是 `guest-passthrough-client` + `Overwatch Twilight Switch ...`；若协调者选择 AoA profile，须先在其负责范围扩展/认证 Suite，不能绕过身份限制。

统一构建部署由协调者执行，本线程无打包命令、无新模型资源。接入键后，实际会话中使用：

```powershell
.venv/Scripts/python.exe research/sprint-20261024/run_batch.py --pid <nativePid> --created <nativeCreated> --mc-pid <mcPid> --mc-created <mcCreated> --world "<exactWorldName>" --guest-sha256 <installedSha256> --output research/sprint-20261024/oldgaps-live --only oldgaps-mei-protection,oldgaps-mei-switch,oldgaps-winston-melee
```

## MC 适配与边界

- 治疗按原版 amount/interval 在 MC 每秒 20 tick 分布；150 native HP → 15 MC HP 的总额、`.1` 换算和不中断补发是现有 MC 适配，不是新发现的原版服务器插值。
- Cryo MC 灭火和 `ALLOW_DAMAGE` 保护沿用既有实现；本轮没有扩充为任意药水净化、移除生存规则或伪造技能触发。
- quick-melee 的 MC 球形候选和实际方块遮挡仍是既有适配，不声称完整原版目标过滤；本轮只准备温斯顿专属验收。
- 当前保护验证是隔离创造实验室中绕过创造免伤的真实 vanilla/Fabric 伤害路径；不自动关闭完整生存伤害矩阵缺口。
- 冰壳 Renderer/原版网格留给 models；温斯顿 Shift/E/Q 没有足够提交证据，保留未实现。

## 采证需求

以下是交给 capture 线程或 Claude 的**数据行**；只读全部原版 graph 的前/中/后变化，并保留 process creation/source/model。旧机图定义仅帮助定位，不能充当本机技能成功证据。

| 英雄 | 技能 | 按键/时长 | 要看的 graph/节点 |
|---|---|---|---|
| 美 | Shift Cryo 保护 | Shift 120ms；观察 5s；隔离实验场在前/中/后各一次已有 wraith-hit | `05800000000005fe:30` ModifyHealth Begin/End；原版 `237` 时长、150 amount；对应 `/combat.sustain` active/nativeTick/source/model/protectedDamageEvents、真实 HP。运行 `oldgaps-mei-protection`；不是仅看创造免伤。 |
| 美 | Shift 中途换英雄 | Shift 120ms；实际新 Begin 后立即 H/选麦克雷，3s 内须完成；再观察 1s | `05800000000005fe:30` 原版 End/模型注销与新 local/model/hero；`/combat.sustain` 不再 active，真实 HP 无旧治疗/保护。运行 `oldgaps-mei-switch`；H 被拒绝须如实记录。 |
| 美 | Shift 可见冰壳 | Shift 120ms；完整观察 Begin→End 5s | `05800000000005fe` 全图，寻找实际 Effect/CosmeticEntity/CreateEntity Begin/End 与实体 GUID/模型 GUID；node30 只证明治疗，不证明冰壳。若只服务器有创建声明，记录其未执行，不用猜节点号；转交 models。 |
| 温斯顿 | V quick-melee | V 120ms，墙后与移墙后各一次，间隔至少 800ms；末尾空闲 600ms | `0580000000000043:13` TrackTargets、`:12` ModifyHealth 与 `0d800000000001dc` 动态伤害；确认 hero `02e0000000000009`、targetHealth/accepted/blocked/hits/damageApplied。运行 `oldgaps-winston-melee`。 |
| 温斯顿 | Shift Jump Pack | 分别 Shift 120ms / 900ms；每次观察至少 5s，含着地；前后取全部图快照 | 候选 `058000000000010a:10/12` MovementMod、`:14` TrackMovement、`:16/19/45` TrackTargets、`:15/20/44/57` ModifyHealth、`:58` Ability；记录全部节点真实时间变化、速度/重力声明、起飞/着地对应与撞墙取消。上述是旧声明候选，尚无本机提交认证。 |
| 温斯顿 | E Barrier Projector | E 120ms；观察 8s；若只有预览再分别记录左键确认、右键取消（每次独立） | 候选 `05800000000000fa:2` CreateEntity、`:14` MovementMod、`:20` Anim、`:23` CosmeticEntity、`:26` Ability；记录全图及新实体/owner/GUID；区分按键/搜索/预览与真正创建提交。 |
| 温斯顿 | Q Primal Rage | 明示诊断充能至当前原版 cost（历史为 2000），Q 120ms；观察至少 15s；活跃期一次 V、一次 Shift，分别取快照 | 候选 `0580000000000109:6/51` Anim、`:7` HealthPool、`:9` ModifyHealth、`:14` MovementMod；同时记录 `010a`、`00fe` 全图及 hero/model/health/maxHealth、真实 native charge drain/End。需要真正的变身/攻击提交，不以满充能或动画替代。 |

## 未解决项

美保护实际伤害、Cryo 中途换英雄、冰壳原版提交/呈现和温斯顿近战专属 live 验收均未在本线程取得；温斯顿三个技能仍待表内采证。11 个 unused slots 不属于缺失实现。保留所有已有修改和私有失败证据；没有提交任何文件。

统一源码/命令/分批计划见 [INTEGRATION-20261026.md](INTEGRATION-20261026.md)。标记仅表示源码/计划已接入；未执行游戏、素材安装或实机采证。最终全量compileClientJava日志在 research/sprint-20261024/integration-round2-20261026/compile-final.log。

## B15 失败修正（本节覆盖前文对应测试前提）

读取了 `research/integration-results/B15-test.log` 及三个 `integration-live-B15-oldgaps-*/result.json`，未运行游戏或实机脚本。**B15 的 `oldgaps-mei-protection` 已通过且 cleaned=true，保留该接受证据。** 不把后续两个失败解释成保护回归。

### 根因分级

| 用例 | B15 数值证据 | 结论 |
|---|---|---|
| `oldgaps-mei-switch` | 两个 Shift 输入分别为 wall `1793022787376` / `1793022797598`，仅隔 **10.222s**；前次 Cryo 结束观测为 `1793022791717`，距第二次输入 **5.881s**。重新选 Mei 后仍为同一个 model `2147485796`；sustain 绑定仍为 Mei、无 sustainError/rejected，旧 End tick `22144` 未推进。 | 符合同英雄冷却未恢复/前提未满足；`cleanup` 和 MC `casts=0` 不能重置原版冷却。没有证据证明读取断开，也没有采得可据以认定精确原版冷却时长的数值。新增等待是测试隔离策略，不宣称“原版冷却=15s”。 |
| `oldgaps-winston-melee` | 原版 actor 已为 hero `02e0000000000009`、model `2147485867`；第一拳 runtime `heroId=0009, accepted=1, blocked=1, rejected=0`，真实目标 HP=20。两次 V 输入仅隔 **1.444s**；第二拳后 accepted 仍为 1。 | 已证明选人和至少一次近战绑定/消费成功，不能按 sustain.hero=0 判断失败。sustain 只支持 Mei/Bastion，在 Winston 上归零是正常行为。旧结果没有 0043 原版节点快照，**尚不能进一步证明二拳是原版未提交，还是原版提交过但客户端漏接**；本次补足恢复前提和可分辨的诊断，不猜改生产读取器。 |

### 本次改动（仅 oldgaps 文件，无共享改动、无需新 JAR）

- `research/sprint-20261024/verify_oldgaps.py`：每个 Mei Cryo 用例在正常选人后额外等待 **15s**，保持 exact identity/foreground/hero/model 检查，确认本英雄 sustain 绑定和 inactive 后只发送一次 Shift。仍必须观测实际新的 05fe:30 执行，不以等待、按键或 `casts=0` 当成功。
- 同文件：Winston 每拳前等待原版 **0043:13 TrackTargets End**，松开 V，再等待 **2.5s** 恢复余量；只发一次新 V。移墙后确认 `wallBlocks=0`，仍需 `accepted/hits/damageApplied` 与真实 HP 一致。不会重试乱发攻击或放宽伤害断言。
- 同文件：每个 sample 增加只读 native hero/model 及小范围原版节点数字，Winston 保存 `0043:8/12/13/15/30`；Mei 保存 `05fe:30`。失败时保留 `nativeMeleeSteps.covered/open.before/after/progress`，第一拳已通过部分也立即保存。`no-new-native-TrackTargets` 表示本次没有更晚原版记录；`native-TrackTargets-without-client-admission` 表示原版记录已推进而 accepted 未推进；`accepted-without-target-hit` 表示已消费但没有目标命中。仅看到更晚 End 记录只用于诊断，不补造原版 Begin/攻击。
- 同文件：中途换英雄使用本脚本自己的轻量原版 actor 读取和有界选人函数；仍只有一次 H，必须正向证明 picker mode2 才点击、确认后必须实际 FPS mode1 + 麦克雷 + 新 model，且必须在本次 Shift 输入后 **3s** 内出现。沿用两次 650ms 菜单等待、原有坐标换算、进程身份/前台/尺寸检查；省去通用 Suite 完成后的额外稳定延迟和完整武器扫描对这 3s 窗口的占用。H 被原版拒绝或实际换人太晚仍失败，不能当自然 End 后换人通过。
- 新建 `tools/oldgaps_test_policy.py`：纯数值进度分类，以及注入身份/按键/原版视图读取函数的有界选人逻辑；不直接访问进程，不添加任何回调。
- 新建 `tools/test_oldgaps_test_policy.py`：10 项离线回归，包括 B15 的 Winston 选人/首拳真实数值、原版未提交/漏消费/命中无 HP 证据分级、sustain=0 不误判，以及 H 被拒绝不盲点、不二次 H、实际换人迟于截止不能通过。
- `tools/verify/verify_oldgaps_offline.py`：补充两个新 Python 文件的 AST 检查。

已运行（均为离线，无游戏输入）：

```powershell
.venv/Scripts/python.exe -m unittest discover -s tools -p test_oldgaps_test_policy.py -q
.venv/Scripts/python.exe tools/verify/verify_oldgaps_offline.py
```

结果：新增 **10 tests OK**；原有 **20 phase checks passed**、3 个 Java 源文件类型检查和 Python AST 检查通过。没有构建/部署 JAR，没有修改 Suite、run_batch、NativeSkillReader 或其他共享文件；本轮生产 Java 无变化。

### Claude 需重跑与会话安排

**需重跑键：`oldgaps-mei-switch,oldgaps-winston-melee`；不要求独立会话。** 新脚本已内置等待，run_batch 无需改键或拆批；可以在同一经过身份认证的会话依次运行。`oldgaps-mei-protection` 的 B15 通过结论保留，不要求为此次测试前提修正重复运行。

```powershell
.venv/Scripts/python.exe research/sprint-20261024/run_batch.py --pid <nativePid> --created <nativeCreated> --mc-pid <mcPid> --mc-created <mcCreated> --world "<exactWorldName>" --guest-sha256 <installedSha256> --output research/sprint-20261024/oldgaps-B15-fix --only oldgaps-mei-switch,oldgaps-winston-melee
```

原版未允许 H 中断 Cryo 时，保留该真实限制；若温斯顿仍失败，优先读取新的 `nativeMeleeSteps.open.progress` 及前后 node13/8/15，依据实际分类再处理。**此次只完成源代码和离线修正，没有声称两个重跑键已实机通过。**
