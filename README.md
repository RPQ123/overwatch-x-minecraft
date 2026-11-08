<div align="center">
  <img src="assets/launcher/owmc.png" width="128" alt="Overwatch × Minecraft logo">
  <h1>Overwatch × Minecraft</h1>
  <p><strong>用原版守望先锋英雄，闯进真正的 Minecraft 世界。</strong></p>
  <p>
    <kbd>v1.0.0</kbd>
    <kbd>Windows x64</kbd>
    <kbd>MC 1.21.1 Fabric</kbd>
    <kbd>OW 0.8 Beta</kbd>
    <a href="LICENSE"><kbd>MIT</kbd></a>
    <kbd>14 位英雄</kbd>
  </p>
  <p>
    <a href="#演示">▶ 演示</a> ·
    <a href="#下载">下载</a> ·
    <a href="#快速开始">快速开始</a> ·
    <a href="#按键">按键</a> ·
    <a href="#英雄还原进度">英雄技能</a> ·
    <a href="README.en.md">English</a>
  </p>
</div>

项目将 **2016 年守望先锋离线测试版 0.8.0.24919** 与 **Minecraft 1.21.1** 连接起来。守望先锋提供英雄、武器、动画、HUD 和声音，Minecraft 提供地形、生物、移动、碰撞和存档。玩家在守望先锋窗口中游玩。

这是非商业粉丝项目，与暴雪娱乐、Mojang、微软无关。游戏客户端、模型、语音等运行资源不随源码仓库提供；演示图片和图标的权利归原作者。

## 演示

<p align="center">
  <img src="docs/media/heroes-12.gif" width="768" alt="12 位英雄在 Minecraft 世界中的实机演示">
</p>

<p align="center"><sub>宣传片链接待补 · <a href="docs/media/README.md">演示素材来源</a></sub></p>

<table>
  <tr>
    <td width="50%" align="center">
      <img src="docs/media/genji-shuriken.jpg" width="440" alt="源氏 · 手里剑与 HUD"><br>
      <sub>源氏 · 手里剑与 HUD</sub>
    </td>
    <td width="50%" align="center">
      <img src="docs/media/widowmaker-sniper.jpg" width="440" alt="黑百合 · Minecraft 生物"><br>
      <sub>黑百合 · Minecraft 生物</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="docs/media/mei-freeze.jpg" width="440" alt="小美 · 冰冻喷雾"><br>
      <sub>小美 · 冰冻喷雾</sub>
    </td>
    <td width="50%" align="center">
      <img src="docs/media/twilight-forest.jpg" width="440" alt="麦克雷 · 暮色森林"><br>
      <sub>麦克雷 · 暮色森林</sub>
    </td>
  </tr>
</table>

## 特性

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>🎯 原版英雄</strong><br>
      14 位英雄保留原版手模、武器动画、HUD 和声音，阵容包含路霸和温斯顿。
    </td>
    <td width="33%" valign="top">
      <strong>🌍 真实世界</strong><br>
      探索地形、生物和维度。Minecraft 负责移动、碰撞与存档。
    </td>
    <td width="33%" valign="top">
      <strong>⚔️ 生存与训练</strong><br>
      F5 召唤英雄训练 NPC，切换生存或无敌。英雄与训练 NPC 免疫掉落伤害。
    </td>
  </tr>
  <tr>
    <td width="33%" valign="top">
      <strong>🧭 世界工具</strong><br>
      飞行、调时间、建传送门、召唤怪物、进入 Boss 区域和补充技能资源。
    </td>
    <td width="33%" valign="top">
      <strong>🌲 暮色森林与光影</strong><br>
      探索已安装的维度模组，可选 Iris / MakeUp 光影。
    </td>
    <td width="33%" valign="top">
      <strong>🚀 一键启动</strong><br>
      双击启动器进入英雄选择，结束游戏时保存世界。
    </td>
  </tr>
</table>

## 下载

<!-- DOWNLOAD_LINKS -->
**OWMC v1.0.0 整合包（`OWMC-1.0.0.zip`，5.46 GB）**。下载链接待补。

此下载区对应按当前开发版重建的整合包，包含英雄与生存更新。

备用链接待补 · SHA256：`8b4069c050b40af85574fa1d0fb94c9e5a8009b6616946227e6f13cb3318c226`
<!-- /DOWNLOAD_LINKS -->

## 快速开始

<p align="center"><img src="docs/media/launcher.png" width="640" alt="启动器主页"></p>

