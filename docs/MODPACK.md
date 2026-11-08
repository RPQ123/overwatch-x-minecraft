# 一键启动与整合包（任务 B，第二轮 / v1.0.0）

本轮范围：底层路径接入、缺失私有资源降级、账号接口和 v1.0.0 构建审计。
最新用户决定：默认构建 `OWMC-1.0.0`，包括裁剪的私有语音/模型、ffmpeg 和用户已有的精确校验 OW 客户端本地副本。
`--include-private` 默认开启，不增加目录后缀；`--public` 排除客户端、私有资产和 ffmpeg；`--without-client` 可单独省略客户端。
私有素材清单按用户要求标注“暴雪娱乐版权所有；非商业粉丝作品，按 Blizzard 粉丝内容政策使用，禁止商用”。
README 顶部使用相同声明，并注明非官方粉丝作品、与暴雪无关。这是用户指定声明，本构建没有核实素材或完整客户端的再分发授权。
客户端另标为专有本地副本，ffmpeg 保留独立 GPLv3；本轮仅生成本机文件，不上传或发布。
继续使用两个真实进程：原版离线 OW 负责英雄表现，Minecraft 负责实际世界。
**当前产物是内部结构预览包，不能据此宣称换机即玩或完整可玩验收。**
本轮不启动游戏、不下载 MC/OW 游戏文件。任务 A 已结束，本轮可以修改底层路径。
任务 A 的 `startupParallel=true`、并行/串行执行顺序和就绪条件保留；29.7 秒是任务 A 沙盒外的历史实测值，
不是本轮速度结论。六个启动/就绪函数的 AST 与修改前一致；Java 仅修改私有资源路径读取，不改世界启动逻辑。
工作区已有 `AGENTS.md` 改动保留；不提交 git，不改桌面快捷方式，不写 C 盘。

## 启动入口盘点

| 入口 | 现状与处理 |
| --- | --- |
| `ow x mc 启动器.exe` | 统一入口。打开现有 OW 风格窗口，启动、正常结束、重启、设置、首次运行均在窗口中完成。 |
| `launchers/Start-Overwatch-Minecraft.cmd` | 旧直启入口改为统一入口的兼容壳；原直启功能保存在 `launchers/legacy/Start-Overwatch-Minecraft.cmd`，不再作为面向玩家的入口。 |
| `launchers/Stop-Overwatch-Minecraft.cmd` | 保留既有正常保存/恢复控制，供开发与故障处理；不打进整合包。 |
| `launchers/Configure-Overwatch-Minecraft.cmd` | 保留旧设置编辑器；日常使用统一窗口的“设置”。不打进整合包。 |
| `launchers/Launch-Overwatch-AoA.cmd` / `launchers/Stop-Overwatch-AoA.cmd` | NeoForge/Connector 独立实验档案专用，仍保留原文件。本轮不迁移，也不打包这些扩展。 |
| `tools/open_project_launcher.ps1` | 根目录由脚本位置推导。开发仓库用 `.venv`，整合包用 `runtime/python`，也可从 `config/launcher.json` 读取。隐藏的是 Python 控制台；UI 会自行显示。 |
| `tools/project_launcher.py` | 已有 UI/操作命名互斥锁、精确进程身份、脱离 UI 的协调器、严格关闭和失败重试。保留这些行为，并加入首次运行页。 |
| `launchers/standalone/` | 独立 MC、第二 MC、Prism、隔离 OW 研究入口，保留但不随包发布。Prism 并非统一启动器运行依赖。 |
| `launchers/legacy/` | 早期 bridge/MC 主窗口武器实验，以及本次归档的直接会话入口。只供研究，不和监督器叠加运行。 |

只读检查了项目根目录的 `守望先锋×我的世界 启动器.lnk` 和
桌面上的 `守望先锋×我的世界.lnk`：二者都指向 PowerShell，参数中的脚本路径、
工作目录与图标绑定原开发机的工作区。
这些快捷方式不复制到包中，也没有重新保存或改写。移动包后直接双击包内统一 CMD。
系统 Desktop API 本轮返回空目录，因此桌面清单取自原开发机的实际桌面目录。

