<div align="center">
  <img src="assets/launcher/owmc.png" width="128" alt="Overwatch × Minecraft logo">
  <h1>Overwatch × Minecraft</h1>
  <p><strong>Play original Overwatch heroes in a real Minecraft world.</strong></p>
  <p>
    <kbd>v1.0.0</kbd>
    <kbd>Windows x64</kbd>
    <kbd>MC 1.21.1 Fabric</kbd>
    <kbd>OW 0.8 Beta</kbd>
    <a href="LICENSE"><kbd>MIT</kbd></a>
    <kbd>14 heroes</kbd>
  </p>
  <p>
    <a href="#demo">▶ Demo</a> ·
    <a href="#download">Download</a> ·
    <a href="#quick-start">Quick start</a> ·
    <a href="#controls">Controls</a> ·
    <a href="#hero-restoration-progress">Hero abilities</a> ·
    <a href="https://space.bilibili.com/13152709">Bilibili</a> ·
    <a href="README.md">简体中文</a>
  </p>
</div>

The project connects the **2016 offline Overwatch beta 0.8.0.24919** with **Minecraft 1.21.1 (Fabric)**. You play in the Overwatch window, and Minecraft saves your world.

This is a non-commercial fan project, unaffiliated with Blizzard Entertainment, Mojang, or Microsoft. The source repository does not include game clients, models, voices, or other runtime assets. Demo footage and icons belong to their respective creators.

## Demo

<p align="center">
  <img src="docs/media/heroes-12.gif" width="768" alt="Gameplay featuring 12 heroes in Minecraft">
</p>

<p align="center"><sub><a href="docs/media/README.md">Media sources</a></sub></p>

<table>
  <tr>
    <td width="50%" align="center">
      <img src="docs/media/genji-shuriken.jpg" width="440" alt="Genji · Shuriken and HUD"><br>
      <sub>Genji · Shuriken and HUD</sub>
    </td>
    <td width="50%" align="center">
      <img src="docs/media/widowmaker-sniper.jpg" width="440" alt="Widowmaker · Minecraft creatures"><br>
      <sub>Widowmaker · Minecraft creatures</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="docs/media/mei-freeze.jpg" width="440" alt="Mei · Freeze spray"><br>
      <sub>Mei · Freeze spray</sub>
    </td>
    <td width="50%" align="center">
      <img src="docs/media/twilight-forest.jpg" width="440" alt="McCree · Twilight Forest"><br>
      <sub>McCree · Twilight Forest</sub>
    </td>
  </tr>
</table>

## Features

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>🎯 Original heroes</strong><br>
      Play 14 heroes, including Roadhog and Winston, with original first-person models, weapon animations, HUD, and sound.
    </td>
    <td width="33%" valign="top">
      <strong>🌍 A real world</strong><br>
      Explore terrain, creatures, and dimensions. Minecraft handles movement, collisions, and saves.
    </td>
    <td width="33%" valign="top">
      <strong>⚔️ Survival and training</strong><br>
      Press <kbd>F5</kbd> to summon training NPCs or switch between survival and invulnerability. Heroes and training NPCs are immune to fall damage.
    </td>
  </tr>
  <tr>
    <td width="33%" valign="top">
      <strong>🧭 World tools</strong><br>
      Toggle flight, set the time, build portals, summon mobs, travel to boss areas, or instantly charge your ultimate and reset cooldowns.
    </td>
    <td width="33%" valign="top">
      <strong>🌲 Twilight Forest and shaders</strong><br>
      Explore dimensions from installed mods such as Twilight Forest. Iris / MakeUp shaders are optional.
    </td>
    <td width="33%" valign="top">
      <strong>🚀 One launcher</strong><br>
      Double-click the launcher to load the world and open the hero picker. The world saves when you exit.
    </td>
  </tr>
</table>

## Download

<!-- DOWNLOAD_LINKS -->
<div align="center">
  <h3><a href="https://pan.baidu.com/s/1dt433i2fr2vXsVXvQznhUg?pwd=1234">⬇ Download OWMC v1.0.0 from Baidu Netdisk</a></h3>
  <p><code>OWMC-1.0.0.zip</code> · <strong>5.46 GB</strong></p>
  <p>Extraction code <kbd>1234</kbd> · Updated <strong>2026-11-08</strong></p>
  <p><strong>SHA256</strong> <code>8b4069c050b40af85574fa1d0fb94c9e5a8009b6616946227e6f13cb3318c226</code></p>
