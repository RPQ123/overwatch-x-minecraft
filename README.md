<div align="center">
  <img src="assets/launcher/owmc.png" width="144" alt="Overwatch × Minecraft logo">
  <h1>Overwatch × Minecraft</h1>
  <p><strong>用守望先锋的英雄，探索真正的 Minecraft 世界。</strong></p>
  <p>简体中文 · <a href="README.en.md">English</a> · <a href="#下载">下载</a> · <a href="docs/PLAYER-README.md">玩家说明</a> · <a href="docs/BUILDING.md">开发构建</a></p>
</div>

项目将 **2016 年守望先锋离线测试版 0.8.0.24919** 与 **Minecraft 1.21.1** 连接起来。守望先锋提供英雄、武器、动画、HUD 和声音，Minecraft 提供地形、生物、移动、碰撞和存档。玩家在守望先锋窗口中游玩。

这是非商业粉丝项目，与暴雪娱乐、Mojang、微软无关。游戏客户端、模型、语音等运行资源不随源码仓库提供；演示图片和图标的权利归原作者。

## 演示

<p align="center">
  <img src="docs/media/heroes-12.gif" width="640" alt="12 位英雄在 Minecraft 世界中的实机演示">
</p>

宣传片：链接待补。[演示素材来源](docs/media/README.md)。

| 原版英雄与武器 | Minecraft 世界 |
| --- | --- |
| ![源氏的手里剑与 HUD](docs/media/genji-shuriken.jpg) | ![黑百合与 Minecraft 生物](docs/media/widowmaker-sniper.jpg) |
| ![小美的冰冻喷雾](docs/media/mei-freeze.jpg) | ![麦克雷探索暮色森林](docs/media/twilight-forest.jpg) |

## 特性

- **12 位英雄**：保留原版手模、武器动画、HUD 和声音，技能可作用于 Minecraft 生物与地形。
- **真实世界**：探索、移动、方块碰撞、维度传送和存档由 Minecraft 负责。
- **游戏内菜单**：切换飞行、调整时间、建造传送门、召唤怪物、前往 Boss 区域、补充技能资源。
- **暮色森林与光影**：支持已安装的维度模组，可选 Iris / MakeUp 光影。
- **统一启动器**：自动加载世界和英雄选择界面，结束时保存世界。

开发版另有 **F5 英雄训练 NPC 召唤、生存 / 无敌切换和小美冰墙修复**，将在下个整合包版本加入。

## 下载

<!-- DOWNLOAD_LINKS -->
**OWMC-1.0.0 整合包（约 5 GB）：下载链接待补。**

备用链接：待补 · SHA256 校验文件：待补。
<!-- /DOWNLOAD_LINKS -->

## 快速开始

取得完整整合包后：

1. 完整解压 ZIP，双击 **`ow x mc 启动器.exe`**。
2. 等待英雄选择界面，选人后开始游玩。若关闭了“打开即启动”，先点击“开始游戏”。
3. 退出时点击启动器中的 **“结束游戏”**，等待存档完成。

需要 Windows 10 2004+ / Windows 11 x64、支持 Direct3D 11 和 OpenGL 的显卡，至少 8 GB 内存（建议 16 GB），预留约 20 GB 空间。整合包自带运行时，无需另装 Python 或 Java。请解压到 NTFS / exFAT 磁盘；ZIP 超过 FAT32 的单文件限制。

安装、运行库、日志和故障处理见[玩家说明](docs/PLAYER-README.md)。

## 按键

操作时让守望先锋窗口保持焦点；部分笔记本需要配合 `Fn`。

| 按键 | 功能 |
| --- | --- |
| WASD / 鼠标 | 移动 / 转向 |
| 空格 / Ctrl | 跳跃；飞行时上升 / 下降 |
| 鼠标左键 / 右键 | 主攻击 / 次攻击 |
| R / V | 装弹 / 近战 |
| Shift / E / Q | 英雄技能 / 终极技能 |
| H | 返回英雄选择 |
| F5 | 英雄召唤 / 生存模式（开发版） |
| F6 / F7 | 飞行 / 世界设置 |
| F8 / F9 | 传送门 / 怪物召唤 |
| F10 / F11 | Boss 入口 / 技能资源补充 |

菜单使用主键盘或小键盘数字选择，按屏幕提示翻页和返回。

## 英雄还原进度

**12 位英雄，78 项技能与机制：✅ 已还原 69 项 · 🚧 部分 2 项 · ❌ 未还原 7 项。**

