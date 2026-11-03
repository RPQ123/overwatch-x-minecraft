# 新英雄模块开发约定（Codex 并行线程必读）

Claude 是总指挥：规划、集成、构建部署、实机测试。Codex 线程只写**本英雄自己的新文件**，不改共享文件，
不启动游戏（沙盒无法切分辨率），不构建/部署 JAR。完成后把"登记行"写在回复里，由 Claude 统一登记。

## 路线（与已通过的狂鼠/半藏/美/托比昂相同）
原版负责：按键判定、手部动画、弹药/冷却/HUD。原版里交给服务端的部分（投射物飞行、命中、伤害、范围效果、
召唤物、护盾实体、治疗目标等）由 MC 补。触发信号只用原版节点（WeaponVolley 新 tick、确认节点、动画 End、
状态 Begin/active），**不许用按键伪造攻击**。没有原版信号时如实写明，作为显式 MC 适配。

## 每个英雄只新增这些文件
| 文件 | 作用 |
|---|---|
| `guest/src/main/java/lab/owmcguest/<Hero>Server.java` | `public final class <Hero>Server implements HeroServerModule`，`INSTANCE` 单例；MC 物理、伤害、状态 JSON |
| `guest/src/client/java/lab/owmcguest/<Hero>Client.java` | `implements HeroClientModule`，`INSTANCE`；静态块里 `NativeSkillReader.register("<名>",new NativeSkillReader.Spec(hero,graph,Map.of(节点名,索引)))`；每 tick 读节点、新 tick 时 `server.execute(...)` 交给 Server |
| `tools/prepare_hero_<hero>.py` | 常量 `HERO`、`GRAPHS`，函数 `prepare(process,pid)`：照抄 `tools/prepare_native_junkrat.py`，为每个 graph 写 `native-<名>-request-<pid>.json`（名与 Java register 一致），并校验节点类型哈希 |
| `research/sprint-20261024/verify_<hero>.py` | 实测脚本，照抄 `verify_junk_hanzo.py` 结构；只看 `/combat` 数值与目标血量 |

## 参考实现（照着写）
- 客户端：`NativeJunkratController.java`（三个 graph、首样本作基线、读取失败重建基线、来源过期 150 ms 返回）。
- 服务端：`NativeJunkratRuntime.java`（Scope 校验 owner/世界、先判墙再判实体、爆炸视线遮挡、两环衰减、publish 状态）、
  `NativeBlizzardRuntime.java`（范围效果）、`NativeVenomRuntime.java`（持续伤害）、`NativeTorbjornRuntime.java`（召唤物索敌）。
- 伤害：`NativeDamageTargets.projectileDamage/meleeDamage/beamDamage/explosionDamage(world,entity,player,原版伤害*NativeShotSimulation.HP_SCALE)`，HP_SCALE=0.1。
- 治疗/护盾/增益：用 MC 效果（`StatusEffects.REGENERATION/ABSORPTION/SPEED/STRENGTH` 等）或直接 `heal()`，写明是适配。
- 原版模型：`tools/ow_asset_chain.py <实体GUID>` → `tools/build_mesh_pack.py <名> <实体GUID>` → Java `OriginalMeshPack.get("<名>").draw(...)`；参考 `JunkratRenderer.java`。
- 测试场景（`/combat/test/<名>`）：`mei-lab`（地面+5 格村民）、`far-lab`（16 格）、`enderman`（敌对目标）、`ground-lab`、`cleanup`。
  需要新场景时写在回复里，由 Claude 加。

## 规则
- 数值：原版声明有就用原版（`tools/inspect_native_volley.py` 读齐射：投射物 GUID/速度/重力/寿命）；没有的写成常量并在类注释标"MC 适配值"。
- 状态 JSON 必须包含计数（casts/hits/damageApplied 等），供实测判定。
- 编译检查：`cmd /c "set GRADLE_USER_HOME=%CD%\tools\gradle-cache && tools\gradle\gradle-8.10.2\bin\gradle.bat -p guest --console=plain --no-daemon compileClientJava"`。
  注意：多个线程同时编译可能互相看到对方未完成的文件；编译失败若来自别人的文件，等一会儿重试，不要改别人的文件。
- 所有文本文件 UTF-8 写入。
- 完成后回复（中文 ≤10 行）：新增文件清单、登记行（`XxxServer.INSTANCE,` / `XxxClient.INSTANCE,`）、需要的新测试场景、哪些是 MC 适配。
