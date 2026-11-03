# 2026-10-26b 集成与用户验收

本轮六份交接的共享项已接入：rockets、menus、builders、voice、hanzo、scope。只改源码/文档、跑离线检查与编译；没有开游戏、修改游戏存档、下载、打包 JAR/DLL 或部署。原有修改和未跟踪文件保留，改前副本在 `research/sprint-20261024/integrator-20261026b-before/`。

## 已落地与冲突处理

- rockets 五处：`simulation.admit(RocketFlightTuning.adapt(batch))`；真实 explode 在地形破坏前调用自击退；Pharah travel 在 requested 后先处理 MC 火箭跳并重建累计基线；Server/Client 注册各一行。原 `lastBatch=batch` 和协议原数值认证保留，重放不叠乘速度；原统一 tick/reset/status 复用，不增回调所有者。堡垒呈现诊断同步改为恢复的银弹与 MC 尺寸/速度适配。
- menus：TwilightBossMenu 改用 F10（0x79），整个 draw 交给 BossMenuPresentation，六条消息转 MenuText；F12 停用此菜单入口。F7 已由对应线程停用建门，F8 统一传送门、F9 召唤、F11 充能+已认证 ability 冷却恢复的既有代码保留。新增 `verifyMenusCooldown` 离线 check 登记，不重复注册菜单或模块。
- builders：`torb-pack-recipient-lab` 加入测试 allowlist 和独立服务器 switch，转 `NativeBuildersLab.action`；原伤害/提交门控、已有轮胎 DEFERRED 状态保留。
- voice：删除旧 `voice-optional` 项，保留 `voice`、`voice-roster`；新增 `voice-front12`，只运行 Genji/McCree/Pharah/Reaper/Soldier76/Tracer/Bastion/Hanzo/Junkrat/Mei/Torbjorn/Widowmaker。已有语音注册不重复添加；新白名单、700ms、概率/保底逻辑由交接源码负责。
- hanzo：无新共享行，核对 `hanzoSkills` 诊断及既有六个相关键继续指向更新后的断言，倍率只在原版认证后施加。
- scope：`native_compositor_version.py` 选择 v43，build_live_passthrough 支持列表加入 43；矩形 capture/restore 的停用由现有 hud_hint_region.hpp 实现。没有构建/加载 v43，仍须下轮冷部署。

以本轮用户要求处理三处覆盖：语音的“只留明确选人/技能大招/击杀台词”覆盖上一轮 reload/status/idle 扩展，旧 starter/optional 下载命令及旧 voice-optional 测试不再执行；Pharah/Bastion 恢复指定历史外观覆盖上一轮的 OriginalMeshPack 模板替换，本轮不重跑整套 models/colors 包；前12英雄是本轮玩法与试玩范围，坦克/辅助既有代码及历史键保留，本轮不新增其玩法或安排其测试。全局语音清单仍按追加要求清退，19人默认选人资格不改成12人资格。

## 编译与本地证据

全量 `compileClientJava --rerun-tasks` 通过：26 秒，compileJava/processResources/compileClientJava 三任务实际执行。使用 HERO-MODULE-GUIDE 的 Gradle 入口、仓内缓存与 Java Temp；未遇 Loom 锁，未删锁文件。日志：`research/sprint-20261024/integration-20261026b/compile.log`。离线策略/接线核对与源码哈希在同目录；这些不是实机、合成像素、光照或声音验收。

集成后 rockets 五个离线 Java 检查通过、私有恢复素材12/12哈希匹配，`integrationPending=[]`。菜单四个边沿/冷却检查、700ms选人及击杀概率/保底夹具通过（固定种子34980/100000），日志 `checks.log`。静态审计确认五处rockets接线、F10/六条消息、89个唯一action、53个唯一测试键、voice-optional退役及v43选择一致；build_live_passthrough 的PowerShell语法通过。没有运行原生DLL构建脚本。

## 需要用户下轮执行的命令

以下命令本轮均未执行。先按当前档案/精确进程身份完成既有正常 Stop、保存与回调/显示恢复；现有旧 DLL 会话必须先正常退出，不热加载第二个 compositor owner。进入仓库后，先生成停止期间的完整档案/存档备份：

```powershell
Set-Location -LiteralPath '<项目根>'
.\.venv\Scripts\python.exe tools/dev_cycle_support.py backup --logs research/integration-20261026b
```

1. 私有语音清单修剪，必须在最终 guest 打包之前运行。工具先保留 `manifest.before-20261026b-voice.json`（不覆盖已有备份），再修剪 manifest，保留 MP3；同时重新生成严格默认表/Java 准入表，不联网。

```powershell
.\.venv\Scripts\python.exe tools/prune_voice_defaults.py --apply-private
```

