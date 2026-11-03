# tools 目录说明

这里存放双进程 OW × Minecraft 路线的启动、构建、维护与离线研究工具。
从仓库根目录运行 Python 命令，统一使用 `.venv/Scripts/python.exe`。

| 位置 | 用途 |
| --- | --- |
| `tools/` 根目录 | 稳定入口、被导入的共享模块、构建脚本和现有离线测试。保留路径以兼容启动器、整合包、历史研究脚本和测试。 |
| `modpack/` | 整合包构建、安装、账户与客户端发现、首次运行及相关离线测试；保持原结构。 |
| `verify/` | 独立的验证、校准、检查与测量脚本。部分脚本需要真实进程，不能把这个目录整体当作离线测试运行。 |
| `assets/` | 独立的原版资源提取、网格/材质/光照审计与语音分析工具；CASC 辅助源码也在这里。被其他模块导入的资源工具仍在根目录。 |
| `_archive/` | 旧路线脚本和一次性任务输入；原位置及归档原因见 [`_archive/INDEX.md`](_archive/INDEX.md)。保留研究记录，不作为日常启动入口。 |
| `gradle/` | 本地 Gradle 分发。构建脚本引用其固定路径，未移动。 |
| `gradle-cache/` | 本机 Gradle/Loom 缓存。离线构建依赖它，未移动或删除。 |
| `python/`、`PrismLauncher/` | 本地便携运行时/客户端启动工具，未移动或删除。 |
| `__pycache__/` | 可重新生成的 Python 字节码缓存；本轮仅列作删除候选。 |

## 主要入口

- 图形启动器：`open_project_launcher.ps1` → `project_launcher.py`。
- 会话启动与正常停止：`launch_passthrough_session.py`、`stop_passthrough_session.py`；模块恢复控制为 `stop_passthrough.py`。
- 来宾启动：`launch_passthrough_guest.py`；AoA 实验入口：`launch_aoa3_lab.py`、`aoa3_passthrough_lab.py`。
- 设置：`configure_passthrough.py`。只读环境检查：`check_environment.py`。
- 开发流程：`dev_cycle.sh`、`dev_cycle_support.py`；构建使用 `build_*.ps1` 和 `resolve_native_compiler.ps1`。
- 启动计时：`benchmark_startup.py`、`startup_timeline.py`。
- 线程完成等待：`wait_codex.py`。
- 语音维护：`prune_voice_defaults.py`、`voice_download.py`。

用户指定的最后五个文件，以及启动入口、共享依赖、所有现有 `test_*.py` 均保持原位。
测试原本使用同目录导入、仓库相对路径和整合包固定清单，因此本轮没有集中到 `tests/`。
`verify_*`、日期任务等如果仍被测试或仓库其他源码引用，也保留原位置；不能仅凭名称判定为过时。

## 离线检查

```powershell
.venv/Scripts/python.exe tools/check_environment.py
.venv/Scripts/python.exe -m unittest discover -s tools -p test_project_launcher.py
.venv/Scripts/python.exe -m unittest discover -s tools -p test_passthrough_session.py
.venv/Scripts/python.exe -m unittest discover -s tools/modpack -p test_*.py
.venv/Scripts/python.exe -m unittest discover -s tools -p test_startup_*.py
```

Windows 的两个 PowerShell 辅助入口测试应在与正式 CMD 入口一致的进程执行策略下运行。
本轮的记录脚本 `research/tidy/T2-run-tests.py after` 仅对子进程设置 `PSExecutionPolicyPreference=Bypass`，
并将临时文件放在工作区内；不修改系统策略，不启动游戏。

本轮路径映射为 `research/tidy/T2-moves.json`，跨区域文档修正请求为
`research/tidy/T2-requests.md`，完整整理与检查结果为 `research/tidy/T2-report.md`。
