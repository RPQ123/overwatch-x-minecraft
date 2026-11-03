# Widow 第三轮交接（2026-10-27）

本线程按 `AGENTS.md`、`HERO-MODULE-GUIDE.md`、`PARALLEL-ROUND-20261026b.md` 执行：不开游戏、不构建或部署 JAR、不改共享文件。保留工作区原有修改和未跟踪文件；未提交。两真实进程路线不变。

## 已改文件

- `guest/src/main/java/lab/owmcguest/NativeVenomRuntime.java`：每次已认证的原版 E 发射，在服务端用一次 `nextBoolean()` 做等概率选择；普通诡雷仍走原有粘附、触发、75 原版伤害/5 秒毒流程；蜘蛛弹沿用同一位置、发射方向、20 m/s 初速及 9.8 m/s² 重力，触地后才生成实体。撞墙或顶面先停止水平飞行并下落，最长仍使用原诡雷的 100 tick 飞行上限。增加蜘蛛计数与实际血量、尺寸、目标遥测；会话清理同时移除召唤物。
- `guest/src/client/java/lab/owmcguest/VenomMineRenderer.java`：接入蜘蛛渲染器；飞行中的蜘蛛分支使用对应生物模型，普通诡雷仍用原版私有网格。
- 新增 `guest/src/main/java/lab/owmcguest/WidowSpiderEntity.java`：继承 `CaveSpiderEntity`，保持普通毒蜘蛛攻击属性、难度缩放和中毒效果，使用原版毒蜘蛛材质。`GENERIC_SCALE=.3` 同时缩放模型和碰撞宽高，预期宽 .21、高 .15（普通毒蜘蛛 .7×.5）。名字是始终显示的逐字 RGB 彩虹渐变 `Spider Man`。落地后每 20 tick 扣除最大生命的 1/10（默认最大 12，即每秒 1.2）；200 tick 到期强制死亡，外部治疗也不能延长寿命。
- 新增 `guest/src/client/java/lab/owmcguest/WidowSpiderRenderer.java`：复用原版毒蜘蛛渲染器；空中仅画渲染代理，不提前生成会攻击的实体。
- 新增 `guest/src/test/java/lab/owmcguest/WidowMeleeReaderCheck.java`、`tools/verify/verify_widow_offline.py`：本进程 Win64 内存夹具，验证通用近战读取器的 Widow 特例及共享修正候选，绝不连接游戏进程。

## 6a 行为与边界

50% 的单位是每次已认证发射，既不按帧重抽，也不以按键触发。认证链仍是未改动的 `NativeGrappleController.pollVenom` → 原版 graph `0056`、WeaponVolley node 1 新 tick、cast node 24 → `NativeVenomRuntime.cast`。增加 owner/world/model/source 会话复核。

“周围所有生物”按 `LivingEntity` 实现：16 格内、可见的最近存活目标，包括动物、村民、其他怪物、其他蜘蛛及其他玩家；仅排除自身、发射者及旁观实体。选目标和实际伤害入口都排除发射者。其他玩家的创造/旁观无敌仍遵守 MC 本身规则。昼夜不改变索敌意愿，不使用只针对玩家/铁傀儡的原版蜘蛛目标表。切人、死亡、跨世界、来源会话失效或显式 cleanup 会提前移除召唤物；不落盘、不掉战利品、不产经验。

概率、30% 大小、16 格索敌、逐字彩虹名、掉血/寿命和全生物索敌均为本轮用户要求的 **MC 适配**；没有改造或伪造原版 E 的触发。10 秒按 20 TPS 的 200 个服务端 tick 计时。普通诡雷的旧逻辑保留；新蜘蛛的普通 MC 攻击不乘 OW 的 `HP_SCALE`。

## 必须由 Claude 落地的共享改动（原样）

### 1. 注册实体与默认属性

在 `guest/src/main/java/lab/owmcguest/GuestMod.java` 的 `onInitialize()` 中，紧接 `CombatParticles.register();` 增加：

```java
        WidowSpiderEntity.register();
```

[已集成 integrator]

必须在注册表冻结前执行；不要放到服务器 tick、施放时或仅有 `owmc.frameExport` 的分支里。客户端已有 `VenomMineRenderer.register()` 会调用新增的 `WidowSpiderRenderer.register()`，无需另加客户端登记行；无需 `HeroServerModules` / `HeroClientModules` 新模块，也不要重复登记渲染器。

### 2. 修复 Widow 原版近战读取（6b 的根因）

共享 `NativeMeleeRuntime.supported()` 和 `tools/prepare_native_melee.py` 已包含 Widow 的 hero `0x02e000000000000aL`。V 已由原版通用 graph `0043` 的 TrackTargets node 13 驱动，不缺近战处理器。