## 本机依赖与迁移边界

| 依赖 | 已处理 / 仍需处理 |
| --- | --- |
| 启动器根路径 | `Path(__file__)` / `$PSScriptRoot` 推导，不写死盘符。新增模块所有写入限于根目录；拒绝 `..` 越界和源文件链接。 |
| Python | 开发固定 `.venv/Scripts/python.exe`（3.13）。构建时从明确提供的 Python 根目录复制运行时与 Tk；只复制具名依赖及其许可证，不复制整个 venv、`.pth`、账号或缓存。 |
| Java / MC | `launch_minecraft.py`、guest、安装/校验和 Java 构建入口读取同一配置。开发默认仍是原 MC/runtime 目录；包内默认 `runtime/java/bin/java.exe`。 |
| 构建工具 | Gradle 8.10.2、Gradle cache、本机 MinGW、源构建 JDK 仅供开发；玩家包不包含也不依赖编译器。继续使用 `resolve_native_compiler.ps1`，不引入旧 E: 编译器路径。 |
| 校准代码闭包 | `owTypes` 指定 OWLib 类型目录，已去掉具体用户名和盘符。源码/提取工具数据不打包。 |
| OW | 启动、观察、显示租约、窗口安排、PE/PDB、MinHook 与严格恢复都消费配置路径；可选择外部 OW 目录。精确 SHA256、PE/PDB GUID/age、进程创建时间和回调所有者校验保留。更改路径后不会继续放行默认旧路径。 |
| 私有音频/模型 | Python 消费 `privateAssets`/`meshAssets`，Java 通过 JVM 属性消费相同配置；完整语音与 ffmpeg 可独立指定。默认裁剪复制进 private-assets，ffmpeg 单独放 tools/ffmpeg。缺失/不可用时逐项停用并输出中文警告，继续启动；已有哈希校验保留。 |
| MC 档案 | 不复制现有 saves、options、日志、Boss 配置或私有 resourcepacks。新世界仅保存名称/种子/`createWorld=true`，真实建世界必须等首次正常游戏启动。 |
| MC 账号 | 保持已有离线研究身份与空 token，包默认 development-offline、关闭联机。external 仅有内存接口，显式选择后必须提供有效会话；不登录、不读账号库、不保存凭据。详见下文。 |
| 性能模组 | 开发默认仍要求原有、已校验的 Sodium。包内默认允许缺少 Sodium 后使用 MC 原版渲染，不自动下载；已有 Sodium 错误哈希/冲突渲染器仍拒绝。这个 vanilla 分支仅通过离线准备检查，实际合成/FPS 待外测。 |

新增路径集中在 `tools/modpack/config.py`。开发仓库没有新配置时使用原默认值；
相对配置路径随整个目录移动，用户选择的外部 OW 路径允许存为绝对路径。
路径已贯通底层，但真实换机启动尚未验收。编辑 `ready` 或 `backendIntegration` 不会解除显式 external 模式的账号要求。
当前默认沿用已有离线研究模式，不进行真实账号登录；它不证明 Minecraft 游戏所有权。

## 配置接口与默认值证明

配置文件：`config/launcher.json`，schemaVersion=1。模板在 `tools/modpack/launcher.example.json`。
相对路径跟随包根目录，显式绝对路径用于玩家自己的外部安装。修改路径后重新打开启动器/监督器，
不对正在运行的会话热切换。`paths` 支持：

