# 第三方素材与实现参考台账

2026-10-24 10:31：美喷雾冻结独立实现已实际验收，语义参考仍固定
EntityMeiBlast.java / ebbc2324c123fcafc81fdc6749cde50ea0dc5e09 / SHA25696c1acc2…。
config台账登记目标MeiFreezeProgress.java及版本差异；30接触/10tick间隔/90tick
冻结来自2018参考，非已认证Beta计时。原代码/素材均未复制，生产素材导入仍0。
粒子/声音使用MC自带资源；完整范围、实际通过和失败见NATIVE-MEI-FREEZE.md。

2026-10-24追加：固定提交的ItemMeiBlaster.java（SHA256 f628f710…）与
EntityMeiBlast.java（96c1acc2…）已逐文件Git blob/SHA256校验并保留在私有缓存。
前者仅参考冰箱期间灭火语义，当前生产仍用原Beta实际阶段与治疗参数；后者为
喷雾冻结研究，尚未部署。没有导入其源码、计时器、模型或音效；见机器清单新增
historical_implementation_references和NATIVE-MEI-DETAILS.md，Private License限制保留。

更新：2026-10-23。机器清单：[config/third-party-assets.json](../config/third-party-assets.json)。
本轮新增的33个实际文件仅进入私有候选缓存，**没有导入生产JAR，没有替换OW
原生模型，没有发布或提交第三方文件**。逐文件来源、固定版本、哈希与用途均已记录。

## Minewatch 固定身份与使用范围

