# 2026-10-27 menus：F9 随机召唤怪物

第三轮用户反馈 2。只改 menus 文件与新增辅助/检查文件；未开游戏、未构建或部署 JAR、未修改原版 DLL。其他线程和已有修改保留。

## 行为与按键

F9 首页：1「随机召唤怪物（含模组）」、2 旧随机 8 怪、3 多目标 12 村民、4 范围 4 村民、5 近距目标、6 末影人目标、7 远距目标、8 全部单体列表。
9 下一页、0 上一页；第 2 页的 1 清理测试场景。F9 关闭，重开回第 1 页。主数字行/小键盘共用原按键边沿保护。

新随机选项一次一只，服务端收到固定选择串 `random:monster` 后自行遍历**当前实际注册的** `Registries.ENTITY_TYPE`，没有从客户端接受候选 ID/名单，也没有沿用原随机批次的固定 8 种生物池。候选按实体类型等概率抽取，原版/模组使用相同规则。

敌对/中立候选须可召唤、可构造为 `MobEntity`，满足以下任一声明：`SpawnGroup.MONSTER`、`Monster`、`Angerable`、`RangedAttackMob` 或有限且正的原版攻击伤害属性。后一组兼容未实现 `Angerable` 的山羊、海豚、熊猫、羊驼及类似模组中立生物。普通猫、豹猫、狐狸、美西螈、青蛙、鹦鹉、悦灵、兔子和雪傀儡另作明确排除：它们有捕猎/特殊变种攻击属性或友方远程 AI，不能因此当作对玩家中立反击的怪物。纯被动生物和非生物实体不进入随机池。

### 大型 BOSS 规则（显式 MC 适配）

精确 ID 黑名单：

```text
minecraft:ender_dragon
minecraft:wither
twilightforest:naga
twilightforest:hydra
twilightforest:ur_ghast
aoa3:tyrosaur
aoa3:elite_tyrosaur
```

体积条件同时满足：宽、深各 ≤3 格，高 ≤4 格，包围盒体积 ≤18 立方格；所有边长必须有限且 >0。三个阈值是本轮用户要求的 **MC 便利功能适配值**，不是原版 OW 技能参数。
注册尺寸和构造后的实际包围盒都检查；复用单体路径调用 `SpawnReason.COMMAND` 初始化后再次检查，并在最终放置时复检。因此初始化后变大的模组实体/史莱姆不能绕过上限。黑名单 ID 即便被缩小也排除；不对所有 Boss 标签/类名做一刀切，小中型 Boss 仍可入池（需符合敌对/中立声明与尺寸）。

选择完成后进入**原 `SummonMenuRuntime.summon` 单体分支**，共用原生实体创建/初始化、安全位置搜索、已加载区块、边界、高度、碰撞、玩家占位、`canPlayerModifyAt` 与落地/水域检查；没有另写一条随机传送/无碰撞生成路径。保持单人服务端线程、存活创造玩家、owner、世界身份和 admission 校验；沿用原清理标记，无新包、命令字符串或 NBT 通道。

原手动单体列表和旧随机 8 怪批次不受新增随机池黑名单/体积规则影响。随机池空或初始化后超限时明确报错，不偷换成旧 8 种随机池，也不重试多个实体或修改地形。

## 文件

- 修改 `guest/src/client/java/lab/owmcguest/SummonMenu.java`：新入口、9 项根菜单分页、进入列表/重开菜单回首页。
- 修改 `guest/src/main/java/lab/owmcguest/SummonMenuRuntime.java`：服务端随机候选筛选，并将结果送入现有单体安全放置分支。
- 修改 `guest/src/main/java/lab/owmcguest/PortalMenuKeys.java`：新增 `firstPage()`，只重置页码，保留按住键的边沿保护。
- 新增 `guest/src/main/java/lab/owmcguest/{RandomSummonPolicy,SummonMenuOptions}.java`：过滤阈值/精确名单与菜单选项映射。
- 修改 `guest/src/main/resources/assets/owmcguest/lang/{zh_cn,en_us}.json`：新增随机选项、空池/尺寸错误文案，补根菜单页码和翻页说明。
- 新增 `guest/src/test/java/lab/owmcguest/RandomSummonPolicyCheck.java`；新增本文。

