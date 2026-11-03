# 2026-10-27 第三轮集成

范围依 `PARALLEL-ROUND-20261026b.md` 第三轮表：前12英雄的既有双进程路线。已处理 voice/menus/oldgaps/rockets/hanzo/scope/builders/widow 八份交接，源码落地点在原条目后标 `[已集成 integrator]`。本轮没有开游戏、下载、修剪私有清单、构建 JAR/DLL 或部署；既有修改和未跟踪文件保留。

## 接线与覆盖关系

- 猎空：WorldFrameExporter 在 locomotion tick、world/pose 计算后、SessionGuard 之前无条件 prime；不放进被初次切换跳过的普通技能分支。Guard 只移除 Pulse 硬 reset，改在 NativeEliminationRuntime.configure 后 revalidate。主动 HTTP cleanup 与服务器停止的硬 reset 保留；新增 pulseBinding/recallSound 导出及两个 run_batch 键。
- rockets：移除上一轮暂停 Pharah 飞行的 useVanillaTravel 分支；持续采样 native 位移，在实际 move 前叠加 pharahMotion，碰撞后通知 pharahBlocked；vanilla 水平残余在原 movement 适配之后加入。保留原 voice/其他英雄 travel 分支、已登记的共用 server/client 模块及真实爆炸入口；新增堡垒 glowFrames/error 导出。
- builders：现有 `concussiveMine` 调用已携带原投掷 nativePid/nativeTick、完整 Scope、实际 b.pos 和 radius3；核对它复用 rockets apply/去重，没有叠加旧本人 addVelocity 或额外×1.5。共享 movement 接好后才能保住水平残余；无需第二个模块或攻击入口。
- Widow：GuestMod 紧接 CombatParticles.register 注册实体/默认属性，位于 frameExport 条件外、注册表冻结前。原 VenomMineRenderer 已登记 WidowSpiderRenderer，未重复登记。NativeSkillReader 仅给 Widow 大招时长校验增加 `!melee`，不放宽其余身份/几何/节点/伤害守卫。
- menus：核对已有 F9 tick/draw/状态出口，新随机候选直接走已有服务端单体分支；无新 HTTP/包/模块。登记 verifyRandomSummonPolicy check。
- voice、Hanzo：无新增共享运行时注册，保留现有诊断与测试路由。500ms 取代700ms；击杀/多杀共用跨英雄生命周期的10秒硬冷却取代上一轮3500ms。散射总倍率由×2改为原版基础×4，fallback300/300；不把旧×2数据当新验收。
- scope：选择 v44 并扩展构建支持列表。新 debug_banner_fill.hpp 已由现有 HUD helper 引用，不新增链接源或 callback owner。它覆盖上一轮“完全停用遮字”的策略：只从当前 post-HUD 邻近像素回填精确小框，不能恢复 pre-HUD 大矩形遮盖。

**语音内容仍有未确认项：** 当前固定候选为 `041b1e23a19cb344ff2dba19428da7ec`，代码不会随机回退，但目录中文注释不能证明录音就是日语 `竜が我が敵を喰らう`。本轮没有听辨确认，也没有擅改为另一 hash。固定策略、语言确认、实际原版Q触发和物理音频分别验收。

## 本轮离线结果与证据

全量 `compileClientJava --rerun-tasks` 通过：27秒，compileJava/processResources/compileClientJava 三任务实际执行；使用 HERO-MODULE-GUIDE 的 Gradle 入口、离线缓存及工作区 Temp，未遇 Loom 锁、未删锁文件。日志、检查结果、源码哈希及本轮独立 diff 位于 `research/sprint-20261027/integration/`；改前副本位于 `research/sprint-20261027/integrator-before/`。离线通过不升级为游戏/像素/声音验收。

