# Replacement PC takeover — 2026-10-16

## 2026-11-04 — T5代码构建交付，用户手测待进行

仅代码/构建，未启动OW/MC、改分辨率、录制或操作键鼠；不提交、不重建dist。开发候选48/29/11/16/10/1，JAR SHA256 `de0662031b984ff39b7f9e7586188149b1b28260c3ff330078498ebf89e8f32a`，body29 `19bb2d7dd1c2bdd80845a5ad8652cd83bcbbfb3e8e8ee7aa472ff75aff297f00`。现有00:57 JAR与00:58 DLL已核对晚于最终源码，交付日志成功；完整71任务、最后源码刷新8任务、原生17夹具通过。HTTP首轮2秒响应超时，未改bridge，收尾限时独立复跑通过1测试。

实现：MC原版小白头+蓝紫特效灵魂球；Mei E预览/LMB边沿确认/E或RMB取消；真实原生10秒冰墙与8秒炮台冷却及回执；9列共享几何、五原版柱+连续冰芯和1/16地形碰撞；黑百合Shift/跳跃中途取消动量超级跳，MC重力/碰撞及原生12秒冷却保留。均待用户实际画面、HUD和手感验收，不能据夹具声称实机通过。

7506个人档案SHA零差异，原配置及无关源码保持；T5中文已用UTF-8重写并确认无连续三个问号。报告、手测清单、29项改动及SHA见 `research/fix/T-report.md` 的T5节；证据 `research/fix/T5-lab/evidence/closeout.json`，完成标记 `research/fix/T5-DONE.txt`。T3枪口精确像素等旧的未验收项继续保留。


## 2026-11-03 — T4 掉落物/吸附代码与构建交付，待用户手测

本轮继续遵守用户的**只改代码、只构建，不启动 OW/MC、不改分辨率、不录视频、不操作键鼠**。没有实机验收、提交或 dist 重建；最终只读游戏与监督器为 0，配置/设置按原字节保持。

开发候选为 **48/28/11/16/10/1**；新 JAR SHA256 `72353555dc5b26d3f04028f1725d9eb10fb3e67e6e3b89aef1f4624078abbe55`，body28 SHA256 `fb6564a73166e8d9dc4d889861ff0b417b8f80454f2bc067f03d730cd744bec0`。Java 离线 build70任务、body28原生16夹具、正确HTTP入口及环境检查通过；它们不等于原生钱包/HUD/模型的实际游玩通过。

实现了实际致死伤害归属的 Reaper 灵魂球与 Torb Scrap，补英雄 NPC/其他 LivingEntity，移除“附近 Monster 任意死就掉自己废料”的旧路径。三类物品（含护甲包）共用落地10秒一圈、0–0.05m浮动、3m吸附、LOS/方块/区块/边界检查、最终接触消费；灵魂球50OW→5MC回血，废料25/200，原生E耗50不二次扣镜像。作用域/死亡/停止清理，不生成持久物品实体。

废料通过已有 body 逻辑线程上的原生 Set&Notify 写 entity变量0409；80-byte序列请求/回执、身份/新鲜度/类型/代码守卫、读回确认、重复/失败不重复入账，成功后才移除碎片。只镜像真实原生钱包，不做MC-only充值。实际新变量通知/HUD及T3第三次E仍待手测。

**专用原版灵魂球/Scrap资产尚未认证**，已明确使用自制蓝色骷髅球/齿轮替代；两个包的 provenance 标记 authored-fallback，资源放在现有 D 盘根 `research/fix/T3-lab/mesh-assets/{reaper-soul,torb-scrap}`，未进源码/JAR。原版护甲包继续沿用。

本轮25项源/构建/测试文件，7505个人档案SHA零差异，1560源码快照无无关变化；T4开始前用户已有的28项变化和2新增已保留并增量备份。完整根因/实现、SHA、资源来源和手测表见 [T-report.md](../research/fix/T-report.md) 的 T4 交付节；机器证据 `research/fix/T4-lab/evidence/closeout.json`，6个资产输入见 `research/fix/T4-rebuild-files.txt`。完成标记 `research/fix/T4-DONE.txt` 仅指代码构建交付。T3精确枪口像素等未验收项仍保留。


## 2026-11-03 — T3 代码与构建交付，实机暂停待用户验收

**以用户最新指示为准：只改代码、只构建，不启动 OW/MC、不改分辨率、不录视频、不操作鼠标键盘。** 本轮没有在此指示后恢复实机。旧会话已正常停止，无强杀；最终游戏/监督器/录制辅助进程为 0，桌面只读核对为 2560×1440@200Hz/32bpp。

开发候选：guest JAR SHA256 `3f61554deacf9c3f95490d450a6c15b26c85e9f77d2b588f41a5bb119a9cef71`，六个 native owner **48/27/11/16/10/1**；v48 SHA256 `4d2178628f61a15353eaddaf542a8e7447d860cfb939c0e1525fa9176b8d1640`。原有另外五个 DLL 不变。Java 离线 build 69 tasks、正确 HTTP 契约入口、只读环境检查均通过，原生构建/分组手模 GPU 夹具通过；**没有最终构建实机通过结论**。

已实现炮台枪管中点、统一视觉枪口层、护甲包落地旋转/30 秒生物 2 倍尺寸、Shift 预览/LMB 确认/取消、多组原生换弹手模合并；追加 Torb 大弹体/视觉慢速/火光、实际相机与坦克首帧延迟修正，以及放大毒雷/暴雪/脉冲和蓝色爆炸波。

**枪口像素残差尚未实测，JSON 仍 verified=false；连续第三次 E 的原生 throw 条件尚未定位。** 最终 12 英雄、村民/NPC/自然恢复、新特效都等用户手测；不能把早期 kit/placement 或 T2 视频当作最终候选验收。

个人档案 7503 项 SHA 零差异，原有源码 1626 项无无关变化。原设置已按字节恢复，launcher 仅保留 `paths.meshAssets=research/fix/T3-lab/mesh-assets`；私有资产不进源码/JAR。没有提交、没有重建 dist，dist 仍是旧包。`T3_live.py` 入口已禁用，全局手模 trace 已归档。

完整九项根因/实现、12 英雄检查表、手测清单、产物 SHA、36 个资产重建输入见 [T-report.md](../research/fix/T-report.md) 的 T3 最终交付节；机器证据为 `research/fix/T3-lab/evidence/closeout.json`，源文件 SHA/diff 在同目录。`research/fix/T-DONE.txt` 标记的是本轮代码构建交付完成，实机验收仍待进行。


## 2026-11-03 — T2 托比昂弹丸、红线、护甲包已实机完成

开发guest JAR SHA256 `b60368b13b8a3b9da0c3f2e22c19cef3934232eee63a58a2ef8ca7a5cda2f9cb`；native仍47/27/11/16/10/1。
原版0157→D0D铆钉体积模型已按真实MC扫掠呈现；02d0原版为瞬时霰弹，使用45%原网格作100ms体积残像，保留hitscan伤害语义。
一级/二级/Core炮台的真实炮口→锁定目标红线、切换/丢失清线，原版02a1护甲包落地/本人拒绝/他人拾取/600tick超时，七项实机通过。
T1九项回归与11英雄主武器/F5–F11/785语音烟测通过；天然树冠导致的无效首轮测试及修正已完整留证。
可见像素/片段见`research/fix/T2-verification.mp4`（10秒）和768×624 JPEG对照图，详见`T-report.md`。

当前`paths.meshAssets=research/fix/T2-lab/mesh-assets`，含新rivet及其余105包；该一项配置有意保留，其余launcher原值及个人世界选择已恢复。
私有资产不在源码/JAR；未来整包输入28个文件及guest/六DLL的SHA见`research/fix/T2-rebuild-files.txt`。
**dist未重建**，正式包仍46/26旧基线。不能把开发修复说成ZIP已更新。
正常保存退出、无强杀/残留，桌面2560×1440@200；7499个人档案SHA零差异，无无关源码改动，无提交/删除。
证据`research/fix/T2-lab/evidence/closeout.json`。不代表全英雄全技能或历史PLAYABLE-GOAL完成。


## 2026-11-03 — 线程 T：托比昂五项阻塞已实机修复，通用双武器槽47/27

开发仓库当前选择 **compositor47 / body27 / gate11 / emission16 / bootstrap10 / spawn1**。
根因是离线创建路径把武器数组槽1/2的原生脚本参数1c都初始化为0，当前选槽1f也为0：默认两武器同时显示，1/2后两图都退出。
新增 `native_weapon_slots.hpp`，在现有body逻辑owner按实际STU武器数组初始化索引和默认选槽，并调用原版Set&Notify；
输入例外使用当前已初始化多武器元数据证明，不再特判托比昂。天使0004同路夹具通过，但本轮未实机验收天使，完整辅助技能/MC手枪绑定仍需独立工作。

`research/fix/T-lab/evidence/accept-04/result.json` 的9项全部通过：默认仅枪，2锤击真实怪物并得50废料、
1枪左键20→19/目标20→14.5、右键19→14/目标20→10，一级炮台锤升二级、250→300修理，12次切换，
实际Shift/E/Q和Core自然End。此Beta原版右键声明耗弹5；建造预览需正常RMB取消，E不取消。
护甲包现有源码的投掷者排除逻辑实机通过：本人W走过包仍在，真实村民接同一包获得7.5MC吸收。
当前guest build SHA仍为 `1666e58f84d218e31883c06e51cf1e08d1a7fe4e266d2ce8fa9fec1515dae2f5`。

`regress-01` 其余11英雄均在1/2后主武器对MC造成伤害；F5–F11实际菜单/飞行/补能烟测通过，语音785/785、missing0、error空，准确双进程原声保留。
原生构建夹具、Java67任务、Python相关检查及正确HTTP入口通过。未声称11英雄全部技能/长时游玩或历史PLAYABLE-GOAL完成。

正常Stop已保存世界并退出：无游戏/监督器/录制辅助残留，无强杀，桌面恢复 **2560×1440@200**。
开发档案7499项SHA比较零差异，1442项源码检查无无关改动，设置和launcher配置恢复原字节；
`T-lab/evidence/closeout.json`、`T-report.md` 留证。交付 `research/fix/T-verification.mp4`（9秒）及768×708 JPEG对照图。
**dist未重建，下面线程I的正式包仍是46/26，不能把开发修复说成已更新ZIP。** 没有Git提交或删除文件。

## 2026-11-03 — 线程 I 一键整包验收完成，正式 ZIP 已生成

最新稳定出厂包 `data/oneclick-final-20261103-015311/OWMC-1.0.0` 已完整重新构建，
包含 C1 第三轮 EXE/启动脚本/UI 所有权协议、C3 隐藏窗口修复及后续 guest 资源复用修正、
C5 六项正式 DLL（46/26/11/16/10/1）。用户明确取消 30 秒目标，停止提速迭代。
同一 manifest 的连续三次新中文/空格目录（轮 11/12/13），仅双击 EXE 自动到原版选人，
耗时 **36.552 / 40.405 / 51.343 秒**。本包可见窗口仅启动器与原版游戏；
实际原版像素/MC 合成、调试栏与 DEV ENABLED 隐藏、785 语音、麦克雷原生弹药减少/
发射/MC 接收、正常世界保存、模块恢复、零残留与桌面 2560×1440@60 恢复全部通过。

正式目录 `dist/OWMC-1.0.0`；ZIP `dist/OWMC-1.0.0.zip`，5,303,337,840 字节，
SHA256 `a2209ca431830cf33af16a3d3e9333dedc28c920913d29953a188cde0ba02862`，
校验文件 `.zip.sha256`。11,499 项归档已逐文件回读/CRC/SHA 与整包 SHA 校验，源目录稳定。
旧 dist 四项保留于 `dist/_old/I-before-final-*`。严格出厂 manifest SHA256
`2b6373ac586955524467f7809797ac09e7a8183da06756460fa73ccdd40ee075`。
包内 guest JAR SHA256 `d165befa3ef836459f2c7b57860bcfcf117da187c3987bae982ad311d496f908`，
这是整包基线，不应与下方历史开发档案 installed JAR 混淆。

游戏进程已全部正常退出；开发两个档案与测试前备份逐文件 SHA 比较无变化，个人世界未动，
没有强杀或 Git 提交。完成标记 `research/oneclick/I-DONE.txt`；
验收/归档/档案保护证据在 `research/oneclick/I-evidence/{acceptance,final-archive,closeout,development-profile-closeout}.json`，
完整过程及失败轮次见 `research/oneclick/I-report.md`。
轮 10 的桌面截图被遮挡，已排除；轮 11/12 有清晰第一人称像素，轮 13 使用准确 HWND 的
Windows.Graphics.Capture。初始源氏直接确认后的攻击问题保留在轮 03，最终三轮明确选麦克雷；
跨机器环境未实测。本次是一键流程验收，不代表历史 PLAYABLE-GOAL 全英雄/技能/长时游玩完成。

## 2026-11-02 — 启动计时/优化候选；完整性能实测仍受显示与融合阻塞

任务 A 详见 `docs/STARTUP-SPEED.md`。所有游戏/监督进程已正常关闭（最终均为 0），
设置已按原字节恢复，桌面 2560×1440@200，未强杀、未提交、未查看截图。
分段单调时钟计时和有限 3 轮 benchmark 已接入；并行冷启动为显式选项 `startupParallel`，默认关闭。
修复非 Twilight 已选存档卡在原版实验性备份确认页的问题：使用原版创建备份并进入按钮，
随后 4 次 MC 真实玩家/帧就绪为 32.3～34.2 秒，但不代表原生融合或完整启动通过。

2560 两次尝试原版已出生，合成器却 poses/blended=0；临时 1920 的两次正常启动又被显示 TEST
拒绝（-1, flags=2）。没有成功选人基线/优化后各 3 次，也没有 Iris 开关对照；不能声称 47 秒已缩短。
Python 169 项、HTTP 契约入口、最终 Java build/check 与环境检查通过。
默认 guest build=installed `5f92c172e176ed0b2ca5bd03240804eb7ec386e27d377663055b117f0388ab68`；
AoA 档案与原版 DLL 未替换。关闭/设置恢复/备份证据在 `research/launcher/startup-closeout-20261102.json`。
`project_launcher.py` 本任务只改 `SessionBackend.clean_start` / `wait_started`；其余并发整合包/UI 工作须保留。

## 2026-10-25 11:30 — 通宵收尾：大量技能代码就绪，实测被远程桌面显示阻塞

状态：两个游戏均已关闭，显示 2376×1080@144，租约 restored。总表 57 ACCEPTED-live / 12 PARTIAL（9 项为“代码就绪待实测”）。
详细过程见 docs/_archive/2026-10/OVERNIGHT-PLAN-20261025.md；Codex 简报/模型索引 docs/SKILL-BRIEFS-20261025.md；审查 docs/CODE-REVIEW-20261025.md（13 项，已修 10，剩 F07/F11/F13）。

已写好并编译、尚未实测（下次先跑 `bash tools/dev_cycle.sh research/sprint-20261024/run_batch.py research/sprint-20261024/batchN`）：
- 美：冰墙（原版 0622 预览 node2/确认 node19；MC 真实地面、屏障碰撞 + 5 根原版冰柱 0400000000000932 2 倍绘制）；暴雪（064a Volley10；原版无人机 0946 模型、范围冰冻复用喷雾冰冻）。
- 狂鼠：榴弹/震荡地雷/捕兽夹（022b:31、096a:12、09ba:7；原版参数与模型；地雷遥控引爆信号未校准，未接）。
- 半藏：散射（b9:26，6 子箭 20° 反弹）、龙击（b9:76，双龙穿墙），原版箭模型。
- 托比昂：炮台/护甲包 MC 运行时（未接原版触发节点，需 research/sprint-20261024/calibrate_torb_kit.py 校准）。
- 黑百合：钩索绳索粒子。

显示/启动经验：
- 本机主显示由 GameViewer 远程桌面虚拟显示器提供；远程连接时它会把临时切换的分辨率改回，原版启动中途失败。dev_cycle 遇此退出码 3 并自动清理（tools/close_half_started_native.py 对半启动原版发 WM_CLOSE）。
- 2376 下原版选人界面不响应点击，必须 1920×1080（nativeFullscreen=true + nativeDisplayTemporary=true，仅动态切换不写注册表）。
- 原版窗口化 1920（Settings_v0.ini WindowedFullscreen=0）合成模块收不到帧，不可用；已恢复为 1。
- 驱动把注册表 2560@200 读回 @60；native_display_mode 的注册表比较只看分辨率/色深（19 项测试通过）。

原版模型管线：tools/ow_asset_chain.py（Codex，支持多子网格/LOD0/双 UV）→ tools/build_mesh_pack.py → ~/.universal-modder/assets/owmc-mesh/<名称>/ → OriginalMeshPack。

## 2026-10-24 23:40 — Claude 接管；黑百合 Shift/E 实测通过；显示租约修复

Claude 接管主导代码，Codex 只做重复性工作（见 AGENTS.md 省流与中文规则）。英雄状态总表 docs/HERO-MATRIX.md
（57/84 项 ACCEPTED-live；源氏三项按用户游玩确认）。黑百合抓钩与剧毒诡雷（原版模型）实测通过，详见
NATIVE-WIDOW-KIT.md 与 research/sprint-20261024/widow-live3。安装中的 guest JAR 为 c40a27ee…（两个配置）。

显示：用户桌面现为 2560×1440@200Hz；2560 全屏下原版客户端初始化失败，仍用 1920×1080@200Hz 切换。
本机驱动读不到注册表分辨率时，租约记 registryUnavailable 并以当前模式作备份/恢复依据（tools/native_display_mode.py，19 项测试通过）。
Codex 沙盒无权切换分辨率：凡需启动游戏的测试由 Claude 端运行（tools/dev_cycle.sh：关→建→装→启→测）。

## 2026-10-24 13:57 — All installed Boss entries and F8 portal menu accepted

New human scope completed at the entry/construction level: real AoA8 (four
normal+four elite) and Aether3 Boss entries, F12 global random, old Boss-bar
retirement/readmission, and F8 numeric/keypad portal selection. Read
ALL-INSTALLED-BOSSES.md and PORTAL-MENU.md. F8:1–8 build,9next,0previous;
F12:page1 AoA1–8,0switches to Aether1–3,9global random. F7/F9 shortcuts retained.
Current NeoForge catalog has14 actual portals. All14 were really constructed;
Nether/Aether/Abyss walking transports passed.11 original living Boss types and
author rooms/arena summoning passed, not11 complete fights/rewards/reset.

Final guest build=both installed profiles SHA256
b89986b9a12aedf03e060d3989073e6ff28dbf71031820e4aee8c071811cf1cd.
Native25392(created1792821215.6133695)/MC29532(created1792821195.2374167),
six unchanged42/26/11/16/10/1, real1920x1080 original McCree animated picker over
the Overworld village. Final ground/W movement/HP20/flight-off and own combat
fixture cleanup actually passed. Recheck identities next turn. Independent
supervision was launched with verified explicit job breakaway and left running;
no claim is made that the earlier absent processes were caused by Codex restart.
Current user world is isolated Overwatch Twilight Switch AoA Compatibility Lab;
old Fabric/TF saves/settings retained. Use launchers/Launch-Overwatch-AoA.cmd and its scoped
normal Stop command. No heartbeat was recreated; the old deadline task ended.

Actual evidence index: research/sprint-20261024/all-bosses-portals-acceptance.json.
aoa-boss-live1/all2 passed all8; aether-boss-all1 all3; portal-live3 all14 builds
but failed old End cleanup; final-menu/final4 passed the corrected owned End
cleanup; portal-enter-nether2/mods1 actual original portal transports passed.
boss-roundtrip-final2: End→Smash native shot275→270.36444, random9→real elite
Nethengeic Wither original arena, End same-UUID bar ADD/readmission and Overworld
removal passed. Final b899 cold checks final-menu/final-aoa/final-aether and menu
exclusion all passed. Final-picker actual grounding/W movement/picker passed.
57Gradle tasks,46 launcher fixtures, correct HTTP and environment passed.

Failures remain saved: protected fixture bedrock rejection, early world-load
harness failure, old End block-entity cleanup rejection, original terrain
blocking a Boss shot, and unsupported2376 original-picker construction refusal.
No failure was relabeled as success.2376 existing first-person numeric input was
tested separately and does NOT certify original picker compatibility. An actual
in-session display reversion recurred; normal focus did not recover it. Strict
normal Stop/save/restart restored accepted1920; its cause and TIMER/H gap remain
OPEN. Do not claim all general runtime bugs or all13dimension/all-hero roundtrips
fixed. No native callback/DLL changed, no attack freshness gate weakened.
Source/profile/save backup before work: all-bosses-portals-20261024-132138;
final source/artifact backup is indexed with the final audit. No commits/releases.

## 2026-10-24 13:20 — Human resumed Boss/portal work after the deadline

New human instructions explicitly resume work: connect all currently installed
AoA/Aether Bosses, repair bugs, and consolidate portals into an F8 numeric menu
(including the numeric keypad). The old13:00 deadline ended its automation and
does not prohibit this newly requested work. Single thread only; do not recreate
the deleted heartbeat without a new recurring request. At resumption no native,
project Java or supervisor process remained; cause is not established. Historical
22548/2016 are not current targets. New full source/profile/save backup:
~/.universal-modder/backups/all-bosses-portals-20261024-132138.

The pinned actual AoA3.7.16.1 Boss tag/registry contains8 Boss types (four normal
and four elite), not the unregistered historical roster. Aether has three Boss
types. Author source/API and actual installed JAR are being checked; private
references remain outside source control. F8 menu/build changes are currently
source candidates until cold deployment and actual client verification.

## 2026-10-24 13:04 — Time-bounded run ended; heartbeat removed, games retained

The13:00 Beijing deadline has passed. No development or game input occurred
after the deadline;12:40 freeze was retained. At the first post-deadline wake,
the expired ow-mc heartbeat was deleted through the app automation tool. This
does not mean the full backlog is complete. Its configuration snapshot is saved
privately under ~/.universal-modder/backups/ow-mc-deadline-20261024/.
Actual receipt: research/sprint-20261024/deadline-ended-1300.json. Final read-only
identities remained native22548(created1792815905.3526216)/MC2016(created1792815884.6385078),
supervisors32060/33648, six42/26/11/16/10/1 unchanged, original picker and healthy
transport. Both games and independent play supervision were left running.
Re-audit on any human-requested resumption; historical IDs are not authority.
Unloaded AoA altars/summoning, full Boss encounters and the other recorded
unfinished items remain OPEN in AETHER-AOA3.md/acceptance index. Do not resume
from another stale heartbeat or describe this cutoff as full completion.

## 2026-10-24 — Approved ordered sprint resumed until13:00 Beijing

## 2026-10-24 12:32 — Final AoA/Aether cold regressions accepted; bounded closeout

Guest04a79a38e8e9e9109856ad1e56c04dad1b4cf7b6d5e1704c054bcb58e491d608
build=installed in default Fabric and isolated NeoForge profile. Actual
launchers/Launch-Overwatch-AoA.cmd cold started native22548(created1792815905.3526216)/
MC2016(created1792815884.6385078), independent supervisor32060/33648. Re-audit
next turn. Six42/26/11/16/10/1 unchanged; original native McCree animated picker,
real Overworld village/night background,1920x1080 and20MC HP/natural ground.
No owned test targets/walls remain. Root viewed the actual menu, arrival and
final picker. Final actual passed/cleaned: aoa3-final-boss-menu3 (missing TF
choice rejected without request,9original BronzeBossRoom+Slider,old dragon bar
gone and same UUID restored on real return), aoa3-final-hit3 (native ammo/real
MC damage), aoa3-final-ground-picker2 (flight off/landing/real W movement/cleanup/
picker). Ground-picker1 failed only its already-closed test driver at the final
H; preserve that failed closeout, second independent driver passed.56Gradle,
3mod manifest fixtures, correct HTTP and environment passed. Global diff-check
found a pre-existing unrelated WorldFrameMappingCheck EOF blank; own paths clean,
not edited. A wrong unittest module invocation was corrected to its real script.

Read AETHER-AOA3.md and aether-aoa3-acceptance.json. Dedicated Stop CMD also
actually saved both games and restored display normally, no force kill. Old
Fabric default settings and old TF worlds retained. This establishes basic
AoA/Aether fusion and scoped F12/HUD behavior; all unloaded AoA altars/summoning,
full Boss battles/rewards/reset and all-hero13dimension/performance checks remain
OPEN. Do not call them finished or resume deprioritized Torb/TF expansion. Only
bounded final audits/docs after12:20; freeze12:40 and pauseow-mc at13:00, retain
independent playable background. Source backup aether-aoa3-final-20261024-122441.

## 2026-10-24 12:25 — AoA3/NeoForge real fusion and Boss HUD roundtrip; final menu cold check

Latest human priority supersedes Torb/Twilight battles: AoA3+Aether, global F12
random Boss and no stale Boss bar. Read AETHER-AOA3.md. Single thread and13:00
deadline remain; no new expansion after12:20, freeze12:40. Official AoA3.7.16.1
requires NeoForge, not Fabric. Official NeoForge21.1.264 installed after verified
46-library prefetch; no proxy/API/model/auth edits. Base AoA+Aether1.5.10 NeoForge
title passed. Official Connector2.0.0-beta17+ForgifiedFabricAPI+owoNeo then loaded
the unchanged Fabric bridge, new disposable AoA world,13actual dimensions and
real color/depth export. Original OW fusion/native McCree ammo+actual MC damage
passed/cleaned in aoa3-fusion-hit2; hit1 failed fixture remains. This is a basic
fusion slice, not all hero/dimension/Boss acceptance.

Use aoa3-connector-client ONLY for this environment; never open missing-TF old
saves in it. Original Fabric profile/default settings remain intact. Dedicated
launchers/Launch-Overwatch-AoA.cmd / launchers/Stop-Overwatch-AoA.cmd use tools/aoa3_passthrough_lab.py,
the original six-owner supervisor and strict normal stop with a scoped PROFILE.
Dedicated Stop/save/display restoration actually passed, no game force-kill.
Current cold launch via the actual CMD is underway; re-audit real IDs/creation.
Guest04a79a38e8e9e9109856ad1e56c04dad1b4cf7b6d5e1704c054bcb58e491d608
build=installed in both stopped profiles. Native six42/26/11/16/10/1 unchanged.
Prior2cf3f313/0068bf84 are real historical accepted increments, not current hashes.

F12 keeps1..8 only with TF,9global loaded living Boss/tag/AoA class recognition,
0Aether original dungeon. With no TF,9now locates original BronzeBossRoom and
requires a real living Boss, never a fake empty-room success. NeoForge actually
found two original Slider UUIDs in aoa3-aether-travel1 and aoa3-boss-hud-roundtrip2.
Boss battle/loot/reset were not tested. Fabric Gold/Silver missing-entity failures
remain; third Fabric pass was dungeon-entry ONLY. All not-yet-loaded AoA altars/
summoning are still open; do not claim arbitrary AoA Boss encounters complete.

BossHudTravelScope filters only retired original UUIDs, keeps original Map and
packets, actual server ADD re-admits, PBO epoch blocks stale readback. Actual
End dragon bar->F12 departure absence->same dragon bar on return passed/cleaned
on Fabric and again on NeoForge; root viewed the original composed images.
Final menu disables missing-mod entries;56Gradle passed, cold regressions pending.
Backups accepted-aether-aoa3-20261024-122029 and aether-aoa3-final-20261024-122441.
Do not resume the deprioritized Naga/Torb fixture. Preserve prior H gap/TIMER/
in-session display reversion OPEN issues; this work did not root-cause them.

## 2026-10-24 12:02 — Latest human priority: Aether/AoA3 and random Boss F12

Read docs/AETHER-AOA3.md. Human deprioritized Torb/Twilight battles and requested
AoA3+Aether plus expanded random F12 and no previous Boss HUD. Do not resume the
Naga battle fixture planned before that interruption. Single thread/deadline hold.
Aether official Fabric1.21.1-1.5.11 + stable owo0.12.15.4 actually installed after
strict Stop/full profile+save backup. Actual Aether dimension entered; original
Gold/Silver room generation found but no living Boss yet. Two failed fixtures
preserved; do not spawn substitute bosses or call dungeon transport a Boss pass.
Current candidate guest53013649564104f28aa8b4957bbac3047e6cca97fa4d5d5881c450b603207aaa
is cold deployed for F12 9/global random,0/Aether dungeon entry and original
BossBarHud retirement/packet-ADD revival/PBO epoch protection.56Gradle and3mod
manifest tests/HTTP passed; actual third arrival/random/old HUD verification pending.
Six native42/26/11/16/10/1 unchanged. New actual identities must be re-audited.

AoA official3.7.16.1 package acquired and inspected: NeoForge>=21.1.200 required,
not Fabric. Required Gecko/Tslat/SmartBrain dependencies already nested. Isolated
aoa3-neoforge-client staged only, no accepted fusion. Official NeoForge21.1.264
installer's Java library requests timed out; only that exact helper was ended,
Python prefetch of installer-declared URLs/SHA1 under existing network is running.
No game kill/proxy/model/auth/API edits. All sources/hashes/real failures in
private mod-cache/boss-mods-20261024 and research/sprint-20261024. Preserve old baseline.

## 2026-10-24 11:32 — Torb Core charging fixed; complete armor/turret still open

Read NATIVE-TORBJORN-CORE.md and research/sprint-20261024/torb-core-charge-acceptance.json.
Guestdfa55f9fb3aedca1fc453875b59b783b1f1173e38b2632bd08843605e0589332
built=installed after strict normal Stop/save. Six42/26/11/16/10/1 unchanged.
Final actual native13812(created1792812605.5368965)/MC31120(created1792812588.519281),
supervisor30808/child; recheck next round. Original Torb animated picker, real
Overworld village/night background,1920x1080 and independent play retained.
Actual MC20HP/no owned target/wall/effects. Root viewed all four Core active
images, actual Core/Widow recording contacts and final picker.

Real before trace core-health2 found original entity04bb=20s, separate local29e=.7s,
but sampled health arrays stayed base200/MC20. HealthPool19 literal300 is not an
authenticated MC armor route. Actual bug: meter reached76.44895 during active Core.
New exact1c2 nodes21/30/19/20/17 binding suppresses passive and actual-hit credit
through the native active phases. Missing/partial/wrong identity refuses credit;
actual End resumes only new idle credit. No guessed timer, key-driven skill,
new native callbacks or native script calls. No armor/turret fake implementation.

Five real Torb passes/cleaned/video0: four worlds each original Core/rivet20->14.5/
meter0, actual End/new idle charge/ordinary20->14.5; cold active-Core->76->newTorb
clears old phase and normal attack works. Observed End19.20-19.32s after first
sampled active state, not a claim of exact20.000s or2016/retail values. Shared
Widow regression3 really passed reveal/actual hit with meter0/End/idle/ordinary.
55Gradle,52supervisor,9binding-ACK and correct HTTP passed. Backups
torb-core-charge-20261024-111827 and accepted-torb-core-charge-20261024-113155.

Failures preserved: live1 failed before Q after supervisor's loaded emission
health check rejected; later same six owners healthy/zero failures and adopted
without new injection. Root cause remains unproved. Widow regression1 expected
20HP after its explicit hit; regression2 read before server target publication.
Harness now waits actual target/wall and checks its real post-hit HP at End.
These do not weaken production freshness. Original hero fixture constructor was
refused before focus/input: same native29100 had current+registered/window revert
to2376x1080, while active lease target stayed1920. construction-failure.json
preserves it. Normal Stop/save then normal cold restart recovered; hero2 passed.
Do not claim the live display reversion is fixed or2376 picker works.

Next avoid unbounded Core armor/turret guessing: their server route, incoming
damage/armor semantics, scrap/hammer remain open. Advance a verifiable original
Widow E/Shift or real Naga/Minoshroom battle/reset and approved maps/UI. All
hero kits/five Boss maps/UI are still incomplete. H pose gap/TIMER writer and
this live display reversion remain OPEN. Single-thread12:20/12:40/13:00 unchanged.

## 2026-10-24 11:08 — Native Widow Infra-Sight accepted; shared skills preserved

Read NATIVE-INFRA-SIGHT.md and research/sprint-20261024/widow-infra-acceptance.json.
Guest860dd3c730487c3f2bd630ac67d4675146fec00285737f6e86621f81e87121b6
built=installed after normal Stop/MC save; six42/26/11/16/10/1 unchanged.
Final actual native14644(created1792810237.9891343)/MC31492(created1792810220.3256333),
Python supervisor31144/child. Historical identities only, recheck next round.
Root viewed four-world original red visor+real red MC wall silhouette, no
silhouette after End, Sonic/Mei regression images and final original animated
Widow picker/Overworld sky.1920x1080 and independent play background retained.
MC actual20HP; target/wall/Mei freeze/Infra view clean.

Actual original graph0067 nodes6animation/13effect/10timer/18windup, typed literal
15 and current variable237=15, drive local loaded living nonplayer MC outlines.
No key creates reveal, no global glow/team mutation, no server damage/weakness
bypass or chunk/entity loading. Original hands/visor/HUD/animation/meter stay.
Explicit PVE target policy is NOT authenticated OW server team/invisibility;
menus/focus/source loss conservatively revoke and do not join old active Q.
150ms source/view and500ms pose bounds unchanged; new-scope active baseline cannot
replay. Fifteen-second cap is not extended by repeated snapshots. Sampled first
active span14.937s; whole native cleanup observed about15.7s, not exact15.000s.

Six real passed/cleaned/video0: four worlds' covered target20HP/no damage,
original Q+red MC outline, End clears, active charge0 then idle natural credit,
native ordinary attack20->17.400002; active-hit credit0; hero76 and TF->Overworld
interrupts clear old reveal, fresh Widow does not replay. Typed original Q
windup/animation/effect/timer now suppress passive/damage credit; health/readiness
reject missing current Widow skill acknowledgement.55Gradle,52supervisor,
8scope/ack fixtures and correct HTTP passed.

Shared one-world real Sonic arrow/stone silhouette/expiry/replay/ordinary20->7.5
and Mei real chill/freeze/cover/AI+travel expiry/recovery/icicle passed/cleaned/
video0. Not full all-hero or new four-world regression of older skills.

First Widow live1 failed BEFORE Q: Python binding referenced primitive shadowed
by another branch's local import, ending supervision, not either game. Logs and
failure preserved. Own import alias fixed; direct current read-only prepare
passed. Supervisor-only adoption re-used the same six healthy owners, no extra
injection/game restart. New live2 and later passes are separate evidence.
Final supervisor3 uses the new skill-ack check, final actual reentry/readiness
confirmed. Private backups widow-infra-20261024-104646 and
accepted-widow-infra-20261024-110826 preserve source/settings/profile/JAR.

Mei E preview0622 did not confirm actual wall in the air lab. Fresh Q entered
064a Volley10 but no factory: read-only graph21nodes/13states, runtime states[5]
==nodes[10], flags408003; gate11 does not authorize its extra bit2. Don't widen
general masks or claim this proves entire Blizzard server path. Explicit deferral
details NATIVE-MEI-WALL-BLIZZARD.md; production wall/Q unchanged. Torb original
Q calibration1 captured1c2 HealthPool19/effect20/chase17 and windup/animation,
not complete MC armor/turret/core. No factory expected from Q-only observation.
Next verify Torb real parameters/armor boundary or original Widow E/Shift, then
Boss/maps/UI; do not turn snapshots into completed skills. All-hero/five-map/UI
goals, H pose gap/TIMER root cause remain OPEN. Single thread,12:20/12:40/13:00
boundaries unchanged. No imported private game/Minewatch assets or unrelated commit.

