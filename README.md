<div align="center">
  <img src="assets/launcher/owmc.png" width="128" alt="Overwatch × Minecraft logo">
  <h1>Overwatch × Minecraft</h1>
  <p><strong>在 Minecraft 的方块世界里，用原版守望先锋英雄开战。</strong></p>
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
    <a href="https://space.bilibili.com/13152709">B 站主页</a> ·
    <a href="README.en.md">English</a>
  </p>
</div>

项目连接 **2016 年守望先锋离线测试版 0.8.0.24919** 与 **Minecraft 1.21.1（Fabric）**。在守望先锋窗口游玩，世界进度由 Minecraft 保存。

这是非商业粉丝项目，与暴雪娱乐、Mojang 或微软无关。源码仓库不提供游戏客户端、模型或语音等运行资源。演示画面和图标的权利归原作者。

## 演示

<p align="center">
  <img src="docs/media/heroes-12.gif" width="768" alt="12 位英雄在 Minecraft 世界中的实机演示">
</p>

<p align="center"><sub><a href="docs/media/README.md">演示素材来源</a></sub></p>

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
      操控包括路霸和温斯顿在内的 14 位英雄，保留原版手模、武器动画、HUD 和声音。
    </td>
    <td width="33%" valign="top">
      <strong>🌍 真实世界</strong><br>
      探索地形、生物和维度。Minecraft 处理移动、碰撞与存档。
    </td>
    <td width="33%" valign="top">
      <strong>⚔️ 生存与训练</strong><br>
      按 <kbd>F5</kbd> 召唤训练 NPC 或切换生存与无敌模式。英雄和训练 NPC 免疫掉落伤害。
    </td>
  </tr>
  <tr>
    <td width="33%" valign="top">
      <strong>🧭 世界工具</strong><br>
      切换飞行、调整时间、建造传送门、召唤怪物、前往 Boss 区域，或一键充满大招、恢复冷却。
    </td>
    <td width="33%" valign="top">
      <strong>🌲 暮色森林与光影</strong><br>
      探索暮色森林等已安装模组提供的维度，可选 Iris / MakeUp 光影。
    </td>
    <td width="33%" valign="top">
      <strong>🚀 一键启动</strong><br>
      双击启动器加载世界并进入英雄选择界面，退出时保存世界。
    </td>
  </tr>
</table>

## 下载

<!-- DOWNLOAD_LINKS -->
<div align="center">
  <h3><a href="https://pan.baidu.com/s/1dt433i2fr2vXsVXvQznhUg?pwd=1234">⬇ 百度网盘下载 OWMC v1.0.0</a></h3>
  <p><code>OWMC-1.0.0.zip</code> · <strong>5.46 GB</strong></p>
  <p>提取码 <kbd>1234</kbd> · 更新于 <strong>2026-11-08</strong></p>
  <p><strong>SHA256</strong> <code>58d08b12f640c368419c91e9177f80ec840ed627aed24322cd9634935de547aa</code></p>
</div>
<!-- /DOWNLOAD_LINKS -->

## 快速开始

1. 完整解压 `OWMC-1.0.0.zip`，双击 **`ow x mc 启动器.exe`**。
2. 等待英雄选择界面，选人后开始游玩。如果关闭了“打开即启动”，先点击“开始游戏”。
3. 退出时点击启动器中的 **“结束游戏”**，等待世界保存完成。

<p align="center"><img src="docs/media/launcher.png" width="640" alt="启动器主页"></p>

**系统要求**　Windows 10 2004+ 或 Windows 11（64 位），显卡支持 Direct3D 11 和 OpenGL。至少 8 GB 内存，推荐 16 GB，预留约 20 GB 磁盘空间。

整合包自带 Python 和 Java 运行时。ZIP 超过 FAT32 的单文件上限，请解压到 NTFS 或 exFAT 磁盘。

安装、运行库、日志和故障排查见[玩家说明](docs/PLAYER-README.md)。

## 按键

游玩时请让守望先锋窗口保持焦点。部分笔记本使用功能键时需同时按住 <kbd>Fn</kbd>。