| 键 | 开发机默认 | 包内默认/用途 |
| --- | --- | --- |
| `owExecutable` | 根目录原研究 EXE | 相同相对位置；向导可改成外部路径，唯一允许 SHA256 不变 |
| `owFallbackExecutable` | 旧 offline-lab EXE | 仅未覆盖主路径时保留旧白名单；主路径覆盖后需明确配置才启用 |
| `minecraft` | `minecraft-1.21.1` | 游戏安装/库/资产，首次从官方获取，不打包 |
| `java` | 原 MC 的 java-runtime-delta/bin/java.exe | `runtime/java/bin/java.exe` |
| `python` | `.venv/Scripts/python.exe` | `runtime/python/python.exe` |
| `profile` / `poseProfile` | 原 guest-passthrough / guest-pose-test 目录 | 同名相对目录或自选位置，设置/保存/停止均使用它 |
| `aoaProfile` / `neoProfile` | 原 aoa3-connector / aoa3-neoforge 目录 | 辅助 NeoForge 路径也统一解析，扩展模组仍不打包 |
| `privateAssets` | 原 `~/.universal-modder/assets` | 根目录 `private-assets`；默认裁剪复制，`--public` 不包含 |
| `meshAssets` | privateAssets/owmc-mesh | 可独立指定，默认从 privateAssets 派生 |
| `heroVoiceAssets` | privateAssets/ow1-zhcn-2016/thnu-full | 完整语音来源，可独立指定 |
| `ffmpeg` | 原用户目录 universal-modder/ffmpeg/bin/ffmpeg.exe | `tools/ffmpeg/ffmpeg.exe` 默认附带；缺失不影响预转码完整语音 |
| `owTypes` / `neoInstallSource` | 原用户目录的研究工具/NeoForge 元数据 | private-tools 下的用户自备数据，不打包 |
| `displayLease` / `backups` | 原 `.universal-modder/runtime` / backups | 包内 data/runtime / data/backups |

`test_portability.py` 独立列出并逐项比较全部旧默认值，还与当前 launcher-lib 的 Java 解析结果比较。
迁移测试将自有源码复制后改名到含中文和空格的根目录，验证 OW/Java/profile/停止识别和 JVM 私有资源参数，
所有私有资源缺失时也能生成命令。测试的 EXE/JAR 均为惰性自写夹具，没有复制或启动游戏。

Java 接收 `owmc.privateAssetsDirectory`、`owmc.meshDirectory`、`owmc.heroVoiceDirectory`、
`owmc.heroVoiceFfmpeg`；生产启动时总会传入配置解析后的绝对路径。单独运行旧 Java fixture 才使用兼容默认值。
native-host 未发现固定盘符的启动路径；既有 DLL 所在位置和请求目录推导继续使用，不改回调或帧协议。
`verify_provided_shutdown_abi.py` 仅改路径解析；对应 `native_normal_close.py` 的固定源码 SHA256 已更新为
新文件的精确值，未取消源码校验、PE/PDB 校验或严格正常关闭流程。

私有资源报告在 `research/launcher/resource-status.json`，`SessionBackend.snapshot()` 提供 `resourceWarnings`。
收到 UI 分工补充后，本轮不再修改 LauncherUI/设置页/首次运行页；界面展示由 Claude 接手。

`prepare_lab.py` 为沙盒外实测创建新的 data/ 副本，拒绝覆盖、先备份停机档案到 research/，
不启动或停止游戏，不改参考档案和出厂包；测试副本跳过旧 profile 中的私有资源包，默认指向不存在的私有目录。
有包内客户端时优先使用副本中的 game/，否则复用参考 OW；MC 安装仍复用参考路径，Java/Python 使用包内运行时。
`--development-offline` 必须明确给出，以确认此次实测范围。
可再传 `--without-sodium`，只在新副本复制时跳过已固定的 Sodium，不删除任何源文件。
私有包实测应传 `--bundled-private`，保持指向包内 private-assets；不传时仍用于验证缺失资源的降级路线。
实测副本含用户自己的世界与配置，不能拿来分发；应始终使用未运行的 dist 出厂包做审计。

## 目录结构