</div>
<!-- /DOWNLOAD_LINKS -->

## Quick start

1. Extract the entire `OWMC-1.0.0.zip` archive and double-click **`ow x mc 启动器.exe`**.
2. Wait for the hero picker and select a hero. If “打开即启动” (start on opening) is off, click “开始游戏” (start game).
3. To quit, click **“结束游戏”** (stop game) in the launcher and wait for the world to save.

<p align="center"><img src="docs/media/launcher.png" width="640" alt="Launcher home page"></p>

**System requirements** 64-bit Windows 10 2004+ or Windows 11 and a GPU that supports Direct3D 11 and OpenGL. Allow at least 8 GB of RAM, with 16 GB recommended, and around 20 GB of free disk space.

The package includes Python and Java runtimes. Extract it to an NTFS or exFAT drive because the ZIP exceeds FAT32’s file size limit.

See the [player guide (Chinese)](docs/PLAYER-README.md) for installation, runtime dependencies, logs, and troubleshooting.

## Controls

Keep the Overwatch window focused. Some laptops require holding <kbd>Fn</kbd> to use function keys.

| 🎮 Movement & combat | Action | | ⚙️ Menus & function keys | Action |
| :---: | --- | --- | :---: | --- |
| <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd> | 🏃 Move | | <kbd>H</kbd> | 🦸 Return to hero picker |
| <kbd>🖱️ Mouse</kbd> | 👀 Look | | <kbd>F5</kbd> | 🧑‍🤝‍🧑 Hero summons / survival mode |
| <kbd>Space</kbd> | ⤴️ Jump / ascend in flight | | <kbd>F6</kbd> | 🕊️ Flight |
| <kbd>Ctrl</kbd> | ⤵️ Descend in flight | | <kbd>F7</kbd> | 🌤️ World settings |
| <kbd>🖱️ Left click</kbd> | 🔫 Primary attack | | <kbd>F8</kbd> | 🌀 Portals |
| <kbd>🖱️ Right click</kbd> | 🎯 Secondary attack | | <kbd>F9</kbd> | 👾 Mob summons |
| <kbd>R</kbd> | 🔄 Reload | | <kbd>F10</kbd> | 🐉 Boss destinations |
| <kbd>V</kbd> | 👊 Melee | | <kbd>F11</kbd> | 🔋 Charge ultimate / reset cooldowns |
| <kbd>Shift</kbd> | ✨ Ability 1 | |  |  |
| <kbd>E</kbd> | ✨ Ability 2 | |  |  |
| <kbd>Q</kbd> | 💥 Ultimate | |  |  |

Use the number row or numeric keypad in menus. Follow the on-screen prompts to change pages or go back.

## Hero restoration progress

**14 heroes · 89 abilities and mechanics · ✅ 86 restored · 🚧 1 partial · ❌ 2 not restored**

