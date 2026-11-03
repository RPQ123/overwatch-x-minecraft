# models 交接 · 2026-10-26

本线程只改下列 Renderer、tools 打包辅助及本交接。没有开游戏、构建 JAR、部署、改 profile/save、加载 native callback 或提交代码。按并行约定仅运行了离线检查和 `compileClientJava`。现有其他线程的修改保留。

**源码直接替换已完成；全英雄可见物盘点已完成；需要共享数据的效果仍待集成，不能称为全部可见物已替换或实机通过。** 表中“待接线”均不是 ACCEPTED-live。

## 改动与统一命令

- 改：`BastionTankRenderer.java`、`BioticFieldRenderer.java`、`HelixRocketRenderer.java`、`MccreeEffectsRenderer.java`、`PharahRocketRenderer.java`、`PharahBarrageRenderer.java`、`PharahConcussiveRenderer.java`。
- 新：`OriginalWorldRenderer.java`，供上述 Renderer 调用；另有一个受作用域保护的可选 `models` 快照渲染回调。
- 新：`tools/models_20261026_assets.py`、`tools/models_20261026_jobs.py`、`tools/models_20261026_pack.py`、`tools/models-20261026-pack-jobs.json`。
- 未改：`*Client.java`、`*Server.java`、`Native*Runtime.java`、`OriginalMeshPack.java`、`Hanzo*`、`Junkrat*`、共享注册/场景/HTTP 文件。

Claude 在游戏正常关闭后只需执行这 **一条素材安装命令**（本线程未执行）：

```powershell
.venv/Scripts/python.exe tools/models_20261026_pack.py --batch tools/models-20261026-pack-jobs.json
```

61 个任务包含本轮新资源、原有 Mercy/D.Va/Roadhog/Lucio/Symmetra 包，以及 colors 线程的非 Hanzo 禅雅塔/查莉雅包。后者保留 `ow_material_params` 的已审计配方；不把未知 runtime 变量当归档贴图。Hanzo/Junkrat 包仍由其原交接负责。

该辅助先调用现有 `build_mesh_pack.build`，再按 JSON 中**明确指定**的材质真实 `refType=3` 采样器生成 MC 配方；核对原归档 SHA256/CKey、重新解码像素，并更新 provenance/文件哈希。单包完成后才替换旧包，失败保留旧包；没有替换 source 数组。未解材质不再回退到 MC 铁块。61 包中仅保留 colors 已明确禁用的两组禅雅塔折射球 `skip`；彩色 core/glow 同批提供。

本机缺 chain 时，用辅助中的 `--extract GUID...`（内部调用 `ow_asset_chain.collect`，预载 21 英雄包）补齐；所有实际选中 GUID、model/material、采样器、原始 bounds 均在上述 JSON。`--index` 可重做 graph 审计，`--hero-entities Reaper` 可重做灵魂球的有界实体排查。

## 原版资源与盘点表

表内 `04:xxxx`、`03:xxxx`、`0d:xxxx`、`0c:xxxx` 分别完整展开为 `040000000000xxxx`、`030000000000xxxx`、`0d0000000000xxxx`、`0c0000000000xxxx`。**资源不存在、未找到可解析网格、未认证用途、缺动态材质是四种不同情况。** 粒子模板也是原版网格；不能把“无独立弹体”写成“无网格”。原版手/HUD/第一人称武器仍由 OW 绘制，不重复移植。