```text
OWMC-<版本>/
  ow x mc 启动器.exe       唯一玩家入口
  modpack.json                        内部预览版标识，不记录本机绝对路径
  manifest.json                       每个静态文件的路径、字节数、SHA256、组件、许可证
  README.md
  docs/MODPACK.md
  tools/project_launcher.py
  tools/open_project_launcher.ps1
  tools/modpack/                      配置、向导服务、官方下载/校验与构建工具
  tools/*.py, bridge/*.py             启动/关闭入口的本地依赖闭包及英雄插件
  assets/launcher/                    项目图标（发布许可仍需确认）
  guest/build/libs/owmc-guest-0.1.0.jar
  native-host/build/                  六个当前版本 DLL，不复制整个 build 目录
  runtime/python/                     Python 3.13 + Tk + 具名依赖/许可证
  runtime/java/                       OpenJDK 21，保留全部 legal/
  minecraft-1.21.1/mods/              可选且明确审查的 Fabric API
  licenses/fabric-api/LICENSE
  game/Overwatch Beta 0.8.0.24919/     默认包含已校验的专有客户端本地副本；--public 排除
  private-assets/                     785 条语音白名单与实际引用模型；--public 排除
  tools/ffmpeg/                       备用转码工具与 GPLv3 许可；--public 排除
  config/launcher.json                出厂相对路径；首次准备后变为本地可变配置
  data/tmp/                          首次打开才产生的临时文件，不写系统 TEMP
  research/launcher/                 操作日志，首次操作才产生
  guest-passthrough-client/           首次准备/运行才产生，不复制旧档案
```

六个 DLL 的版本从已有 `native_*_version.py` 与 `native_bootstrap_maps.py`
静态解析，另加固定 local-hero-spawn-v1；不导入可能操作原生进程的模块来探测版本。
构建不重新编译、不覆盖另一线程正在测试的产物；复制后有独立 SHA256 清单。
本轮读取六个 DLL 的 PE 导入表，只发现 Windows 的 KERNEL32/USER32、D3D11、
D3DCOMPILER_47、MSVCRT/UCRT 系列依赖，没有发现额外的 MinGW 共享运行库；
没有为检查导入表而加载这些 DLL，也不将它视为游戏渲染证明。

## 首次运行流程

1. 双击统一 CMD。整合包自动进入与设置页一致的中文“首次运行”页。
2. 点击“检查环境”：64 位 Windows 10 2004+、Python 3.13/Tk、物理内存、所在卷可用空间、
   显卡名称与驱动。建议 16 GiB 内存，低于 8 GiB 或可用空间不足 15 GiB 阻止安装。
   显卡枚举只作准备提示，不代表 D3D11/OpenGL、合成像素或 FPS 验收。
3. 自动使用包内 game/ 的客户端；没有内置时，依次查找 game/、包同级、各本地盘常见位置的
   `Overwatch Beta 0.8.0.24919`。只读 SHA256：
   `f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f`。
   仅匹配后自动填入，不执行；都没有找到时，首次准备保存步骤才弹选择框。
   显式选择但哈希不符会中文拒绝，不绕过校验、不提供 OW 下载。
4. “保存配置”记录相对/外部路径和新世界名，生成 `config/download-plan.json`。
   用配置文件 SHA256 检测其他窗口修改；不覆盖既有游戏设置和存档。
5. 玩家以后明确点击“下载 MC/Fabric”才访问 Mojang/Fabric 官方服务。
   固定 MC 1.21.1、Fabric Loader 0.19.5；使用已内置的 launcher-lib 安装依赖，
   不启动游戏，也不进行登录。本轮没有执行此按钮或下载任何游戏文件。
6. Mojang 官方元数据给的是 SHA1：先以官方 HTTPS + 上游 SHA1 校验客户端、
   所需 Windows 库、资产索引及所有资产对象；Fabric 库从官方 Maven `.sha1` 校验。
   验证通过后才生成本地 `config/installation-sha256.json`。
   “校验安装”重新逐文件比对大小与 SHA256；不能把首次计算出的 SHA256 冒充上游预置值。
