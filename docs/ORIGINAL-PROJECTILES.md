# Original projectile assets — 2026-10-18

**用户随后取消整个新增显示方案，当前已移除模型显示、自旋、实体注册及对应 Java 类。**
攻击/伤害桥保持；以下仅为历史研究记录，不是当前启用功能。OWLib 的只读提取工具和
私有外部资源保留用于后续英雄与音效研究，不会被当前 guest jar 加载。

用户拒绝上一轮自制三叶几何、CRIT/ELECTRIC_SPARK/END_ROD 粒子替代，要求原版
OW 子弹效果，并明确授权使用 OWLib 从其本机国服客户端只读提取后适配。
后续用户明确指出缺少飞行自旋，并授权无人值守运行和实机测试。

## 已接入的源氏模型

- 本机资源来源：`D:/ow/over/Overwatch`，`.build.info` 为 `2.25.0.0.154088`。
  DataTool `2.25.0.0+1151+68397365` 成功读取 RCN/zhCN 本地资源，`--online=false`。
- 官方项目：[OWLib](https://github.com/overtools/OWLib)。工具和源码在用户目录
  `.universal-modder/toolchains/`；没有安装到游戏目录，没有附加国服游戏进程。
- 原生发射资源 `04000000000007ca` 对应 OWLib `0000000007CA.003`，明确引用
  模型 `0000000029F9.00C`，材质 `0000000021D5`、shader217。模型是无骨骼刚体，
  2145 个顶点、1044 个三角形，尺寸约 0.1642 × 0.1422 × 0.00957 米。
  实际三视图 `research/_archive/2026-10/original-shuriken-orthographic.png` 已检查。
- 材质含原版 Albedo `4D7E`、Emission `4D80`、PBR `4D7F`、Normal `4D81`。
  纹理语义由官方 [io_scene_owm](https://github.com/overtools/io_scene_owm)
  `shader_metadata.py` 核对。当前使用原始顶点、索引、UV、颜色贴图和发光蒙版；
  发光蒙版与颜色贴图合成为 MC emissive 材质输入。
- 独立弹体实体只负责显示，同一条已接收的原生发射记录负责扫掠碰撞与一次伤害。
  命中、超时、换人、维度/会话切换和停机清理；不再生成上述替代粒子。
- 手里剑绕飞行轴自旋，按每个实体的 age + tickDelta 插值，当前 6 转/秒。
  **速度是适配参数，尚未绑定或逐帧校准原版角速度。** 原始几何没有放大或改形。

## 尚未完成

原版模型/贴图不是完整原版效果。OWLib 当前 `SaveLogic/Combo.cs` 的 `SaveEffect`
在写 `.oweffect` 之前直接返回；`SaveAnimation` 同样跳过完整动画效果输出。
`extract-anything` 能得到三个关联模型和材质，但不能因此声称全部光尾、命中特效、
电弧和 OW PBR/bloom 渲染已经移植。

当前不添加替代的麦克雷射线粒子或温斯顿电弧。其原生手部、HUD、攻击和 MC
伤害桥保持现有逻辑，完整原版世界特效仍待适配。`/combat` 明确报告
`presentationMode=original-genji-model`、`originalEffectGraph=false`，诊断工具也
保留这一未完成项。其他英雄接入仍须逐名校准。

## 本地复现

```powershell
.venv/Scripts/python.exe tools/assets/extract_original_projectiles.py --client 'D:/ow/over/Overwatch' --datatool '<USERPROFILE>/.universal-modder/toolchains/owlib/2.25.0.0-1151/DataTool.exe'
```

脚本提取唯一确认的 `7CA` 依赖链，输出本地私有资源包至
`<USERPROFILE>/.universal-modder/assets/owmc-original-projectiles/`。
`provenance.json` 记录原始文件、工具、客户端 build-info 与运行资源的 SHA256。
Java 端校验 schema、资源绑定、尺寸、数组边界和哈希；缺失/不匹配时禁用显示，
不生成替代模型，也不影响攻击接收和伤害。客户端更新后必须重新校准。
资源不进入源码、jar 或提交；只提交适配器。启动器仍按原流程复制 guest jar。

## 本机验证

Guest `build` 与全部 Java 检查通过（含 30..240 FPS 相同角位移的旋转检查）。
37 项 Python 启动、目录、诊断和 OWLib 格式边界检查通过；
`python bridge/test_contract.py` 的独立 Java HTTP fixture 通过。
实际目标提取中的 3 个 OWMDL、34 个 OWMAT、4 个 OWENTITY 全部解析通过。

修复自旋后的录像 `research/_archive/2026-10/original-spin-hit-proof.mkv` 与连续帧拼图
`research/_archive/2026-10/original-spin-crop-sheet.png` 已检查：原版三叶模型在飞行中改变角度，
原生投掷/弹药/手部保留，村民产生真实命中反馈。受控三发使 admitted 从69到72，
entityHits 从0到3，目标20到9.5；事件重放不追加伤害。
临时目标已清理，没有放置测试墙，活动弹体0。最终状态及边界见
`research/_archive/2026-10/original-spin-final-result.json`，结束进程身份须以该记录/当前状态为准。

较早 `owlib-original-hit-proof` 一次输入因前台变成 SearchApp 被工具拒绝，
期间用户也在换人/开火，不能将那段计数用作受控三发验收。
用户随后明确授权无人值守测试，才完成上述单独验证。

测试前备份：
`<USERPROFILE>/.universal-modder/backups/native-original-effects-20261018/20261018-170645.zip`。
仍使用原存档 Fresh15C、1080p、OW Low、无光影、8区块、昼夜循环。