| 英雄 | 可见物 | 本轮前现状 | 原版 GUID / 网格 | 结果 |
|---|---|---|---|---|
| 源氏 | 手里剑 | MC 没有独立弹体渲染，不是已存在的占位物 | `04:07ca`；chain 有网格 | 索引保留；不凭 native 飞行记录新增第二弹道 |
| 源氏 | 刀挥、火花、命中尘 | `GenjiSwordParticles` / `GenjiCombatParticles` 的 SWEEP/SPARK/CLOUD | `03:0305` 为 01dc:3 风效；`03:1712` 为 03a3:28，非已认证刀痕 | 打好 `genji-dash-wind`；刀痕/命中映射未认证，保留显式 MC 适配，不冒用风效 |
| 麦克雷 | 闪光弹弹体 | 自绘圆柱/金属环/肋条 | `04:037d → 0d:11d8`，颜色 `0c:23a9` | **已替换**，保留飞行寿命/旋转呈现与原门控 |
| 麦克雷 | 闪光弹爆光/火花 | FLASH/POOF/SPARK/Dust | `04:037d` 同链 `0801/520140d2` | `mccree-flash-impact` 已打包；原 runtime 未公开有 scope 的爆点，待发布真实命中快照 |
| 麦克雷 | 午时圆圈/骷髅 | 自绘 UI 几何 | `03:03ae` 空效果；`03:0610` 有模板但未认证为骷髅 glyph | 保留原 MC UI；没有用任意粒子贴图冒充锁定图标 |
| 法老之鹰 | 主炮火箭 | 私有旧导出弹体 + 自绘尾焰片 | `04:0033 → 0d:084c` | **改用 OriginalMeshPack**，原 +Z 轴；保留原收敛/FOV/遮墙检查 |
| 法老之鹰 | 主炮拖尾/亮光 | 自绘交叉尾焰/光片 | `04:0033` 的 `07f5/d599b3d4`、`0801/4f47ebdc` | **已替换为原版模板/采样器**；MC 尺寸/时序 |
| 法老之鹰 | 主炮爆炸 | 自绘 sprite/atlas 播放 | `04:0033` 的 `0801/1a1a7d5f` | **已替换**，沿用真实 `PharahRocketImpacts` 爆点 |
| 法老之鹰 | 弹幕弹体 | `mc-barrage-mini-v1` 自制弹体 | `04:0052 → 0d:084c`，真实直接模型引用 | **已替换**，不再加载自制迷你弹；Wave 路径/近处隐藏保留 |
| 法老之鹰 | 弹幕拖尾/爆光 | 自绘曲线 ribbon/sprite | `04:0052` 的 `07f5/6773ddf6`、`0801/811b6b59` | **已替换**；保留同一 Wave 采样和真实 impact cue |
| 法老之鹰 | 震荡弹弹体/压力壳 | 两层自绘球 | `04:010f → 0d:084c`；原折射 `085b` 只有 builtin/变量 | **弹体/尾迹改原版**；爆点画同链原版模板，未伪造折射球面 |
| 死神 | 灵魂球及拾取 SOUL 粒子 | 自绘青色晶体 + MC SOUL | 未认证 GUID；见下方有界反证 | **仍为 MC 占位**。没有把传送预览 `04:019d` 或温斯顿盾 `04:01c3` 冒认成灵魂球 |
| 死神 | 暗影步出发/落点烟与预览圈 | LARGE_SMOKE/粒子圈 | `03:028b`、`03:028c`；00f2:35/36 | 原模板已打 `reaper-shadow-start/end`；`models` 端点待接线 |
| 死神 | 幽灵形态烟 | SMOKE | `03:004a`；0020:10 | `reaper-wraith` 已打；状态/位置待接线；`03:0131` 自身无网格 |
| 死神 | 死亡绽放区域/命中粒子 | ASH/CRIT | `03:00ac`；0044:42 | `reaper-blossom` 已打；只消费已存在 Q runtime，不能新造 Q 触发 |
| 士兵76 | 螺旋飞弹三股弹体/尾迹 | 自绘银弹/ribbon | `04:072c → 0d:1883` 及同链原粒子片 | **已替换**；源包本身3枚，各186顶点、三角形不跨组；每 shot 只绘制整包一次，将三组映射到既有三股 MC 轨迹，不会复制成9枚；这不是原 emitter |
| 士兵76 | 生物力场装置 | 自绘金属饼 | `04:072d` / `04:068a → 0d:1acf` | **已替换**；使用 0258:8 的部署模型，底部对地 |
| 士兵76 | 治疗范围环/脉冲 | 自绘圆环 | `03:0b06`；0258:7 的原粒子片 | **改为 24 个原版模板采样**；5m 圆周与时序明确为 MC 适配 |
| 士兵76 | 治疗命中反馈 | HAPPY_VILLAGER | 同上只认证部署效果，未认证治疗目标 emitter | 仍为 MC 反馈；不把范围模板冒作原版治疗命中 |
| 猎空 | 脉冲炸弹/插墙体 | 已是经哈希核对的原版独立 pack | `04:0045 → 0d:0b2c` | 保留 `PulseBombRenderer` 原实现；不是占位物 |
| 猎空 | 脉冲爆炸/电火花 | EXPLOSION_EMITTER/SPARK | `04:0045` 旧独立原包有实体；爆炸 emitter 未由当前 Renderer 暴露 | 仍待命中快照/效果绑定，不按炸弹模型伪造爆炸 |
| 猎空 | 闪现/回溯轨迹 | REVERSE_PORTAL/SPARK/END_ROD | `03:00bb` 有模板；`03:0079/007a/007f` 各自空效果 | `tracer-blink` 已打；不能由空句柄证明全技能无网格；回溯逐点快照待接线 |
| 堡垒 | 坦克炮弹/拖尾 | 自绘八棱炮弹 + 橙线 | `04:03ce`：`0801/36545914`、`07f5/cdf08941` | **已替换**。该弹是 effect 模板，不是实体金属壳；原时效/遮墙门控保留 |
| 半藏 | 飞行/散射/插墙箭、音波脉冲/双龙 | 原版模型 + MC 呈现适配 | `04:01a4/020c/0149/034f/033b/033c` | **明确不在本线程编辑范围**；详见 hanzo/colors 交接 |
| 狂鼠 | 榴弹/地雷/夹/轮胎/死亡炸弹 | 多数原版模型，爆炸/烟为 MC 粒子 | `04:11a9` 等；既有 projectile audit | **明确不在本线程编辑范围**；builders 负责爆炸/死亡逻辑，不修改其 Renderer |
| 美 | 冰柱/插地冰墙 | 原版冰柱 + 不可见碰撞 BARRIER | `04:0932 → 0d:2a64` | 保留既有 JunkratRenderer 路径，2 倍大小为原有 MC 适配；材质仍不完整 |
| 美 | 冰冻喷雾/冻住反馈 | SNOWFLAKE | `03:0b89`；05e7:13 | `mei-freeze-snow` 已打；目标冻结层/喷雾 emitter 尚未认证，不把单片当完整冰壳 |
| 美 | 暴雪无人机/冰雪区域 | 原版无人机 + SNOWFLAKE/WHITE_ASH | `04:0946`、`03:15ce` 原冰片；`03:0f06/16be` 自身空 | 无人机保留；`mei-blizzard-shard` 已打，区域快照待接线 |
| 托比昂 | 炮台 1/2/3 级 | 原版 0092e 子网格/等级呈现 | `04:0143 → 0d:092e` | 保留；不重打未经等级筛选的全模型覆盖已安装等级包 |
| 托比昂 | 护甲包 | 原版模型 | `04:02a1 → 0d:0c40`，`0c:1500` | 保留，原 audit 已核对；不改 JunkratRenderer |
| 托比昂 | 废料/锤击/Core/炮口烟 | builders 的 MC 适配/SMOKE；部分尚无世界视觉 | `03:0225` 空；`03:03a9` 有模型但无唯一已绑定颜色 | 原版索引保留，未认证废料/锤击物体用途，不冒用武器/升级件；待 builders/状态端点 |
| 黑百合 | 毒雷飞行/插墙体 | 已是原版独立 pack | `04:00af → 0d:06f2` | 保留 VenomMineRenderer 及面法线姿态；不是占位物 |
| 黑百合 | 毒气/附着毒雾 | 紫色 Dust | `03:00f9`；0057:19/16 | `widow-venom-gas` 已打；真实触发/受毒目标列表待接线 |
| 黑百合 | 抓钩/锚点/绳 | 深色 Dust 绳，钩未显示 | `04:00d3 → 0d:0711`；`03:0291` 片；`04:00d9/00da/00db` 无网格 | 原钩/flash 已打；**没有认证原版绳索网格/连续 UV**，绳保留 MC 适配，见开放项 |
| D.Va | 驾驶员手枪弹 | 原版片，但旧普通材质/姿态 | `04:1000` 的 `0801/6ccc2cd2` | 同名包改原版加色采样器；客户端 billboard/居中需下面共享替换 |
| D.Va | 机甲矩阵/自爆/召唤机甲 | 当前没有已实现的 MC 世界可见体 | 026a/0276/02cc 索引有原版候选 | 不借资产存在启动未认证技能；本轮不新增伪造机甲 |
| 莱因哈特 | 屏障 | 不可见 BARRIER 碰撞，没有 MC 可见盾面 | `04:011a → 0d:0a3c`，0095:10/58 | `reinhardt-barrier` 已打；原原子/镜面动态输入不执行；盾位置/法线快照待接线 |
| 莱因哈特 | 烈焰击 | 原先技能未启用；原 projectile audit 已找网格 | `04:01ea → 0d:0c1f` | 保留证据，不由模型线程启用 E 或新增伤害；oldgaps 需先提供已认证 view |
| 莱因哈特 | 裂地猛击/冲锋反馈 | 尚无独立 MC 可见物 | `03:0275/0290/02cf` 等 graph 候选 | 非已有占位，未按候选效果假造提交 |
| 路霸 | 左键碎铁弹 | 原版拖尾片/旧材质 | `04:029a → 0d:07f5` | 同名包保留原模板/贴图并加色；不能称有独立碎铁实体 |
| 路霸 | 右键碎铁球 | 原版球网格/旧材质 | `04:0295 → 0d:14c0` | 同名包更新材质，原碰撞与飞行不改 |
| 路霸 | 鸡飞狗跳弹片 | 原版片曾因无 RGB 变灰块 | `04:0405 → 0d:0801`，材质 `2e4a449f`，BC4 `0510` | 用**该材质真实强度图**加色白光；动态原色未认证，不猜黄色 |
| 路霸 | 钩与链 | runtime 有钩位置但没有可见钩/链 | `04:03f7 → 0d:092a`；`04:0463` 无模型；`03:08b1` 是片/火花模板 | 原钩已打，端点待接线；**尚无认证连续链网格**，不把火花说成链条 |
| 温斯顿 | 电弧 | 伤害已实现，MC 无独立可见电弧 | `03:0840 → 0d:0e71`，00fe:125/127/143 | `winston-tesla` 已打；需要每次真实 beam 调用的实际端点，不从 LMB 推断 |
| 温斯顿 | 屏障发生器/圆顶 | 本代码基线没有 MC 屏障 runtime/可见圆顶 | `04:01c2 → 0d:0c03`；`04:01c3 → 0d:0d02`；00fa:2/22 | 两原包已备；**有模型不等于已接技能**。等待已认证的部署/生命周期 view |
| 查莉雅 | 右键榴弹/引力弹 | 原版效果网格；颜色由 colors 线程修复 | `04:03db/08ce → 0d:11c3/0dbf` | colors 非 Hanzo 任务并入本批；不重复手写紫色 tint |
| 查莉雅 | 激光束 | END_ROD 串 | `03:0585` 的 `07f5/023170db`；0241:36 | `zarya-beam` 已打；每 tick 实际命中端点未公开，待快照 |
| 查莉雅 | 自身泡泡 | ENCHANT / 临时吸收 HP | `04:03da → 0d:10d7`；0244:9/025c:32 | `zarya-barrier` 已打，真实 `234f` 表面；自身 shieldOwner 快照待接线；不启用 E 投射盾 |
| 查莉雅 | 引力区域/爆炸 | PORTAL/EXPLOSION | `04:08ce` / 已有 graviton 彩色材质 | 包保留；已有 MC field 的半径/寿命仍是 MC 规则，服务器粒子未擅删 |
| 卢西奥 | 左键音波弹 | END_ROD + 旧结论“无 LOD0” | `04:05ff/0600 → 0d:19f2/19b6` | **纠正旧结论**；`lucio-sonic/glow` 已打，已有 Client 可用；姿态共享替换见下 |
| 卢西奥 | 音障表面/冲击光 | 只有吸收 HP，无世界表面 | `03:11bf → 0d:2345`；073a:7 | `lucio-sound-barrier` 已打；只随实际 barrier lease，快照待接线 |
| 卢西奥 | 歌曲/音爆/增幅光环 | UNKNOWN 歌曲或无可见世界物 | `03:0a46` 自身空；`03:1286` 另有原模板 | 不把 0a46 空等同整套音障纯粒子，不用音障模板伪造歌曲状态 |
| 天使 | 手枪弹 | 原版粒子片，旧代码未居中/billboard | `04:0158 → 0d:0801` / `d6b19e91` | 同名包加色；共享调用需换 helper；无独立金属弹体 |
| 天使 | 治疗/增伤光束及目标光 | MC 目标/治疗已实现，但世界无连续光束 | `03:01ed → 0d:07f5`；`03:0198` 的原彩色片；006b:37/34 | `mercy-heal-beam/target-glow` 已打；beam 只有 BC4 `1344`，**保持白色，不猜金/蓝原色**；待真实 target 快照 |
| 天使 | 复活/守护天使/被动外部特效 | 复活提交缺失，其他未有对应世界可见体 | 006e/0071/0079 原版索引 | 未由搜索/资产存在触发复活；不新增无授权 emitter |
| 秩序之光 | 炮台/传送器与插墙体 | 原版网格 | `04:0250 → 0d:0c02`、`04:0241 → 0d:0c16` | 任务并入同批；保留真实布局/碰撞 |
| 秩序之光 | 能量球 | END_ROD，Client 跳过 `symmetra-orb` | `04:022e` 的 `0801/a6da5c50` | **纠正无 LOD0 旧结论**，已打 `symmetra-orb`；Client 删除 skip 并调用下方 helper 后可显示 |
| 秩序之光 | 主束/炮台束 | 原版模板但旧 Client 沿 +Z 拉伸，模型实际沿 +Y | `03:02e7 → 0d:07f5` / `f90a566c` | 同批保留原材质；共享 helper 调用纠正轴/居中，未改伤害 |
| 秩序之光 | 友方护盾 | 原版折射球壳被画成灰块 | `03:0401`：`0dbf/25193e00` 无静态纹理；同 effect `0801/82141096` 有 `1fee` | `symmetra-shield` 改为**同效果原彩色层**；球壳折射未解；Client 需 billboard，不能仍当实体球 |
| 禅雅塔 | 主/副射击球体 | 原版折射灰球 | `04:0236/0261`，`0cae/d8edbb06` + `0801/5443ff5c,b66cb8c5` | colors 的 core/glow 包并入；按 colors 交接接两层，不启用被 skip 的两折射壳 |
| 禅雅塔 | 谐/乱球与圣 | server buff/状态，缺或未认证外部世界层 | `04:0242/0243`、`03:0375/033d/039d` graph 候选 | 本轮未把搜索/Aura 或资源候选升级成原版可见事件；待对应线程提供目标/生命周期 |

