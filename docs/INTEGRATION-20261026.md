# 2026-10-26 共享集成交接

integrator 已处理两轮共十一份交接：support、tanks、builders、symmetra、colors、stability、voice、oldgaps、models、hanzo、capture。可接入的共享接线与指定文件修改已落地，对应原条目标 `[已集成 integrator]`；有明确采证前提的项目见末节。只改源码与文档，没有开游戏、制作/安装 JAR 或 DLL、下载/安装素材、操作存档、提交代码。既有修改及未跟踪文件保留。

## 集成与离线结果

- support：两条 travel、8 个场景、专属状态/回收、3 个严格键；原有模块不重复登记，乱的倍率不再接共享伤害层。
- tanks：12m `roadhog-split-lab` 及路由、7 个 `-signals` 键；四英雄原有注册/travel 保留。
- builders：两个 Mixin、7 个场景、清理与诊断、5 个键；已有 `junkratError` / `torbError` 保留单份。HTTP cleanup 与 NativeCombatRuntime.close 均保留 builders 点名的原样清理行；`NativeCombatScene.cleanup()` 再集中回收三套场景，幂等覆盖场景切换，源码已注释；GuestMod 在保存前也走此清理。
- builders 共享策略：`NativeChargeController` 独立 `junkTire` reader，校验 source/model/hero/四节点；windup/control/view 或同 owner/world/source/model 的新鲜 MC tire 排除充能，未知绑定拒绝 credit。托比昂仅在核实本地 Torbjorn、原版默认第一人称、前台且隐藏光标时放行主键盘原生 1/2；数字小键盘、其他英雄、滚轮/中键、Deadeye 锁沿用原策略。Python guard 与 native filter 同步；`pose_observer.cpp` 仅补现有 WndProc 同谓词与 `start` 条件回调，避免另外一层继续吞掉 1/2，没有新增 hook owner。
- symmetra：5 个新 action 和已有 placement 转交 `SymmetraLab`，加专属回收、7 个键；打包工具允许真实 03/04 根。旧 placement 的通用 heroLab 实现保留但 HTTP 不再走它。
- colors：禅雅塔 core/glow 两层按交接代码接入；新增龙骨骼/材质诊断。查莉雅沿用已审计橙红包，源码注释蓝色变体必须等原版阵营证据，未擅自切蓝。
- stability：Suite.choose 转交稳定选择器，voice 子类刷新尺寸后 super 的行为保留；Reinhardt tick/travel 均增加 inputActive 检查。
- voice：可选弹药准备旁路、优先于通用测试路由的 4 种状态端点、2 个键；旧 Runtime/Events 注册保留。交接初次稳定后又补了容量1/Hanzo弓排除及prepare修改；最终按加标记前最新 SHA256 `f2ce8c0c03957424c9338814bfcc5e0a2dc41d4747778cbf9ff41fa1b014d46d` 复核，共享接口未变，已重新全量编译，期间语音源码未再变化。

`compileClientJava --rerun-tasks` 全量通过：26s、compileJava/processResources/compileClientJava 三任务实际执行。使用 HERO-MODULE-GUIDE 的 Gradle 入口、离线缓存与工作区 Java Temp；未遇 Loom 锁，未清理任何 guest/.gradle 锁。另有 native 生产翻译单元 `-fsyntax-only` 通过、13 项充能门控 fixture、6 项托比昂作用域 fixture、Python AST、47 个唯一测试键/脚本路径、88 个唯一 action 与诊断去重检查通过。全部是离线证据。

本地备份：`research/sprint-20261024/integrator-before-20261026/`；编译日志/检查结果：`research/sprint-20261024/integration-20261026/{compile.log,compile-final.log,native-syntax.log,checks.json}`。原始素材、证据、class 与备份均留忽略目录。

第二轮接线：oldgaps 的 3 个功能键及 `verifyNativeSustainPhase` check 任务已登记；既有 sustain tick/伤害保护/JSON 不重复注册。models 的 `OriginalWorldRenderer` 仅注册一次，新增四个 diagnostics；Mercy/DVa/Lucio/Roadhog 子弹居中，Symmetra 球/真实 +Y 光束/护盾彩色层使用交接 helper，禅雅塔两层保持 colors 路线。

