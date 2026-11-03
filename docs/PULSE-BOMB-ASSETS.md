# 猎空脉冲炸弹原模型与私有素材管线

2026-10-23 的本增量已经从用户本机 0.8.0.24919 原包得到真正的脉冲炸弹网格、
原颜色纹理与发光纹理，完成可重复转换及渲染代码替换。它不是新版零售素材导出，
也不是 Minewatch 模型。原数据与转换产物全部保存在项目外私有缓存，JAR 只带加载
和渲染代码。**本页的资产/纯视觉检查通过，不代表本轮游戏内画面验收。** 当前技能
伤害、黏附与生命周期另见 [NATIVE-TRACER-KIT.md](NATIVE-TRACER-KIT.md)；
[NATIVE-PULSE-BOMB.md](NATIVE-PULSE-BOMB.md) 是较早原生声明取证，不能覆盖后续实现。

## 来源和版本

原生校准已证明猎空 graph34 的 Volley1 使用 `0400000000000045`。本次读取同一
离线客户端的本地 CASC 内容，沿实际包声明、实体引用、Look/Material 绑定找到模型。
只读提取器由已有 `tools/assets/casc_read_local.cpp` 构建，固定 SHA256
`f24271c8272d012c3a590ef5be839482ec28d754c41268e10df9eaf01d0246af`；
目标 EXE 固定 SHA256
`f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f`。
提取器拒绝 ONLINE 存储和非24919产品，读取设有大小上限、拒绝覆盖文件，未接触进程。

来源链：`Manifest/Win_SPWin_RCN_LenUS_EExt.apm` → 猎空主包
`AppPackageManifests/Windows-RCN/enUS/02e0000000000003` → 其声明的共享依赖
`0400000000000001` → 下表资源。每个文件同时验证包内 CKey/长度以及固定 SHA256；
包文件也固定哈希。未把未引用的目录扫描结果当作模型归属证明。

| 原资源 | 用途 | 原始字节数 | SHA256 |
| --- | --- | ---: | --- |
| `0400000000000045` | 原生炸弹实体，引用模型和Look | 1,056 | `0f66b6497553dec9588cefaeedb09f25d14cf0ed8f21b26cfce4f14fbea9ce47` |
| `0d00000000000b2c` | 原始刚性网格 | 38,480 | `f90dee3ea70c5ff84ba8c516dc83feb1bce2a49bd599c6a65630769f2cb6dd37` |
| `0980000000000b99` | 原Look与材质槽 | 1,616 | `f314bcaf0ee2b59414b3325acf30712f560ad6b47ded6b5d6b01dec8f005c017` |
| `0e000000000000cf` | 材质及语义绑定 | 240 | `79ee80239ab2e4a9b32abef656ac5d77f02d79c174d15b34238ef89e8c1b24b9` |
| `0c00000000000376` | 原Emission纹理头 | 32 | `8d5b88e7d7ce43cb8cf9e0e053035f99ceccc0f07979badfcce188a1b238810f` |
| `0c00000000000379` | 原Albedo纹理头 | 32 | `60f7c79b35e2cab5100e56101f4a582de7010ecef23ef175904abc0c0154ca41` |
| `0320000100000376` | 原512² BC1发光顶层 | 131,088 | `5502d2a931d9abef9cf70c72b6a9dc8784a9af844e7640fecf8be26bc9a412e9` |
| `0320000100000379` | 原512² BC3颜色顶层 | 262,160 | `888e6adec8316f84bb676d93e2e8f253673a26655acfb57e98dc1f7116b87ec5` |

材质槽哈希 `d3621d55261c5ab7` 同时在网格与Look出现；材质的语义
`ad10f602` 指向Albedo379、`bcbe747d` 指向Emission376。完整 CKey/包哈希/来源收据
仅写入私有 `provenance.json` 与研究证据，没有复制原始游戏资源进仓库。