作者：2piradians / Minewatch团队。正式模组入口：
[CurseForge Minewatch](https://www.curseforge.com/minecraft/mc-mods/minewatch)。
源代码核对固定为提交 `ebbc2324c123fcafc81fdc6749cde50ea0dc5e09`
（2018-04-29），不是跟随可变分支。实际 `build.gradle` 为Forge
`1.12.2-14.23.3.2673`、Java8、模组 `1.12.X-3.13`；仓库分支名1.12.1不能
替代实际构建版本。当前目标是Fabric1.21.1/Java21，不直接安装旧JAR。

[固定提交LICENSE](https://github.com/2piradians/Minewatch/blob/ebbc2324c123fcafc81fdc6749cde50ea0dc5e09/LICENSE)
实际SHA256：`2f0d35191312811d352e52f8601908cc29d4c5ecb4287ef96271f2518d4d4012`。
这是Private License；可私人研究/修改，公开修改或衍生需要作者书面许可，
不能再分发源代码、素材或模组镜像。CurseForge同时标为All Rights Reserved。
用户授权本机私用复用不等于取得公开发布许可。此台账可记录元数据，实际受限
文件保留在项目Git范围以外，后续转换输出也须保持私有并逐项追加记录。

## 实际缓存与核验

私有根：`~/.universal-modder/references/minewatch-20261023/candidate-assets/`。
本轮33文件，共1,812,899字节。每个文件都经原作者GitHub固定提交URL获取，
实际字节计算Git blob SHA1，并与先前固定提交递归树记录一致；另计算SHA256。
它们是可追溯的候选文件，尚未实际渲染或安装。哈希证明文件身份，不证明适合
现有比例、坐标、发射方向、材质、动画或游戏内还原。

| 候选组 | 本轮实际文件 | 可评估用途 | 当前结论 |
| --- | --- | --- | --- |
| 狂鼠榴弹 | OBJ+MTL、`junkrat_weapon_3d.png` | 榴弹外观及滚动/旋转显示 | 贴图依赖已补入候选缓存；比例/挂点/碰撞待测 |
| 狂鼠地雷 | OBJ+MTL+实体贴图 | 投掷地雷、落地和引爆表现 | 模型/材质依赖有身份，玩法与原生事件未接入 |
| 狂鼠夹子 | bottom/middle/top三组OBJ+MTL、夹子贴图 | 开合与触发时的可见结构 | 三部分分别有哈希；关节/姿态/实体碰撞待测 |
| 美冰箱/冰锥 | 各OBJ+MTL+贴图 | 冰锥弹体与冰箱外壳 | 尚未替换原生手部或技能表现 |
| 黑百合钩索 | OBJ+MTL、钩子/绳索贴图 | 钩子弹体、绳索连接 | 绳索附着点和拉拽规则待适配 |
| 黑百合毒雷 | 整体和上下部分OBJ+MTL、蓝/红贴图 | 投掷、落地、触发/阵营显示 | 整体MTL引用不存在的通用纹理名；不能直接导入当完整 |
| 半藏箭 | 普通/音波箭两张贴图 | 结合当前箭模型评估材质 | 固定树有箭renderer，未发现独立箭OBJ；不宣称已有完整模型 |

机器清单还记录OBJ顶点数、面数、包围盒、mtllib，以及MTL逐项贴图依赖。
`widowmaker_mine.mtl` 引用 `minewatch:entity/widowmaker_mine`，对应PNG不在固定
树里；上下部分引用蓝色贴图。后续必须核对旧renderer动态材质选择并显式适配，
不能生成一个同名贴图后声称原版文件齐全。

固定树未发现托比昂炮台实体模型；少量托比昂图标存在不能当成完整炮台素材。
本轮没有为堡垒替换武器模型：项目原生OW已经拥有原版手部，MC素材只补缺失的
世界实体/技能表现，不以模组武器覆盖原生展示。

## 先前实现参考与本轮素材复用的区分

此前四输出制作实际读过Minewatch的治疗场、Recall/SavedState、Wraith/Shadow
及武器实现，作为私人行为参考；已有文档明确没有把受限代码或声音/模型复制
进生产JAR。本轮清单列出缓存中实际存在的四个代表源码文件及SHA256：
`EntitySoldier76Heal.java`、`ItemTracerPistol.java`、`ItemReaperShotgun.java`、
`ItemPharahWeapon.java`。这不是完整阅读历史，不冒称已追溯所有旧资料。

本轮增加的是原文件候选缓存和元数据，生产导入计数仍为0。2018模组规则只是
实现参考；OW本机2015 Beta事件/配置和2016经典语义仍分别核验，不把模组
数值、现代吸血或改版技能当作早期OW。保留原生英雄/动画/HUD的双进程路线。

其他已有来源：早期中文原录音、OWLib抽取物和MC自建模型已有各自文档与私有
索引；本文件尚未完成它们的全量逐文件整合。见EARLY-CHINESE-VOICE.md、
GENJI-VOICE.md、ORIGINAL-PROJECTILES.md及对应assets脚本。未整合不代表可公开分发。

## 后续真正导入时必须追加

每个导入项记录：作者、原始URL/提交/文件路径、原始SHA256、许可、私有目标
路径、转换工具/版本与参数、坐标/比例/材质/挂点/动画改动、输出SHA256、
对应原生事件、实际截图/录音、碰撞伤害与生命周期验收。机器字段
`target_path` 当前为null、`transformations` 为空，`visual_fit/in_game` 均false。
只有实际导入和测试发生后才能改变。

清单不得记录API令牌或下载会话信息。素材进入任何公开包前须重新核对许可和
实际文件清单；当前授权没有要求发布，亦未进行发布。

私有证据：`research/map-catalog-20261023/minewatch-cached-result.json` 保存本轮
统计和缓存位置；机器清单保存所有33文件的固定Git blob与SHA256。

## 续作取得的Shadow地图与资源包

这是地图候选缓存，未进入生产运行档案，也不计作Minewatch导入。完整来源链、
原始包身份和机器字段见PVE-MAPS.md、config/pve-maps.json及私有下载报告。

| 文件 | 作者来源 | SHA256 | 当前用途 |
| --- | --- | --- | --- |
| Shadow世界ZIP，77,380,608字节 | Mundi / TheWorfer27本人MCCreations记录指定Drive | `e992151058233379e49cc1ab72f831131b0e01be2ad97e70d309913db986f357` | 只读预检；实际1.21.4，禁止当前1.21.1打开 |
| 外部多人资源ZIP，52,345,462字节 | Mundi本人PMC描述指定Drive；包内署名eepyhana/pigwa | `2d11b1d7f5906afcc795132e028a23d3b0c33e5026ce3f99a82fb9d7e330fa4c` | 只读路径/CRC/元数据；未安装或转换 |
| 世界内嵌resources.zip，52,348,124字节 | 同一原世界ZIP内 | `178b29bad8c23caef425f2dc153b6c592fc79b8e564c262ff9802eebfdcb120c` | 有界内存检查，未另行导出；不同于外部资源包 |

作者页提供私人游玩下载，但没有查得允许本项目公开再分发的许可；不把下载
链接视为开放素材授权。这些文件不进入Git或发布包。地图其他署名包括
Smarty的command repeater、InterWall的inventory、Scorpionem/Mundi的crafting
数据包；这些是包内实际描述，尚不等于完整作者/许可清单。

## The Mewoster 私有补充测试图

来源：[OpenVoxel Studios现行作者页](https://openvoxel.studio/maps/the-mewoster)
明确指定其本人GitHub Releases的`the-mewoster.zip`。署名Kubik、ChoosingBerry、
The Bread Giver；作者站All Rights Reserved，未取得公开再分发许可。

原包SHA256 `2388fecb1e6734f7846911c23bbfab71f430233c0813bd53da8b823ca692e1d3`，
4,351,550字节；内嵌资源ZIP SHA256
`3ef321ca70006f1b3b98fa515a45d5dc06f1f1e78b9260f8b9cfc17d4537eea2`，79,198字节。
原包只在项目外私有缓存，资源包只在内存中检查，未提取进JAR、未转换、未安装。
元数据见config/pve-map-probes.json，原规则及具体证据见PVE-MAPS.md。
补充小图仅用于兼容性探测，不作为“热门五图完成”的一张计数。

## Arena of Darkness 原包与内嵌资源

来源：[Mundi作者页](https://www.mccreations.net/en-US/maps/arena_of_darkness)
→ 同作者公开文件记录 → 该记录指定的Drive原包。作者TheWorfer27、Twelfth115；
实际包1.20.4。原包未安装或改动；之后已生成仅私有的部分数据包迁移候选，
仍不可安装或称1.21.1兼容，未上传。

世界及资源合包192,507,154字节，SHA256
`624c63961ac4610e42a77d9ab4552e84f6a9a3f6e925693e910aa25a2a3ef5c9`；
内嵌resources.zip 131,919,310字节，SHA256
`eca96a4a546f1685a3dcce68b1ed7904074a5c59615b0ecfe684c4e07bb7980a`。
原包仅在项目外私有缓存，内嵌文件只在内存中检查；没有抽出音效或贴图进入
生产JAR。许可仍是未查得公开再分发授权，不能当作开放素材包。

包内描述还记录VanillaTweaks Armor Statues、CMDred Time Library、基于
vdvman1模板/sourceblock生成的raycast等参考；其中部分数据包原本禁用。
这些署名是实际包内信息，未完成逐作者/逐资源许可审计，不能因为原地图
可下载就宣称全部声音和贴图均可再分发。详见PVE-MAPS.md与私有nested报告。

本轮部分迁移候选仅改三个启用嵌套数据包的精确目录/JSON，来源仍是同一个
原作者包；不是新许可、不是已验收世界或生产资源导入。新ZIP SHA256
`0429bc43a220713412402c1fa344c10ad3d9035faa37672ef5cbe2e48e50ecdb`，
192,230,816字节，位于项目外maps私有缓存。完整规则、逐文件原/新哈希、
749项原payload、重复构建与未完成项见ARENA-PORT.md及对应私有manifest。
原地图命令、模型、音效、Shader及转换包均不进入Git或公开发行；本轮未把
任何受限文件复制进生产JAR。元数据和通用预检/转换代码与实际受限包分开保存。

后继v2仅在私有候选中迁移81处dust命令字符串，SHA256
`2ebb56d9140253c2c26cfd7d4b30de6ea568fc53002bcead382e29aa40e7edf1`，
191,457,363字节。来源沿用原作者→v1链；不增加素材授权。19个文件发生有界
变化，其他733个payload保留；Shader、模型、音频均未转换或导入生产。
逐命令原/新文本与哈希、NBT保留证明仅在私有arena-port-2证据中，公开台账
只保留身份与转换范围。该候选仍不可安装，未通过Boss玩法验收。

## 猎空脉冲炸弹：本机24919原始模型

2026-10-23实际读取用户本机精确哈希离线Beta24919 CASC，沿原生
`0400000000000045`实体→`0d00000000000b2c`模型→Look/Material→原512²纹理
完成有据转换。作者/权利人为Blizzard；用户私有研究/本机加载，未取得公开分发授权。
OWLib格式源码作为工具参考，不把其MIT许可解释成游戏模型/纹理的许可。
没有从Minewatch导入这个模型，也没有声称来自不支持的154504零售导出。

原网格SHA256 `f90dee3ea70c5ff84ba8c516dc83feb1bce2a49bd599c6a65630769f2cb6dd37`；
731顶点/868三角形，保留米制比例，只平移包围盒中心。原BC1/BC3 DWORD平面交错
复原后解码颜色与发光层，MC不透明金属/加法发光和接触朝向属于明确的展示适配。
完整8资源、3包来源/哈希、输出身份/转换限制见
[PULSE-BOMB-ASSETS.md](PULSE-BOMB-ASSETS.md)及专属工具。

原始文件仅在`~/.universal-modder/assets/ow-beta-24919-pulse/`，转换包仅在
`~/.universal-modder/assets/owmc-pulse-bomb/`，未复制进生产JAR或仓库；
JAR读取私有文件的代码已落源码。第二次独立构建三输出SHA一致，21合成fixture及
纯Java姿态fixture通过；实际软件预览已看。本轮尚无新模型游戏画面验收，不能以
`prepare.ready=true`冒充实机通过。Minewatch33候选生产素材导入仍为0。
