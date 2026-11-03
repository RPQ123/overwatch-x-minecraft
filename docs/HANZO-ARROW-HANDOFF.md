# 半藏箭矢模型与呈现交接（2026-10-25）

本轮不开游戏，不构建或部署 JAR。`tools/check_environment.py` 通过，使用项目 Python 3.13。
只处理普通箭、音波箭、散射母/子箭。龙击线程在本轮同步更新了同一个运行时的龙段，已保留其改动。
没有修改 `NativeShotSimulation`、`NativeCombatRuntime`、`WorldFrameExporter`；交接前与备份 SHA256 比较一致。
本文件的数值证据是本机保存的原版 24919 声明/工厂记录及本轮重新读取的本地档案，不是本轮实机验收。

## 原版素材与打包

本轮通过 `tools/ow_asset_chain.py` 的原有 SHA256 防护重新提取以下资源；全部 chain 为 complete。

| 对象 | 实体/资源 GUID | 原版模型/材质 | 说明 |
|---|---|---|---|
| 普通箭，强/弱 | `0400000000000144` / `040000000000020b` | `0d00000000000b8d`，Look `0980000000000c10` | 原始完整 LOD0：2304 顶点 / 2938 三角形 |
| 音波箭，强/弱 | `0400000000000149` / `040000000000020d` | 同一 b8d，Look `0980000000000c11` | 颜色贴图 `0c0000000000102e`；另保留原版 102f/1030/1031 采样 |
| 散射母箭及六子箭，强/弱 | `04000000000001a4` / `040000000000020c` | 同一 b8d，Look `0980000000000c12` | 原版 child Volley 仍引用这两个实体，无独立子箭网格 |
| 音波冲击外观实体 | `040000000000014a` | Look `0980000000000c11` | 此实体链本身没有独立网格，不把它当作可直接打包的脉冲模型 |
| 飞行附属粒子 | `04000000000001b9` → `0300000000000244` | `0d00000000000801` / `0e0000006966f477` | 8 顶点 / 4 三角形；强度贴图 `0c00000000000242` |
| c3 感应/脉冲 | `03000000000002fe` | `0d00000000001385` / `0e0000008a92fe7f`，`0d00000000000dbf` / `0e0000007b543afe` | 3354/6240、1677/3120 顶点/三角形；强度贴图 `0c00000000001298`，16×16、BC4 |
| c3 其他效果 | `0300000000000297` / `0300000000000295` | 0297 含三个 0801 材质对；0295 无可解析 renderer | 原始数据和已支持的网格、纹理均已提取；不冒充完整 effect 播放器 |

`c3.raw` 中 0297、0295、02fe 的原始 GUID 偏移分别为 4888、7736、17656。
现有私有 `hanzo-arrow` 包的 entity 是 **01a4 散射**，并非已选好普通箭头的包。
b8d 的静态绑定姿态有重叠箭头：部件 0 为普通箭头、2 为散射箭头、3 为音波箭头，1 为箭杆、4 为尾羽。
这个部件选择来自提取几何和单张部件接触图，是明确的静态呈现适配；原版隐藏遮罩/动画尚未执行。
新加载器只画 `[0,1,4]` / `[1,3,4]` / `[1,2,4]`，分别 1390 / 1748 / 1312 三角形，避免三个箭头重叠。
所有箭保留米单位与 +Z 长轴；以所选模型箭尖对齐实际碰撞位置。

Claude 在本机运行：

```powershell
.venv/Scripts/python.exe tools/assets/prepare_hanzo_arrow_assets.py
.venv/Scripts/python.exe tools/build_mesh_pack.py --batch research/hanzo-arrows-20261025/mesh-jobs.json
```

需要从档案完整重提时，第一条加 `--extract`。它仍只读取本地档案，不启动游戏。
jobs 为 `hanzo-arrow-primary`、`hanzo-arrow-sonic`、`hanzo-arrow-scatter`、`hanzo-sonic-pulse`、`hanzo-sonic-sense`。
后三个 FX 的研究关联与来源链哈希写入 Sonic chain 的 `researchAssociations`；没有伪造 0149→c3 的原始字节引用。
合并是已校准音波 impact-script 的研究素材包关联；c3 到各 FX 的字节引用则逐项验证。
以后重跑原始 0149 素材链会重建 chain，故应再运行本准备脚本，然后打包。
通用打包器对 BC4 效果保留 `grey` group 与 `materialTextures`；专用 `HanzoSonicPulseMesh` 从验证过的原版 BC4 红通道建立 alpha，**不会画铁块贴图**。
本轮仅用 `--out-root research/hanzo-arrows-20261025/validation-packs` 试打包，没有安装到私有资产目录。
所有提取文件、图片、试包和局部证据留在忽略的 research 目录，不加入提交。

