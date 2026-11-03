# 第三方组件与资源声明

本公开快照的自有代码采用 [MIT License](LICENSE)，版权人 **2026 RPQ123**。
MIT 仅覆盖本项目拥有权利的代码与相应自有说明。下列第三方组件、许可文本、
游戏画面与商标继续适用各自权利和条款，不因顶层 LICENSE 而改为 MIT。
核对日期：2026-11-03；版本来自现有开发环境审计，依赖本身不随源码快照提供。

## 游戏客户端和资源

- Overwatch 客户端、英雄模型、动画、语音、音效与贴图属于**暴雪娱乐**及相应权利人，
  不在本仓库内，也不在 MIT 授权范围内。
- Minecraft 客户端及其游戏资源属于 Mojang / Microsoft 及相应权利人；同样不随仓库提供。
- `docs/media/` 包含压缩演示素材和官方英雄图标，保留其中游戏作品与商标的原有权利；
  不作为 MIT 游戏素材包授权。素材来源见 [媒体说明](docs/media/README.md)。
- 项目 logo 由 `tools/assets/draw_launcher_icon.py` 绘制；项目名称、图标或声明均不授予
  暴雪、Mojang、微软或其他第三方的商标权。本项目与上述公司无隶属或认可关系。
- 本项目为非商业粉丝研究项目。这是项目定位；自有代码的许可条款以 MIT 原文为准。

