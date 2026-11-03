# 第三方组件、致谢与许可来源

核对日期：2026-11-03。以下结合当前源码、本机固定版本 JAR / wheel 元数据和上游项目资料；它不是一份顶层项目许可证，也不是完整整合包的再分发授权。表中链接指向作者项目或许可文本，实际分发时仍需保留对应版本的 notice、许可与适用的源码提供信息。

## 路线与原版研究

| 项目 | 用途 | 许可与来源 |
| --- | --- | --- |
| [Universal Modder](https://github.com/rehan-remade/universal-modder) | 跨游戏研究工具与工作方法 | [MIT](https://github.com/rehan-remade/universal-modder/blob/main/LICENSE)。 |
| [mashup-mods skill](https://github.com/rehan-remade/universal-modder/tree/main/skills/mashup-mods) | 双进程 passthrough 路线参考 | 随 Universal Modder 项目许可；本轮使用该仓库中的发布核查方法整理材料。 |
| [Prometheus](https://github.com/saturn-xvi/prometheus) | 原版离线客户端加载与结构研究；本地工具引用其布局与符号 | [AGPL-3.0](https://github.com/saturn-xvi/prometheus/blob/main/LICENSE)，以确切上游版本为准。不能由本项目的 MIT 声明覆盖派生代码。 |
| [Dear ImGui](https://github.com/ocornut/imgui) | Prometheus 上游界面组件；本仓库未内置该库源码 | [MIT](https://github.com/ocornut/imgui/blob/master/LICENSE.txt)。 |
| [Minewatch](https://github.com/2piradians/Minewatch) | 部分旧技能行为 / 参数的研究参考 | 当前研究说明记录未导入其代码和美术；不能据机制参考推断获得任何游戏素材授权。 |

## Minecraft 与渲染

| 项目 / 实际版本 | 用途与范围 | 许可与来源 |
| --- | --- | --- |
| [Fabric Loader 0.19.5](https://github.com/FabricMC/fabric-loader) | 默认 MC 1.21.1 guest 加载器 | [Apache-2.0](https://github.com/FabricMC/fabric-loader/blob/master/LICENSE)。 |
| [Fabric API 0.116.17+1.21.1](https://github.com/FabricMC/fabric-api) | guest API / 事件接入 | [Apache-2.0](https://github.com/FabricMC/fabric-api/blob/1.21.1/LICENSE)，实际 JAR 附 `LICENSE-fabric-api`。 |
| [Twilight Forest Fabric 4.8.754](https://github.com/TeamTwilight/twilightforest-fabric) | 暮色森林维度、实体与 Boss | 本机 JAR 元数据为 `LGPL-2.1`；[上游许可](https://github.com/TeamTwilight/twilightforest-fabric/blob/latest/LICENSE)声明 2.1 或更新版本。当前 JAR 未附独立许可文本，完整包需补齐确切构建来源与许可材料。 |
| [owo-lib 0.12.15.4+1.21](https://github.com/wisp-forest/owo-lib) | 扩展模组依赖 | [MIT](https://github.com/wisp-forest/owo-lib/blob/braid-ui/LICENSE)，本机 JAR 附许可。 |
| [Sodium 0.8.13+mc1.21.1](https://github.com/CaffeineMC/sodium) | 默认开发档案的性能渲染器 | [PolyForm Shield 1.0.0](https://github.com/CaffeineMC/sodium/blob/dev/LICENSE.md)，由本机 JAR 元数据及许可核对；不能沿用其他旧版本的 LGPL 标记。源码可见不等于可按 MIT 再分发。 |
| [Iris 1.8.14-beta.1+mc1.21.1](https://github.com/IrisShaders/Iris) | 可选光影加载器；本机当前放在停用目录 | 本机 JAR 标记 `LGPL-3.0-only`；[上游许可](https://github.com/IrisShaders/Iris/blob/26.1/LICENSE)。未安装或停用时不承诺光影效果。 |
| [MakeUp Ultra Fast 9.5g](https://github.com/javiergcim/MakeUpUltraFast) | 可选 shader pack | [LGPL-3.0](https://github.com/javiergcim/MakeUpUltraFast/blob/master/LICENSE)，本机 ZIP 包含 LICENSE 与作者链接。 |
| [JNA](https://github.com/java-native-access/jna) | Windows API / 本地映射访问 | [Apache-2.0 或 LGPL-2.1-or-later](https://github.com/java-native-access/jna/blob/master/LICENSE)。 |
| [Mixin](https://github.com/SpongePowered/Mixin) | guest 的运行时接口接入 | [MIT](https://github.com/SpongePowered/Mixin/blob/master/LICENSE.txt)。 |

本机额外存在 Aether Fabric 1.5.11：JAR 声明代码 LGPL-3.0、Fabric 接入代码 LGPL-2.1，**资产 All Rights Reserved**；见 [The Aether](https://github.com/The-Aether-Team/The-Aether)。另有 `laowu_meme 2.0.0` 标记 MIT 并附许可，但未提供上游主页字段，发布包如需包含，须记录原始来源。NeoForge / Connector / AoA 是独立实验档案，不能据默认 Fabric 文档推断它们已纳入同一个包。

## 工具与运行时

Python 依赖版本见 [requirements-dev.txt](../tools/requirements-dev.txt)，具体 wheel 保留自己的许可目录。下表是当前打包文档已核对的范围，完整清单见 [MODPACK.md](MODPACK.md#分发范围与许可证)。

| 组件 | 许可与参考 |
| --- | --- |
| [Python 3.13](https://docs.python.org/3.13/license.html) | PSF-2.0 与随构建附带的第三方条款；Tk / Tcl / OpenSSL / VC 等不能统称为 PSF。 |
| [OpenJDK 21](https://openjdk.org/legal/gplv2+ce.html) | GPL-2.0-only WITH Classpath-exception-2.0 与第三方条款，保留 `legal/` 与对应源码提供信息。 |
| [minecraft-launcher-lib](https://github.com/JakobDev/minecraft-launcher-lib) | 8.0，BSD-2-Clause。 |
| [psutil](https://github.com/giampaolo/psutil) / [websockets](https://github.com/python-websockets/websockets) | 7.2.2 / 15.0.1，BSD-3-Clause。 |
| [NumPy](https://github.com/numpy/numpy) | 2.5.4，本机 wheel 含 BSD-3-Clause、0BSD、MIT、Zlib、CC0-1.0 等许可，保留完整目录。 |
| [Pillow](https://github.com/python-pillow/Pillow) | 12.3.0，MIT-CMU 与捆绑第三方条款。 |
| [PyMongo](https://github.com/mongodb/mongo-python-driver) | 4.13.2，Apache-2.0；传递依赖 dnspython 为 ISC。 |
| [FFmpeg](https://ffmpeg.org/legal.html) | 本机媒体处理工具的构建声明 GPL v3 or later；本轮只运行本地程序，不把二进制上传源码仓库。 |

Claude / Codex 参与项目开发与本次材料整理。本轮导出的图片 / GIF 均来自既有实机成片，没有生成新的游戏画面。

## 自有代码与专有资源

本项目自有代码采用 [MIT](../LICENSE)，版权人 RPQ123，2026 年。第三方或派生作品保留原许可；详见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。项目 logo 的绘制脚本在 `tools/assets/draw_launcher_icon.py`；游戏商标权不由 MIT 授予。

OW / Minecraft 客户端、模型、语音、贴图与原始提取数据保持在本地忽略目录，不属于本项目 MIT 代码许可。演示截图 / GIF 不构成游戏资源包授权。粉丝、非商业、署名或在致谢中列出作者，都不能替代具体的再分发许可。