## 弹道核对

`inspect_native_volley.py` 是需要真实 PID 的只读内存工具；遵守“不开游戏”，本轮没有虚构 PID 或重新运行它。
核对的是其读取规则与现存原版树：`hanzo-scatter-calibration1/current-bow-definitions.json` 的 b9:6/20/26，
`final-secondary-expressions.json`，`hanzo-current-calibration2/{result,current-c3}.json`，以及历史原版工厂采样。

| 项目 | 原版声明/观测 | 当前 MC / 本轮处理 |
|---|---|---|
| 普通箭速度 | 蓄力相关，25–90 m/s；历史实测拉弓 150/400/1000 ms 对应 39.3/57.5/90 m/s | 已准入 factory 的实际 velocity，不在渲染器重算蓄力 |
| 普通/音波重力、寿命、路径界限 | `9.800000190734863 m/s²`，5 s，100 m | `tickArmory` 使用 effect.gravity，每步最多 .025 s，扫真实 MC 墙/实体，并累加路径长度 |
| 音波速度 | 同为蓄力箭；当前机器保存过弱/中/强 28.9/60.1/90 m/s | 同普通箭的实际 factory velocity |
| 音波感应 | c3 SetVar12/13：d7=10、1a6=10；Wait9 引 d7；TrackTargets11 引 1a6、角度 360，literal radius=0 | 200 tick、10 m 球形筛选、固定碰撞锚点、原有红色轮廓保持；10 m 球体不等于原版完整目标形状 |
| 音波脉冲 | 已提取 c3/02fe 网格/强度图；完整 shader、颜色、曲线、周期未认证 | 专用网格呈现：青色、20 tick 一次、.1→10 m 扩张，明确为 MC 视觉适配，不影响揭示时长/选敌 |
| 散射母箭 | 当前原版强箭工厂 90 m/s；弱箭历史 34.1 m/s；表达式常量 25/65、charge2a5；重力同上，10 s / 300 m，直接伤害 contextual1dc | 现有适配仍固定 90 m/s、75 原版 HP；20 Hz 重力近似。新增加载边界与 300 m 上界守卫，不新增伤害准入 |
| 散射子箭 | 6 支，split.m_spread=20，spread-mode=2；bounce 整数5、restitution=.8999999761581421；重力同上，10 s / 300 m | 6 支以撞击面法线为轴的等间隔 20° 环、最多5次反弹；系数 .9；具体分布/完整表面响应仍是适配 |
| 子箭速度/伤害 | 原始字节码与常量支持候选解释 `.8*(20+65*q)`、`15+(75-15)*q`，q 为原版 charge2a5；范围16–68 m/s、15–75 HP。contextual980 的 idle getter 仍未认证 | 仍固定52 m/s、75 HP，未偷偷改成声称原版的上下文结果；需要 Claude 接入真实原版蓄力/伤害后再改。公式为字节码解释，尚非原版子箭轨迹/伤害 oracle |
| 插墙箭留存 | 尚无原版留存时长证据 | 普通、音波、散射均 200 server tick 的 MC 呈现适配；音波实际 reveal 仍由原状态机独立控制 |

**左键并非瞬时射线。** 当前半藏普通/音波 Shot 有 effect 且非 hitscan，进入 `tickArmory`，
不是 `tick` 内不带 effect 的直线分支。渲染跟踪同一条真实扫碰撞段，没有第二套预测弹道，也不额外 raycast 造成伤害。
普通/音波的 bounces=0，不会触发通用模拟器中其他武器的 .65 反弹分支。
因此不需要改 `NativeShotSimulation` 的半藏物理；剩余共享变动仅为被动呈现接线。

## 新文件与散射修改

- `HanzoArrowPresentation.java`：只接收真实已准入 sweep 的端点/命中；有界视图、去重、卸载接触拒绝、200 tick 插墙回收、scope/reset。
- `HanzoArrowRenderer.java` / `HanzoArrowMesh.java`：普通/音波/散射母子箭原版部件；米单位、+Z 朝向、箭尖接触、世界/owner/model/host-generation/新鲜度检查、矩阵 finally 恢复；模型失败有 5 秒重试间隔。
- `HanzoSonicPulseMesh.java`：原版 02fe 网格与 BC4 mask，专用半透明呈现；原版效果曲线/颜色未认证。
- `HanzoArrowPresentationCheck.java`：呈现生命周期 fixture，不证明原版弹道或实机像素。
- `tools/assets/prepare_hanzo_arrow_assets.py`：SHA 检查后整理本机素材链和五个 pack job。
- `NativeHanzoSkillRuntime.java`：仅散射 flight/embedded/view、卸载边界、300m 上界；删除散射 CRIT/电火花替代轨迹。接触后母箭留存、子箭反弹预算耗尽后留存；结束/失效 scope 清理。
- `JunkratRenderer.java`：删除原先半藏箭绘制段。龙线程现有 `HanzoDragonRenderer` 自行负责龙箭/龙体；本新渲染器不画龙。