集成后的 rockets 六组 Java main、两份共享候选源码类型检查及3个 glow 素材哈希通过，共享两处被核对为已集成；Widow 修正后的真实 reader 内存夹具通过（包括首样本/重放/篡改），不再依赖 research 候选替换；Tracer 20+10门控断言、7个生产源类型检查和前12语音761条清单核对通过。静态审计确认 prime/guard/configure 顺序、保留主动cleanup/stop硬清理、实体注册时机、单次共用矿雷调用、55个唯一测试键及v44版本一致。PowerShell构建脚本语法通过，未构建DLL。

另通过随机怪物策略62项、500ms选人及击杀10秒/固定hash策略夹具；builders 三组共18项检查通过。它们只验证离线策略/编译字节码，不证明首次实机Q、蜘蛛AI、实际飞行或日语内容。

## 用户下轮执行的命令

先按当前实际档案与已核实进程身份，完成既有正常 Stop、保存、回调/显示恢复。旧 v43 owner 必须先正常退出，不能给它再加载一个 v44。随后在仓库执行停止状态的 profile/save 备份：

```powershell
Set-Location -LiteralPath '<项目根>'
.\.venv\Scripts\python.exe tools/dev_cycle_support.py backup --logs research/integration-20261027
```

1. 先听辨本地固定候选。这条命令只交给用户在下一轮打开已有音频；本轮未播放：

```powershell
$hanzoUlt = Join-Path $env:USERPROFILE '.universal-modder/assets/ow1-zhcn-2016/thnu-full/hanzo/041b1e23a19cb344ff2dba19428da7ec.mp3'
Start-Process -FilePath $hanzoUlt
```

若确认是目标日语，按下一条同步私有白名单；默认数目应为761，无需下载。若不是，先定位已听辨 hash，连同 HeroVoicePolicy.HANZO_ULT_HASH、prune_voice_defaults.py 的同名常量及生成输入一起更新，再生成/编译；不能只改私有 manifest。日语确认未完成时，其余功能可独立验收，但不能把这一项记为通过。

```powershell
.\.venv\Scripts\python.exe tools/prune_voice_defaults.py --apply-private
```

工具保留 MP3，仍使用已有 `manifest.before-20261026b-voice.json` 备份名且不覆盖旧备份；当前白名单过滤掉另一半藏 ult_cast。它会再生成默认表与 Java 准入表，所以应在最终打包之前运行。旧 optional/starter/无字幕 uncertain 均不恢复。

