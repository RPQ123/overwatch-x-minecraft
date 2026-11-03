# 启动耗时（任务 A，2026-11-02）

**状态：计时、备份确认修复、优化候选和离线检查完成；完整实测验收受阻。**
没有取得“优化前 3 次 / 优化后 3 次”的成功启动样本，不能报告从 47 秒降到了多少秒。
47 秒是任务简报提供的估计，不是本轮复现值。Iris 开/关对照也未完成。并行启动默认关闭。

保留原版离线 OW + 真实 MC 两进程路线；没有改原生 DLL、英雄/战斗/菜单/语音实现，
没有删除用户模组、强杀游戏、查看截图或提交 Git。

## 实测经过与阻塞证据

初始配置：Fabric 1.21.1，光影 off，视距 16，2560×1440，MC/OW 240 FPS；
存档 `Overwatch World 20261027-2332`，桌面 2560×1440@200。环境检查通过，开始时没有游戏/监督进程。

1. 首组正常 `toggle` 的两次内部尝试均在 MC 世界就绪处超时。Java 线程与屏幕名称日志确认：
   客户端停在原版 `BackupPromptScreen` 的实验性世界备份确认页，玩家为空、发布帧为 0。
   正常关闭后，扩展既有 Twilight 的“原版先备份再进入”路径到启动器明确选中的现有存档。
   修复后 4 次后续启动均真实进入 MC 世界，首次世界就绪在 32,317～34,151ms。
2. 2560×1440 下，两次串行尝试的原版 Genji 出生/武器图已完成，但合成器最终 `poses=0`、
   `blended=0`。已有 Present 和 MC 源帧不能充当可见融合证据；两次均判失败并正常关闭。
3. 按接续文档临时选择已验收的 1920×1080，正常启动两次均在显示模式 TEST 处返回
   `Display mode change refused: -1, flags=2`，没有继续启动 OW。未绕过显示租约或改注册表。
   因不能进行 1920 对照，也不能断言分辨率是 2560 失败的唯一根因。
4. 不再追加同类失败启动。所有组均通过正常启动器停止；最后游戏/监督均为 0，原设置逐字节恢复，
   桌面仍是 2560×1440@200。最终 guest 已构建并安装到默认停机档案。

## 已取得的阶段分布

下表是修复实验性世界确认后的 **2560 串行两次失败尝试**，不是成功基线，也不是 3 次中位数。
两次都未进入合成选人阶段；错误/停止/内部重试耗时没有当成成功启动性能。

| 阶段 | 尝试 1（ms） | 尝试 2（ms） | 优化后 3 次中位数 |
|---|---:|---:|---|
| 启动器校验、拉起 Python 至脚本首行 | 2042 | 1314 | 未取得 |
| Python 导入 | 209 | 207 | 未取得 |
| MC 档案/资源准备 | 1854 | 1496 | 未取得 |
| JVM 拉起至 Fabric 首条日志 | 2210 | 2219 | 未取得 |
| Fabric/模组加载至 bridge 客户端初始化 | 14989 | 14474 | 未取得 |
| 客户端资源准备至请求进入世界 | 4848 | 5055 | 未取得 |
| 世界加载至真实玩家/帧就绪 | 5882 | 6126 | 未取得 |
| OW 拉起至原版客户端/插件就绪 | 6483 | 5518 | 未取得 |
| 原版 bootstrap/地图 | 6482 | 6269 | 未取得 |
| 原版出生调用 | 184 | 160 | 未取得 |
| 等待源氏模型/武器图 | 186 | 113 | 未取得 |
| 合成器就绪、选人界面 | 失败，poses/blended 为 0 | 同左 | 未取得 |
| 完整成功启动总耗时 | 未取得 | 未取得 | 未取得 |

这些数据提示可把约 12～13 秒的原版初始化与约 30 秒的 MC 拉起重叠，
但这只是优化方向，不能把区间相加/相减当成实际节省时间。

## 改动

- `tools/startup_timeline.py`：Python `perf_counter_ns` 单调计时，线程安全的独立时间线，
  `research/launcher/startup-timeline-*.json` 保存事件、阶段毫秒、身份及失败原因。
  会话状态 `startup` 包含路径、阶段和里程碑摘要。
- `tools/launch_passthrough_session.py`：分离 `launch_native` / `launch_pair`；
  `startupParallel=true` 才将 MC 拉起与 OW 冷初始化并行，双方就绪并核对存档后才安装共享合成/战斗模块。
  工作线程只存在于本次启动，失败时也等待其结束；不新增回调所有者或改变已加载模块的拒绝条件。
  新 MC 的 HTTP 探测超时从 2 秒降到 250ms、间隔从 200ms 降到 100ms，运行时 API 默认超时仍为 2 秒。
  默认串行的窗口安排顺序保持原样。
- `tools/launch_passthrough_guest.py`：档案准备计时；仅为明确选中的现有存档传递启动备份许可属性。
- `guest/.../WorldFrameExporter.java`、`TwilightTrialStartup.java`：客户端/世界启动日志，
  首次加载时通过原版“创建备份并进入”按钮处理实验性世界提示。只接受实验性提示，
  不自动接受版本降级等其他提示，不选跳过备份，不重复确认普通存档；保留既有 Twilight 行为。
- **`tools/project_launcher.py` 本任务仅改两个函数**：
  `SessionBackend.clean_start` 传递单调时钟原点；`SessionBackend.wait_started` 使用单调超时和 200ms 正常就绪轮询。
  同文件的整合包/界面等其他并发改动属于另一线程，未重置或覆盖。