取得完整整合包后：

1. 完整解压 ZIP，双击 **`ow x mc 启动器.exe`**。
2. 等待英雄选择界面，选人后开始游玩。若关闭了“打开即启动”，先点击“开始游戏”。
3. 退出时点击启动器中的 **“结束游戏”**，等待存档完成。

需要 Windows 10 2004+ / Windows 11 x64、支持 Direct3D 11 和 OpenGL 的显卡，至少 8 GB 内存（建议 16 GB），预留约 20 GB 空间。整合包自带运行时，无需另装 Python 或 Java。请解压到 NTFS / exFAT 磁盘；ZIP 超过 FAT32 的单文件限制。

安装、运行库、日志和故障处理见[玩家说明](docs/PLAYER-README.md)。

## 按键

操作时让守望先锋窗口保持焦点；部分笔记本需要配合 `Fn`。

| 按键 | 功能 | 按键 | 功能 |
| --- | --- | --- | --- |
| WASD / 鼠标 | 移动 / 转向 | H | 返回英雄选择 |
| 空格 / Ctrl | 跳跃；飞行时上升 / 下降 | F5 | 英雄召唤 / 生存模式 |
| 鼠标左键 / 右键 | 主攻击 / 次攻击 | F6 / F7 | 飞行 / 世界设置 |
| R / V | 装弹 / 近战 | F8 / F9 | 传送门 / 怪物召唤 |
| Shift / E / Q | 英雄技能 / 终极技能 | F10 / F11 | Boss 入口 / 技能资源补充 |

菜单使用主键盘或小键盘数字选择，按屏幕提示翻页和返回。

## 英雄还原进度

**14 位英雄 · 89 项技能与机制 · ✅ 86 项已还原 · 🚧 1 项部分 · ❌ 2 项未还原**