The full kits of McCree, Mei, Torbjörn, Widowmaker, Roadhog, and Winston have been confirmed in game. Expand a hero to see controls and status. [Icon sources](docs/media/README.md#图标规格).

<details>
<summary><img src="docs/media/heroes/genji/portrait.png" width="24" height="24" alt="Genji"> <strong>Genji</strong> · 8/8 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/genji/shuriken.png" width="32" height="32" alt="Shuriken"> | Shuriken | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/shuriken-fan.png" width="32" height="32" alt="Shuriken (Secondary Fire)"> | Shuriken (Secondary Fire) | <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/swift-strike.png" width="32" height="32" alt="Swift Strike"> | Swift Strike | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/deflect.png" width="32" height="32" alt="Deflect"> | Deflect | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/dragonblade.png" width="32" height="32" alt="Dragonblade"> | Dragonblade | <kbd>Q</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/double-jump.png" width="32" height="32" alt="Cyber-Agility (Double Jump)"> | Cyber-Agility (Double Jump) | <kbd>Space</kbd> → <kbd>Space</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/wall-climb.png" width="32" height="32" alt="Cyber-Agility (Wall Climb)"> | Cyber-Agility (Wall Climb) | Face a wall and press <kbd>W</kbd> + <kbd>Space</kbd> | ✅ Restored |
| <img src="docs/media/heroes/genji/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/mccree/portrait.png" width="24" height="24" alt="McCree"> <strong>McCree</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mccree/peacekeeper.png" width="32" height="32" alt="Peacekeeper"> | Peacekeeper | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mccree/fan-the-hammer.png" width="32" height="32" alt="Fan the Hammer"> | Fan the Hammer | <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mccree/combat-roll.png" width="32" height="32" alt="Combat Roll"> | Combat Roll | <kbd>W</kbd> + <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mccree/flashbang.png" width="32" height="32" alt="Flashbang"> | Flashbang | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mccree/deadeye.png" width="32" height="32" alt="Deadeye"> | Deadeye | <kbd>Q</kbd> → wait for lock-on → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mccree/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/pharah/portrait.png" width="24" height="24" alt="Pharah"> <strong>Pharah</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/pharah/rocket-launcher.png" width="32" height="32" alt="Rocket Launcher"> | Rocket Launcher | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/pharah/jump-jet.png" width="32" height="32" alt="Jump Jet"> | Jump Jet | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/pharah/concussive-blast.png" width="32" height="32" alt="Concussive Blast"> | Concussive Blast | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/pharah/barrage.png" width="32" height="32" alt="Barrage"> | Barrage | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/pharah/hover-jets.png" width="32" height="32" alt="Hover Jets"> | Hover Jets | Hold <kbd>Space</kbd> in the air | ✅ Restored |
| <img src="docs/media/heroes/pharah/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/reaper/portrait.png" width="24" height="24" alt="Reaper"> <strong>Reaper</strong> · 5/6 restored · 1 not restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/reaper/hellfire-shotguns.png" width="32" height="32" alt="Hellfire Shotguns"> | Hellfire Shotguns | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/reaper/wraith-form.png" width="32" height="32" alt="Wraith Form"> | Wraith Form | <kbd>Shift</kbd> + <kbd>W</kbd> | ✅ Restored |
| <img src="docs/media/heroes/reaper/shadow-step.png" width="32" height="32" alt="Shadow Step"> | Shadow Step | <kbd>E</kbd> → <kbd>🖱️ Left click</kbd> to confirm | ✅ Restored |
| <img src="docs/media/heroes/reaper/death-blossom.png" width="32" height="32" alt="Death Blossom"> | Death Blossom | <kbd>Q</kbd> | ❌ Not restored |
| <img src="docs/media/heroes/reaper/the-reaping.png" width="32" height="32" alt="The Reaping"> | The Reaping | Approach the soul after a kill | ✅ Restored · collecting a soul restores health |
| <img src="docs/media/heroes/reaper/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/soldier76/portrait.png" width="24" height="24" alt="Soldier: 76"> <strong>Soldier: 76</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/soldier76/heavy-pulse-rifle.png" width="32" height="32" alt="Heavy Pulse Rifle"> | Heavy Pulse Rifle | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/soldier76/helix-rockets.png" width="32" height="32" alt="Helix Rockets"> | Helix Rockets | <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/soldier76/sprint.png" width="32" height="32" alt="Sprint"> | Sprint | <kbd>W</kbd> + <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/soldier76/biotic-field.png" width="32" height="32" alt="Biotic Field"> | Biotic Field | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/soldier76/tactical-visor.png" width="32" height="32" alt="Tactical Visor"> | Tactical Visor | <kbd>Q</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/soldier76/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/tracer/portrait.png" width="24" height="24" alt="Tracer"> <strong>Tracer</strong> · 5/5 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/tracer/pulse-pistols.png" width="32" height="32" alt="Pulse Pistols"> | Pulse Pistols | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/tracer/blink.png" width="32" height="32" alt="Blink"> | Blink | <kbd>W</kbd> + <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/tracer/recall.png" width="32" height="32" alt="Recall"> | Recall | Move first → <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/tracer/pulse-bomb.png" width="32" height="32" alt="Pulse Bomb"> | Pulse Bomb | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/tracer/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/bastion/portrait.png" width="24" height="24" alt="Bastion"> <strong>Bastion</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/bastion/recon.png" width="32" height="32" alt="Configuration: Recon"> | Configuration: Recon | <kbd>🖱️ Left click</kbd> in Recon mode | ✅ Restored |
| <img src="docs/media/heroes/bastion/reconfigure.png" width="32" height="32" alt="Reconfigure"> | Reconfigure | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/bastion/sentry.png" width="32" height="32" alt="Configuration: Sentry"> | Configuration: Sentry | <kbd>Shift</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/bastion/self-repair.png" width="32" height="32" alt="Self-Repair"> | Self-Repair | Hold <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/bastion/tank.png" width="32" height="32" alt="Configuration: Tank"> | Configuration: Tank | <kbd>Q</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/bastion/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/hanzo/portrait.png" width="24" height="24" alt="Hanzo"> <strong>Hanzo</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/hanzo/storm-bow.png" width="32" height="32" alt="Storm Bow"> | Storm Bow | Hold <kbd>🖱️ Left click</kbd> → release | ✅ Restored |
| <img src="docs/media/heroes/hanzo/sonic-arrow.png" width="32" height="32" alt="Sonic Arrow"> | Sonic Arrow | <kbd>Shift</kbd> → charge and release <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/hanzo/scatter-arrow.png" width="32" height="32" alt="Scatter Arrow"> | Scatter Arrow | <kbd>E</kbd> → charge and release <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/hanzo/dragonstrike.png" width="32" height="32" alt="Dragonstrike"> | Dragonstrike | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/hanzo/wall-climb.png" width="32" height="32" alt="Wall Climb"> | Wall Climb | Face a wall and press <kbd>W</kbd> + <kbd>Space</kbd> | ✅ Restored |
| <img src="docs/media/heroes/hanzo/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/junkrat/portrait.png" width="24" height="24" alt="Junkrat"> <strong>Junkrat</strong> · 5/7 restored · 1 partial · 1 not restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/junkrat/frag-launcher.png" width="32" height="32" alt="Frag Launcher"> | Frag Launcher | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/junkrat/concussion-mine.png" width="32" height="32" alt="Concussion Mine"> | Concussion Mine | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/junkrat/detonate.png" width="32" height="32" alt="Concussion Mine (Detonate)"> | Concussion Mine (Detonate) | <kbd>Shift</kbd> → <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/junkrat/steel-trap.png" width="32" height="32" alt="Steel Trap"> | Steel Trap | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/junkrat/rip-tire.png" width="32" height="32" alt="RIP-Tire (Driving)"> | RIP-Tire (Driving) | <kbd>Q</kbd> → <kbd>W</kbd>, <kbd>Space</kbd> to climb walls | ❌ Not restored |
| <img src="docs/media/heroes/junkrat/total-mayhem.png" width="32" height="32" alt="Total Mayhem"> | Total Mayhem | Automatic on death | 🚧 Partial · visual effects are incomplete |
| <img src="docs/media/heroes/junkrat/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/mei/portrait.png" width="24" height="24" alt="Mei"> <strong>Mei</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mei/endothermic-blaster.png" width="32" height="32" alt="Endothermic Blaster"> | Endothermic Blaster | Hold <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mei/icicle.png" width="32" height="32" alt="Endothermic Blaster (Icicle)"> | Endothermic Blaster (Icicle) | <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mei/cryo-freeze.png" width="32" height="32" alt="Cryo-Freeze"> | Cryo-Freeze | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mei/ice-wall.png" width="32" height="32" alt="Ice Wall"> | Ice Wall | <kbd>E</kbd> to preview, <kbd>🖱️ Left click</kbd> to place, <kbd>E</kbd> / <kbd>🖱️ Right click</kbd> to cancel | ✅ Restored |
| <img src="docs/media/heroes/mei/blizzard.png" width="32" height="32" alt="Blizzard"> | Blizzard | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/mei/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/torbjorn/portrait.png" width="24" height="24" alt="Torbjörn"> <strong>Torbjörn</strong> · 10/10 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/torbjorn/rivet-gun.png" width="32" height="32" alt="Rivet Gun"> | Rivet Gun | <kbd>1</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/rivet-gun-secondary.png" width="32" height="32" alt="Rivet Gun (Secondary Fire)"> | Rivet Gun (Secondary Fire) | <kbd>1</kbd> → <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/build-turret.png" width="32" height="32" alt="Build Turret"> | Build Turret | <kbd>Shift</kbd> to preview, <kbd>🖱️ Left click</kbd> to place, <kbd>🖱️ Right click</kbd> to cancel | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/armor-pack.png" width="32" height="32" alt="Armor Pack"> | Armor Pack | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/molten-core.png" width="32" height="32" alt="Molten Core"> | Molten Core | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/forge-hammer.png" width="32" height="32" alt="Forge Hammer"> | Forge Hammer | <kbd>2</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/turret-repair.png" width="32" height="32" alt="Forge Hammer (Repair)"> | Forge Hammer (Repair) | <kbd>2</kbd> → <kbd>🖱️ Left click</kbd> on a damaged turret | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/turret-upgrade.png" width="32" height="32" alt="Forge Hammer (Upgrade)"> | Forge Hammer (Upgrade) | <kbd>2</kbd> → <kbd>🖱️ Left click</kbd> on a level 1 turret | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/scrap-collector.png" width="32" height="32" alt="Scrap Collector"> | Scrap Collector | Approach scrap after a kill | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/widowmaker/portrait.png" width="24" height="24" alt="Widowmaker"> <strong>Widowmaker</strong> · 6/6 restored</summary>

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/widowmaker/widows-kiss.png" width="32" height="32" alt="Widow’s Kiss (Automatic)"> | Widow’s Kiss (Automatic) | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/widows-kiss-scoped.png" width="32" height="32" alt="Widow’s Kiss (Scoped)"> | Widow’s Kiss (Scoped) | Hold <kbd>🖱️ Right click</kbd> → <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/grappling-hook.png" width="32" height="32" alt="Grappling Hook"> | Grappling Hook | <kbd>Shift</kbd> to fire, <kbd>Shift</kbd> or <kbd>Space</kbd> to release early | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/venom-mine.png" width="32" height="32" alt="Venom Mine"> | Venom Mine | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/infra-sight.png" width="32" height="32" alt="Infra-Sight"> | Infra-Sight | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/roadhog/portrait.png" width="24" height="24" alt="Roadhog"> <strong>Roadhog</strong> · 6/6 restored</summary>

| Icon | Ability | Input | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/roadhog/scrap-gun.png" width="32" height="32" alt="Scrap Gun"> | Scrap Gun | <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/roadhog/scrap-gun-secondary.png" width="32" height="32" alt="Scrap Gun secondary fire"> | Scrap Gun secondary fire | <kbd>🖱️ Right click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/roadhog/chain-hook.png" width="32" height="32" alt="Chain Hook"> | Chain Hook | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/roadhog/take-a-breather.png" width="32" height="32" alt="Take a Breather"> | Take a Breather | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/roadhog/whole-hog.png" width="32" height="32" alt="Whole Hog"> | Whole Hog | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/roadhog/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

<details>
<summary><img src="docs/media/heroes/winston/portrait.png" width="24" height="24" alt="Winston"> <strong>Winston</strong> · 5/5 restored</summary>

| Icon | Ability | Input | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/winston/tesla-cannon.png" width="32" height="32" alt="Tesla Cannon"> | Tesla Cannon | Hold <kbd>🖱️ Left click</kbd> | ✅ Restored |
| <img src="docs/media/heroes/winston/jump-pack.png" width="32" height="32" alt="Jump Pack"> | Jump Pack | <kbd>Shift</kbd> | ✅ Restored |
| <img src="docs/media/heroes/winston/barrier-projector.png" width="32" height="32" alt="Barrier Projector"> | Barrier Projector | <kbd>E</kbd> | ✅ Restored |
| <img src="docs/media/heroes/winston/primal-rage.png" width="32" height="32" alt="Primal Rage"> | Primal Rage | <kbd>Q</kbd> | ✅ Restored |
| <img src="docs/media/heroes/winston/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | <kbd>V</kbd> | ✅ Restored |

</details>

## How it works and development

Overwatch reads your input and renders the original heroes. Minecraft handles movement, collisions, and combat results. Its world image appears in the Overwatch window alongside the original first-person models and HUD.

<details>
<summary><strong>Build from source</strong></summary>

Development requires Windows x64, Python 3.13, JDK 21, Gradle 8.10.2, and MinGW-w64. See the [build guide](docs/BUILDING.md), [two-process design](docs/PASSTHROUGH.md), and [documentation index](docs/README.md).

</details>

## Credits and license

Thanks to [Universal Modder](https://github.com/rehan-remade/universal-modder) for the [two-process approach](https://github.com/rehan-remade/universal-modder/tree/main/skills/mashup-mods), [Prometheus](https://github.com/saturn-xvi/prometheus) for offline-client research, and Fabric, Twilight Forest, Sodium, Iris, and the other open-source components. Developed with assistance from Claude / Codex.

Project-owned code is licensed under the [MIT License](LICENSE), copyright **2026 RPQ123**. Third-party code and assets retain their own licenses. See [third-party notices](THIRD_PARTY_NOTICES.md) and [component details](docs/THIRD-PARTY.md).

## Author

[Follow the author on Bilibili](https://space.bilibili.com/13152709)