7. 当前沿用已有离线研究身份，空 token、关闭联机；外部账号提供方仅定义接口，未接入登录。
   游戏准备完成后可由 Claude 在沙盒外实测。独立换机验收仍未完成，不能把离线夹具当作“一键开玩”证明。
   真正创建世界应由已有 guest/MC 正常启动流程完成。

环境检查和构建默认均离线，不会触发下载。安装失败保留文件与日志；
目前首次安装只接受干净的游戏子目录，已有/半完成安装必须先保留后改用新解压目录，
不对玩家文件做自动删除或无依据修复。后续需补充带所有权记录的断点恢复。

启动器原有 action mutex 继续串行化请求，重复点击不新建所有者；
启动失败保持正常清理、最多两次启动，严格恢复失败不继续启动。
关闭 UI 不终止独立协调器或游戏。新安装/校验在同一 action mutex 下执行，
发现运行中的项目游戏或监督器会拒绝修改安装。

## MC 账号调查与接口（不接入凭据）

旧代码确实是**离线开发身份**：读/生成 `development-identity.json` 的用户名和 UUID，
`token=""`，服务地址指向 localhost:9，`disableMultiplayer=true`；没有 Microsoft/OAuth 登录、
所有权校验或真实账号 token。这个 JSON 不能证明拥有游戏，也不会复制进包。

`tools/modpack/account.py` 保持开发默认行为，包默认 `account.mode=development-offline`，不带用户原来的身份 JSON。
首次运行只在包内生成研究身份，不尝试登录。显式选择 external 时，
受信任的 `AccountProvider.session()` 将来应在内存中提供用户名、UUID、会话 token、有效期和所有权确认。
`AuthenticatedSession` 不在 repr 暴露 token，过期/未确认所有权会拒绝；配置的 account 只接受 mode，
禁止把 token 等凭据字段放进 JSON。本轮没有调用真实提供方，没有读官方 Launcher/Prism 账号库或系统凭据。
现阶段没有账号登录界面、回调 URL、客户端 ID 或凭据导入工具。