## 找不到/不能认证时的具体证据

私有证据统一在忽略目录 `research/asset-cache/models-20261026/`，不提交素材或提取数据。

- `graph-index.json`：21 英雄 **244 个 graph，901 处原始 0300/0400 候选引用**；含偏移、typed config、直接 owning node、SHA256。901 不是 901 个可见物；没有直接 owner 或非资源 config 的候选不能直接命名用途。
- `reaper-entities.json`：Reaper 自身包 18 个规范实体，11 处直接模型引用；主体/武器/通用冰壳等可以按 bounds 排除为灵魂球。Reaper graph `0045` 的 `1320` 经反向 typed pointer 验证归属 Volley1（`0044` 中是 Volley48），不是灵魂生成；其中 raw 6840 的 `01c3` 归属 `c1694221`，不能作为灵魂球实体引用。没有认证 2015 本地客户端的 soul prefab；**这不证明全归档没有灵魂球**。保留晶体占位如实标记。
- 每个实际查询 GUID 的 `research/asset-cache/<GUID>/chain.json` 都由当前支持 0300 和多包记录的 `collect` 重新生成。`03:0079/007a/007f/0a46/020e/020f/0210/058d/050e/01a1/0f06/16be/0225` 等是完整读到的空句柄（1 资源、0 meshExports），不是全技能无网格的证明；有色相邻 effect 另行列出。
- 路霸 `04:0463` 1 资源/0 网格；黑百合 `04:00d9/00da/00db` 各 2 资源/0 网格；当前没有认证连续绳/链的 native 顶点/UV/拉伸规则。找到的 `08b1` 粒子/火花不冒作链。
- `04:03dc` 治疗场配置有 32 个链资源而无网格；部署物模型实际在 `04:068a` / `04:072d`。这种情况明确跟随 typed 配置定位 CosmeticEntity，不把配置无网格当整技能无模型。
- `01c3/011a/03da` 三条盾链仍 `complete=false`：有缺失 mip/纹理；**选定网格和配方实际使用的采样器均已验证**。不能把局部可画包标成完整 shader、完整链或视觉通过。