麦克雷、小美、托比昂、黑百合、路霸、温斯顿的全部技能均已实机确认。展开任意英雄可查看按键与状态。[图标来源](docs/media/README.md#图标规格)。

<details>
<summary><img src="docs/media/heroes/genji/portrait.png" width="24" height="24" alt="源氏"> <strong>源氏</strong> · 8/8 已还原</summary>

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

</details>

<details>
<summary><img src="docs/media/heroes/mccree/portrait.png" width="24" height="24" alt="麦克雷"> <strong>麦克雷</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mccree/peacekeeper.png" width="32" height="32" alt="维和者"> | 维和者 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/fan-the-hammer.png" width="32" height="32" alt="六连发"> | 六连发 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/combat-roll.png" width="32" height="32" alt="战术翻滚"> | 战术翻滚 | W + Shift | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/flashbang.png" width="32" height="32" alt="闪光弹"> | 闪光弹 | E | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/deadeye.png" width="32" height="32" alt="神射手"> | 神射手 | Q → 等锁定 → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/pharah/portrait.png" width="24" height="24" alt="法老之鹰"> <strong>法老之鹰</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/pharah/rocket-launcher.png" width="32" height="32" alt="火箭发射器"> | 火箭发射器 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/jump-jet.png" width="32" height="32" alt="推进背包"> | 推进背包 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/concussive-blast.png" width="32" height="32" alt="震荡冲击"> | 震荡冲击 | E | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/barrage.png" width="32" height="32" alt="火箭弹幕"> | 火箭弹幕 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/hover-jets.png" width="32" height="32" alt="悬浮"> | 悬浮 | 空中按住空格 | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/reaper/portrait.png" width="24" height="24" alt="死神"> <strong>死神</strong> · 5/6 已还原 · 1 未还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/reaper/hellfire-shotguns.png" width="32" height="32" alt="地狱火霰弹枪"> | 地狱火霰弹枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/wraith-form.png" width="32" height="32" alt="幽灵形态"> | 幽灵形态 | Shift + W | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/shadow-step.png" width="32" height="32" alt="暗影步"> | 暗影步 | E → 左键确认 | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/death-blossom.png" width="32" height="32" alt="死亡绽放"> | 死亡绽放 | Q | ❌ 未还原 |
| <img src="docs/media/heroes/reaper/the-reaping.png" width="32" height="32" alt="灵魂收割"> | 灵魂收割 | 有效击杀后靠近拾取 | ✅ 已还原 · 治疗已实测，受害者头颅呈现待复测 |
| <img src="docs/media/heroes/reaper/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/soldier76/portrait.png" width="24" height="24" alt="士兵：76"> <strong>士兵：76</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/soldier76/heavy-pulse-rifle.png" width="32" height="32" alt="重型脉冲步枪"> | 重型脉冲步枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/helix-rockets.png" width="32" height="32" alt="螺旋飞弹"> | 螺旋飞弹 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/sprint.png" width="32" height="32" alt="疾跑"> | 疾跑 | W + Shift | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/biotic-field.png" width="32" height="32" alt="生物力场"> | 生物力场 | E | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/tactical-visor.png" width="32" height="32" alt="战术目镜"> | 战术目镜 | Q → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/tracer/portrait.png" width="24" height="24" alt="猎空"> <strong>猎空</strong> · 5/5 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/tracer/pulse-pistols.png" width="32" height="32" alt="脉冲双枪"> | 脉冲双枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/blink.png" width="32" height="32" alt="闪现"> | 闪现 | W + Shift | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/recall.png" width="32" height="32" alt="闪回"> | 闪回 | 先移动 → E | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/pulse-bomb.png" width="32" height="32" alt="脉冲炸弹"> | 脉冲炸弹 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/bastion/portrait.png" width="24" height="24" alt="堡垒"> <strong>堡垒</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/bastion/recon.png" width="32" height="32" alt="侦察模式"> | 侦察模式 | 侦察形态左键 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/reconfigure.png" width="32" height="32" alt="模式切换"> | 模式切换 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/sentry.png" width="32" height="32" alt="哨卫模式"> | 哨卫模式 | Shift → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/self-repair.png" width="32" height="32" alt="自我修复"> | 自我修复 | E 按住 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/tank.png" width="32" height="32" alt="坦克模式"> | 坦克模式 | Q → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/hanzo/portrait.png" width="24" height="24" alt="半藏"> <strong>半藏</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/hanzo/storm-bow.png" width="32" height="32" alt="风"> | 风 | 按住左键 → 松开 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/sonic-arrow.png" width="32" height="32" alt="音"> | 音 | Shift → 蓄力左键松开 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/scatter-arrow.png" width="32" height="32" alt="散"> | 散 | E → 蓄力左键松开 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/dragonstrike.png" width="32" height="32" alt="竜"> | 竜 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/wall-climb.png" width="32" height="32" alt="攀墙"> | 攀墙 | 面墙 W + 空格 | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/junkrat/portrait.png" width="24" height="24" alt="狂鼠"> <strong>狂鼠</strong> · 5/7 已还原 · 1 部分 · 1 未还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/junkrat/frag-launcher.png" width="32" height="32" alt="弹跳榴弹"> | 弹跳榴弹 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/concussion-mine.png" width="32" height="32" alt="震荡地雷"> | 震荡地雷 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/detonate.png" width="32" height="32" alt="地雷引爆"> | 地雷引爆 | Shift → 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/steel-trap.png" width="32" height="32" alt="捕兽夹"> | 捕兽夹 | E | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/rip-tire.png" width="32" height="32" alt="炸弹轮胎·驾驶"> | 炸弹轮胎·驾驶 | Q → W；贴墙可空格 | ❌ 未还原 |
| <img src="docs/media/heroes/junkrat/total-mayhem.png" width="32" height="32" alt="垂死挣扎"> | 垂死挣扎 | MC 真实死亡后自动掉落 | 🚧 部分：画面待完善 |
| <img src="docs/media/heroes/junkrat/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/mei/portrait.png" width="24" height="24" alt="小美"> <strong>小美</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mei/endothermic-blaster.png" width="32" height="32" alt="冰冻喷雾"> | 冰冻喷雾 | 按住左键 | ✅ 已还原 |
| <img src="docs/media/heroes/mei/icicle.png" width="32" height="32" alt="冰锥"> | 冰锥 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/mei/cryo-freeze.png" width="32" height="32" alt="急冻"> | 急冻 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/mei/ice-wall.png" width="32" height="32" alt="冰墙"> | 冰墙 | E 预览，左键确认，E / 右键取消 | ✅ 已还原 |
| <img src="docs/media/heroes/mei/blizzard.png" width="32" height="32" alt="暴雪"> | 暴雪 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/mei/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/torbjorn/portrait.png" width="24" height="24" alt="托比昂"> <strong>托比昂</strong> · 10/10 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/torbjorn/rivet-gun.png" width="32" height="32" alt="铆钉枪"> | 铆钉枪 | 1 → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/rivet-gun-secondary.png" width="32" height="32" alt="霰弹铆钉"> | 霰弹铆钉 | 1 → 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/build-turret.png" width="32" height="32" alt="部署炮台"> | 部署炮台 | Shift 预览，左键确认，右键取消 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/armor-pack.png" width="32" height="32" alt="护甲包"> | 护甲包 | E | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/molten-core.png" width="32" height="32" alt="熔火核心"> | 熔火核心 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/forge-hammer.png" width="32" height="32" alt="锻造锤"> | 锻造锤 | 2 → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/turret-repair.png" width="32" height="32" alt="炮台修理"> | 炮台修理 | 2 → 对损坏炮台左键 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/turret-upgrade.png" width="32" height="32" alt="炮台升级"> | 炮台升级 | 2 → 对一级炮台左键 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/scrap-collector.png" width="32" height="32" alt="废料收集"> | 废料收集 | 有效击杀后靠近拾取 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/widowmaker/portrait.png" width="24" height="24" alt="黑百合"> <strong>黑百合</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/widowmaker/widows-kiss.png" width="32" height="32" alt="自动步枪"> | 自动步枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/widows-kiss-scoped.png" width="32" height="32" alt="狙击模式"> | 狙击模式 | 按住右键 → 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/grappling-hook.png" width="32" height="32" alt="抓钩"> | 抓钩 | Shift 发射，再按 Shift 或空格取消 | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/venom-mine.png" width="32" height="32" alt="剧毒诡雷"> | 剧毒诡雷 | E | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/infra-sight.png" width="32" height="32" alt="红外侦测"> | 红外侦测 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/roadhog/portrait.png" width="24" height="24" alt="路霸"> <strong>路霸</strong> · 6/6 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/roadhog/scrap-gun.png" width="32" height="32" alt="废铁枪"> | 废铁枪 | 左键 | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/scrap-gun-secondary.png" width="32" height="32" alt="废铁枪次攻击"> | 废铁枪次攻击 | 右键 | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/chain-hook.png" width="32" height="32" alt="链钩"> | 链钩 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/take-a-breather.png" width="32" height="32" alt="呼吸器"> | 呼吸器 | E | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/whole-hog.png" width="32" height="32" alt="鸡飞狗跳"> | 鸡飞狗跳 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

<details>
<summary><img src="docs/media/heroes/winston/portrait.png" width="24" height="24" alt="温斯顿"> <strong>温斯顿</strong> · 5/5 已还原</summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/winston/tesla-cannon.png" width="32" height="32" alt="特斯拉炮"> | 特斯拉炮 | 按住左键 | ✅ 已还原 |
| <img src="docs/media/heroes/winston/jump-pack.png" width="32" height="32" alt="跳跃背包"> | 跳跃背包 | Shift | ✅ 已还原 |
| <img src="docs/media/heroes/winston/barrier-projector.png" width="32" height="32" alt="屏障发生器"> | 屏障发生器 | E | ✅ 已还原 |
| <img src="docs/media/heroes/winston/primal-rage.png" width="32" height="32" alt="原始暴怒"> | 原始暴怒 | Q | ✅ 已还原 |
| <img src="docs/media/heroes/winston/melee.png" width="32" height="32" alt="近战"> | 近战 | V | ✅ 已还原 |

</details>

## 工作原理与开发

两个游戏同时运行：守望先锋接收操作并呈现英雄，Minecraft 处理世界与战斗结果，再把世界画面送回守望先锋窗口。

<details>
<summary><strong>开发者构建</strong></summary>

开发需要 Windows x64、Python 3.13、JDK 21、Gradle 8.10.2 和 MinGW-w64。具体步骤见[构建说明](docs/BUILDING.md)，架构见[双进程方案](docs/PASSTHROUGH.md)，其余资料见[文档索引](docs/README.md)。

</details>

## 致谢与许可

感谢 [Universal Modder](https://github.com/rehan-remade/universal-modder) 的[双进程路线参考](https://github.com/rehan-remade/universal-modder/tree/main/skills/mashup-mods)、[Prometheus](https://github.com/saturn-xvi/prometheus) 的离线客户端研究，以及 Fabric、暮色森林、Sodium、Iris 和相关开源组件。项目由 Claude / Codex 辅助开发。

项目自有代码采用 [MIT License](LICENSE)，版权归 **2026 RPQ123**。第三方代码和资源适用各自许可，详见[第三方声明](THIRD_PARTY_NOTICES.md)与[组件说明](docs/THIRD-PARTY.md)。