## 2026-10-24 10:31 — Mei spray freeze accepted in four worlds and during hero switch

Read NATIVE-MEI-FREEZE.md and research/sprint-20261024/mei-freeze-acceptance.json.
Guest8c5e7d5bcb7d8694e30d24b12ee52221d2ad03605fcff3938b5f6c1702714a56
built=installed; six42/26/11/16/10/1 unchanged. Final actual native26680
(created1792808578.0166929)/MC29816(created1792808561.1781073), independent
supervisor16808/child. Historical identity only: re-audit before next inputs.
Root viewed all four real frozen-target images, recording contact and original
animated Mei picker, Overworld sky/1920x1080. Actual MC20HP/no test objects,
wall0/Mei effect entries empty; background usable.

Five real passed/cleaned/video0: Overworld live2,Nether,End,Twilight,hero-switch2.
Native actual spray2.25HP/40m/s/10m successful contact -> partial slow/decay,
stone cover no damage/no chill,30contact freeze, actual AI/travel gate without
persistent NoAI,90tick expiry, speed restored.5 and real movement resumes,
then icicle200->192.5 with no borrowed chill. Frozen movement0m; recovered
1.0444-1.2004m. During freeze, changing to76 retained the target timer and his
native rifle actually damaged it with no new chill; expiry and Mei reentry pass.

This is an explicit MC reconstruction using pinned Minewatch2018 timing, NOT
authenticated Beta2015/2016/retail freezing. Ordinary vanilla non-boss mobs only;
players/mod mobs/Bosses and mid-freeze world transition remain unaccepted. Own
temporary movement modifier and server AI/travel Mixins avoid saved NoAI locks;
vanilla gravity retained. No source/art copied. Runtime removes ordinary MC
attacker-directed spray impulse while preserving previous velocity and real
teleport/removal reactions. No new native owner/script call or freshness change.
Full Mei wall/Blizzard/Cryo shell remain OPEN.

First live1 failed to reach30contacts because target drifted out of spray;
candidate6c874149 preserved. First hero-switch failed a replay assertion across
the one-tick diagnostic publication boundary/possible last real flight, before
switching; not proof replay created damage. Its recorder wait was too short;
separate-cleanup passed. Corrected harness drains flights/stable old-last-shot
before replay baseline and records40s bounded cleanup; new hero-switch2 passed.
Failures were NOT rewritten.54Gradle tasks, environment and correct HTTP pass.
Normal Stop receipts1792808235120948400-28824 and1792808521493327000-14716 fully
saved/exited before cold copies; no loaded JAR/DLL overwritten. Private backup
mei-freeze-20261024-101352 and accepted-mei-freeze-20261024-103054 retain sources,
profile/config/JAR. H pose gap/TIMER root cause remain independent OPEN.

HanzoQ bounded original calibration captured b9/node76/resource034f20m/s/5s/10m,
status8/type1/result0; contextual635 damage unbound, no authenticated double
dragon path. Temporary deferral, NOT MC Dragon completion; see NATIVE-HANZO-DRAGON.
Next continue Mei wall/Q if verifiable or Torb/Widow concrete event/calibration;
do not repeat known deferred Scatter/Junkrat geometry without new evidence.
Boss/five maps/UI/performance/cleanup and all-hero goal still OPEN. Single thread
and12:20/12:40/13:00 boundaries unchanged; no agents or unrelated changes.

## 2026-10-24 10:00 — Cryo fire cleansing accepted; real normal-stop readback transient fixed

Read NATIVE-MEI-DETAILS.md, NATIVE-DISPLAY-LIFECYCLE.md latest, and
NATIVE-JUNKRAT-CALIBRATION.md. New accepted guest built=installed SHA256
e9f1b7c02f0422f14b5fcd13f80ca8725e20e669367308b6aa48b276d76f47c1.
Native six42/26/11/16/10/1 hashes unchanged. Latest actual native29556
(created1792806697.7124667)/MC12808(created1792806680.8427014), supervisor29840/
child; recheck next round. Final root-viewed original Mei animated picker,
Overworld real MC background,1920x1080 fullscreen; independent play background.

Mei's existing fresh original Cryo heal phase now extinguishes its MC owner,
including another ignition while active. Real four-world passed/cleaned/video0:
fire before Cryo, active clear/reclear, real native150HP/3.9s healing, original
End, new fire afterEnd remains, no lingering heal, actual icicle20->12.5. Real
Bastion repair negative control healed5MC HP/s but retained fire/extinguished0,
release and Recon20->16 passed. Final cleanup verified actual MC HP20/alive/
creative immunity restored, no test fire/targets/walls/Sonic. Index is
research/sprint-20261024/mei-cryo-fire-acceptance.json. This is NOT full Mei,
freeze accumulation, ice wall, Blizzard, visible Cryo shell or mid-Cryo switching.

Initial fixture-only7e12f7c7 JAR/before1 failed BEFORE Cryo because vanilla creative
immunity itself cleared fire; not a valid before-fix reproduction. Preserve it.
The explicit isolated Switch-lab fire helper now temporarily disables only that
ability flag, preserves/restores it and fire ticks, and uses a safe6HP margin.
It cannot grant native skill authority. Current fix keyed to actual fresh Mei
phase only, no duration/healing/budget/ownership changes. Minewatch2018 exact
source/blob/hash recorded as private semantic reference; no code/art imported.
Native current Mei primary2.25HP/40m/s/5s/10m/status0/type3 was actually recaptured.

Normal Stop26340 failed after native normal exit on final REGISTERED=None again;
1792806335604026600-30612 remains failed, normal retry1792806355280859500-28420
completed display/MC save before restart. tools/native_display_mode.py now does
bounded OBSERVATION-ONLY final readback retries forNone; real mismatch/new native
still reject, no repeated mode mutation/strong kill/stale combat authority.
Actual Stop30220 receipt1792806640150788800-27504 passed with readbackRetries1,
all restore/normal close/2376x1080/144 desktop restore/MC save completed.19 display,
19 normalStop fixtures plus53 Gradle tasks and correct HTTP contract passed.

Hanzo Scatter remains temporarily deferred: current factory has no observable
projectile for split geometry/timer oracle; don't guess .65 bounce/context980.
Junkrat actual385 primary20m/s/10s/100m was captured; native31/38 direct40/blast80,
restitution.5 and unknown timer/motion fields need actual interpretation. No MC
Junkrat grenade/mine/trap/tire enabled; details in calibration doc. Continue one
verifiable remaining defense skill from current metadata; full freeze/wall/Q,
Torb/Widow and Boss/maps/UI remain open. Don't turn these bounded deferrals into
full completion. H/camera gap and TIMER cause remain independent OPEN issues.

Private backup mei-cryo-fire-20261024-094502; accepted increment snapshot/index
records exact new sources/profile/hash. Never deploy fixture-only probe as
production. No loaded JAR/DLL overwritten, extra owner/reader or retired experiment.
Keep single thread and12:20/12:40/13:00 cutoff, protected Boss Free world and APIs.

## 2026-10-24 09:33 — Hanzo climb four-world acceptance; Scatter original split calibrated

Read NATIVE-HANZO-CLIMB.md and NATIVE-HANZO-SCATTER.md. This round did not change
production JAR/DLLs: guesta33b051c and six42/26/11/16/10/1 remain accepted. Exact
native26340/creation1792803216.3757503 and MC1248/1792803199.7798753 were rechecked;
future rounds must re-audit. Independent background remains usable,1920x1080
fullscreen, final actual original Hanzo animated picker over MC Overworld sky.
Root viewed final picker and real stone-contact images from four dimensions.

Five actual passed/cleaned/video-exit0 climb receipts: Overworld current2,
Nether,End,Twilight and Soldier76 negative control. Hanzo rose4.1768m(first3)/
4.0244m(TF), completed mantle with creative flight OFF, stood after release,
advanced original native climb ticks, then actual bow20->7.5.76 only jumped
1.2522m with no climb starts/native ticks and rifle still damaged. Index is
research/sprint-20261024/hanzo-climb-acceptance.json. This is the existing MC motor
acceptance, not new movement code, original numeric parity, all wall shapes,
mid-climb interruptions or full Hanzo completion.

Initial climb-current1 remains failed: fixed1.2s forward hold walked off the far
edge of the one-block-thick wall AFTER its0.96m mantle completed. Release upon
observed completion passed. Do not call that trace a production mantle repair.
No artificial movement lock, flight or teleport was used to pass climbing.

Current real E released Scatter1a4 at90m/s/lifetime10/range300/status8/type1/result0.
Actual b9/node26's split config contains a SECONDARY Volley, six count, bounce
integer5, restitution.9, parent spread20 and mode2. Child speed references charge
with .8/20/65, damage contextual980 with node84 initializer15/75/charge. Exact
raw expressions are saved; existing pure-product guard rejects this new path.
The diagnostic evaluatedDamage0 is unbound default, not proved zero original
damage. Split geometry/context/surface response remain unproved; no Scatter
production admission/MC damage has been enabled. Do not apply generic .65 bounce.
Next bounded calibration or explicit deferral, then Dragon/remaining Hanzo and
Junkrat/Mei/Torbjorn/Widow, real Boss/maps/UI. Do not repeat H failure indefinitely.

Environment and correct HTTP contract passed. Profile/config backup is private
hanzo-scatter-calibration-20261024-092224; exact path in calibration result.
Docs/source/options backup hanzo-climb-docs-20261024-093303. No Minewatch assets
imported, native code/bindings and original attack freshness unchanged, no extra
reader/owner. H/camera publication gap and TIMER root cause remain OPEN.
Single-thread and12:20/12:40/13:00 cutoff boundaries remain unchanged.

## 2026-10-24 09:04 — Hanzo native Sonic admitted and visibly accepted in four worlds

Read NATIVE-HANZO-SONIC.md and
research/sprint-20261024/hanzo-sonic-final-acceptance.json first. Current accepted
guest is a33b051c7de7918e85871bd0c15c7d0d92ce9fa10816ed4abb9ba4ab56621e55,
built=installed. Native six42/26/11/16/10/1 hashes are unchanged. Actual final
native26340(created1792803216.3757503)/MC1248(created1792803199.7798753), independent
supervisor13064/child,1920x1080 fullscreen; root viewed original animated Bastion
picker over actual MC Overworld night sky. Re-verify these identities next round.

Current real original b9/node20 emitted0149 strong at90m/s and020d short/mid at
28.9/60.1m/s, lifetime5/range100, status8/type1/result0. Current constructed c3
was actually read and typed:10second/10range variables, Wait and TrackTargets.
The adapter deliberately labels fixed MC impact and10m sphere as reconstruction;
the original TrackTargets shape/attachment/pulse presentation is NOT authenticated.
No Shift/logger-produced fake shot or new callback/native script call was added.
Both ordinary and Sonic contextual125HP damage remain original factories.

New typed armory guard validates current owner/graph/node/config/resource/prefab
and c3. Full resource-tree snapshot raced actual loading in live1. Replaced it
with existing coherent exact-key lookup; pending/missing current resource causes
whole binding retry, never a cached primary-only partial success. Earlier wrong
declared-type guards and live1 failure remain recorded. Native request wire unchanged.

Sonic uses actual deduplicated original admission -> retired loaded MC block/entity
contact ->200tick scoped detection. Real live4/Nether/End/Twilight2 all passed:
ordinary125HP20->7.5 before/after, real stone impact while covered target stays20,
same entity revealed behind stone, one impact, replay does not extend duration,
expiry clears. Root viewed the four actual red silhouette images in the contact
sheet. Both active-pulse hero replacement and active Twilight->Overworld transition
revoked the old reveal BEFORE natural expiry and allowed fresh ordinary damage.
Those two cases also passed/cleaned with real native events. Remaining Hanzo
Scatter/Dragon/wall climb/attachment/pulse fidelity are NOT complete.

Critical visual fix: initial live2/3 server checks passed but root images had no
outline. Actual1.21.1 bytecode proved outlines composite AFTER renderWorld, and
the vanilla/no-Iris export also bypassed pendingRender at an earlier END event.
Both paths now export after the original vanilla outline framebuffer composite,
before GUI/postprocessing, with source MC hand excluded. No duplicate world render,
invented HUD silhouette, global glowing potion or team mutation. Final live4's
client diagnostics also confirm loaded matching UUID/model/host, isGlowing/hasOutline
true and red color. The earlier visual failures are not promoted to passed.

Initial Twilight row failed while the real client DownloadingTerrainScreen still
transitioned after server/body readiness; no attack/fixture followed that failure.
The failed row remains. The test now observes actual creative client readiness
before input, without weakening Identity.health; fresh Twilight2 really passed.
One normal Stop also failed after actual native exit on registered display readNone;
normal retry completed desktop restore and MC save BEFORE any relaunch, no force.

Final new-capture Bastion Tank regression passed actual direct/blast/cover/terrain,
range/model/replay/charge suppression/End natural continuation and Recon damage;
owned fixtures cleared. Final API had no target/wall/active Sonic; H returned to
the original picker. 53 Gradle build/check tasks and correct HTTP contract passed.
Backups: private hanzo-sonic-integration-20261024-083304 and hanzo-outline-20261024-084641.
No Minewatch assets/code copied this increment. Process/module final audit is
current-runtime-audit.json; seven actual acceptance receipts are indexed above.

Original native H/camera7s publication gap and old TIMER cause remain OPEN; this
MC capture fix does not prove either cured. Next ordered work is Hanzo remaining
typed skills, then Junkrat/Mei/Torbjorn/Widow, original Boss fights/maps/UI/cleanup.
Keep single-thread rule,12:20 expansion stop,12:40 freeze and13:00 final deadline.

## 2026-10-24 08:12 — Native menu publication gap isolated; current Bastion forms tested

Current native29520(created1792799418.0418055)/MC10476(created1792799401.2362573)
were freshly identity/hash/module checked. Six owners42/26/11/16/10/1 and guest
af92f746 remain unchanged. Environment prerequisite check passed. Original1920x1080
fullscreen and independent supervision remain active; final original Bastion
picker pixels were actually viewed. PIDs are clues, not authorization for later runs.

New bounded independent READ-ONLY mapping trace reproduced the McCree H failure:
native host pose stopped at frame190789 for up to7322ms. MC body stopped485ms
after its last host sample, consistent with HostPoseReader's existing500ms
camera rejection. During the body gap MC captured1044 more frames and its world
advanced100 ticks. Thus this instance was NOT a stalled MC client tick/body-only
publisher: the original native observation channel stopped first. The existing
compositor report had viewMode2 and growing frames/heldFrames while poses held;
the exact rejected/missing draw stage still needs proof. No freshness or3s menu
deadline was widened. Full suite again failed H; charge motion/fire lock/native
End/real ordinary damage passed. Actual video shows held last composed hand
frames. Separate same-pawn cleanup passed and failures were not relabeled.
See NATIVE-MENU-PUBLICATION.md and menu-publication-{trace1,deadeye1} under research.
The bounded reader finished and unmapped; do not leave or stack a same-session reader.

Then current-build Bastion forms/self-repair acceptance passed and cleaned in
bastion-forms-current4: real repair2->8.75MC HP, actual original rate5MC HP/s,
release stops healing,20 cap; Recon moved2.75m on actual floor; Sentry moved0;
original Sentry attacks20->2HP and Recon after reconfiguration20->16HP. Root
viewed actual forms contact and final animated picker. This is ONE Overworld lab,
not four dimensions/full-kit fidelity/complete native visual or audio parity.
No production source/DLL/JAR changed; earlier Tank acceptance remains separate.

Keep forms-current1/2/3 failed: first start() removed the lane and native Y velocity
showed falling; second same-hero selection retained Sentry instead of recreating
Recon; third correctly blocked F6 takeoff in Sentry. The final harness first
replaces Genji->Bastion, and uses explicit air fixture ONLY after grounded Sentry
immobility proof. That fixture is not a new gameplay flight permission. Existing
profile/config/source backup: private menu-publication-20261024-080437.

Next: bounded native camera/draw-stage diagnosis (do not substitute stale body or
an invented pose), then ordered Hanzo typed Sonic factory/config calibration and
integration. Preserve deadline/single-thread rule and retained current baseline.

## 2026-10-24 07:55 — Fullscreen restart lifecycle and gate-stop report repair

Read NATIVE-DISPLAY-LIFECYCLE.md and research/sprint-20261024/ first.
Production now prepares the enumerated1080p display mode BEFORE native process
creation and durably binds its original-desktop backup to the exact native
identity. Normal Stop restores original current AND registered desktop after
actual native exit; it refuses live owners/user-changed modes/bad backups.
Do not move that mode switch after cold_ready: actual8488 failed composition.
Driver dmSize188 and index0 cache refresh are handled explicitly, preserving
both failed first attempts. No native DLL/JAR or callback-owner change.

Actual5428 stop first failed because gate11's complete terminal report remained
.json.tmp despite original Volley pointers being restored; exact rename error
was not captured. tools/stop_passthrough.py now recovers ONLY the pinned unique
production11, exact request creation/admin, no entry/tick lab hooks, success
terminal AND all three actual original pointers. It cannot accept JSON alone or
skip global/input/light/FPS restoration. The retry full-stop-v2 actually passed
strict native close, precise console pause, actual normal exit, both desktop
modes1920->2376 and normal MC save/exit. No force. The original failed stop stays
failed. Private source/report backups: gate-stop-report-20261024-074813 and
display-lifecycle-20261024-073136 under ~/.universal-modder/backups/.

Then actual full cold start4 created native29520(created1792799418.0418055),
MC10476(created1792799401.2362573); defaultdesktop2376 was automatically changed
to accepted1920x1080/144 BEFORE native startup. Fresh picker/clicks/native attacks
worked; six owners42/26/11/16/10/1, guestaf92f746 unchanged. The private active
receipt is ~/.universal-modder/runtime/native-display-lease.json. Treat these
PIDs only as clues and re-verify live creation/module/hash before acting.

display-lifecycle-bastion-smoke actually passed/cleaned on this new session:
real03ce direct/blast/attenuation/cover, block collision/destruction,48-block
travel, model render, exact-once replay, Tank charge0, End natural continuation
and real Recon damage. Root viewed its actual contact sheet and final original
Bastion picker. This is one Overworld lab with diagnostic Q, not all forms/four
dimensions or complete Bastion reconstruction. Current independent supervisor
retains play at the original picker over MC. Fixtures and narrow scope are in
the display document; proper HTTP contract passed.

Important OPEN regression: the new cold McCree run passed charge movement,
firing lock, native End and ordinary damage, but its full H test FAILED (first
camera170ms, then body publication beyond original3s). The latter menu wait uses
the existing same-identity observation-only gap handling; no extra combat/stale
permission. Do not claim the earlier warm v3 pass covers cold startup. Separate
cleanup closed the menu onto the exact SAME pawn, observed actual owned-object
removal and returned to picker; test failures were retained. Next inspect that
source/selection publication boundary, then ordered Bastion forms/defense/Boss/UI.
Stay single-thread and honor13:00 deadline; no retired labs or43/44 promotion.

## 2026-10-24 07:15 — Deadeye full control/menu regression actually passed

Read research/sprint-20261024/deadeye-menu-1080-v3/result.json. On actual
native13316(created1792795570.9374413)/MC2744(created1792795554.4128861),
the full controlled suite passed charging movement/view, real confirmed-fire
movement/view/F6 lock, original End and idle recovery, real ordinary damage,
H during another firing sequence, current-model reentry/owned-fixture cleanup,
and return to the original picker. No runtime DLL/JAR changed. Root viewed both
recorded contact sheets: original weapon/shot poses, individual target deaths,
skull markers, sepia and final original McCree preview are visible. This remains
a single isolated world, explicit diagnostic charge; not natural charge, all
dimensions, full original parity or a crash-free lifetime claim.

The final picker transition actually contained18 host-pose expired observations
and33 guest-body expired observations before a fresh same-identity sample arrived
within the original3s deadline. Those waits sent no input and gave no stale
combat permission. 17 harness and7 scope fixtures passed. The production150ms
combat deadline and foreign/future/torn rejection were not relaxed.

Important fullscreen correction: the earlier normal production restart DID
complete (restart1080-final-audit.json), including native normal close/MC save
and both fresh processes. However native exit restored BOTH current and registered
desktop to2376x1080/144Hz. At that size actual picker clicks failed although its
pixels and composition advanced; scaled/internal coordinates, dwell and hiding
the supplied debug overlay did not fix it. Restoring hero-select availability
for one bounded source-defined-byte probe also did not fix it; that byte was
restored to its exact original0 before any hero switch. Do not repeat these
failed probes or blame absent composition. Escape could reach actual Genji
hands/world, but did not repair picker selection.

A separate accepted1920x1080/144Hz display-mode control immediately restored
native Genji preview/confirmation and allowed the full Deadeye suite above.
Current desktop and original OW HWND are NOW1920x1080; original registered/current
DEVMODE before this control is backed up under private
known-1080-control-20261024-071157. This is an actual gaming-mode workaround,
not a proved arbitrary-resolution/input fix. Production restart must still
preserve/reapply the accepted mode after old native exit; do not claim that gate
complete merely from the earlier successful process restart. The test harness
now accepts only actually calibrated16:9 clients and refuses2376x1080.

v1 attempt had NO inputs: unquoted PowerShell floating arguments truncated exact
process creation times. Quote both timestamps; never weaken identity comparison.
v2 retained the real2376 picker failure. v3 passed and cleaned; earlier failures
are not relabeled. Backups: private deadeye-picker-20261024-070110.
Current six owners42/26/11/16/10/1 and guestaf92f746 remain unchanged.
Next: make the accepted fullscreen mode survive the normal restart lifecycle,
then continue ordered defense/Boss/UI work. Single thread;13:00 deadline remains.

## 2026-10-24 06:45 — Fullscreen fusion restored, baseline42 retained

Read FULLSCREEN-RENDER-BOUNDARY.md and research/sprint-20261024/ first.
Working baseline is original42/26/11/16/10/1 and guestaf92f746, unchanged.
Actual registered display1920x1080/144Hz + original WindowedFullscreen=1,
exclusive flags0 and explicit FullScreenWidth1920/Height1080 restored visible
fusion. nativeFullscreen=true is idempotent; root viewed original Genji animated
preview, hands/HUD over MC, actual2.16m movement/ammo24->21, H back to picker.
No owned test objects were created. Old desktop2376x1080/144Hz current/registered
DEVMODE backups are private ~/.universal-modder/backups/fullscreen-display-20261024/.
The working1080p display mode remains set; restore old mode only after native
shutdown and re-evaluate startup. Arbitrary output resolutions are not accepted.

native3672(created1792795339.4209368), MC28192(created1792795138.5142791),
supervisor27128/26384 passed that smoke; 34213 composed/3 held, six unique owners.
Production normal restart from actual first-person is now being checked; these
IDs become historical upon its completion. Read latest final audit/live state.
This is not damage/four-world/full-hero acceptance. Failed43/44 stage candidates
were archived, and original dirty42 source/build script restored byte-for-byte;
their actual stencil targets were HDR26/GBuffer29, not a proved native HUD.
Do not promote44 or build42 from archived44 source based on pose/fixture success.

Production normal Stop wiring and actual full/partial-owner exits/MC saves passed;
Keep-Minecraft now passed actual native close preserving the verified same guest.
23 close/17 stop/52 supervisor/46 launcher/10 fullscreen fixtures and correct
bridge/test_contract.py passed. ABI verifier remainsf401296b. Combat restart and
MC-source-loss gates still need separate actual evidence.

Final-picker body-gap harness now retries only structurally valid, past-expired,
same source/guest/host/world samples in the existing observation-only opt-in and
original3-second deadline. Future/torn/foreign samples remain hard failures;
combat gates unchanged.7 scope/14 harness fixtures passed; actual full suite
pending. Adapt old2560x1440 coordinates to1080p; do not resize native to run it.
Continue ordered defense/Boss/UI checklist in this one thread, deadline13:00.

## Earlier approved startup notes (superseded where different above)

Latest user instruction: **one thread only**. All former subtasks are completed;
do not spawn, resume or delegate any further agent work. Continue the full
assault/defense, five-map, UI and bug-fix scope sequentially in this thread.
ow-mc was updated in place with this rule. The user also prioritizes OW fullscreen
before further gameplay iteration. Original inject PresentHook3f1ab writes zero
to gameBase17a1123 every frame (fixed-source/binary evidence saved); do not patch
the provided DLL or break its accepted SHA. Use original-window borderless
fullscreen via `nativeFullscreen=true` and the idempotent window_layout helper.
Actual WindowClass is `TankWindowClass`, so case-insensitive matching was repaired
after the first helper refused the capitalized name. An exclusive-INI experiment
failed camera/compositor startup and is preserved, not counted as success.

Production normal Stop has already passed actual picker stops with strict
restoration, original close/console acknowledgement, exit0/report classification
and MC save. A partial-start target had only bootstrap/localhero/compositor mapped;
the helper now inventories real callback module families after supervisor stop,
skips only truly unmapped owners and verifies the inventory again before close.
Missing reports for mapped owners remain hard failures. Its actual partial-start
normal close also passed without force. Evidence is underresearch/sprint-20261024/
and research/normal-session-stop/. Full combat restart and source-loss acceptance
are still separate pending gates. Restored all exclusive-INI flags to0 after the
failed experiment; only the external original-window borderless mode stays on.
The latest `start-borderless-only` cold launch is pending visible acceptance;
check current process/module identities again, never reattach over the failed PID.

The user approved PLAN-UNTIL-1300-20261024.md and clarified that the hour slots
are advisory: complete items in order. The13:00 Beijing deadline remains;
UTC cutoff2026-10-24T05:00:00Z. Automation ow-mc was updated in place to ACTIVE,
same30-minute heartbeat/thread. No duplicate automation was created. Stop new
feature expansion at12:20, freeze at12:40, save and pause development at13:00;
retain independent normal-play background. This supersedes old PAUSED directions.

Root owns all code, game input, build/deployment, shared lifecycle and acceptance.
Earlier preparation receipts remain useful read-only references; those agents
must not be resumed. Production verify_provided_shutdown_abi.py
must remain at its accepted f401296b SHA unless a later proved need is reviewed.
First priority is actual normal Stop/Restart wiring, then final-picker observation
and gameplay lifecycle regression, then defense/Boss maps/UI/final organization.

Entry prerequisites passed with .venv Python3.13.13. Entry guest remainsaf92f746…,
six modules42/26/11/16/10/1 unchanged. The prior games/supervisor were absent;
no old PID was assumed live. Settings/options/installedJAR and root-owned test
sources were backed up privately; receiptresearch/sprint-20261024/entry-backup.json.
Root selected a new isolated full-mod test world
`Overwatch Twilight Switch 20261024 Sprint Lab`, same seed, and requested the
first baseline startup. Latest live identities must come from real session status,
not this note. Boss Free user save remains preserved. Test worlds/fixtures are
not user play acceptance; successful F12 landing is not a completed Boss fight.

## 2026-10-23 — Twilight boss menu delivered; latest user requests one restart

After the wrap-up pause, the human separately requested a Twilight Forest world,
unlocked progression and F12 boss selection, then **“帮我重新启动一套”**.
These scoped requests authorize this work; automation `ow-mc` remains PAUSED.
The active profile is `Overwatch Twilight Boss Free 20261023`, seed
`-490526775015596785`, pinned TF4.8.754/Fabric1.21.1. The later launcher-selected
ordinary `Overwatch World 20261023-231148` profile was backed up before restoring
the requested Twilight profile for this restart. Do not assume historical PIDs
below are current.

F12 in native OW first person opens the Chinese menu;1–8 choose Naga, Lich,
Minoshroom, Hydra, Knight Phantom, Ur-Ghast, Alpha Yeti and Snow Queen. F12 closes.
The real `tfEnforcedProgression` rule is disabled, bypassing order/biome gates.
Original boss shields, weakpoints and combat phases remain; no replacement boss
or final-castle boss was invented. Destinations are actual original room entrances
or safe room edges, without excavation. Native camera direction is retained;
the player may need to turn after arrival. See TWILIGHT-BOSS-TRAVEL.md.

Final guest SHA256 `af92f746c1b6e736e3dddc25ec41b7fe8043430ff318026f5c97b0ba2ff6ebe0`;
server source `245fedb13a7897267cdf392268a617c74dde7633c5e4f94dedae4c2c4500f5b8`.
All52 Gradle tasks passed. Actual `research/twilight-boss-menu-20261023/eight-v5/`
passed eight original destinations, real floor/health, released owned tickets,
native composition and rendered-camera checks; root viewed all eight screenshots.
`repeat-v5` passed Naga→Minoshroom→Naga, including an already consumed original
spawner with a living original Naga. `final-controls` passed held-F12 deduplication,
normal close/reopen, actual1.8m walking and three native shuriken block hits.
No artificial bosses/fixtures were spawned; this is not all-eight boss combat
acceptance. Initial failures, wrong floors and old-camera test failures remain.

The entity lifecycle repair waits for the real ServerEntityManager LOADED state
under existing FULL33 tickets before querying an activated boss room; terrain
readiness alone was insufficient. It does not respawn missing bosses or enlarge
all ticket radii. Native modules remain the six existing unique owners
compositor42/body26/gate11/emission16/bootstrap10/localhero1. No loaded DLL/JAR
was overwritten. Strict native restoration and original close preceded each
cold deployment. Backups are under the private universal-modder backups directory.

Before the latest restart, both games and the old supervisor were already absent;
the stale session-status error was not used as proof of a live owner. Read the
latest `research/twilight-boss-menu-20261023/user-restart-audit.json` and
`user-restart-picker.png` for current identities. Restart completed with
native27556/MC32708 and independent supervisor23712/30540; six unique owners,
real Twilight dimension, progression disabled, original hero-selection screen
over MC. These IDs are historical as soon as a process is replaced. The older production
launcher Stop path and native TIMER root-cause issues remain open; this menu work
does not prove those fixed. Do not automatically resume the paused development.

## 2026-10-23 — User-requested wrap-up; continuous development paused

The latest human instruction is **“先准备收尾吧”**. No new feature work or game
tests should start without a later resume instruction. Automation `ow-mc` is
now **PAUSED**, while the independent normal-play supervisor remains running.
This is a requested pause, not completion of the approved development plan.
Existing source edits, private backups and successful/failed evidence are
preserved; nothing was published or committed.

Final live audit: `research/tracer-blink-visibility-20261023/final-audit.json`.
At wrap-up native9272(created1792753825.7246218), MC12576
(created1792753131.5803754) run the fully modded isolated
`Overwatch Twilight Switch 20261020 Ult Lab`. Root actually viewed Genji's
original preview and hero-selection HUD over real MC terrain; confirmation was
not clicked. Do not reuse these historical IDs as future authorization.
Six unique modules: compositor42/body26/gate11/emission16/bootstrap10/localhero1.
Installed/built guest SHA256
`928c338c4095798b1ca76a7279abf24661b2db6a39d3f758f602ee21c4e8f01b`;
compositor42 `85441d23e6d34000bcb1fc84192f4fe3726800f6dc57b90ed46d2162ac125a63`.
The hand-mask diagnostic marker was archived before the last cold start;
the current report confirms `handMaskTraceEnabled=false`, zero reported
adapter failures and viewMode2. This is not a long-duration crash-free claim.

Completed bounded increments:

- **Tracer Blink visibility repaired and actually reviewed.** In41, three real
  Blinks each lost36 frames: genuine hand projections1.74013–1.98089 were
  rejected despite complete native hand stages.42 accepts the original
  same-frame draw only for current native Tracer in first person; world-camera
  exclusion shares that classifier. Native FOV/animation are unchanged; there
  is no old-gun-pixel replay. All3223 captured42 frames retained the hand pair;
  three dense60fps contact sheets show both pistols throughout. World lenses
  remain excluded. Three real Blinks, wall collision,8 post-Blink native shots,
  real HP loss and fixture cleanup passed. Preserve the late117-frame reader
  gap and lack of a separate compositor-restored native control. This is not
  every-world/persistent-fists/full-kit acceptance. See TRACER-BLINK-VISIBILITY.
- **Latest terrain exceptions deployed.** Flashbang and Concussive have no
  newly added terrain explosion, retaining flash/air cues, damage/status/push.
  Six real skill tests passed: these two left24 glass blocks unchanged;
  Pharah primary,76 Helix,Tracer Pulse and Pharah Barrage destroyed eligible
  glass while bedrock survived. Videos and owned-fixture cleanup passed.
  Barrage small white impacts/orange effect were actually viewed. This
  supersedes older all-skills terrain wording. See EXPLOSIVE-TERRAIN and
  `research/explosive-terrain-20261023/live-v3-exceptions/`.
- **Pulse original mesh deployed.** Actual Beta24919 geometry/albedo/emission
  replace the MC two-box model; native throw, attached mesh and real terrain
  blast were recorded. Root viewed a real contact frame. Source/version/hash
  and incomplete material/countdown/debris parity are in PULSE-BOMB-ASSETS;
  private game assets are not public source files. Full orientation/entity
  attachment/four-world visuals remain unaccepted.
- **McCree actual-fire movement/view lock implemented.** Three real runs have
  featurePassed, charging movement/view, original End recovery and H interrupt
  true. One lock run held MC/native position and view at zero change for20
  samples/815ms, the next for19 samples/920ms, with real movement before/after.
  **Overall harness acceptance remains false:** live41-first had recording/
  cleanup failures; live41-final1 cleaned/recorded but failed final-picker
  waiting with Host pose stale; live42-final also cleaned/recorded but failed
  with Guest body scope stale. Preserve those false results. Root viewed the
  final1 native hands, lock marks and shooting contact sheets. Do not relax
  150ms identity/freshness or claim new complete four-dimension acceptance.
  See DEADEYE-INPUT-LOCK.

The latest guest build/check completed50 Gradle tasks; native42 CPU/GPU/depth
fixtures and correct `python bridge/test_contract.py` entry passed. Native
15548 and30976 both completed strict per-owner restoration, WM_CLOSE, original
shutdown/precise console acknowledgement and actual exit0 with no matched crash
report; neither was forcibly killed. The provided two-data-byte shutdown ABI
repair remains. TIMER writer/unknown Loop Exit/old Tracer fists remain open.

Important unfinished issue: launcher Stop/Restart still uses old
`proc.terminate()` after adapter restoration. The shared normal-close candidate
was **not wired** when wrap-up was requested. The tested verifier was restored
byte-for-byte to its task-entry backup, SHA256
`f401296b19f48e7e2d9e28271471e3ed1a20d08e236fb31725d8faaa7be11ba8`.
Candidate/manifest are in
`research/bastion-cannon-20261023/mc-shell/normal-session-stop/`; no half-wired
helper remains in production. Until fixed, use the verified
`verify_provided_shutdown_abi.py --close` path for native normal shutdown.

On resume prioritize final-picker freshness handling without weakening combat
guards, production normal-stop wiring/real acceptance, remaining world/hero
interrupt regressions, then approved defense skills, five Boss maps, complete
launcher and final organization. Five maps still have zero completed real Boss
acceptance; no new worlds were installed during wrap-up. Existing Recall,
charge/voice/light/particles and normal-play background remain. Hollywood
1080pLow/8 chunks/no shaders/day-night cycle/particlesALL are retained. No180FPS
minimum or completed all-hero restoration is claimed.

## 2026-10-23 — Current explosion rule and parallel user follow-ups