## Claude 需加的注册和调用

只补一次，放在现有客户端 render 注册行旁；不再注册已有七个 Renderer，也不加 native callback：

```java
OriginalWorldRenderer.register();
```

[已集成 integrator]

可在 `/combat` 客户端 diagnostics 区补：

```java
diagnostic.addProperty("modelsRenderFrames",OriginalWorldRenderer.frames);
diagnostic.addProperty("modelsSubmissions",OriginalWorldRenderer.submissions);
diagnostic.addProperty("modelsRejected",OriginalWorldRenderer.rejected);
diagnostic.addProperty("modelsError",OriginalWorldRenderer.error);
```

[已集成 integrator]

### 既有 Client 的局部替换（本线程未改这些文件）

保留原 scope/host/world/freshness 检查，仅替换其矩阵 push/draw/pop。本 helper 自动按真实 bounds 居中；下面直径是 **MC 呈现值**。

```java
// MercyClient，原 projectiles 循环内
OriginalWorldRenderer.mesh(ctx,"mercy-pistol",v.at(),null,true,.12f,.12f,.12f,1);

// DVaClient，原 views 循环内
OriginalWorldRenderer.mesh(ctx,"dva-pistol",v.at(),null,true,.12f,.12f,.12f,1);

// LucioClient，原 views 循环内；19f2 是原模板，非1m实体弹
OriginalWorldRenderer.mesh(ctx,"lucio-sonic",v.at(),null,true,.28f,.28f,.28f,1);
OriginalWorldRenderer.mesh(ctx,"lucio-sonic-glow",v.at(),null,true,.28f,.28f,.28f,1);
```