真正故障在 `guest/src/client/java/lab/owmcguest/NativeSkillReader.java` 的 `poll()` 尾部（本线程读取时约第 261 行）：针对 Widow 的大招 `infraDuration()` 校验没有排除 `melee` reader，因而在合法近战绑定上读取根本不存在的 `infraDuration` / `infraAnimation` 字段，抛异常并拒绝整份近战样本。只需在条件中增加 `&&!melee`，不要新建或再挂一个近战回调。

将以下整行：

```java
            verify();if(spec==null&&!grapple&&!venom&&hero==NativeInfraSightState.HERO&&infraDuration()!=15)throw new IllegalArgumentException("Infra-Sight duration unavailable");var geometry=melee?geometry():null;error="";return new State(generation,model,hero,Map.copyOf(snapshot),geometry);
```

[已集成 integrator]

替换为：

```java
            verify();if(spec==null&&!melee&&!grapple&&!venom&&hero==NativeInfraSightState.HERO&&infraDuration()!=15)throw new IllegalArgumentException("Infra-Sight duration unavailable");var geometry=melee?geometry():null;error="";return new State(generation,model,hero,Map.copyOf(snapshot),geometry);
```

[已集成 integrator]

该改动保留原有进程创建时间、英雄/模型/来源、节点类型、伤害成员身份、球形几何、新 tick、会话与墙遮挡门禁，仍从原版读取当前近战伤害并由通用服务端路径转换和施加。

## 离线验证与命令

`tools/check_environment.py` 已通过（Python 3.13.13，全部只读前置检查通过）。`compileClientJava --offline` 成功。最终近战夹具通过：原读取器中 Winston 成功、Widow 因缺少大招字段而触发 `NullPointerException`；临时候选读取器中 Widow 原版近战/动态伤害/几何、首样本、重放和篡改门禁均通过。结果见本地 `research/sprint-20261027/widow-offline/result.json`，`sharedSourceUntouched=true`、`gameStarted=false`、`jarBuilt=false`、`deployed=false`。核验脚本使用 Java 参数文件绕过 Windows 长 classpath 限制，所有候选源与日志仅放在 ignored 的 research 目录。

```powershell
.venv/Scripts/python.exe tools/verify/verify_widow_offline.py
```

脚本先编译当前英雄源码，然后用同一份合法 melee 内存布局分别验证 Winston/Widow；共享文件未落地时，先证明 Winston 成功而 Widow 被拒绝，再只在 research 中编译加了 `&&!melee` 的候选读取器，验证 Widow 成功、首样本基线、不重放、动态原版伤害及篡改拒绝。共享修正已经落地时也可运行，直接核验集成后的读取器。夹具不证明实际按 V 的 MC 命中，也不证明蜘蛛实体、AI 或渲染实机表现。

Claude 落地两处共享接线后，统一编译/打包命令（本线程未执行打包）：

```powershell
$env:GRADLE_USER_HOME=Join-Path (Get-Location).Path 'tools/gradle-cache'
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon compileClientJava build
```

部署及启动仍用现有统一流程，由 Claude 负责；先备份配置/存档，使用当前机器核验的进程身份。

## 建议的实机验收（待 Claude，尚未执行）

1. 用原版 E 连续多次发射并记录 `/combat.venom` 的 `throws`、`mineRolls`、`spiderRolls` 增量：两分支总数等于已认证发射数，每次只走一种结果。单次/短样本无需恰好一半；不新增强制结果的按键旁路。原诡雷仍粘附、触发和持续伤害；蜘蛛弹飞行中可见，碰地后 `spiderSpawns` 增加且 `spiderSpawnFailures` 不增。
2. 查看 `spiders[]` 数值：默认出生 HP 12、width≈.21、height≈.15、scale≈.3，名字确为逐字彩虹 `Spider Man`。每秒 `spiderDecayTicks` 增加且 HP 约少 1.2；无外伤/治疗时 200 tick 内消亡，`spiderTimeouts` 增加。治疗不延寿，换人/死亡/跨维度/cleanup 无残留。
3. 邻近放动物、村民、敌怪和其他蜘蛛，观察 `spiders[].target`、`spiderHits`、`spiderDamageApplied` 及目标实际 HP/中毒；确保发射者 HP 不受它攻击。与普通毒蜘蛛在同一难度、同类目标上对比。`spiderDamageApplied` 仅记录直接近战造成的生命/吸收损失，不把后续原版中毒 tick 混入这个计数。现有 `/combat/test/venom-target` 可测 E；混合生物用现有 F9 菜单，无必需新增共享测试场景。
4. Widow 用现有 `/combat/test/melee`：墙后 V 不伤，去墙 V 使 `melee.accepted/hits/damageApplied` 与目标实际 HP 变化；静置不再扣血；换人后首次采样仍不重放旧近战。回归 Winston/其他英雄通用近战，以及 Widow Q 的原有大招时长校验。

未完成：两处共享文件接线仍由 Claude 落地，蜘蛛出生/AI/渲染与实际 V 伤害均待实机验收。当前只可标为源码及离线夹具验证，不能标为 ACCEPTED-live 或完整可玩目标完成。