Latest user direction overrides older terrain-preservation notes: **every real
implemented explosion must be able to destroy blocks, at different strengths**.
Read EXPLOSIVE-TERRAIN.md before interpreting older Tank "stone unchanged"
results. Native beta metadata/damage are unchanged; terrain is an explicit MC
customization. Common projectile explosions and real Flashbang/Concussive/Pulse
impacts now use vanilla resistance, drops, loaded-chunk and unbreakable guards,
without applying entity damage or impulse twice. Terrain runs after this blast's
original cover/damage/status decisions. Source build/check48 tasks and correct
HTTP entry passed. Installed guest d4c9cb8ff5397f3e0c343709fd230aab8b020c7aea17e0afb59310c3a1126841.

Current observed user-play runtime native25624(created1792745944.920534)/
MC21696(created1792745927.2043777), six unique owners: compositor40/body26/
gate11/emission16/bootstrap10/localhero1. Emission16 SHA256
899033a800bdd0b772199c7a3bcc82c1beeb0db4bb7702d5e9ff40339e342da9.
Only current checkpoint/recheck identifies future targets; do not reuse these
IDs blindly. Evidence: research/explosive-terrain-20261023/checkpoint-user-active.json.
User was actively playing/using ChatGPT (foreground PID13308, idle0.218s);
extra hero changes/combat/focus loss invalidated controlled UI tests. Stop UI
input under interference and continue independent code. Do not blame these
failed tests on a proved native defect or count them as successful acceptance.
The initial explosion fixture also incorrectly required Bastion's3 armory
variants for every hero; corrected without changing gameplay.

Read-only actual user-play counters observed709 projectile explosions/2083
blocks removed, Flashbang1 burst/1 block, Concussive3/20, Pulse2/102 with no
terrain errors. This is real runtime evidence, **not a controlled full-kit or
four-dimension acceptance**. All owned fixtures were cleared before user play;
no user mobs, positions, maps or gameplay were subsequently cleaned/reset.

Bastion MC cannon is now implemented, unlike the older section below. Actual
original03ce factory ->50 direct/140 splash, swept collision, attenuation,
solid cover,48-block flight, model render, replay rejection and original End ->
Recon fire passed Overworld/Nether/End on bc18158c... and Twilight after cold
charge-fix deployment8e021969... . Models are explicitly MC-authored.48 blocks
is not proof of100-block cutoff. Original ground movement had separate earlier
four-dimension acceptance. New positive-terrain behavior has not yet passed
its new controlled four-dimension matrix. Preserve all old failed harness,
non-Begin and worker-transition snapshots; no unsupported cause attribution.
NativeChargeController now reads same-identity original Tank105 and rejects
active/unknown form charge; actual Tank splash/far kept0, original End resumed
new idle credit. Prior in-Tank credit333/1200 is fixed at that tested gate.
Read NATIVE-BASTION-TANK.md and private bastion-cannon/mc-shell evidence.

Latest priority follow-ups (source work, do not claim all deployed):
- McCree: after actual Deadeye confirmed fire through original End, lock both
  movement and view. Reuse the unique native input owner, current scoped data,
  no guessed Q timer, stale permissions or render-thread script calls.
- Pharah: actual Barrage ground impacts need a small visible explosion like
  Helix. Source now uses small EXPLOSION packets instead of intermediate smoke;
  the installed d4c9cb8f JAR still has the intermediate smoke policy.
- Tracer: inspect Blink's brief missing native guns versus raw native behavior;
  do not use old-frame replay or a fake MC gun. Real Pulse Bomb model is under
  private original-resource investigation; the installed model is the old
  MC-authored two-box approximation.
Parallel agents may own these files; coordinate before editing/building.

Other completed independent code, not game acceptance: launcher settings now
share action mutex/request-specific receipts and guarded save;55 fixtures pass,
actual new GUI path pending. Arena v2 privately converts81 old dust commands
in17 MCA+2 structure files, with original other bytes/commands/stages preserved;
repeat ZIP SHA2ebb56d9140253c2c26cfd7d4b30de6ea568fc53002bcead382e29aa40e7edf1.
It is still blocked_static,0 maps installed/fought; see ARENA-PORT.md. Hanzo Sonic
candidate classes are saved but **not wired/deployed**; see NATIVE-HANZO-SONIC.md.

Normal strict restore+WM_CLOSE+original console-pause acknowledgment passed
22116/18276/29836 with no forced kills this increment. Provided shutdown ABI
repair remains. TIMER writer/unknown Loop Exit/old Tracer fists are still open;
no current matching report is not proof of no crash. Preserve Recall empty
history, all other hero/voice/light/ALL-particle baselines and the approved
continuous plan. No publishing, messaging others or unrelated commits.


## 2026-10-23 — Recall empty-history repair and original Bastion cannon factory

Read RECALL-EMPTY-HISTORY.md and the new section of NATIVE-BASTION-TANK.md.
The continuous user-approved plan is still active; this is a bounded completed
stability increment, not all hero kits or all crash causes finished.

Current cold test runtime native22116(created1792736907.0493207)/
MC19532(created1792736889.7193532). Six unique owners now use gate11, with
body26/compositor40/emission15/bootstrap10/localhero1 unchanged. Gate11 SHA256
b53f738e2096ebb7043f8fffbb706a98de25e6e42c47be68365a544ef7a5ee51;
guest JAR8ea5e757a77aa57451e633482e9aaf99c62fb8ced76398f56397b97e752d139e.
Provided inject.dll shutdown ABI correction c82f8cea... remains installed.
Use the final-audit.json under research/recall-empty-history-20261023 for final
actual state; these IDs are evidence for this run, not next run targets.

Recall real defect: a fresh admitted cast with no MC pre-Begin history returned
without completion. Native root31 ended after real animation End, but history1
waited forever for phase2/3, locking real original primary. A narrowly scoped
500ms creative Switch-world fixture produced the real failure: native Begin in
the pause window, root End, history1 still active, real target20->20, no factory
or primary ammo consumption. The diagnostic baseline retained old refusal logic;
it is not the production JAR. Native original32->40 self-refill was separately
observed with adapter0; the first total-ammo assumption was rejected.

The production fix emits exact-cast cancellation only in that already-admitted
empty branch. Existing client still waits for real End and original logic owner
then completes history1 once. No new native hook/thread and no guessed timer.
Actual fixed-overworld-v3/nether/end/twilight all passed empty phase3->primary,
then normal Recall with real movement, HP2->20/ammo16->40->primary. Empty-mode
target20->15.199997, no MC heal/warp or adapter refill, all fixtures cleaned.
Actual screenshots were viewed.48 Gradle tasks, C++ phase3/current-scope fixture,
52supervisor/14map fixtures and correct HTTP entry passed. Earlier failures
remain evidence. One End observation saw unknown HTTP generation0 for27.6ms;
the test sent no input and resumed the same identity within250ms. This does
not prove the source-interruption root fixed. Positive foreign scope still fails.

Bastion gate9 rejected actual Tank024f flags400083/408003. gate11 narrowly
admits the proved original class/current owner/29nodes/22states and
m_states[19]==m_nodes[25]. The previous field+6c=11 interpretation was wrong;
it is not the runtime index. Failed gate10 evidence is preserved. Actual gate11
now captured ONE original03ce factory, current owner,60m/s/5s/100m/status8/type1,
zero filtered Tank calls and restored callback flags. The MC target stayed20:
03ce remains outside armory, so MC cannon damage is STILL NOT IMPLEMENTED.
After this original-event proof, next bind real shell/direct50/blast140/rings/
collision/visible explosion; do not invent unproved self-knockback semantics.
Actual gate11 overworld Tank move/collision/End/Recon/Sentry/active-Q swap and
post-swap Recon real damage passed. Other three-world cannon tests remain open.

Three strict restore+normal WM_CLOSE exits10208/30324/2016 passed with exact
original console-pause acknowledgment, no forced kills.30324 was a failed
startup attach-path mismatch (gate9 loaded while expecting10), not a crash;
attach and supervision now share native_weapon_gate_version.py to avoid this.
TIMER writer, unknown Loop Exit and historical Tracer fists remain open.

Map author packages are now actually acquired/preflighted: Shadow is really
1.21.4 and blocked as incompatible; Arena is1.20.4 with old datapack directories,
pending migration. Supplemental Mewoster is1.21 and structurally passes but is
not one of the five popular maps or gameplay accepted. No map installed/fought.
See PVE-MAPS.md and private map-catalog download-followup/download-next evidence.
No restricted Minewatch candidate has been production-imported. Launcher v1
and project cleanup retain their previous partial status.

Final actual state: native22116/MC19532, original animated Genji selection
preview over natural Overworld village/day, not confirmed; screenshot
recall-empty-history-20261023/final-picker_small.png actually viewed. MC20HP,
alive, grounded grass at57.5/65/12.5, creative flightoff, fixtures/hold cleared,
independent supervisor alive, six unique mapped module paths/hashes recorded.
No matching current native error report was found; this is not all-crash proof.
Final McCree20->13 and Genji20->9.5 actual attacks/replay passed as well.
ow-mc remains ACTIVE every30min with updated current docs/builds/next work.

## 2026-10-23 13:54 — approved continuous plan, shutdown ABI and launcher v1

User approved CONTINUOUS-DEVELOPMENT-PLAN-20261023.md with "可以，开始吧".
Thread heartbeat ow-mc ACTIVE every30min, no old10:00 cutoff. Work continues
through stability, defense6, five playable Boss maps, full launcher and cleanup.
Preserve existing work; all candidates/partial kits remain explicitly partial.

Current native10208 created1792734649.1345408 / MC13552 created1792733436.0110652.
Same six unique owners/body26/compositor40/gate9/emission15/bootstrap10/localhero1;
guest2d1b9e7b… unchanged. final-audit.json under research/continuous-20261023
records exact paths/identities. Final screenshot actually viewed: original
animated Genji picker over natural MC village/night, no hero confirmation,
MC20HP/alive/grounded grass/flightoff, fixtures cleaned, independent supervisor.

PROVIDED-SHUTDOWN-ABI.md records an actual repair of the supplied plugin's
proven slot4 return ABI error. inject.dll now c82f8cea31aca0da8e1cd0b2b4d1a6a1c671a86fa4f1a52120985cbeec2ff2d6;
original12a0cf4a… and pinnedPDB/private manifest retained in
~/.universal-modder/backups/provided-shutdown-abi-20261023. Only two DATA bytes
changed in exact PrometheusSystem slot4; existing return0 function/code/PDB/
DIR64 unchanged. No runtime patch/new hook/callback owner.26220 strictly restored/
stopped before install; executableSHA unchanged. New27304 report was actual
825346, not TIMER; source/actual CRT allocation and return ABI are proved.
Unknown Loop Exit scheduler and d1428b TIMER writer remain open.

Actual19496 passed eight Tracer overlap cases with real post-skill damage,
Pharah/Mercy/DVa each four-world natural charge continuity(12rows,~4.85..5.13/s,
noF11/grants).19496 and2424 passed actual WM_CLOSE/native teardown AFTER all
four adapters strictly restored and slot still corrected, then real exit0/no
matching current report; no forced termination. Original supplied atexit
system("pause") was explicitly observed and acknowledged ONLY on the exact
verified console, without global input.8544's first20s timeout remains failed
evidence, not relabeled. This is no all-crash/Tracer fists root-fix claim.

Launch-Overwatch-Minecraft.cmd is the new desktop launcher entry. Actual UI
was captured/viewed; corrected hidden-console entry showed the real UI, root
clicked Start and reached picker2424. Closing UI did not stop native/backend:
Genji->Tracer actual target20->13.999996 passed on19496 with six owners.
Duplicate Start reused the existing supervisor.35launcher/5settings/52supervisor/
14ABI/13map-preflight fixtures and proper HTTP contract entry passed.
Original pythonw redirector console/hidden-window attempt is retained as failed
harness/entry evidence, fixed via hidden PowerShell plus own-HWND Tk show.
Flight is F6; configure AND old session entry now reject F7..F11 conflicts
before startup effects. Config defaults/loaded guest unchanged.

PVE-MAPS.md/config/pve-maps.json: five metadata candidates only, zero installed
or Boss-accepted; first author's package route403, no unverified mirror used.
THIRD-PARTY-ASSETS.md/config/third-party-assets.json:33 private Minewatch
candidate files verified against fixed Git blob/SHA256; production imports0.
Known gaps include missing generic venom texture reference and unavailable
independent Hanzo arrow/Torb turret model. No files reorganized/deleted yet.
Next: bounded remaining lifecycle investigation, then Bastion true Tank cannon,
continue map-author package access/actual preflight and UI/map integration.

## 2026-10-23 all-hero passive charge repair, body26

The user explicitly reopened development after the prior10:00 cutoff to fix
natural ultimate charging for ALL heroes. No recurring automation was recreated.
Read ALL-HERO-CHARGE.md. Current native27304, retained verified MC from23316;
read actual process creation and session-status instead of reusing old IDs.

Actual defects: generic charge roster omitted8 of21 heroes; native HUD notify
accepted ONLY McCree and hardcoded1200 cost. Pharah really gained~5points/s but
displayed0%; Reinhardt/Mercy/DVa actually gained0 before the eligibility fix.
Now all21 are eligible; Genji keeps its dedicated single writer. body26 sends
original Set&Notify from the existing logic thread for20 non-Genji heroes using
their actual typed charge/cost and verified owner. No extra callback or remote
execution; compositor40 and other owners unchanged, still6 unique modules.

body26 SHA25666e4e47e68b280a8cc2e699ff3cfd94e231531699cb3a7e1370184540e3156e9;
guest2d1b9e7bf63e3552a7894a06c086137abd6e4b1faacd87c96f8260752d317794.
Source/config backups in research/all-hero-charge-20261023/backup.json.48 Gradle
tasks/14 native fixtures/51 supervision fixtures/proper HTTP entry all passed.
26 strict restoration SHA pin added;23316 was deliberately restored normally,
not crashed, after a bounded original-DVa HUD diagnosis. MC kept running.

after-all21 actual pass:21 idle-only8sec samples,4.8758..5.0835points/s, noF11,
attacks/time changes/grants. Original paired HUD images actually viewed:20
heroes' percentages advance. DVa is existing pilot/pistol with entire original
HUD missing; strict compositor restoration/original-native.png proves original
client also lacks that HUD. Its float meter naturally reached400/400 in78.60s,
held cap3s; this does not prove Mech lifecycle or visible DVa HUD fixed.
four-worlds passed12 actual same-pawn samples:Pharah/Mercy/DVa each Overworld/
Nether/End/Twilight, actual scope, charge retained, resumed~5points/s/cleanup.
Symmetra full-meter PASSED:8->1000/1000 in198.49s idle, original full-ready
glow actually viewed,3s cap held,noQ/F11/damage/grants. DVa original-HUD gap
remains separate. Final main-world Pharah selection preview/no confirmation,
creative flight off/fixtures cleaned/independent backend retained. Final exact
identity/hash/module/restore evidence:all-hero-charge-20261023/final-audit.json.

All source tests and meter growth are separate from full21 ultimate gameplay.
Existing skill implementations/voices/light/Genji and McCree remain retained.
Old TIMER/shutdown crash roots and intermittent Tracer fists remain open.

## 2026-10-23 09:58 - final ordinary restart and independent picker

Current native16304(created09:53:20)/MC27704, independent supervisor25776/24080.
Actual6 unique mapped owners: bootstrap10/localhero1/compositor40/body25/gate9/
emission15; hashes and process creation times are in
research/four-dps-20261023/final-audit.json. Current actual guest remains
e75de8368a52cf1681db6df52f919261892eed68ce346b83de727c8e9f3aa190.
17876/17452 were deliberately normally restored/stopped; all4 mutable owners
verified strict restoration, including separate input/light/FPS restore.

Clean main world, MC20HP/alive, no lab target/wall, ALLparticles,1080p/Low/
8chunks/no shaders/day-night cycle retained. Final picker-preview.mkv and both
extracted images were actually viewed: original Genji animated preview and
MC main-world village/portal background, no confirmation into gameplay. An
unselected initial picker capture is separate and does not prove hero animation.
ready=false/phase=hero-selection is EXPECTED here; independent supervisor waits
for the player's confirmation. It does not need the chat to own the controls.

Final acceptance: FOUR-DPS-RESULTS.md. All4 normal-damage-earned Q rows,16
first-shot switches, all5 mid-skill portal interruptions and final Blink collision
are accepted with evidence. Shadow focus before AND after real warp passed on
the new build; no duplicate warp, native End and guns recover. No current matched
error report is an observation, NOT proof either original crash root is fixed.
Remaining original parity and intermittent Tracer fists are explicitly open.
Stop new development at the agreed today10:00; leave both games/backend available.

## 2026-10-23 09:44 - Shadow focus recovery and earned Q acceptance

Current native17876(created09:40:54)/MC17452(created09:40:37), independent
supervisor23844/24032, same6 owners/body25. Guest is now
`e75de8368a52cf1681db6df52f919261892eed68ce346b83de727c8e9f3aa190`.
28368/25768 were deliberately strictly restored/stopped, not crashes.
Read FOUR-DPS-RESULTS.md for this run's accepted increments and limits.

All4 earned-Q hero rows actually passed: Reaper154.000001MCdamage/cost1500,
Tracer83.600002/900, Soldier76 135.3/1500, Pharah160/1500. NoF11/direct meter
or direct damage. Q/debit/nativeEnd/post-primary passed. Aggregated evidence:
research/four-dps-20261023/earned-ultimates-accepted.json. v1/v3 suite failures
remain failures; only individually accepted hero rows are aggregated.

shadow-focus-v1 reproduced locked native guns after actual MC foreground:
departure admitted, scope suspension erased MC pending/receipt, zero warp,
native shadowCompleted0. New MC terminal retention cancels gameplay but retains
only that exact cast's phase2/3 cleanup. Different world/model/source drops it;
server stop/test clear erases it. Native still waits actual departure End and
actual arrival End. No new native callback/DLL. shadow-focus-after-v2 PASSED:
MC foreground17452, no stale teleport, one cancellation/native cleanup, real
post-primary20->5.999999, cleaned.48 Gradle tasks/proper HTTP entry passed.
Latest mid-skill-world-shadow-terminal-v4 PASSED/cleaned all5 actual portal
interruptions on this new build. Blink-collision-final PASSED/cleaned native
3->2->1->0/recharge/empty refusal/7.48m open/real wall stop; actual gun pixels
inspected. shadow-focus-after-move-v3 also PASSED: after actual warp, real MC
foreground, exactly one move, original End/post-guns/no replay. Final ordinary
restart and picker inventory follow before10:00.

Before this Shadow patch, mid-skill-world-recall-terminal-v3 PASSED all5 actual
Recall/Shadow/Wraith/Blossom/Pulse portal interruptions on28368, including no
old Recall heal/ammo and post-world guns. Do not reuse it as the new build pass.

Open: native23196 became unarmed Tracer (original native pixels showed fists,
no original factories despite fresh combat binding). Normal restoration/slot
keys/fresh hero recreation did not recover that process; cold native28368 did.
Single PulseQ and ReaperQ->Tracer both passed on28368; entitySlot1f=0 before/
after. No trigger/root fix proved. See tracer-slot-diagnosis. Do not label it a
compositor defect or blame user input. TIMER pool and supplied shutdown ABI
roots remain open. Backups/failed evidence retained; no SFX prototype deployed.

## 2026-10-23 08:52 - current Recall focus/terminal recovery and four-world gates

Current native23196(created08:37:37)/MC25768, same6 native owners including
body25; guest8385781552e4f931b2dfb73b5573d6ae29ab37825e4cf154c46a9a29cbcc8db2.
13304 was deliberately strictly restored/stopped normally, not a crash. Current
session-status/executable/module inventory remains the authority for identities.

Four-DPS switch-four-worlds-v5-owner-guard PASSED/cleaned all16 real first shots
900ms after picker confirmation, actual damage/no replay/full nativeHP/current
camera-relative light/ALLparticles. Actual16-image contact sheet inspected. Prior
v4 also passed after generic-primary priority + bounded exact Biotic lookup.
New producer-owner prefix guard defers transport until MC's current model agrees,
without extending500ms projectile freshness;48 Gradle tasks/51 supervisor/8 map
fixtures and proper HTTP entry point passed. Older failedv1/v2/v3 stay failures.
Death Blossom blossom-four-worlds PASSED/cleaned all4 actual60ticks/3s/cover/End/
post-primary. Reaper-cooldowns-v1 PASSED Wraith8s AFTER End, refused early press,
actual reuse after0; invalid Shadow click/no warp/RMB cancel/no CD/post-primary.

New actual defect recall-focus-before reproduced locked guns after admitted E
and real MC-window focus. Original root31 ended, but MC discarded its pending
End and native history1 never completed. Recall now requires focus only for
admission; actual fresh same-owner cast End can finish in background. A server
scope reset preserves only that exact old cast's terminal cancel disposition.
Unknown scope cannot rewind/heal; a definite different pawn/world/source drops
the receipt. Fresh original End + exact current scope can retry a terminal ACK
without executing another MC heal/warp; native body still independently matches
its exact awaiting begin. No native DLL/callback/thread ownership change.

recall-focus-after-v2 PASSED/cleaned: real MC foreground,2->20HP,32->40ammo,
one original history completion and real post-return primary. First after test
measured the same outcomes but had a misplaced passed flag; retained as failed
harness, not rewritten. recall-io-after-v4 PASSED/cleaned with3.006s exclusive
file lock/48 genuine Java IO-retry observations, one terminal recovery and actual
primary/no duplicate MC completion or native ammo adapter call. Earlier IO
harnesses wrongly required an extra adapter write even when original ammo was
already40, and required healing even when an observed scope interruption safely
cancelled the effect. Their failures/data remain separate, not relabeled passes.
Cancellation guarantees no extra MC heal/warp or adapter ammo refill; original
native animation may independently change its magazine. Minimize attempt failed
its IsIconic setup check (input driver still active), not a feature acceptance.

Current actual earned-ultimates-v1 is running: all4 Q charged through ordinary
real native gun damage, no F11/meter grant, then real activation/debit/End/guns.
Next: finish this, repeat mid-skill portal cancellation with new Recall code,
Blink collision/current Pharah feedback, and final runtime/strict-restoration
check before today10:00. Full weapon headshot/falloff/cinematic parity and both
native crash roots remain unproved. No extra SFX prototype was deployed: prior
native-only Wraith/arrival captures already correlate with pinned reference SFX;
that reference does not authenticate the original recording date.

## 2026-10-23 08:04 - Helix visible transport and focused regressions

Current native19684/MC8848 cold-loaded body25 and guest
8e9bbb8bb9be7757cc926bca3746a9b3ffb46ec7079294f0c88d55e44f4dbe80.
Six native owners unchanged from07:22/body25;4832 was deliberately strictly
restored/stopped, not a crash. Current actual session-status/hash supersedes IDs.
Read NATIVE-SOLDIER-HELIX.md. Actual helix-live-v1 PASSED/cleaned: one native
factory/one12MC damage blast,20->8, three cosmetic strands, cooldown retry inert,
real cover20, replay inert, post-skill rifle. Actual contact sheet inspected.
48 Gradle tasks passed. MC model is authored here, not an original export.

Actual Soldier Sprint5.5->8.25m/s passed. Native Visor natural/damage charge,
acquisition/occlusion/End/drain/ordinary-fire regression passed on19684; actual
private original Mandarin Q found in MC process audio correlation.634859.
Actual Pharah held-Space response passed3 pulses:88.4/45.6/75.6ms,7.90195m/s,
no creative flight;3 actual primary shots/3 flashes and no replay. Prior4832
open/ceiling/Shift/fuel depletion-recovery passed; first open harness failed only
saving its result due a shadowed output variable, and was rerun successfully.

Actual picker clip was320,180,2240,1260 inside a2560x1440 native client, clamping
confirm y1358 to1259. Which process last constrained it is unproved. New Python
supervisor repair releases only a fresh verified native viewMode2, its exact
foreground HWND, visible cursor, no mouse drag, strict contained centered clip.
No hooks/focus change/gameplay release. Actual automatic picker release and
refused gameplay release passed;3 policy/49 supervisor fixtures passed. Same
4832 was adopted by refreshing only the supervisor; no new callback owners.

Reaper shadow-io-after PASSED genuine~.87s exclusive receipt-file contention,
30 FileSystemException observations, actual blocked destination/no warp and
post-cancel real guns. Same-scope terminal disposition is retried, never a warp.
blossom-movement-after passed2.75m/s Q and5.5m/s after; separate cleanup proof
confirms cleaned=true. Actual MC Mandarin Q correlation.746977. Focus-loss-v2
passed held W with exact MC foreground and0 movement; first focus harness failed
to acquire foreground, not a movement-feature pass. Soul-core-v2, all4 Shadow/
Wraith worlds and all5 mid-skill portals passed; read NATIVE-REAPER-KIT.md.

Four-DPS first-shot/light regression v1 failed an invalid setup: a native equip
resets view to180/0, whereas the fixture target was placed on the previous
0/-25 ray. Actual rocket was admitted along180/0; not evidence of lost damage.
Corrected v2 is running. Full4 kits/cosmetic parity/falloff/headshots and crash
roots are not certified by these increments. Deadline remains today10:00.

## 2026-10-23 07:15 - five mid-skill portals passed; actual cancellation IO gap fixed candidate

Actual1960/body25 mid-skill-world-v2 PASSED/cleaned all5: Recall, Shadow Step,
Wraith, Death Blossom and Pulse Bomb mid-cast portals. Old MC effects cancelled,
no old Shadow warp, Recall magazine32 stayed32/no old-world heal, actual fresh
primary after each. shadowCancelledAim now recovers the pre-receipt portal race.
Read NATIVE-REAPER-KIT; native25 hash941bf7a6232e9cb9dead9b8ef7c6a04c6ea52eb42786c372bd4742b32a2b25c4.

Actual shadow-io-before-v2 intentionally held this PID's ack file exclusively
for~.87s and placed real reversible blocks at the admitted destination.28 genuine
FileSystemException sharing failures, MC cancel/no warp, but native completion
was lost because terminal receipt wall time expired. Feature FAILED/reproduced,
not a pass. First IO harness wrongly counted only AccessDenied and failed its
assertion despite actual FileSystemException rows; retained separately.
New MC source refreshes only same-live-scope finished/cancelled dispositions for
transport retries; it cannot re-admit a warp (only phase1 does that), nor move
without a pending MC record. Actual corrected IO retest pending.

Actual blossom-movement-before: original effective limits2.75 but MC distance0
while W was held during Q. Generic pose input is intentionally first-person,
whereas Q selects cinematic camera. New candidate uses current admitted Q plus
exact foreground HWND/PID and hidden cursor for read-only WASD, at original
computed limits, with no hook/new callback owner/synthetic input. Needs actual
movement/focus-loss/end tests. Source47 Gradle tasks passed; final optimized
candidate is building. Native1960 strictly restored/stopped normally. Next
launcher will cold-load same native25 plus new guest; verify actual IDs/hashes.
Full4 kits/weapon parity and crash roots remain open; no idle-stability claim.

## 2026-10-23 07:04 - actual Shadow/Soul passes; portal race found and candidate25

body24 Shadow first pass and shadow-four-dimensions-v1 PASSED/cleaned in all4
worlds. Original clips/real warp/0.01m landing/post-E damage; actual Mandarin
arrival in MC process mix correlated.802212. Soul-core-v2 PASSED actual kill,
one globe/no replay, walking pickup2->7HP/5healed and cleanup; actual contact
sheet viewed. v1 soul preflight failed because the test assumed Overworld while
actually in Twilight, not a skill pass. Injury-preserving world regression
injured-world-v1 PASSED for Tracer/Reaper/76/Pharah: same-pawn2HP carried across
worlds, current scope/HP alive, actual guns. It does not prove every mid-skill.

mid-skill-world-v1: Recall mid-E portal PASSED (no old rewind/heal/ammo reset,
32magazine remains32; fresh post-world primary). Shadow mid-confirm portal
FAILED actual target20HP. MC had admitted the target, but the world changed
BEFORE body received the file receipt. Native shadowAdmissionCalls stayed4
while MC starts advanced5; original query/selector still caught the next click
(refused increment), so this is an actual pre-admission cancellation bug.

New body25 candidate tracks the current MC world even without a pending native
admission; world change with an active unadmitted original query ends current
priority16 and starts original ready5. It grants no old-world warp/MC effect.
941bf7a6232e9cb9dead9b8ef7c6a04c6ea52eb42786c372bd4742b32a2b25c4.
14 C++ fixtures include this exact no-receipt portal case. Actual retest pending.
Old26888(body24) strictly restored/stopped normally; no crash claimed.
New guest has a reversible actual Shadow destination obstruction fixture for
real collision/IO-cancellation testing. Native23/24 failures retained. Obtain
current PIDs/loaded hashes, not these historical IDs. Full4 kits/crash roots open.

## 2026-10-23 06:39 - Reaper Wraith actual four worlds passed; Shadow candidate

New accepted Wraith body22: cbe392b3dd70607b9330c6cb06daeea8e3f4b82473a6adf3d6ae96f69f04ea68.
research/reaper-kit-20261023/wraith-core-v5 and wraith-four-dimensions-v1 PASSED
and cleaned in all4 dimensions: real damage18->18 during immunity,18->16 after,
5.5->6.875 native speed, blocked guns during cast, actual post-End damage.
Original state2 starts original Wait4/physical1/5; root20 closes only after BOTH
Anim3 and Wait4 actual End. Early20/21 root completion FAILED real gun recovery.
No legacy lab flags or second callback owner. Native22/MC were strictly stopped
normally after actual tests; original contact sheet viewed. Read NATIVE-REAPER-KIT.

Current launch supervisor-shadow1.* uses body23/private first Shadow candidate.
Actual17200 is a historical identity once stopped; verify process before action.
shadow-core-v1 FAILED: valid MC ground/actual confirm, native query2 End, but no
original departure animation and no real warp. No success claim. New24 candidate
isolates original departure25/arrival26 around real MC transport, leaves native
E priority16 until End, and uses provided typed ExecuteNode60 for original10s
cooldown. Full original server coordinate-warp subtree must NOT be executed with
missing OW-map target outputs. The callback remains on the existing logic owner.
New MC Soul Globes (official2016 50HP pickup;15s/1.5m explicit MC policy) candidate
compiled but not accepted/deployed yet. Full4-hero kit and crash roots still open.

## 2026-10-23 06:10 - Tracer accepted core, Reaper Q accepted, Wraith candidate

Deadline remains today10:00 Asia/Shanghai, per clarified request. Tracer body19
actual recall-sixth, recall-repeat and four-dimensions-v1 PASSED: real3-second
MC history/health/ammo restoration, both native End stages, two Blink, sticky
bomb/fuse/cover/no next-Q credit and post-skill guns in all4 worlds. Read
NATIVE-TRACER-KIT.md. Once-per-pawn health now excludes same-pawn dimension
changes; low-health portal regression pending (old cleanup masked the injury).

Reaper blossom-core-v1/v2 FAILED and remain evidence. v3 PASSED60 actual MC
ticks/3s,200->148.99963 near/behind, covered/outside200, one Begin/End, no
replay, Q debit and post-Q actual primary. Runtime8868/body19; contact sheet
viewed. Original cinematic disables input in its Begin frame: guarded150ms
preceding same-scope gameplay admits that real cast, then exact continuation.
Private explicitly tagged Mandarin ally Q played once; mixed-audio correlation
pending. Incomplete single-word recordings were NOT deployed as full Q.

body20 adds clean original Wraith root20 completion after actual Anim3 End,
within the same existing logic owner. Old lifetime/authority lab flags stayOFF.
MC candidate uses native phase for immunity/early25% speed/smoke; actual tests
pending. body20 hash6beb19ccf2f3672ddaac8e059688ab230261ca23308ab9404c414130752b2702.
First body20 launch22412 failed version verification (report still19). Strict
restoration/stop passed; corrected/rebuilt cold. New launch logs
research/reaper-kit-20261023/supervisor-wraith2.*. Obtain actual current PID,
creation and modules. No second owner or mapped DLL swap. Pharah E/Q and76
field acceptance preserved. Full4 kits, Reaper Step/Orbs and crash roots open.

## 2026-10-23 — four-DPS work authorized and bounded heartbeat resumed

Latest05:13: actual17428 cold-loaded body19
b54c94dae41563bc6a4df29c75a1c73367a9998bd98eebd56bb093e837b7c8d2,
other5 DLLs unchanged. After a metadata-declaration preflight failure, only the
exact independent supervisor was refreshed (same games/6 owners); logs end in
supervisor-recall4-refresh. Actual recall-sixth passed4.2m rewind/0.0m error,
2→20HP, original30→40 ammo via guarded native Set&Notify, real post-E target
20→13.999996, both original End stages and cleanup. Same-model repeat and four
dimensions are running next. Keep earlier16/17 failures, third fixture failure
and fourth missing-ammo failure separate. Do not call all Tracer kit accepted.
Read NATIVE-TRACER-KIT.md and research/tracer-kit-20261023. Old Reaper flagsOFF.

Latest04:52: read NATIVE-TRACER-KIT.md. Actual native12668 is cold-running new
body17(e919c0406d66495468304dd8d8f22bb57d9fc6175b235af5ac7ad056fc471516)
and guest5f9e09de0cf3f09dbf86397bc6d53a4fa9924c516b3138299eda628a7346ffb3.
Other5 native DLL versions unchanged; no overlay owner. Strict stop of14976
passed. New launcher logs research/tracer-kit-20261023/supervisor-recall2.*.
body16 Recall attempt actually rewound4.2m but FAILED post-E fire; actual graph
links then proved root31 owns history4/animation9/Stack27.17 candidate follows
Anim9 End to close that exact root, not the Stack27 leaf. Actual second test
is running, not accepted. Old Reaper experiment flag remainsOFF.46 Gradle,
11 C++ body fixtures,48 supervisor and proper HTTP test passed.

New76 field four-dimension actual healing/expiry/world-interruption passed on
23456; proper separate injured-hero interruption also passed. v4 final harness
failure was a wrong generic-meter wait for Genji, preserved as failure. Mixed
Mandarin E audio correlation .8919; correct MC puck/ring contact sheet viewed.
Native21640/23456 were intentional strict restoration stops, not crashes.
Pulse Bomb first native21640 test passed actual throw/stick/delayed kill but
exposed inappropriate next-Q credit. Current5f9e source removes that credit and
adds two private Mandarin throw variants; corrected charge/audio need real test.
Reaper/complete4-hero kits still unfinished; do not claim this sprint complete.

Latest04:12: native31364 actually CRASHED (exit0, matching report) at825346
after2:43, distinct from oldd1428b. Read NATIVE-TIMER-CRASH.md new section and
research/biotic-field-20261023/crash31364. Four-dimensions-v3 has only2 passing
rows, not complete. Exact reporters closed without sending. A normal recovery
launcher is starting unchanged4dc8bed4 guest and6 native owners, logs
research/biotic-field-20261023/supervisor-recovery1.*. Verify new IDs, cleanup and
read actual native825346 code before deciding cause. Do not blame focus/user/GPU.

Latest04:05: read new NATIVE-BIOTIC-FIELD.md section. Candidate4dc8bed4... (45
Gradle tasks/47 supervisor/proper HTTP checks) cold-starting after strict stop of
19520. Six native DLL versions unchanged. New field core-v2 actually passed,
four-dimensions-v2 passed individual4 worlds + world cancellation but FAILED
injured-hero cancellation because full-health prerequisite blocked new owner
initialization. New once-per-confirmed-native-pawn creative health init fixes
that candidate path; not yet game-tested. Quads fix/3 random Mandarin E clips/
Mandarin Visor/scoped private field loop also await final live acceptance.
Current launcher logs research/biotic-field-20261023/supervisor-final.*. Check
real new identities; older native19520/21628/15200/28852 are now stopped.