[已集成 integrator]

`SymmetraClient` 在原 world/age 检查后、原 skip/选包/矩阵分支前加下列代码；删除原 `symmetra-orb` 的 skip。其它炮台/传送器原分支保留：

```java
if(v.mesh().equals("symmetra-orb")){
    OriginalWorldRenderer.mesh(ctx,"symmetra-orb",v.at(),null,true,.35f,.35f,.35f,1);
    continue;
}
if(v.mesh().equals("symmetra-beam")){
    if(OriginalWorldRenderer.beam(ctx,"symmetra-beam",v.at(),
        v.at().add(v.direction().normalize().multiply(v.scale())),.08f,1))
        SymmetraServer.INSTANCE.beamMeshFrames++;
    continue;
}
if(v.mesh().equals("symmetra-shield")){
    if(OriginalWorldRenderer.mesh(ctx,"symmetra-shield",v.at(),null,true,.8f,.8f,.8f,.5f))
        SymmetraServer.INSTANCE.shieldMeshFrames++;
    continue;
}
```

[已集成 integrator]

原 `07f5` 模板纵轴为 **+Y**，不能沿旧 +Z 拉伸。`beam()` 自动按实测 bounds 归一化源宽/长并旋到实际端点。禅雅塔继续采用 colors 交接的两层调用；此处不覆盖其实现。Roadhog 原模板也需居中；不要再用全尺寸1m片当子弹。