2. 重建 compositor v44。先离线 GPU 检查，再构建 DLL；本轮两条均未执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/verify/verify_scope_hud.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_live_passthrough.ps1
```

产物为 `native-host/build/owmc-live-passthrough-v44.dll`，记录实际 SHA256。源码已选44而文件未构建时，不把启动/环境就绪当成新版已经可用。构建沿现有 resolve_native_compiler.ps1，不引入旧 E: 路径。

3. 统一打包 guest。此 remapJar 入口合并交接中的重复 build_guest/build 命令，包含实体、客户端与共享源码；本轮未执行：

```powershell
$env:JAVA_HOME="$PWD\minecraft-1.21.1\runtime\java-runtime-delta\windows-x64\java-runtime-delta"
$env:GRADLE_USER_HOME="$PWD\tools\gradle-cache"
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon remapJar
```

产物 `guest/build/libs/owmc-guest-0.1.0.jar`。本轮没有新提取/网格打包/下载命令：堡垒 glow 读既有 Pharah 私有 flare/glow/flame，蜘蛛复用原版 CaveSpider 模型/材质。不重新安装前轮整批 models/colors 包。安装、精确 SHA 更新和冷启动沿既有对应档案流程。

## 实机验收：自动键与手动试玩分开

每批一个新会话；**T01 必须在该进程第一次选择猎空/第一次Q时先跑，早于任何 voice-front12 或其他含猎空Q的测试**。不得靠重复切人把首发修好。自动脚本仍用当次六项精确身份与隔离 Switch profile，冷启动前备份存档；地形破坏会真实改块。

| 批次/范围 | 自动 run_batch 键或手动 | 实际通过条件 |
|---|---|---|
| T01 猎空首次Q/Recall数值 | `tracer-first-pulse,tracer-recall-start-sound` | 首次单次Genji→Tracer后只按一次Q，primes>0且model正确、launches/explosions各恰+1、真实接触/fuse及目标HP下降，空闲无重播；E先有≥10历史样本，recallSound.starts恰+1、submitDelayMs≤50，playWall早于completionWall，End/回执重试不再提交。 |
| T02 猎空生命周期/听感 | 手动试玩 | 同会话再次Genji→Tracer首发仍正常；已投弹后短暂失焦/输入确认切换不取消，同scope reader重绑不重播；真正换人/世界/来源取消旧弹，未知身份最多暂停150ms无计时/伤害。Recall Begin当前客户端tick提交后由用户听感确认同步，数值不等于耳机输出延迟。 |
| R01 法老地面/空中火箭跳 | 手动试玩 | 脚下/身侧真实爆炸，无Space也离地；Shift上升、悬浮、下降时半径内真实地面/墙面命中都能加力，native sequence持续更新，随后立即继续Shift/悬浮，不等落地、不瞬移。碰顶只清Y；空中连发/E/Q组合、motion暂缺恢复、换人/失焦/世界/死亡无残余继承。 |
| R02 堡垒光效与炮跳/76火箭跳 | 手动试玩 | 夜间/室内、远近上下和连续多弹见银弹+亮核/星芒/交叉尾焰，tankShellGlowFrames增长且error为空；近墙不穿透、不丢多弹顶点。三种已认证弹药的boost=1.5、maxImpulse=1.65，最高Y/水平距离比前轮增加；重复令牌、远处/遮挡/未加载不kick，不重复伤害。76速度仍不改。 |
| B01 狂鼠基础回归 | `junkrat-base` | 记录first-ground-contact、fuse30tick、ground/fuse计数、direct80/blast160、terrain3.5及真实破坏增量；不是只读到参数就通过。 |
| B02 狂鼠触地引信/威力/站地矿跳 | 手动试玩 | 空中超过发射30tick不自爆；墙/顶面不启动引信，首次向上地面碰撞后30tick引爆，多次反弹不续期，晚落地也给足30tick，直击立即爆。高HP目标核8/16MC满额与遮挡，damage先于terrain。站地脚边投雷再右键，不先跳，mineImpulses与minePushes各+1、正Y与实际离地；空中/隔墙/远处/重复右键/换scope分别检查，不叠旧自击退。 |
| H01 半藏散射×4 | `hanzo,hanzo-full,hanzo-visual,hanzo-scatter-weak,hanzo-scatter-medium,hanzo-scatter-strong` | actualParent/Child=base×4，原参数母100–500/子60–300 OW HP，fallback300/300；高HP无护甲目标核真实HP。反弹不变×8/×16，仍六子箭、原弹道/蓝光/插墙/到期清理，左键/音波/龙不改；缺同次原版参数仍BLOCKED。 |
| W01 Widow E概率/实体/AI/清理 | 手动试玩 | 每次认证E只抽一次，throws增量=mineRolls+spiderRolls；短样本不强求恰一半。原诡雷旧流程保留；蜘蛛飞行可见，触地才spawn，墙顶先落地，spiderSpawnFailures不增。出生HP12、scale≈.3、宽≈.21/高≈.15、逐字彩虹Spider Man；每20tick约扣1.2、200tick强制死亡，治疗不延寿。 |
| W02 Widow蜘蛛攻击/近战 | 手动试玩 | F9放混合动物/村民/敌怪/蜘蛛，核target、实际HP/中毒及spiderHits/damageApplied；不伤发射者，换人/死亡/世界/cleanup无残留。现有venom-target可测E，melee/wall/open测V：墙后不伤、去墙后accepted/hits/damageApplied与HP一致，静置不重播；回归Widow Q时长验证。离线Winston读取回归不扩成本轮坦克试玩。 |
| M01 F9随机怪物 | 手动试玩 | 首页1新随机、2旧8怪、8单体、第2页1清理；主数字/小键盘一次只生成一只。看selection=random:monster、resolvedEntity、randomCandidates/randomSpawned，原版/模组同规则；黑名单及宽深>3/高>4/体积>18不经随机生成，小中型Boss允许，初始化变大也拒绝。池空/密闭/无安全落点/边界/未加载/失焦/施法/非创造/死亡拒绝，不偷换成旧8种池或改地形。 |
| V01 选人/技能/固定hash数值 | `voice,voice-front12` | 前12按当前白名单回归，Tracer/Bastion补充选人仍静音，其余确认后约500ms一次；500ms是门控延迟，另有tick/资源调度。Hanzo实际Q的recentHash固定041b1e23…，旧另hash不加载，无随机回退；数值只证固定项，日语须独立听辨。 |
| V02 10秒硬冷却/日语原声 | 手动试玩 | 观察一次实际kill/multikill人声开始，之后10秒内连续真实击杀/切人/死亡/失焦/世界切换均不能绕过；events.kill+multikill不增、cooldownSuppressed增加、不抽样不累计、不在到期补播。冷却外仍35%及8秒相邻3杀保底，高优先级结束后取得声道才开始10秒。连续真实Hanzo Q均同hash，并实际听出指定日语。 |
| S01 DEV遮字/F1/开镜 | 手动试玩 | 实际v44新进程，普通→F1开关→Widow开关镜→开镜中F1→H返回；DEV字形/描边无残留，右上角无亮矩形/空白，转向回填随当前画面。优先1080p，QHD仅租约允许；亮天空/暗地形/F1底色均测，原手/HUD/MC Boss条正常。小框邻近插值可能略软，不当作恢复被字覆盖的真实细节。 |

自动首批下一轮可在 Git Bash 执行（此命令会构建/部署/开游戏，本轮未执行）：

```bash
OWMC_RUN_BATCH_ONLY='tracer-first-pulse,tracer-recall-start-sound' bash tools/dev_cycle.sh research/sprint-20261024/run_batch.py research/sprint-20261027/tracer-first-live
```

不要无筛选跑全部历史键；不安排坦克/辅助扩展测试。声音沿原MC进程音频判据及0.6秒开头跳过规则；数值提交与物理输出分开。优先/combat、HP/弹药/位置/像素统计，确需图片只看长边≤768的JPEG80或多帧≤1024接触表。所有实机、可见融合、AI/音频听感和用户试玩接受均未由本轮离线结果代替。

r27-H01补充集成：已落地 `hanzo-combat-lab` 场景路由、`hanzoCombatLab` 诊断及仅外部HTTP cleanup的前置回收（不放入NativeCombatScene.cleanup本体）；全量 `compileClientJava --rerun-tasks` 通过（37秒，3任务实际执行），未开游戏或部署。

menus/voice最新补充集成：已接F9生命周期全局注册及common spawn Mixin（随机×8、排除BOSS血条、统一名称/3600tick期限，覆盖旧一次一只/小Boss可入池规格）；voice最新无新增共享项，041已退役，部署前须执行 `tools/prune_voice_defaults.py --apply-private` 安装P10派生片段ea38…并按新技能10秒冷却验收；全量 `compileClientJava --rerun-tasks` 通过（26秒，3任务实际执行），未开游戏或部署。

voice第四次补充集成：已登记MC起落声音过滤两项client Mixin并删除旧jump通知；半藏大招提前沿既有自动prepare消费b9:79 EntryGameMessage新tick，76仅作对照、不再由dragonCasts晚触发；全量 `compileClientJava --rerun-tasks` 通过（35秒，3任务实际执行），761条清单不变、无需重复apply-private；原版进程起落语气声仍待定位，未开游戏或部署。

## Claude 直接修改（2026-10-27 用户第五次反馈）
- 半藏大招（MC 适配：用户要求）：`NativeHanzoSkillRuntime` 射程 60→120 m；龙体半径 4 m 内非玩家生物先以半藏为攻击者打满再 kill（保留击杀归属）；沿途半径 4 m 球内可破坏方块清除（不掉落，跳过 hardness<0 与未加载区块）。诊断新增 `dragonDevour/dragonKills/dragonBlocksCleared`。已构建安装（jar 79904860…），待用户试玩确认。
- 启动器重做：`tools/project_launcher.py` 新 Canvas UI（守望风格斜切按钮、状态卡、热键条），后端新增 `toggle`/`reboot` 动作（在 action 互斥锁内判定运行状态；停止走 crash-stop 路径，启动前自动正常关闭残留进程）。46 项启动器测试通过；真机连续 toggle：停 10s → 启（选人）→ 停 10s → 启（选人）全部成功。旧版备份 research/_archive/2026-10/launcher-before-redesign-20261027.py。


## 第五次反馈补集成（2026-10-27，当前执行入口）

四份最新追加段均已处理并标记：Hanzo 七文件双端补丁、`/combat.hanzoControls`、原版 HNZ1 能力/请求/相机选择/撤销/诊断，以及 Widow 毒雷与声波箭/Widow Q 轮廓 OR 合并已落地。voice/builders 无新增共享 Java 注册，已核对原出口。新增 `hanzo-q-controls`、`voice-ult-ready`，原测试键和失败/BLOCKED 退出码逻辑保留。Hanzo 的 range120、devour/击杀/清块及龙绘制保持当前版本；不从 Q 键生成施放、不放宽其他英雄 cinematic/menu 或 Deadeye 锁。

合并说明：交接 native 诊断行需包在 `OWMC_LIVE_BLEND` 内，否则普通 pose-only 编译会引用不存在的 live 对象；已注释保留原行意图。选择 **v45** 冷启动身份，保留 v44 的 DEV 小框修复，避免覆盖旧 DLL 身份。没有新增 hook/callback owner。全量 `compileClientJava --offline --rerun-tasks` 通过（37 秒，3 任务实际执行）；live C++17 `-Wall -Wextra -Werror -fsyntax-only` 和 HNZ1 假内存夹具通过，无 DLL 输出。普通 pose-only 语法亦通过，检查时仅将原有 `nextLightSample` 未使用警告降为 warning，未改其 worker 源码。未遇 Loom 锁、未删锁文件。证据及改前副本：`research/sprint-20261027/integration/feedback5/`。

### 用户要执行的命令（按顺序，仅供后续执行）

本节覆盖前文 v44 构建与 761 条白名单同步步骤。先完成既有正常停止、保存和恢复流程，旧 callback owner 必须退出；以下命令本轮均未执行。语音源码已为 **785 条**，当前交接记录私有 manifest 仍为 761；先复用 22 个 MP3、仅下载缺失 2 个，再统一打包。当前 P10 日语派生片段不变，**不再执行 `--apply-private` 裁 P10**。无需重打模型包。

```powershell
Set-Location -LiteralPath '<项目根>'
.\.venv\Scripts\python.exe tools/dev_cycle_support.py backup --logs research/integration-20261027-feedback5
.\.venv\Scripts\python.exe tools/voice_download.py --list research/voice-20261027-feedback5/download-additions.json
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_live_passthrough.ps1
$env:JAVA_HOME=Join-Path (Get-Location) 'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta'
$env:GRADLE_USER_HOME=Join-Path (Get-Location) 'tools/gradle-cache'
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon remapJar
Get-FileHash -Algorithm SHA256 native-host/build/owmc-live-passthrough-v45.dll,guest/build/libs/owmc-guest-0.1.0.jar
```

每条命令成功后再执行下一条，任何非零退出即停止；下载失败不进入打包。私有同步后需确认 manifest=785、运行时 `assetsReady=true`。DLL 使用脚本内的 `resolve_native_compiler.ps1`；产物是 v45 DLL 与新 Guest JAR，两端都须按既有流程冷部署/更新精确 SHA，单装 JAR 时 `hanzoControls.nativeCapability=false` 不放开控制。正常重启启动器以自动发现 Lucio/Hanzo voice helper；仅复用旧启动器且已核实 Lucio 当前原版 PID 时才补执行 `.\.venv\Scripts\python.exe tools/prepare_hero_lucio_voice.py --pid $verifiedNativePid`。

### 待重跑键与手动试玩（功能先于采证）

以下每行独立新会话，按表顺序执行；每批使用当次精确进程身份/world/JAR SHA。保留前文猎空首次 Q 必须早于任何含猎空 Q 的语音批次的要求；已有采证 13 组继续放在全部功能回归之后。不要无筛选运行全部历史键。

| 顺序/范围 | run_batch 键 | 必须重验 |
|---|---|---|
| F5-H1 半藏双端控制 | `hanzo-q-controls` | 真实 b9:76 只新增一次施放；Q 输入到释放、龙绘制早期及约四秒后均有实际位移≥0.4m、原版 yaw≥2° 且 MC 跟随、龙仍在飞；同时记录 cameraSelections/Refusals/Reason。只有 HNZ1 ready 不算通过。 |
| F5-H2 半藏战斗回归 | `hanzo-full` | 原版 Q 手部/发龙、range120、devour/击杀/清块、散射和安全战斗场景；切菜单/失焦/死亡/换人换世界撤销，Q 结束不跳回旧相机；Reaper/Deadeye 另手动回归。 |
| F5-B 炮台 | `torb` | 基础 1→2 后继续锤不升3，Core 临时3/火箭，End 回2且HP≤300；Core内升级后也回2；重复周期、本人拒拾与其他对象拾取。原锤击提交缺证据仍记 BLOCKED。 |
| F5-V1 语音回归 | `voice` | 半藏 b9:79、唯一 P10 日语、技能/Q 10秒冷却、击杀规则、普通技能忙时不抢占，Q/就绪可抢占。 |
| F5-V2 前12英雄 | `voice-front12` | 堡垒 Q 必须实际Tank105 Begin并播放，选人仍静音；其他原版起手、素材与技能录音依脚本验收。 |
| F5-V3 明确要求的21人就绪 | `voice-ult-ready` | `--mode roster --heroes all --select-only --ult-ready --roster-audio`；Reinhardt 在末尾，之后不换人。初读满值标未覆盖，实际消费后再补未满→满；持续满只播一次，下一充满周期可再播。此批仅语音，不新增坦克/辅助玩法。 |
| F5-W 黑百合毒雷 | 手动试玩 | 原版 E 真实触雷即轮廓、100tick五次毒伤后撤销；自然到期/cleanup/失效只撤本模块贡献。原有/毒效期间新增的其他 Glowing、声波箭/Widow Q 继续各自时长，颜色不变；蜘蛛分支与V伤害回归。 |

单批调用示例（每次 `dev_cycle` 以既有流程创建新会话；替换键和唯一输出路径）：

```powershell
$env:OWMC_RUN_BATCH_ONLY='hanzo-q-controls'
bash tools/dev_cycle.sh research/sprint-20261024/run_batch.py research/sprint-20261027/feedback5-hanzo-controls-live
Remove-Item Env:OWMC_RUN_BATCH_ONLY
```

未集成共享项：无。仍待实机：半藏实际 Q 相机类型/生命周期与上述全部可玩/像素/音频验收；语音四位英雄仍缺认证施放 Begin，查莉娅瞬时/秩序之光放置提交的证据边界沿最新 voice 表；原版进程起落语气声尚未定位（MC 侧过滤已在前次集成）。本轮未开游戏、联网下载、写私有语音、打包 JAR/DLL 或部署。
- 启动器第二版（用户第六次反馈）：设置并入启动器窗口（不再单独进程/互斥等待），保存仍走 configure_passthrough CLI + 设置哈希校验；打开时短暂置顶避免被全屏游戏遮挡。toggle/reboot 改为自愈：启动等到选人界面（≤240s），失败则正常清理后重试一次；关闭异常退出且仍有进程时最多正常关闭 3 次；只有残留进程无监督时按钮显示「重新启动」。根因记录：用户 20:19 的关闭被 0xC000013A 中断（与 20:18 启动失败后的监督器清理重叠），20:18 启动失败为原版 weapon gate 未保持激活（偶发）。58 项测试通过；真机：.cmd 连续打开 3 次均 0.6s 前台出现、重复点击不多开；UI 同路径 detached toggle 启动 47s 到选人、关闭 10s 无残留。


## 第六次反馈补集成（2026-10-27，覆盖第五次控制/语音结论）

半藏改为用户当前要求的 **Q Begin 起锁移动与视角，施法 End 且同次龙 released 后解锁**，不再沿用 HNZ1 的施法中自由移动/正常相机选择。已落地交接四文件精确补丁：NativeLocomotionController 锁期归零/取消移动并移除旧速度恢复；登记 HanzoQTravelMixin（含垂直惯性、creative travel）；HostCameraMixin 接 cameraRotation；pose_observer.cpp 改 HNZ2 请求/同次施法身份/150ms时效、同一个输入过滤 owner、失焦撤销、stop清理和诊断，删除 continueHanzoControls/HanzoGameplayCamera 全部原版相机指针选择。既有 HostPoseReader/WorldFrameMapping/hanzoControls/Motor/Input 接线继续复用。取消且未发箭的施法在真实 End 撤锁；菜单/失焦/死亡/换scope/cleanup按原门控撤销，不重入旧Begin。龙 range120/devour 与现有 renderer 保留。交接最新段部分中文原文已损坏为问号，采用用户明确需求及可读精确补丁，集成补记已写清覆盖关系。

语音最新代码沿既有调用链生效：堡垒改 `012f:123` 变形动画 Begin，105仅作晚到形态见证；死神优先 `0044:9`，允许同owner/source/model/world、≤150ms的已认证runtime Begin回执，统一10秒去重且保护已认证电影期声道。固定中文“正在肃清敌人”，Early仍唯一播放所有者；`/combat.heroVoice.reaperBegin` 保留成功/失败遥测。无需新增共享Java/Mixin，已原样登记 **`voice-reaper`**。`tools/project_launcher.py` 的 SHA256 前后相同，新 UI 与 toggle/reboot 完整保留。

全量 `compileClientJava --offline --rerun-tasks` **通过（27秒，3任务实际执行）**；实际编译的 HanzoQTravelMixin 有client refmap映射，Java双条件/取消/失效/重建基线/时序/协议夹具通过；live C++17严格语法及HNZ2 native夹具通过，无DLL输出。普通pose-only语法通过，仅沿用前轮对既有unused变量warning的离线处理，未改worker。未遇Loom锁、未删锁。只读环境检查唯一未通过项是尚未构建的 `owmc-live-passthrough-v46.dll`，按本轮边界留给用户构建。证据/改前备份：`research/sprint-20261027/integration/feedback6/`。

### 用户后续执行（v46 DLL + Guest JAR，按顺序）

先沿既有正常停机、保存、恢复与备份流程完成冷构建准备；旧callback owner退出后再部署，不能热加载第二个owner。本轮选择 **v46 / HNZ2**，覆盖前文v45构建要求；旧HNZ1 DLL不能满足新Guest能力校验。以下命令本轮均未执行，每条成功后才执行下一条，非零退出立即停下：

```powershell
Set-Location -LiteralPath '<项目根>'
.\.venv\Scripts\python.exe tools/dev_cycle_support.py backup --logs research/integration-20261027-feedback6
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_live_passthrough.ps1
$env:JAVA_HOME=Join-Path (Get-Location) 'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta'
$env:GRADLE_USER_HOME=Join-Path (Get-Location) 'tools/gradle-cache'
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon remapJar
Get-FileHash -Algorithm SHA256 native-host/build/owmc-live-passthrough-v46.dll,guest/build/libs/owmc-guest-0.1.0.jar
```

DLL构建继续使用脚本中的 `resolve_native_compiler.ps1`。双端产物按既有冷部署和精确SHA流程安装；**本轮没有下载、apply-private、英文槽安装或其他声音同步命令**：最新voice交接确认私有manifest与源码均785条，现有死神中文OGG保留，覆盖前文第五次尚待785同步的历史状态。正常重启启动器即可由既有HERO+prepare自动发现新Bastion helper，无需修改启动器。若必须复用旧启动器进程，仅在核实当前英雄Bastion及当前PID后执行：

```powershell
.\.venv\Scripts\python.exe tools/prepare_hero_bastion_voice.py --pid $verifiedNativePid
```

仅当 `reaperBegin.clipReady=false` 且确认当前profile确为 `guest-passthrough-client` 时，在正常停机后补准备已有本地资源（无网络，不安装英文候选）：

```powershell
.\.venv\Scripts\python.exe -c "import sys; from pathlib import Path; sys.path.insert(0,'tools'); from four_dps_voice_assets import prepare; assert prepare(Path('guest-passthrough-client'))"
```

### 待重跑（每行新会话，功能回归后再采证）

| 顺序 | run_batch 键 | 本轮验收 |
|---|---|---|
| 1 | `hanzo-q-controls` | 真实Begin到End/released双条件满足前移动、视角均锁；取nativeCastMillis/lockMillis和HNZ2 motion-filter帧；解锁后立即正常移动/转向，龙仍真实released/绘制；不得继续用前轮“施法期位移≥0.4m/转向≥2°”当通过条件。 |
| 2 | `hanzo-full,hanzo` | 保留120m/吞噬伤害/清块/龙体绘制及散射回归；手动补Q锁期F6/creative/跳跃/惯性、End解锁、菜单/失焦/死亡/换人/世界/cleanup撤销、无同次重入，Reaper/Deadeye无回归。 |
| 3 | `voice-reaper` | 实际原版Q+固定中文hash+MC进程录音；保存before/after reaperBegin，9动画或同scope新鲜runtime回执准入，同次双源只播一次，电影期不被声道清理切断。 |
| 4 | `voice-front12` | 堡垒必须 `native:bastion-012f:123-transform-begin`，105/第一弹不得补播；其余语音及最高优先级/10秒技能冷却回归。猎空首次Q专项仍应早于这批。 |

新键运行示例（先更新双端并完成冷部署，使用当次精确身份；dev_cycle为每批建新会话）：

```powershell
$env:OWMC_RUN_BATCH_ONLY='voice-reaper'
bash tools/dev_cycle.sh research/sprint-20261024/run_batch.py research/sprint-20261027/feedback6-voice-reaper-live
Remove-Item Env:OWMC_RUN_BATCH_ONLY
```

未集成共享项：无。锁定时长、实际原版施法/解锁、堡垒提前与死神可听且不中断仍待实机，不以归档推算/夹具/编译代替。本轮未开游戏、打包JAR/DLL或部署，未改私有声音。
- Claude 直接修改（第七次反馈，2026-10-27）：半藏 Q 改为“原版 Begin 即锁定，同次龙释放即解锁”（原版 volley 与 Begin 同帧，不能作为射出时刻）；锁定加 500ms 抖动宽限、4s 上限；实机 f10：锁定 548ms，位移/转向 0，判定通过。F7 新增世界设置菜单（WorldSettingsMenu/WorldSettingsRuntime；NativeWorldSettings 增加玩家控制模式与永远白天锁定；永久夜视每秒补回）。F9 删除测试目标，新增全花色猫（其一命名老吴）与随机原版动物×8；召唤生物保留自定义名。安装 laowu_meme-2.0.0+1.21.0-1.21.1+fabric.jar（GitHub Rogic460，MIT，sha256 b17e63cf…）。死神大招语音禁用。启动器主页新增光影开关（Iris + MakeUp-UltraFast，开=低档）。自动备份只保留最近 8 份（清理前 48 份旧备份释放约 78G）。
