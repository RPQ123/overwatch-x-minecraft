# Hanzo Dragonstrike：原版网格接入候选，完整原版还原尚未验收

## 2026-10-25 Codex 离线交接

本轮没有启动游戏，没有构建/部署 JAR，没有改 `WorldFrameExporter` 或 `JunkratRenderer`。
新增 `HanzoDragonRenderer`，修改 `NativeHanzoSkillRuntime` 的龙部分，以及网格加载器必要的长模型/效果绘制支持。
下面是离线档案与编译证据，**不是实际合成像素、原版伤害或用户游玩验收**。

### 部件与 GUID

所有读取使用 `ow_asset_chain.Archive` 的本机研究 EXE/reader SHA256 守卫和清单 CKey/bytes 校验。
双龙资源由原英雄 `0141` 的图 `0101` 引用 `0580000000000132`；该图有52个节点。
不要把蓝/红配色资源直接当成两条不同形状的龙；两种配色都引用同一个完整模型。

| 用途 | 实体/效果 GUID | 模型/材质/贴图 GUID | 结论 |
|---|---|---|---|
| 引导箭 | `040000000000034f` | 模型 `0d00000000000b8d`，Look `0980000000000c10`，颜色 `0c0000000000102e` | LOD0 2304顶点/2938三角形/5子网格 |
| 蓝色完整龙 | `040000000000033b`、`0400000000000237` | 模型 `0d00000000000ee9`，Look `09800000000010e8`，材质 `0e000000000007a5`，颜色 `0c00000000001bc6` | 0132:49/31；3064顶点/4396三角形；龙头、龙身、尾一体，未发现独立头/身模型 |
| 红色完整龙 | `040000000000033c`、`0400000000000239` | 同一 `0d00000000000ee9`，Look `0980000000001188`，材质 `0e00000000000810`，颜色 `0c00000000001d08` | 0132:48/32；配色替代；阵营条件未执行验证 |
| 引导箭拖尾 | `034f → 0400000000000354 → 0300000000000497` | 模型 `0d0000000000075d` / 材质 `0e0000008e2eb8c3`、`0e000000cfa17e2d` | 每组18顶点/16三角形，通用拖尾体，不能冒充龙 |
| 拖尾片 | 同上0497 | 模型 `0d000000000007f5` / 材质 `0e0000002a74326b`、`0e0000002391004a` | 每组16顶点/8三角形 |
| 拖尾体 | 同上0497 | 模型 `0d0000000000099f` / 材质 `0e000000c41c6344` | 50顶点/48三角形 |

`0497` 是5个发射器、无普通 particle-renderer 表、5个 trail-renderer 的布局；本轮补了这种表的有界解析和回归测试。
完整龙原始 XYZ 包围盒为 `[-1.75952,-2.64384,-37.60709]..[1.75952,2.28127,3.05326]`，长度40.66035m。
离线转换把模型底部/中心移到原点，Z约±20.33；加载器旧的绝对坐标4m上限会拒绝它，现扩大到64m，保留SHA/有限值检查。

蓝/红颜色图是实际 BC1 sRGB，均值RGB约 `[90.2,143.6,175.6]` / `[174.1,101.0,91.4]`；没有凭印象给灰色模型染蓝。
每种龙材质还保留 `1ce9` 的 BC1线性图、`1bc7` 的 BC5、`0754/1bf7/1bf8/1d26` 的BC4，以及refType=2变量 `0c000000581a3da4`。
这不是可直接当漫反射的七张图。材质内还存在 `.5/1/5/20/3` 等重复float4，未认证其参数语义，不能拿它们虚构RGB。
主色用原版颜色图；自发光透明层近似原效果，原版滚动遮罩、UV动画、混合、骨骼蒙皮动画尚未播放。
拖尾材质没有唯一可绑定颜色图，包保留其采样器/变量证据；渲染器暂不绘制灰色拖尾网格，保留每条龙每tick一个粒子作MC适配。

### Claude 执行的资产命令

提取/核对（本轮已运行；只写忽略的缓存）：
```powershell
.venv/Scripts/python.exe tools/inspect_hanzo_dragon_assets.py --validate-packs
```
安装私有网格包（Claude执行，必须在开启MC之前；8项含蓝/红龙、引导箭和5种拖尾绑定）：
```powershell
.venv/Scripts/python.exe tools/build_mesh_pack.py --batch tools/hanzo-dragon-pack-jobs.json
```
原始/PNG/完整mesh/验证包都在被忽略的 `research/asset-cache/`，不进JAR或提交。
本轮校验包位于 `hanzo-dragon-pack-validation/`；逐数组/分组/文件SHA/PNG回读结果在 `hanzo-dragon-audit/evidence.json`。

### 数值逐项对照

