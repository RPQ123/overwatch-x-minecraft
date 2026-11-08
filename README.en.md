<div align="center">
  <img src="assets/launcher/owmc.png" width="144" alt="Overwatch × Minecraft logo">
  <h1>Overwatch × Minecraft</h1>
  <p><strong>Original Overwatch heroes in a real Minecraft world.</strong></p>
  <p><a href="README.md">简体中文</a> · English · <a href="#download">Download</a> · <a href="docs/PLAYER-README.md">Player guide (Chinese)</a> · <a href="docs/BUILDING.md">Build guide</a></p>
  <p><a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License for project code"></a></p>
</div>

This project connects the **2016 offline Overwatch beta 0.8.0.24919** with **Minecraft 1.21.1**. Overwatch provides the heroes, weapons, animations, HUD, and sound. Minecraft provides the terrain, creatures, movement, collision, and saves. You play in the Overwatch window.

This is a non-commercial fan project, unaffiliated with Blizzard Entertainment, Mojang, or Microsoft. Game clients, models, voices, and other runtime assets are excluded from the source repository. Demo images and icons belong to their respective creators.

## Demo

<p align="center">
  <img src="docs/media/heroes-12.gif" width="640" alt="Gameplay featuring 12 heroes in Minecraft">
</p>

Full trailer: link pending. [Media sources](docs/media/README.md).

| Original heroes and weapons | Minecraft worlds |
| --- | --- |
| ![Genji’s shuriken and HUD](docs/media/genji-shuriken.jpg) | ![Widowmaker and Minecraft creatures](docs/media/widowmaker-sniper.jpg) |
| ![Mei’s freeze spray](docs/media/mei-freeze.jpg) | ![McCree exploring the Twilight Forest](docs/media/twilight-forest.jpg) |

## Features

- **Fourteen heroes.** Roadhog and Winston join the roster with original first-person models, weapon animations, HUD, and sound.
- **A real world:** Minecraft handles exploration, movement, block collision, dimension travel, and saves.
- **In-game menus:** toggle flight, adjust time, build portals, summon mobs, travel to Boss areas, and refill ability resources.
- **Twilight Forest and shaders:** use installed dimension mods and optional Iris / MakeUp shaders.
- **One launcher:** load the world and hero picker automatically, then save the world when you stop.

- **F5 and survival.** Summon training NPCs for all 14 heroes and toggle survival or invulnerability. Player heroes and training NPCs are immune to fall damage.
- **Health sync on hit.** Native health reads and writes run in the background to reduce main-thread waits on hit. In-game performance awaits a retest.

## Download

<!-- DOWNLOAD_LINKS -->
**OWMC v1.0.0 package (`OWMC-1.0.0.zip`, 5.46 GB).** Download link pending.

This download section is for the package rebuilt from current development, including the hero and survival updates.

Mirror pending · SHA256: `8b4069c050b40af85574fa1d0fb94c9e5a8009b6616946227e6f13cb3318c226`
<!-- /DOWNLOAD_LINKS -->

## Quick start

<p align="center"><img src="docs/media/launcher.png" width="640" alt="Launcher home page"></p>

Once you have the complete package:

1. Extract the entire ZIP and double-click **`ow x mc 启动器.exe`**.
2. Wait for the hero picker, then select a hero. If “打开即启动” (start on opening) is off, click “开始游戏” (start game).
3. Click **“结束游戏”** (stop game) in the launcher and wait for the world to save.

Requirements: Windows 10 2004+ / Windows 11 x64, a GPU with Direct3D 11 and OpenGL support, at least 8 GB RAM (16 GB recommended), and about 20 GB free space. The package supplies its runtimes; no separate Python or Java installation is needed. Extract to NTFS / exFAT: the ZIP exceeds FAT32’s single-file limit.

See the [player guide (Chinese)](docs/PLAYER-README.md) for installation, runtime dependencies, logs, and troubleshooting.

## Controls

Keep the Overwatch window focused. Some laptops require `Fn` for function keys.

| Keys | Action |
| --- | --- |
| WASD / mouse | Move / look |
| Space / Ctrl | Jump; ascend / descend while flying |
| Left / right mouse | Primary / secondary attack |
| R / V | Reload / melee |
| Shift / E / Q | Hero abilities / ultimate |
| H | Return to the hero picker |
| F5 | Hero summons / survival mode |
| F6 / F7 | Flight / world settings |
| F8 / F9 | Portals / mob summons |
| F10 / F11 | Boss destinations / ability resource refill |