诊断沿用 `/world` 的 `portalMenu.summonMenu.runtime`，增加 `randomRequests`、`randomSpawned`、`randomCandidates`、`resolvedEntity`。`selection` 保持 `random:monster`；`resolvedEntity` 是服务端抽中的实际注册 ID。总请求/成功/生成数沿用旧计数，拒绝也保留 error，未生成不加成功计数。

## 共享接线（原样）

**本轮不需要修改任何共享文件或登记 Hero 模块。** 已有接线继续生效：

```java
// PortalMenu.tick(MinecraftClient c) 中已有：
SummonMenu.tick(c);
// PortalMenu.draw(DrawContext context) 中已有：
if(SummonMenu.visible()){SummonMenu.draw(context);return;}
```

[已集成 integrator]

`WorldFrameExporter`、`GuestMod`、`NativeCombatScene`、`NativeCombatRuntime`、模块注册表、`run_batch.py` 均未改。无需新增 HTTP 操作码/网络 receiver；F8/F10/F11 维持集成后的原接线。

若 Claude 将本轮检查纳入共享 `guest/build.gradle`，以下为完整新增代码（本线程未修改该构建文件）：

```groovy
tasks.register('verifyRandomSummonPolicy', JavaExec) {
    dependsOn tasks.named('testClasses')
    classpath = sourceSets.test.runtimeClasspath
    mainClass = 'lab.owmcguest.RandomSummonPolicyCheck'
}
tasks.named('check') { dependsOn tasks.named('verifyRandomSummonPolicy') }
```

[已集成 integrator]

## 离线验证

- `.venv/Scripts/python.exe tools/check_environment.py`：`ok=true`，本地证据 `research/_archive/2026-10/menus-20261027-environment.json`。
- guest `compileClientJava`、原 `verifyPortalMenuKeys` 和新 `verifyRandomSummonPolicy` 全部通过（6 个任务，最终 22s）；新检查 62 项，覆盖精确黑名单、缩小 Boss 仍禁止、小中型模组类型可选、各尺寸/体积边界、非有限值、敌对/中立判别与原版被动动物排除、空池不调用 RNG、所有候选索引可达、旧批次/单体/清理入口保留、根菜单第 2 页、按住键/失焦/busy 防重复。没有启动 Minecraft 测试服务端。
- 两种语言各 81 个键一致，UTF-8 和 `%s` 占位符数量检查通过；本轮 Java 文件定向空白检查通过。
- 本次未改 HTTP/包协议，未重复运行无关的全量桥接测试；未作实机验收。

本地临时 init 文件只登记 JavaExec 检查，位于忽略的 `research/_archive/2026-10/menus-20261027.init.gradle`；日志 `research/_archive/2026-10/menus-20261027-check.log`。不提交本地证据。

```bat
set GRADLE_USER_HOME=%CD%\tools\gradle-cache
tools\gradle\gradle-8.10.2\bin\gradle.bat -p guest --offline --console=plain --no-daemon -I ..\research\menus-20261027.init.gradle compileClientJava verifyPortalMenuKeys verifyRandomSummonPolicy
```

Claude 统一打包命令（本线程未执行）：

```bat
set GRADLE_USER_HOME=%CD%\tools\gradle-cache
tools\gradle\gradle-8.10.2\bin\gradle.bat -p guest --offline --console=plain --no-daemon build
```

## 待实机核对

1. 备份 profile/save，按当前精确进程身份与既有正常停止/恢复流程统一部署；F9 首页 1、旧批次 2、单体 8、第 2 页清理各可选，主数字行/小键盘都不重复生成。
2. 多次随机时按 `resolvedEntity`、`randomCandidates` 与实际生成数核对原版/模组候选；黑名单和超阈值实体永不经随机项生成，小中型 Boss 仍可出现。按一次只增加一只；无安全空间时 0 只且报错。
3. 密闭、边界、未加载区、切维度、失焦/施法、非创造/死亡等拒绝路径保持；抽到初始化后超限的类型也应失败而不生成。
4. mod 自定义 AI 若完全不使用 MONSTER 声明、上述接口或攻击属性，通用声明无法证明其敌对/中立性；需在实际注册池中核对后补明确的类型适配。构造失败的类型不入池。离线策略检查不证明任意模组 AI 分类、实际可见菜单或实际安全落点全部已验收。