| 🎮 移动与战斗 | 作用 | | ⚙️ 菜单与功能键 | 作用 |
| :---: | --- | --- | :---: | --- |
| <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd> | 🏃 移动 | | <kbd>H</kbd> | 🦸 返回英雄选择 |
| <kbd>🖱️ 鼠标</kbd> | 👀 转向 | | <kbd>F5</kbd> | 🧑‍🤝‍🧑 英雄召唤 / 生存模式 |
| <kbd>空格</kbd> | ⤴️ 跳跃 / 飞行时上升 | | <kbd>F6</kbd> | 🕊️ 飞行 |
| <kbd>Ctrl</kbd> | ⤵️ 飞行时下降 | | <kbd>F7</kbd> | 🌤️ 世界设置 |
| <kbd>🖱️ 左键</kbd> | 🔫 主攻击 | | <kbd>F8</kbd> | 🌀 传送门 |
| <kbd>🖱️ 右键</kbd> | 🎯 次攻击 | | <kbd>F9</kbd> | 👾 怪物召唤 |
| <kbd>R</kbd> | 🔄 装弹 | | <kbd>F10</kbd> | 🐉 Boss 入口 |
| <kbd>V</kbd> | 👊 近战 | | <kbd>F11</kbd> | 🔋 大招充能 / 冷却恢复 |
| <kbd>Shift</kbd> | ✨ 技能 1 | |  |  |
| <kbd>E</kbd> | ✨ 技能 2 | |  |  |
| <kbd>Q</kbd> | 💥 终极技能 | |  |  |

菜单支持主键盘和数字小键盘，翻页和返回请按界面提示。

## 英雄还原进度

**14 位英雄 · 89 项技能与机制 · ✅ 86 项已还原 · 🚧 1 项部分还原 · ❌ 2 项未还原**

