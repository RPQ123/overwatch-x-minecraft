# 开发者构建与发布范围

本文列出当前源码入口。它不提供游戏客户端、提取资源、工具链或已有世界，也不把构建成功等同于游戏内验收。接续已有开发环境时，先读 [TAKEOVER.md](TAKEOVER.md)、[PASSTHROUGH.md](PASSTHROUGH.md) 与 [PLAYABLE-GOAL.md](PLAYABLE-GOAL.md)。

## 环境

Windows x64；Python 3.13；JDK 21；Gradle 8.10.2；MinGW-w64。Python 依赖固定在 [requirements-dev.txt](../tools/requirements-dev.txt)，Java / Fabric 依赖在 [guest/build.gradle](../guest/build.gradle)。环境准备脚本使用 `uv`，首次安装依赖需要网络。

```powershell
.\tools\setup_environment.ps1
.\.venv\Scripts\python.exe tools/check_environment.py
```

所有 Python 命令使用项目 `.venv/Scripts/python.exe`。`check_environment.py` 是只读前置检查；干净克隆缺少本地客户端、库或工具时会明确失败，不能通过改写检查结果跳过准备步骤。客户端只接受项目 SHA256 守卫所限定的离线研究副本，现行正式服不适用。

## Minecraft guest

```powershell
.\tools\build_guest.ps1 -Tasks build,check
```

脚本解析本地 Java 配置，使用 `tools/gradle/gradle-8.10.2` 与工作区 Gradle cache。JAR 输出到 `guest/build/libs/owmc-guest-0.1.0.jar`。这是构建与离线检查，不启动游戏；没有客户端、依赖或缓存时需先自行完成开发环境准备。

## native-host

先正常结束现有会话；构建脚本会拒绝覆盖正在使用的模块。六个生产模块分别从以下入口构建：

```powershell
.\tools\build_live_passthrough.ps1
.\tools\build_guest_body.ps1
.\tools\build_weapon_gate.ps1
.\tools\build_native_emission.ps1
.\tools\build_session_bootstrap.ps1
.\tools\build_local_hero_probe.ps1
```

编译器统一由 [resolve_native_compiler.ps1](../tools/resolve_native_compiler.ps1) 查找，不把开发机的绝对路径写回源码。版本由各脚本与当前选择器决定，DLL 写入 `native-host/build/`。停止、恢复和精确进程身份检查不能省略；不得对已有 owner 再加载第二份，也不得启用已退役的 hero-layer replay V2/V3。

## 协议检查

```powershell
.\.venv\Scripts\python.exe bridge/test_contract.py
```

这个入口会自行启动所需的 Java fixture。单独运行 unittest discovery 不会准备该服务。通过 fixture 只能说明对应协议或离线检查成立，不能证明实际融合像素、攻击、语音或持续游玩。

## 整合包构建

打包器需要已经完成的 JAR、六个 DLL、启动器及合法取得的运行时输入。下面沿用 [MODPACK.md](MODPACK.md#构建与检查) 的接口，使用新的版本名，避免覆盖已有目录：

```powershell
$packPython = .\.venv\Scripts\python.exe -c "import sys; print(sys.base_prefix)"
$packJava = 'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta'
.\.venv\Scripts\python.exe tools/modpack/build.py --version 1.0.0-public-review --python-runtime $packPython --java-runtime $packJava --include-fabric-api --public
.\.venv\Scripts\python.exe tools/modpack/build.py --verify dist/OWMC-1.0.0-public-review
```

`--python-runtime` 指向完整、干净的 Python 3.13 + Tk 安装根目录，不能指向 venv；`--java-runtime` 指向保留 `legal/` 的 OpenJDK 21 根目录。已有目标一律拒绝覆盖，换新版本名即可。上面只列命令，本次文档整理没有执行打包或游戏测试。

`--public` 排除 OW 客户端、私有语音 / 模型及打包器定义的私有资源输入。它不代表包已经满足所有第三方许可、对应源码提供、账号登录或可运行条件。完整内部包的默认资源范围、运行时要求和验证方式见 [MODPACK.md](MODPACK.md)；该文档保留历史记录，最新包状态以 [TAKEOVER.md](TAKEOVER.md) 顶部为准。

## 当前版本差异

2026-11-03 静态核对：当前源码与开发 JAR 已有 `SurvivalMenu`、`HeroSummonRuntime`；现存 `dist/OWMC-1.0.0` JAR 没有这两个类。因此，不能把新版 README 的 F5 / 生存功能当作旧包已包含的内容。主控应在后续包中同步、正常启动验收并更新校验和，再填写 README 的下载占位。本轮没有修改旧包。

## 公开的内容

保留自有源码、构建说明、可审查的配置模板和压缩演示媒体。游戏目录、存档、提取资源、运行时、编译器、`research/`、`data/`、`dist/` 与日志保持忽略。`guest/src/main/resources/data/` 是项目的 MC 数据定义源码，应正常保留；它不等同于仓库根目录的私有 `data/`。

`.gitignore` 不会移除已经跟踪的文件，也不会清理历史。先完成已有内容脱敏、历史处置和许可决定，再由主控执行明确的提交 / 推送动作。第三方范围见 [THIRD-PARTY.md](THIRD-PARTY.md)。