Latest execution checkpoint03:32: actual Pharah b0e9c44e tests passed
research/pharah-live-20261023/e-primary-v3 (idle5.04pt/s, real primary/earned
135credit,18.53m enemy E push, terrain/protected blocks/splash/replay/cleanup)
and barrage-four-dimensions (each real90-shot cover/open/End/debit/fresh primary).
Native E/primary contact sheets were actually viewed. MC process audio recorded
through the actively rendering OW window; initial coarse vanilla-explosion
correlation .4125 is below its acceptance threshold and not claimed audio pass.
Initial dimension-assumption and hidden-MC-capture failures are preserved.

Read NATIVE-BIOTIC-FIELD.md new section. Built59bb0ba49d78e8d4e3b09ff96ace3f49350500db2c306509528dbba76ddf622a
adds original-cast/Volley to MC healing-field compatibility adapter,44 Gradle and
45 supervisor + proper HTTP checks passed. Chinese E/original field loop pending.
Old28852/10580 strictly restored/stopped, MC saved. Normal independent launcher
is cold-starting the new guest; actual new PID/module/profile audit and healing
tests still required. No native DLL changed or second owner installed.

Read FOUR-DPS-SPRINT.md. User approved starting the expanded Pharah/Reaper/
Soldier76/Tracer full-kit work unattended, through the previously confirmed
October23 10:00 Asia/Shanghai deadline. Existing mc heartbeat is ACTIVE with
an end bound and a clock/checkpoint/stop guard. No new thread or callback owner.
Reaper's full new route is in scope; old quarantined flags remain OFF. Preserve
successful gameplay fixes and actual version distinctions. Begin with the
already deployed Pharah regression's real tests, then76 field/Tracer/Reaper.
Current rechecked native28852/creation134371684133462617 and MC10580 have the
b0e9c44e guest and original6 owners, still at native picker before test inputs.
Those identities are observations, not reusable permissions or test acceptance.

## 2026-10-23 — authorized deployment/live Pharah regression in progress

The user's latest explicit instruction is to apply the changes and complete
in-game tests; this lifts the older code-only constraint below for this work.
No game/native owner/supervisor was running at preflight. The all-zero old
session-status file is preserved under research/pharah-live-20261023; its cause
is unknown. World level.dat/level.dat_old decompress correctly. Complete cold
profile backup: ~/.universal-modder/backups/pharah-live-profile-20261023/
20261023-024223.zip. Normal launcher is starting built guest b0e9c44e... with the
existing six native owners/settings. This is in progress, not live acceptance.

## 2026-10-22 — Pharah explosion / charge / E code repair (latest)

Read [PHARAH-REGRESSION.md](PHARAH-REGRESSION.md). User constraint remains
**code only while using the PC**. No restart/focus/input/deployment was performed.
Subsequent live native13744/creation134371425293318036 was observed read-only,
with six unique unchanged bootstrap10/localhero1/compositor40/body15/gate9/emission15
modules. Installed/running guest remains
fe2924bdf567b07905eb1c937f6e8bdef3bcec33b5edd3aeee5eb789274767ca.
Earlier no-games audit below is historical; always recheck actual current PID.

Built source guest is now
b0e9c44ef6797fbe83b47cf16fdbd769e0ef6f43804f77ce5d693268229da4ae.
It is not installed/game-tested. Private research/pharah-regression-20261022/
code-final-audit.json pins source/profile/mapped hashes and old live observations.
Do not mistake old live counters for acceptance of this new code.

Primary rockets call the actual ServerWorld overload sending ExplosionS2CPacket;
the previous extra-boolean overload bypassed it and selected smoke. Normal MC
burst/audio restored in code; damage/terrain guards and separate Barrage remain.
ASM check follows actual MC dependency's packet-producing descriptor and caller.
Charge now accepts fresh equivalent tick publications and keeps same-session
credit over meter failure; active/unknown/full/reset/freshness guards remain.
Existing5pt/s policy/native cost/Genji/76/body15 ownership is preserved.

E excludes ordinary hurt knockback from its radial vector and selects exposed
multipart victims once. Terrain reads remain loaded/bounded. Existing custom
1.5x enemy/.5MC HP and self impulse remain, not certified original OW physics.
Inspected official E footage guides the MC-made round orb/violet pressure shell;
real impacts only, scoped model/source/world/replay/expiry guards. Full original
model/effect/physics parity remains uncertified. Particle setting remains ALL.

Final43-task build, proper Java-backed HTTP contract and new charge/actual-MC-
transport/burst lifecycle checks passed; headless only. Next permitted live run
must verify burst/audio, timed idle/damage/Q charge, E cover/parts/push, four-
dimension recreation/replay, cleanup and all restoration gates. Preserve all
existing movement, combat feedback, McCree/Genji/76/Pharah and voice fixes.
No new native owner/DLL, hot overwrite, publication or unrelated commit.

## 2026-10-22 — all-hero walking / background cursor; code-only handoff (latest)

**Latest human constraint: the user is using this PC; only edit code. Do not
launch/restart games, focus windows or send game input while this constraint is
in force.** At the final read-only audit, no exact project native game, MC guest
or session supervisor was running. Do not treat an older PID below as live.
Read [HERO-MOVEMENT.md](HERO-MOVEMENT.md). Current evidence is
research/all-hero-locomotion-20261022/code-final-audit.json, not a new live
final-audit.json; the last full suite remains failed/incomplete.

Latest built source guest SHA256:
fe2924bdf567b07905eb1c937f6e8bdef3bcec33b5edd3aeee5eb789274767ca.
The installed profile remains the previous cursor candidate
96f7ec3e67b8122b5f3eb2e0279cd9cbe709be8aa59835185141338d51a27eff;
no profile JAR was replaced after the code-only reply. The existing normal
launcher copies the built guest on a later permitted launch. All six native
DLLs remain byte-identical to the preceding combat-feedback delivery:
bootstrap10/localhero1/compositor40/body15/gate9/emission15. No native owner
was added, rebuilt or overwritten. Check actual identities/hashes again then.

Two reproduced faults are fixed in the guest route: five old motor heroes kept
their old direction for5–7 MC ticks after reversal, and native body animation
received friction-damped velocity (~2.33m/s despite actual5.5–6m/s movement).
Schema2 binds both reflected BASE speeds and current native component15's six
COMPUTED directional limits. All ordinary heroes use current input direction
and those real scope/sprint/root limits; old cumulative native motor displacement
is no longer normal walking authority. MC remains collision/gravity authority.
BodyMotionSample exports actual completed tick displacement for original animation,
with zero/baseline on collision, release, source/model/world change or teleport.
Pharah real flight, Tracer Blink, Genji climb/double jump and custom F6 stay separate.

Latest code-only addition uses at most3 coherent speed-read attempts and verifies
the current native identity before/after them. A changing modifier suppresses
movement for that tick without fabricating a hero0/session reset. Real owner/model
changes still revoke old scope. Actual Win64 self-process fixtures cover both
paths; full39-task guest build, proper Java-backed HTTP contract and environment
checks passed. This last revision has **not** been tested in game.

Actual native12508/MC4728, guest4c4736ef... passed final-all21:21 heroes' base
direction/release/strafe/ground/body-speed checks and20 ordinary jumps; Pharah's
native hover/primary has separate passing acceptance. Original21 first-person
hands/weapons contact sheet was actually viewed. Native scope/sprint/draw/root
modifier checks passed. Actual Bastion Sentry's previously reproduced1.2522m jump
is now0, F6 refusal passed, Mei root passed; same-model jump recovery remains
untested. These are base movement/model observations, not full21 kits/forms.
D.Va is still the real pilot/pistol; Mech spawn/ejection/recall remains unfinished.

The following failed Nether selection reproduced background MC lockCursor clipping
the foreground OW picker to the MC client rectangle. New HostMouseCaptureMixin
permits MC capture only when MC's actual Win32 HWND is foreground. It neither
hooks native input nor writes global ClipCursor. Actual native25864/cursor96f
passed Nether/End/Twilight picker transfers and Genji/McCree reselection. Fourth
Overworld selection/focus failed during PC use. The suite did not reach the final
all21 or world/attack matrix; do not promote its3 passing rows into a full pass.
MC foreground cursor behavior still needs deliberate live acceptance.

Native25864 later exited0, classified process-exit-unclassified, with no matching
error report found; the supervisor stopped MC. The user confirmed using the PC,
not explicitly closing games. Its cause is unproven. Do not label this a proven
manual/normal stop, crash-free run, or a timer-root-cause fix. Actual strict normal
stops26572/8204/12508 did confirm all restoration gates; keep them distinct.
Historical TIMER and825346 issues remain unproven. Failed/interfered tests and
exit evidence are retained. Cleanup of the interrupted last live suite was not
accepted; before further live work reset the reversible lab fixture and audit it.

Next permitted live run: final-build21/world movement and attack matrix; rooted
jump release; MC foreground capture; speed-reader transition/session stability;
actual pixels and strict cleanup/restoration. Preserve all existing Chinese voices,
combat feedback, McCree/76/Pharah/Genji fixes and Hollywood1080pLow/8chunks/no
shaders/day-night/particlesALL. Do not revive quarantined Reaper experiments.

## 2026-10-22 — classic combat feedback and Deadeye crowd fix (latest)

Read [COMBAT-FEEDBACK.md](COMBAT-FEEDBACK.md) first. Current actual native26572,
creationFILETIME134371359676399473; MC20808; independent supervisor11732. Six
unique verified modules: bootstrap10/localhero1/compositor40/body15/gate9/emission15.
Guest source/profile SHA256a0b3b308e4a59f14be8addf4b1e02ab0b7e9100727f7de9d72f501f7d2c5a41f;
body15 SHA2566631271a4e3247aa31f68b56a5d43c165502b9d196430ac40a74ab4cc5ed5cd4.
The final-audit under research/combat-feedback-20261022 verifies module paths and
hashes, matching source/profile JAR, advancing native/source frames157/71 over a
bounded.7s observation, and no matching current error report. This is not a minimum
FPS or crash-root-cause acceptance. Native TIMER and startup825346 causes remain
unproven. Earlier PIDs below are historical, not current deployment evidence.

Actual original animated McCree picker over daytime MC terrain was viewed.
Player grounded65/full20HP/not flying/particlesALL; no fixture blocks, pending
shots, old sound tails or Q jump lock. Both games stay open with the independent
supervisor. Original Hollywood/1080pLow/8chunks/no shaders/day-night and existing
Chinese voices,76Visor, Genji particles, F9/F10/F11 remain. Hanzo is paused.

Deadeye's three separate six-shot limits now consistently allow a bounded64-target
volley. Body15 changes only the selected presentation request's ordinal admission;
it keeps body14's single original logic owner/Wait72 cadence/ack/freshness guards.
No extra owner or loaded DLL overwrite. Lethal skull forecasting includes actual
vanilla armor/toughness/Resistance/Protection/absorption. Filled red skulls/rings
and per-lethal-shot MC red droplets are adapters, not exported original OW assets.
Grounded and creative Space/F6 suppression follows fresh actual native Q and
releases afterward. Flashbang gets stronger detonation visuals without changing
the user's2-second visible50%-slow mechanics. All admitted heroes share actual
MC damage/death hit/kill audio receipts, with expiry/deduplication/session reset.
Private classic recordings are hash-pinned outside source; exact earliest OW1
sound-bank provenance remains unverified. Do not silently call them Beta exports.

live4 and four-dimensions-v3 actually passed12 ready armored/absorbing targets,
12 original animation shots and12 separate deaths, replay, native charge/End,
flash/potion, ordinary attack, health and light after hero recreation in Overworld,
Nether, End and Twilight Forest. Actual skull/night-blood frames were inspected.
ground-audio passed actual grounded Q no-jump, ordinary jump recovery and isolated
hit/kill mixed-audio identification at48kHz (.83782/.93484). shared-heroes passed
Genji and76 actual nonlethal/kill/replay, supplementing McCree/Pharah; do not claim
all21 complete kits were play-tested. mid-sequence passed actual world/H-picker
cancellation, no further old shots/bursts/sounds after settlement and primary
recovery. Hero interruption admitted one additional shot before selection settled;
do not misreport an immediate keypress-time cancellation or exactly one shot.

Pharah-live2 passed stronger enemy E impulse (user custom1.5x, at most5OW-equivalent
HP), unchanged self displacement2.656m, replay, two original primary rockets,
real hit/kill feedback, original private mesh/muzzle, terrain destruction and
protected blocks. Actual flame/impact sequence viewed. The implementation retains
retail154088 private mesh/sprites, not a successful154504 extraction; exact full
original effect graph and original OW knockback physics remain uncertified.

Keep failed evidence: live1/live2, initial interfering pharah-live1, overlapping
mix/16kHz audio thresholds, and first two four-dimension harness failures. The
first had31 nearby real mobs and an obsolete<=6-shot assertion; v2 fired with only
11/12 lethal markers and its armored/absorbing target survived correctly. Passing
v3 isolates the air corridor and waits for12 ready targets. Never relabel failures.

Strict stop744 encountered a final-report rename race: actual final tmp and
read-only memory proved all releases, while main JSON stayed intermediate. New
stop recovery is pinned exclusively to compositor40's mapped binary hash and
actual finished/inactive/released-state, original user32 prologues/light/frame
bytes, plus a fresh unchanged complete tmp. It does not accept intermediate JSON.
Actual744 strict restoration/save/exit passed;22 restoration and3 stop fixtures
pass. Body15 recovery has its build pin. Final guest build38 tasks, native64-shot
request fixture, private pack installer and proper HTTP contract passed. Backups,
full success/failure records and final actual audit are in the research folder.

## 2026-10-22 — independent Pharah Barrage presentation (latest)

**Current delivery:** native25412, creationFILETIME134371140459941079; actual
MC25960; independent supervisor17060. Guest source/profile SHA256
a3ec52c8464b3aab1eecb38d1675340b1f7158737b0f83860ecd0fcd68c07f7e.
Six unique native modules unchanged (emission15/compositor40/body14/gate9/
bootstrap10/localhero1). Actual original animated Pharah picker over nighttime
real MC Overworld was viewed. Player grounded65/full20HP/not flying, particlesALL,
no active shots or firing loop. 168native/56source frames advanced over.6s;
not a minimum-FPS claim. Hollywood/1080p/nativeLow/8chunks/no shaders/day-night
are retained. final-audit.json has exact current identity, hashes, actual state,
supervisor and no matching current report; old/crash PIDs below are historical.

Final a3ec52c8... passed final-four-dimensions (Overworld/Nether/End/Twilight,
real hero recreation, two90-shot volleys each, cover20/open0HP, one loop/End,
meter drain, replay, primary20->8/earned charge/full200HP) and final-mid-switch
(actual in-flight hero/world cancellation, no old sound/impact/damage, fresh
Pharah/McCree primary recovery). All fixtures cleaned. Wall-final native contact
and final picker actually viewed; loop/voice actual-audio acceptance is live3.
Earlier candidate four-dimensions/mid-switch-retry results are separate, and the
first mid-switch/no-F11 attempt remains failed. Do not promote an old mix failure
or diagnostic counter alone into visible or human play acceptance.

Read [PHARAH-BARRAGE.md](PHARAH-BARRAGE.md)'s NEW presentation pass first. Native
emission15/compositor40/body14 and the six DLL hashes remain unchanged; the guest
now owns an independent MC-made mini-rocket, curved pale ribbon, server-impact
orange sprites, and an actual-admission/native-firing-scoped private recorded
loop. Early Mandarin audio ducks that loop. No key creates a projectile/sound;
native90-shot Wave physics and real MC direct/splash/cover stay authoritative.
The mesh is not an original Barrage export, and the loop is a mixed original
gameplay recording adaptation, not a clean sound-bank stem. Full37-task build,
three installer tests and proper HTTP contract passed. Installed private files
are hash-checked; assets/audio stay outside source. No native DLL was rebuilt or
overwritten. Retain source/model/world reset and emission15 episode cancellation.

Evidence is research/pharah-barrage-art-20261022/. The previous delivery29400 had
a matching crash report with exit0 at RVA825346; its report/dump is preserved in
crash29400/. It is not the d1428b TIMER release address. The crash happened after
delivery; its cause is unproven, and this visual/audio pass does not repair it.
The supervisor correctly caught it and did not restart-loop/send the report.
Old live1/live2 audio audits and the first F11/no-flight interruption attempt
FAILED and remain preserved. Ducking live3 and covered-wall actual captures
passed; the original loop is audible in actual MC audio (correlation.94896),
with the preserved Mandarin callout identified at.42116. No human listening/play
acceptance or180FPS claim is made. Final dimensions/current process/cleanup and
supervisor evidence are finalized in final-audit.json and the entry below.

The old bili reference manifest is unreliable: P01 video=Pharah/P20=Winston,
P01 audio=McCree/P02 audio=Pharah. The official website clip is silent, so only
its visuals are used. Do not repeat the old paired-hero attribution or pretend
that its2016 upload date proves the earliest recording. The separate thnu-three
installed Chinese voice pack is unchanged. Normal stops23600/23496 actually
restored every owner (strict-stops.json); final owner identity is not either PID.

## 2026-10-22 — Pharah Barrage and interrupted-world ownership

Delivery audit: native29400 creationFILETIME134370780670347393, actual MC20936,
independent supervisor PID pair from final-audit.json. Six unique mapped modules
match selected hashes; guest06eba252... matches the private profile JAR. Actual
native/source frame advances84/27 over.6s, source particlesALL, player grounded
Overworld65/full20HP/not flying, no pending flight/fixture, no matching report
(bounded evidence only). Actually inspected delivery-picker_small.png: original
animated Pharah foreground over real daytime MC terrain. Left both games open at
the Pharah picker. ready:false/hero-selection is expected; native21424 is the
strictly restored/stopped tested identity, not the current process.

Read [PHARAH-BARRAGE.md](PHARAH-BARRAGE.md). Selected native owner is emission15,
compositor40/body14 unchanged. The former node2 Q gap now uses actual90 native
factories and resolved original Wave sampling, not guessed straight projectiles.
Native pure-arithmetic oracle:96 actual comparisons, max2.38419e-7. Visible scaled
private primary rocket mesh/flame sprites follow the same curved server path;
this is not a separately exported original Barrage mesh/full effect graph.

Emission14 candidates passed normal four-dimension cover/open/primary/charge but
FAILED mid-switch: the original channel continued emitting into a new MC world.
The failure stays in research/pharah-completion-20261022/mid-switch/. Emission15
pins the first actual factory0 to its original world/model/host/MC generation;
a scope mismatch cancels the episode until a fresh original factory0/tick, and
returning cannot revive it. Actual mid-switch-v15 world and hero interruption
passed, with no remaining flights/damage and fresh Pharah/McCree primary recovery.
Current-model/hero consumer validation also rejects departed-model journal rows.
Final four-dimensions-v15 actually passed on native21424:8 complete Qs/720
real factories, cover/open/replay/End/primary recovery and real ordinary-damage
charge. Native resources, rooted Q/recovery, primary terrain/protected blocks
and E/cooldown/non-damaging push also passed. normal-stop-v15 verifies all
restoration gates before the cold delivery. Use final-audit for the current
PID/creation/hashes;21424 is now a deliberately stopped tested identity.

Guest06eba252a2235658091a43024fccc725a62ec0ff61f297e02a0dfd238c3d9613.
Native emission15 hash502bf180e351d0e85d1c6b590dc6f7228a9e271c28efa7a6d89562139dbac701.
Never overwrite mapped DLLs. All actual intermediate stops strictly restored
owners/global/input/light/frame-limit and saved MC. Preserve classic Chinese
voices, McCree body14 acknowledgement/cadence,76Visor, Genji particles, E, F9/F10/
F11 and Hollywood1080p/Low/8chunks/no-shaders/day-night/particlesALL. Alternate
Pharah node7's third motion, original full Barrage effects/SFX/launch compartments,
E exact OW impulse and historical TIMER/startup crash roots remain uncertified.


## 2026-10-22 — Deadeye timing/presentation and Pharah E acceptance

**Delivery audit completed:** native27352 creationFILETIME134370741077395001,
actual MC5224, independent supervisor1640/25816. final-audit.json verifies six
unique selected modules and matching manifest hashes, advancing composed frames,
no current matching error report (bounded evidence only), particlesALL, no lab
objects/pending shots, and grade cleared. Actual screenshot was inspected:
animated native McCree picker over the real daytime MC village, Overworld player
grounded/full health; both games stay open. `ready:false/hero-selection` is the
expected supervised picker state, not an assertion of gameplay failure.
Body14 itself passed final-four-dimensions-v14, mid-sequence-v14, fault recovery
and pharah-e-v14 before the strictly verified29540 shutdown and this cold launch.

Read DEADEYE-PARITY.md and PHARAH-CONCUSSIVE.md first, then the older timer/voice
notes below. Selected owners are compositor40, body14 and emission13, plus the
unchanged bootstrap10/localhero1/gate9. Body14 SHA256
7e4c57e491d557c71501000c4ea41407fe973ffb07a277399bb8825ef49323f3;
emission13 SHA2560bbcf58b6b38d03e8164a6fa3352e96cc03c66ef15e3e656ad991ae1aeb7cd70;
guest SHA25649ac34c2a9eba76d88aff5fdbf97e00b4e84c4e30ff2f8e414ed0117b8a75f42.
Native source SHA guard remains f73a747b...08e9f. Never overwrite mapped DLLs or
select body12 merely because historical accepted runs below used it.

McCree original graph022f has a.1333000064s target-loop Wait72, distinct from the
.33s animation69 envelope. The adapter now queues each target after its own
fresh original Begin; the original logic thread alone restarts69/alias019f at
>=134ms wall spacing. Normal actual native timestamps are128/144ms because of
16ms clock quantization. Each shot still releases its own MC damage. Sepia is a
GPU pass only on the exported MC background; private shot audio is an actual
recorded beta primary revolver, not a certified unique Deadeye asset. Original
postshader/full vignette/target ordering/aim rotation/full muzzle chain remain
uncertified. All21 selection callouts, Mandarin Q/E, Genji randomized Q and white
animation-synchronous sword cosmetics remain; no private audio is in the JAR.

Body13 passed normal four-dimension play but FAILED650ms request-file contention:
second Begin was overwritten by End before MC saw it. Do not restore that failed
version. Body14/request2 adds an explicit acknowledged-sequence tail to the168B
request; ack remains88B. Preserve Begin until MC confirms it, never refresh its
damage wall time, and bound absent acknowledgement to1s cancellation. This uses
the same existing logic owner, no second callback or arbitrary timer discard.

Actual native29540/MC29004 passed final-four-dimensions-v14, mid-sequence-v14
(world and H-picker interruption each stopped after precisely one new shot),
transport-contention-v2 (650ms/37 IO failures/four separate20HP deaths/no replay/
normal recovery), and pharah-e-v14. Then29540 was deliberately normally stopped:
normal-stop-v14 verifies body14, gate9, emission13 and compositor40 restoration,
including individual input/light/frame-limit releases. It did NOT crash.
Current delivery process identity/modules/creation/hashes/screenshot must be
read from research/mccree-deadeye-parity-20261021/final-audit.json, once created,
and actual session-status.json;29540 is a historical tested identity after stop.

Pharah E now uses actual script007b/node3/resource010f factory events through
emission13, with native60/5/100/0/8 and12s cooldown calibration. Effect3 resolves
actual MC collision/cover, zero HP damage and radial self/enemy push. Its impulse
curve/decay are explicitly MC adaptations, NOT original OW physics certification.
pharah-e-four-dimensions passed all four dimensions and replay/cooldown; pharah-final
passed cover and original primary terrain/splash/protected blocks/replay. Q still
fails current compound motion calibration:90 real native factories,0 MC admissions,
target20HP. Preserve that explicit deferred gap under the user's permission for
difficult/server-dependent skills; do not enable a guessed straight-flight Q.

36 Gradle tasks, added E protocol/collision/replay refusal checks, native body/
armory/real MinHook fixtures, proper HTTP contract,45 supervisor tests,19 stop
tests and private-asset preservation tests passed. Startup version-label and
lab-height failures are retained; one NoAI E failure recording was accidentally
overwritten by the next test and has only an explicitly marked console summary.
Do not inflate any of these into a full-kit/full-original/long-session guarantee.

Original TIMER corruption and separate startup825346 remain without proven root
cause. No matching report in a tested live identity is bounded evidence only.
Old21144 was already exited at this turn's start with0xc000013a; no matching report
or proven cause was established. Native22512/8772/29584/1432/22548/29540 were explicit
restored shutdowns in this work. Preserve Hollywood/1080p/Low/8chunks/no shaders/
day-night/ALL, the pinned full-mod Twilight lab and existing saves. Automation
was observed PAUSED in prior continuity; do not silently reactivate it. Independent
game supervision is separate from scheduled development work.

## 2026-10-21T22:15 — latest voice and sword timing acceptance

Read EARLY-CHINESE-VOICE.md and GENJI-PARTICLES.md newest sections. All21 native
roster selection recordings actually passed:20 classic Mandarin plus original
OW1 Bastion nonverbal. Confirmed first person +1000ms, no picker hover, rapid
reselection cancels old pending line, same-hero H/back and all four dimensions
never replay. Actual MC audio matched all21; measured audible1.063..1.151s.
Native source flags1 alone is NOT first-person proof; inputActive also gates
native viewMode1/focus. This corrects the earlier immediate/hover admission.

Genji Q now deliberately randomizes original OW1 Japanese1FEDD and classic
Mandarin per latest user request; both naturally chosen in actual Q and mixed
audio matched. Actual McCree E/Q and Pharah Q Mandarin also passed. Core audio
correlations .80439..1.0. ALL21 SELECT is complete, not all21 full skill/banter
inventories. Other hero skill lines still need true native events and source
matrices. No invented speech on nonverbal skills, noTTS. Exact earliest2015 dates
unverified. Assets private, no OGG/MP3/WAV bundled in guest JAR.

Final combined guest SHA256 e0d9998247222ef06d43f6e2ac91e1a45c8c36307573e8b8bf078dd84dd311ce.
White-layered-sweep-v3-animation uses actual native47/48 Begin for local MC
cosmetics; damage57/58 unchanged. Fresh final target20->8->0, exactly two visual
events, observed animation-to-FX15.86/27.97ms, both before tracking, ALL and cleaned.
Wrong69/70 recovery candidate is preserved as failed; do not revert to it.
Six original native modules unchanged, compositor40/body12 ownership preserved.
36 Gradle tasks,5 asset-preservation tests and proper HTTP contract passed.

Latest actual native21144 creationFILETIME134370645797735686,
MC29288, independent supervised session12240/26964. Final audit:
research/three-hero-chinese-20261021/final-audit.json: six unique modules, matching
hashes, no matching current report, progressing composed frames, ALL, cleaned
fixtures and no pending Deadeye shots. Original Hollywood/1080p/Low/8chunks,
no shaders and day/night preserved. Final screenshot inspected: native Genji
first-person over actual MC village. Attempt to finish on picker encountered
focus failure, so further UI input stopped; do not claim final picker or force
input over active use. Both games remain usable independently of this thread.

Read NATIVE-TIMER-CRASH.md: startup960 report/minidump is a DISTINCT crash at
RVA825346 before Q, not oldd1428b TIMER. Exact960 creation unavailable. Native
29420/23300/27408/3716 were deliberately strict restored stops. Old TIMER writer
still unproved;21 swaps and a fresh no-report audit do not certify a root-cause fix.
Current heartbeat automation was observed PAUSED; preserve that explicit state
while updating its continuity prompt, do not silently reactivate it.


## 2026-10-21 20:42 — Genji white cosmetic build, early Chinese voice research

Subsequent quiet controlled run passed in the same6848/12968: sword target20->8->0,
exactly10 cosmetic particles per swing, Shift7 segments/35 cloud particles, idle
and McCree switch no replay, particlesALL. Cleaned after asynchronous cleanup
settled. Read GENJI-PARTICLES.md newest section and live-result.json passed=true.
White contact sheet actually inspected. This supersedes pending bounded test
below; broader four-dimension/full-kit acceptance remains separate.

Read GENJI-PARTICLES.md and EARLY-CHINESE-VOICE.md. User rejected the initial
green dust and requested a richer MC sweep. Current guest7803b009c103a64291ac0b5c
ea4959544b3deb6b902269fc1816ec8e2766ec39 has three white SWEEP_ATTACK layers,
small ELECTRIC_SPARK accents and sparse white CLOUD dash wake. No green dust.
Both startup options and runtime force MC particles ALL, including Low preset.
Existing native event/session guards and damage paths are unchanged.

Both normal strict cold stops (23132,25844) succeeded; these are deliberate
stops, not crashes. Fresh native6848/MC12968, supervisors5544/27716; six unique
unchanged native DLLs (compositor40/body12), installed guest hash and white style
verified, no matching report at audit,113 composed-frame advances in0.7s and
actual particleMode ALL. Current original picker over real MC village is visible.
This is deployment/presentation health, NOT final white-effect play acceptance.
Research/genji-particles-20261021 contains backups, actual captures, final audit,
and both failed controlled tests. Extra dash/attack/model transitions appeared
before their harness inputs; UI tests stopped. Do not claim target17 is the
expected single12-damage sword hit or promote green captures to white acceptance.
Next quiet run: final white visuals, one-swing damage, Shift, idle/replay,
hero/world switches. Temporary lab targets/blocks cleaned; supervisor stays live.

All21 early Mandarin selection/skill/ultimate replacement remains active and
unfinished. Twenty-one2016 original-uploader public Q reference clips and private
SHA256 manifest acquired/visually indexed; contain SFX, not clean deployed clips.
Installed GenjiQ is still Japanese, McCreeE English, McCreeQ accepted early Chinese.
Current retail154504 unsupported by official OWLib1151; isolated fallback failed
and no retail files/process were modified. Existing154088 Genji Chinese assets
remain usable for provenance work. Hourly mc heartbeat updated with both latest
requests, no duplicate automation. Preserve all prior accepted McCree/76 fixes.

## 2026-10-21 19:56 — Latest accepted Deadeye slice

Read NATIVE-MCCREE.md newest section. Current native23132/MC5808 uses compositor40,
body12, guest4559dae8… and independent supervisor. Actual final-four-dimensions
passed original per-shot animations/damage/charge/End/ordinary fire/fullHP/light
after Genji->McCree in Overworld, Nether, End and Twilight Forest. Actual650ms
request-file contention/36 IO failures recovered four distinct shots without
replay; actual Chinese Q mixed audio correlation.98768 passed. Earlier failed
gap/IO tests and their evidence are retained, not promoted to passes.

Keep separate: exact original server target order/aim rotation/full muzzle event
sequence is not yet certified. Old TIMER pool corruption has no proven writer;
moving script calls to the measured native logic thread is not a root-cause claim.
Read NATIVE-TIMER-CRASH.md. Bounded observer live23132 is current;30248/28272/17964/
23400 observers stopped with their actual targets. Only30248/12096/17852 crashed
in this work; later three were intentionally strictly restored/stopped. Private
profile/source/config/voice backups and videos are in research/mccree-native-shots-
20261021/. Never overwrite mapped DLL or add callback owners. Original Reaper lab
remains disabled. Selected Hollywood/1080p/Low/8chunks/no shaders/day-night retained.
Final mid-sequence world/hero interruption tests passed, no residual shots, fresh
revolver/fullHP recovered. Final-audit.json verified six unique owners, matching
hashes, no current crash report and cleaned fixtures. Current actual animated
McCree picker over MC Overworld is saved as final-visible_small.png. Independent
supervisor2100/12964 remains. Latest receipt/voice/cancellation results supersede
the earlier in-progress paragraphs below, which are retained as history.

## 2026-10-21 19:45 — Latest work supersedes older live-PID claims

Read NATIVE-MCCREE.md newest section before operating. User's current priority is
original Deadeye draw/separate shooting animations with damage per gunshot and
early Chinese Q voice. Selected compositor40/body11 and guest0136dabf… are cold
testing in native17964/MC28624. Four-dimension results are not accepted yet; read
research/mccree-native-shots-20261021/gap-four-dimensions/result.json. Earlier
30248/12096/17852 actually crashed (exit0 is not health). Their reports are saved;
30248 observer is stopped. Original-only3900 and fusion28272 were deliberately
normally stopped. Current bounded read-only reader17964 is under
research/mccree-native-shots-20261021/live17964/; inspect heartbeat before starting
another on this PID/creation. Independent session supervisor remains the launcher.

Compositor40 performs no meter notifications or Deadeye native calls. Body11 now
owns them on the existing logic update; actual render versus logic thread IDs
differ. No timer root cause is claimed. Preserve all accepted E/utility/Genji/76/
initialization/light changes, strict restoration and single-owner rules. Native
69 animation has actual per-shot proof; exact original server ordering/full muzzle
effect sequence and mixed Chinese audio proof remain separate acceptance gates.

## 2026-10-21 18:20 — Timer pool reuse evidence; read-only recorder

Read docs/NATIVE-TIMER-CRASH.md latest section. Actual TIMER pool element size56
and free-list first-word writes match all three invalid virtual-call pointer
lattices. Duplicate release/premature or concurrent reuse remain hypotheses; no
native fix is claimed. A bounded one-Hz independent QUERY/VM_READ identity reader
is running for native30248 under research/native-timer-20261021/live-30248-1803/.
It records script/owner/timer metadata for future crash-register correlation;
seven parser fixtures and the three real historical dumps passed. No gameplay
input, extra native callback, artifact change or new combat test was introduced.
Existing OW30248/MC23340 and supervisor remain healthy. Hourly prompt mojibake
was repaired through structured Unicode input; preserve this corrected prompt.

## 2026-10-21 17:25 — Timer-notification identity and exit0 crash evidence

Read NATIVE-TIMER-CRASH.md. Guarded actual-image disassembly now identifies the
three crashes' object as a **TIMER notification**: d14200 selects byte+0x22;
table d14440 maps type1 to d14266, whose d1428b virtual destructor call crashes.
Type8/attribute-change instead maps to d14405. The provided header agrees. The
visible f4f600 detour belongs to the supplied logger, not our d354b0 projectile
factory. This is object-category evidence, **not proof of the corrupting source**;
the native crash remains unfixed. Do not suppress arbitrary timers or blame the
notification/UI/input/GPU path without causal evidence.

Fixed a separate supervisor gap: after supervised gameplay exit, a matching local
error report now produces nativeExitClassification=crash-report plus evidence,
even if nativeExitCode=0. Exact project reporter executable/arguments, actual
redirected Documents, PID/time/Application/size/stable-content checks prevent
misclassification. No report is sent and no crash/restart loop is introduced.
Ten report-identity fixtures and45 supervisor tests pass. Actual historical
38368/26516/13448 files are all recognized with their reporter windows closed;
current30248 has no matching crash report. Picker-only startup exceptions are
still the older path, explicitly not claimed as fully upgraded.

The updated independent supervisor adopted the **same** native30248/MC23340 and
the same six healthy native owners; no game restart, extra injection, callback
owner, gameplay input or test target was introduced. Actual paths/hashes/JAR
b09fe17e… were rechecked; composition/fullHP/full original meter pixels inspected
and125 frames advanced in the final read-only audit (not an FPS guarantee).
The same native process had been alive about52minutes at the final audit; idle
survival is not sustained combat acceptance. Evidence is under
research/native-timer-20261021/ and the earlier notification-lifetime/crash13448/.
Current real supervisor worker16448 adopted via the existing exact-project
stop_supervisor control and normal startup/stage_ready ownership checks.
All potion/charge/HUD/slot/voice/Visor/strict-stop settings/artifacts remain as in
the previous accepted section. Highest next work is timer allocator/queue/release
ownership, originating script/user data and possible reuse/double release.