现有 Sonic 状态、实际冲击准入、揭示/红色发光文件未改。
不要把 sensing sphere 的选敌策略称为已经替换掉的原版 server 算法；此次替换的是可见模型与特效网格。

## Claude 的登记与最小共享接线

在 `WorldFrameExporter` 现有 renderer 注册区增加：

```java
HanzoArrowRenderer.register();
```

在现有诊断构建区增加（必需三项，后续分类字段按需）：

```java
diagnostic.addProperty("hanzoArrowRenderFrames",HanzoArrowRenderer.frames);
diagnostic.addProperty("hanzoArrowRenderErrors",HanzoArrowRenderer.errors);
diagnostic.addProperty("hanzoArrowRenderError",HanzoArrowRenderer.error);
diagnostic.addProperty("hanzoArrowPrimaryFrames",HanzoArrowRenderer.primaryFrames);
diagnostic.addProperty("hanzoArrowSonicFrames",HanzoArrowRenderer.sonicFrames);
diagnostic.addProperty("hanzoArrowScatterParentFrames",HanzoArrowRenderer.scatterParentFrames);
diagnostic.addProperty("hanzoArrowScatterChildFrames",HanzoArrowRenderer.scatterChildFrames);
diagnostic.addProperty("hanzoArrowStuckFrames",HanzoArrowRenderer.stuckFrames);
diagnostic.addProperty("hanzoSonicPulseFrames",HanzoArrowRenderer.pulseFrames);
diagnostic.addProperty("hanzoArrowSegments",HanzoArrowPresentation.segments);
diagnostic.addProperty("hanzoArrowEmbedded",HanzoArrowPresentation.embedded);
diagnostic.addProperty("hanzoArrowPresentationRefused",HanzoArrowPresentation.refused);
```

frames 是网格提交计数，不是最终合成原版像素或人类可玩验收。
**普通/音波模型在以下共享接线完成之前不会凭空产生。** Claude 决定并执行：

在 `NativeCombatRuntime.tick` 的现有 `WorldAccess` 实现中增加一个被动回调：

```java
public void present(Shot shot,Vec from,Vec to,NativeShotSimulation.Hit hit){
    if(lastBatch!=null)HanzoArrowPresentation.segment(
        new HanzoArrowPresentation.Scope(owner,worldId,modelId,lastBatch.source()),
        shot,from,to,hit,server.getTicks());
}
```

在 `simulation.tick(...);` 返回后、同一个现有 owner/alive/world 验证分支内增加：

```java
if(lastBatch!=null)HanzoArrowPresentation.publish(
    new HanzoArrowPresentation.Scope(owner,worldId,modelId,lastBatch.source()),
    simulation.activeProjectiles(),server.getTicks(),System.currentTimeMillis());
```

在 `NativeCombatRuntime` 的 scope/source 更换、失效 owner 分支、`close()`、`resetSession()` 中补 `HanzoArrowPresentation.reset();`。
不新增 callback owner、native 调用、按键准入、网络协议或独立模拟器；`impact` 的 Sonic 现有逻辑保持。
若要真正还原散射的弱/中/强弹道，需要另接受验证的 Scatter 工厂 velocity 与 contextual1dc/980；
当前散射只通过 b9:26 信号进入，不能从该 tick 反推出蓄力值，也不能把 child evaluatedDamage=0 当成真实零伤害。

## 验证与剩余验收

证据在 `research/hanzo-arrows-20261025/`：source-before、assets.json、mesh-jobs.json、validation-packs、validation.json。
五包的源网格数组、分组三角形、文件哈希、PNG 与来源一致；三个共享类的备份哈希检查一致。
`compileClientJava` 与呈现 fixture 的最终结果见同目录 `checks.json`。
fixture init-script 的两次路径参数失败保留在交接说明：首次未引用含空格路径，第二次相对路径被 Gradle 的 `-p guest` 解析到 guest 下；使用 `../research/...` 修正。
没有启动游戏、改配置/存档、安装素材或产出新 JAR；不得据此写 ACCEPTED-live。
实际飞行/插墙可见、三种箭头原版隐藏动画、原版 shader/pulse、散射原版蓄力上下文和完整表面响应，仍需主线程后续核验。