第三轮集成索引：[INTEGRATION-20261027.md](INTEGRATION-20261027.md)。上述标记只指源码接线/删除旧行/既有接线核对，不表示实机验收。全量compileClientJava --rerun-tasks通过（27秒，3任务实际执行），未遇Loom锁、未删锁文件；未开游戏、打包JAR/DLL或部署。原“待接线”段落保留交接时历史，最新结果以本补记为准。

## 用户第三次试玩反馈追加：随机 ×8、全部 BOSS 血条排除、统一名字与三分钟期限

**本段覆盖上文“一次一只”和“小中型带血条 Boss 可以入池”的旧规格。** 本次未启动游戏、构建/部署 JAR、改动原版 DLL，也未修改下面列出的共享文件。完整生效须 Claude 应用本段两处必需接线，不能只部署本线程源码。

### 最终行为

- F9 首页 1 改为「随机召唤怪物 ×8（含模组，无BOSS血条）」。候选仍由当前服务端注册表产生，保留敌对/中立筛选和已有尺寸限制；一次请求目标为 8 只，可重复抽中同一合法类型。共用单体 `spawnOne` 的初始化、已加载区块、边界/高度、碰撞、权限和安全放置检查，增加已有 LivingEntity 占位检查，避免 8 只叠在同一落点。
- 最多尝试 80 次，某类型被初始化/血条/体积/位置检查拒绝后，本次不再尝试该类型。安全位置不足或 admission 失效时实际可能不足 8，明确报错并保留真实生成计数；不为凑数放宽碰撞或权限，不把部分结果记作满批成功。
- 随机池排除**所有能识别出独立 BOSS 血条的类型**，不再对小/中型带条 Boss 豁免。覆盖末影龙、凋零、暮色 8 Boss、天堂 3 Boss、当前 AoA 8 Boss 的精确 ID，以及实际服务端 `BossBar`/`ServerBossBar` 字段、继承/接口、泛型容器、运行时 HUD 容器、Boss 标签和自定义血条/协议元数据。没有因为当前无人追踪、血条隐藏或字段尚为 null 就放行。
- `BossBarEvidence` 使用实际 `BossBar.class` 的可赋值关系，适配 Fabric/Connector 运行时重映射；共享 Entity/LivingEntity/MobEntity 基类也用实际 Class 身份识别。其他模组自定义条通过继承、字段/返回类型、容器及类常量池中的 BossBar/BossEvent/HealthBar/BossHUD/同步协议证据识别。读取失败、生成类不可检查、容器过深/超预算均拒绝随机准入。检查深度 ≤4、对象预算 128；不遍历整个 World/AI 引用图。
- 只创建**未入世界**的候选对象进行检查，初始化后、真正 spawn 前再次复检。没有先把 Boss 召到玩家面前再杀掉。探测/失败对象走 DISCARD；公共 hook 也会拒绝探测阶段的附带 spawn，避免试探对象的自定义构造/移除逻辑通过标准 spawn 路径留下实体。
- **通过 F9 生成的旧随机 8 怪、单体、随机池和测试批次目标**统一设置 `CustomName = entity.getType().getName().copy()`、`CustomNameVisible=true`，显示该生物默认显示名。测试场景用于诊断的内部 Map 键保留；原头顶测试字符串改为生物名。
- 每只记录绝对到期标签 `owmc-f9-until:<Overworld总游戏tick+3600>` 和所有权标签 `owmc-f9-summoned`。使用 3600 个服务端游戏 tick（20 TPS 时三分钟）；暂停/停服不计入，切换白天/夜晚不会重置期限。标签由原版 Entity `Tags` NBT 保存。卸载只移出内存索引，不删期限；重载沿用原值，已经到期的立即 DISCARD。改维度仍使用同一服务端 Overworld 总时钟。
- 到期不走 damage/kill/death/loot/XP 流程，直接 DISCARD，并在同一服务端调用范围禁止移除逻辑另行 spawn 实体，覆盖标准路径上的自定义掉落物/经验球。自然生成、区块重载的普通怪物、其他测试入口不继承 F9 范围；只处理本功能明确标记的实体。