应保留 762 条默认素材；当前 762 个 MP3 均已有，**无需下载旧 optional/starter 或无字幕 uncertain**。Tracer/Bastion 默认中文选人关闭；其余19人的既有选人入口保留。旧 thnu-three 可作原始索引，不手删 MP3/OGG。冷启动现有准备流程后重新生成所拥有的 sounds.json，测试前等 `assetsReady=true && pendingResourceReload=false`。

2. 本轮没有必须重打的新网格包。恢复的 Pharah 私有 projectile/barrage 资产仍用原目录；体积由源码缩放。只有旧炮台分级包缺失时才执行一次下面命令；已有包齐全则跳过：

```powershell
.venv/Scripts/python.exe tools/prepare_native_builders_assets.py
```

3. 构建 scope 修复的新 v43 compositor。沿用解析后的本机编译器；必须在旧游戏正常退出之后执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_live_passthrough.ps1
```

源码已选择43而新 DLL 尚未生成期间，启动/环境检查不能被当成新版已可用；构建后记录实际 `owmc-live-passthrough-v43.dll` SHA256。不要重建或覆盖仍被旧进程加载的 DLL。

4. 统一打包 guest。选用 voice 交接的 `remapJar` 入口，已包含本轮共享源码；它替代重复运行 rockets 的 build_guest 默认 build 与 menus 的另一遍 build，不须连跑三个打包入口。

```powershell
$env:JAVA_HOME="$PWD\minecraft-1.21.1\runtime\java-runtime-delta\windows-x64\java-runtime-delta"
$env:GRADLE_USER_HOME="$PWD\tools\gradle-cache"
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon remapJar
```

产物为 `guest/build/libs/owmc-guest-0.1.0.jar`。安装、精确 SHA 更新与冷启动沿既有对应档案流程；本轮未执行。若下轮使用 dev_cycle，它会再次统一构建/安装/启动并先备份，不能把它当成只读测试命令。

## 本轮实机验收清单

每批一个新会话，先备份隔离 Switch profile/save；默认飞行关闭，火箭跳使用实际 MC 重力/碰撞。地形破坏会真实改块，测试后按备份/原清理控制恢复。下表的自动键是现有 run_batch 入口；“手动试玩”表示本轮没有对应 run_batch 数值脚本，不能用编译或旧脚本成功冒充验收。

| 英雄/项目 | 对应 run_batch 键 | 实际验收与需保存证据 |
|---|---|---|
| 法老之鹰：左键/E/Q外观与速度 | 手动试玩 | 旧私有左键火箭/星芒尾焰、E青色圆弹/压力球、Q银色小火箭/弯曲尾迹恢复且约放大1.25；适配速度左键26.25、E45、Q33.75格/秒；原弹药/冷却/提交次数不变、近墙不穿透，Q保持原Wave弯曲路径。 |
| 法老之鹰：脚下火箭跳与恢复 | 手动试玩 | 不按Space，实际左键命中脚下后 `rocketSelfImpulse.pushes/impulseY` 增长、真实最高Y上升且HP不因新适配额外降低；背墙/远处/重放不重复kick。`flight.mcRocketJump` 仅弹跳期间出现，落地后走/飞/Shift/E/Q不拉回；换人/菜单/维度/死亡取消旧cue。E原击退保留，Q不新增自身kick。 |
| 堡垒：坦克炮外观/自击退 | 手动试玩 | 银色八边炮弹长.60、半径.10及同步尾迹；实际适配弹速45格/秒。飞行关闭、脚下炮击能实际向上自推；记录HP/弹药/起点/最高Y、pushes/duplicates/blocked，墙后无穿墙kick，重复journal不重复爆炸/击退。 |
| 士兵76：螺旋飞弹自击退 | 手动试玩 | 右键真实已加载命中后沿爆点三维径向自推，脚下可向上；速度不改，不增加自身伤害、不重复原伤害/地形破坏，遮挡/远距/重放拒绝多余kick。 |
| 士兵76：奶棒/小圈/真实光源 | 手动试玩 | 装置1.5倍，小圈半径.65、5格边界和扩散脉冲可见；夜间/室内以真实方块光照确认level14。出场/回场/5秒结束/重投/死亡/换人/维度/正常停止后检查lightActive、原空气恢复、区块票释放与placed/removed；玩家替换该格后cleanup保留玩家块。 |
| 半藏：散射双倍伤害与反弹 | `hanzo,hanzo-full,hanzo-visual,hanzo-scatter-weak,hanzo-scatter-medium,hanzo-scatter-strong` | `damageMultiplier=2`，baseParent/baseChild与实际各×2；fallback75/75→150/150 OW HP。无护甲高血量目标核母箭/子箭/反弹后真实HP，第二次反弹不变×4/×8；左键/音波/Q不改，六子箭/蓝光/插墙/余辉/到期清理继续通过。缺原版同次参数仍BLOCKED。 |
| 狂鼠：左键体积/引信/地形 | `junkrat-base` | 真实M1原版准入后显示2倍，空中/反弹30tick引信、直击仍即爆；地形power1.75与76同位置同材质比较，记录terrainBursts/terrainBlocks。伤害先于挖块、墙后不被新洞追溯伤害、基岩不破；雷/夹/被动炸弹不获得新尺寸/引信/破坏。整套junkrat键含旧轮胎门槛，本轮不靠它宣称轮胎已修好。 |
| 托比昂：永久升级/三级修理/Core | `torb-calibrate`，随后新会话 `torb` | 原版2与锤击提交后实际1→2→3，各级受损先修理，满血三级继续敲不生成四级；核baseLevel与真实HP/显示包。基础二级Core临时三级后回二级，永久三级Core结束保留三级及800OW HP上限。 |
| 托比昂：本人拒拾与友方拾包 | `torb` | 本人刚出手及走到落点均拒拾、包仍在且packsTaken不增；`torb-pack-recipient-lab`指定友方村民/其他合法队友实际拾取后包消失、7.5MC吸收，lastPackRecipient匹配；60秒正常过期，不把armorRemaining=0当友方余量。 |
| 语音：选人/明确技能/大招/静音 | `voice`、`voice-front12` | 前12英雄中Tracer/Bastion的MC补充选人声应静音，原版自身音效仍归原版；其余实际确认第一人称后约700ms且一次。核已有Hanzo/Mei明确技能、尤其冰墙成功一次只播一次、原Q入口无重复。连闪/回溯/跳/受伤/装弹/状态/长待机不出附加人声；全局默认表仍保留其余19人资格，历史voice-roster键保留但本轮不扩测坦克/辅助。 |
| 语音：单杀概率与连杀保底/生命周期 | 手动试玩 | 只用真实MC死亡、当前攻击者/同世界/UUID去重；单杀35%抽样允许不播但须有mcKills与killSpeech抽样证据，不能把未播判成音频通过。8秒相邻间隔内累计3杀后，等3500ms冷却/高优先级语音结束至少一句，实际播出后清零；看events.multikill及killSpeech.guarantees。失焦/死亡/切人/世界/source/model变更取消待播，素材重载不追补旧击杀。 |
| F1 + 黑百合开镜/右上角 | 手动试玩 | 以实际v43哈希与新进程身份，依次普通→F1开关→开镜关镜→开镜中F1→H选人返回；亮天空/深地形、1080p必测，QHD只在显示租约允许时测。右上角地形连续转向、F1面板/镜外暗角无矩形缺口；手/HUD/Boss条正常。原生调试文字重现是保留原HUD的取舍，不再用矩形遮罩盖回。 |
| F8：全部传送门 | 手动试玩 | F7不再建门、F9不再建暮色门；F8按实际安装模组列出地狱/末地/暮色/天堂/AoA等原生入口，主数字/小键盘、1–8选择、9下一页/0上一页、按住/失焦/切人/换世界不重复执行。 |
| F9：批次与全部单体生物 | 手动试玩 | 六种批次与清理看真实计数；8进入单体列表，核服务端注册ID/种数与分页，测试陆地/水生/飞行/大体积生物。碰撞、未加载、边界及非实验/非创造/死亡/多人请求按各自守卫拒绝，失败构造条目不冒称已覆盖。 |
| F10：全部Boss入口与互斥 | 手动试玩 | F10打开原AoA/暮色/天堂/随机Boss页面，F12不再打开；与F8/F9互斥无残帧，真实入口/原生召唤、传送后旧Boss条退场/同UUID重入保留。缺模组条目拒绝，F10不再召随机8怪。 |
| F11：大招和技能恢复 | 手动试玩 | 前12英雄逐个真实消耗Shift/E/多充能技能/Q，再按F11比对原HUD、真实remaining、utilities.refills/cooldownRefills/cooldowns.restored；施法/按住/失焦/非创造拒绝或不重复。大招成功但冷却失败不能整次算通过；多充能是否全部回满、燃料等非timer资源不作完成承诺。 |

自动批仍用每批新会话；例如下轮在 Git Bash 执行（会构建、部署并开游戏，本轮未执行）：

```bash
OWMC_RUN_BATCH_ONLY='junkrat-base' bash tools/dev_cycle.sh research/sprint-20261024/run_batch.py research/sprint-20261024/integration-20261026b-junkrat
```

需要真实声音时保留原MC进程音频关联、0.6秒开头跳过与原阈值。优先/combat、实际HP/弹药/位置/光照和像素统计；确需看图只取JPEG80长边≤768，多帧合一张≤1024接触表。渲染计数、夹具或构建成功均不等于可见融合/用户手感通过。临时LIGHT的崩溃/强杀后持久化恢复未实现；只能报告正常生命周期结果，不能把它升级为崩溃恢复通过。