新增主源集 `OriginalEffectFrames`，只发布已有授权状态的 `models`：Mercy 当前治疗/增伤通道与真实目标、Zarya 自盾及真实截断射线、Roadhog 实际钩位置、Lucio 实际音障 owner；Reinhardt 从仍存在的已放置 BARRIER 集合取中心/宽高，使用放置时平面法线，按原 bounds 归一化，不跟随查询时视角转盾；Winston 来自 accepted beam 的实际 present 端点（空射再按真实墙/已加载前缀截断）；麦克雷只在已加载的实际 impact 后发布。另接 Widow 当前 pull.anchor/真实受毒目标、Reaper 已确认出发/落点/幽灵/绽放、Mei 已落地暴雪区域、Genji 已扫过的 dash 段。所有数据沿当前 owner/world/source/model 和实际 lease/事件/tick 时间，重置撤销、不用累计 casts 或查询时间续租。

Hanzo 的现有准备插件/场景/三个诊断入口保持单份，另加 150/400/1100ms 三个 native-scatter 测试别名以适配两参数 dev_cycle。capture 不新增 callback、HTTP 服务或 run_batch 键；已核对其 43 项需要的 MC 场景均有路由，13 组两阶段采证排在全部功能测试之后。第二轮离线检查：capture 24 项 fixture、oldgaps 20 项断言/3 源类型检查通过；全量编译最终结果及源哈希记录于 `research/sprint-20261024/integration-round2-20261026/`，不是实机或像素验收。

第二轮最终 `compileClientJava --rerun-tasks` 全量通过：26s、3 个任务实际执行；沿用 HERO-MODULE-GUIDE 的 Gradle 入口、工作区 Temp 与离线依赖，未遇 Loom 锁、未清理锁文件。离线审计确认 53 个唯一键/23 个功能批、13 组43项采证及全部场景路由、61+10 个唯一模型/颜色包和52个根；检查与本轮独立 diff 留在上述本地目录。

## Claude 后续运行命令（依次；本轮均未执行）

先用对应档案的既有正常 Stop 关闭两游戏并核对恢复结果，备份 profiles/config/saves。AoA 会话用其 scoped Stop；不要误用默认 Fabric Stop。素材提取缓存若已齐全，跳过下面取链步骤；不重复下载/提取。

1. 缺缓存时提取所需根：`integration-20261026-asset-roots.json` 合并 models、colors、builders 与原有额外根，去重后 52 项；模型辅助预载 21 英雄包。039c 的旁支可能使 collect 不完整，必须核对所选 101b/3f08；不能把任意错误当可忽略。

```powershell
.venv/Scripts/python.exe tools/inspect_native_builders_archive.py
.venv/Scripts/python.exe tools/inspect_symmetra_graphs.py
$assetRoots = @(Get-Content -Raw -Encoding utf8 tools/integration-20261026-asset-roots.json | ConvertFrom-Json)
.venv/Scripts/python.exe tools/models_20261026_assets.py --extract @assetRoots
```

2. 安装顺序如下，各批最终包名无交集。models 61 项已包含 Mercy/DVa/Roadhog/Lucio/Symmetra 及 colors 的 10 项禅雅塔/查莉雅包；不再单跑旧 mercy-pistol、symmetra batch、默认 zarya 单包，以免覆盖已选择材质/采样器。`integration-20261026-colors-jobs.json` 从原 colors 20 项原样过滤重名，仅留下 10 项 Hanzo，仍须重新打包以写入新材质/骨骼数据。builders 一条命令包含两类狂鼠包与三级炮台。共 61+10+5+1=77 个唯一最终包；无资源/材质配方的项目仍如实失败，不造模型。

```powershell
.venv/Scripts/python.exe tools/build_mesh_pack.py reinhardt-fire 04000000000001ea
.venv/Scripts/python.exe tools/prepare_native_builders_assets.py
.venv/Scripts/python.exe tools/models_20261026_pack.py --batch tools/models-20261026-pack-jobs.json
.venv/Scripts/python.exe tools/build_mesh_pack.py --batch tools/integration-20261026-colors-jobs.json
```

输出仍为私有 `~/.universal-modder/assets/owmc-mesh/`，不放 JAR/提交。模型包按各自 helper 的原始数组/材质/哈希流程生成；没有把去重清单当成安装或像素通过。