按开发版最新结果统计，包含主次攻击、被动、近战和移动机制。小美冰墙已修复，现有 `1.0.0` 整合包待更新。[状态依据与图标来源](docs/media/README.md#技能状态与图标来源)。

### <img src="docs/media/heroes/genji/portrait.png" width="32" height="32" alt="源氏"> 源氏

8/8 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/genji/shuriken.png" width="32" height="32" alt="手里剑"> | 手里剑 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/genji/shuriken-fan.png" width="32" height="32" alt="扇形手里剑"> | 扇形手里剑 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/genji/swift-strike.png" width="32" height="32" alt="疾影"> | 疾影 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/genji/deflect.png" width="32" height="32" alt="闪"> | 闪 | E | ✅ 已还原 |
| <img src="docs/media/heroes/genji/dragonblade.png" width="32" height="32" alt="龙刃"> | 龙刃 | Q → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/genji/double-jump.png" width="32" height="32" alt="二段跳"> | 二段跳 | 空格 → 空格 | ✅ 已还原 |
| <img src="docs/media/heroes/genji/wall-climb.png" width="32" height="32" alt="爬墙"> | 爬墙 | 面墙 W + 空格 | ✅ 已还原 |
| <img src="docs/media/heroes/genji/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/mccree/portrait.png" width="32" height="32" alt="麦克雷"> 麦克雷

5/6 已还原 · 1 部分

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mccree/peacekeeper.png" width="32" height="32" alt="维和者"> | 维和者 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/fan-the-hammer.png" width="32" height="32" alt="六连发"> | 六连发 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/combat-roll.png" width="32" height="32" alt="战术翻滚"> | 战术翻滚 | W + Shift | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/flashbang.png" width="32" height="32" alt="闪光弹"> | 闪光弹 | E | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/deadeye.png" width="32" height="32" alt="神射手"> | 神射手 | Q → 等锁定 → 左键 | 🚧 部分：画面待完善 |
| <img src="docs/media/heroes/mccree/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/pharah/portrait.png" width="32" height="32" alt="法老之鹰"> 法老之鹰

6/6 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/pharah/rocket-launcher.png" width="32" height="32" alt="火箭发射器"> | 火箭发射器 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/jump-jet.png" width="32" height="32" alt="推进背包"> | 推进背包 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/concussive-blast.png" width="32" height="32" alt="震荡冲击"> | 震荡冲击 | E | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/barrage.png" width="32" height="32" alt="火箭弹幕"> | 火箭弹幕 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/hover-jets.png" width="32" height="32" alt="悬浮"> | 悬浮 | 空中按住空格 | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/reaper/portrait.png" width="32" height="32" alt="死神"> 死神

5/6 已还原 · 1 未还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/reaper/hellfire-shotguns.png" width="32" height="32" alt="地狱火霰弹枪"> | 地狱火霰弹枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/wraith-form.png" width="32" height="32" alt="幽灵形态"> | 幽灵形态 | Shift + W | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/shadow-step.png" width="32" height="32" alt="暗影步"> | 暗影步 | E → 左键确认 | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/death-blossom.png" width="32" height="32" alt="死亡绽放"> | 死亡绽放 | Q | ❌ 未还原 |
| <img src="docs/media/heroes/reaper/the-reaping.png" width="32" height="32" alt="灵魂收割"> | 灵魂收割 | 击杀 → W 拾取 | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/soldier76/portrait.png" width="32" height="32" alt="士兵：76"> 士兵：76

6/6 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/soldier76/heavy-pulse-rifle.png" width="32" height="32" alt="重型脉冲步枪"> | 重型脉冲步枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/helix-rockets.png" width="32" height="32" alt="螺旋飞弹"> | 螺旋飞弹 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/sprint.png" width="32" height="32" alt="疾跑"> | 疾跑 | W + Shift | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/biotic-field.png" width="32" height="32" alt="生物力场"> | 生物力场 | E | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/tactical-visor.png" width="32" height="32" alt="战术目镜"> | 战术目镜 | Q → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/tracer/portrait.png" width="32" height="32" alt="猎空"> 猎空

5/5 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/tracer/pulse-pistols.png" width="32" height="32" alt="脉冲双枪"> | 脉冲双枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/blink.png" width="32" height="32" alt="闪现"> | 闪现 | W + Shift | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/recall.png" width="32" height="32" alt="闪回"> | 闪回 | 先移动 → E | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/pulse-bomb.png" width="32" height="32" alt="脉冲炸弹"> | 脉冲炸弹 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/bastion/portrait.png" width="32" height="32" alt="堡垒"> 堡垒

6/6 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/bastion/recon.png" width="32" height="32" alt="侦察模式"> | 侦察模式 | 侦察形态左键 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/reconfigure.png" width="32" height="32" alt="模式切换"> | 模式切换 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/sentry.png" width="32" height="32" alt="哨卫模式"> | 哨卫模式 | Shift → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/self-repair.png" width="32" height="32" alt="自我修复"> | 自我修复 | E 按住 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/tank.png" width="32" height="32" alt="坦克模式"> | 坦克模式 | Q → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/hanzo/portrait.png" width="32" height="32" alt="半藏"> 半藏

6/6 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/hanzo/storm-bow.png" width="32" height="32" alt="风"> | 风 | 按住左键 → 松开 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/sonic-arrow.png" width="32" height="32" alt="音"> | 音 | Shift → 蓄力左键松开 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/scatter-arrow.png" width="32" height="32" alt="散"> | 散 | E → 蓄力左键松开 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/dragonstrike.png" width="32" height="32" alt="竜"> | 竜 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/wall-climb.png" width="32" height="32" alt="攀墙"> | 攀墙 | 面墙 W + 空格 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/junkrat/portrait.png" width="32" height="32" alt="狂鼠"> 狂鼠

5/7 已还原 · 1 部分 · 1 未还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/junkrat/frag-launcher.png" width="32" height="32" alt="弹跳榴弹"> | 弹跳榴弹 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/concussion-mine.png" width="32" height="32" alt="震荡地雷"> | 震荡地雷 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/detonate.png" width="32" height="32" alt="地雷引爆"> | 地雷引爆 | Shift → 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/steel-trap.png" width="32" height="32" alt="捕兽夹"> | 捕兽夹 | E | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/rip-tire.png" width="32" height="32" alt="炸弹轮胎·驾驶"> | 炸弹轮胎·驾驶 | Q → W；贴墙可空格 | ❌ 未还原 |
| <img src="docs/media/heroes/junkrat/total-mayhem.png" width="32" height="32" alt="垂死挣扎"> | 垂死挣扎 | MC 真实死亡后自动掉落 | 🚧 部分：画面待完善 |
| <img src="docs/media/heroes/junkrat/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/mei/portrait.png" width="32" height="32" alt="小美"> 小美

6/6 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mei/endothermic-blaster.png" width="32" height="32" alt="冰冻喷雾"> | 冰冻喷雾 | 按住左键 | ✅ 已还原 |
| <img src="docs/media/heroes/mei/icicle.png" width="32" height="32" alt="冰锥"> | 冰锥 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/mei/cryo-freeze.png" width="32" height="32" alt="急冻"> | 急冻 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/mei/ice-wall.png" width="32" height="32" alt="冰墙"> | 冰墙 | E → 左键确认 | ✅ 已还原（开发版） |
| <img src="docs/media/heroes/mei/blizzard.png" width="32" height="32" alt="暴雪"> | 暴雪 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/mei/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/torbjorn/portrait.png" width="32" height="32" alt="托比昂"> 托比昂

5/10 已还原 · 5 未还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/torbjorn/rivet-gun.png" width="32" height="32" alt="铆钉枪"> | 铆钉枪 | 1 → 左键 | ❌ 未还原 |
| <img src="docs/media/heroes/torbjorn/rivet-gun-secondary.png" width="32" height="32" alt="霰弹铆钉"> | 霰弹铆钉 | 1 → 右键 | ❌ 未还原 |
| <img src="docs/media/heroes/torbjorn/build-turret.png" width="32" height="32" alt="部署炮台"> | 部署炮台 | 向地面 Shift | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/armor-pack.png" width="32" height="32" alt="护甲包"> | 护甲包 | E | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/molten-core.png" width="32" height="32" alt="熔火核心"> | 熔火核心 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/forge-hammer.png" width="32" height="32" alt="锻造锤"> | 锻造锤 | 2 → 左键 | ❌ 未还原 |
| <img src="docs/media/heroes/torbjorn/turret-repair.png" width="32" height="32" alt="炮台修理"> | 炮台修理 | 2 → 对损坏炮台左键 | ❌ 未还原 |
| <img src="docs/media/heroes/torbjorn/turret-upgrade.png" width="32" height="32" alt="炮台升级"> | 炮台升级 | 2 → 对一级炮台左键 | ❌ 未还原 |
| <img src="docs/media/heroes/torbjorn/scrap-collector.png" width="32" height="32" alt="废料收集"> | 废料收集 | 真实击杀后 W 拾取 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

### <img src="docs/media/heroes/widowmaker/portrait.png" width="32" height="32" alt="黑百合"> 黑百合

6/6 已还原

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/widowmaker/widows-kiss.png" width="32" height="32" alt="自动步枪"> | 自动步枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/widows-kiss-scoped.png" width="32" height="32" alt="狙击模式"> | 狙击模式 | 按住右键 → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/grappling-hook.png" width="32" height="32" alt="抓钩"> | 抓钩 | 面向可攀墙 Shift | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/venom-mine.png" width="32" height="32" alt="剧毒诡雷"> | 剧毒诡雷 | E | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/infra-sight.png" width="32" height="32" alt="红外侦测"> | 红外侦测 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

## 工作原理与开发

两个游戏同时运行：守望先锋接收操作并呈现英雄，Minecraft 处理世界与战斗结果，再把世界画面送回守望先锋窗口。

开发需要 Windows x64、Python 3.13、JDK 21、Gradle 8.10.2 和 MinGW-w64。具体步骤见[构建说明](docs/BUILDING.md)，架构见[双进程方案](docs/PASSTHROUGH.md)，其余资料见[文档索引](docs/README.md)。

## 致谢与许可

感谢 [Universal Modder](https://github.com/rehan-remade/universal-modder) 的双进程路线参考、[Prometheus](https://github.com/saturn-xvi/prometheus) 的离线客户端研究，以及 Fabric、暮色森林、Sodium、Iris 和相关开源组件。项目由 Claude / Codex 辅助开发。

项目自有代码采用 [MIT License](LICENSE)，版权归 **2026 RPQ123**。第三方代码和资源适用各自许可，详见[第三方声明](THIRD_PARTY_NOTICES.md)与[组件说明](docs/THIRD-PARTY.md)。