整合包应让玩家使用官方或受支持的正版账号启动器，由未来适配层接收经验证会话；
官方登录和游戏所有权由该提供方负责，退出/过期必须重新获取会话，不能回退为假身份。
development-offline 延续当前离线研究环境；它与官方 Launcher 已登录后的离线能力不是同一个实现，也不确认游戏所有权。
参见 [Minecraft 官方账号说明](https://www.minecraft.net/en-us/article/how-create-minecraft-account)、
[官方登录帮助](https://help.minecraft.net/hc/en-us/articles/27201635294861-Troubleshooting-Minecraft-Sign-in-Issues)。
只分发模组与自有代码，不分发游戏本体，仍遵循 [Minecraft EULA](https://www.minecraft.net/en-us/eula)。

## 分发范围与许可证

以下是构建范围和本轮读取实际 JAR/运行时元数据的结果，不代表所有发布条件已经满足。

| 组件 | 许可证与处理 |
| --- | --- |
| 项目 Python 代码、guest JAR、六个 DLL、图标和说明 | 仓库没有顶层项目许可证；清单标记 `LicenseRef-OWMC-Internal-Only`，不替作者决定公开授权。源码许可、图标来源及 native 链接依赖需发布前确认。 |
| 默认包中的语音/模型 | `component=private`，license 使用本文顶部用户指定的暴雪粉丝声明；仅允许明确标记 includesPrivate 的包，不要求后缀。授权未核实，不上传或公开分发。 |
| OW 客户端本地副本 | `component=game-client`，专有内容、再分发授权未核实；复制前后匹配精确 OW SHA256，不属于私有素材声明的许可范围。 |
| ffmpeg | `component=ffmpeg`，实际二进制声明 GPL v3 or later，保留 LICENSE.txt；不能误标为暴雪素材。完整语音为预转码 OGG，无须运行时转码，但按用户要求保留工具。 |
| Python 3.13 / Tk / 捆绑原生依赖 | PSF-2.0 及原构建中的第三方许可证；保留 `LICENSE.txt`、Tk/Tcl 许可与依赖 notice。以 `LicenseRef-CPython-Bundled-Licenses` 标注整个运行时，不能仅凭 PSF 就覆盖 OpenSSL/Tk/VC 等组件。发布前需要完整构建来源、许可审计与 VC runtime 权利核对。 |
| OpenJDK 21 | GPL-2.0-only WITH Classpath-exception-2.0 与第三方许可；保留 `legal/` 全树、release。正式分发还须记录与二进制对应的源码获取/提供方案。本地输入仅用于内部预览。 |
| minecraft-launcher-lib 8.0 | BSD-2-Clause。 |
| psutil 7.2.2 / websockets 15.0.1 / idna | BSD-3-Clause。 |
| NumPy 2.5.4 | 实际 wheel 声明 BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0；保留 wheel 的全部许可目录。 |
| Pillow 12.3.0 | MIT-CMU，保留随 wheel 附带的第三方许可。 |
| PyMongo 4.13.2 / requests | Apache-2.0；dnspython 为 ISC，urllib3 为 MIT，charset-normalizer 为 MIT，certifi 为 MPL-2.0。所有具名依赖都保留 dist-info 和许可证，manifest 记录实际安装版本。 |
| Fabric API 0.116.17+1.21.1 | Apache-2.0；可选参数加入，验证实际 JAR 的 ID/版本/许可证，原 JAR 不修改，复制原 `LICENSE-fabric-api`。 |
| Fabric Loader 0.19.5 | Apache-2.0；首次运行从 Fabric 官方服务获取，当前包不预放 Loader 库。 |
| owo-lib | MIT；可选扩展依赖，本次不包含。 |
| Sodium 0.8.13 | 实际 JAR 为 Polyform-Shield-1.0.0，不作为开源依赖打入本轮包；需要单独审查或改造可选后端。 |
| Aether Fabric 1.5.11 | 元数据为代码 LGPL-3.0 / Fabric 代码 LGPL-2.1，但资产 All Rights Reserved；本次不包含。 |
| Twilight Forest Fabric 4.8.754 | 元数据 LGPL-2.1，未找到 JAR 内独立许可文本；需按确切构建审查代码/资产及对应源码，本次不包含。 |
| NeoForge、Connector、ForgifiedFabricAPI、laowu_meme、Iris/MakeUp | 不在本次最小包范围，不复制现有模组目录。今后逐项固定版本、来源、散列和许可后再纳入。 |

许可证参考：[Python 官方许可](https://docs.python.org/3.13/license.html)、
[Fabric 1.21.1 原始许可证](https://github.com/FabricMC/fabric/blob/1.21.1/LICENSE)、
[Fabric Loader 许可证](https://github.com/FabricMC/fabric-loader/blob/master/LICENSE)、
[OpenJDK 许可](https://openjdk.org/legal/gplv2+ce.html)、
[Python 独立构建说明](https://github.com/astral-sh/python-build-standalone/blob/main/docs/running.rst)。
实际许可文本随构建输入保留，表格不取代它们。
本机 dnspython 2.9.0 wheel 没有附许可文件；构建器补入确切 v2.9.0 上游的
[ISC 文本](https://raw.githubusercontent.com/rthalley/dnspython/v2.9.0/LICENSE)，仅允许该版本使用此补充文件。

两种包都不包含：MC 客户端/版本库/资产/游戏运行档案、账号 token、开发身份、存档、截图/内存证据、
`.universal-modder`、`.venv`、本机快捷方式、Prism、编译器、Gradle/cache、密钥。
内置 Java 是独立许可的 OpenJDK 运行时，MC 本体和资源不会随它复制。
公开精简包还禁止 OW 客户端、原厂 DLL/PDB 和任何私有语音/模型/贴图、ffmpeg。
默认本地完整包按下文白名单带入提取素材，并复制用户已有客户端（排除日志、缓存、转储和账号文件）；没有上传或公开分发。

## 默认资源包（用户新增决定）

构建参数 `--include-private` 默认开启。目录为 `OWMC-<版本>`，README 顶部和清单标记用户指定声明及未核实授权。
`--public` 关闭私有资源、ffmpeg 和客户端；公开包即使出现一个私有或客户端文件也会审计失败。
配置文件默认指向包内 private-assets，不记录源机器的资源绝对路径。

- 完整英雄语音严格取 `HeroVoiceDefaultCatalog.java` 的 785 条不重复白名单，排除其他候选与历史备份。
  优先验证 profile 中 OGG 缓存的原 MP3 SHA256/OGG SHA256 回执；缓存不完整时，只对哈希匹配的现有 MP3 在工作区临时目录转码。
  包内仅保留已预转码 OGG 与裁剪后的 785 条清单，不携带原 MP3。运行时可直接加载 OGG，不依赖转码；仍按用户要求带 ffmpeg 及其许可。
  缺失条目保留 unavailable 标记，Java 计入未就绪/缺项而继续游戏，不把缩短的目录误报完整。
- 模型从 Java 实际字符串引用、名称拼接及炮台 1..3 等有限变体选择，再只复制 provenance 中逐文件 SHA256 匹配的模型与纹理。
  不复制整个 meshAssets、不复制 raw 缓存、未引用模型、旧模型副本和零散研究文件。
- 另外保留启动代码明确引用、已有固定 SHA256 的旧技能语音与命中音效，单独计入额外音效统计，不扩充 785 条主白名单。
- 输入缺失、权限不可读或校验失败的组会记录在 `private-assets/bundle-summary.json`，不关闭游戏、不启用错误资源。
  此处模型组数表示文件组已打包验证；实际 GPU 加载、声音播放和原生攻击仍须 Claude 在沙盒外确认。
- 出厂审计检查 manifest/marker 的 includesPrivate、private 组件和声明一致，不依赖目录后缀。
  客户端只允许作为 game-client 出现在 game/ 指定目录，同时校验 includesClient 和主程序 SHA256；不能藏进 private-assets。

## 准备游戏客户端

默认本地包已包含用户已有的已校验客户端，使用 game/ 中的副本。此副本未确认完整客户端再分发授权。
构建 `--public` 或 `--without-client` 时，把你已有的 `Overwatch Beta 0.8.0.24919` 文件夹放进包的 `game/`，
启动器会自动找到并通过 SHA256 校验，无须手工选择；完成 MC 首次准备后使用根目录入口一键启动。
也会检查整合包同级和本地盘常见目录，均未找到才弹选择框。显式配置的有效客户端优先，不静默替换错误版本。

## 构建与检查

使用项目 Python 3.13；构建命令不会联网。运行时源目录是显式输入，不能给 venv，
也不能把玩家整个 game/profile 根目录当作运行时输入。

```powershell
$packPython = .\.venv\Scripts\python.exe -c "import sys; print(sys.base_prefix)"
$packJava = 'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta'
.\.venv\Scripts\python.exe tools/modpack/build.py --version 1.0.0 --python-runtime $packPython --java-runtime $packJava --include-fabric-api
.\.venv\Scripts\python.exe tools/modpack/build.py --verify dist/OWMC-1.0.0
# 不带客户端/私有资源/ffmpeg 的精简包，另用新版本名，避免覆盖。
.\.venv\Scripts\python.exe tools/modpack/build.py --version 1.0.0-public --python-runtime $packPython --java-runtime $packJava --include-fabric-api --public
.\.venv\Scripts\python.exe tools/modpack/build.py --verify dist/OWMC-1.0.0-public
```

`--python-runtime`、`--java-runtime` 为显式输入。省略时仅产出结构骨架，CMD 会清晰报缺运行时；
本轮实际产物应使用这两个参数。已经存在的输出一律拒绝，不删不覆盖，使用新版本号。
失败保留半成品供检查；缺 `manifest.json` 的包不能打开启动器。

文件清单不包含它自身，避免自引用散列；所有其他静态文件必须且只能列一次。
检查逐文件大小、SHA256、许可、禁止路径、疑似密钥和未登记额外文件。
guest JAR 拒绝捆绑媒体/模型。复制源拒绝链接/联接与越界。
构建从源码的本地 import、脚本文字引用和动态英雄插件计算依赖闭包，不复制整个仓库。
`dist/`、`config/`、`data/`、`private-assets/`、`game/` 已加入 `.gitignore`。
安装/启动以后产生的 `config/`、临时文件和日志属于可变状态，不能塞回分发清单；
出厂 config/launcher.json 也记录在清单中；要复查出厂包应在未运行的副本上执行严格 `--verify`。

不含客户端的包另用 `um publish check <包目录> --game <已验证的离线 OW 目录>` 做独立 lint：
第一轮预检为 0 failures / 8 warnings。四条 `dnspy` 命中实际是合法依赖中的
`dnspython` 注释，并非反编译内容；三条路径命中来自第三方原包的示例/构建元数据，
保留原件；旧校准工具路径已经在第二轮配置化。v1.0.0 以 RESULTS 的实际审计记录为准。
完整本地副本含专有客户端，通用发布检查不能据此判作可发布；组件审计允许的仅是用户要求的本地复制，不授予再分发许可。
完整本机结果不随包分发。内部预览没有发布、上传或生成公开授权。

离线测试（TEMP/TMP 指到工作区；本机默认 PowerShell 策略阻止测试夹具 dot-source，
这里只给测试进程设置 Bypass，不修改系统执行策略）：

```powershell
$env:TEMP = Join-Path (Get-Location) 'data/tmp'
$env:TMP = $env:TEMP
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PSExecutionPolicyPreference = 'Bypass'
.\.venv\Scripts\python.exe tools/test_project_launcher.py
.\.venv\Scripts\python.exe tools/test_passthrough_session.py
.\.venv\Scripts\python.exe -m unittest discover -s tools -p 'test_startup_*.py'
.\.venv\Scripts\python.exe -m unittest discover -s tools/modpack -p 'test_*.py'
```

## 需要配合

第二轮已处理路径接入、可选资源缺失降级和 Sodium 缺失准备分支；这些只经过离线检查和构建。

1. Claude 在沙盒外执行默认开发启动、迁移副本、私有资源缺失和正常停止验收，具体命令在 `tools/modpack/RESULTS.md` 末尾。
   真实原生融合像素、攻击、声音缺失时的技能行为、帧率都不能从夹具推断。
2. 将受支持的账号提供方接入现有内存接口；本轮只调查与定义接口，不实现登录。
   安装断点恢复须先记录本工具的文件所有权，再在固定版本和 SHA256 下安全恢复，不能泛化删除目录。
3. 为自有代码/图标选定许可证，补齐 native 链接组件、Python 构建/VC/Tk/第三方 notice 与
   OpenJDK 对应源码提供信息；完成之前只保留内部预览，不发布、不生成上传记录。
4. Sodium/扩展 Boss 模组不随本轮包复制，未来若要纳入需单独明确许可和源码/通知义务；vanilla 路线的实际融合性能也尚未验收。

## 第一轮验证记录（历史保留）

2026-11-02：环境基线检查通过；现有启动器 49 项、新模块 38 项离线测试通过
（含真实 Tk 首次运行布局、重复请求、严格恢复、错误哈希、清单污染/篡改及复制时并发更新）。
沙盒内 C 盘 Tcl 无法读取脚本，布局测试将脚本复制到工作区临时目录后通过，没有改动 C 盘。
实际构建、出厂清单和内置运行时的统计另记在仓库 `tools/modpack/RESULTS.md`，
这份本机测试记录不随包分发。没有启动游戏或下载受版权保护的游戏文件。
另一线程同时修改的会话/guest/启动测速源码均保留，本轮没有编辑这些路径。