### 新护盾/光束/区域层的数据协议（仍待集成）

新回调只读取各 runtime 现有 JSON 中的可选 `models`，缺字段就不画；**不是用 status 布尔值猜射击/部署**。只在服务器原已认证状态生成快照。schema 如下：

```json
{"models":{"owner":"UUID","world":1,"source":1,"model":1,"wall":0,"effects":[
  {"mesh":"mercy-heal-beam","at":[0,0,0],"to":[0,0,1],"width":0.08,"alpha":0.8},
  {"mesh":"zarya-barrier","at":[0,1,0],"scale":[1,1,1],"alpha":0.22},
  {"mesh":"reinhardt-barrier","at":[0,2,0],"scale":[1,1,1],"direction":[0,0,1],"axis":"z","alpha":0.25}
]}}
```

[已集成 integrator]

数字仅展示结构，不能复制为事件数据。`owner/world/source/model` 必须来自 runtime 当前 scope；`wall` 使用该 lease/heartbeat 的实际时间，不用 UI 查询时间刷新旧数据。回调强制当前英雄、host input/flags、玩家存活、owner/world/source/model 相符、0..200ms、新鲜 chunk、≤128层、有限坐标、≤100m beam、scale/alpha 范围；失效只返回，不创建替代攻击。

为让集成可直接落地，建议 integrator 新建一个**主源集** JSON 小工具 `OriginalEffectFrames`（不依赖客户端类型），以下为完整代码；本线程没有越界创建它：

```java
package lab.owmcguest;
import com.google.gson.*;
import java.util.UUID;
import net.minecraft.util.math.Vec3d;
final class OriginalEffectFrames {
    static JsonArray vec(Vec3d p){var a=new JsonArray();a.add(p.x);a.add(p.y);a.add(p.z);return a;}
    static JsonObject frame(UUID owner,long world,long source,long model,long wall){
        var f=new JsonObject();f.addProperty("owner",owner.toString());f.addProperty("world",world);
        f.addProperty("source",source);f.addProperty("model",model);f.addProperty("wall",wall);
        f.add("effects",new JsonArray());return f;
    }
    static JsonObject body(JsonObject frame,String name,Vec3d at,Vec3d scale,float alpha,boolean billboard){
        var e=new JsonObject();e.addProperty("mesh",name);e.add("at",vec(at));e.add("scale",vec(scale));
        e.addProperty("alpha",alpha);e.addProperty("billboard",billboard);
        frame.getAsJsonArray("effects").add(e);return e;
    }
    static void beam(JsonObject frame,String name,Vec3d from,Vec3d to,float width,float alpha){
        var e=new JsonObject();e.addProperty("mesh",name);e.add("at",vec(from));e.add("to",vec(to));
        e.addProperty("width",width);e.addProperty("alpha",alpha);frame.getAsJsonArray("effects").add(e);
    }
}
```

[已集成 integrator]

下面是在既有 `publish()` 的 `json=o.toString()` 前的**实际接线候选**，只画已有状态，仍须由 integrator 编译/实测；不会创建原先被封锁的技能。