- 英雄头像与技能图标 © Blizzard Entertainment，来源为 [Overwatch Wiki](https://overwatch.weirdgloop.org/)；仅用于非商业粉丝项目展示，逐文件来源见 [媒体说明](docs/media/README.md#技能状态与图标来源)。

## 路线、研究和直接保留的第三方材料

| 项目 | 使用范围 | 原许可 |
| --- | --- | --- |
| [Universal Modder](https://github.com/rehan-remade/universal-modder) | 工具方法与双进程路线参考；特别感谢 [mashup-mods skill](https://github.com/rehan-remade/universal-modder/tree/main/skills/mashup-mods) | [MIT](https://github.com/rehan-remade/universal-modder/blob/main/LICENSE)；Copyright 2026 Rehan and universal-modder contributors。 |
| [Prometheus](https://github.com/saturn-xvi/prometheus) | 指定离线客户端的结构、偏移、符号与本地通信协议参考；上游加载器与补丁数据由本地研究环境另行提供 | [AGPL-3.0](https://github.com/saturn-xvi/prometheus/blob/main/LICENSE)。不由本项目 MIT 覆盖。 |
| [Dear ImGui](https://github.com/ocornut/imgui) | Prometheus 上游的 UI 组件，本仓库未内置其源码 | [MIT](https://github.com/ocornut/imgui/blob/master/LICENSE.txt)。 |
| [Minewatch](https://github.com/2piradians/Minewatch) | 旧技能机制和参数研究参考，没有随快照导入其代码或美术 | 仅作为研究致谢，不授予其代码或资源使用权。 |
| [OWLib / TankLib](https://github.com/overtools/OWLib) | 本地资源工具与 STU 结构参考；工具链及其源码不随快照提供 | [MIT](https://github.com/overtools/OWLib/blob/master/LICENSE)，Copyright 2016–2024 overtools。 |
| [CascLib](https://github.com/ladislav-zezula/CascLib) | 自有 `tools/assets/casc_*.cpp` 工具调用其 API；库和头文件需另备 | [MIT](https://github.com/ladislav-zezula/CascLib/blob/master/LICENSE)，Copyright 2014 Ladislav Zezula。 |
| [dnspython](https://github.com/rthalley/dnspython) | 打包器保留许可材料 `tools/modpack/licenses/dnspython-2.9.0-LICENSE.txt`，未内置库实现 | ISC；该文件保留原版权与许可全文，不按本项目 MIT 重新授权。 |

此次静态检查未识别到直接复制的 Prometheus 实现源码。`tools/observe_overwatch.py`、
`tools/inspect_native_scripts.py` 等读取其公开结构/协议，`tools/relay_prometheus.py`
适配其本地协议；`tools/prepare_overwatch.py` 从用户另备的上游源码读取补丁数据。
Prometheus 的 `.cpp` / `.h` / `.cs`、DLL、PDB 和补丁数据没有复制进本快照。
结构或协议参考不构成对上游实现代码的重新授权；以后如导入、修改上游代码，
必须保留其原有许可头并满足适用许可，不能改标 MIT。

## Minecraft 模组与渲染组件

| 组件 / 开发环境版本 | 用途 | 许可来源 |
| --- | --- | --- |
| [Fabric Loader 0.19.5](https://github.com/FabricMC/fabric-loader) | 默认 guest 加载器 | [Apache-2.0](https://github.com/FabricMC/fabric-loader/blob/master/LICENSE)。 |
| [Fabric API 0.116.17+1.21.1](https://github.com/FabricMC/fabric-api) | Fabric API 与事件接入 | [Apache-2.0](https://github.com/FabricMC/fabric-api/blob/1.21.1/LICENSE)。 |
| [Twilight Forest Fabric 4.8.754](https://github.com/TeamTwilight/twilightforest-fabric) | 暮色森林维度、实体和 Boss | [LGPL-2.1-or-later](https://github.com/TeamTwilight/twilightforest-fabric/blob/latest/LICENSE)；现有 JAR 元数据写作 `LGPL-2.1`。 |
| [owo-lib 0.12.15.4+1.21](https://github.com/wisp-forest/owo-lib) | 扩展模组依赖 | [MIT](https://github.com/wisp-forest/owo-lib/blob/braid-ui/LICENSE)。 |
| [Sodium 0.8.13+mc1.21.1](https://github.com/CaffeineMC/sodium) | 性能渲染器 | [PolyForm Shield 1.0.0](https://github.com/CaffeineMC/sodium/blob/dev/LICENSE.md)，该构建不可沿用旧版 LGPL 标记。 |
| [Iris 1.8.14-beta.1+mc1.21.1](https://github.com/IrisShaders/Iris) | 可选光影加载器，审计时位于停用目录 | [LGPL-3.0-only](https://github.com/IrisShaders/Iris/blob/26.1/LICENSE)，按所用 JAR 元数据。 |
| [MakeUp Ultra Fast 9.5g](https://github.com/javiergcim/MakeUpUltraFast) | 可选 shader pack | [LGPL-3.0](https://github.com/javiergcim/MakeUpUltraFast/blob/master/LICENSE)。 |
| [JNA](https://github.com/java-native-access/jna) | Windows API / 共享映射访问 | [Apache-2.0 或 LGPL-2.1-or-later](https://github.com/java-native-access/jna/blob/master/LICENSE)。 |
| [Mixin](https://github.com/SpongePowered/Mixin) | guest 运行时接口接入 | [MIT](https://github.com/SpongePowered/Mixin/blob/master/LICENSE.txt)。 |

额外实验档案与默认整合包有区别：Aether Fabric 1.5.11 的代码为 LGPL-3.0，Fabric 接入
代码为 LGPL-2.1，资产 All Rights Reserved，见 [The Aether](https://github.com/The-Aether-Team/The-Aether)。
NeoForge / Connector / AoA 的独立实验档案不随此源码快照提供，也不代表默认包已包含它们。
`laowu_meme 2.0.0` 的本地元数据标记 MIT，但缺少上游主页，若未来随完整包提供仍需补齐来源。

## 开发工具与 Python / Java 依赖

固定 Python 版本见 [requirements-dev.txt](tools/requirements-dev.txt)；当前审计版本与详细
上游链接见 [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md)。本快照没有包含这些运行时或二进制。

| 组件 | 原许可 |
| --- | --- |
| [Python 3.13](https://docs.python.org/3.13/license.html) | PSF-2.0 及随发行版附带的第三方条款。 |
| [OpenJDK 21](https://openjdk.org/legal/gplv2+ce.html) | GPL-2.0-only WITH Classpath-exception-2.0 及第三方条款。 |
| [minecraft-launcher-lib 8.0](https://github.com/JakobDev/minecraft-launcher-lib) | BSD-2-Clause。 |
| [psutil 7.2.2](https://github.com/giampaolo/psutil) / [websockets 15.0.1](https://github.com/python-websockets/websockets) | BSD-3-Clause。 |
| [NumPy 2.5.4](https://github.com/numpy/numpy) | BSD-3-Clause，发行版另含 0BSD、MIT、Zlib、CC0-1.0 等第三方条款。 |
| [Pillow 12.3.0](https://github.com/python-pillow/Pillow) | MIT-CMU 及捆绑第三方条款。 |
| [PyMongo 4.13.2](https://github.com/mongodb/mongo-python-driver) | Apache-2.0；其 dnspython 依赖为 ISC。 |
| [FFmpeg](https://ffmpeg.org/legal.html) | 现有媒体工具构建声明 GPL-3.0-or-later；该工具二进制不随源码提供。 |

项目由 Claude / Codex 辅助开发。组件的公开源码、免费使用、署名或非商业声明均不自动
授予完整客户端或资源再分发权。将来如发布包含依赖的整包，仍需保留各版本要求的许可、
notice、版权信息及适用的源码提供材料。