麦克雷、小美、托比昂、黑百合、路霸、温斯顿的全部技能均已实机确认。点击英雄名展开技能表。[图标来源](docs/media/README.md#图标规格)。

<details>
<summary><h3><img src="docs/media/heroes/genji/portrait.png" width="40" height="40" align="absmiddle" alt="源氏">&nbsp; 源氏 &nbsp;<code>✅ 8/8 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/genji/shuriken.png" width="32" height="32" alt="手里剑"> | 手里剑 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/shuriken-fan.png" width="32" height="32" alt="扇形手里剑"> | 扇形手里剑 | <kbd>🖱️ 右键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/swift-strike.png" width="32" height="32" alt="疾影"> | 疾影 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/deflect.png" width="32" height="32" alt="闪"> | 闪 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/dragonblade.png" width="32" height="32" alt="龙刃"> | 龙刃 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/double-jump.png" width="32" height="32" alt="二段跳"> | 二段跳 | <kbd>空格</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/wall-climb.png" width="32" height="32" alt="爬墙"> | 爬墙 | <kbd>空格</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/genji/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/mccree/portrait.png" width="40" height="40" align="absmiddle" alt="麦克雷">&nbsp; 麦克雷 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mccree/peacekeeper.png" width="32" height="32" alt="维和者"> | 维和者 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/fan-the-hammer.png" width="32" height="32" alt="六连发"> | 六连发 | <kbd>🖱️ 右键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/combat-roll.png" width="32" height="32" alt="战术翻滚"> | 战术翻滚 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/flashbang.png" width="32" height="32" alt="闪光弹"> | 闪光弹 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/deadeye.png" width="32" height="32" alt="神射手"> | 神射手 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mccree/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/pharah/portrait.png" width="40" height="40" align="absmiddle" alt="法老之鹰">&nbsp; 法老之鹰 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/pharah/rocket-launcher.png" width="32" height="32" alt="火箭发射器"> | 火箭发射器 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/jump-jet.png" width="32" height="32" alt="推进背包"> | 推进背包 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/concussive-blast.png" width="32" height="32" alt="震荡冲击"> | 震荡冲击 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/barrage.png" width="32" height="32" alt="火箭弹幕"> | 火箭弹幕 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/hover-jets.png" width="32" height="32" alt="悬浮"> | 悬浮 | <kbd>空格</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/pharah/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/reaper/portrait.png" width="40" height="40" align="absmiddle" alt="死神">&nbsp; 死神 &nbsp;<code>🚧 5/6 已还原</code> <sub>1 项未还原</sub></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/reaper/hellfire-shotguns.png" width="32" height="32" alt="地狱火霰弹枪"> | 地狱火霰弹枪 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/wraith-form.png" width="32" height="32" alt="幽灵形态"> | 幽灵形态 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/shadow-step.png" width="32" height="32" alt="暗影步"> | 暗影步 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/reaper/death-blossom.png" width="32" height="32" alt="死亡绽放"> | 死亡绽放 | <kbd>Q</kbd> | ❌ 未还原 |
| <img src="docs/media/heroes/reaper/the-reaping.png" width="32" height="32" alt="灵魂收割"> | 灵魂收割 | 被动 | ✅ 已还原 · 拾取后恢复生命值 |
| <img src="docs/media/heroes/reaper/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/soldier76/portrait.png" width="40" height="40" align="absmiddle" alt="士兵：76">&nbsp; 士兵：76 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/soldier76/heavy-pulse-rifle.png" width="32" height="32" alt="重型脉冲步枪"> | 重型脉冲步枪 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/helix-rockets.png" width="32" height="32" alt="螺旋飞弹"> | 螺旋飞弹 | <kbd>🖱️ 右键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/sprint.png" width="32" height="32" alt="疾跑"> | 疾跑 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/biotic-field.png" width="32" height="32" alt="生物力场"> | 生物力场 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/tactical-visor.png" width="32" height="32" alt="战术目镜"> | 战术目镜 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/soldier76/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/tracer/portrait.png" width="40" height="40" align="absmiddle" alt="猎空">&nbsp; 猎空 &nbsp;<code>✅ 5/5 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/tracer/pulse-pistols.png" width="32" height="32" alt="脉冲双枪"> | 脉冲双枪 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/blink.png" width="32" height="32" alt="闪现"> | 闪现 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/recall.png" width="32" height="32" alt="闪回"> | 闪回 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/pulse-bomb.png" width="32" height="32" alt="脉冲炸弹"> | 脉冲炸弹 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/tracer/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/bastion/portrait.png" width="40" height="40" align="absmiddle" alt="堡垒">&nbsp; 堡垒 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/bastion/recon.png" width="32" height="32" alt="侦察模式"> | 侦察模式 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/reconfigure.png" width="32" height="32" alt="模式切换"> | 模式切换 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/sentry.png" width="32" height="32" alt="哨卫模式"> | 哨卫模式 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/self-repair.png" width="32" height="32" alt="自我修复"> | 自我修复 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/tank.png" width="32" height="32" alt="坦克模式"> | 坦克模式 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/bastion/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/hanzo/portrait.png" width="40" height="40" align="absmiddle" alt="半藏">&nbsp; 半藏 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/hanzo/storm-bow.png" width="32" height="32" alt="风"> | 风 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/sonic-arrow.png" width="32" height="32" alt="音"> | 音 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/scatter-arrow.png" width="32" height="32" alt="散"> | 散 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/dragonstrike.png" width="32" height="32" alt="竜"> | 竜 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/wall-climb.png" width="32" height="32" alt="攀墙"> | 攀墙 | <kbd>空格</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/hanzo/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/junkrat/portrait.png" width="40" height="40" align="absmiddle" alt="狂鼠">&nbsp; 狂鼠 &nbsp;<code>🚧 5/7 已还原</code> <sub>1 项部分还原，1 项未还原</sub></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/junkrat/frag-launcher.png" width="32" height="32" alt="弹跳榴弹"> | 弹跳榴弹 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/concussion-mine.png" width="32" height="32" alt="震荡地雷"> | 震荡地雷 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/detonate.png" width="32" height="32" alt="地雷引爆"> | 地雷引爆 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/steel-trap.png" width="32" height="32" alt="捕兽夹"> | 捕兽夹 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/junkrat/rip-tire.png" width="32" height="32" alt="炸弹轮胎·驾驶"> | 炸弹轮胎·驾驶 | <kbd>Q</kbd> | ❌ 未还原 |
| <img src="docs/media/heroes/junkrat/total-mayhem.png" width="32" height="32" alt="垂死挣扎"> | 垂死挣扎 | 被动 | 🚧 部分还原 · 画面表现不完整 |
| <img src="docs/media/heroes/junkrat/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/mei/portrait.png" width="40" height="40" align="absmiddle" alt="小美">&nbsp; 小美 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mei/endothermic-blaster.png" width="32" height="32" alt="冰冻喷雾"> | 冰冻喷雾 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mei/icicle.png" width="32" height="32" alt="冰锥"> | 冰锥 | <kbd>🖱️ 右键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mei/cryo-freeze.png" width="32" height="32" alt="急冻"> | 急冻 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mei/ice-wall.png" width="32" height="32" alt="冰墙"> | 冰墙 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mei/blizzard.png" width="32" height="32" alt="暴雪"> | 暴雪 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/mei/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/torbjorn/portrait.png" width="40" height="40" align="absmiddle" alt="托比昂">&nbsp; 托比昂 &nbsp;<code>✅ 10/10 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/torbjorn/rivet-gun.png" width="32" height="32" alt="铆钉枪"> | 铆钉枪 | <kbd>1</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/rivet-gun-secondary.png" width="32" height="32" alt="霰弹铆钉"> | 霰弹铆钉 | <kbd>1</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/build-turret.png" width="32" height="32" alt="部署炮台"> | 部署炮台 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/armor-pack.png" width="32" height="32" alt="护甲包"> | 护甲包 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/molten-core.png" width="32" height="32" alt="熔火核心"> | 熔火核心 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/forge-hammer.png" width="32" height="32" alt="锻造锤"> | 锻造锤 | <kbd>2</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/turret-repair.png" width="32" height="32" alt="炮台修理"> | 炮台修理 | <kbd>2</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/turret-upgrade.png" width="32" height="32" alt="炮台升级"> | 炮台升级 | <kbd>2</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/scrap-collector.png" width="32" height="32" alt="废料收集"> | 废料收集 | 被动 | ✅ 已还原 |
| <img src="docs/media/heroes/torbjorn/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/widowmaker/portrait.png" width="40" height="40" align="absmiddle" alt="黑百合">&nbsp; 黑百合 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/widowmaker/widows-kiss.png" width="32" height="32" alt="自动步枪"> | 自动步枪 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/widows-kiss-scoped.png" width="32" height="32" alt="狙击模式"> | 狙击模式 | <kbd>🖱️ 右键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/grappling-hook.png" width="32" height="32" alt="抓钩"> | 抓钩 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/venom-mine.png" width="32" height="32" alt="剧毒诡雷"> | 剧毒诡雷 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/infra-sight.png" width="32" height="32" alt="红外侦测"> | 红外侦测 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/widowmaker/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/roadhog/portrait.png" width="40" height="40" align="absmiddle" alt="路霸">&nbsp; 路霸 &nbsp;<code>✅ 6/6 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/roadhog/scrap-gun.png" width="32" height="32" alt="废铁枪"> | 废铁枪 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/scrap-gun-secondary.png" width="32" height="32" alt="废铁枪次攻击"> | 废铁枪次攻击 | <kbd>🖱️ 右键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/chain-hook.png" width="32" height="32" alt="链钩"> | 链钩 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/take-a-breather.png" width="32" height="32" alt="呼吸器"> | 呼吸器 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/whole-hog.png" width="32" height="32" alt="鸡飞狗跳"> | 鸡飞狗跳 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/roadhog/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

<details>
<summary><h3><img src="docs/media/heroes/winston/portrait.png" width="40" height="40" align="absmiddle" alt="温斯顿">&nbsp; 温斯顿 &nbsp;<code>✅ 5/5 全部还原</code></h3></summary>

| 图标 | 技能 | 按键 | 状态 |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/winston/tesla-cannon.png" width="32" height="32" alt="特斯拉炮"> | 特斯拉炮 | <kbd>🖱️ 左键</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/winston/jump-pack.png" width="32" height="32" alt="跳跃背包"> | 跳跃背包 | <kbd>Shift</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/winston/barrier-projector.png" width="32" height="32" alt="屏障发生器"> | 屏障发生器 | <kbd>E</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/winston/primal-rage.png" width="32" height="32" alt="原始暴怒"> | 原始暴怒 | <kbd>Q</kbd> | ✅ 已还原 |
| <img src="docs/media/heroes/winston/melee.png" width="32" height="32" alt="近战"> | 近战 | <kbd>V</kbd> | ✅ 已还原 |

</details>

## 工作原理与开发

守望先锋接收操作并渲染原版英雄，Minecraft 处理移动、碰撞和战斗结果。Minecraft 的世界画面回传到守望先锋窗口，与原版手模和 HUD 一起呈现。

<details>
<summary><strong>开发者构建</strong></summary>

开发需要 Windows x64、Python 3.13、JDK 21、Gradle 8.10.2 和 MinGW-w64。具体步骤见[构建说明](docs/BUILDING.md)，架构见[双进程方案](docs/PASSTHROUGH.md)，其余资料见[文档索引](docs/README.md)。

</details>

## 致谢与许可

感谢 [Universal Modder](https://github.com/rehan-remade/universal-modder) 的[双进程路线参考](https://github.com/rehan-remade/universal-modder/tree/main/skills/mashup-mods)、[Prometheus](https://github.com/saturn-xvi/prometheus) 的离线客户端研究，以及 Fabric、暮色森林、Sodium、Iris 和相关开源组件。项目由 Claude / Codex 辅助开发。

项目自有代码采用 [MIT License](LICENSE)，版权归 **2026 RPQ123**。第三方代码和资源适用各自许可，详见[第三方声明](THIRD_PARTY_NOTICES.md)与[组件说明](docs/THIRD-PARTY.md)。

## 作者

[在 B 站关注作者](https://space.bilibili.com/13152709)