```java
// MercyServer.publish(target)：只在真实 MC 目标/运行中的 channel 上画束。
if(target!=null&&running!=null&&channel!=null&&target.getServer()!=null){
    var p=owner(target.getServer(),running);var lease=permission;
    if(p!=null&&lease!=null){
        var f=OriginalEffectFrames.frame(running.owner(),running.world(),running.source(),running.model(),lease.wall());
        OriginalEffectFrames.beam(f,"mercy-heal-beam",p.getEyePos().add(0,-.25,0),target.getBoundingBox().getCenter(),.08f,.8f);
        OriginalEffectFrames.body(f,"mercy-target-glow",target.getBoundingBox().getCenter(),new Vec3d(.35,.35,.35),.7f,true);
        o.add("models",f);
    }
}

// ZaryaServer.publish()：只画已成功授予的 self shield，不画 E 搜索候选。
if(scope!=null&&shield&&shieldOwner!=null){
    var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),heartbeat);
    OriginalEffectFrames.body(f,"zarya-barrier",shieldOwner.getBoundingBox().getCenter(),new Vec3d(1,1,1),.22f,false);
    o.add("models",f);
}

// RoadhogServer.publish()：只用现有 hook 的服务器位置；不制造链或 hook damage。
if(scope!=null&&hook!=null){
    var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),lease);
    var e=OriginalEffectFrames.body(f,"roadhog-hook",hook.at,new Vec3d(.5,.5,.5),1,false);
    e.add("direction",OriginalEffectFrames.vec(hook.direction));
    o.add("models",f);
}

// LucioServer.publish()：只在现有 Aura barrier 租约及当前 owner 目标上显示。
if(scope!=null&&barrier){
    var target=shields.stream().map(Owned::entity).filter(e->e.isAlive()&&e.getUuid().equals(scope.owner())).findFirst().orElse(null);
    if(target!=null){
        var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),lease);
        OriginalEffectFrames.body(f,"lucio-sound-barrier",target.getPos().add(0,.3,0),new Vec3d(12,1,12),.6f,false);
        o.add("models",f);
    }
}
```

[已集成 integrator]

这些样例中天使手位偏移、光束宽度、泡泡透明度、钩缩放、音障覆盖尺寸全是 **MC 呈现参数**，不是原版 emitter 曲线。Mercy 目标光层目前只有治疗侧候选，BOOST 暂可共用白色束；若需忠于原阵营/通道颜色，应先认证颜色变量，不能凭英雄印象 tint。

其余数据接线需要真实端点，不能从按键或累计 casts 反推：

| 发布位置 | 已准备的层 | 需要的数据/边界 |
|---|---|---|
| `ReinhardtServer.publish` | `reinhardt-barrier` | 从**当前已放置的 shield BlockPos 集合**计算中心/宽/高及平面法线；按原 bounds 6.7894×4.2529 归一化 scale，`axis:"z"`，wall=heartbeat；不能跟随当前视角随意转盾 [已集成 integrator] |
| `ZaryaServer` 实际 beam raycast 后 | `zarya-beam` | 当前 scope、heartbeat、真实截断后的起终点；不从 beamActive 猜未遮墙的15m线 [已集成 integrator] |
| `NativeCombatRuntime` 真实 Winston beam 调用 | `winston-tesla` | 原 accepted beam 的 Source/owner/model/world、当前真实射线端点；其 status 是新回调已订阅来源 [已集成 integrator] |
| Winston 屏障新 runtime（尚未有） | `winston-projector/barrier` | 先认证部署/消失；原圆球 mesh 为10m直径，世界底/中心需真实部署锚点；没有事件前不得画圆顶（未集成：缺认证部署/消失runtime，维持不画） |
| `NativeGrappleController.publish` | `widow-hook/grapple-flash` | 原 `scopeWorld/scopeSource/scopeModel`、当前 owner UUID、真实 `pull.anchor`、frameWall；只在 pull 存在时发布；绳网格未认证 [已集成 integrator] |
| `NativeShadowRuntime` / `NativeWraithRuntime` / `NativeReaperRuntime` 的 publish | 对应 reaper 三类包 | 当前 scope/lease 和既有出发/目的地/玩家位置；不由画面计时新造转移/伤害 [已集成 integrator] |
| `NativeRecallRuntime.publish` | `tracer-blink` 候选层 | 只用现有 recall 实际历史点；Blink 与 Recall 的原 effect 用途不同，须确认用法后接，不冒作完整回溯动画（未集成：Blink模板用于Recall未认证，不冒用） |
| `NativeBlizzardRuntime.publish` | `mei-blizzard-shard` | 当前 scope/lease、真实区域锚点/剩余期，MC 范围采样；原 shard 不等于完整暴雪 emitter [已集成 integrator] |
| `NativeVenomRuntime.publish` | `widow-venom-gas` | 实际触发 mine/仍受毒目标的 scope/位置；不用投射物年龄猜毒雾 [已集成 integrator] |
| `NativeDashRuntime.status` | `genji-dash-wind` 候选层 | 仅认证 dash 段端点；刀痕用途仍未认证 [已集成 integrator] |
| 麦克雷真实爆点 | `mccree-flash-impact` | 合入 NativeCombatRuntime 的 `models`，新回调已订阅麦克雷；不要按 .27s 到时在空中制造爆炸 [已集成 integrator] |