## 2026-10-21 16:35 — Applied potion survives hero reset; strict stop; crash evidence

This is the latest artifact/acceptance section; earlier sections are historical.
Guest SHA256 `b09fe17e98a78449727b6ff91988f7b2b5a00d1d71693aa21f06b8595b7a4506`; native six DLLs unchanged (compositor38).
Final actual native30248/MC23340, independent
supervisors15792,26100. Current identity,
hashes, actual native pixels and cleanup are in
`research/mccree-polish-20261021/mid-effect-final-audit/final-audit.json`.

Reproduced the previously documented boundary: E hit followed immediately by H /
Genji selection made NativeSessionGuard remove Flashbang's compensation while
vanilla SlownessIII still had8ticks left. Effective target speed changed.25 ->
.274999991 (45% slow), before returning.5. This was a real gameplay defect;
the initial harness also hit a transient diagnostic reset and is retained as a
failed test, not confused with lost native attacks. Guard reset now preserves
already admitted victim effects. MC server ticks own their expiry; server stopping
still calls the full cleanup. No input/admission/native model lifetime guard was
relaxed. Actual accepted E->H/Genji sequence kept exact50% through the remaining
8..1 potion ticks after the guard reset, then restored speed and particles.
Fresh McCree ordinary20->13 shot, full health and current-model light passed.
`mid-effect-accepted/result.json` is the actual receipt. General mod abilities and
victim chunk-unload/potion stacking semantics are not promoted to accepted.

New guest repeated all four dimensions: E actual damage/2s potion/exact slow/
expiry/replay, Q four locks/actual kills/remaining meter debit/native End,
ordinary fire after slot input, full HP and settled actual light all passed in
`mid-effect-four-dimensions/result.json`. Recovered-session Soldier76 core test
also passed: `native-visor-32760-1792571541722132900.json`.
35 guest build tasks,18 stop-report tests,3 session-stop tests,45 supervisor tests,
proper HTTP contract entry point and environment prerequisites passed.

Fixed a stop acceptance race independently of the gameplay patch. An actual32784
report said enabled=false/restored=true while slotInputRestored,viewLightRestored
and nativeFrameLimitRestored were still false: render stop publishes its vtable
result before all releases finish. The old helper could then terminate too early.
`restoration_complete` now requires all three release acknowledgements and
slotInputFilter=false for compositor37+, in both polling and session skip/final
checks. Regression fixture rejects each missing/false flag and wrong PID. Actual
strict32760 stop, preserving MC, completed with all flags true/failures0; fresh
native was cold-started afterwards. No mapped DLL was overwritten or extra owner
installed.32784's earlier incomplete snapshot is not accepted as full restoration.

**Open native crash:** after the four-dimension pass,13448 exited before the next
Visor test could begin, opening this project's BlizzardError reporter. Exit code0
was captured but is NOT a healthy exit: its minidump has execute access violation
0xc0000005, RIP in heap data, caller original native RVA d1428b / return d1428d
(`call [rax]`). Earlier38368 and26516 error logs have the same native call stack.
Private original logs/minidumps and guarded live read-only caller disassembly are
preserved in `crash13448/`; source reports are under
`D:/wendang/Overwatch/Logs/Overwatch/errors`. Error-report windows for exactly these
three project PIDs were closed without sending anything. The original provided
client error handler returns0, so future audits must inspect its reports as well.
The corrupt object's owner/cause is still unproven. Do not assert it is a user,
time limit, input hook, notification call or GPU fault; do not mark sustained
stability solved. The failed first Visor attempt is separate from the later pass.
Highest next priority is identify this native object/lifetime before adding kits.

Final audit: full native200/200/MC20, grounded Overworld/F6OFF, real passive meter
growth, ordinary shot after all top-row/numpad digits/wheels/actual middle click
and no duplicate replay, six actual mapped identities and matching installed/built
JAR, targets/random test mobs/air floors cleaned, native frames advancing and
visible composition inspected. Source settings remain Hollywood/1080p/Low/
8chunks/no shaders/day-night cycle. Private classic voices and real F9 diamond
activation were not changed. Hourly automation now prioritizes native crash
reports and strict restoration, retaining the user2s override and other fixes.

## 2026-10-21 — McCree potion, original charge HUD and slot-input repair

Final cold deployment audited: native32784/MC26620, independent wrapper15272 /
worker37896. Six unique actual mapped native owners match the pinned files;
installed/built guest hashes match. All top-row/numpad digits, wheel both ways
and an actual middle-mouse click were followed by a real20->13 shot and replay
without duplicate damage. Passive charge advanced; actual native final HUD60%
was inspected. Full native200/200/MC20, grounded Overworld, F6OFF, targets/mobs/
temporary air floors cleaned, owners healthy.246 frames advanced between the
two final audit snapshots (not an FPS guarantee). Final screenshot inspected.
`research/mccree-polish-20261021/final-audit.json` is authoritative for this run.
Exit-code telemetry is present in this cold-started supervisor. No UI test
interference was observed in the accepted final runs.

This section supersedes the older1.2s/compositor34/b295 baseline below. User now
explicitly requests **2 seconds of visible Slowness potion**, a custom duration,
not a claim that the modern official duration changed. Active guest SHA256:
`e67325ca84c08abc528258490f295be74300186457d5cc21ebec7bd926b84892`.
Compositor38 SHA256:
`320a13ba1d4748e6f0a425de1acac5497e8fd3c60c1abe2c29ee37b60fc85a7d`.
Body10/gate9/emission12/bootstrap10/localhero1 remain unchanged.

Real four-dimension Genji->McCree tests passed in
`research/mccree-polish-20261021/lifecycle-final38/result.json`: E75 native-HP
equivalent damage, exact50% effective speed, actual40tick potion with particles,
expiry and replay; Q four real locks, actual fire/kills, meter debit, automatic
native End and immediate20->13 ordinary shot after1/2/3 and both wheel directions;
full native health and independently read current-model camera-relative light.
Read-only light diagnostics initially refused compositor38 because their version
allowlist ended at34; fixed the diagnostic and reran, rather than relaxing light
ownership, hash, map or direction checks. Visor24436-1792568941537642800 passed.

Flashbang now gives actual SlownessIII for40server ticks; an extra modifier
compensates vanilla45% to the requested50%. Potion rendering is vanilla MC.
The impact burst combines FLASH/POOF/ELECTRIC_SPARK/gold dust and a quiet MC
explosion sound; it does not destroy terrain. Canister has silver body/caps,
gold collars, six ribs and a top lever. This is explicitly **MC-made geometry**,
not an exported original mesh. Grenade, native throw, burst, potion particles,
Q circles/skulls and native meter were reviewed in actual native video/contact
sheets. Existing collision/cover/native-event admission remains authoritative.
Arbitrary mod-mob spells are not fully hindered. On caster hero/world reset the
extra compensation is removed; an already applied vanilla potion expires normally,
so exact50% across a mid-effect caster reset is not yet accepted.

Deadeye already earned passive and real-damage charge; its original HUD subscription
was not notified by raw numeric writes. Existing compositor render owner now calls
the original SetValueFromRemote/Set&Notify method, matching the supplied plugin's
CVD_Edit call context. It checks current McCree model/admin/component/varbag,
numeric vtable/GUID/cost/value/membership, exact native function prefix and dirty
flag ownership; no second callback/subscription or replacement HUD overlay.
Int-to-float promotion was a failed candidate and is withdrawn. Original typed
payload writes are preserved. Real native20% and full/skull pixels passed; Q
still follows the documented offline Beta rules, not complete modern Deadeye.

Slot inputs are suppressed only in this exact native OW process's first-person,
foreground, hidden-cursor gameplay. Existing compositor owns individual MinHook
hooks for raw input, key-state queries and **PeekMessage/GetMessage**, plus its
WndProc filter; no adoption of another owner's hook, global uninitialize or
second callback owner. Digits/numpad digits, wheel and middle button are blocked;
movement/fire/skills and visible-cursor menus pass. MC inventory controls remain
in another unhooked process. Earlier low-level Python hooks, UI-unbind macro and
raw/key-state-only routes failed real fire tests and are not production paths.
`smoke38.json` proves real20->13 shots after digit and wheel, not counters alone.
Owned-memory/Win64 MinHook fixtures passed, including message filtering and exact
code restoration. Actual normal stop of24436 confirmed global restored=true,
slotInputRestored=true, failures=0 before cold startup; no mapped DLL overwritten.

F9 now completes all supports/border/flowers before water, then spawns a real
diamond and invokes the installed mod's public validated activation. The diamond
is consumed by the real mod; its real lightning/portal/travel applies. Four active
`twilightforest:twilight_portal` blocks stayed active. Actual native W+jump into
the pool reached Twilight Forest and an ordinary native shot did20->13 there:
`portal-travel.json` includes delayed arrival and the earlier short-wait failure.
The initial pool built while falling had a raised rim; a held jump crossed it.
Do not equate water or direct dimension-switch fixtures with portal entry proof.
Player does not need to throw an extra diamond. F10/F11 behavior unchanged.

Private classic voice selection: McCree AB63 Hold up now / AB5E It's high noon
from The Omnic Talking; Genji OW1/classic1FEDD, not newer059BBD or unused1FEDF.
Genji's archive OGG decodes identically to the previous local recording; the file
wrapper/hash differs. Archive upload dates2023/2026 are not recording dates.
Official2015 gameplay references and a2016 collection were checked; absolute
earliest2015 provenance for all three clean clips is **not established**.
Current actual mixed MC audio correlates E.753/Q.943/Genji.99999998 to the pinned
clips, and the Genji real native Begin schedules exactly one callout. Media stays
private outside commits/JAR; installer/provenance pins retained. See GENJI-VOICE.

35 guest build tasks, native input/meter/light/GPU/restoration fixtures,45 supervisor
tests,17 stop tests,4 light tests, HTTP contract fixture and final environment
prerequisites passed. These fixture results are separate from gameplay above.
Two earlier native processes exited unexpectedly without a captured exit code;
no cause is proven. Keep the failure evidence.24436 ran >11minutes and was then
deliberately stopped through normal recovery (watcher exit15); that controlled
stop is not an unexplained crash. Supervisor now retains a SHA-verified read-only
native handle to record future exit codes. Full sustained/all-hero/performance
acceptance is still open; do not claim every crash,180FPS or modern skill parity
is solved. Failed candidates/logs/videos are retained in the same research folder.
Hollywood/1080p/Low/8chunks/no shaders/day-night cycle and the mod-pinned isolated
Twilight Switch world are unchanged. Current final identity is in final-audit.json;
all earlier PIDs in this document are historical. Hourly automation was updated
to the new2s/potion/input/voice/HUD/portal scope and stays quiet without progress.

## Latest: McCree E/Q and F9–F11 — 2026-10-21

Post-deployment read-only audit: same36980/37592 and six pinned native modules,
JARb2958826… unchanged, owners healthy and actual native pixels inspected.
Fixed a real calibration-tool regression: the old E inspector rejected the new
12s cooldown as a beta mismatch. Schema2 separates beta receipt/modern cooldown
and leaves MC implementation unjudged. Five fixtures and actual native inspection
passed. research/control-profile-20261021/ preserves failure/before/after/audit;
no input, restart or new runtime skill was involved. Next gameplay work remains
the documented MC hindering/art/Q fidelity or next feasible picker-order skill.

Latest McCree request supersedes the earlier Deadeye cancellation. Read
NATIVE-MCCREE.md: original E factory now drives actual MC collision and modern
75HP/1.2s/50% slow/12s cooldown; typed original Q activation/targeting/fire drives
MC locking, occlusion, actual damage and remaining-meter debit. Separate private
original English E/Q voices preserve Genji's pack; MC-made grenade/lock rendering
is explicitly distinguished from retail-extracted assets. F9 real Twilight
portal, F10 random real mobs and F11 typed full charge are foreground single
edges. Four dimensions, actual health/light, cover/cancel/expiry/replay and held
utility keys passed on the mechanics candidate; final voice/audio audit is
recorded separately in research/mccree-complete-20261021/. Native owners are
compositor34/body10/gate9/emission12/bootstrap10/localhero1; normal restoration
and cold deployment were used. No Reaper experiment resumed. Q follows beta
rules and persistent typed action observation, not a lossless pellet journal or
full modern-server parity. Preserve Visor/Bastion/initialization fixes below.

Final acceptance: guestb2958826bbacf63b5d2d3764f47f7fb9ff80353fd2fb312fd81bf9217be7f90c
is cold-deployed. Actual native36980/MC37592, independent wrapper39432/worker37000;
six verified unique native DLLs, no owner failures. completion-lifecycle-settled/
result.json passed all four dimensions with E exact slow/expiry/replay, Q real
locks/damage/debit/automatic native End, immediate ordinary20->13shot, full HP and
settled current-model light. Visor regression36980-1792557585780972900 passed.
Actual mixed MC audio correlates to original E/Q clips0.853/0.983; visible grenade,
red circles/skulls and final native gameplay inspected. final-audit.json records
the exact process creation/module/artifact identities and134 advancing frames
(not an FPS guarantee). Cleaned targets, mobs and air floors; grounded McCree
200/200, MC20, F6OFF in Overworld. F9 portal remains usable. Hollywood,1080p/Low,
8chunks/no shaders/day-night cycle unchanged. PIDs/hashes below are historical.
Native Q recovery uses a fresh, scoped MC volley acknowledgement to send original
RMB once in the exact foreground process; it never sources an attack. MC-made
grenade art, arbitrary mob ability hindering and full retail Q parity remain
separate fidelity limits. See NATIVE-MCCREE.md and the retained failed receipts.


## Latest: Bastion Tank movement lock repaired — 2026-10-21

Read NATIVE-BASTION-TANK.md. Actual old adapter locked Tank as a transition:
native W velocity existed, MC displacement0. Add original012f/Tank105 to the
current-owner state binding; only unique Recon/Tank permits existing native
motion. Sentry/missing/conflicting states remain locked, with no delayed motion.
Real four-dimension grounded Tank movement, wall collision, release, native End,
Sentry lock, active-Q replacement/fresh Recon, fullHP/current light and actual
Recon damage/replay all passed. Lab meter grants are explicitly distinguished
from natural full-charge acceptance. Cannon still unavailable: original024f/25
is observed but no current-owner factory event was captured. No fake shell or
whitelist shortcut is enabled. Recall remains broken/deferred independently.

Current actual native21460/MC22668, independent wrapper25588/worker9388. Guest
JAR SHA256 cd5196f73c34be272190ccef724c8b7546147dad44c4cf7cf533d596c872d0c8.
Six native DLL hashes/versions unchanged; full normal restoration/stop preceded
cold deployment. Global Hollywood,1080p/Low,8chunks/no shaders/day-night cycle;
settings unchanged and same mod-pinned isolated Switch world. Final76 native
200/200/MC20, grounded Overworld/F6OFF, current light, no targets/blocks/active
projectiles or diagnostic flag. Actual final native pixels and all four Tank
captures inspected;57frames advanced in the sample, not an FPS guarantee.
Old39520/25228 and35352/39876 below are historical now.

Full33-task guest build/check,45supervisor fixtures and proper HTTP contract
passed. Post-deployment actual76 Visor suite passed passive/damage credit,
explicit-grant Q/drain, off-axis hit, cover/replay/End. Earlier normal-full-charge
proof remains separate. Private research/bastion-tank-20261021/ has before/,
q-probe.json, movement-before/after.json, lifecycle/result.json, failed speed
assumption receipt and final-audit.json. Visor receipt:
research/native-visor-21460-1792542441740716700.json. New verifier:
tools/verify_bastion_tank_movement.py. Next feasible picker-order skill is Hanzo;
Tank cannon remains a separately deferred native emission/physics investigation.

Latest heartbeat: NATIVE-PULSE-BOMB.md records read-only Tracer Q calibration,
not a new MC skill. Actual34/Volley1/projectile45 has15speed,30gravity,400/5
health modifiers and2/4 radius rings; unknown contact/fuse rules stay deferred.
Original Q was observed with an explicit lab meter grant; duplicate factory
statuses share one firing identity. Post-Q pistol20->15.199997 and fresh76
rifle20->16.599998 passed. Accepted JAR/six DLLs and39520/25228 unchanged;
independent35352/39876 remains usable, fullHP/grounded Overworld/F6OFF, fixtures
and diagnostic flag cleared, actual composed pixels inspected. Recall remains
broken; no E/failed guards were used. Next feasible picker-order work is Bastion
Tank calibration, or a separately proven Pulse Bomb attachment/fuse oracle.

## Latest: Recall attack-lock investigation; failed guards withdrawn — 2026-10-21

Read NATIVE-RECALL.md before testing Tracer E. A baseline-only A/B confirmed
ordinary pistol damage20->15.199997 before E, but after native Recall starts,
new shots are not admitted (203->203) and a new target stays20. Original native
hero replacement recovers. MC Recall is not implemented; exact native history/
input completion cause remains open. Two guard candidates failed actual tests
and were completely removed from ordinary launch/stop/tools. Never call this
a completed Recall/quarantine or revive the failed timer/variable candidates.

Current final native39520/MC25228, independent supervisor wrapper35352/worker39876.
Accepted guest JARc4f57937… and all six original native module hashes unchanged;
global Hollywood,1080p/Low,8chunks/no shaders/day-night cycle. Restored launcher/
stop/refresh-test source is byte-identical to this heartbeat's before/ snapshot.
Native callback restoration/cold startup flushed every experimental process.
Final native76 full200/200, MC20, grounded Overworld/F6OFF, no test targets/blocks/
projectiles or guard record for39520; actual composed pixels inspected. Frames
advanced, status ready/error-free, independent supervisor verified. Old26888/
26040/32320 identities below are historical, not current runtime evidence.

Post-recovery real76 Visor suite passed: passive/damage credit, native Q/drain,
off-axis hit, cover/replay/End. This suite used an explicit lab grant for Q;
the earlier natural-full-charge acceptance is separately documented. A final
new-model rifle/light/grounded smoke also passed.45supervisor/3stop fixtures and
HTTP contract passed; no new guest/native build was needed. Private receipts:
research/tracer-recall-20261021/final-audit.json, restored-smoke.json,
unprotected-ab.json and research/native-visor-39520-1792536352064540000.json.
The only new ordinary code retained is read-only inspect_native_recall.py.
Avoid ordinary Tracer E; H/native reselection restores a triggered lock. Advance
other feasible skill work while preserving this explicit limitation and Visor.

Latest heartbeat follow-up: read NATIVE-BIOTIC-FIELD.md. Read-only Soldier76 E
calibration located distinct072d visual/03dc field/0258 script and5/5/40 startup
variables. Two real E/injury/entity probes recorded a deployment gap; no MC
healing field was enabled. Current accepted Visor JAR/native DLLs and exact
26888/25228 processes remain unchanged; restored fullHP/grounded Overworld,
test fixtures/diagnostic flag cleared, independent supervisor34092/17156 healthy.
Next feasible skill-order investigation is Tracer Recall/Pulse Bomb. This
calibration does not change kit acceptance or prove server parity.

## Latest: Soldier76 native-Q MC Visor core — 2026-10-21

Read NATIVE-VISOR.md and HERO-SKILLS.md. Reproduced original-Q active/drained
with admitted rifle bullets but no off-axis MC damage. Fixed comparing the
factory tick with the different native state clock. Keep original15/12 phases,
geometry, damage/ammo, HUD and native drain; first observed acquisition boundary
is timestamped AFTER verified reads. No early timer or new native hook/schema.

Final guest JAR SHA256:
c4f57937e63e98c7602cb29a552c486e09dd253f1ac46730310503302e113065.
Compositor34/all native owners unchanged. Actual final26888/MC25228, independent
supervisor wrapper34092/worker17156, global Hollywood, Soldier76 native200/200/
MC20, grounded in actual Overworld/F6OFF. Targets/blocks cleared and composed
frames advancing. Actual identities must be checked again before mutations.

Final code passed four real dimension rows: inactive miss, active12degree
off-axis hit, real cover, replay, Q-active McCree replacement, fresh Soldier
without historical Q, current fullHP and scoped light. Normal passive/actual
damage credit from seven20HP targets reached native1500cost without explicit
test grants; native Q drained to0, hit20->16.599998, ended/charged again, and
post-End off-axis fire missed. Native Visor pixels over MC inspected. Actual
normal charge and explicit four-byte lifecycle test grants are separate evidence.

Private receipts: research/hero-skills-implementation-20261021/final/. Candidate,
original failure and corrected test-assumption receipts retained separately.
Full33-task build/check,45supervisor and HTTP contract passed. Snapshot/source/
old JAR backed up. No commit/publication. The user's continuation request also
resumed the existing hourly mc heartbeat ACTIVE with updated hero-order/native
fidelity instructions and quiet-unless-meaningful notifications. Flashbang/
Concussive MC effects, Biotic Field and full kits/target-outline/server parity
remain pending; do not revive Reaper experiments or cancelled Deadeye.

## Latest: hero-order control-skill calibration — 2026-10-21

The preceding initialization/light34 milestone remains deployed. Read
HERO-SKILLS.md for the new hero-order request, official references, exact typed
McCree/Pharah E data and explicit gaps.8actual E activations plus8native-cooldown
repeat rejections passed across the four real dimensions, with current fullHP
and light scope. This does NOT implement MC Flashbang stun or Concussive Blast
knockback. Their missing original status/physics policy stays unguessed.

Added inspect_native_control_skills.py (read-only, no production binding/event)
and3typed-configuration fixtures. Actual Windows report-sharing interruption in
factory calibration now uses existing bounded retries;17report/stop checks pass.
Original interrupted receipt is preserved. Private research/hero-skills-20261021/
has raw observations,8-row accepted rerun and final audit. No DLL/JAR replaced.
Automation mc remains PAUSED. Recheck actual process identities before any work.
Final actual audit: OW33748/MC36272, independent supervisor alive, Hollywood,
McCree200/200/MC20, grounded on real Twilight mushroom terrain, F6OFF, targets/
temporary blocks removed and calibration flag absent. Final composed native
gameplay screenshot was inspected. The center native H prompt is still visible
in that capture; this increment does not claim to resolve every legacy HUD item.

## Latest: current hero/world initialization + scoped light34 — 2026-10-21

Read SWITCH-READINESS.md before older snapshots. Actual33748/MC36272 with
independent supervisor38260/11548 is Hollywood/McCree, full native200/MC20,
natural brown-mushroom ground/F6OFF; picker restoration and gameplay pixels
inspected. Actual identities must be rechecked. This verified milestone is
followed by the user's new hero-order request: McCree Flashbang, then Pharah E
Concussive Blast. Research/calibration are not completion; no new skill yet.

Compositor34 SHA25625c910f5a159648e8a46858bd8a1c9b1424eaa3ddeec17f99328244049433fad;
final JAR1971e71b186382514de3625505b9963d66be9d13ca252a45ac636cccfb034f1f.
Same render owner/12Sun bytes, actual hero/world epoch and fresh-pose guard,
current CPU packet rechecks with strict same-scene cached-object recovery.
RGB/materials/reflections unchanged. Reporting distinguishes guarded ownership
from fresh packet confirmation. No loaded DLL overwritten or second owner added.

Fixed real first-shot binding loss, old Genji model retained-object ownership,
partial/meter initialization caching and a Windows status-sharing supervisor
exit. Fresh shared scope+actual observer identity50ms discovery,4Hz telemetry,
retryable skill repair and current model/world acknowledgements. Dash/ultimate
requests v2 require live controller/reference/hero/graph. Java signed-long world
IDs compare as the same unsigned wire bits. Exact content PE/PDB caching reduces
repeated binding work without weakening module identity. Health fills once per
identity, including partial retry.45supervisor/6scope/2cache tests pass.

Actual four dimensions:8first shots and8first Shift activations passed, fullHP,
replay unchanged. Six heroes' real attacks and28yaw screenshots passed/inspected;
same-process reload and full MC restart recovered independently. Final-JAR
four-dimension8shots repeated. Native Q/default callout, Pharah Space and76
sprint tested. Also repaired actual Dragonblade near dead zone:1/2/4m hit once,
7m/real wall did not. Explicit test grants are recorded. Genji dash timing/
distance still varied in one probe; activation is accepted, not every exact
skill timing/distance, all21kits,180FPS or MC material-light transport.

Private receipts: research/switch-readiness-20261021/. Earlier failed probes
and scope limits are preserved/documented there. Automation mc remains PAUSED.
Do not revive quarantined Reaper experiments; new skills need current native
data + official sources and actual world/hero regression before deployment.

## Latest: Hollywood weapon contrast, compositor33, full control — 2026-10-20

User explicitly revoked code-only and authorized full operation, later closed
the games and requested reopening/continued comparison. Final actual8416/MC27300
is independently supervised, Hollywood08000000000002af, McCree first-person,
native200/200 and MC20/20, grounded on real Twilight grass/F6OFF. Actual composed
frames advance; all four owners healthy. Read research/weapon-gray-20261020/
final-audit.json and WEAPON-GRAY.md. Do not reuse stale PIDs on takeover.

Production compositor33 SHA256:
f551244c334620b005c19585e91214200493f9b0d435987b74e0cc52e93f0e86.
It removes the non-Pharah extra foreground gamma lift and changes the existing
Sun-direction rig from overhead to calibrated camera-key coefficients
(0.5,-0.707106781187,-0.5). Native RGB/materials/reflections remain; Pharah's
prior tint policy unchanged. Only12Sun bytes are owned/restored by the SAME
render owner. This improves visible contrast, not full MC dynamic light transport.

Native-only7direction causal test after normal compositor restoration restored
all original light values. Real fused McCree12angles, Genji/Pharah/Reaper/76
4angles each and rapid-pan sheets were inspected. Actual picker Sun restoration
passed. McCree real movement/fullHP/damage/replay passed; Genji first cold shot
produced no new factory event, then reselect+settle retry passed target20->9.5,
replay unchanged. Do not claim that input/initialization timing issue was fixed.
Active temporary targets/platforms cleaned; original interrupted test receipts
and cleanup limits are documented in WEAPON-GRAY.md. No all-hero/all-angle or
sustained180FPS acceptance. Before-after.jpg is unretouched real screenshots.

native_compositor_version.py is now the shared launcher/attachment identity;
build default reads it and refuses a mapped target. Legacy32 remains separately
buildable. --keep-minecraft normal stop preserves the exact verified guest for
controlled native A/B, with3policy fixtures and real adoption/restoration checks.
40supervisor/17stop/4runtime-setting/4light fixtures, native GPU/restoration/
key-rig fixtures and HTTP contract passed. Automation mc remains PAUSED.

## Latest override: Hollywood again; CODE ONLY while user plays — 2026-10-20

User changed their selection back to Hollywood and reported dull/gray revolver
pixels. Normal Stop/Start deployed Hollywood25584, still compositor31. The map
change alone is NOT a weapon-gray fix. User explicitly answered "我还在玩，先只改代码"
after unexpected extra input invalidated the attempted static A/B. No game input,
hero changes, restart or candidate deployment until user releases the PC.

Read WEAPON-GRAY.md. Candidate32 removes the non-Pharah extra gamma shadow lift,
with exact RGB/alpha GPU swatch and existing native/hidden callback fixtures
passing. Built separately using build_live_passthrough.ps1 -NativeForegroundCandidate;
SHA256 a8b69a931c1bb5fafb73f765bcdd642d77c50dab9df53b5e0d924805a9ede668.
BUILD ONLY, not loaded/visually accepted. Launcher still selects31 deliberately,
whose mapped file hash remains unchanged. Native ambient/reflections may still
need work; do not claim this speculative candidate fixed the screenshot.
Current config nativeMap=hollywood globally. Older Kyoto decision below revoked.

## Latest user selection: use Kyoto login for every hero — 2026-10-20

After reviewing the21hero paired atlas, user explicitly selected Kyoto login
for all heroes. nativeMap=kyoto-login is the global setting (no per-hero scene
switch). Hollywood5164/MC22592 was stopped through normal restoration/save;
the current session cold-started Kyoto with unchanged compositor31 and the
existing camera-relative light profile. Do not revert to Hollywood based on the
earlier agent preference. Evidence: research/kyoto-selected-20261020/.
Actual36644/MC39124: map0800000000000664 verified, compositor31/failures0,
real Genji picker foreground over Minecraft visually inspected. Independent
supervisor remains available. final-audit.json records the actual identities;
recheck them on takeover.

## Latest override: user released input; all21-hero lighting atlas — 2026-10-20

User explicitly stopped all input and authorized unattended Hollywood/Kyoto
tests; this supersedes the code-only interval below. Latest request is a full
hero comparison image. Use normal UM CLI input, not the optional persistent
input experiment. Current compositor is31, SHA256
ed1d50c08cd613f44797a60b0db5da75209f373b50ac32d34acc62d53dfe8c4b.
Read NATIVE-FIXED-LIGHT.md latest increment before historical version30 notes.

Hollywood now has its own exact Sun profile under the SAME existing render
owner. Only12direction bytes change, restoring on picker/stop. Actual36912 passed
160static views (4heroes x40angles), visually inspected plus rapid pan and actual
picker restoration. It reduces gross directional flips; normal reflective
variation and map-specific ambient color remain. Kyoto9740/MC20408 and then
Hollywood5164/MC22592 each completed21hero captures at the same MC position,
dimension and yaw/pitch0. Actual42captures and visually inspected overview/three
detail pages are in research/lighting-ab-20261020/all-heroes/. Images retain
original colors; native idle poses differ slightly, particularly Torbjorn.
Final5164/22592 is on original Genji picker over real MC, Hollywood configured;
actual Sun restoration passed, failures0, MC alive. Independent supervisor
remains running. See final-audit.json; recheck identities on takeover.

One prior Kyoto33032 run stalled input after Genji40views; reason unconfirmed.
Normal stop/restart recovered it. Do not infer working input from healthy module
reports. Partial failed McCree captures are not acceptance. Kyoto9740 normal CLI
controls passed12angles each for Genji/McCree/Pharah/Soldier76 and rapid-pan checks.
Guest f4b6d99238240650b56c7fee716fcdd9d166fb1afd9be4cbf6525509e4e6e438
is now actually deployed; Visor MC aim/fullultimate acceptance still pending.

Automation mc remains PAUSED. Saves are disposable per user. Preserve source;
no unrelated commits or publishing. All21 here means the original beta roster,
and presentation capture does not mean every attack/skill is complete.

## Latest user steering / code-only interval — 2026-10-20

Read docs/_archive/2026-10/ITERATION-1-2-3.md for this increment and exact evidence. User is using
the PC and explicitly requested code-only work: do not send game input or stop/
restart games until they release it for testing. Save files are disposable;
additional save cloning/backup/restoration is unnecessary.

Lighting is now first priority: user still reports overwhite/overblack angles.
NEXT cold-start configuration is Hollywood08000000000002af, existing bootstrap10
quiet/neutral-daylight header route. Current29676 remains on Kyoto deliberately.
Read-only audit: compositor30 owns the light,147060updates/322pending/failures0;
direction acquisition is operating, but this is not uniform-lighting acceptance.
Genji/MC full200/20 on grounded real Twilight leaves; independent supervisor is
running. Recheck actual identities on takeover. No new map or all-angle visual
acceptance yet. Angle checker now supports both scenes,8yaws x5pitches including
near-vertical views; requires image inspection separately from direction checks.

Emission11 exact terminal tmp recovery is now implemented and actually tested
with a forced Windows sharing race, original hooks/callbacks restored.17stop and
40supervisor fixtures pass. Actual22436 four-dimension switch/reload and25144 MC
process restart/damage/movement/replay passed. Late Genji sword events now carry
session/world identity and server hero/model guards; deterministic delayed-
producer fixture passes. Actual blade transfer race acceptance remains pending.

Soldier76 Tactical Visor MC aim/charge-pause adapter and Pharah vertical launch-
basis fix are coded. Native25144 Visor graph/timeline/45radius/45cone measured;
real MC aim/occlusion/end test has NOT passed (input lost foreground, then user
requested code-only). Barrage complex motion remains safely deferred. Latest
guest build f4b6d99238240650b56c7fee716fcdd9d166fb1afd9be4cbf6525509e4e6e438
passed33Gradle tasks, including pure Begin/rifle/session/cone guards and Win64
reader fixtures. It is BUILD-ONLY, not hot-deployed. Running profile remains
187d2a8bb7808a3991e1ef42ce331320f44563e91da7090fcb1011fb83ef9ccd.
Do not claim matching source/build/profile JARs until a normal approved restart.

## Latest override: camera-relative Kyoto native light — 2026-10-20

Read NATIVE-FIXED-LIGHT.md first for this increment. Compositor30 keeps the
original native main light above the actual camera during first-person play,
restoring original direction at the picker/stop. Only12light-direction bytes
change; no camera/movement/attack rotation or new callback owner. Kyoto header,
bootstrap10, other owners and guest JAR are unchanged. Native reflections remain;
this is not full MC lighting/time-of-day transport.

Actual19240/MC16824: Genji12/McCree12/Pharah4angle checks passed; screenshot
sheets inspected. Genji/McCree real movement/fullHP/damage/replay checks passed;
actual picker restored original Sun direction. Final full-health McCree gameplay
and independent supervisor remain available; final-audit.json records current
identities/hashes/advancing frames and clean fixtures. Recheck on takeover.
Evidence: research/kyoto-fixed-light-20261020/. No new all-dimension/all-hero or
sustained180FPS acceptance is claimed by this lighting increment.

Worker reads the transient CPU packet's unique typed light candidate; existing
render owner validates/binds/writes/restores. Do not restore the failed fixed
arena offset or GPU-callback-only acquisition. The private diagnostic reads the
actual owner through matched mapped DLL/hash/COFF symbol; it never writes it.
Build preflight now rejects an actually loaded target before compiling.

Bootstrap report read-sharing races use existing bounded read_report in attach
and ensure_bootstrap (40supervisor/13stop fixtures). A separate emission11
terminal tmp race on32320 was recovered only after exact original native patch/
callback bytes and process creation were read/verified; unchanged terminal JSON
was promoted, then ordinary stop/save completed. No forced callback repair.
Automatic generic emission terminal recovery is still open; details/proof in
NATIVE-FIXED-LIGHT.md. No loaded DLL was overwritten.

## Latest override: Kyoto login backing scene — 2026-10-20

User requested Kyoto_Login_Scene. Config nativeMap=kyoto-login now cold-starts
actual0800000000000664 with bootstrap10, preserving its original map header/
lighting instead of applying Hollywood overrides. See NATIVE-BACKING-MAPS.md.
Other four owners and guest JAR unchanged. Actual four-dimension8-row McCree/
Genji movement/damage/replay and Pharah3Space/3shot checks passed. Original Pharah
picker animation/hand/HUD and MC background pixels inspected. Initial cold Genji
native working set3.17->1.73GB; this is not a sustained all-hero saving. FPS
improvement is not established; first sample lost foreground. Read exact limits.

Final native29540/MC6840/supervisor35968(wrapper28772), Pharah original animated
picker over real Twilight; player20HP/grounded/F6OFF on natural mushroom, native
200HP/ammo6, fixtures clear. Six actual mapped project DLLs/four live owners,
bootstrap10 actual map/header-unmodified proof and current JAR hashes audited;
frames advance. Evidence:research/kyoto-login-20261020/final-audit.json. Verify
fresh identities on takeover. Future ordinary starts keep Kyoto; cold Hollywood
fallback remains available through nativeMap=hollywood, normal Stop/Start.

