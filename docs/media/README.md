# README 演示素材

本目录收录宣传片导出的压缩截图、短 GIF，以及 README 使用的官方英雄头像和技能图标。完整成片、原声和原始录像不随仓库提供。

## 来源

本地源文件：`research/promo/promo-v1.mp4`，127,122,474 字节，159.2 秒，1920×1080 / 30 fps。SHA256：

```text
29ed31b42713db2b8209d644f315793c42bce3f7a5af94123eac9e94c01da6bd
```

剪辑区间依据 `research/promo/executed-shotlist.json`；成片验收记录为 `research/promo/promo-v1-verification.json`。这些是本机复核路径，不提供指向未入库文件的失效链接。宣传片：（链接待补）。

源片记录 12 位英雄的部分技能、F6–F11 与实际暮色森林维度。它不包含后续 F5 / 生存功能和冰墙修复镜头；没有把旧片中的阻塞项目改写成演示通过。

## 公开文件

| 文件 | 成片时间 | 规格 / 说明 |
| --- | ---: | --- |
| [genji-shuriken.jpg](genji-shuriken.jpg) | 4.05 s | 1280×720；原版源氏手模、手里剑和 HUD。 |
| [widowmaker-sniper.jpg](widowmaker-sniper.jpg) | 131.60 s | 1280×720；黑百合未开镜射击，原版武器与 MC 目标。 |
| [mei-freeze.jpg](mei-freeze.jpg) | 109.40 s | 1280×720；小美喷雾演示截帧；文件名不表示这一张静帧能单独证明完整冰冻流程。 |
| [twilight-forest.jpg](twilight-forest.jpg) | 155.00 s | 1280×720；真实暮色森林维度与原版麦克雷武器。 |
| [heroes-12.gif](heroes-12.gif) | 下表 | 640×360，10 fps，84 帧，8.4 秒，6,257,005 字节；无音轨，循环播放。 |

四张 JPEG 共 452,856 字节；五个媒体文件总计 6,709,861 字节（约 6.71 MB）。不把完整视频和语音复制到这里。

## GIF 的 12 个原片区间

每段 0.7 秒，按以下顺序硬切，不含开场 / 结尾占位或未通过审查的技能：

| 英雄 | 入点（秒） | 原剪辑片段 |
| --- | ---: | --- |
| 源氏 | 2.90 | `genji-primary` |
| 麦克雷 | 19.40 | `mccree-primary` |
| 法老之鹰 | 28.50 | `pharah-primary` |
| 死神 | 40.60 | `reaper-primary` |
| 士兵：76 | 50.30 | `soldier76-primary` |
| 猎空 | 63.00 | `tracer-primary` |
| 堡垒 | 73.80 | `bastion-recon` |
| 半藏 | 86.50 | `hanzo-primary` |
| 狂鼠 | 98.60 | `junkrat-primary` |
| 小美 | 108.30 | `mei-primary` |
| 托比昂 | 119.70 | `torbjorn-turret` |
| 黑百合 | 131.00 | `widowmaker-primary` |

## 导出与核查

使用本地现有 FFmpeg `N-127564-g3c92f003c7-20261015`。截帧按上表时间，`scale=1280:720:flags=lanczos`、JPEG `-q:v 3`，移除文件级元数据。GIF 从同一输入 split / trim 12 段，分别 `setpts=PTS-STARTPTS,fps=10,scale=640:360:flags=lanczos,setsar=1`，concat 后采用 `palettegen=max_colors=192:stats_mode=diff` 与 `paletteuse=dither=sierra2_4a:diff_mode=rectangle`，无音轨。

用 Pillow 逐帧读取 GIF，核对 84 帧、总时长 8,400 ms、12 段和文件大小小于 8,000,000 字节。四张 JPEG 均重新解码检查。视觉检查只看长边不超过 1024 px、JPEG 质量 80 的对照拼图；初选图片与拼图留在被忽略的 `_preview/`，没有删除原文件。

画面中的英雄、模型和游戏界面权利归相应权利人；这些演示媒体不适用未来自有代码的 MIT 授权建议。