3. 语音先下载 starter（203 条，估算 5.075MB）。catalog/准入表本轮已由 voice 生成，只有采集策略改动时才先运行 `tools/build_voice_optional_catalog.py` 重新生成。完整批与 starter 有 hash 重叠，下载器依 manifest/文件校验复用；完整批只按需运行，不要求全部下载。

```powershell
.venv/Scripts/python.exe tools/voice_download.py --optional --list research/voice-20261026/download-starter.json
# 可选补全：1007条/估算25.175MB；不下载 deferred 或 uncertain 分析任务到播放库。
.venv/Scripts/python.exe tools/voice_download.py --optional --list research/voice-20261026/download-optional.json
```

语音仍写私有 `~/.universal-modder/assets/ow1-zhcn-2016/thnu-full/`。开始用例前要求 assetsReady=true 且 pendingResourceReload=false。无字幕本地分析不是必需下载/打包步骤，按 voice 交接的 `analyze_voice_unsubtitled.py --limit 32` 另做听辨，不自动启用音频。

4. 托比昂输入例外包含 native 源码改动，游戏停止且完成既有恢复后，Claude 需先重建现用 compositor；只改 Python/JAR 不足以放行 1/2。该脚本沿用 `resolve_native_compiler.ps1`，不使用旧 E: 路径。随后每批的 dev_cycle 自行构建/安装 guest，勿用隔离 javac 输出或旧 JAR。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_live_passthrough.ps1
```

## 统一测试计划：每批一个新会话

先做下表全部功能测试，再做后面的 C01–C13 采证。53 个注册键全部列于功能表：保留首轮 47 个，第二轮新增 oldgaps 3 个及 Hanzo 3 个别名。每行正常 Stop 后新建会话，禁止把多行合在一局。表内按 run_batch 注册顺序执行，`--only` 的文字顺序不改变执行顺序。某技能无真实提交时应失败/BLOCKED；`-signals` 通过只表示诊断完成。死亡/被动测试先额外确认完整存档备份。

| 批次 | run_batch 键（逗号分隔） | 关注点 |
|---|---|---|
| B01 | `mei,hanzo,hanzo-full,hanzo-visual` | 既有回归、冰墙/龙/音波颜色与生命周期 |
| B02 | `voice` | Hanzo/Mei旧声音与冰墙回归 |
| B03 | `voice-optional` | starter 后真实装弹信号/状态；无台词 signal_only/skip 不作声音验收 |
| B04 | `voice-roster` | 21人抽查；执行前把 all 展开并将 Reinhardt 放最后，结束后直接停会话 |
| B05 | `mercy,mercy-commits` | 手枪HP、守护天使位移、被动；缺提交明确失败 |
| B06 | `zenyatta,zenyatta-commits` | 谐治疗/乱一次倍率/圣；双层原版珠呈现 |
| B07 | `lucio,lucio-commits` | 音爆/滑墙数值；UNKNOWN歌曲继续阻塞 |
| B08 | `zarya,zarya-cover,zarya-grenade,zarya-self,zarya-e,zarya-q,zarya-e-signals` | 遮挡/自身盾/引力、E纯诊断、材质现用变体 |
| B09 | `roadhog,roadhog-hook-signals,roadhog-split-signals` | 钩子/12m远端分裂证据，父弹不得冒充子弹 |
| B10 | `dva,dva-call-signals` | 驾驶员回归与hero/model前后快照，非机甲验收 |
| B11 | `junkrat,junkrat-base,junkrat-tire,junkrat-wall,junkrat-passive` | create32、轮胎位移/爬墙/引爆、充能排除、死亡仅六弹及复活 |
| B12 | `torb-calibrate` | 先独立采原版1/2、repair10/strike24与Core信号；失败保留证据 |
| B13 | `torb` | 新会话做废料账本/修理/Core完整链；无真实信号不得通过 |
| B14 | `symmetra,symmetra-beam,symmetra-orb,symmetra-shield,symmetra-turret,symmetra-portal,symmetra-placement,symmetra-lifecycle` | 全链与分项；3/47/66无提交不得加盾/放置 |
| B15 | `oldgaps-mei-protection,oldgaps-mei-switch,oldgaps-winston-melee` | Cryo 前中后实际伤害保护计数；3秒内换人；温斯顿近战遮墙/移墙/空闲 |
| B16 | `hanzo-scatter-weak,hanzo-scatter-medium,hanzo-scatter-strong` | 分别150/400/1100ms，require-native-scatter+verify-expiry；输入时长不是q来源，任何回退明确失败 |
| R01 | `reinhardt` | 新会话，仅锤击，结束直接停 |
| R02 | `reinhardt-cover` | 新会话，仅遮挡，结束直接停 |
| R03 | `reinhardt-barrier` | 新会话，仅屏障，结束直接停 |
| R04 | `reinhardt-attempt` | 新会话，仅尝试记录，结束直接停 |
| R05 | `reinhardt-charge-signals` | 新会话，仅冲锋候选诊断，结束直接停 |
| R06 | `reinhardt-fire-signals` | 新会话，仅E候选诊断，避免前次Shift占用 |
| R07 | `reinhardt-shatter-signals` | 新会话，仅Q候选诊断，结束直接停 |

为适配 dev_cycle 只收两个参数，run_batch 增加 `OWMC_RUN_BATCH_ONLY` 默认值；原 `--only` 仍可覆盖。使用 Git Bash，替换每次的键和唯一输出目录：

```bash
OWMC_RUN_BATCH_ONLY='mercy,mercy-commits' bash tools/dev_cycle.sh research/sprint-20261024/run_batch.py research/sprint-20261024/integration-live-B05
```

不要无筛选运行 run_batch 默认全表。原 handoff 的 voice-roster 注册元组仍原样保留；共享 `batch_command()` 仅在执行时展开21人顺序，避免原名单在 Reinhardt 后继续换人。默认 idle 仍关闭。

独立稳定性专项另开会话：静止/结束barrier/结束charge后 Reinhardt→McCree→其他英雄，这是专门复现换人修复的例外，不能与上述技能批混跑。保留 selectionDiagnostics、mode/active/default/vtable、inputActive、hero/model、HP/弹药；失败即收证停止，不盲重按H。另做原版已退出后的正常保存MC、重复Stop、双方正常Stop；MC自然崩溃才检查退出4/无重试/报告保留/API或GLFW正常收尾，无自然复现只记离线通过。

颜色/网格/声音需要实际合成像素/分进程音频验证，渲染帧数或文件存在不足以通过。优先 /combat、实际HP/弹药与像素统计；若确需看图，单张JPEG80长边≤768，多帧合一张≤1024接触表。完整用户游玩接受仍需另外验收。

models 专项与相应英雄功能批一起核：`modelsRenderFrames/modelsSubmissions/modelsRejected/modelsError`、真实端点截墙、盾面与真实 BARRIER 对齐，换世界/英雄/source/model/租约失效后不残留。Pharah 主炮/弹幕/震荡、Soldier 螺旋/力场、Bastion 炮弹沿既有对应 tools verifier 另开正常会话复核；models 没有交付这些项目的新 run_batch 脚本，不能把未执行的专项记为通过。

### 功能测试之后：13 组原版采证

每行也是独立冷启动会话，同一进程 creation 禁止改跑其他 group。以下列出全部 43 个 `prepare --case` 值；它们是 capture 入口参数，不是新增 run_batch 键。每项先 prepare，再由 Claude 满足真实原版地面/目标/受击/武器等条件并预充 Q，再 capture；MC 场景不替代原版前提。

| 采证批 | group | 按顺序执行的 case |
|---|---|---|
| C01 | mercy | `mercy-pistol-select-fire,mercy-guardian,mercy-resurrect,mercy-unknown-e,mercy-glide,mercy-self-heal` |
| C02 | zenyatta | `zenyatta-harmony,zenyatta-discord,zenyatta-transcendence,zenyatta-shield-recovery` |
| C03 | lucio | `lucio-boop,lucio-song,lucio-wallride` |
| C04 | zarya | `zarya-projected-barrier,zarya-energy-absorb,zarya-energy-decay` |
| C05 | dva | `dva-call,dva-postcall-cannon,dva-postcall-boost,dva-postcall-matrix,dva-postcall-unknown-e,dva-postcall-selfdestruct` |
| C06 | roadhog | `roadhog-hook-damage,roadhog-secondary-split` |
| C07 | junkrat | `junkrat-tire-create,junkrat-tire-end,junkrat-death-passive` |
| C08 | torbjorn | `torbjorn-hammer-select,torbjorn-hammer-strike,torbjorn-hammer-repair,torbjorn-scrap,torbjorn-core,torbjorn-core-end` |
| C09 | symmetra | `symmetra-beam-damage,symmetra-photon-shield,symmetra-turret,symmetra-teleporter,symmetra-shield-recovery,symmetra-shield-ammo-probe` |
| C10 | reinhardt-contact | `reinhardt-charge-contact` |
| C11 | reinhardt-pin | `reinhardt-charge-pin` |
| C12 | reinhardt-fire | `reinhardt-fire-strike` |
| C13 | reinhardt-shatter | `reinhardt-shatter` |

`energy-decay/tire-end/hammer-strike/hammer-repair/core-end` 的 prepare 必须加 `--keep-selected`；DVa 后续必须给 `--form-from "$out/DVa-call.json"` 并独立确认实际形态，自毁最后。延时 End/自疗/恢复由 Claude 在真实阶段临近结束时启动另一个短窗口，可选 `.5` 秒基线；工具不自动长轮询。天使 2 尚未获专属 slot 例外、原版友方/尸体等前提缺失时保持 BLOCKED，不能借托比昂例外全局放行。

直接运行两阶段入口（本轮未执行实机路径）；`$ids` 每次冷启动取本次六项真实身份，`$backup` 必须是停止期间生成且早于两进程创建时间的完整档案/具名存档回执：

```powershell
.venv/Scripts/python.exe research/sprint-20261024/capture_blocked_skills.py plan
$ids = @('--pid','PID','--created','CREATED','--mc-pid','MC_PID','--mc-created','MC_CREATED','--world','Overwatch Twilight Switch WORLD','--guest-sha256','JAR_SHA256')
$backup = 'research/dev-cycle/profile-backup.json'
$out = 'research/sprint-20261024/capture-20261026-C12'
.venv/Scripts/python.exe research/sprint-20261024/capture_blocked_skills.py prepare --case reinhardt-fire-strike @ids --profile-backup $backup --output-dir $out
# 满足真实原版前提；需要Q的case须在capture前自然充满/由既有控制器预授能。
.venv/Scripts/python.exe research/sprint-20261024/capture_blocked_skills.py capture --prepared "$out/Reinhardt-fire-strike.prepare.json" --native-scene-ready
```

每组结束先请求已有 `/combat/test/cleanup`，再正常 Stop/保存/恢复；不在莱因哈特后换人。失败/重试用新的输出目录（例如 retry-1），不覆盖旧证据。全部组完成后逐个输出目录运行离线分析，报告名也须全新：

```powershell
.venv/Scripts/python.exe tools/analyze_capture.py research/sprint-20261024/capture-20261026-C12 --output research/sprint-20261024/capture-20261026-C12/candidate-report.json
```

capture 退出0仅代表准备/采证质量门通过；qualityPassed、Begin/End、变量变化和候选排名均不自动认证技能提交。维持 `skillCommitVerified=false/lossless=false/userPlayAccepted=false`。oldgaps 表要求的 Mei 冰壳和 Winston Shift/E/Q 新专项不在当前 13 组清单内，保留为后续采证需求；本轮没有虚增组数或伪造记录。

## 未集成或尚未执行

- 两轮明确可接的共享源码/注册/路由/诊断/测试键已接入；所有已存在模块/Runtime/Events核对后保留单份。原交接的编译失败记录是历史事实，后续全量通过不改写它们。
- 有条件的查莉雅蓝色选包未启用：缺原版阵营条件证据，保留橙红是交接要求。`controlCommitted` 没有已认证生产者，交接明确作为未来接口；未伪造本人控制事件。idle 默认关闭，未改启动参数。
- 素材下载/打包/安装、native重建、guest打包部署及所有实机批均留给 Claude；它们不属于本轮源码集成遗漏。原版未观测的提交、D.Va形态、能量/歌曲语义、完整shader/龙原版clip、逐英雄装弹认证、用户可玩验收继续 OPEN；详见各 handoff，不能由本轮编译升级为通过。

- models 的 Winston projector/barrier 暂不发布：没有已认证部署/消失 runtime。Recall 不借 tracer-blink 画回溯：原 effect 用途尚未认证。死神灵魂、连续绳/链、完整冰壳/折射等仍无认证资源或端点，保持原交接边界。原服务器粒子在未安装并实际验收替代层之前保留为 MC 适配，不能用“粒子消失”冒充替换完成。