## Latest heartbeat: bounded terminal body-report recovery — 2026-10-20 08:09Z

Actual current10364/MC30276 audited read-only: six expected mapped DLLs/four
enabled owners/failures0, current source/build/profile JAR hashes, advancing
frames, fullMC20HP/grounded/F6OFF on the natural mushroom. Actual composed Pharah
launcher/HUD over Twilight forest inspected. No input, restart or stop event;
independent supervision remains available. Evidence:research/heartbeat-20261020-0809/.

Fixed the previously observed final body.json.tmp rename race in the existing
Python stop control. Only body-v10 terminal reports newer than this exact
process are eligible. Actual original three-slot native callbacks must be read
and verified; a remaining copied body callback on any other object rejects
recovery. The bytes/mtime/size are rechecked before bounded rename retries.
Missing events can recover a verified already-restored body; other owners retain
their original failure behavior. No native memory writes/new owner/DLL rebuild.
13stop fixtures and39supervisor fixtures pass. Actual running body rejected a
synthetic terminal JSON without changing either file or stopping the game.
Positive promotion/retry paths are fixture-tested; this heartbeat did not stop
the live session to reproduce the full real rename failure. The prior manual
positive native proof remains research/_archive/2026-10/pharah-terminal-body-report-recovery.json.
Next: original animated Pharah muzzle/hardpoint calibration or another bounded
unfinished skill; full modern VFX parity and all-hero ultimate activation remain open.

## Latest override: Pharah primary and Space response — 2026-10-20

Read [PHARAH-RESPONSE.md](PHARAH-RESPONSE.md) for official video provenance,
visual limits, guarded native200ms Wait removal and requested8m/s Space lift.
The current isolated Switch A test passed three actual Space pulses at peak
7.90195m/s, final rise delays57.42/65.91/67.28ms,3native rockets/3flashes and replay
deduplication. Ceiling/landing, native fuel depletion/recovery/Shift retry and
terrain/splash checks passed. Final additive-material pixels were inspected;
the temporary bright rectangles are fixed by packing RGB intensity correctly.
Final native10364/MC30276/independent supervisor29800, safe grounded fullHP,
F6OFF/ammo6, fixtures clear; six mapped DLLs/four owners and JAR hashes audited.
Evidence:research/_archive/2026-10/pharah-reference-final-audit.json. Recheck live identities.
Mesh size2 is user-requested, not an exact measurement of official world size.
The actual official Rocket Launcher clip was inspected; full native effect
graph and animated hardpoint tracking remain incomplete. Do not claim1:1.

One normal stop exposed a terminal body report left in.json.tmp after failed
MoveFileEx. Original three actual body callbacks were read and verified, then
the unchanged terminal report was promoted; ordinary stop then restored/saved
the session. Evidence:research/_archive/2026-10/pharah-terminal-body-report-recovery.json.
No second owner, DLL overwrite or forced callback repair was used.

## Latest override: Dragonblade voice and walk response — 2026-10-20

Read [GENJI-VOICE.md](GENJI-VOICE.md) for this increment's private asset
provenance, implementation, exact tests and limits. The actual native Genji
ultimate now plays the extracted default Japanese callout. Reaper/Soldier76
reversals and release no longer replay old-direction motor inertia; sprint
boost remains. Nether/End hero checks passed. Switch A settings are preserved;
no retail attachment, native DLL change or quarantined Reaper experiment was
used. Final deployment evidence: `research/_archive/2026-10/voice-motor-final-deployment.json`.
Recheck live identities instead of reusing historical PIDs below.

## Current override: generic ultimate meter and active background — 2026-10-20

The user resumed project operation; heartbeat `mc` is ACTIVE. The current
background session is a fresh normal launch and remains available for later
hero/dimension checks. Historical process IDs below are not current runtime
evidence. The later Pharah changes, generic ultimate-meter work, incomplete
acceptance, current test-clone settings and Overwatch x Genshin migration
guidance are in [the current README](../README.md), especially sections 2,
10, 15–17 and the latest MODLOG entry.

The current session selects `Overwatch Twilight Switch 20261019 A`;
`research/_archive/2026-10/pharah-original-settings.json` retains the original Trial A settings.
The newest Pharah build passed its recorded build/fixture and bounded flight/
blast checks, but new ceiling/landing and in-flight visual acceptance remain
unfinished. Do not infer acceptance from older flight or projectile records.

The 2026-10-20 increment generalized typed native charge/cost feedback to the
verified Assault/Defense roster while keeping Genji's Dragonblade event reader
as the sole Genji writer. A fresh real session selected McCree and reported
`nativeCharge.ready=true`, `charge=57`, `cost=1200`, and an empty non-Genji
`ultimate.error`; an earlier same-session Winston switch reported charge
62→82 with cost2000. Build/check (29 tasks) and the HTTP contract passed.
Evidence: `research/_archive/2026-10/ultimate-meter-20261020.json`. This is a charge-meter and
offline-credit adapter, not complete native activation for every ultimate.

The subsequent Switch A lifecycle run passed all 8 rows across Overworld,
Nether, End and Twilight Forest: McCree/Genji rebind, movement, native damage,
replay deduplication and cleanup. Evidence is
`research/world-hero-switch-3884-1792456979018044100.json`, with four dimension
captures. MC subsequently saved and stopped normally, but the initiator is not
established: the verifier's normal finally block cleans fixtures, not MC itself.
The connection refusal therefore proves an unavailable server, not why it stopped.
Those four captures were produced; do not infer visual inspection from that run.

Root retains the three current Start/Stop/Configure entrypoints. Eight auxiliary
entrypoints moved to `launchers/standalone` and `launchers/legacy` with adjusted
root paths and project-Python bindings. Three verified extracted installation
archives were removed (approximately 3.75 GiB); differing original OW archive
members were preserved first. Sources, saves, installed tools, game copies,
current artifacts and evidence remain. Private audit/old README/launcher backups:
`research/cleanup-20261019/`. Read-only environment and launcher configuration
checks passed after cleanup; these are not new real-game acceptance.

## Latest heartbeat: initial-picker guest recovery and normal-stop race

Supersedes older live IDs: native24880 / MC21484 / standalone supervisor14768.
Original Trial A/settings restored, confirmed Genji then H back to animated picker;
actual composed image inspected. 1080p/OWLow/8chunks/no shaders/day-night/F6flight,
same seed. Player20HP/alive/onGround/flightOFF approx(57.500,25,10.898), native200HP.
Six expected actual mapped DLLs/four healthy owners/private probesOFF/hashes/frame
progress/current hero-model/clean fixtures audited. research/_archive/2026-10/initial-picker-final-status.json
passed. Games and independent background stay available.

Fixed source-inspected gap: before first confirmation, wait_for_selection did
not supervise a stopped MC. GuestRecovery now shares creation-aware identity,
current world/JAR manifest and the3-restart budget across picker and gameplay.
Actual2592 initial picker: MC32128->3884 automatically, same native model, body
writes0, no false gameplay confirmation, real MC composition/Genji animation
inspected; subsequent actual movement/Genji20->9.5/replay passed. Then gameplay
MC3884->30956 on clone A->B passed McCree/Genji movement/fire/replay, native stays
200HP with sampled source-gap Yspan0.004883; shared restart count2. See
INITIAL-PICKER-RECOVERY.md for exact evidence/backup/limits. Python-only change;
39 launcher and3 stop-read fixtures pass; native/guest artifacts unchanged.

Also observed PermissionError13 on normal-stop world-live report read after3
owners restored. Added bounded8x30ms read/parse retry to existing stop controls;
normal rerun restored all owners/saved MC, no forced exit. Evidence
research/_archive/2026-10/initial-picker-stop-race.json. Final cold supervisor includes last edit.
Next cached yellow H prompt or another bounded hero/source slice; no full kits/
portal/FPS claim. Quarantined Wraith/lifetime experiments stay OFF.

## Latest heartbeat: Tracer Blink dimension/model regression

Supersedes older live IDs: native24440 / MC3164 / standalone supervisor5156.
Original Twilight Trial A/settings restored after clone-only tests. Confirmed
Genji once to initialize full supervision, then H back to original animated picker
over real TF; final composed image inspected. Settings1080p/OWLow/8chunks/no shaders/
day-night/F6flight/same seed. Player20HP/alive/onGround/flightOFF at approx
(57.500,25,10.898); native200HP. Six mapped project DLLs/four healthy owners,
private lifetime/skill/factory probesOFF, loaded/profile/build hashes match, source
frames advancing and phase/hero/model current. research/_archive/2026-10/blink-worlds-final-status.json
passed. Games and independent background stay available.

Actual native21700 in the separate mod-pinned Switch A clone: four-dimension
Tracer Blink checks passed after world transfer and McCree->Tracer recreation.
All8 original Shift activations consume3->2 charges once, move7.47949..7.48047m
horizontally with vertical0, one capture/event, no idle phantom displacement.
Each dimension's actual pistol burst admits10/hits10, target20->13.999996; replay
unchanged/zero rejects. Composed native hands150HP/30ammo over actual TF/Overworld/
Nether inspected. Evidence research/blink-world-switch-21700-1792376098940089700.json.
Added repeatable tools/verify/verify_blink_world_switch.py; no production code changed.
See BLINK-LIFECYCLE.md for backup, corrected platform-fall harness false positives
and explicit limits. No physical portal/all-kit/FPS acceptance. Long Blink source
loss/same-model reload/Recall/Pulse Bomb remain open. Cached yellow H prompt still
visible; choose that bounded UI defect or another hero lifecycle slice next.
Normal save/stop on both transitions; no extra owner or loaded DLL replacement.

## Latest user-requested fix: world/hero reload lifecycle

Supersedes older live IDs: native7116 / MC24652 / standalone supervisor18072.
Original Twilight Trial A/settings restored; final animated Genji picker over MC
inspected. 1080p/OWLow/8chunks/no shaders/day-night/F6flight, same seed. Player20HP,
alive/onGround/flightOFF at approx(57.500,25,10.898). Six actual mapped native DLLs,
four healthy owners, private probes OFF, loaded/source/profile hashes match;
research/_archive/2026-10/world-switch-final-status.json passed. Background and games stay live.

Fixed stale-source native falling/death, replacement MC different-world resume,
false stability from repeated same packets, source-epoch hero rebind and same-save
client disconnect/controller reset. Added clone-only real dimension/reload tests.
Actual Overworld/Nether/End/Twilight x McCree/Genji 8 rows passed movement/native
damage/replay. Same-process unchanged-model reload, same-save MC process restart,
and different-save MC restart with OW unchanged passed; native alive throughout
sampled loading gaps. Final cold-build Genji20->9.5/replay also passed. No full
portal/all-hero/FPS acceptance. See WORLD-HERO-SWITCH.md for exact evidence,
backup, test-only reload hang/recovery, sampler false positive and remaining scope.
Native8 fixture suites, guest27-task build/check, Java-fixture HTTP contract and
33 supervisor Python regressions passed. No loaded DLL overwritten/extra owner.
Next: another bounded hero lifecycle check or cached yellow H prompt; Wraith OFF.

## Latest heartbeat: damage categories and teleport-safe splash

Supersedes older live IDs: native30012 / MC24764 / standalone supervisor23264.
Startup research/_archive/2026-10/damage-categories-final-startup.log. Same isolated Twilight
Trial A/settings/seed; final original Genji picker over TF inspected. Player20HP,
alive/grounded mushroom(57.5,25,12.5),flightOFF. Actual mapped six native DLL paths
checked (world29/body10/gate8/emission11/bootstrap9/localhero1),4 owners healthy,
private probes OFF, loaded guest/source/profile hashes match. Current phase/hero/
model, no error/warning, source frames advancing; picker readyfalse expected.
research/_archive/2026-10/damage-categories-final-status.json passed. Games/background stay live.

Fixed untagged generic damage source bypassing original projectile reactions.
NativeDamageTargets now has explicit projectile/melee/beam/explosion routes.
Only actual projectile/hitscan/direct impacts carry IS_PROJECTILE; quick melee,
dash/blade and explicit Tesla beam remain separate. IS_EXPLOSION splash and
all4 bypasses_cooldown remain. No damage/range/cooldown values changed. Actual
MC Enderman.damage bytecode confirms its IS_PROJECTILE branch; local private
research/_archive/2026-10/enderman-1.21.1-javap.txt. See NATIVE-DAMAGE-TYPES.md for routes/limits.

Actual30012 tools/verify/verify_native_damage_categories.py passed: McCree native ray
7 incoming triggers original Enderman teleport,40HP unchanged/IS_PROJECTILEtrue;
original quick melee5 loss40->35 with non-projectile source; Winston31 native
interval receipts40->36.351974 using non-projectile native_beam, release/idle/
replay stable. Original hands/HUD/real target screenshots inspected. No synthetic
damage or immunity/stat changes. Air fixture pauses AI/gravity only and records
at most32 receipts for its exact owned target; orphan/shutdown cleanup included.
research/native-damage-categories-30012-1792371881793147200.json.

Also fixed splash using pre-direct-hit target boxes: direct native damage may
teleport/remove a real target. Resolve direct reaction first, then collect actual
current splash bounds/exposure. Actual Pharah direct4 on Enderman triggers
teleport outside blast; one detonation,HP40 unchanged,direct/splash loss0,no
stale explosion receipt; replay unchanged (same report). Final normal Pharah
4+8 damage20->8/terrain/protected blocks/range/replay still pass:
research/native-blast-30012-1792371910771690800.json. Final Genji20->9.5/replay
unchanged/zero rejects: research/_archive/2026-10/damage-categories-genji-fire-30012.json.

After category split, real mod/server fixtures24504 retain Naga explosion immunity
and segment reduction, Hydra head reduction; research/twilight-multipart-24504.json.
Those are server fixtures before the splash-order follow-up, not fresh native
Hydra firing. Existing native Naga acceptance below remains historical proof.
Normal stop/save before testing; backup damage-categories-20261019/
20261019-085523.zip (806files,714.7MB) under universal-modder/backups. Final guest
27-task build/check (including explicit beam dispatch regression) and Java-fixture
HTTP contract passed this heartbeat. No loaded DLL overwritten/extra owner,
unrelated reset/clean/commit. All test targets/blocks/boss bars gone, griefingtrue.
Current Pharah optional Barrage remains deferred; no full kit/fight/FPS claim.
Cached yellow H prompt is still visible in some hero gameplay captures despite
hideHeroPrompt=true; separate pending UI issue, not fixed by this damage work.
Next: a bounded unfinished hero skill or that reproducible UI defect; full Hydra
native weak points/progression/all kits/sustained180FPS remain open. Wraith OFF.

## Latest heartbeat: actual native Naga segment hits and original boss bar

Supersedes older live IDs below: native9300 / MC32532 / standalone supervisor19648.
Startup research/_archive/2026-10/twilight-native-ai-startup.log; same separate Twilight Trial A,
seed/settings unchanged (1080p/OWLow/8chunks/no shaders/day-night). Final animated
Genji picker over TF inspected. Player20HP/alive,flightOFF,grounded mushroom at
(57.5,25,12.5). Actual mapped native DLL paths checked: existing world29/body10/
gate8/emission11, bootstrap9/localhero1 only. All4 owners healthy, private probes
OFF, loaded guest jar hash matches source/profile manifest. Hero/model/phase
status current, no error; picker ready=false expected. Evidence:
research/_archive/2026-10/twilight-native-ai-final-status.json passed. Games/background stay live.

Added a bounded live Naga fixture, confined to the separate creative TF trial:
POST /world/twilight/native-naga and native-cleanup. It applies NO fixture damage,
keeps original AI/health/boss-bar updates, pauses gravity only, validates loaded
empty air within border/height, temporarily disables griefing, and removes boss/
parts and restores the rule on cleanup, owner/dimension/flight loss or1200 server
ticks (60s at20TPS).
Normal shutdown cleanup remains active. Bounded32 damage receipts exist only
while this opted-in fixture owns the actual target; no normal gameplay log spam.
/world bossHud reads original client BossBarHud metadata and pixel availability.

Actual9300 tools/verify_twilight_native_fire.py passed:3 original Genji projectile
admissions/hits, all3 damage receipts identify real NagaSegment504/parent494,
3.5 incoming ->2.3333359 MC loss each (upstream reduction), parent120->112.99999.
Replay HP/receipts/damage unchanged. Original AI active; original Chinese Naga
bar percent0.9416666 matches health. Actual MC and composed native windows both
inspected; original hands/ammo21/24/HUD and original mod boss bar visible.
research/twilight-native-fire-9300-1792368123384796600.json and -native/-mc shots.
This is native-vs-Naga-segment and dynamic-bar acceptance in a controlled air lab,
NOT a full boss fight/progression, Hydra native-fire acceptance or all kits.

Earlier17440 test damaged the real Naga but did not record exact hit parts;
31996 confirmed3 segment receipts/120->113 with AI paused, whose bar stayed1.0.
Keep these evidence levels distinct. Final live fixture keeps original AI so
the upstream bar updates naturally; no custom percent/health writes were added.
Temporary entities/blocks/bar removed, griefing restoredtrue; final player landed
and H picker is supervised. No extra callback owner/loaded DLL overwrite.

Backup before tests after normal save/stop:
<USERPROFILE>/.universal-modder/backups/twilight-native-boss-20261019/20261019-075433.zip
(803files,690.3MB). Environment/SHA checks, final guest27-task build/check and
Java-fixture HTTP contract passed. No unrelated changes reset/cleaned/committed.
Next: actual native Hydra weak-point shots or one bounded unfinished hero skill;
full fights/progression/all kits/sustained180FPS remain open. Current Pharah
Barrage deferral below still applies. Quarantined Wraith probes stay OFF.

## Latest heartbeat: explosion semantics and supervised hero switching

Supersedes the older live IDs below. Final native24032 / MC32616 / independent
supervisor24864; recheck processes before input. Startup:
research/_archive/2026-10/twilight-blast-supervision-startup.log. Same separate Twilight Trial A,
same seed,1080p/OWLow/8chunks/no shaders/day-night. Final original animated
Pharah picker over actual TF inspected; status phase=hero-selection,ready=false
is expected. Status hero matches actual native body, no global error.
research/_archive/2026-10/twilight-blast-supervision-final-status.json passed. Player20HP/alive,
flightOFF,grounded brown_mushroom_block at(57.5,25,12.5), not the old grass Y7.
All4 owners enabled/failures0; private lifetimeOFF/calls0, Entry/Tick absent,
skillMask0 and factoryCalibrationOFF. Probe/targets/blocks cleared and griefing
restoredtrue. Games and standalone supervisor remain running.

Fixed merged direct/splash damage: exact impacted part receives ordinary direct
damage, then once-per-canonical-owner splash uses tagged native_explosion.
Original boss part.damage preserves immunity/armor. Real mod/server fixture8016
passed: Naga explosion40 leaves120HP, ordinary40 ->93.333336; Hydra explosion40
360->355, ordinary40 ->350. This is server-fixture acceptance, NOT native shots
at bosses. research/twilight-multipart-8016.json. Actual native Pharah primary
24032 passed direct4+splash8 MC loss20->8, terrain destruction/protected blocks,
range and replay dedup after cold restart. Evidence:
research/native-blast-24032-1792364639247432500.json.

Fixed an optional Pharah armory calibration error preventing supervisor health,
hero and picker status updates. Only typed known unsupported Pharah extensions,
with exact current hero/model rechecked, become structured optional-armory
warnings. Validated primary remains active; unexpected failures still retry.
Current Barrage variants need calibration and remain unadmitted; older Barrage
proof below does NOT establish current availability. Native24032 actual
Pharah ->McCree ->Genji ->Pharah and final H picker passed, warnings1/0/0/1,
no global error: research/supervised-hero-switch-24032.json. Actual primary blast
test also passed while warning present. No guard relaxed or second owner loaded.

Before tests: normal restore/save/stop and profile backup
<USERPROFILE>/.universal-modder/backups/twilight-blast-20261019/20261019-064832.zip
(801files,674.5MB). Environment/hash checks, guest27-task build/check, Java-fixture
HTTP contract,32 startup regressions and11 weapon-binding checks passed.
Next: native-vs-multipart firing/boss-bar visual acceptance or a bounded unfinished
skill. Full boss fights, full12 kits and sustained180FPS remain unaccepted.
Keep quarantined Wraith probes OFF. Hourly mc heartbeat remains active.

## Latest: continued development and real Twilight Forest trial

Supersedes the ordinary Fresh15C running state below. User requests ongoing
hero/bug improvements and trying Twilight Forest; difficult/server-dependent
skills may remain deferred. Thread heartbeat 守望先锋与MC持续完善 (id mc) is ACTIVE,
hourly. Do useful incremental work and notify only meaningful progress/failure.
Read docs/TWILIGHT-FOREST.md before changing the mod/profile/world selection.

Current standalone supervisor16328, native27264, MC20412; recheck actual IDs.
Startup research/_archive/2026-10/twilight-final-startup.log. Separate Overwatch Twilight Trial
20261019 A, same seed,1080p/OWLow/8chunks/no shaders/day-night. Original Fresh15C
save preserved and backed up before installation. Official Fabric1.21.1 beta
4.8.754 is pinned/hash guarded; do not open the trial without that dimension mod.

Actual native3604 Genji walked through the mod's portal into mushroom_forest;
20HP/grounded grass at(57.5,7,12.5). McCree ->Genji ->Mei ->Genji inside TF all
had full original pools and20MC HP; actual McCree20->13/Genji20->9.5 MC target
damage and replay passed. This is not all-dimension/all-hero acceptance.
Current27264 repeats native Genji20->9.5/replay unchanged/rejected0 after the
multipart fix. Actual composed native hands/HUD and mushroom-forest pixels
inspected. research/_archive/2026-10/twilight-final-native-fire.json and final gameplay capture.

OptionalMultipartTargets fixes excluded Porting Lib body-part targets and the
undamageable Hydra root hiding its real parts. Bounded typed optional API,
world/parent/ID guards, one loaded-entity scan per server tick; damage still calls
the original part and preserves armor/weak-point rules. Real mod/server fixture
27264 passed Naga12parts, segment120->93.333336 on40 incoming; Hydra46parts,
head360->355 on40 incoming. Actual admission/resolution and canonical owner
health passed. research/twilight-multipart-27264.json. This fixture directly
calls server damage: NOT a native projectile-vs-boss firing acceptance or a
complete boss fight. Probe bosses/parts discarded, mobGriefing restoredtrue,
probeActivefalse. No temporary test blocks. User-cancelled projectile visuals
and retired replay owners remain disabled.

Found/fixed unattended reopen blocked at MC experimental-world prompt:
TwilightTrialStartup selects vanilla Create Backup and Load only for the opted-in
separate trial and exact experimental prompt. Cold auto marker in latest MC log,
native archive backups/2026-10-19_06-08-15_Overwatch Twilight Trial 20261019 A.zip
(7,946,064bytes). No manual click needed in final cold run. Never generalize this
to arbitrary confirmation screens. Earlier blocked run ended before OW launch;
it was stopped/saved normally, not a native crash.

Guest27-task build/check,28 startup checks and Java-fixture HTTP contract pass.
Current4 owners enabled/failures0, lifetimeLabOFF/calls0, optional Entry/Tick
scopes absent/mask0, factoryCalibrationOFF. Full20MC HP,flightOFF/grounded grass.
Final native Genji picker over TF; games and independent supervisor remain live.
research/_archive/2026-10/twilight-final-status.json. Stationary source mean4.26ms,p956.68ms is
only a short MC render sample, not sustained180FPS composed/travel acceptance.
Next: actual native attacks against mod multipart bosses, their visual boss bars
and immunity rules, then measured unfinished hero abilities. Bastion Q capture
changed119 state records but had no observed tank factories in its first firing
window; do not claim a tank feature or missing-server diagnosis from that alone.
Keep quarantined Wraith experiments OFF.

## Latest scope decision — difficult skills deferred, ordinary launch restored

User explicitly permits postponing difficult or server-dependent heroes/skills.
Do not resume private Wraith research as an automatic next step. Consolidate the
verified slices below; full12 kits and exact original parity remain incomplete.
Ordinary startup: research/_archive/2026-10/assault-defense-stable-final-startup.log. Current
native30608 / MC30100, independent supervisor12536; always recheck actual
processes and research/session-status.json rather than trusting historical PIDs.
No new world: Fresh15C, seed-490526775015596785,1080p/Low/8chunks/no shaders,
day/night cycle. Independent supervisor remains the hero-binding owner.

Private native14848 lifetime experiment passed FLOW ONLY: exact provided
inject.dll StartStopState helper atRVA7acd0, called once from the existing body
callback, advanced original PhaseOut1/MovementMod5 Begin AND End. Evidence:
research/reaper-lifetime-14848-1792357210689184900.json. This did not validate
speed, cooldown, protection, firing exclusion or stability. Subsequent advanced
test failed; the native process exited unexpectedly before a second lifetime
command was posted. Cause unknown; no WER entry is not proof of a normal exit.
Its fixture also removed its own air floor when creating a target; do not use
that failed script as acceptance. MC supervisor subsequently saved all dimensions.

The helper remains strict private opt-in research, not a production feature.
Normal launch must show body nativeLifetimeLab=false/calls0 and gate
skillMask0,skillEntryInstalled=false,skillTickInstalled=false. No extra callback
owner. Do not enable OWMC_NATIVE_LIFETIME_LAB/OWMC_REAPER_ENTRY_PROBE/
OWMC_REAPER_TICK_PROBE for ordinary play. Failed and partial evidence is retained.

Fixture cleanup now runs on SERVER_STOPPING before the save. Initial loaded
player-area recovery removes only old AI-disabled/no-gravity villagers with the
exact lab name "Native projectile verification" after interrupted tests; it does
not alter terrain or other villagers. Guest27-task build/check passed after this
change. Actual normal launch recovered1 orphan, wallBlocks0/testError empty,
player20HP/alive/flightOFF/onGround grass at(-210.51758,84,86.03223).
research/_archive/2026-10/assault-defense-stable-final-check.json passed: all4 modules enabled /
failures0, private lab OFF/calls0, Entry/Tick scopes absent/mask0, deep factory
calibrationOFF,3 actual Genji projectile emissions admitted/refused0 and composed
MC frames advancing. This is a startup/fire smoke test, not a new full damage,
performance or cross-dimension acceptance. Actual original hand/ammo21/24/HUD
over MC inspected; final original Genji picker over MC inspected. Native health
200/200, MC20. Games and supervisor left running at hero-selection.

## 2026-10-19 active work — supersedes older running-state claims

Current ordinary startup research/_archive/2026-10/assault-defense-stable-final-startup.log,
native30608. Verify actual PID/status; earlier21996/17576/4832/28948/12148/29284
were restored/stopped/saved. Private14848 exited as described above. Loaded versions
world29/body10/gate8/emission11; same filenames do not establish same content.
Never overwrite loaded DLLs or attach another callback owner. Preserve dirty files.
Same Fresh15C world/seed,1080p/Low/8chunks/no shaders/day-night; no new world.
Independent supervisor stays running after the agent's turn.

Verified slices (private evidence, never equate them with full12 kits):
- Actual21996 Hanzo wall climb adaptation:4-block wall rise4.0213m and landed
  on top at84/onGround;41 native climb ticks. Genji rise4.1768m/33 native ticks,
  Soldier only1.2522m jump/zero climb/zero starts. Fixtures cleaned. Existing
  MC6m/.30 tick/ledge rules are adapter policy, not original beta constants.
  Native packet animation state admitted for exact current Genji/Hanzo/model.
  Pending native horizontal motor totals are discarded during climbing. See
  research/wall-climb-21996.json; native climb video/contact is separate evidence.
- Native4832 self-heal acceptance passed: Bastion0153/ModifyHealth2 actual
  Begin/End gates50HP over1s; Mei05fe/ModifyHealth30 gates150HP over native
  duration expression237-.1 (237 currently4),150 total cap. Exact target GetOwner,
  literal/config/dynamic path/membership/current owner/creation guards. Native
  server implementation is absent: distribution is an explicit MC adaptation,
  not proven original server interpolation. Real MC health, idle (natural regen
  disabled), release/End, maximum cap and McCree reset passed; injury/rule restored.
  research/native-sustain-4832-1792354907713856600.json. Cold28948 also fixes lab
  regeneration restoration to the original world after dimension transfer.
- Actual21332 Genji Deflect reflected an existing vanilla arrow, killed1HP
  target and reset original Dash8 ->0 once. Inactive/covered/cooldown/model switch
  refused. Original beta3x16-byte corner pairs; MC eye/aim anchor is explicit
  adaptation. Fireball/trident/all-dimension acceptance remains open.
- Real24880 Hanzo150/400/1000ms release: original contextual getter49/75/125HP,
  MC15.1/12.5/7.5; weak normal020b and full0144 same actual Volley, no copied
  formula. Native Gravity9.8 and speed40.6/57.5/90. Config+68 diagnostics never
  proved damage dataflow and are not used. Earlier weak-arrow refusal is resolved.
- Native14608 quick melee all12, original0043 TrackTargets13, live50HP,
  radius1/offset(0,1.5,1.5). Torb needs gun1; hammer separate/pending. Attempts
  with2/3/wheel only proved weapon selector0015, not a hammer attack. Do not call
  unknown node19 an attack: it has count/condition/out_Index fields.
- Mei icicle27448 damage75/gravity0,cover20/open12.5/replay passed. Actual28948 passed cover20/open18.874998/replay/zero rejects. It
  adds original spray resource8be, actual2.25HP/40m/s/life5/range10/type3 factory.
  Its tags0e34/1732 do not by themselves establish freeze semantics; freeze open.
- Earlier7376 Soldier rifle/Helix, Bastion Sentry, Torb alternate, Widow scope
  damage/cover/replay; Sprint/Bastion root/Mei Cryo root/Widow+Hanzo slowdown passed.
- Native28860 Barrage90 actual shots/cost1500/drain0,cover20/open0/replay0,
  primary damage charge feedback passed. Passive5 native points/sec is explicit
  missing-server policy. Native27448 Barrage root92 samples xyzrange0/postwalk
  recovery passed, recording inspected. Pharah Flight/Blink prior evidence below.

Open native Wraith issue: actual Shift enters graph0020/nodes20/18/12/2/3,
Anim3 ends but PhaseOut1/MovementMod5 never Begin. Opt-in scoped Entry/Finish
server-bit experiment17576 failed to advance it; skillMask restored0. A second scoped original TickScript experiment12148 executed19 times, also
failed. Shift-held28948 did not advance it either. Ordinary cold29284 confirmed
skillEntryInstalled=false,skillTickInstalled=false,skillMask=0. Optional scopes
are NOT installed by default; private OWMC_REAPER_ENTRY_PROBE or
OWMC_REAPER_TICK_PROBE flags are required. Gate request OWGATE05/version5/128.
No second owner. Restoration/owner/thread fixture passed. Do not enable by default, force
Finish or guess a speed multiplier. Read-only native callback disassembly in
research/_archive/2026-10/reaper-state2-full-17576.txt. Runtime state indexes are graph.m_states;
logger keys are graph.m_nodes: map via definition pointers, never equate indexes.
No server acknowledgment theory has been proved.

Full12 skills/attacks/1:1 have NOT passed. Junkrat actual primary4832 uses
node31,20m/s/life10, not node30 life3. Ricochet(.5/300 on31 vs.4/12 on30),
Settle(5/.25/1) field semantics still open; do not enable guessed .65 bounce.
Mei freeze/wall/blizzard, Torb hammer/turret/armor, most remaining abilities open.
Native factory deep snapshots and bulky rows defaultOFF, opt-in creation-scoped
calibration only; actual ordered attack journal staysON. User-cancelled added
projectile models/trails and retired replayV2/V3 remain disabled.

Guest27-task build/check (Win64 skill/melee/healing/Deflect/meter guards),
emission/armory/MinHook restoration fixtures,11 binding/28 startup Python tests
and earlier independent HTTP contract passed. Profile backup20261019-020639.zip.
No reset/clean/unrelated commit. See MODLOG and ASSAULT-DEFENSE for actual gates.

## 2026-10-18 latest: original Pharah flight and Tracer Blink verified

**Current state supersedes every earlier PID/running-state paragraph below.**
Native4560, MC23208 and the independent session supervisor are running. The
inspected final native window shows the original animated Pharah picker over
actual MC terrain. Expected phase is hero-selection, ready=false, error=null,
firstPerson=false: waiting for confirmation is intentional. Player is grounded
on natural grass at(-210.7,81,93.63459),20MC HP,alive,creative/invulnerable,F6 flight
OFF. No temporary blocks/targets remain. All4 native owners are enabled with0
failures and loaded artifact SHA256 values match disk; see
research/_archive/2026-10/assault-defense-final-status.json. Startup log:
research/_archive/2026-10/tracer-blink-startup.log. Settings remain1080p/OWLow/8chunks/no shaders/
day-night/Fresh15C,seed-490526775015596785. No new user world was created.

Latest skills requirement means original execution, resources and collision
behavior must be calibrated, not merely simulated on a key press. See
docs/NATIVE-FLIGHT.md and docs/NATIVE-BLINK.md for evidence and explicit limits.
Pharah imports original vertical hover/Jet physics, fuel/timers remain native,
MC resolves blocks. Native4560 ceiling regression passed: feet193 ->196.2,
roof198,horizontal drift0,172 ready samples,cleaned=true. Native resource test
in28968 proved RMB/Space fuel100 ->0 ->100 and original10s Shift refusing repeat.
Exact horizontal air momentum, concussive blast/Barrage remain open.

Tracer Blink now observes the actual original script0024/nodes5/10 teleport in
the existing body owner. A PID/creation/current-model/graph/logger binding is
prepared by the persistent supervisor. No new callback owner or key-derived
teleport exists. Original3 charges/recharge/animation/HUD remain native. MC uses
the observed horizontal displacement and actual block-shape sweep. Real native
4560 test passed: free7.47949..7.47998m,wall stop7.19982m,exhausted press refused,
recharge allowed another native teleport but MC remained against the wall.
Exactly4 native/MC events,cleaned=true. Recording/contact sheet inspected.
Genji ->Tracer ->Pharah ->Tracer retained full MC health and stable position,
reset native capture count on each new Tracer and caused no phantom movement.
Tracer primary damage/cover/replay also passed afterward. Recall/Pulse Bomb and
wider dimension/focus/stall/edge acceptance remain open.

Startup prewarms the existing body/gate/emission observers behind the initial
animated picker. Body pose writes are held ONLY until the first gameplay view.
After that, retain normal MC body authority even in later menus, preventing the
native actor falling in Hollywood while the picker is open. Do not reinstate an
all-menu body pause. Fresh cold startup confirmed Reaper first in27992 and
Tracer first in4560; their actual primary MC damage/cover/replay passed.

The earlier61-selection post-ID-wrap proof in4324 remains valid: the supplied
plugin's first-record-only inline lookup was fixed compatibly by promoting the
current local owners within unordered buckets, preserving all IDs/pointers/
counts. The failed pool-only proof and0/0 pixels remain separately preserved.
Subsequent actual Genji kill reset original Shift to0, another Shift started
normally and replay did not reset twice. Instant full HP on the very first spawn
frame is still unproven; the supervisor corrects the initial169 after binding.