原有两份待改源码已备份到本地 `research/sprint-20261027/widow-before/`（NativeVenomRuntime SHA256 `75f4c7338efad3c4aee3eb6b0c9f5dfa3e378258ff91291c0580da3e1f6737de`；VenomMineRenderer SHA256 `c95435e28103369d5f47c18efd62b0dc3e46d58d36bc58c7470fb133a0ed7027`）。不提交本地证据或备份。

第三轮集成索引：[INTEGRATION-20261027.md](INTEGRATION-20261027.md)。上述标记只指源码接线/删除旧行/既有接线核对，不表示实机验收。全量compileClientJava --rerun-tasks通过（27秒，3任务实际执行），未遇Loom锁、未删锁文件；未开游戏、打包JAR/DLL或部署。原“待接线”段落保留交接时历史，最新结果以本补记为准。

## 追加：诡雷中毒目标的 Glowing 轮廓（2026-10-27 试玩反馈）

本次仅修改 `guest/src/main/java/lab/owmcguest/NativeVenomRuntime.java`，新增 `guest/src/client/java/lab/owmcguest/NativeVenomReveal.java`，并追加本段交接；彩蛋蜘蛛抽签、飞行、实体及攻击逻辑保持。没有新增按键触发或改变 E 原版认证。

诡雷真实触发后，服务端为正在中毒的目标发布独立显形快照，客户端通过 MC 原生 `Entity.isGlowing` / outline 绘制链显形。显形从触发时开始，沿用 `POISON_TICKS=100`（20 TPS 下 5 秒），第五次原定毒伤 tick 完成后同时结束；再次被诡雷命中时与现有毒效一起刷新。只改变毒效在最后一次伤害后的清理时点，原有 20/40/60/80/100 tick 五次伤害及伤害数值保持。自然到期、cleanup、死亡、换人/来源失效、世界变化均撤销本模块的显形贡献。身份校验包含 owner/world/source/model、维度、实体 ID+UUID、目标存活与 150 ms 快照新鲜度。

显形采用逻辑“或”，不写 `setGlowing`、不添加/删除/替换 `StatusEffects.GLOWING`，也不修改队伍颜色。因此目标既有的药水、命令、其他模组、半藏声波箭或 Widow Q 发光不被缩短或清除；毒效结束只使本模块的条件返回 false。颜色保持 MC/其他既有来源的结果。该效果属于 **MC 适配**，只作用于本地融合客户端；蜘蛛的普通毒蜘蛛攻击不触发诡雷显形。

### Claude 必须补的一处共享接线（本线程未改共享文件）

在 `guest/src/client/java/lab/owmcguest/mixin/HanzoSonicGlowMixin.java` 的 `owmc$sonicOutline` 中，将现有：

```java
        if(!result.getReturnValueZ()&&(HanzoSonicReveal.reveals((Entity)(Object)this)||lab.owmcguest.NativeInfraSightController.reveals((Entity)(Object)this)))result.setReturnValue(true);
```

替换为：

```java
        if(!result.getReturnValueZ()&&(HanzoSonicReveal.reveals((Entity)(Object)this)||lab.owmcguest.NativeInfraSightController.reveals((Entity)(Object)this)||lab.owmcguest.NativeVenomReveal.reveals((Entity)(Object)this)))result.setReturnValue(true);
```

[已集成 integrator] 上述替换已落地，仅把 `NativeVenomReveal` 以 OR 加入现有轮廓判定。

只修改 `isGlowing` 这一行；`owmc$sonicColor`、`getTeamColorValue` 逻辑保持。无需新增模块、tick 回调、Mixin JSON 或注册行，现有 `NativeVenomRuntime.tick/resetSession` 已发布和清除快照。上轮已经集成的实体/近战接线继续沿用，不重复添加。

新增 `/combat.venom` 数字证据：`poisonRevealed`、`poisonRevealDurationTicks`、`poisonRevealTargets[]`（id/uuid/ticksRemaining）。这些字段表示服务器许可显形的目标，不等于客户端已经显示轮廓；共享接线落地前不会新增可见轮廓。最后一个目标到期后，即使没有飞行中的诡雷或存活蜘蛛，也会发布清零状态。

本次只读环境检查 12/12 通过；离线 `compileClientJava --offline` 成功（32 秒），新增客户端类产物存在，日志见 `research/sprint-20261027/widow-poison-reveal/compile.log`。源码差异复核确认未改蜘蛛分支、未写入或删除外部发光状态，共享 Mixin 保持原样；该静态复核不代表实机表现。未开游戏、未打包/部署。Claude 集成共享行后，按上文命令编译打包；实机待验：普通目标触雷即出现轮廓，100 tick 后消失；原有较长/无限 Glowing 在毒效结束和 cleanup 后仍保持；中毒期间新增的其他发光来源仍按自身时长继续；Widow Q 与声波箭原有显形回归；蜘蛛分支和原诡雷五次毒伤不回归。