| 项目 | 原版定义证据 | 原实现 → 当前 |
|---|---|---|
| 引导箭速度/距离/寿命 | b9:76 的 `ac2f916a/308e35d5/5257be73`，20m/s、10m、5s；历史真实工厂一致 | 20/10 → 不变，补100tick寿命上限 |
| 引导箭重力 | 既有 typed node76 校准为0 | 无重力不变 |
| 龙目标查询半径 | 0132:25 `m_out_Var=1a6`、`m_value=4`；七个TrackTargets:1/7/10/20/36/38/44的 `m_radius` CRC32=`71ef3ca4` 都绑定1a6 | `DRAGON_RADIUS` **2 → 4m** |
| 龙速度 | 0132存在20/12等赋值，但运动表达式/变量语义尚未完整认证 | 20m/s保留，**MC 适配** |
| 射程/寿命 | 原版含Wait/ChaseVar图和多段查询体；尚未还原完整出口/距离语义 | 60m，即释放后约3s保留，**MC 适配** |
| 每秒伤害/周期 | 未认证原版最终ModifyHealth与脉冲聚合；不能把任意赋值当DPS | 200 OW HP/s、每10tick一次，HP_SCALE=.1，**MC 适配** |
| 穿墙 | 本轮未验证原版服务器遮挡/追踪过滤 | 不做方块阻挡，**MC 适配** |
| 缠绕半径/频率 | 原版蒙皮/动画轨道未解释 | 1.2m、.6rad/tick=12rad/s，约1.91圈/s；双龙相差π，**MC 适配** |

原版0132:3/4/29还分别给变量 `d7/2a9/1df` 赋20/12/5，已记录原始绑定；未把这些数硬解释成速度/寿命/角频率。
4m是原版查询半径，不证明MC单球伤害体等价于原版七段目标查询；现有MC目标中心检测还含`.5m`容差。
引导箭impact仍是contextual `0d80000000000635`（历史varbag曾为125），本轮没有添加引导箭直接伤害。

### 渲染接线与实测

`NativeHanzoSkillRuntime.dragonViews` 是不可变record列表的volatile快照，含owner/world/source/model、前后位置、方向、age、travelled、released、采样纳秒。
Q引导箭已从旧 `arrowViews` 移至专属龙视图，防止旧Junkrat/箭渲染路径重复绘制；未改散射箭代码。
新渲染器检查当前owner/world/source/model、原版输入状态、150ms host帧新鲜度和250ms快照时限。
蓝龙包绘两次，使用服务器方向、插值位置、相差π的轴向正弦形变及逐段生长裁切；形变法线用逆转置修正。
这是原版几何/颜色图配MC动画，不能称为原版完整动画、音效或全部数值还原。
末影龙吼声仍保留为显式MC适配。正确声效需Claude另行提取/绑定。

由Claude在WorldFrameExporter添加：
```java
HanzoDragonRenderer.register();
diagnostic.addProperty("hanzoDragonRendererFrames",HanzoDragonRenderer.frames);
diagnostic.addProperty("hanzoDragonRendererErrors",HanzoDragonRenderer.errors);
diagnostic.addProperty("hanzoDragonRendererError",HanzoDragonRenderer.error);
diagnostic.addProperty("hanzoDragonDraws",HanzoDragonRenderer.dragonDraws);
diagnostic.addProperty("hanzoDragonArrowFrames",HanzoDragonRenderer.arrowFrames);
```
frames是有绘制提交的世界帧数，dragonDraws是单龙提交数，arrowFrames是引导箭提交数；errors累计缺包/绘制异常，error为最后错误。
实测至少确认：缺包拒绝、龙头朝向/生长/两龙缠绕、原版蓝色而非灰色、实际合成像素、伤害/穿墙/范围、换世界/英雄/会话后无旧视图。
新伤害半径未实测；不能沿用旧半径2的通过结果。完整原版还原仍有上表所列开放项。

---

## 历史：2026-10-24 有界校准

2026-10-24 actual calibration:
`research/sprint-20261024/hanzo-dragon-calibration1/result.json`.
Original Hanzo selection, explicit lab-only Q grant and actual Q input captured
graphb9/node76's original factory. The helper restored its diagnostic switch,
cleaned its objects and recorded video exit0. Its passed flag is calibration
only; `mcDragonAcceptance=false` explicitly forbids treating this as a skill pass.

Observed original resource040000000000034f: speed20m/s, lifetime5s, range10m,
status8/type1, result0(no observable original projectile). Actual nativeTick1270
and owner2147487778 are historical evidence only. Typed original node76 config
has gravity0 and contextual impact damage0d80000000000635. Diagnostic damage0
was an unbound default, not proof that the original starting arrow deals zero.

No following twin-dragon spawn, trajectory, server damage volume or lifecycle
has been authenticated. No MC Dragon event admission, damage or model was added.
This remains temporarily deferred rather than guessing a key-driven damage ray.
The current accepted ordinary arrow, Sonic and climb routes stay unchanged.