All21 original hero presentation/movement foundations are present. Additional
primary damage/cover/replay is verified for Reaper,Tracer,Bastion,Torbjorn,
Widowmaker, alongside previous Genji/McCree/Winston/Pharah. The12 complete
Assault/Defense kits and1:1 acceptance have NOT passed. Soldier/Mei/Hanzo/Junkrat
attacks, most remaining abilities, generic ult charge, exact falloff/secondary
physics and native VFX remain open. Guessed freeze/lifesteal/projectile defaults
are refused. User-cancelled added projectile visuals remain disabled.

Latest cold artifacts passed7 native body fixtures,22-task guest build/check,
26 startup Python tests and the independent HTTP contract entry point. The
profile backup before tests remains
<USERPROFILE>/.universal-modder/backups/assault-defense-20261018/20261018-183325.zip.
Preserve all pre-existing source changes; no unrelated reset/clean/commit occurred.

## 2026-10-18 earlier: original Assault/Defense abilities and Pharah physics

### Earlier snapshot, superseded by the section above

Earlier native4324, live Minecraft and its independent supervisor were running.
research/_archive/2026-10/assault-defense-final-status.json reports ready=true, zero native body
failures,22 bucket promotions, matching loaded artifact hashes and0 fixture
blocks. Inspected final native PNG: original Pharah,200/200,actual MC grass
terrain. Player is grounded on grass at(-218.2498,129,93.4010),creative/invulnerable
with F6 flight OFF, ready for actual native hover. Settings remain1080p/OWLow/
8chunks/no shaders/day-night/Fresh15C; no new user world was created.

The compatibility fix below passed61 real hero selections across all21 originals
and an actual collided bucket. HUD mirrors agree with native pools; inspected
Mercy shows200/200 after wrap. Subsequent real Genji shots killed an MC fixture,
reset original Shift and allowed a second dash; Reaper primary/cover/replay also
passed after wrap. Data-only failed evidence remains separately preserved.
Current armory primary-only checks passed Reaper,Tracer,Bastion,Torbjorn,Widowmaker
in PID4324; the first Bastion attempt began during original equip lock, then the
settled retry passed. Verification now waits for that native animation.

Pharah resource/ceiling tests also passed after wrap. Space AND right-click
consume native fuel100 ->0 and release restores100. Space raised actual MC feet
118 ->120.8428 with creative flight false. Shift repeats during cooldown do not
create another native action. Latest ceiling: feet104 ->107.20000005,head stops
at roof109,horizontal drift0,cleaned=true. Native clips/contact sheets inspected.

Additional armory admission is deliberately limited to each calibrated primary
resource; secondary/ultimate/melee factories need their own calibration. No
uncalibrated freeze/lifesteal/projectile defaults are presented as original kit
completion. Soldier/Mei/Hanzo/Junkrat attacks and most non-Genji abilities, generic
ultimate charge, exact air control/falloff/secondary physics and native VFX remain
open. Full12-hero1:1 acceptance has NOT passed. See docs/ASSAULT-DEFENSE.md.

**Critical stress finding/update:** the first43-switch test passed native pool
reads but FAILED actual acceptance: inspected Genji pixels show0/0 and subsequent
Reaper firing emitted no new events. Preserve
research/_archive/2026-10/hero-bucket-stress-data-only-failed.json and the collision screenshot.
The provided plugin's inline EntityAdminBase::getEntById also only examines each
bucket's first record; fixing just our readers is insufficient.

A new local_bucket_compat.hpp workaround now runs in the existing native body
owner callback. It promotes the current controller/model records to the head of
their unordered native buckets while retaining every ID/pointer/count. No
provided-plugin binary/code, native function, extra callback owner or retail
client is modified. Typed ownership/header/entry checks and failed-write
rollback are covered by a native fixture. Native engine lookup scans all bucket
members; the permutation makes legacy inline plugin lookup see current owners.
This is being cold-tested with the new body DLL, startup
research/_archive/2026-10/bucket-compat-startup.log. New stress checks original HUD entity-variable
mirrors AND health pools; a pool-only pass must never be accepted again.

The first stress run also captured the existing transient169 HP before the
two-second supervisor initialized full health. It settles correctly, but instant
full-health presentation on the very first spawn frame is not proven.

Read docs/ASSAULT-DEFENSE.md. The user's latest requirement is original skill
behavior, explicitly including Pharah flight. Do not describe approximate MC
physics/status defaults as fidelity acceptance. Uncalibrated Hanzo/Junkrat/Mei
generic profiles are currently refused rather than admitting guessed values.

Genji elimination -> original Shift cooldown reset is implemented and real-tested:
research/genji-elimination-reset-live-result.json passed. A nonlethal hit did not
reset; a real MC kill reset the native remaining timer to0; the next native Shift
began and restored its normal8s cooldown; replay caused no second reset. The test
was in the Overworld, not the earlier End fixture. Temporary targets cleaned.

Fixed a concrete long-session entity lookup defect in Python PoseReader and C++
NativeLocalHero: all records in each native4096-bucket table must be inspected.
The old first-record-only lookup missed controllers/models after low12-bit ID
collisions. Python collision fixtures and the real DLL shared-gate fixture pass;
real long-session/dimension stress remains required before attributing every
prior zero-health/gun-loss failure solely to this defect.

Native armory typed resource/damage/owner profiles now carry actual factory
pellets for additional heroes. Reaper/Tracer/Bastion/Torb/Widow/Soldier profile
preparation is integrated into hero refresh, but individual real damage and
alternate/skill acceptance are pending. Do not claim all12 heroes complete.

Pharah flight currently has a new native physics displacement transport under
test (native_flight.hpp, NativeFlightReader/Controller). It retains original
velocity/gravity while MC resolves actual block collision and reports blocked
axes. Original fuel, hover activation and Jump Jet cooldown remain native.
F6 creative building flight bypasses this channel. Initial standing real run
reported flight.ready=true and stopped correctly at ground. Full jet/hover/
ceiling/dimension evidence is pending. Native oracle with restored body writer:
research/pharah-native-flight-oracle.json. Avoid another callback owner.

Update: read docs/NATIVE-FLIGHT.md. Actual open-air and ceiling tests now pass
on PID31368, both with0.0 horizontal drift and cleaned fixtures. Original fuel
100 ->0 ->100 and Shift0 ->10, refused repeat with the same native action tick
also passed. Horizontal movement retains the existing reflected-speed/input
adapter because the supplied native mover drifted after Jet. Do not claim full
horizontal physics or dimension acceptance. All-hero switching stress is active.

Actual primary damage/cover/replay checks passed Reaper,Tracer,Bastion,Torbjorn,
Widowmaker. These are weapon-channel slices, not complete kit/falloff/trajectory
fidelity. Soldier primary is a complex original amount expression and currently
refuses admission; inspect its script0254/node25 rather than assigning a guessed
damage. Generic status/lifesteal placeholders were removed. Reaper's older
standalone passing result was overwritten by the first multi-hero test and is
being recaptured; the test now preserves individual hero records.

The latest full build/check passed21 Gradle tasks, original emission lifecycle,
shared gate/entity-collision fixture, body/native flight accumulator, native
armory owner guards,26 startup tests and the independent Java HTTP contract.
Current startup research/_archive/2026-10/pharah-flight-startup.log; read live status/processes,
because all PIDs in historical notes are obsolete. Keep only exact guarded exe.

## 2026-10-18 latest: Pharah primary damages terrain

Read `docs/NATIVE-PHARAH.md` for the native primary calibration and real acceptance.
Primary script0023/node10/resource0033 now supplies factory-confirmed kind3 rockets
at35m/s; MC owns swept collision, calibrated40+80 damage and vanilla terrain blast.
Real test: ammo6->5, stone23->22, both protected blocks survive, nearby target
20->14.785919 and outside target stays20; replay changes nothing. Independent
direct hit20->8 also passed. Inspected actual recording/contact sheet; fixtures
cleaned. Latest launch log is `research/_archive/2026-10/pharah-release-startup.log`; read current
session status rather than reusing the test PIDs. Same1080p/OWLow/no shaders/
8chunks/day-night/Fresh15C profile. Added projectile visuals remain cancelled.

Final readiness snapshot: `research/_archive/2026-10/pharah-final-ready.json` and inspected PNG.
Native21672/MC27340 were live, ready=true, original Pharah in first person,
grounded/flight-off,20MC HP,0 fixture blocks, no feed error; loaded artifact hashes
match files on disk. Both games and their persistent supervisor are left running.

The generic21-hero camera/body/health foundation below is present; MC combat is
now calibrated for four heroes, not all21. Pharah/Reaper native attack audio was
captured; do not add duplicate fallback sounds to those working native attacks.
Other weapons/audio remain open work. Previous unexplained client exits had no
matching native Application crash event in the inspected window; cause is not
established. Do not attribute them to the user without evidence.

## 2026-10-18 current work: remove projectile visuals, expand beta hero roster

User cancelled the added projectile model/spin entirely and prioritized all
remaining heroes, then requested missing attack audio from current local retail
assets. OriginalProjectile* runtime/classes/registration have been removed;
`presentationMode=disabled-by-user` preserves existing simulation/damage only.
User's unattended input/launch/test authorization persists.

Active work (not full acceptance): native metadata on PID15268 confirmed all21
STUFirstPersonComponents, actual45/50/53/55/60/65FOVs and1.0..1.82 eye offsets.
Body binding now reads the actual reflected camera definition, rather than only
three hard-coded heroes. Added45/65degree mask recognition excluding70degree
world camera. Shared native Volley gate follows actual local model ownership
and valid script resource type, retaining execution-bit and owner-thread guards.
Health/locomotion preflights now allow the verified21-hero roster; non-Volley
heroes can be observed without inventing a Volley graph. Native damage event
calibration still covers the original three only; additional weapons/audio are
in progress, not completed by these changes. Keep that distinction explicit.

Backup: <USERPROFILE>/.universal-modder/backups/all-heroes-20261018/20261018-173748.zip.
Current diagnostic launches use `research/heroes-foundation-startup*.log`.
Do not use the older native/module process IDs below as current evidence.

## 2026-10-18: user rejected substitutes; original Genji model with spin

**Supersedes the custom projectile presentation below.** User explicitly rejected
the procedural three-blade model and MC tracer/beam particles, then authorized
OWLib extraction from their own current retail installation, followed by unattended
input tests. These substitute classes/particles have been removed from the jar.
Read `docs/ORIGINAL-PROJECTILES.md` for provenance, reproduction and evidence.

Local retail build154088 supplies the actual 7CA -> 29F9 shuriken model, original
vertices/UVs/size and albedo/emission textures through a private SHA256-verified
asset pack outside the repo. OriginalProjectileRenderer draws those assets and
interpolates per-projectile self-rotation. Spin is currently adapter-tuned at6rps,
not measured native angular velocity. Full original effect graphs, trails,
impact effects, OW PBR/bloom and other heroes' world effects are still pending.
No native callback module changed; native hands/HUD and combat admission remain.

Guest build/all checks,37 Python tests and the independent HTTP contract passed.
Inspected actual spin recording/frame sheet: three controlled native shots hit
the fixture,20 ->9.5HP; replay caused no extra damage. Fixtures cleaned,0 active
visual entities. Both games/supervisor remain running; use
`research/_archive/2026-10/original-spin-final-result.json` and current session status for identity.
Settings remain1080p/OWLow/no shaders/8chunks/day-night/Fresh15C. No retail game
process was attached or modified. User authorization to operate autonomously
persists; don't ask them to manually fire/select heroes for routine tests.

## 2026-10-18: projectile presentation iteration, not full hero acceptance

Read `docs/HERO-EXPANSION.md` for the current hero matrix and verification limits.
Native callbacks remain compositor29/body10/weapon8/emissions11. The guest now
has a registered transient projectile visual entity/renderer, hit-clipped tracer
and bounded beam presentation driven only by admitted original events. This is
adapter geometry, not the extracted original projectile model. Build/check and
32 Python startup/diagnosis/catalog tests passed. After the user approved live
input testing, Genji firing was verified in the actual composed native window:
three shots hit the temporary wall without damaging the target; three unobstructed
shots reduced its health from 20 to 9.5. Replaying an event added no damage or
entity. A 60-FPS recording and cropped frame sheet show the flying three-blade
entity. Removed an oversized END_ROD trail found during this test and scaled
the visual to 0.35. Evidence: `research/_archive/2026-10/live-fire-projectiles-fixed.mkv`,
`research/_archive/2026-10/projectile-crop-sheet.png`, `research/_archive/2026-10/live-fire-final-result.json`.
Temporary target/wall were cleaned up; the inspected final screenshot is
`research/_archive/2026-10/live-fire-clean-final.png`.

The new read-only `tools/native_hero_catalog.py --pid <verified-pid>` found 21
actual hero names in this machine's PID26908, with matched DLL/PDB identity.
Only Genji/McCree/Winston have calibrated combat adapters. Other original hero
resources and some Volley graphs exist, but their damage, ammo, abilities,
viewmodel masks and dimension transitions are not implemented/accepted.

Settings: 1080p, OW Low, no shaders, 8 chunks, day/night cycle, original Fresh15C
save. `tools/diagnose_native_combat.py` inspects layers without firing or loading
hooks and treats hero selection as an expected stage. At the end of the approved
test the native PID was 31656, MC PID 18364, ready=true, Genji in first person in
the saved End dimension. Both games and their supervisor remain running. Backed
up the profile again at `<USERPROFILE>/.universal-modder/backups/hero-projectiles-20261018/before-live-fire/profile.zip`.
Do not infer current process identities from older entries below; read the live
session status. Live firing acceptance here covers Genji primary fire only,
not other heroes, all abilities or dimension-switch regressions.

## Current: fresh 1080p world at hero selection

Current live processes are native Overwatch PID7060 and Minecraft PID26720.
The launcher is intentionally waiting at the native animated hero-selection
screen (`phase=hero-selection`); it has not entered a hero's first-person view,
so the startup Low profile has not yet been applied to the native renderer.
The world is newly generated as `Overwatch Seed World Fresh 15` with seed
`-490526775015596785`, natural creative mode, fixed noon and 15 chunks. Runtime
health reports full-world frame transport, 37,861 published frames, no guest
errors and a connected host pose. Settings are 1920x1080, MakeUp low shader and
Overwatch Low. Evidence: `research/_archive/2026-10/fresh-world-selection.png`.

The previous `Overwatch Seed World Fresh 12` save and launcher settings were
backed up before creating the new save at
`<USERPROFILE>/.universal-modder/backups/owmc-lighting-restart/`.
The native Low profile now uses DynamicAmbient=1/SinglePointAmbient=0, and the
live compositor first-person exposure is 1.15 (down from 1.30). Build and GPU
mask tests pass; McCree's in-game view still needs visual confirmation after a
hero is selected. A cold stop/start cleared the old process and frame caches.

## Current: 2K seeded world, shader option and persistent OW Medium profile

The current live session is native PID 19184 with Minecraft PID 21220. It cold
created `Overwatch Seed World 2K` as a natural creative world from seed
`-490526775015596785`, then restarted and reopened that saved world. The live
status reports `worldKind=creative-natural`, fixed noon (`timeOfDay=6000`),
16-chunk view distance, healthy composition and zero module failures.

The persistent profile is now MC 2560x1440 (2K), Iris MakeUp UltraFast 9.5g
shader low, and Overwatch Medium. The launcher applies the verified native
profile at startup (`AADetail=1`, `LocalFogDetail=2`,
`DirectionalShadowDetail=1`, `DynamicAmbient=1`, `SinglePointAmbient=0`) and
records the readback in `research/session-status.json`; no original game config
file is rewritten. The GUI and CLI expose both the OW profile and the new-world
seeded creation path.

Real screenshots `research/_archive/2026-10/new2k-selection.png` and
`research/_archive/2026-10/final-2k-low-medium.png` show the animated native Genji picker and
first-person hand/HUD over the new MC terrain. The final 15-second bounded
2K+low-shader measurement averaged 93.18 distinct composed FPS with zero held
or unmasked frames; the earlier 2K+medium-shader run averaged 96.10. This
combination is visually working but does not meet the former 180-FPS target.
The faster 1080p/no-shader profile remains available through the settings tool.

## Current: HUD masking, vanilla boss bar, shaders and QHD option

The current route keeps H change-hero availability hidden through the verified
native flag only; the broad screen restore mask was removed, so F1 hero details
and the ultimate control remain native. MC's own `BossBarHud` pixels are copied
to the optional screen-space overlay, preserving the vanilla Ender Dragon name,
font, animation and purple bar. The earlier generated GDI bar is no longer used.

Iris 1.8.14-beta.1 for MC1.21.1 and MakeUp UltraFast 9.5g are pinned behind the
settings tool (`off`, `low`, `medium`); the default is off for performance. MC
uses a natural creative world with seed `-490526775015596785`, fixed daytime,
16-chunk view distance and reduced clouds, particles and entity shadows. Genji
climb is bounded to the existing six-block/30-tick adapter behavior.

The frame mapping was versioned to protocol2 and QHD capacity (2560x1440), with
the live compositor changing to v29. QHD real-play evidence averaged175.5
distinct composed FPS (minimum half-second window162.2), below the requested
stable180. The stable default remains1920x1080: the corresponding evidence
averaged210.0 FPS with minimum window191.9, zero held/unmasked frames. The
configuration GUI now exposes 1080p/1440p and 16..32 chunk choices. These are
bounded measurements, not a guarantee for every map or future shader choice.

## Current: Hollywood map audio removed with bootstrap8

**Supersedes all runtime/module statements below.** Native26592, MC2368,
supervisor exec75402, Genji ready=true, modules8/1/26/10/8/11. Normal grounded
creative/invulnerable/full20HP at(-538.6989136893663,73,-363.69999998807907),
flightfalse. This turn created no temporary blocks/entities. Final state:
research/_archive/2026-10/hollywood-quiet-final-ready.json. Original15736/MC8900 were normally
stopped/restored/saved before the new cold startup.

Bootstrap8 removes Hollywood's environment SoundSpace and37type12sound
placeables before original resource fixups. Exact0x320header fingerprint;
only20bytes differ. Sky, light probes, entities, geometry, native hero and weapon
resources are retained. Reports mapsQuieted1,mapFailures0,phase3,restoredtrue.
No global audio setting was changed. Original-process8s idle recording before
RMS0.0058907, settled after RMS2.449e-10/peak6e-10 (numerical silence). The first
post-selection capture contains fading startup/hero audio; do not confuse it
with the later settled result. See docs/MAP-AUDIO.md for evidence and scope.

Fresh one-click startup initially hit Windows module enumeration
ERROR_BAD_LENGTH before attachment. Launcher now retries only that condition,
10attempts maximum/50ms delay; other failures immediately abort. Relaunch safely
adopted26592 and completed.23launcher tests pass, including finite retries.
New bootstrap DLL/request version8; launcher, attach and environment checks agree.
Private CascLib was rebuilt with this PC's compiler; the previous E: archive had
an incompatible CRT import. casc_read_local.cpp now supports optional bounded
--prefix (<=16MiB) for files<=256MiB, still offline24919/read-only/no overwrite.

Fixture map_audio_data_test passes800single-byte corruption rejections,
wrong-map/reapply rejection and byte-for-byte preservation outside20bytes.
Real video research/_archive/2026-10/hollywood-quiet-verified-heroes.mkv shows native McCree,
Winston, Genji picker/entry animations, weapons/HUD and firing over MC. Its
contact sheet hollywood-quiet-heroes-sheet.png and all3picker screenshots were
visually inspected. Verified native IDs42/9/29, zero emission failures;
Winston32beam intervals. Audio RMS0.022403/peak0.317078 with quiet intervals
between sounds. Do not use the earlier hollywood-quiet-three-heroes capture as
hero-switch proof: its very short H tap was missed; all3labels were still Genji.
Corrected drive holds H150ms and waits600ms before clicking; actual IDs verified.

20s real final-composition test:186.754FPS;39windows minimum163.107, below150=0,
heldFrames1, unmaskedFrames0. Evidence hollywood-quiet-perf.json. This bounded
result is not a zero-stutter or all-map guarantee. Earlier this turn no-audio
frame recordings were not substituted for the original-process audio capture.

Backup after stop/save: <USERPROFILE>/.universal-modder/backups/
owmc-map-audio/20261016-081306.zip (72,286,072compressed bytes,151files). Initial
backup while MC was live failed on a locked file; the completed stopped-profile
snapshot is the usable one. No archive resources were overwritten.

Goal still active: native daytime illumination remains Hollywood plus existing
mask gamma, not an MC light transfer; remaining hero abilities/temporary health,
climb motor fidelity, F1 help and sustained/user acceptance remain outstanding.
Hollywood ambience is now scoped/verified above, not the older pending status.

## Current: McCree roll motor, direct hero startup and emission11 verified

**Supersedes all runtime/version statements below.** Live native15736, MC8900,
supervisor exec97708, Genji ready=true, modules7/1/26/10/8/11. Latest guest jar
contains NativeRollReader/Controller/Phase and the disconnect-rebase correction.
Feet(-538.6989137,73,-363.69999999), grounded on natural birch leaves, flightfalse,
creative invulnerable/full20HP. No temporary blocks/entities remain. Final evidence:
research/_archive/2026-10/roll-emission11-final-ready.json, roll-emission11-final_small.png.

McCree roll is now actual MC movement driven by original1f0/node4 Wait Begin/End.
Typed native speed0670=15m/s, timeout=.4s. Exact movement expressions8/11 and their
source owner/paths are validated. Reader correlates native action timestamps,
checks process/model/script ownership, and rejects stale/changed data. Direction
is latched from original camera/host directional intent only after native Begin;
it is not an evaluated native output vector. MC retains gravity/block collision.
Flight, vehicle and fluid travel do not use this override. See NATIVE-ROLL.md.

Actual16892/MC17092: forward, backward and diagonal roll intervals each6.0000MC
blocks; wall test stopped after0.8900blocks, extra Shift taps in cooldown did not
start another roll. Winston isolation preserved exact XYZ and counter; switching
back rebound a new McCree model and rolled again. Native hand holster/recovery and
cooldown were inspected in mccree-roll-motor-open-sheet.png.340air-only test blocks
were cleaned, callbacks restored and MC saved. Backup is
<USERPROFILE>/.universal-modder/backups/owmc-roll/20261016-074126.zip
(44,214,173compressed bytes). Do not use the attempted nonexistent
minecraft-1.21.1/guest-passthrough-client path; actual profile is workspace-root
guest-passthrough-client. All target fixtures were also removed in later tests.

Startup investigation found three old first-hero limitations:
1. Initial health wait only supervised after Genji-specific channels passed.
   It now enters the persistent loop after hooks connect and rebinds/retries the
   current hero there. Missing Genji-only channels still report ready=false for
   Winston/McCree, honestly; they no longer terminate the supervisor.
2. Body attach precheck required only weapon0304. It now validates supported
   hero, matching base graph and component owners; allows extra skill graphs
   (McCree also has01e9), matching the already-three-hero native body10.
3. Emission10's initial request guard only allowed Genji projectile07ca despite
   live rebind supporting all three. Emission11 uses the same exact hero/resource
   validator for startup/rebind; wrong initial pairs report inactive/restored
   failure. Guest accepts producer11, protocol still3, request stillv4/168bytes.
   No callback or damage semantics changed. Build/lifecycle fixture and all valid/
   crossed pair tests passed. Never overlay11 onto a process with10 mapped.

Failed10928 had emission10 mapped but its worker returned at the old request
guard before hooks/events/report. Its body/weapon/compositor were restored by
normal stop, then the process terminated and MC saved. No re-injection occurred.
Fresh19536 selected McCree FIRST on emission11, automatically initialized200HP,
bound roll and kept supervision beyond20s. Two shots hit a real MC target20->6;
actual HUD ammo6->4, then original roll restored4->6, cooldown8. Final-source
phase reset was loaded. Native19536 was normally stopped/restored/saved.
Fresh15736 selected Winston FIRST, initialized400+100HP, and native600ms beam
damaged a real MC target20->16.351988 (31intervals,1Begin/End,0failures). Switching
to Genji then hit a fresh target20->9.5 with3native projectiles and ready=true.
Evidence emission11-{mccree,winston}-first-selection.json,
emission11-{mccree,winston,genji}-live-hit.json, roll-final-source-cold-check.json,
mccree-roll-ammo-{before,after}_small.png and roll-emission11-final-ready.json.

Native roll phase and actual Win64 reader fixtures pass (idle/reconnect baseline,
original Begin/End/action correlation, owner/creation/NaN guards,6m cap/diagonal).
Full guest build/check, native emission lifecycle/restoration,21launcher,5health,
7performance tests pass. The sampler now retries brief Windows report-file locks
within250ms, records retries and rejects stale reports; it never restarts a game
or substitutes an old sample. One pre-fix sampling attempt failed on a file lock.

16892 McCree20s:187.26distinct composed FPS,38windows minimum172.15, held0/unmasked0.
Final15736 Genji forest15s:193.45FPS,28windows minimum177.04, held0/unmasked0.
Both had0windows below150. Evidence mccree-roll-motor-perf.json and
roll-emission11-final-perf.json. These are bounded report windows, not1%lows or
indefinite/map-independent guarantees. Goal remains active: native daytime
illumination, Hollywood ambience, remaining hero abilities/temporary health,
climb motor fidelity, F1 help and sustained/user acceptance remain outstanding.

## Current: body10, original creative health pools, successful cold startup

**This supersedes all runtime/version statements below.** Current native8828,
MC5048, supervisor exec44285; ready=true, Genji, modules7/1/26/10/8/10.
Feet(-544.1079366,71,-363.8100000), grounded, creative invulnerable, flightfalse.
No temporary blocks/entities remain. Backup before the body10 fixtures:
<USERPROFILE>/.universal-modder/backups/owmc-climb/20261016-072218-body10-health.zip
(44,203,687bytes), containing the correct guest-passthrough-client save.

The launcher now initializes all three heroes' original base health pools once
per model recreation, reading typed native HealthPool configuration instead of
hardcoding hero values. Genji/McCree200, Winston400normal+100armor; original HUD
and automatic switch initialization verified. Only each base slot's12bytes are
written; extra active pools are refused, metadata preserved, owner/configuration
checked and failed writes rolled back while the owner is unchanged. This is
creative initialization, not damage/regeneration/Primal Rage support. See
NATIVE-HERO-HEALTH.md and tools/native_health_binding.py.

Final startup21372 exposed a new guard defect: script+150 is a resource ID, not
a user-space pointer. Fixed it to read a raw64-bit ID. The failed supervisor
was safely replaced, adopting healthy hooks without reloading; then21372 was
normally stopped/restored and MC saved. Fresh8828 automatically initialized
Genji169->200 and reached ready=true; an independent check-only read confirmed
200/200. Evidence body10-final-cold-ready.json, native-health-fill-8828.json and
body10-final-cold_small.png. All5health and21launcher tests pass.

Body10 fixes presentation ground/air flags using the same owned bit mask as the
mover. Original TrackMovement10aa870 publishes airborne to+108/entity1a1 and
grounded to+110/entity0221; older notes calling1a1 grounded are incorrect.
Climbing retains the appropriate air flag plus80 (88/85), and mode8c remains
scoped. Native rollback/field-preservation checks pass. Real6760 recording
climb10-platform-contact.mkv still shows alternating native climbing hands and
6blocks of MC rise; all49air-only fixture blocks were cleaned before stop/save.

Grounded entity0221 also enables the original McCree roll graph1f0/node2. On
actual6760, heldShift produced node4 and9 Begin20096/End20496 (400 native units),
node11 movement action and node15 animation; original HUD cooldown8->7. Evidence
mccree-roll-grounded.mkv/.json/-sheet.png. **MC feet did not move: roll displacement
is still unimplemented.** Body9 baseline never entered those states.

Repeated-climb15s:189.93distinct composed FPS,29windows minimum170.87, below150=0,
held0/unmasked0. Fresh8828 cold15s:192.93FPS,28windows minimum170.87, below150=0,
held0/unmasked0. Evidence body10-climb-perf.json and body10-final-cold-perf.json.
These bounded report windows are not individual-frame or indefinite guarantees.

Next roll work: observe original1f0/node4 active Begin/End, not raw Shift. Node4
m_timeout=.4; node8/11movement expressions use scriptlocal0670=15. Node8 uses
native throttle/forward/left; node11 is forward fallback. Decode directions before
implementing MC displacement, retaining MC collision/gravity. Never broaden
NativeDashController.heroReady to McCree: it also gates Genji wall climbing.
Private evidence graph-05800000000001f0-23620.json, mccree-roll-expressions.json,
mccree-roll-variables.json; research/_archive/2026-10/inspect_graph.py and test_roll_live.py.
Remaining: full hero abilities/temporary health, climb motor fidelity, daylight
native illumination, Hollywood ambience removal, F1 help and sustained acceptance.
Hollywood remains the user-authorized fallback; the full goal stays active.

## Current: body9 original climbing hands verified; cold startup repaired

**This supersedes the body6 production statement below.** Current native23620,
MC23080, supervisor exec49667; ready=true, Genji, modules7/1/26/9/8/10.
Feet(-544.1070,69,-363.5510), grounded on birch leaves, creative invulnerable,
flightfalse. All test blocks/entities cleaned before the final cold startup.
World backup before fixture work:
<USERPROFILE>/.universal-modder/backups/owmc-climb/20261016-065618-body9-wall.zip
(44,110,517bytes). Earlier064627-body8.zip is also the correct passthrough save.

Body8 was insufficient: mode2/flag80 on the two mover histories did not reach
the actual animation predicate. Read-only inspection found original
TrackMovement10aa870 reading component12+A060 via context getterd14af0.
Body9 additionally sets ONLY flag80/mode8c on that presentation state, preserving
other flags, vectors, profile IDs and history. Optional CLM2 body extension is
same-tick Genji model-identity guarded; stale contact clears, and hero changes
rebind original component owners. See NATIVE-CLIMB.md for the exact contract.

Actual native25048 climb9-platform-contact.mkv shows original alternating hands
over a temporary MC stone wall,6blocks of MC movement, and normal recovery.
147trace samples include28MC-active,28original04b4=true and28originalAnim40-active
samples. McCree/Winston W+Space did not increase MC or native climb counters;
returning to Genji worked (climb9-genji-return.*,31nativeAnim40-active samples).
The49air-only fixture blocks were restored before normal stop/save. Motor
speed/rise limits are still adapter settings, NOT proven original constants.

Repeated-climb20s performance:189.42distinct composed FPS,38report windows all
>=150 (minimum169.88), held0/unmasked0. Final cold-run15s:193.74distinct FPS,
28windows all>=150(minimum178.29), held0/unmasked0. Evidence
research/_archive/2026-10/climb9-repeated-perf.json and climb9-final-cold-perf.json. These are
bounded report-window tests, not all maps or individual-frame/1%low guarantees.

During one intermediate startup, stationary water travel bypassed the movement
injection and left locomotion readiness stuck on an earlier missing camera.
NativeLocomotionController now polls once per player tick from the normal client
tick as well as sharing that cache with movement. The final cold run selected
Genji and reached ready=true while fully stationary at the same water location;
research/_archive/2026-10/climb9-water-cold-ready.json records this. No movement input was needed.
Moved to the current leaf platform afterwards. Final screenshot and health:
research/_archive/2026-10/climb9-final-cold_small.png, climb9-final-cold-health.json.

Native body rollback/field-scope checks, all guest checks and20launcher tests
pass. body9 remains the loaded/versioned artifact. The diagnostic field is now
nativeAnimationRequested (contact intent), not a hardcoded native verification
claim. Build and launcher versions all agree. No game binaries are committed.
Remaining: native climb motor fidelity/mantle, full Winston/McCree abilities and
health/armor, actual daylight native illumination, Hollywood ambient removal,
F1 help polish and broader sustained acceptance. The goal remains active.

## Latest investigation: climb7 rejected, production stays on body6

Cold test23972 used compositor26/body7/weapon8/emission10 with the ordinary saved
world. The candidate appended a CLM1 contact extension to the existing256-byte
body packet and wrote WallMove bit80 plus XYZ at MovementState+70. Native/guest
builds, malformed packet guards, write-failure rollback and20 launcher checks
passed. Actual recording **did not show climbing hands**: the shuriken idle pose
remained throughout. Native script0157/node9 entered on held Space and finished
on release, and36 body ticks accepted the extension, but this is insufficient
animation evidence. Do not promote or reuse body7 as verified. All its production
source/manifest/guest changes were explicitly undone, the guest rebuilt with all
checks passing, and23972 stopped with all adapters restored and MC saved.
Private candidate sources/tests remain in research/climb7-candidate; actual
video/trace/contact sheet are research/climb7-contact.* and climb7-contact-sheet.png.
The recorder trace overwrites the recorder's small JSON metadata, not its MKV.

The test used an existing birch trunk, changing no blocks or entities. MC rose
1.2blocks then hit the natural leaf ceiling; held input repeated after landing
(three starts, total3.6blocks). This is a ceiling/rearm observation, not native
climb fidelity. Grounded final feet(-562.0348,68,-309.7). Saved pretest archive:
<USERPROFILE>/.universal-modder/backups/owmc-climb/20261016-063237-passthrough.zip
(44,170,197bytes). Earlier063155.zip contains a different old lab profile and is
NOT the current-world backup.

Read-only findings for follow-up (rebind addresses to the current process):

- Original Genji graph0580000000000157 has node9 STUStatescriptStateWallMove,
  enabled by node67 LogicalButton42 -> node10 BooleanSwitch (!dynamic0543).
  Client factory10a6980 creates vtable15e6b80, Update10ad3e0; server factoryd9a770
  creates15e6588, Updated9ae30. Client Update reads MovementState flag80 and XYZ70,
  then publishes dynamic04b7. Entry itself does not prove physical climbing.
- Native10b2e60 enables bit80, sets mode8c=1 and copies a frame to80;
  10b2e90 clears bit80/mode8c and resets80/84/88/70. Functions10b47b0/10b4bxx
  also require profile identifier88 and richer state. XYZ70 semantics are NOT
  proven to be a surface normal; do not write an inferred normal there again.
- The WallMove node's embedded STUWallMoveProfile array (field846a3348) has
  one90-byte profile,18ConfigVar pointers. Among values are upward vector(0,1,0),
 4.5,.2,1.5,.5, but their unknown field names/roles must not be guessed.
- Node11 typef6e1e486 has named m_climbSpeed=7.5, but it reads separate flag20
  and the larger MovementState90 record (requiresCC=1), publishing ledge-related
  position/height variables. It may be a different mantle mechanism: **7.5 is
  not established as Genji's sustained wall-climb motor speed**. Leave adapter
  constants explicitly labeled until native behavior is established.
- Tools research/_archive/2026-10/inspect_climb_graph.py, inspect_climb_fields.py and
  test_climb_live.py preserve bounded read-only graph inspection and short
  actual input/recording procedures. native-climb-graph.json is from stopped11196.

Production baseline restored: native28344 / MC12872 / supervisor exec19806,
ready=true, Genji model2147485825, modules7/1/26/6/8/10. Walked back from the
trunk to feet(-562.0335,68,-304.03), grounded, health20, no blocks/entities changed.
Actual screenshot climb7-baseline-restored_small.png confirms normal native hands
and HUD over MC. Post-restoration15s check: distinct195.84FPS, native238.43,
MC221.87;29 report windows all>=150 (minimum176.36), held1, unmasked0. This is
a bounded idle restoration check, not a new all-hero play acceptance. Evidence:
research/_archive/2026-10/climb7-baseline-restored-perf.json and -health.json.20 launcher tests
passed again after reverting the candidate. Original broader baseline below
remains authoritative for performance and weapons. Revalidate PIDs before work.

## Latest: all three heroes exceed150 FPS in measured play (compositor26)