- `tools/benchmark_startup.py`：有限 3 轮正常 `toggle`/`stop`，每组先备份停机档案，
  保存每次尝试与停止结果，失败即停止追加启动。支持策略/Iris 对照，结束后恢复设置及 Iris 状态，
  保留并发设置修改，不下载缺失的实验光影依赖。
- 新增 `test_startup_timeline.py`、`test_startup_pair.py`、`test_startup_world_prompt.py`。
  `test_passthrough_session.py` 补齐原有 Bastion/Mei 原生读取夹具的隔离；原始 HEAD 可复现旧失败。

通过 `toggle` 启动时，时钟原点来自 `clean_start`；直接 `start`/监督器入口以脚本首行为原点，
不伪造缺失的父进程时间。Java 阶段是 Python 首次观察日志的时间：原样本的轮询/HTTP 上界约 2.2 秒，
新探测约 350ms，另含日志刷新延迟。没有直接相减 Java 和 Python 的时钟。
模块就绪、真实帧传输、原生合成像素和玩家游玩验收仍分别记录。

## 检查与保留项

- Python：启动器 49、会话 52、新启动相关 14、正常停止 19、显示租约 19、语音资源/事件 16，合计 **169 项通过**。
  两个 Windows 桌面夹具需当前进程设置 `PSExecutionPolicyPreference=Bypass`，未改桌面脚本来绕过测试。
- 按正确入口执行 `.venv/Scripts/python.exe bridge/test_contract.py`：1 项 HTTP/Java 契约通过。
- 最终 `tools/build_guest.ps1`：`BUILD SUCCESSFUL`，62 个任务，含现有菜单/英雄/语音等离线检查。
  最终只读环境检查通过。上述不等于 12 英雄、F7～F11、语音的真实游戏回归验收。
- 7 个顶层模组 JAR（Fabric 展开为 97 个条目）全部保留：bridge、Fabric API、Sodium、owo、
  Twilight Forest、Aether、`laowu_meme`。TF/Aether 即使 `twilightTrial=false` 也参与加载；
  不能仅据此判断多余，未删除。没有改 JVM 堆/JIT 参数，没有使用 `TieredStopAtLevel`。
- 已知风险：显示/原版融合阻塞仍未解决；并行冷启动的 GPU/CPU 竞争尚未实测，默认不开；
  Iris 编译开销没有对照数据。自动原版备份会增加磁盘使用量。

## 证据与后续复测

所有原始证据及备份均在 Git 忽略目录内：

- `research/launcher/startup-baseline-20261102/`：最初超时与完整停机档案备份；
- `research/launcher/startup-serial-off-20261102/results.json`：2560 两次失败尝试及阶段；
- `research/launcher/startup-serial-1080-off-20261102/results.json`：显示 TEST 拒绝及正常关闭；
- `research/launcher/startup-closeout-20261102.json`：最终身份、显示、原设置恢复、停止回执、模组清单；
- `research/launcher/startup-build-final.log`、`startup-test-*.log`、`startup-environment-final.json`；
- `research/launcher/original-settings-20261102.json`：本任务前设置原字节。

默认档案 build=installed guest SHA256：
`5f92c172e176ed0b2ca5bd03240804eb7ec386e27d377663055b117f0388ab68`。
AoA 独立档案未替换；原版 DLL 未重建。

需要先恢复正常的显示/合成启动条件，再依次执行以下有限实验；每个输出目录必须是新的。
三组会自动正常停止并恢复设置；第一组才是候选版本上的可比串行基线。

```powershell
.venv/Scripts/python.exe tools/benchmark_startup.py --output research/launcher/serial-off-next --strategy serial --shaders off --runs 3
.venv/Scripts/python.exe tools/benchmark_startup.py --output research/launcher/parallel-off-next --strategy parallel --shaders off --runs 3
.venv/Scripts/python.exe tools/benchmark_startup.py --output research/launcher/parallel-iris-next --strategy parallel --shaders low --runs 3
```

在取得成功样本和真实功能回归之前，任务 A 的完整完成标准仍未通过。

## 沙盒外实测（Claude，2026-11-02）

上面的失败都发生在 Codex 沙盒里：从沙盒启动的游戏不能改显示模式，也无法完成画面合成。
在沙盒外用同一个 `tools/benchmark_startup.py`、同一份代码重测，结果如下（光影关闭，2560×1440，每组 3 次全部进入选人界面并正常关闭）：

| 策略 | 3 次耗时（秒） | 中位数 | blended |
|---|---|---:|---|
| 串行（原方式） | 40.1 / 39.6 / 39.0 | **39.6 s** | 31 |
| 并行（MC 与 OW 同时冷启动） | 30.2 / 29.7 / 29.3 | **29.7 s** | 15 / 24 / 28 |

决定：`startupParallel` 默认改为 `true`（`launch_passthrough_session.py`）。如果要退回串行，在 passthrough-settings.json 里设 `"startupParallel": false`。
证据目录：`research/launcher/claude-serial-off-20261102/` 和 `research/launcher/claude-parallel-off-20261102/`。
并行时各阶段耗时的中位数：Fabric 加载 6.9 s，MC 资源 8.9 s，进入世界 5.6 s，原版进程与插件 4.3 s，原版初始化 6.4 s，合成器 1.8 s，观察器 3.1 s。
光影开启时的启动耗时还没有对照数据。