## 技能状态与图标来源

状态更新于 2026-11-08，覆盖 14 位英雄的 89 项技能与机制。76 项已还原、4 项已实现待实机、7 项部分、2 项未还原。

原有状态来自 78 项实机抽查与冰墙复测。托比昂、小美、黑百合、死神和生存机制按后续实机记录与离线修复更新。路霸有主次射击、拉取、治疗、击退等实机记录，后续视觉、拉取与音频修改仍待复测。温斯顿按当前实现和离线结果列出，原始暴怒的原生变身与 HUD 待验收。麦克雷神射手和狂鼠垂死挣扎保留部分状态，炸弹轮胎仍未还原。

- 78 项抽查记录 SHA256：`daabe413a53bc476987edf6d4cef7961eb372bdaa89071e894fed020aae0bcba`。
- 冰墙与轮胎复测记录 SHA256：`d23a87dedac1c4fe5b9a92e90bc4fdd2dccd4bc7697fbf7ec85b9d9b1662efe7`。

### 图标规格

103 张 PNG（14 张头像、89 张技能图），统一 64×64，总计 394,193 字节，单张最大 9,673 字节。所有图片均本地存放，不使用外站热链。

图像由 [Overwatch Wiki](https://overwatch.weirdgloop.org/) 提供，原作 © Blizzard Entertainment。优先选用 2017 年底以前的存档版本，共 82 个文件；其余采用站内现有图像。仅作等比缩放、方形排版与中性底色处理，没有重绘图形。

二段跳和爬墙共用“Cyber-Agility”图标；普通近战使用通用“Quick Melee”图标；同一武器的开火模式、地雷投放与引爆、锤击与炮台维护可共用对应技能图标。英雄与技能名称按本项目使用的旧版技能组列出，保留 McCree、Scatter Arrow、Armor Pack、Self-Repair 和 Configuration: Tank 等旧版名称。

下表的“图像版本”是来源文件的上传时间；来源页保留版权和图像说明，下载链接指向实际使用的图像版本。

| 本地文件 | 来源页 | 原图 | 图像版本 |
| --- | --- | --- | --- |
| [heroes/genji/portrait.png](heroes/genji/portrait.png) | [Icon-Genji.png](https://overwatch.weirdgloop.org/w/File:Icon-Genji.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181018235709%21Icon-Genji.png?e4c4b) | 2015-11-07 |
| [heroes/mccree/portrait.png](heroes/mccree/portrait.png) | [Icon-Cassidy.png](https://overwatch.weirdgloop.org/w/File:Icon-Cassidy.png) | [下载](https://overwatch.weirdgloop.org/images/Icon-Cassidy.png?9e60b) | 2022-10-05 |
| [heroes/pharah/portrait.png](heroes/pharah/portrait.png) | [Icon-Pharah.png](https://overwatch.weirdgloop.org/w/File:Icon-Pharah.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024028%21Icon-Pharah.png?64226) | 2014-11-07 |
| [heroes/reaper/portrait.png](heroes/reaper/portrait.png) | [Icon-Reaper.png](https://overwatch.weirdgloop.org/w/File:Icon-Reaper.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024133%21Icon-Reaper.png?bb8b4) | 2014-11-07 |
| [heroes/soldier76/portrait.png](heroes/soldier76/portrait.png) | [Icon-Soldier 76.png](https://overwatch.weirdgloop.org/w/File:Icon-Soldier_76.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024447%21Icon-Soldier_76.png?50a48) | 2015-07-08 |
| [heroes/tracer/portrait.png](heroes/tracer/portrait.png) | [Icon-Tracer.png](https://overwatch.weirdgloop.org/w/File:Icon-Tracer.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024844%21Icon-Tracer.png?c1b28) | 2014-11-07 |
| [heroes/bastion/portrait.png](heroes/bastion/portrait.png) | [Icon-Bastion.png](https://overwatch.weirdgloop.org/w/File:Icon-Bastion.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181018235223%21Icon-Bastion.png?2cf08) | 2014-11-07 |
| [heroes/hanzo/portrait.png](heroes/hanzo/portrait.png) | [Icon-Hanzo.png](https://overwatch.weirdgloop.org/w/File:Icon-Hanzo.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019023309%21Icon-Hanzo.png?4119c) | 2014-11-07 |
| [heroes/junkrat/portrait.png](heroes/junkrat/portrait.png) | [Icon-Junkrat.png](https://overwatch.weirdgloop.org/w/File:Icon-Junkrat.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019023417%21Icon-Junkrat.png?99beb) | 2015-10-21 |
| [heroes/mei/portrait.png](heroes/mei/portrait.png) | [Icon-Mei.png](https://overwatch.weirdgloop.org/w/File:Icon-Mei.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019023706%21Icon-Mei.png?2d137) | 2015-11-07 |
| [heroes/torbjorn/portrait.png](heroes/torbjorn/portrait.png) | [Icon-Torbjörn.png](https://overwatch.weirdgloop.org/w/File:Icon-Torbj%C3%B6rn.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024803%21Icon-Torbj%C3%B6rn.png?732dd) | 2014-11-07 |
| [heroes/widowmaker/portrait.png](heroes/widowmaker/portrait.png) | [Icon-Widowmaker.png](https://overwatch.weirdgloop.org/w/File:Icon-Widowmaker.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024938%21Icon-Widowmaker.png?2708b) | 2014-11-07 |
| [heroes/genji/shuriken.png](heroes/genji/shuriken.png) | [Ability Shuriken.png](https://overwatch.weirdgloop.org/w/File:Ability_Shuriken.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Shuriken.png?af929) | 2015-11-07 |
| [heroes/genji/shuriken-fan.png](heroes/genji/shuriken-fan.png) | [Ability Shuriken.png](https://overwatch.weirdgloop.org/w/File:Ability_Shuriken.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Shuriken.png?af929) | 2015-11-07 |
| [heroes/genji/swift-strike.png](heroes/genji/swift-strike.png) | [Ability Swift Strike.png](https://overwatch.weirdgloop.org/w/File:Ability_Swift_Strike.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20260810145623%21Ability_Swift_Strike.png?02781) | 2015-11-07 |
| [heroes/genji/deflect.png](heroes/genji/deflect.png) | [Ability Deflect.png](https://overwatch.weirdgloop.org/w/File:Ability_Deflect.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Deflect.png?736a1) | 2015-11-07 |
| [heroes/genji/dragonblade.png](heroes/genji/dragonblade.png) | [Ultimate Dragonblade.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Dragonblade.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Dragonblade.png?1ec1b) | 2015-11-07 |
| [heroes/genji/double-jump.png](heroes/genji/double-jump.png) | [Passive Cyber-Agility.png](https://overwatch.weirdgloop.org/w/File:Passive_Cyber-Agility.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119022420%21Passive_Cyber-Agility.png?62e06) | 2015-11-25 |
| [heroes/genji/wall-climb.png](heroes/genji/wall-climb.png) | [Passive Cyber-Agility.png](https://overwatch.weirdgloop.org/w/File:Passive_Cyber-Agility.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119022420%21Passive_Cyber-Agility.png?62e06) | 2015-11-25 |
| [heroes/genji/melee.png](heroes/genji/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/mccree/peacekeeper.png](heroes/mccree/peacekeeper.png) | [Ability Peacekeeper.png](https://overwatch.weirdgloop.org/w/File:Ability_Peacekeeper.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119023403%21Ability_Peacekeeper.png?d4182) | 2016-06-22 |
| [heroes/mccree/fan-the-hammer.png](heroes/mccree/fan-the-hammer.png) | [Ability Fan the Hammer.png](https://overwatch.weirdgloop.org/w/File:Ability_Fan_the_Hammer.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Fan_the_Hammer.png?be0e7) | 2025-10-17 |
| [heroes/mccree/combat-roll.png](heroes/mccree/combat-roll.png) | [Ability Combat Roll.png](https://overwatch.weirdgloop.org/w/File:Ability_Combat_Roll.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Combat_Roll.png?2fc24) | 2015-03-09 |
| [heroes/mccree/flashbang.png](heroes/mccree/flashbang.png) | [Ability Flashbang.png](https://overwatch.weirdgloop.org/w/File:Ability_Flashbang.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Flashbang.png?e5fa6) | 2022-06-19 |
| [heroes/mccree/deadeye.png](heroes/mccree/deadeye.png) | [Ultimate Deadeye.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Deadeye.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Deadeye.png?5d293) | 2015-03-09 |
| [heroes/mccree/melee.png](heroes/mccree/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/pharah/rocket-launcher.png](heroes/pharah/rocket-launcher.png) | [Ability Rocket Launcher.png](https://overwatch.weirdgloop.org/w/File:Ability_Rocket_Launcher.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119024457%21Ability_Rocket_Launcher.png?51348) | 2016-06-22 |
| [heroes/pharah/jump-jet.png](heroes/pharah/jump-jet.png) | [Ability Jump Jet.png](https://overwatch.weirdgloop.org/w/File:Ability_Jump_Jet.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119024127%21Ability_Jump_Jet.png?21583) | 2014-11-12 |
| [heroes/pharah/concussive-blast.png](heroes/pharah/concussive-blast.png) | [Ability Concussive Blast.png](https://overwatch.weirdgloop.org/w/File:Ability_Concussive_Blast.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128012947%21Ability_Concussive_Blast.png?e27ca) | 2014-11-12 |
| [heroes/pharah/barrage.png](heroes/pharah/barrage.png) | [Ultimate Barrage.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Barrage.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Barrage.png?7315e) | 2014-11-12 |
| [heroes/pharah/hover-jets.png](heroes/pharah/hover-jets.png) | [Passive Hover Jets.png](https://overwatch.weirdgloop.org/w/File:Passive_Hover_Jets.png) | [下载](https://overwatch.weirdgloop.org/images/Passive_Hover_Jets.png?a7972) | 2024-08-23 |
| [heroes/pharah/melee.png](heroes/pharah/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/reaper/hellfire-shotguns.png](heroes/reaper/hellfire-shotguns.png) | [Ability Hellfire Shotguns.png](https://overwatch.weirdgloop.org/w/File:Ability_Hellfire_Shotguns.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119024758%21Ability_Hellfire_Shotguns.png?a94fc) | 2016-06-22 |
| [heroes/reaper/wraith-form.png](heroes/reaper/wraith-form.png) | [Ability Wraith Form.png](https://overwatch.weirdgloop.org/w/File:Ability_Wraith_Form.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Wraith_Form.png?b9155) | 2014-11-12 |
| [heroes/reaper/shadow-step.png](heroes/reaper/shadow-step.png) | [Ability Shadow Step.png](https://overwatch.weirdgloop.org/w/File:Ability_Shadow_Step.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Shadow_Step.png?306fe) | 2014-11-12 |
| [heroes/reaper/death-blossom.png](heroes/reaper/death-blossom.png) | [Ultimate Death Blossom.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Death_Blossom.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Death_Blossom.png?d97fd) | 2014-11-12 |
| [heroes/reaper/the-reaping.png](heroes/reaper/the-reaping.png) | [Passive The Reaping.png](https://overwatch.weirdgloop.org/w/File:Passive_The_Reaping.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119024601%21Passive_The_Reaping.png?9ffaf) | 2015-11-27 |
| [heroes/reaper/melee.png](heroes/reaper/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/soldier76/heavy-pulse-rifle.png](heroes/soldier76/heavy-pulse-rifle.png) | [Ability Heavy Pulse Rifle.png](https://overwatch.weirdgloop.org/w/File:Ability_Heavy_Pulse_Rifle.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119025521%21Ability_Heavy_Pulse_Rifle.png?4f5c8) | 2016-06-22 |
| [heroes/soldier76/helix-rockets.png](heroes/soldier76/helix-rockets.png) | [Ability Helix Rockets.png](https://overwatch.weirdgloop.org/w/File:Ability_Helix_Rockets.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Helix_Rockets.png?7984a) | 2015-07-08 |
| [heroes/soldier76/sprint.png](heroes/soldier76/sprint.png) | [Ability Sprint.png](https://overwatch.weirdgloop.org/w/File:Ability_Sprint.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Sprint.png?d3ba2) | 2015-07-08 |
| [heroes/soldier76/biotic-field.png](heroes/soldier76/biotic-field.png) | [Ability Biotic Field.png](https://overwatch.weirdgloop.org/w/File:Ability_Biotic_Field.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Biotic_Field.png?76dc0) | 2015-07-08 |
| [heroes/soldier76/tactical-visor.png](heroes/soldier76/tactical-visor.png) | [Ultimate Tactical Visor.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Tactical_Visor.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Tactical_Visor.png?9603e) | 2015-07-08 |
| [heroes/soldier76/melee.png](heroes/soldier76/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/tracer/pulse-pistols.png](heroes/tracer/pulse-pistols.png) | [Ability Pulse Pistols.png](https://overwatch.weirdgloop.org/w/File:Ability_Pulse_Pistols.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119051243%21Ability_Pulse_Pistols.png?92e99) | 2016-06-22 |
| [heroes/tracer/blink.png](heroes/tracer/blink.png) | [Ability Blink.png](https://overwatch.weirdgloop.org/w/File:Ability_Blink.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128010342%21Ability_Blink.png?fc737) | 2014-11-12 |
| [heroes/tracer/recall.png](heroes/tracer/recall.png) | [Ability Recall.png](https://overwatch.weirdgloop.org/w/File:Ability_Recall.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Recall.png?bc069) | 2014-11-12 |
| [heroes/tracer/pulse-bomb.png](heroes/tracer/pulse-bomb.png) | [Ultimate Pulse Bomb.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Pulse_Bomb.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Pulse_Bomb.png?2545f) | 2014-11-12 |
| [heroes/tracer/melee.png](heroes/tracer/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/bastion/recon.png](heroes/bastion/recon.png) | [Ability Configuration Recon.png](https://overwatch.weirdgloop.org/w/File:Ability_Configuration_Recon.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119020945%21Ability_Configuration_Recon.png?fb66c) | 2016-06-22 |
| [heroes/bastion/reconfigure.png](heroes/bastion/reconfigure.png) | [Ability Reconfigure.png](https://overwatch.weirdgloop.org/w/File:Ability_Reconfigure.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Reconfigure.png?75818) | 2014-11-11 |
| [heroes/bastion/sentry.png](heroes/bastion/sentry.png) | [Ability Configuration Sentry.png](https://overwatch.weirdgloop.org/w/File:Ability_Configuration_Sentry.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119021021%21Ability_Configuration_Sentry.png?e491c) | 2016-06-22 |
| [heroes/bastion/self-repair.png](heroes/bastion/self-repair.png) | [Ability Self-Repair.png](https://overwatch.weirdgloop.org/w/File:Ability_Self-Repair.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Self-Repair.png?98307) | 2014-11-11 |
| [heroes/bastion/tank.png](heroes/bastion/tank.png) | [Ultimate Configuration Tank.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Configuration_Tank.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Configuration_Tank.png?6d917) | 2016-09-16 |
| [heroes/bastion/melee.png](heroes/bastion/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/hanzo/storm-bow.png](heroes/hanzo/storm-bow.png) | [Ability Storm Bow.png](https://overwatch.weirdgloop.org/w/File:Ability_Storm_Bow.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119022809%21Ability_Storm_Bow.png?f2fa3) | 2016-06-22 |
| [heroes/hanzo/sonic-arrow.png](heroes/hanzo/sonic-arrow.png) | [Ability Sonic Arrow.png](https://overwatch.weirdgloop.org/w/File:Ability_Sonic_Arrow.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128012520%21Ability_Sonic_Arrow.png?2121f) | 2014-11-11 |
| [heroes/hanzo/scatter-arrow.png](heroes/hanzo/scatter-arrow.png) | [Ability Scatter Arrow.png](https://overwatch.weirdgloop.org/w/File:Ability_Scatter_Arrow.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Scatter_Arrow.png?4070b) | 2014-11-11 |
| [heroes/hanzo/dragonstrike.png](heroes/hanzo/dragonstrike.png) | [Ultimate Dragonstrike.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Dragonstrike.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Dragonstrike.png?bdde8) | 2014-11-11 |
| [heroes/hanzo/wall-climb.png](heroes/hanzo/wall-climb.png) | [Passive Hanzo Wall Climb.png](https://overwatch.weirdgloop.org/w/File:Passive_Hanzo_Wall_Climb.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119022616%21Passive_Hanzo_Wall_Climb.png?31db8) | 2015-11-26 |
| [heroes/hanzo/melee.png](heroes/hanzo/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/junkrat/frag-launcher.png](heroes/junkrat/frag-launcher.png) | [Ability Frag Launcher.png](https://overwatch.weirdgloop.org/w/File:Ability_Frag_Launcher.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119022914%21Ability_Frag_Launcher.png?a1869) | 2016-06-22 |
| [heroes/junkrat/concussion-mine.png](heroes/junkrat/concussion-mine.png) | [Ability Concussion Mine.png](https://overwatch.weirdgloop.org/w/File:Ability_Concussion_Mine.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Concussion_Mine.png?5f08a) | 2015-09-24 |
| [heroes/junkrat/detonate.png](heroes/junkrat/detonate.png) | [Ability Concussion Mine.png](https://overwatch.weirdgloop.org/w/File:Ability_Concussion_Mine.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Concussion_Mine.png?5f08a) | 2015-09-24 |
| [heroes/junkrat/steel-trap.png](heroes/junkrat/steel-trap.png) | [Ability Steel Trap.png](https://overwatch.weirdgloop.org/w/File:Ability_Steel_Trap.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Steel_Trap.png?11d64) | 2015-09-24 |
| [heroes/junkrat/rip-tire.png](heroes/junkrat/rip-tire.png) | [Ultimate RIP-Tire.png](https://overwatch.weirdgloop.org/w/File:Ultimate_RIP-Tire.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_RIP-Tire.png?f5427) | 2015-09-24 |
| [heroes/junkrat/total-mayhem.png](heroes/junkrat/total-mayhem.png) | [Passive Total Mayhem.png](https://overwatch.weirdgloop.org/w/File:Passive_Total_Mayhem.png) | [下载](https://overwatch.weirdgloop.org/images/Passive_Total_Mayhem.png?71b58) | 2015-09-24 |
| [heroes/junkrat/melee.png](heroes/junkrat/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/mei/endothermic-blaster.png](heroes/mei/endothermic-blaster.png) | [Ability Endothermic Blaster.png](https://overwatch.weirdgloop.org/w/File:Ability_Endothermic_Blaster.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128011459%21Ability_Endothermic_Blaster.png?998df) | 2015-11-07 |
| [heroes/mei/icicle.png](heroes/mei/icicle.png) | [Ability Icicle.png](https://overwatch.weirdgloop.org/w/File:Ability_Icicle.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Icicle.png?da2c4) | 2025-10-17 |
| [heroes/mei/cryo-freeze.png](heroes/mei/cryo-freeze.png) | [Ability Cryo-Freeze.png](https://overwatch.weirdgloop.org/w/File:Ability_Cryo-Freeze.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128011526%21Ability_Cryo-Freeze.png?6ac40) | 2015-11-07 |
| [heroes/mei/ice-wall.png](heroes/mei/ice-wall.png) | [Ability Ice Wall.png](https://overwatch.weirdgloop.org/w/File:Ability_Ice_Wall.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128011554%21Ability_Ice_Wall.png?07773) | 2015-11-07 |
| [heroes/mei/blizzard.png](heroes/mei/blizzard.png) | [Ultimate Blizzard.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Blizzard.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Blizzard.png?8b5cc) | 2015-11-07 |
| [heroes/mei/melee.png](heroes/mei/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/torbjorn/rivet-gun.png](heroes/torbjorn/rivet-gun.png) | [Ability Rivet Gun.png](https://overwatch.weirdgloop.org/w/File:Ability_Rivet_Gun.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119051422%21Ability_Rivet_Gun.png?de8b8) | 2016-06-22 |
| [heroes/torbjorn/rivet-gun-secondary.png](heroes/torbjorn/rivet-gun-secondary.png) | [Ability Torbjörn Secondary Fire.png](https://overwatch.weirdgloop.org/w/File:Ability_Torbj%C3%B6rn_Secondary_Fire.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Torbj%C3%B6rn_Secondary_Fire.png?37a59) | 2026-09-25 |
| [heroes/torbjorn/build-turret.png](heroes/torbjorn/build-turret.png) | [Ability Deploy Turret.png](https://overwatch.weirdgloop.org/w/File:Ability_Deploy_Turret.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181003181032%21Ability_Deploy_Turret.png?24963) | 2014-11-12 |
| [heroes/torbjorn/armor-pack.png](heroes/torbjorn/armor-pack.png) | [Ability Armor Pack.png](https://overwatch.weirdgloop.org/w/File:Ability_Armor_Pack.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Armor_Pack.png?c4d98) | 2024-11-26 |
| [heroes/torbjorn/molten-core.png](heroes/torbjorn/molten-core.png) | [Ultimate Molten Core.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Molten_Core.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181010184103%21Ultimate_Molten_Core.png?673d0) | 2014-11-12 |
| [heroes/torbjorn/forge-hammer.png](heroes/torbjorn/forge-hammer.png) | [Ability Forge Hammer.png](https://overwatch.weirdgloop.org/w/File:Ability_Forge_Hammer.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119053937%21Ability_Forge_Hammer.png?968c4) | 2015-11-24 |
| [heroes/torbjorn/turret-repair.png](heroes/torbjorn/turret-repair.png) | [Ability Forge Hammer.png](https://overwatch.weirdgloop.org/w/File:Ability_Forge_Hammer.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119053937%21Ability_Forge_Hammer.png?968c4) | 2015-11-24 |
| [heroes/torbjorn/turret-upgrade.png](heroes/torbjorn/turret-upgrade.png) | [Ability Forge Hammer.png](https://overwatch.weirdgloop.org/w/File:Ability_Forge_Hammer.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119053937%21Ability_Forge_Hammer.png?968c4) | 2015-11-24 |
| [heroes/torbjorn/scrap-collector.png](heroes/torbjorn/scrap-collector.png) | [Passive Scrap Collector.png](https://overwatch.weirdgloop.org/w/File:Passive_Scrap_Collector.png) | [下载](https://overwatch.weirdgloop.org/images/Passive_Scrap_Collector.png?14214) | 2015-11-23 |
| [heroes/torbjorn/melee.png](heroes/torbjorn/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/widowmaker/widows-kiss.png](heroes/widowmaker/widows-kiss.png) | [Ability Widow's Kiss.png](https://overwatch.weirdgloop.org/w/File:Ability_Widow%27s_Kiss.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119054153%21Ability_Widow%27s_Kiss.png?3f0d8) | 2016-06-22 |
| [heroes/widowmaker/widows-kiss-scoped.png](heroes/widowmaker/widows-kiss-scoped.png) | [Ability Widow's Kiss.png](https://overwatch.weirdgloop.org/w/File:Ability_Widow%27s_Kiss.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119054153%21Ability_Widow%27s_Kiss.png?3f0d8) | 2016-06-22 |
| [heroes/widowmaker/grappling-hook.png](heroes/widowmaker/grappling-hook.png) | [Ability Grappling Hook.png](https://overwatch.weirdgloop.org/w/File:Ability_Grappling_Hook.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Grappling_Hook.png?60def) | 2014-11-12 |
| [heroes/widowmaker/venom-mine.png](heroes/widowmaker/venom-mine.png) | [Ability Venom Mine.png](https://overwatch.weirdgloop.org/w/File:Ability_Venom_Mine.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Venom_Mine.png?4ba39) | 2014-11-12 |
| [heroes/widowmaker/infra-sight.png](heroes/widowmaker/infra-sight.png) | [Ultimate Infra-Sight.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Infra-Sight.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Infra-Sight.png?d7911) | 2014-11-12 |
| [heroes/widowmaker/melee.png](heroes/widowmaker/melee.png) | [Quick melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/roadhog/portrait.png](heroes/roadhog/portrait.png) | [Icon-Roadhog.png](https://overwatch.weirdgloop.org/w/File:Icon-Roadhog.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019024332%21Icon-Roadhog.png?6e6cc) | 2015-10-21 |
| [heroes/roadhog/scrap-gun.png](heroes/roadhog/scrap-gun.png) | [Ability_Scrap_Gun.png](https://overwatch.weirdgloop.org/w/File:Ability_Scrap_Gun.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119025357%21Ability_Scrap_Gun.png?88e05) | 2015-09-24 |
| [heroes/roadhog/scrap-gun-secondary.png](heroes/roadhog/scrap-gun-secondary.png) | [Ability_Scrap_Gun.png](https://overwatch.weirdgloop.org/w/File:Ability_Scrap_Gun.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119025357%21Ability_Scrap_Gun.png?88e05) | 2015-09-24 |
| [heroes/roadhog/chain-hook.png](heroes/roadhog/chain-hook.png) | [Ability_Chain_Hook.png](https://overwatch.weirdgloop.org/w/File:Ability_Chain_Hook.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20260810145623%21Ability_Chain_Hook.png?e9105) | 2015-09-24 |
| [heroes/roadhog/take-a-breather.png](heroes/roadhog/take-a-breather.png) | [Ability_Take_a_Breather.png](https://overwatch.weirdgloop.org/w/File:Ability_Take_a_Breather.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Take_a_Breather.png?58040) | 2015-09-24 |
| [heroes/roadhog/whole-hog.png](heroes/roadhog/whole-hog.png) | [Ultimate_Whole_Hog.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Whole_Hog.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20221128013700%21Ultimate_Whole_Hog.png?f998f) | 2015-09-24 |
| [heroes/roadhog/melee.png](heroes/roadhog/melee.png) | [Quick_melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |
| [heroes/winston/portrait.png](heroes/winston/portrait.png) | [Icon-Winston.png](https://overwatch.weirdgloop.org/w/File:Icon-Winston.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181019025022%21Icon-Winston.png?e212f) | 2014-11-07 |
| [heroes/winston/tesla-cannon.png](heroes/winston/tesla-cannon.png) | [Ability_Tesla_Cannon.png](https://overwatch.weirdgloop.org/w/File:Ability_Tesla_Cannon.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119054432%21Ability_Tesla_Cannon.png?9d777) | 2016-07-03 |
| [heroes/winston/jump-pack.png](heroes/winston/jump-pack.png) | [Ability_Jump_Pack.png](https://overwatch.weirdgloop.org/w/File:Ability_Jump_Pack.png) | [下载](https://overwatch.weirdgloop.org/images/archive/20181119054304%21Ability_Jump_Pack.png?65a70) | 2014-11-12 |
| [heroes/winston/barrier-projector.png](heroes/winston/barrier-projector.png) | [Ability_Barrier_Projector.png](https://overwatch.weirdgloop.org/w/File:Ability_Barrier_Projector.png) | [下载](https://overwatch.weirdgloop.org/images/Ability_Barrier_Projector.png?f022a) | 2014-11-12 |
| [heroes/winston/primal-rage.png](heroes/winston/primal-rage.png) | [Ultimate_Primal_Rage.png](https://overwatch.weirdgloop.org/w/File:Ultimate_Primal_Rage.png) | [下载](https://overwatch.weirdgloop.org/images/Ultimate_Primal_Rage.png?fa61e) | 2014-11-12 |
| [heroes/winston/melee.png](heroes/winston/melee.png) | [Quick_melee.png](https://overwatch.weirdgloop.org/w/File:Quick_melee.png) | [下载](https://overwatch.weirdgloop.org/images/Quick_melee.png?4277c) | 2019-04-10 |

## B 站视频封面

`bilibili-cover.jpg`：作者提供的 B 站视频封面，1280×720 JPEG，链接 https://www.bilibili.com/video/BV1DzWn6zE6W/ 。