现有模型 Renderer 直接读取的弹道没有依赖上表快照；不应为了等待这些层而重新加占位体。服务器原 spawnParticles 本线程均未删除。集成时按**已安装素材、已接真端点**逐处去掉对应旧粒子；未连接/未认证的反馈仍保留并标 MC 适配。不要一口气删除所有粒子，把“消失”当替换成功。

## 离线验证与统一实测清单

- `tools/check_environment.py`：通过，`.venv` Python 3.13.13，研究 EXE SHA256 `f73a747b…08e9f` 与 reader 守卫通过。
- `tools/test_ow_asset_chain.py`：22 项通过；`tools/test_build_mesh_pack.py`：7 项通过。没有跑 unittest discovery 代替 HTTP contract，没有改变 HTTP/server 逻辑，本轮无需启动其 Java fixture。
- 所有包只写 `research/asset-cache/models-20261026/validation-packs`；`pack-audit.json` 核对原 positions/normals/UV 逐值相等、分组索引相等、所有 provenance 文件 SHA256、生成贴图 alpha/像素统计。61 包共 41,582 顶点 / 54,057 三角形；2 个 skip 为已知禅雅塔折射壳。
- `compileClientJava` 离线通过；最后结果与本线程源码哈希写 `checks.json`。没有运行 jar/build/部署任务。
- 没有新增实机测试脚本、run_batch 键或场景；沿用已有 pharah/barrage/helix/biotic/bastion/各英雄技能键，由 Claude 在集成后统一测。

离线复现：

```powershell
.venv/Scripts/python.exe tools/models_20261026_jobs.py
.venv/Scripts/python.exe tools/models_20261026_pack.py --batch tools/models-20261026-pack-jobs.json --out-root research/asset-cache/models-20261026/validation-packs
.venv/Scripts/python.exe tools/models_20261026_pack.py --batch tools/models-20261026-pack-jobs.json --out-root research/asset-cache/models-20261026/validation-packs --audit
```

统一实测先正常关闭/备份 profile，再统一构建/安装包。先复核已有 native 提交/弹药/命中计数不变，再测加载/绘制诊断和画面。重点：原 +Z 火箭无倒飞，螺旋/弹幕不重绘双份，治疗装置不悬空，光束在真实墙面/目标截断，换英雄/世界/源进程/租约过期清理，没有旧盾/旧束残留。`OriginalMeshPack.drawCalls` 和本轮 submissions 只证明绘制提交，**不证明合成 native 像素、命中或用户游玩验收**。

全部新 pose、billboard、宽度、源几何居中、加色/fullbright、白色强度图、静态UV0、原 HDR→MC LDR、模板采样和 fade 都是呈现适配；没有恢复完整 native emitter/shader/blend/permutation/折射/动画。需要画面时仅一张 ≤1024px 接触表或长边≤768px JPEG80，禁止打开1080p全图。

Integrator 补记：Roadhog 原模板同步居中；Mercy beam 另核 lease.scope 与 running 一致，Zarya clearOwned 清空端点，Winston 使用真实 accepted present，McCree 只在 loaded impact 后发层。四个直接 publish 样例及其余已具真实端点项均已接；MC尺寸/区域采样不冒称 native emitter。[已集成 integrator]
打包命令已合并去重：本批61项 + colors剩余10项Hanzo，清单为 tools/integration-20261026-colors-jobs.json；原两批重名10项由models配方负责，未实际安装素材。[已集成 integrator]

统一源码/命令/分批计划见 [INTEGRATION-20261026.md](INTEGRATION-20261026.md)。标记仅表示源码/计划已接入；未执行游戏、素材安装或实机采证。最终全量compileClientJava日志在 research/sprint-20261024/integration-round2-20261026/compile-final.log。