手动单体和旧固定批次保留原选择能力；“无 BOSS 血条”准入限制针对新增随机池。手动召出的 Boss 同样获得名字与到期清理。

### 本次文件

- 修改 `SummonMenuRuntime.java`：共享单体放置、随机 8 只、有界重试、请求范围及真实部分计数。
- 修改 `RandomSummonPolicy.java`、`RandomSummonPolicyCheck.java`：8/80 常量、已知带条 Boss 名单和新规格断言。
- 修改 `SummonMenu.java` 与 `lang/{zh_cn,en_us}.json`：×8/无血条/部分失败/缺少接线文案、刷新生命周期诊断。
- 新增 main Java：`BossBarEvidence.java`、`F9SummonAccess.java`、`SummonSpawnScope.java`、`SummonedMobExpiry.java`、`SummonedMobLifecycle.java`、`mixin/F9SummonSpawnMixin.java`。
- 新增 `guest/src/main/resources/owmcguest-f9.mixins.json`；common Mixin 使用 **main** 的 `owmc-guest-refmap.json`，保留已有 client Mixin 配置。
- 新增 `guest/src/test/java/lab/owmcguest/F9SummonLifecycleCheck.java`；本文仅追加，保留先前集成记录。

### Claude 必需的共享接线（原样）

1. `guest/src/main/java/lab/owmcguest/GuestMod.java` 的 `onInitialize()`，在实体登记后、启动世界前加入这一行（同包无须 import）：

```java
SummonedMobLifecycle.register();
```

[已集成 integrator]

该行放在 `owmc.frameExport` 条件外，确保旧存档加载的 F9 实体也立即接受到期检查，不能等玩家第一次打开 F9 再注册。

2. `guest/src/main/resources/fabric.mod.json` 的 `mixins` 数组追加新配置；以当前数组展开后的完整行为：

```json
"mixins": ["owmcguest.mixins.json", "owmcguest-f9.mixins.json"],
```

[已集成 integrator]

新配置已在本线程新增，原样如下：

```json
{
  "required": true,
  "package": "lab.owmcguest.mixin",
  "compatibilityLevel": "JAVA_21",
  "refmap": "owmc-guest-refmap.json",
  "mixins": ["F9SummonSpawnMixin"],
  "injectors": {"defaultRequire": 1}
}
```

[已集成 integrator]

这个公共 hook 在 `ServerWorld.spawnEntity` 的 HEAD 工作，捕获 F9 范围内真正的新生成，因而旧 `PlayerUtilities` 和 `NativeCombatScene` 的多目标路径也统一命名/计时；不把 ENTITY_LOAD 当作“新召唤”而误标自然怪物。`F9SummonAccess` 是 hook 安装标记；缺少 hook 时 F9 除清理外拒绝生成，并显示“生命周期接线未完成”，避免静默漏掉批次期限。

无需改 `PlayerUtilities`、`NativeCombatScene`、`WorldFrameExporter`、原版回调或英雄模块登记表。没有新增包/自由命令/NBT 接收协议。

可选：在共享 `guest/build.gradle` 登记新离线检查，本线程未修改该文件：

```groovy
tasks.register('verifyF9SummonLifecycle', JavaExec) {
    dependsOn tasks.named('testClasses')
    classpath = sourceSets.test.runtimeClasspath
    mainClass = 'lab.owmcguest.F9SummonLifecycleCheck'
}
tasks.named('check') { dependsOn tasks.named('verifyF9SummonLifecycle') }
```

### 诊断与离线验证