[OWLib官方仓库](https://github.com/overtools/OWLib) 的格式源码只作为解析结构参考。
这份Beta原始网格是 flat 格式，不是现代 `.owmdl`，不能伪称由官方 DataTool 成功
导出。现有154504零售版本与已核查的OWLib/TACTLib不兼容，本轮没有重试这条失败路线。
固定 Minewatch 私有缓存中检查到猎空武器/图标，未找到具名脉冲炸弹实体网格，未导入。

[暴雪经典模式文章](https://news.blizzard.com/en-gb/article/24146047/a-blast-to-the-past-begins-with-overwatch-classic)
针对2016年1.0并说明黏附炸弹语义，可作为外观/技能参考；该文不是本机2015 Beta的
精确尺寸、数值或纹理来源。现代、2016经典与24919原资源没有混称。

## 实际转换

`tools/pulse_bomb_assets.py` 只支持这份已测量格式，拒绝布局、骨骼、UV、大小或
索引变化。模型731顶点、868三角形、单刚性单位骨骼。原始float位置、uint16索引、
half UV直接读取，packed normal归一化。原尺寸约
`0.3314175 × 0.1013414 × 0.2968823` 米；不额外放大。仅将实际顶点包围盒中心移至原点。
原正面白色面板/青色灯在 **+Y**，背板在-Y；半厚度为`0.05067068338394165`米。

Beta高分辨率BC1/BC3数据采用DWORD平面布局。转换按每块2或4个DWORD交错回标准
BC数据，再由Pillow解码原512²顶层。该交错可逆，独立fixture覆盖2/4DWORD；原先
直接拼DDS的探测产生彩色错误图，保留在私有probe中，没有把它当成功导出。
最终颜色金属层强制不透明，避免把原PBR alpha当切洞；原发光RGB使用MC的additive
Eyes层。没有照搬完整OW PBR、法线贴图、数码倒计时动画或爆炸碎片图。

默认原数据缓存：`~/.universal-modder/assets/ow-beta-24919-pulse/`。
默认准备输出：`~/.universal-modder/assets/owmc-pulse-bomb/`。
路径限定私有assets根目录，拒绝仓库内输出，现有包校验失败时不覆盖。

| 输出 | SHA256 |
| --- | --- |
| `pulse.json` | `06fad1157877a6e3651dec7f61fdced8f25e814123b6222b5c3cb4e8682afdf5` |
| `body.png` | `fc32849e526a47425b106046af0fce68d788b8ce70779b527bd946df54d764a1` |
| `emission.png` | `6259cefae8985295c3e320f0c1f284659b55af608fbda53afd5093b232a2c591` |

启动准备入口（仅本地验证/转换，不启动游戏）：

```python
from pulse_bomb_assets import prepare
result = prepare()  # ready, originalModel, clientBuild, files, error；inGameVerified始终false
```

若原数据未缓存，显式使用CLI的`--extract-game`读取精确哈希的本机离线目录；普通
`prepare()`不会偷偷下载零售内容。缺包/损坏返回明确错误，不把替代方块当原模型。

## 渲染和黏附适配

`PulseBombRenderer` 取代先前MC自建双盒子模型，加载并验证私有模型/PNG，颜色采用
实际MC光照，原发光纹理独立加亮。保留frameExport、输入准入、source generation、
当前猎空model、owner、world、250ms新鲜度、实际发射年龄与区块已载入检查。资源缺失
只设置诊断错误并不绘制，不改变技能碰撞/伤害/耗能。

原+Y面朝实际接触法线。飞行期保留先前每秒一圈的纯展示旋转，但相位来自这枚炸弹
的`launchedWall`，不使用全局时钟余数；贴上后停止旋转。这是MC展示适配，未宣称
原版动画事件完整导出。`PulseBombPresentation` 只计算视觉位移：实际block接触坐标
已有0.04米外移，再增加半厚度+0.003-0.04；entity接触则增加半厚度+0.003。两者背面
均离真实接触平面0.003米，不移动Runtime保存的接触点、爆炸中心或伤害判定。

## 本轮通过与待测

统一冷部署后的补充实际验收：guest SHA256
`928c338c4095798b1ca76a7279abf24661b2db6a39d3f758f602ee21c4e8f01b`
已在真实原生Q投掷后显示本模型，贴到玻璃上的黑/白/青/橙三角炸弹已由根线程
实际查看，随后真实爆炸破坏玻璃、保护bedrock且自有夹具清理通过。证据：
`research/explosive-terrain-20261023/live-v3-exceptions/pulse.mkv`、
`pulse-frame.png`和`result.json`。这补充下文子任务当时“未操作游戏”的历史状态，
不代表所有方向/贴怪/换维度取消、完整OW材质/倒计时/碎片都已验收。

- 21个纯Python合成fixture通过：平面交错往返、BC1/BC3、损坏/截断/超限包、重复GUID、
  刚性几何/尺寸、布局漂移、NaN/索引/UV/法线拒绝、私有路径/防覆盖与hash失败。
- 纯Java21姿态fixture通过：block/entity背板间隙、发射局部相位、周期、贴附停止和
  非法厚度拒绝。该独立编译没有构建、安装或启动游戏。
- 实际私有原包11文件身份通过；第二个独立输出包的三个文件与首包SHA完全相同，
  转换前后原文件均未变。`prepare()`真实返回ready；这只是素材可读状态。
- 最终转换包生成的软件正/背/两侧预览已实际查看，清楚显示原黑色三角外壳、白面、
  三个橙色卡扣与青灯。它不是游戏截图，使用简化光照，不能替代实际MC材质验收。

运行命令：`.venv/Scripts/python.exe tools/test_pulse_bomb_assets.py -v`。
私有证据：`research/pulse-model-assets-20261023/prepared-pack-verification.json`、
`renderer-backup.json`、`presentation-fixture/`；最终预览仅在原始私有缓存。

本轮未操作游戏输入、未安装/启动世界、未覆盖DLL或已加载JAR。统一guest编译与
实际飞行/贴墙/贴怪/光照/换人跨维度取消画面由根线程单独验收。尚需确认发光层实际
混合、各方向背板不穿墙、原生一次投掷对应一个模型、结束无残影；这些未因软件预览
通过而勾选。完整OW材质/倒计时/碎片效果仍是明确缺口。