Current native11196 / MC27216 / supervisor exec75752, Genji first person,
ready=true, model2147486052. Modules7/1/26/6/8/10; emission requestv4/168,
guest protocol3. Settings capture240/host240,1920x1080 MC input, original native
window2560x1440. No test entities left, no terrain edits. Player remains grounded
in the same natural creative save. Revalidate identities before further work.

Final actual distinct composed-frame measurements (not repeated native presents):

| Hero | Duration | MC FPS | Native FPS | Distinct FPS | Minimum report-window FPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Genji |39.7s|220.22|237.95|194.88|172.15|
| Winston |39.7s|220.38|238.41|192.14|166.34|
| McCree |29.9s|220.84|238.42|193.68|172.82|

All212 windows (0.512..0.520s each) exceed150; all three intervals held0 and
unmasked0, including view turns, native firing/fan/reload. These are bounded
current-map tests, not per-frame1% lows or a guarantee for every future map.
Native startup/selection transitions still have separate held/unmasked counters.
Measure script now reports minimum/under150 report windows and rejects a session
change in the middle of a measurement; six meaningful counter tests pass.
Evidence: research/_archive/2026-10/passthrough26-three-hero-performance-summary.json and its
three source reports. Capture200 had173/170 averages but one Winston window148,
so capture240 is the selected configuration. Do not revert to200 as proven stable.

Original animated Winston foreground over MC was recaptured in two different
poses (passthrough26-winston-picker-a/b). High-FPS native576ms beam still gave
both4m/6m targets3.456 damage;9m/30-degree targets stayed20 and release stopped
damage. All targets cleaned. See emission10-winston-highfps.json.

Native limiter and compositor restoration actually verified on26936: all four
adapters restored, failures0, original float read back100 before process exit,
MC saved. See passthrough26-restoration.json. New11196 cold restart re-applied
the guarded cap successfully. The source-copy optimization and native limiter
are in the one-click launcher version manifest, not temporary experiment scripts.

Next remaining goal work: original daylight/model lighting and Hollywood ambient
audio, full Winston/McCree abilities/ultimates and health/armor, native Genji climb
animation, F1/native YOU hint and longer play acceptance. Do not mark the full
goal complete from these FPS/base-weapon results. Read-only health investigation:
provided player_spawner.cpp explicitly seeds every hero169/200; health component
normal/armor/shield parts at98/1d8/318 with20-byte stride. Winston metadata health
componentaebe9baa has arrayd41f925b of2dd559af entries; its loaded resource05c15
is typea526b6ea with one float2.0, **not proven max health**. Resource reference
0da0d is unloaded. Do not guess400/100 or write these unknown values. Private
native_health_definition.py / native-health-definition-2e0000000000009.json;
they are diagnostic only and runtime pointers belong to stopped26936.

## Previous: compositor26 preparation and restored compositor25 baseline

Native26720/compositor25 and MC stopped normally; original native limit read back
as100 after restoring four adapters, failures0. Evidence passthrough25-restoration.
New compositor26 built and launcher exec40443 is starting (recheck new PID).
Current settings capture200/host240. NativeFrameLimit validates both actual native
float-load instructions, override-1/background60 and writable data page, atomically
owns100->240, restores100 on render-thread stop, refuses external changed values.
The offline loader uses RWX for this data section; v24 wrongly refused it and is
retired. No executable bytes or page permissions changed. v25 actual cold passed.

Actual25:30s baseline MC184.85/native237.76/distinct161.06, held0/unmasked0;
50s with turning/walking/jumping/throw/reload MC186.26/native237.39/distinct169.23,
held1/unmasked0. Average now exceeds150, **not a stable minimum**: half-second
baseline windows dipped to133.72. Source200 target still loses frames between
MC publication and native CPU acquisition. Screenshots retain actual Genji/MC.

Compositor26 removes the redundant full-frame temporary pixel buffer: decode
directly into owned output, then revalidate producer sequence/generation. Race
fixture caught compiler rereading descriptor bytes; an explicit memory fence
after descriptor copy fixes it. Concurrent1280x720 mapped producer80 frames is
checked for whole-publication identity and retained output ownership. Frame wire
and GPU tests, live/selection restoration tests, native frame-limit ownership
tests and20 launcher tests passed. Actual26 performance not yet measured.

## Latest: Winston continuous MC damage verified; actual 100 FPS limiter found

Current native7412 / MC19148 / supervisor exec89946, returned Genji ready=true,
model2147486045. Modules7/1/23/6/8/10, requestv4/168 and guest protocol3.
All test entities removed, no terrain changed. Native24188(emission9) and4980
(emission10) restored all callbacks and MC saved before restart. Revalidate IDs.

Emission10 transports native Winston ChaseVar Begin and Finish/Abort, original
clock, radius8, full cone40 and damage60/s into MC multi-target block-occluded
damage. **Correction to older notes: vtable+118/f53200 is re-entry, NOT End.**
Actual Begin is+110/f531f0; Finish/Abort is+158/f53270 (provided Statescript.h
and live native disassembly). Emission9 incorrectly kept dealing damage after
release and is rejected. Never load it. Emission10 fixes the actual path and
restores both original slots; no button-derived attacks or new native entities.
Per-interval owner/phase/tick keys retain exactly-once ACKs. Native ammo baseline
limits duration; stale world/pose and long sampling gaps drop old damage.

Actual4980: 576ms phase ->3.456 MC HP, HP already decreasing in25 sampled rows
before native finish; idle after finish unchanged. Short input generated48ms
native phase ->0.288HP. Natural leaf occlusion:29 intervals blocked, target20.
Full100 ammo:5s phase then stop, even while input held5.4s; target behind leaves
stayed20. Begin/End4/4, rejected0/failures0. Actual7412 cold restart:4m and6m
targets each20->16.543991 together;9m and30-degree targets stayed20. Replay
unchanged. McCree20->13 and Genji20->9.5 after hero changes. New explicit local
POST /combat/test/beam creates four removable stationary test targets, refuses
occupied sites, never changes blocks. See research/emission10-winston-*.json,
emission10-mccree-regression.json, emission10-genji-regression.json. Full guest
checks/native journal+phase+real-MinHook fixtures and20 launcher tests passed.
Winston original target arcs, health/armor, skills/ultimate remain unfinished.

FPS breakthrough: bounded native thread samples found main thread7724 spinning
at7e7751..7e777f in native frame controller7e7660, reading float100 atRVA179f130.
Render thread3892 mostly waits at9380dc. Actual float loads at7e76d5 and7e75f9
prove the target; override179f138=-1, background179f13c=60. This is separate from
client.MaxFPS and absent from INI registry. Private thread-samples-7412.json and
winston-functions-7e775e.json contain evidence. sample_native_threads.py briefly
suspends exact verified native threads, ALWAYS resumes in finally; one sample
unavailable, max pause1.084ms. It is diagnostic and not a production dependency.

Temporary exact-guarded100->240 experiment, restored100 with readback: host165
now164.88 FPS, MC154.43, distinct142.93. With temporary presentation240:
host235.48, MC152.61, distinct146.86. All held/unmasked0. Source165 target is
actually~154 and asynchronous sampling loses some source frames. **150 distinct
FPS still not met**, but native100 bottleneck is proven and removable. Both
engine100 and presentation165 restored. Next: increase MC capture headroom and
integrate bounded/restorable engine cap into native lifecycle, then cold/sustained
test. Current v23 still runs100 until that change. Full active goal unchanged.

## Latest: Winston native timing calibrated; client cap experiment rejected

Current native28580 / MC2792 / supervisor41993 remain live; returned to Genji,
ready=true, current model2147486126. Same7/1/23/6/8/8 modules and guest protocol2.
No native DLL or MC gameplay change this increment. No test entities/terrain
changes. Revalidate all process identities before continuing.

New tools/observe_native_beam.py resolves Winston script00fe through declared
metadata: node34 ChaseVar output ammo0035, rate20, node30 radius0670=8 and angle
00f3=40, node44 ModifyHealth literal60/period1 and target01d4 shared with node30.
It checks current local owner, script, graph types, numeric vtables/values, and
reads the original logger's node34 Begin/End plus native script clock. It is
strictly read-only diagnostic polling, NOT a lossless combat or MC damage bridge.
Actual25s observation had1447 samples/no errors; a1.024s native phase (599408 to
600432) consumed20.480003 ammo. Crucially, ammo varbag only committed100->79.52
at End. During firing, state+130 also stays100 and state+140 stays at the initial
native time. They are interpolation baselines, NOT continually updated ammo.
Do NOT implement continuous MC damage from polled ammo differences: it would
apply the whole burst after release. Native Begin/End + native clock must own
the phase. Actual hero change to Genji caused the new observer to reject every
later read, never using departed Winston state.

Native TrackTargets Update108ea60 ->108ed70 ->1090400 builds its cone:
definition+108 angle40, multiplied by degrees-to-radians0.017453292 and0.5,
then cosine at1090bf5; radius fromdefinition+140=8. Thus full angle40 / half20
is measured, not a guessed modern hero stat. Node30 offset is(0,1,0). Native
ChaseVar clock scale constant162c73c=0.001. Begin f531f0 is a jump to f54320;
End f53200 optionally commits output through f48240 then calls f54320. A naive
Update1Tick hook alone may not capture this interpolated state. Native damage
period semantics, axis/occlusion and a retained Begin/End channel still need
proof/implementation. Private evidence: winston-beam-ammo-authority.json,
winston-chase-samples.json, winston-beam-owner-change.json, winston-beam-config.json,
winston-block-1090400.json, winston-block-f531f0.json. Previous runtime addresses
are stale after Genji return. No beam MC damage is claimed.

FPS: actual temporary client.MaxFPS165 gave MC154.74/native99.97/distinct99.52,
held0/unmasked0; restored original0 with readback. The original native setting
is a simulation limiter atbff601; changing it did not fix the100FPS bottleneck.
Do not repeat as a proposed fix. native_runtime_settings.py now permits this
bounded typed/identity-guarded auto-restored experiment. Native video UI shows
VSync off/Limit30 off/Ultra/automatic scale. No UI setting was changed. Shared
Documents/Overwatch Settings_v0.ini belongs to normal user configuration and
was only read, not edited. Display adapter currently reports144Hz (FPS target
remains150 distinct composed images; do not claim150Hz physical output).
Private native_setting_xrefs.py reads live executable sections to locate RIP
references; native-xrefs-1833e04.json proves cap usages. Sleep import13822e8 has
many callers; direct Sleep10 candidates7cec8e/7fb9da are only candidates and have
not been shown to be on the frame path. Avoid broad unfiltered disassembly output.

Next concrete work: native Winston phase transport -> MC multi-target cone
collision/damage with original timing, while continuing actual FPS bottleneck
investigation. Full active goal is unchanged;150FPS/daylight/audio/full abilities
are still incomplete. Previous goal turn and this turn are evidence-bearing
progress, not blockers.

## Latest: McCree native hitscan damages the actual Minecraft world (emission 8)

Supersedes process/version references below. Current native28580 / MC2792,
supervisor exec41993, natural creative save, Genji first person, ready=true.
Modules7/1/23/6/8/8, guest protocol2. Native1164 and424 restored/stopped and MC
saved. All test villagers removed; no terrain changed. Recheck live identities.

Emission8 now journals the original McCree factory direction/timing, including
the calibrated offline status8 route. It never fabricates a native entity. Owner,
volley, native tick, shot and pellet identify a ray; native entity remains zero.
Requests v3/136 bytes bind both original literal70 damage paths. Measured native
computed config: speed0, lifetime0, range100. The original instantaneous movement
code multiplies direction by config+50; see NATIVE-HERO-SWITCHING.md. Guest performs
an immediate MC segment collision, nearest block/entity, base body70 OW HP ->7 MC
HP. Native recoil/scatter/ammo/reload remain original. Headshot and falloff remain
unverified/unimplemented; McCree skills/ultimate still pending. Do not label full
McCree combat complete merely because the emission channel is combatReady.

Actual1164: left20->13->6; replay unchanged. Natural leaf occlusion preserved
target20 and incremented blockHits. Right fan yielded six distinct rays, three
entity hits (20->0 actual HP) and three block hits; replay did not damage again.
Winston->McCree first shot20->13; return Genji three shuriken20->9.5, replay9.5.
Actual28580 cold restart: McCree first shot20->13; returned Genji ready=true.
The attempted temporary wall was refused because the site was occupied; the
file named emission8-mccree-wall-after.json is NOT proof of that wall blocking.
Use emission8-mccree-natural-occlusion.json for real MC obstruction proof.

Native journal/real MinHook fixtures now cover McCree capture, duplicate native
callbacks, wrong range/world refusal, two-hero rebinding and both hook byte
restorations. Actual1164 four-adapter restoration also passed, failures0. Guest
build/check, 8 native reflection tests and 20 launcher tests passed. See research/
emission8-* evidence. Final1164 20s: MC155.57/native99.99/distinct98.82FPS,
held0/unmasked0. Actual150FPS is NOT met. No FPS gain is claimed this increment.

Next: Winston beam native authority/MC damage, McCree abilities and falloff,
per-hero native health, F1 help, native climb animation, daylight/native lighting,
Hollywood audio, >=150 distinct FPS. User approved Hollywood fallback. Native
daytime lighting is still gamma1.3 presentation correction, not MC light coupling.

Read-only Winston preparation on28580: original script00fe node34 ChaseVar is
the actual ammo drain state; while firing its runtime index16/vtable15c8e30 has
Begin f531f0, End f53200, Update f535d0. State exists only while active. Original
Update reads native script clock via state+78 ->instance+10 ->+2d0, subtracts
state+140, and advances its native value toward0 at config rate20. This is not
yet a lossless beam observer. Node44 server-only ModifyHealth literal60, period
config1; node30 TrackTargets radius dynamic0670=8 and unknown field9d812041
dynamic00f3=40. Node34 output ammo0035=100. Node44 targets and node30 output both
bind01d4. Units/angle interpretation, original duration semantics and occlusion
must be proven before implementing damage. Nodes81/82 literal40 are separate
attack paths (likely ultimate); do not substitute them for Tesla. Private evidence:
research/winston-beam-config.json, winston-runtime-bindings.json,
winston-functions-f53614.json. Runtime pointers are stale after Genji return.
Private helpers accept PID: winston_native_probe.py, winston_runtime_states.py,
winston-functions.py (functions reader cannot find leaf functions without unwind
entries; split unwind functions require subsequent chunks). All are read-only.

## Latest: McCree native pellet provenance, emission 7

Supersedes process/version references below. Current native424 / MC8548,
supervisor exec56096, natural creative save, Genji first person, ready=true.
Modules7/1/23/6/8/7 (bootstrap/localhero/compositor/body/weapon/emissions), guest
rebuilt for emission7 protocol validation. Four adapters enabled, zero failures.
Verify actual processes and session-status.json afresh. No terrain changed;
test villagers cleaned. Native11112,7284,24016 restored/stopped and worlds saved.

This turn added bounded diagnostic observation of native pellet factory d354b0
alongside the existing Genji initializer hook. Actual24016 McCree left:2 shots
500ms apart; right fan:6 shots at139..161ms, original scatter directions retained.
All McCree factories returned null/status8, type1/resource04000000000002a7.
The offline native entity creation fails before the Genji initializer could see
anything. This explains absent emissions; it is NOT yet a completed MC hitscan.
Read-only declared STU metadata proves both weapon nodes33/38 m_amount are s32
literal70 OW HP. No guessed modern damage/speed values. See hero switching doc.

Required next: carry original factory direction + current owner/MC world identity
into a retained acknowledged hitscan journal; use owner/volley/tick/shot/pellet
identity (volley ID persists and shot/pellet remain0), not fake projectile IDs.
Prove range/falloff/headshot semantics and real MC wall/entity hit behavior. Keep
McCree/Winston combatReady false until their actual damage bridge works. Native
function exception ranges can split one function: d354b0 continues atd3550c.
Status8 can mean missing or failed native admin +210 creation; the exact live
branch still needs proof. Do not fabricate a server.
Private source evidence and live bytes are the spec; no retail target.

Fixture tests preserve args/return and both hook byte restorations. Actual stop
24016 confirms restored=true/failures0. Genji return regression: real3 shuriken
20->9.5HP, explicit replay stays9.5. 8 reflection +20 launcher checks, native
fixtures and full guest build/check pass. The initial factory prefix omitted a
redundant40 byte; guard rejected installation, corrected from real bytes, and
cold restarted. Prepare now validates both prefixes before injection.

Evidence: emission7-mccree-factory-left-right.json,
mccree-damage-calibrated.json, emission7-genji-return-combat.json,
emission7-real-restoration.json in research. Current20s performance:
MC154.90/native100.02/distinctcomposed98.64FPS, held0/unmasked0.150FPS NOT met.
research/_archive/2026-10/emission7-final-performance.json. Remaining goal: McCree/Winston combat
and abilities, per-hero health, F1 banner, native climb animation, daytime native
lighting/Hollywood audio and actual>=150 distinct FPS. Goal remains active.

## Latest: Genji combat reconnects after native hero changes

Supersedes all process/version references below. Current native11112 / MC28200,
supervisor exec93568, natural creative save, initial-Genji startup then
Winston->Genji return. Modules7/1/23/6/8/6 (bootstrap/localhero/compositor/body/
weapon/emissions), current guest rebuilt. All four adapters enabled/zero failures,
ready true. Verify actual processes and research/session-status.json afresh.

Emission6 keeps the same hook/journal across three-hero switches, rejects departed
and non-Genji owners, reloads validated current Genji bindings. Launcher refreshes
movement, dash, ultimate and projectile bindings. Full Genji return no longer
requires a restart. Actual21604 all-three roundtrip: each original three-shuriken
burst damaged an MC villager20->9.5, replay did not damage again.

Fixed first dash idle admission and per-hero native clock reset. Actual16964 first
native tick95,392 and returned tick20,288 both moved MC (begins1->2), with native
Begin authority and MC tree collision. Fixed Dragonblade End timestamps being
counted as extra swings. Actual11112 after Winston->Genji: original shuriken
charged1200, Q drained0, first sword20->8HP/one swing, after1200ms still8, second
sword8->0/two total. Test entities cleaned, no terrain test changes. Evidence:
research/_archive/2026-10/hero-combat-final-ultimate-single-hit.json, hero-combat-final-charge.json,
hero-combat-roundtrip-first-dash.json, emission6-roundtrip-shot.json.

20 Python tests, native MinHook lifecycle/journal fixtures and guest build/check
pass. New Win64 native-map fixture excludes sword End from attack events. Startup
now checks actual mapped bootstrap identity/time: Windows reused28140 with a stale
v3 report and no DLL, which formerly skipped bootstrap. Same process recovered.
Emission5 exposed an input-stream lock preventing atomic request replacement;
restored/cold replaced by6 with shared-delete bounded request reads. All earlier
processes19412/28140/21604/18344/16964 restored and MC saved before next startup.

Next required: actual native McCree hitscan and Winston beam -> MC damage and
abilities; original per-hero health (still169/200 on new heroes); F1 help banner;
native climbing animation; daylight/audio and actual>=150 distinct composed FPS.
Do not call the new heroes combat-ready just because hands/movement/ammo work.
Profile backup: ~/.universal-modder/backups/owmc-hero-lifecycle/20261016-035847.zip.
Final20s sample MC155.02/native100.03/distinctcomposed98.65FPS; held0/unmasked0.
research/_archive/2026-10/hero-combat-final-performance.json.150FPS is still not achieved.


## Newest checkpoint: three-hero presentation/body and native weapon lifecycle

Supersedes the v22 checkpoint below. Built modules now: bootstrap7, localhero1,
compositor23, body6, weapon8, emissions4. See NATIVE-HERO-SWITCHING.md for exact
real evidence and limitations. Original McCree/Winston weapons now visibly render
over MC and body6 follows controller/model replacements using measured eye heights.
Actual native18104 roundtrips proved their movement and original ammo consumption.
Automatic locomotion rebinding McCree->Genji passed on the live guest. The Genji
emission adapter was deliberately stopped for that calibration; full switched
combat is still NOT ready. Native28152 and18104 restored/stopped/saved afterward.

Weapon7's shared-table route passed real Genji emission and McCree ammo/reload.
Weapon8 adds the fixture-proven other-entity callback-thread correction. Winston
consumes ammo without these Volley callbacks; beam damage needs its own observer.
Original body/lens/shared-weapon fixtures and21 Python launcher/performance tests
passed. Current live native19412 / MC5680, supervisor exec5151: natural creative
Genji first person, all four adapters healthy. Actual gate8 shot24->21 and3 native
emissions accepted; research/_archive/2026-10/hero-v23-final-health.json. Verify session-status.json
and actual processes afresh before relying on these PIDs. Latest12s final sample:
MC154.45/native99.96/distinctcomposed99.37FPS, zeroheld/missingmask;
research/_archive/2026-10/performance-v23-final.json. >=150 remains failed.

Next: original Genji emission/dash/ultimate rebind on roundtrip, native McCree
hitscan and Winston beam event transport, per-hero health (spawner169/200), skills,
daylight/audio and >=150 FPS. Do not report rendering/walking as completed combat.

## Newest checkpoint: original locomotion and compositor v22

This section supersedes the PIDs/version/performance claims below. Current live
native4908 / MC19016, natural creative save, Genji first person, all four adapters
healthy. Supervisor exec35151. Verify research/session-status.json afresh.
Native24400,376,16280,21964 and their guest sessions have stopped/restored/saved.
Built modules are bootstrap7, localhero1, compositor22, body5, weapon6, emissions4.

Original BASE locomotion now reads reflected native mover f32 fields. Genji
6/5.4/6/3/3/3 metres/s; actual flat-world per-tick steps .3/.27/.3/.3/.15 prove
forward/back/strafe/forward-diagonal/crouch. McCree/Winston original values
5.5/4.95/5.5/3/3/3 identified, but their gameplay bridge remains incomplete.
See NATIVE-LOCOMOTION.md for exact provenance and remaining physics limits.
Both controller and model IDs change on native H -> new hero -> confirm.
McCree click6->6 proves execution still needs a gate; Winston spawner still uses
200HP. Native-only weapon screenshots are NOT fused combat proof.

v21 added per-stage CPU timing and report timestamps. v22 retains exact544-byte
constant-buffer identities (max64), releases them on render-owner stop, avoids
repeat QueryInterface/GetDesc for cached buffers and copies valid mapped/source
CPU bytes directly before native Unmap/update. No GPU readback introduced.
Native lens/GPU/depth/selection/restoration fixtures passed;19 Python launcher/
performance tests passed. Actual v21 buffer observation .936ms/frame became
.669ms in v22, but final FPS did NOT improve reliably.

Latest20s v22 natural sample: MC153.16, native99.89, distinctcomposed98.15FPS;
zeroheld/missingmask. >=150 remains FAILED. Evidence:
research/_archive/2026-10/performance-v21-profile.json, performance-v22-profile.json,
v21-genji-selection.png and v22-firstperson.png. Native limiter waits were tiny;
original Present .578ms, HUD composition .512ms, draw observation .044ms/frame.
GPU counters: native3D~36.6%, MC~14%; not enough to identify the critical path.

Rejected runtime experiments on16280: app.WaitForRenderFrame0, AADetail0,
DirectionalShadowDetail0, LocalFogDetail1. No reliable FPS gain; every setting
restored. native_runtime_settings.py is experimental only, no startup override.
Actual beta Render registry stayed high quality despite the earlier Render13
file; do not infer applied settings from that file. Avoid repeating these tests
without new evidence. Hollywood fallback remains selected per user instruction.

Next: multi-hero lifecycle and native hitscan/beam authority, per-hero health,
lens/eye calibration; climb animation; map ambient audio/daylight coupling and
native frame critical-path investigation. Full goal remains active.

## Latest active goal and state (supersedes historical sections)

User retains the full multi-hero goal: Genji + Winston + McCree, original animated
selection over MC, climb, independent flight key, original OW movement speeds,
changeable MC saves, one-click launch, actual >=150 FPS, no flashes/stutter.
Native model lighting must match MC daytime. Latest user explicitly permits
Hollywood fallback if one last empty-stage attempt is still unsuitable.

That last attempt ran native PID 2228 with bootstrap v7 + compositor v19. The
actual empty native map now renders original hands and animated selection; v19
fixes hand-before-world draw ordering. However models remain orange/dark, so the
empty stage FAILED lighting acceptance. Both bootstrap Python defaults have been
restored to Hollywood (0x08000000000002af). PID 27816 then proved original bright
hands/HUD over MC again. Empty option 0x0800000000000223 remains experimental.
Evidence: research/empty-map-20261016/last-empty-firstperson.png and
hollywood-fallback.png. All four adapters on 2228/27816 stopped/restored with zero
failures, both exact native PIDs terminated. MC 28036 saved and stopped normally.

Current source/built modules: bootstrap7, localhero1, compositor20, body5, weapon6,
emissions4. Native15612/MC28092 completed live flight tests, then both stopped and
saved through the NEW launchers/Stop-Overwatch-Minecraft.cmd. Native11064/MC20280 proved a
complete alternate-flat-save cold start and actual climbing; test wall/villager
cleaned up before stop. Current live native24400 / MC27172 has returned to the natural save,
Genji first person, all four stages enabled/zero failures and healthy channels.
research/_archive/2026-10/v20-natural-final-health.json records current identity. Verify afresh
when resuming. Other historical clients are stopped.

Flight v20 actual acceptance: doubleSpace all false, Y69->70.2522->69; F6 held1.2s
turned flying on once; Space raised to74.163; next F6 turned off and landedY69.
Evidence research/_archive/2026-10/flight-v20-proof.json. DefaultF6, configurableF6..F10. Native
protocol2 bit64 retains short taps and first-person/foreground gating; guest
release-armed toggle and vanilla abilityResyncCountdown reset prevent doubleSpace.

Climb actual wall test on flat save: one start,10 ticks,2.99999999999997 blocks
motor rise, airborne jump+climb maxY-55.7478 from-60, ended groundedY-60, flyingfalse.
Evidence research/_archive/2026-10/climb-v20-live-proof.json. This is motor proof, original climb
animation remains unverified. Temporary wall and villager cleaned through API.

World selection: launchers/Configure-Overwatch-Minecraft.cmd opens a small Tk picker; CLI
configure_passthrough.py supports list/select/import/flightkey. Imports preserve
source/refuse overwrite. Actual full startup switched natural -> existing flat,
health worldName matched and real flat scene shown. Actual return to natural save passed, original Genji selection foreground and hands
visible again: research/_archive/2026-10/v20-genji-selection-day.png. Native24400 remains running.
Start refuses a running guest with mismatched worldName. STOP restores each
adapter, terminates exact guarded native and saves exact-profile MC normally.

Status now also checks new composed image advancement (3s) and missing foreground
mask samples; live Present counts alone cannot declare a frozen image healthy.
15 launcher tests pass. Guest build/check and v20 native GPU fixtures passed.
New build_session_bootstrap.ps1 reproducibly builds7 (tested after no live7).

Selection v16 actual original Genji/McCree/Winston models and motion were recorded
in research/render-diagnosis-20261016/selection-v16-*.png / *-motion.mkv. This proves
selection animation, NOT switched hero gameplay: body/weapon/emission and ability
bindings still depend on Genji. Original locomotion speed calibration is pending.
Climb uses swept collision with max6blocks/30ticks; live motor acceptance above. 150 FPS NOT passed: latest12s flat sample (performance-v20-flat.json) had MC153.52,
native98.26, distinctcomposed97.35, zeroheld/missingmask/rejections. A prior20s empty sample had MC155.58,
native71.37, distinct composed71.12 FPS, zero held during sample, missing hands in
that older v18 run. Do not report target caps or MC producer FPS as composed FPS.

v18 rejects incomplete old-FOV coverage during selection->gameplay and holds the
last fully composed image. v19 additionally captures hand depth before the first
world draw. Both have independent GPU fixtures; actual v19 hand transition passed.
No production native GPU readbacks. v20 retains those fixes.

Last saved profile backup:
%USERPROFILE%/.universal-modder/backups/owmc-flight-worlds/20261016-023112.zip.
Native2560x1440, MC1920x1080, source and presentation caps165. Default fullBright
true, native hand gamma1.3; exact MC lighting is not fully coupled to native models.
The same guarded offline executable is the ONLY mod target. Preserve all dirty
source. Never load a second callback owner or reload a stopped continuous module.

## Continuation: idle readiness fix and desktop access

The next cold diagnostic launch used native PID 13228, without the compositor or
other adapters. Computer Use could enumerate its Overwatch window, but activation
failed with `GetCursorPos failed: access denied (0x80070005)` and the one read-only
capture retry failed with `FrameArrived timed out`. Windows LogonUI was present
in the same console session. The user was asked to unlock the desktop; no input
was sent to the login/security UI. Prior black window captures are inconclusive
until an unlocked desktop capture succeeds. This does not explain away the real
zero-composition counters; the rendering gate still needs an actual new run.

An independent source defect was fixed in `NativeAbilityReader.poll`: a healthy
native hero with no Shift logger row retained the earlier `native camera
unavailable` error indefinitely. Valid idle bindings now clear that stale error
without inventing an attack, while missing bindings, changed heroes and invalid
native numeric values remain failures. An actual Win64 self-process memory fixture
exercises startup without camera, missing binding, successful idle recovery,
changed identity and invalid speed. The guest build and all Gradle checks passed.

The launcher now requires nonzero composed MC frame IDs and uploads, plus matching
native camera generation/provenance. Hook attachment alone cannot mark it ready.
It reports composition counts and combat-channel errors together instead of a
generic timeout. Twelve launcher tests pass, including zero-blend/neutral-frame,
old-session, synthetic-camera, dead-player and healthy-idle scenarios. These checks
are channel readiness, not a substitute for visible gameplay acceptance.

Resume by identifying the current exact research process, confirming an unlocked
native window, then continue bootstrap/Genji and actual composition diagnosis.
Do not attach a duplicate client or assume historical PID 13228 still belongs to it.

## Installed environment

- universal-modder 0.2.0: installed and enabled in Codex; `um --version` succeeds.
- Source: upstream GitHub main ZIP, downloaded through codeload after Git HTTPS
  failed. Persistent source is `%LOCALAPPDATA%\OWMC\plugin-source\universal-modder-main`.
  Its local marketplace entry points to that extracted directory; the original
  URL-based catalog is retained as `marketplace.json.upstream`. Future updates
  must explicitly refresh that source; this is not an automatically updating Git clone.
- `um win setup` installed SHA256-verified FFmpeg with gfxcapture and AMF support.
  fal has no configured key. Blender/asset generation were not required or tested.
- Project Python: `.venv`, CPython 3.13.13. Dependencies are pinned in
  `tools/requirements-dev.txt`. The system Python 3.11 cannot parse all migrated code.
- MinGW-w64: WinLibs GCC 16.2.0 / UCRT / POSIX / SEH, under
  `%LOCALAPPDATA%\OWMC\toolchains\mingw64`.
  Archive SHA256: `d5dbafc4a170e762ca6143151ec918fb9e2c72736fb14cd704abebc6bdd5276a`.
  GCC's default-manifest linker path failed when its installation directory
  contained spaces, so the compiler was moved out of the workspace into that
  space-free directory. Project source paths with spaces build successfully.
- Fourteen native build scripts now resolve the compiler using `OWMC_CXX`, then
  workspace `tools/mingw64`, then the per-user OWMC toolchain, then PATH.
- `launchers/Start-Overwatch-Minecraft.cmd` explicitly uses the project Python environment.
- `tools/check_world_frames.py` now accepts the existing color-only frame format;
  absent depth is reported as null rather than crashing on `None.min()`.

## Reproduce the development baseline

```powershell
./tools/setup_environment.ps1
./.venv/Scripts/python.exe tools/check_environment.py
./tools/build_guest.ps1 -Tasks build,--offline
./tools/build_live_passthrough.ps1
./tools/build_guest_body.ps1
./tools/build_native_emission.ps1
./tools/build_weapon_gate.ps1
./.venv/Scripts/python.exe -m unittest discover -s tools -p 'test_*.py'
./.venv/Scripts/python.exe bridge/test_contract.py
```

Run the remaining `bridge/test_*.py` files separately. Verified here: 31 tools
unit tests; 27 creative/memory/relay/world-frame tests; 4 host-camera tests; the
standalone Java/HTTP contract test. Guest Gradle build passed, including native
combat, host-pose and actual Win64 mapping checks. All four native builds above
and their GPU/body/weapon/emission fixtures passed on this machine.

`git diff --check` still flags the pre-existing blank line at the end of
`guest/src/test/java/lab/owmcguest/WorldFrameMappingCheck.java`; it was not changed
as part of the takeover.

## Actual runtime smoke test — not playable acceptance

The migrated launcher selected compositor v13, body v5, weapon gate v6 and native
emission v4. The exact research executable SHA256 matched its existing guard.

Minecraft PID 28040 loaded the existing natural creative save successfully and
published 1920×1080 frames. Player health was 20, alive, invulnerable and grounded.
A three-second MC-only capture after native adapters were stopped obtained 87
different frames, zero rejected frames, color-only payload. The actual image was
visually inspected and shows the real birch forest from the saved world.

Native PID 28200 completed the existing bootstrap and Genji spawn routines.
All four modules attached with zero reported failures. However, startup readiness
timed out: the dash channel reported `native camera unavailable`; compositor
report showed 7,561 presents, 7,560 poses, **zero blended frames**, zero texture
allocations/uploads, all frames held, and FOV 40. Module attachment and counters
therefore do not establish successful visual fusion. Native window captures were
black, including after module restoration. Capture validity and the native scene
itself need to be distinguished before attributing the root cause to the renderer.

All four module stop paths reported `restored=true`, `enabled=false`, failures 0.
Minecraft was shut down through its API and its log confirmed all dimensions
saved. The native process did not exit after normal CloseMainWindow; after its
exact executable path and restored adapters were verified, only that test process
was terminated. Neither test process remains. These PIDs are historical, never reuse them.

Local evidence is in `research/migration-20261016/`: environment/artifact hashes,
runtime health, startup failure, restored module reports, MC frame proof and PNGs.
The four pre-rebuild native DLLs are retained under its `artifacts/` subdirectory.

Profile backup before first launch:
`<USERPROFILE>\.universal-modder\backups\owmc-migration-20261016\20261016-001713.zip`
(145 files, 96.4 MB; both saves, mods, options and logs).

## Next development priority

1. Establish a visible, healthy original offline Genji scene on the replacement
   PC before attaching the continuous compositor. Verify the actual world/viewmodel
   lens and HUD insertion boundary; investigate the observed FOV 40 and absent
   blend boundary without weakening identity or freshness checks.
2. Verify fresh camera consumption and real nonzero composed frames, then repeat
   start/stop/resize and movement checks. Current `health()` alone is insufficient
   to prove picture output; inspect `blended`, actual frame IDs and pixels too.
3. Resume actual Genji first-attack damage, Shift wall/damage tests and Dragonblade
   acceptance. Prior-PC evidence in the existing docs is useful context but must
   not be relabeled as new-PC evidence. Pharah, audio isolation, health/death and
   sustained play remain broader unfinished requirements.

## Window-size performance experiment (current blocker)

Native15612 Alt+Enter + WM size1920x1080 gave poses/Present but ZERO new blends,
continuous held frames. Returning2560x1440 restored composition. Do not deploy a
resolution change as an optimization or call held FPS real. No permanent shared
OW settings file edit. Independent GPU resize fixture does not cover this actual
native offscreen/HUD target routing; investigate before adopting lower resolution.