`/world.portalMenu.summonMenu.runtime` 保留请求/成功/实际生成数，新增/扩展：`requestedCount=8`、`resolvedEntities`（本批成功类型）、`randomAttempts`、`bossBarRejectedTypes`、`bossBarRejectedSlots`。`lifecycle` 刷新 `named`、`loaded`、`expired`、`loadEvents`、`lifetimeTicks=3600`。失败/部分批次仍把已实际生成的数量加入计数，不会隐藏实体。

- 环境检查已运行，结果保存在 `research/_archive/2026-10/menus-20261027-feedback3-environment.json`。
- `compileClientJava`、`verifyPortalMenuKeys`、`verifyRandomSummonPolicy`、`verifyF9SummonLifecycle` 离线运行；新检查覆盖延迟 null 血条、继承字段、泛型 Map、Object/Optional/List 包装、父接口、自定义协议、不可读取类型、容器预算/循环、实际 Class 身份的重映射检测，以及期限边界、卸载跨过期、重载不续期和坏标签拒绝。
- 实际已安装 JAR 的只读元数据核对：Aether 的 `SunSpirit`、`ValkyrieQueen`、`Slider` 三类含服务端条引用；AoA 的 `AoABoss` 基类含服务端条引用（覆盖派生 Boss）。证据只含类名/数量：`research/_archive/2026-10/menus-20261027-feedback3-boss-metadata.json`；未复制游戏类或提取内容进源码。
- common Mixin 的 main refmap 映射已核对为 `ServerWorld.spawnEntity` → `Lnet/minecraft/class_3218;method_8649(Lnet/minecraft/class_1297;)Z`，避免误用旧 client refmap。新旧语言键及占位符另作检查。

本地临时检查命令（init 只登记 JavaExec，没有构建 JAR）：

```bat
set GRADLE_USER_HOME=%CD%\tools\gradle-cache
tools\gradle\gradle-8.10.2\bin\gradle.bat -p guest --offline --console=plain --no-daemon -I ..\research\menus-20261027-feedback3.init.gradle compileClientJava verifyPortalMenuKeys verifyRandomSummonPolicy verifyF9SummonLifecycle
```

日志 `research/_archive/2026-10/menus-20261027-feedback3-check.log`。统一打包仍由 Claude 使用本文前述 `gradle -p guest ... build` 原流程；本线程没有打包/部署。

### 尚需统一实机验收

1. 应用**两处必需接线**、备份存档/profile 后统一部署。分别验证 F9 随机 ×8、旧批次、每个测试场景、手动单体，实际生成者都有默认名称、可见标志、所有权和原始截止 tick。随机实际数不足 8 时检查对应 error/计数，不接受虚报满批。
2. 从当前注册池核对普通/模组敌对和中立仍可抽到；各 AoA/Aether/暮色 Boss、延迟创建/自定义条类型不进入随机池。核对附近实体和 Boss HUD：试探/被拒绝对象未入世界，不留下条或实体。
3. 同一批记录服务端初始 tick，跨过 3600 tick 检查 `expired`/`loaded` 与实际实体消失；隔离现场比较物品/经验球计数，确认不新增。再做“未到期卸载→到期后重载”、保存重启后重载、跨维度测试；原截止值不得改变，已过期对象不能重获三分钟。
4. 缺少 common Mixin 的离线装配应拒绝 F9 生成；非创造、死亡、失焦、世界/模型切换与旧权限边沿继续拒绝。
5. 本轮只证明离线代码/元数据/计时策略；未运行实际类加载变换、区块实体保存恢复、掉落/经验和可见菜单验收。对未来模组完全外置、无任何 Boss/血条/协议线索的自定义机制，仍须按其服务端注册/协议补适配；不能把当前已安装类型的覆盖冒称为任意未来模组都经实测。

最终本地结果：`compileClientJava`、按键回归、随机策略 **63 项**、血条/持久化期限策略 **39 项**全部通过，最终 Gradle 7 task / 25s；两语各 **84 键**与占位符一致。新 common 配置已由 `processResources` 复制、main refmap 条目已核对；共享 `fabric.mod.json`/`GuestMod` 接线仍待 Claude 落地。以上是离线结果，不代表实际游戏已验收。
