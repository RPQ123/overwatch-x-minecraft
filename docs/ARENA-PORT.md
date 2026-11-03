# Arena of Darkness：1.20.4 → 1.21.1 静态移植

2026-10-23。本轮实际完成只读全世界审计、受控部分转换、产物复核和可重复
构建；**尚不可安装或开打**。没有打开世界、操作游戏、修改任何现有profile。
原作者包保持不变，实际地图/资源/转换包和完整命令内容只在私有缓存及忽略的
research证据中。来源、许可和正式五图准入继续见PVE-MAPS.md。

## 输入与输出身份

- 原作者：TheWorfer27、Twelfth115 / Mundi Maps。
  [原作者发布页](https://www.mccreations.net/en-US/maps/arena_of_darkness)
  → [作者公开文件记录](https://api2.mccreations.net/creations/maps/arena_of_darkness)
  → [作者Drive包](https://drive.google.com/file/d/16RjFYzacEu_Ln7RpKEEgfKe85jEaH9BH/view?usp=sharing)。
- 固定原包192,507,154字节，SHA256
  `624c63961ac4610e42a77d9ab4552e84f6a9a3f6e925693e910aa25a2a3ef5c9`；
  实际level.dat为1.20.4/DataVersion3700。
- 新私有部分候选192,230,816字节，SHA256
  `0429bc43a220713412402c1fa344c10ad3d9035faa37672ef5cbe2e48e50ecdb`。
  文件为`~/.universal-modder/maps/arena-of-darkness/arena-1.21.1-partial-datapacks-v1.zip`。
  第二次从同一原包构建到新路径，得到相同完整ZIP哈希，不只是文件内容近似。
- Manifest为`research/map-catalog-20261023/arena-port-1/candidate-repeat-manifest.json`；
  逐文件记录原/新路径、原/新SHA256、规则、未完成项及749个保留payload身份。
  明确`compatibility.status=blocked_static`、`installable=false`；玩法三门均false。

## 全世界实际扫描

工具[tools/pve_world_audit.py](../tools/pve_world_audit.py)不解压安装，只读ZIP、
MCA分配表和有界解压的NBT。使用流式NBT扫描，不重建或写出区块；旧版解析器
只适合较小level.dat，不能把跳过数组的字典当作可序列化世界。

| 已扫描内容 | 实际数量 |
| --- | ---: |
| 全部维度及region/entities/poi下MCA | 444 |
| 已分配chunk | 90,162 |
| 独立NBT，包括结构、level、计分板和命令storage | 183 |
| 全部命令出现次数，含启用/禁用数据包及保存的结构 | 11,400 |
| 去重命令文本 | 7,832 |
| 旧物品字段风险出现 | 620 |
| 旧物品tag路径风险出现 | 123 |
| 旧Attributes等命令风险出现 | 177 |
| 旧带参数粒子命令风险出现 | 88 |

风险指标可以重叠，是定位清单，不是完整Brigadier/SNBT解析结果。没有风险匹配
也不等于命令可执行。原世界二进制还实际有7,977个Count、4,557个tag、1,684组
Attributes字段，属于需要游戏数据升级和语义核对的历史数据，不能全局替换键名。
各chunk保留多个历史DataVersion，不能用level.dat单值冒充逐chunk已升级。

137个MCA为空文件；3个实体MCA末扇区未补齐4096字节，真实payload边界与
分配不重叠检查通过，单独报告，未补写或宣称游戏必定接受。`uid.dat`为16字节
Bukkit UUID，不伪当NBT读取。审计v1在这些文件与大结构预算上失败，保留
`audit.json`；改为流式/实际payload边界后，`audit-v2.json`全扫描无解析错误。
这不抹去旧失败，也不把静态扫描通过当成世界加载通过。

## 已证实的版本差异与未做的部分

[Mojang 1.20.5说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
明确区分已保存物品的自动升级与必须改写的命令/数据定义；本轮据此保留世界
版本和原NBT，另外审计命令中的物品、tag路径、配方/图标及粒子参数。
[Mojang 1.21说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21)
列出数据目录、属性、Loot与Shader改动；仅改目录或格式数字不够。

| 实际缺口 | 当前处理 |
| --- | --- |
| 数据目录旧复数名称、函数/实体类型tag目录 | 只对三个启用嵌套包做精确目录段转换，共51项文件路径 |
| 配方result旧item键 | 仅3个已识别合成配方的结果改id，原料item保持原样 |
| 成就图标旧item键 | 24个只有item的简单图标改id；带自定义头NBT的root图标保留并明确阻塞 |
| 旧looting_enchant Loot函数 | 2处精确函数上下文改enchanted_count_increase并显式指定looting和uniform计数 |
| 启用包格式与原版成就过滤路径 | 3个包10→48，1个精确过滤路径改为单数；不是兼容验收 |
| 命令方块give/item/clear和嵌入Item/HandItems/ArmorItems等SNBT | **未改**；复杂自定义数据/药水/头颅/装备须逐语法上下文转换 |
| data命令旧.tag路径及计分板/物品触发机制 | **未改**；不可简单替换成custom_data，否则会丢失受管组件与原Boss逻辑 |
| summon/merge中的Attributes、旧效果与投射物字段 | **未改**；需要区分真实实体数据与字符串里的生成模板 |
| dust等粒子参数 | v1未改；后续v2已完成81处dust，详见末尾独立验收边界，其他粒子仍阻塞 |
| 禁用的Armor Statues/Time/NoCrafting包、Bukkit占位元数据 | 原字节保留；没有扩大启用范围或杜撰Bukkit硬依赖 |

## 资源包实际阻塞

内嵌资源包仍为format22，131,919,310字节，SHA256
`eca96a4a546f1685a3dcce68b1ed7904074a5c59615b0ecfe684c4e07bb7980a`。
287个实际文件、22个模型、0个字体JSON；两个自定义Shader实际有接口差异：

- 作者`fog.glsl`的fog_distance接受mat4、vec3、int；目标1.21.1原版调用与
  定义接受vec3、int。旧include会覆盖目标include，不能直接提高format后使用。
- 作者`position.fsh`读取position输入、GameTime；目标`position.vsh`只输出
  vertexDistance，目标JSON也没有GameTime声明。这是需处理的链接/参数缺口。

比对对象为本机Mojang1.21.1原JAR，SHA1
`30c73b1c5da787909b2f73340419fdf13b9def88`与安装版本元数据相符。
`resource-shader-audit.json`保存真实差异；没有把Shader改动合进本轮候选，
也没有编译或声称表现正确。之后要保留作者无雾/波动意图，并单独验证目标接口、
Sodium环境和实际画面；不能删掉所有自定义表现后声称完整移植。

## 转换器与验证边界

[tools/pve_arena_port.py](../tools/pve_arena_port.py)固定原包SHA256及DataVersion，
只接受私有maps根下的新ZIP路径，拒绝已有目标、大小写别名、路径碰撞、异常
格式、安装器/符号链接和超预算嵌套包；未识别的复杂NBT保持原文并记为阻塞。
不执行任何地图命令，不改版本标记，不写现有profile，不产生“已验收”状态。

三个嵌套包之外，749个文件payload均与原包一致；包括全部MCA、实体/结构NBT、
level.dat、资源包及禁用包。外ZIP容器时间与压缩方式确定化，所以容器本身哈希
变化不代表这些世界文件被升级。读取复制文件时校验CRC，输出另做实际ZIP/NBT
预检；重复构建和逐文件比较证据见`candidate-verification.json`。

18个新fixture通过，覆盖有界解压、Java修饰UTF8、NBT重复键/负数组、大结构流式扫描、MCA
重叠/外部块/截断、末尾padding、真实命令提取、上下文JSON、目录碰撞、私有
路径/原哈希/禁止覆盖、原世界payload保留及可重复构建。原14项清单预检仍应
一起执行。这是工具验证，不能勾选实际Boss战。

```powershell
.venv/Scripts/python.exe -m unittest discover -s tools -p test_pve_world_port.py -v
.venv/Scripts/python.exe -m unittest discover -s tools -p test_pve_map_catalog.py -v
```

后续先按私有命令索引修物品生成/检测与Boss重置，再修资源Shader与原入口；
有实际目标解析证据后才建立新的隔离可运行候选。由唯一游戏驱动者加载、走
原初始化、受伤/失败/获胜和重打验收。当前正式五图仍0张通过，不能把这个
partial ZIP交给启动器显示“开始挑战”。

## 2026-10-23 17:09 后继v2：实际转换81处dust命令

在v1之外生成新私有`arena-1.21.1-partial-dust-v2.zip`，191,457,363字节，SHA256
`2ebb56d9140253c2c26cfd7d4b30de6ea568fc53002bcead382e29aa40e7edf1`。
从同一v1重复构建第二个ZIP，完整字节哈希一致；v1、原作者包均保持原哈希。
同样为`blocked_static / installable=false`，不是世界加载或Boss实战通过。

新增[tools/pve_arena_particles.py](../tools/pve_arena_particles.py)：按已核对的
[Mojang粒子语法说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
做窄转换，仅处理原生命令方块/命令矿车owner内的Command字符串。tokenizer
将selector/SNBT/JSON保持不透明；只支持可确定的execute子句，不盲找`run`，
不会把名为run/particle的计分板假玩家误当子命令，也不会转换聊天中的文字。
保留RGB/scale数字原拼写与精度、命令前缀、坐标、数量、速度、force/normal
和接收者；颜色/scale超出目标范围或未知语法保持原文并报告。

本轮实际转换81处dust，位于17个MCA中的27个chunk，以及2个用于Boss重置
的结构NBT。工具也有dust_color_transition规则和fixture，**原包没有实际该类
样本，不冒称实际转换过**。另7处旧粒子风险是block_marker，仍未处理。
非粒子旧item/tag/Attributes风险数量保持不变，不表示这些命令已适配。

与重建整个NBT不同，本轮只按已验证字符串span替换长度与内容，其他字节逐段
比较相同。改动MCA只重算分配表/压缩，保留时间戳、所有未改chunk原始NBT和
每个字段类型；被改chunk剔除Command值后的二进制仍完全一致。全部非目标
Command原文也逐项比对相同。因此Boss阶段、Invulnerable、伤害、计分等没有
被本轮转换器更改；不是靠游戏内手动改分或杀怪绕过机制。

独立复核：新ZIP中只有上述19个文件payload变化，另733个完全相同；level.dat、
scoreboard、所有启用/禁用数据包及resources.zip原字节保留，未改DataVersion。
整个ZIP CRC通过；原完整审计与实测delta对照证明81个已知旧dust出现全部覆盖，
旧粒子风险88→7。此为完整父审计上的已验证增量，**不是新客户端命令解析器
已通过**。17个新fixtures、先前18个转换/审计fixtures和14个清单fixtures通过。

证据：`research/map-catalog-20261023/arena-port-2/`中的两个candidate manifest、
`candidate-verification.json`和测试输出。首次delta索引因旧审计会去掉首尾空白/
前导斜杠而出现KeyError，失败证据保留；修正关联key后复核通过，实际NBT补丁
与原/新字符串未因此改变。源码/文档/清单已事先备份，未操作任何游戏或UI。

剩余大项仍为物品组件生成/检测、属性/效果、其他粒子、root成就图标和资源
Shader接口；之后才轮到目标解析、隔离世界原入口与完整Boss生命周期实测。