Use number keys or the numeric keypad to select menu items. Follow the on-screen prompts to change pages or go back.

## Hero restoration progress

**14 heroes and 89 abilities and mechanics. ✅ 76 restored · 🧪 4 implemented, awaiting in-game checks · 🚧 7 partial · ❌ 2 not restored.**

✅ marks gameplay with in-game evidence, 🧪 marks implementation with offline checks, and 🚧 marks partial coverage. The tables flag any newer behavior that still needs an in-game check. [Status notes and icon sources](docs/media/README.md#技能状态与图标来源).

### <img src="docs/media/heroes/genji/portrait.png" width="32" height="32" alt="Genji"> Genji

8/8 restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/genji/shuriken.png" width="32" height="32" alt="Shuriken"> | Shuriken | LMB | ✅ Restored |
| <img src="docs/media/heroes/genji/shuriken-fan.png" width="32" height="32" alt="Shuriken (Secondary Fire)"> | Shuriken (Secondary Fire) | RMB | ✅ Restored |
| <img src="docs/media/heroes/genji/swift-strike.png" width="32" height="32" alt="Swift Strike"> | Swift Strike | Shift | ✅ Restored |
| <img src="docs/media/heroes/genji/deflect.png" width="32" height="32" alt="Deflect"> | Deflect | E | ✅ Restored |
| <img src="docs/media/heroes/genji/dragonblade.png" width="32" height="32" alt="Dragonblade"> | Dragonblade | Q → LMB | ✅ Restored |
| <img src="docs/media/heroes/genji/double-jump.png" width="32" height="32" alt="Cyber-Agility (Double Jump)"> | Cyber-Agility (Double Jump) | Space → Space | ✅ Restored |
| <img src="docs/media/heroes/genji/wall-climb.png" width="32" height="32" alt="Cyber-Agility (Wall Climb)"> | Cyber-Agility (Wall Climb) | Face a wall: W + Space | ✅ Restored |
| <img src="docs/media/heroes/genji/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/mccree/portrait.png" width="32" height="32" alt="McCree"> McCree

5/6 restored · 1 partial

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mccree/peacekeeper.png" width="32" height="32" alt="Peacekeeper"> | Peacekeeper | LMB | ✅ Restored |
| <img src="docs/media/heroes/mccree/fan-the-hammer.png" width="32" height="32" alt="Fan the Hammer"> | Fan the Hammer | RMB | ✅ Restored |
| <img src="docs/media/heroes/mccree/combat-roll.png" width="32" height="32" alt="Combat Roll"> | Combat Roll | W + Shift | ✅ Restored |
| <img src="docs/media/heroes/mccree/flashbang.png" width="32" height="32" alt="Flashbang"> | Flashbang | E | ✅ Restored |
| <img src="docs/media/heroes/mccree/deadeye.png" width="32" height="32" alt="Deadeye"> | Deadeye | Q → wait for lock-on → LMB | 🚧 Partial: visuals incomplete |
| <img src="docs/media/heroes/mccree/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/pharah/portrait.png" width="32" height="32" alt="Pharah"> Pharah

6/6 restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/pharah/rocket-launcher.png" width="32" height="32" alt="Rocket Launcher"> | Rocket Launcher | LMB | ✅ Restored |
| <img src="docs/media/heroes/pharah/jump-jet.png" width="32" height="32" alt="Jump Jet"> | Jump Jet | Shift | ✅ Restored |
| <img src="docs/media/heroes/pharah/concussive-blast.png" width="32" height="32" alt="Concussive Blast"> | Concussive Blast | E | ✅ Restored |
| <img src="docs/media/heroes/pharah/barrage.png" width="32" height="32" alt="Barrage"> | Barrage | Q | ✅ Restored |
| <img src="docs/media/heroes/pharah/hover-jets.png" width="32" height="32" alt="Hover Jets"> | Hover Jets | Hold Space in the air | ✅ Restored |
| <img src="docs/media/heroes/pharah/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/reaper/portrait.png" width="32" height="32" alt="Reaper"> Reaper

5/6 restored · 1 not restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/reaper/hellfire-shotguns.png" width="32" height="32" alt="Hellfire Shotguns"> | Hellfire Shotguns | LMB | ✅ Restored |
| <img src="docs/media/heroes/reaper/wraith-form.png" width="32" height="32" alt="Wraith Form"> | Wraith Form | Shift + W | ✅ Restored |
| <img src="docs/media/heroes/reaper/shadow-step.png" width="32" height="32" alt="Shadow Step"> | Shadow Step | E → LMB to confirm | ✅ Restored |
| <img src="docs/media/heroes/reaper/death-blossom.png" width="32" height="32" alt="Death Blossom"> | Death Blossom | Q | ❌ Not restored |
| <img src="docs/media/heroes/reaper/the-reaping.png" width="32" height="32" alt="The Reaping"> | The Reaping | Approach the soul after a kill | ✅ Restored · healing tested, victim head visuals await checks |
| <img src="docs/media/heroes/reaper/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/soldier76/portrait.png" width="32" height="32" alt="Soldier: 76"> Soldier: 76

6/6 restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/soldier76/heavy-pulse-rifle.png" width="32" height="32" alt="Heavy Pulse Rifle"> | Heavy Pulse Rifle | LMB | ✅ Restored |
| <img src="docs/media/heroes/soldier76/helix-rockets.png" width="32" height="32" alt="Helix Rockets"> | Helix Rockets | RMB | ✅ Restored |
| <img src="docs/media/heroes/soldier76/sprint.png" width="32" height="32" alt="Sprint"> | Sprint | W + Shift | ✅ Restored |
| <img src="docs/media/heroes/soldier76/biotic-field.png" width="32" height="32" alt="Biotic Field"> | Biotic Field | E | ✅ Restored |
| <img src="docs/media/heroes/soldier76/tactical-visor.png" width="32" height="32" alt="Tactical Visor"> | Tactical Visor | Q → LMB | ✅ Restored |
| <img src="docs/media/heroes/soldier76/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/tracer/portrait.png" width="32" height="32" alt="Tracer"> Tracer

5/5 restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/tracer/pulse-pistols.png" width="32" height="32" alt="Pulse Pistols"> | Pulse Pistols | LMB | ✅ Restored |
| <img src="docs/media/heroes/tracer/blink.png" width="32" height="32" alt="Blink"> | Blink | W + Shift | ✅ Restored |
| <img src="docs/media/heroes/tracer/recall.png" width="32" height="32" alt="Recall"> | Recall | Move first → E | ✅ Restored |
| <img src="docs/media/heroes/tracer/pulse-bomb.png" width="32" height="32" alt="Pulse Bomb"> | Pulse Bomb | Q | ✅ Restored |
| <img src="docs/media/heroes/tracer/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/bastion/portrait.png" width="32" height="32" alt="Bastion"> Bastion

6/6 restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/bastion/recon.png" width="32" height="32" alt="Configuration: Recon"> | Configuration: Recon | LMB in Recon mode | ✅ Restored |
| <img src="docs/media/heroes/bastion/reconfigure.png" width="32" height="32" alt="Reconfigure"> | Reconfigure | Shift | ✅ Restored |
| <img src="docs/media/heroes/bastion/sentry.png" width="32" height="32" alt="Configuration: Sentry"> | Configuration: Sentry | Shift → LMB | ✅ Restored |
| <img src="docs/media/heroes/bastion/self-repair.png" width="32" height="32" alt="Self-Repair"> | Self-Repair | Hold E | ✅ Restored |
| <img src="docs/media/heroes/bastion/tank.png" width="32" height="32" alt="Configuration: Tank"> | Configuration: Tank | Q → LMB | ✅ Restored |
| <img src="docs/media/heroes/bastion/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/hanzo/portrait.png" width="32" height="32" alt="Hanzo"> Hanzo

6/6 restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/hanzo/storm-bow.png" width="32" height="32" alt="Storm Bow"> | Storm Bow | Hold LMB → release | ✅ Restored |
| <img src="docs/media/heroes/hanzo/sonic-arrow.png" width="32" height="32" alt="Sonic Arrow"> | Sonic Arrow | Shift → charge and release LMB | ✅ Restored |
| <img src="docs/media/heroes/hanzo/scatter-arrow.png" width="32" height="32" alt="Scatter Arrow"> | Scatter Arrow | E → charge and release LMB | ✅ Restored |
| <img src="docs/media/heroes/hanzo/dragonstrike.png" width="32" height="32" alt="Dragonstrike"> | Dragonstrike | Q | ✅ Restored |
| <img src="docs/media/heroes/hanzo/wall-climb.png" width="32" height="32" alt="Wall Climb"> | Wall Climb | Face a wall: W + Space | ✅ Restored |
| <img src="docs/media/heroes/hanzo/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/junkrat/portrait.png" width="32" height="32" alt="Junkrat"> Junkrat

5/7 restored · 1 partial · 1 not restored

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/junkrat/frag-launcher.png" width="32" height="32" alt="Frag Launcher"> | Frag Launcher | LMB | ✅ Restored |
| <img src="docs/media/heroes/junkrat/concussion-mine.png" width="32" height="32" alt="Concussion Mine"> | Concussion Mine | Shift | ✅ Restored |
| <img src="docs/media/heroes/junkrat/detonate.png" width="32" height="32" alt="Concussion Mine (Detonate)"> | Concussion Mine (Detonate) | Shift → RMB | ✅ Restored |
| <img src="docs/media/heroes/junkrat/steel-trap.png" width="32" height="32" alt="Steel Trap"> | Steel Trap | E | ✅ Restored |
| <img src="docs/media/heroes/junkrat/rip-tire.png" width="32" height="32" alt="RIP-Tire (Driving)"> | RIP-Tire (Driving) | Q → W; Space to climb walls | ❌ Not restored |
| <img src="docs/media/heroes/junkrat/total-mayhem.png" width="32" height="32" alt="Total Mayhem"> | Total Mayhem | Automatic on death | 🚧 Partial: visuals incomplete |
| <img src="docs/media/heroes/junkrat/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/mei/portrait.png" width="32" height="32" alt="Mei"> Mei

5/6 restored · 1 partial

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/mei/endothermic-blaster.png" width="32" height="32" alt="Endothermic Blaster"> | Endothermic Blaster | Hold LMB | ✅ Restored |
| <img src="docs/media/heroes/mei/icicle.png" width="32" height="32" alt="Endothermic Blaster (Icicle)"> | Endothermic Blaster (Icicle) | RMB | ✅ Restored · original icicle mesh, wall embedding and fade await in-game checks |
| <img src="docs/media/heroes/mei/cryo-freeze.png" width="32" height="32" alt="Cryo-Freeze"> | Cryo-Freeze | Shift | ✅ Restored |
| <img src="docs/media/heroes/mei/ice-wall.png" width="32" height="32" alt="Ice Wall"> | Ice Wall | E to preview, left click to place, E / right click to cancel | 🚧 Partial · placement tested, widened original five-pillar wall and repeated casts await checks |
| <img src="docs/media/heroes/mei/blizzard.png" width="32" height="32" alt="Blizzard"> | Blizzard | Q | ✅ Restored |
| <img src="docs/media/heroes/mei/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/torbjorn/portrait.png" width="32" height="32" alt="Torbjörn"> Torbjörn

9/10 restored · 1 partial

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/torbjorn/rivet-gun.png" width="32" height="32" alt="Rivet Gun"> | Rivet Gun | 1 → LMB | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/rivet-gun-secondary.png" width="32" height="32" alt="Rivet Gun (Secondary Fire)"> | Rivet Gun (Secondary Fire) | 1 → RMB | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/build-turret.png" width="32" height="32" alt="Build Turret"> | Build Turret | Shift to preview, left click to place, right click to cancel | 🚧 Partial · initial placement tested, repeat placement and hand pose fixes await checks |
| <img src="docs/media/heroes/torbjorn/armor-pack.png" width="32" height="32" alt="Armor Pack"> | Armor Pack | E | ✅ Restored · pickup, armor and growth tested, repeat refresh and full-bright rendering await checks |
| <img src="docs/media/heroes/torbjorn/molten-core.png" width="32" height="32" alt="Molten Core"> | Molten Core | Q | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/forge-hammer.png" width="32" height="32" alt="Forge Hammer"> | Forge Hammer | 2 → LMB | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/turret-repair.png" width="32" height="32" alt="Forge Hammer (Repair)"> | Forge Hammer (Repair) | 2 → LMB on a damaged turret | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/turret-upgrade.png" width="32" height="32" alt="Forge Hammer (Upgrade)"> | Forge Hammer (Upgrade) | 2 → LMB on a level 1 turret | ✅ Restored |
| <img src="docs/media/heroes/torbjorn/scrap-collector.png" width="32" height="32" alt="Scrap Collector"> | Scrap Collector | Approach scrap after a kill | ✅ Restored · drops on kills, attracts nearby scrap, and credits native scrap |
| <img src="docs/media/heroes/torbjorn/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/widowmaker/portrait.png" width="32" height="32" alt="Widowmaker"> Widowmaker

5/6 restored · 1 partial

| Icon | Ability | Keys | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/widowmaker/widows-kiss.png" width="32" height="32" alt="Widow’s Kiss (Automatic)"> | Widow’s Kiss (Automatic) | LMB | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/widows-kiss-scoped.png" width="32" height="32" alt="Widow’s Kiss (Scoped)"> | Widow’s Kiss (Scoped) | Hold RMB → LMB | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/grappling-hook.png" width="32" height="32" alt="Grappling Hook"> | Grappling Hook | Shift to fire, Shift or Space to release early | 🚧 Partial · grapple tested, native 12-second cooldown and aerial momentum await checks |
| <img src="docs/media/heroes/widowmaker/venom-mine.png" width="32" height="32" alt="Venom Mine"> | Venom Mine | E | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/infra-sight.png" width="32" height="32" alt="Infra-Sight"> | Infra-Sight | Q | ✅ Restored |
| <img src="docs/media/heroes/widowmaker/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/roadhog/portrait.png" width="32" height="32" alt="Roadhog"> Roadhog

5/6 restored · 1 partial

| Icon | Ability | Input | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/roadhog/scrap-gun.png" width="32" height="32" alt="Scrap Gun"> | Scrap Gun | Left click | ✅ Restored · spread, ammo and reload tested |
| <img src="docs/media/heroes/roadhog/scrap-gun-secondary.png" width="32" height="32" alt="Scrap Gun secondary fire"> | Scrap Gun secondary fire | Right click | ✅ Restored · close hit and distant split tested, second burst sound awaits checks |
| <img src="docs/media/heroes/roadhog/chain-hook.png" width="32" height="32" alt="Chain Hook"> | Chain Hook | Shift | ✅ Restored · hits and pulls tested, left-hand chain and sustained pull await checks |
| <img src="docs/media/heroes/roadhog/take-a-breather.png" width="32" height="32" alt="Take a Breather"> | Take a Breather | E | ✅ Restored · healing, damage reduction and movement lock tested |
| <img src="docs/media/heroes/roadhog/whole-hog.png" width="32" height="32" alt="Whole Hog"> | Whole Hog | Q | 🚧 Partial · sustained fire and knockback tested, projectile and muzzle visuals await checks |
| <img src="docs/media/heroes/roadhog/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | ✅ Restored |

### <img src="docs/media/heroes/winston/portrait.png" width="32" height="32" alt="Winston"> Winston

0/5 restored · 4 implemented, awaiting in-game checks · 1 partial

| Icon | Ability | Input | Status |
| :---: | --- | --- | --- |
| <img src="docs/media/heroes/winston/tesla-cannon.png" width="32" height="32" alt="Tesla Cannon"> | Tesla Cannon | Hold left click | 🧪 Implemented · native ammo, arcs and damage await in-game checks |
| <img src="docs/media/heroes/winston/jump-pack.png" width="32" height="32" alt="Jump Pack"> | Jump Pack | Shift | 🧪 Implemented · launch, landing damage and cooldown sync await in-game checks |
| <img src="docs/media/heroes/winston/barrier-projector.png" width="32" height="32" alt="Barrier Projector"> | Barrier Projector | E | 🧪 Implemented · original blue hex mesh and projectile blocking await in-game checks |
| <img src="docs/media/heroes/winston/primal-rage.png" width="32" height="32" alt="Primal Rage"> | Primal Rage | Q | 🚧 Partial · temporary health and punches implemented, native transformation and HUD await checks |
| <img src="docs/media/heroes/winston/melee.png" width="32" height="32" alt="Quick Melee"> | Quick Melee | V | 🧪 Implemented · shared melee path awaits in-game checks |

## How it works and development

Both games run together. Overwatch receives input and renders the hero. Minecraft handles the world and combat results, then sends its world image back to the Overwatch window.

Development requires Windows x64, Python 3.13, JDK 21, Gradle 8.10.2, and MinGW-w64. See the [build guide](docs/BUILDING.md), [two-process design](docs/PASSTHROUGH.md), and [documentation index](docs/README.md).

## Credits and license

Thanks to [Universal Modder](https://github.com/rehan-remade/universal-modder) for the [two-process approach](https://github.com/rehan-remade/universal-modder/tree/main/skills/mashup-mods), [Prometheus](https://github.com/saturn-xvi/prometheus) for offline-client research, and Fabric, Twilight Forest, Sodium, Iris, and the other open-source components. Developed with assistance from Claude / Codex.

Project-owned code is licensed under the [MIT License](LICENSE), copyright **2026 RPQ123**. Third-party code and assets retain their own licenses; see [third-party notices](THIRD_PARTY_NOTICES.md) and [component details](docs/THIRD-PARTY.md).
