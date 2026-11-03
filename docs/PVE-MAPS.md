# Boss PVE 地图库：来源与验收

更新：2026-10-23。用户已批准持续开发；本页记录第一增量的实际结果。
机器清单为 [config/pve-maps.json](../config/pve-maps.json)，启动器读取同一清单。

目前五张均为 **candidate**；Shadow 原包已实际预检但为 **incompatible**，
其余仍pending。Arena已生成明确不可安装的部分迁移候选，见ARENA-PORT.md；
没有任何一张已安装、进入世界或通过融合 Boss 实战。
版本相同、下载量高和 ZIP 预检通过都不等于兼容通过。
本轮未操作游戏、未修改现有 profile、未将旧世界升级。

## 来源初筛与真实缺口

热度为2026-10-23所读 MinecraftMaps 页面显示的约数，不是全网排名，不能
把不同站点数据相加。作者上传页是初始来源；拿到包后仍需核对原始说明和许可。

| ID / 地图 | 作者 / 发布入口 | 原始版本与页面地图版本 | 当日显示下载量 | 当前工作项 |
| --- | --- | --- | --- | --- |
| `aghanims-labyrinth-2` / Aghanim's Labyrinth 2 | [Mr_Kheese 原作者](https://www.planetminecraft.com/project/aghanim-s-labyrinth-2-roguelike-pve-map/)，[作者上传列表](https://www.minecraftmaps.com/50287-aghanims-labyrinth-2) | Java1.21.1 / 1.2 | 约50,100 | 首选同版；16层及Boss，需要正确初始化的Boss检查点 |
| `shadow-of-the-skeleton-king` / Shadow of the Skeleton King | [Pigwa、eepyhana、TheWorfer27，Mundi Maps 上传](https://www.minecraftmaps.com/50459-shadow-of-the-skeleton-king) | Java1.21.1 / 1.1 | 约20,500 | 城堡/解谜前置，不能只传送坐标绕过初始化 |
| `arena-of-darkness` / Arena of Darkness | [TheWorfer27、Twelfth115，Mundi Maps 上传](https://www.minecraftmaps.com/50005-arena-of-darkness) | Java1.20.4 / 列表1，作者元数据1.0.0 | 约18,800 | 22个Boss；原包已取得并完成结构/CRC检查，旧目录/命令仍待移植 |
| `boss-blitz-arenas` / Boss Blitz Arenas | [LettuceMayoAndOnion 作者上传](https://www.minecraftmaps.com/47262-boss-blitz-arenas) | Java1.17.1 / 1 | 约7,000 | 7Boss/5竞技场；旧命令、濒死阶段及装备奖励尚待迁移 |
| `aghanims-labyrinth` / Aghanim's Labyrinth | [Mr_Kheese 原作者](https://www.planetminecraft.com/project/aghanim-s-labyrinth/)，[列表页](https://www.minecraftmaps.com/48663-aghanims-labyrinth) | Java1.19.4 / 列表1.6.4b，作者可见日志1.6.3b | 约22,900 | 版本号有冲突，先以实际包身份核实；不可默认为1.21.1兼容 |

一代作者页明确支持1.19～1.19.4，作者后续曾确认1.20.2失效；另有玩家评论称
1.21.1可玩。这两类证据不等价，评论不能替代项目实测。二代作者页明确要求
1.21.1，且存在1.2更新日志；不会取搜索结果中的旧1.1.1包代替。

## 本轮下载结果

已核对二代作者的下载按钮及公开入口：
[作者提供的下载入口](https://www.planetminecraft.com/project/aghanim-s-labyrinth-2-roguelike-pve-map/download/mirror/710107/)。
这里的 `/download/mirror/` 是原作者页面自身的按钮路径，不能据此猜出目标包地址。

实际请求 MinecraftMaps 详情页、PMC作者页与其下载入口均返回 HTTP403；
网页读取工具能看到详情，但点击下载入口只重定向回详情页，没有可核验 ZIP
直链。因此没有下载包，也没有 ZIP SHA256/预检/安装成功记录。没有尝试
Mapcraft等其他镜像、广告下载器、猜测静态文件名或可执行安装器。

失败证据保存在私有 `research/map-catalog-20261023/author-fetch.json`。
后续可以用正常浏览器访问原作者入口确认实际可下载链接；未解决前候选卡片
显示“下载入口待解决”，不显示“开始挑战”。其余四张只核对了作者上传详情页，
下载状态为 `not_attempted`，没有把未尝试写成下载失败。

## 已实现的只读预检工具

新增 [tools/pve_map_catalog.py](../tools/pve_map_catalog.py)：

- `load_catalog()` 校验清单结构、ID重复和基础来源；`challenge_ready()`
  要求兼容状态 `accepted` 且四项验收均为真正布尔 `true`。
- ZIP预检从不解压、不安装、不启动游戏。拒绝绝对路径、路径穿越、Windows
  盘符/ADS/保留名/结尾点空格、大小写别名、符号链接、加密条目及可执行文件。
- 限制文件数量、单文件和总展开大小；计算整个原包SHA256。只读取有界的
  `level.dat`，检查gzip/NBT并报告DataVersion、版本名、世界名和模式。
- 要求一个明确的世界根；列出区块、数据包条目、内嵌资源ZIP与说明文件。
  内嵌资源包、命令方块内容、所有非元数据条目的CRC和实际技能兼容尚未检查，
  这些限制会写入结果。即使 `archive_preflight=true`，其余玩法验收仍为false。
- 输出报告只写新文件，已有证据不覆盖；没有自动下载、移动或删除功能。

示例（以后拿到已核实的包后执行）：

```powershell
.venv/Scripts/python.exe tools/pve_map_catalog.py
.venv/Scripts/python.exe tools/pve_map_catalog.py --preflight '<USERPROFILE>/.universal-modder/maps/author-map.zip' --out research/map-preflight-fresh/report.json
.venv/Scripts/python.exe -m unittest discover -s tools -p test_pve_map_catalog.py -v
```

第一增量13项fixture测试通过，包含恶意路径、符号链接、别名、安装器、预算、
无/多世界、坏gzip/NBT、资源清单、不落盘与未验收候选拒绝放行。
这是工具测试；续作的真实Shadow包结构检查见下文，仍没有实际Boss战通过。

## 2026-10-23 14:13 续作：真实取得Shadow原包，拒绝高版本

Aghanim2已有连续403/网页下载回详情证据，本轮换路线。后台浏览器创建返回
`Browser is not available: iab`；未改用前台Chrome、未发送桌面或游戏输入。
Shadow两张原作者PMC页及Hellfire作者页直接请求也403，未绕验证。

Shadow最新[Mundi PMC页](https://www.planetminecraft.com/project/shadow-of-the-skeleton-king/)
已经写1.21.4；[pigwa PMC页](https://www.planetminecraft.com/project/shadow-of-the-skeleton-king-6398230/)
写1.21.5。不能因为旧列表是1.21.1，就默认原作者当前链接还是旧包。

实际成功来源链为：

1. [Mundi / TheWorfer27 创作者页](https://www.mccreations.net/en-US/creator/theworfer-27)
   → [该作者Shadow发布页](https://www.mccreations.net/en-US/maps/shadow_of_the_skeleton_king)。
2. 该站公开[前端源码](https://github.com/MCCreationsOS/mccreations-next)实际配置
   `DATA_URL=https://api2.mccreations.net`；只读[该图公开记录](https://api2.mccreations.net/creations/maps/shadow_of_the_skeleton_king)
   返回owner=`theworfer-27`、文件1.0.0/声明MC1.21或1.21.1和作者原Drive链接。
   未调用上传、修改、下载计数或其他写入接口。
3. [作者Drive世界文件](https://drive.google.com/file/d/1uohkF3EL80mmxM8t0nWr3wTWp2vmz4M2/view?usp=sharing)
   实际取得 `ShadowOfTheSkeletonKing.zip`。Google的文件体积扫描提示使用其
   正常“Download anyway”表单；没有验证码、登录或浏览器安全警告绕过。

原包77,380,608字节；SHA256：
`e992151058233379e49cc1ab72f831131b0e01be2ad97e70d309913db986f357`。
私有缓存 `~/.universal-modder/maps/shadow-of-the-skeleton-king/ShadowOfTheSkeletonKing-1.0.0-source-20261023.zip`。
没有解压至项目、没有放进当前存档目录、没有启动它。

**实际NBT是1.21.4 / DataVersion4189，而不是页面声明的1.21.1。**
166项、37个region文件、一个明确level.dat、5组数据包和内嵌resources.zip。
结构/路径/gzip/NBT通过，外包所有条目CRC通过；内嵌资源包、两个嵌套数据包
也完成有界路径/体积/CRC检查。元数据中含pack_format57的InventoryPack及
player movement库，不能仅修改level.dat版本号就当成降版可用。

因此清单仅将 `archive_preflight=true`，兼容状态为 `incompatible`，世界加载、
战斗和重打仍false。**禁止用当前1.21.1打开或试着降版该世界**；需要作者提供
旧版包或另找同版Boss图。MCCreations页面/文件声明已证实陈旧，原始证据保留。
level.dat有fabric/axiom等启用记录，不足以证明运行时必须装Axiom；依赖仍需
运行环境核验，不能把编辑器残留当作已证实硬依赖。

另外从Mundi PMC明确提供的[多人资源包链接](https://drive.google.com/file/d/1hIE53abYRbSbMd9DVMKdDFwNaBYRxpJW/view?usp=sharing)
取得52,345,462字节ZIP，SHA256
`2d11b1d7f5906afcc795132e028a23d3b0c33e5026ce3f99a82fb9d7e330fa4c`，
285项，路径/体积/CRC通过，只有资源包、没有level.dat，未安装。
它与世界内嵌resources.zip哈希不同；两者保持独立身份，不混为同一版本。

私有证据位于 `research/map-catalog-20261023/download-followup/`：
`requests.json`、`shadow-world-download.json`、`shadow-world-preflight.json`、
`shadow-nested-preflight.json`、`shadow-resource-result.json`；原作者站点开源
前端与公开地图记录另有只读快照。地图/资源ZIP仅在项目外私有缓存，不进入提交。

## 2026-10-23 14:18 续作：同版短Boss补充图已取得

Hellfire原作者页直接请求403，网页工具的下载点击返回内部错误；Everdark
[原作者下载按钮](https://www.planetminecraft.com/project/everdark-reaper-1-21/download/mirror/712467/)
实际请求403、网页读取重定向回详情。没有用9Minecraft、DLCfun等镜像下载；
MCCreations的Reaper查询也没有该作者这两张Boss图。

换用短Boss补充候选 **The Mewoster**。它是小众地图，**不计最终热门五图**，
独立机器清单为 [config/pve-map-probes.json](../config/pve-map-probes.json)。
MCCreations的OpenVoxel作者记录声明1.21+，旧作者下载路径为软404；沿作者
官网实际 `/maps` 链接找到[现行作者页](https://openvoxel.studio/maps/the-mewoster)，
“Download Latest”明确链接到[作者GitHub原包](https://github.com/OpenVoxelStudios/Maps/releases/download/v1.0/the-mewoster.zip)。
作者署名OpenVoxel Studios、Kubik、ChoosingBerry、The Bread Giver；没有借用
镜像、下载器或重新打包文件。

真实ZIP：4,351,550字节，SHA256
`2388fecb1e6734f7846911c23bbfab71f430233c0813bd53da8b823ca692e1d3`。
缓存 `~/.universal-modder/maps/the-mewoster/the-mewoster-v1.0-source-20261023.zip`。
GitHub发布容器为v1.0，asset ID183811886；发布容器日期不当作此地图创作日期。

实际NBT **1.21 / DataVersion3953**，没有高于当前1.21.1。956项、16个region、
世界根`The Meowster`，保存模式为冒险；两个数据包均pack_format48，内嵌资源
pack_format34。结构/路径/gzip/NBT及外包全部CRC通过；资源ZIP有界路径、体积
与CRC通过。作者页面明确提示：**首次游玩需退出重进一次**。这些只允许进入
下一轮隔离运行验证，尚不能标成兼容或“开始挑战”。本轮没有安装或启动世界。

静态实际规则核查：

- 可见Boss是Animated Java模型，承载者是无敌流浪商人；生命不是普通实体HP，
  而是`health meowster`计分板，原生Bossbar为`health`，总计12格。
- 真正削血条件是打中投出的`exploding_cat`：原脚本读取猫的
  `HurtByTimestamp`，令其按攻击者视向折返；折返猫进入Boss3格内，原函数才
  减少一格生命。不能直接对无敌承载者造成伤害或手动扣计分板冒充Boss战。
- 原作者欢迎按钮调用`meowster:summon`；load设置计分板、Bossbar、冒险默认
  模式及重生/回血规则。后续使用原入口初始化，不能只传送坐标或跳过首次重进。
- 必须实测OW已确认发射命中猫时是否带真实玩家伤害归属、是否触发原折返，
  并完整验证12次原机制、玩家受伤/失败、死亡动画、胜利和原入口重打。
- 创造无敌、全局回血、F10靶怪、爆炸炸图等工具设置都可能破坏挑战；使用独立
  PVE档案，不改全局默认世界。不能因NBT版本较旧就称融合玩法已完成。

预检与规则证据：`mewoster-world-download.json`、`mewoster-world-preflight.json`、
`mewoster-rule-inspection.json`，均位于上述私有download-followup目录。受限
函数和模型仅在私有原包中读取，公开文档只记录机制和文件哈希。

## 2026-10-23 14:34 续作：热门候选Arena原包已取得

本轮沿已经验证的作者公开元数据方法继续推进，没有重新刷Aghanim的403。
唯一词`Aghanim`和`Labyrinth`目录查询没有找到MrKheese的原作者条目；
`Blitz`也没有找到Boss Blitz Arenas。搜索不到只表示本次目录没有可用入口，
不代表作者从未在其他平台发布，也没有借用匿名镜像补包。

热门五图候选之一 **Arena of Darkness** 已从
[Mundi作者发布页](https://www.mccreations.net/en-US/maps/arena_of_darkness)
及[该图公开作者记录](https://api2.mccreations.net/creations/maps/arena_of_darkness)
取得明确原链接：owner=`theworfer-27`，作者TheWorfer27/Twelfth115，声明1.20.4，
文件版本1.0.0 → [作者Drive原包](https://drive.google.com/file/d/16RjFYzacEu_Ln7RpKEEgfKe85jEaH9BH/view?usp=sharing)。
其22个Boss、升级和资源包说明也在作者页核对。

真实包名`ArenaOfDarknessWorldAndRP.zip`，192,507,154字节，SHA256：
`624c63961ac4610e42a77d9ab4552e84f6a9a3f6e925693e910aa25a2a3ef5c9`。
私有缓存 `~/.universal-modder/maps/arena-of-darkness/ArenaOfDarkness-1.0.0-source-20261023.zip`。
实际NBT **1.20.4 / DataVersion3700**，保存模式生存；未被高版本覆盖。
757项、195个region文件，展开合计526,164,784字节。整个原包CRC、路径和
有界NBT通过；全部六个嵌套数据包与内嵌资源ZIP都完成路径/体积/符号链接/
加密/可执行文件检查及CRC。全程只读，没有解压安装或启动世界。

内嵌resources.zip为131,919,310字节、329项、pack_format22，SHA256
`eca96a4a546f1685a3dcce68b1ed7904074a5c59615b0ecfe684c4e07bb7980a`。
原level.dat实际启用ArenaOfDarknessDatapack、PlayerRaycastLaser和
VillagerRaycastLaser；armor statues、NoCrafting、TimeDatapack处于禁用。
有一个Bukkit元数据占位目录，**不能只凭这个目录认定必须Bukkit服务端**。

已证明的移植缺口：

- 两个启用的raycast数据包仍使用`functions`和`tags/functions`旧路径；
  主数据包也有`recipes`和`loot_tables`旧路径，而非仅pack_format警告。
- [Mojang的1.21正式变更说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21)
  明确将这些目录改为单数，并将数据包/资源包格式更新为48/34。原目录不能
  靠提高pack_format或升级世界数据就自动当成已适配。
- 绝大部分Boss规则可能在地图命令方块中；本轮没有扫描所有region里的命令
  字符串，也没有转换旧物品/实体属性NBT、核对受伤实体或运行阶段/胜负。

主清单现在仅 `archive_preflight=true`，兼容仍pending并写明需要移植。
原包1.20.4不是已验收的1.21.1候选构建，不允许直接显示“开始挑战”。
当前可进入后续同版实测的补充模板仍是The Mewoster；Arena保留为正式热门
候选移植输入。实际玩法为0通过，热门五图交付为0完成。

私有证据位于`research/map-catalog-20261023/download-next/`：
`arena-author-metadata.json`、`arena-world-download.json`、
`arena-world-preflight.json`、`arena-nested-preflight.json`及目录检索快照。

## 2026-10-23 15:23 续作：Arena静态审计与部分转换

详见[ARENA-PORT.md](ARENA-PORT.md)。已实际扫描全世界444个MCA、90,162个
分配chunk及183个独立NBT，取得11,400条命令出现/7,832条不同文本。旧物品
生成、tag路径、实体属性与粒子参数仍是实证缺口；风险匹配不是语法解析通过。
资源包两个自定义Shader也已对照本机原版1.21.1接口，发现fog_distance签名及
position输入/参数不匹配，不能直接提高资源格式后开图。

受控工具只转换三个启用嵌套数据包的精确目录与简单配方/成就/Loot上下文，
生成项目外私有partial ZIP，SHA256
`0429bc43a220713412402c1fa344c10ad3d9035faa37672ef5cbe2e48e50ecdb`。
第二次构建完整ZIP哈希相同；749个原文件payload完全保留，包括628个世界
NBT/MCA文件与resources.zip。输出实际ZIP/NBT预检、全部CRC和18个新fixture
通过；原14个预检fixture继续通过。

这仍是**blocked_static / installable=false**的部分迁移候选，不是可运行地图。
没有伪改DataVersion、自动升级、安装或启动世界，正式五图仍0张玩法验收。
机器清单新增static_migration元数据，启动器准入政策与四项实际验收没有放宽。
原包、候选、完整命令及Shader差异仅在私有缓存/research中；没有受限包提交。

后继v2已实际迁移81处原生命令方块dust参数（17个MCA/27个chunk、2个重置
结构），保持原前缀/后缀、其他Command及所有非Command NBT字节。新私有ZIP
`2ebb56d9140253c2c26cfd7d4b30de6ea568fc53002bcead382e29aa40e7edf1`
重复完整哈希相同；旧粒子风险88→7，仍有旧物品/属性/Shader缺口。v2依然
blocked_static，不放开安装或挑战。独立delta复核及17项新增fixture见
ARENA-PORT.md和`research/map-catalog-20261023/arena-port-2/`；没有实际Boss战。

## 五图正式准入

1. 作者来源与许可、原包/资源包SHA256、README及依赖齐全；结构预检通过。
2. 独立世界副本在目标运行档案中加载，命令/数据包/资源包完成核对；不覆盖
   默认融合世界，不用缺失暮色模组的环境打开其存档。
3. 建立正确初始化的Boss前检查点，保留阶段、无敌、弱点、多部位、计分板和
   胜利规则；正常剧情入口仍可使用。
4. 实测OW子弹、射线、近战、爆炸和技能对真实受伤实体结算；验证击杀归属、
   Boss阶段变化、玩家受伤、失败、奖励、原生MC血条和OW HUD。
5. 完成一轮真实战斗，再重置重打一轮；记录截图、混音、版本、伤害和结果。
6. 完成 `archive_preflight / world_load / boss_fight / reset_replay` 全部证据，
   兼容状态改为 `accepted` 后才开启“开始挑战”。暂不兼容就保留原因或替换候选。

当前全局创造模式、工具热键和爆炸破坏可能冲突于地图规则；每图必须建立独立
配置，不能用无敌状态秒杀靶子当作PVE验收，也不能静默修改所有地图设置。

## 下一步

先由唯一游戏驱动者评估The Mewoster隔离挑战副本及冒险规则；当前包仅完成
结构验证。Shadow原包高版隔离，不降版打开；另寻找作者仍提供的1.21.1原包，
最终热门五图目标继续保留，补充图不顶替五张已验收交付。Aghanim/Hellfire/
Everdark现有访问失败留证据，未有新入口时不反复刷同一请求。

本轮检索词：`Aghanim's Labyrinth 2 MrKheese download`、
`site:planetminecraft.com Aghanim 2`，以及以上五个完整作者上传URL。
