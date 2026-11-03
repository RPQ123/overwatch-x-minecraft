# 辅助启动入口

当前统一入口为根目录的 `ow x mc 启动器.exe`：
启动、结束、重启、设置、首次运行都在同一窗口中。
`launchers/Start-Overwatch-Minecraft.cmd` 是保留的兼容别名；原直启方式位于
`legacy/Start-Overwatch-Minecraft.cmd`。不修改已有桌面快捷方式。
整合包只包含统一入口；结构和待接入项见 [MODPACK](../docs/MODPACK.md)。

本目录下的 `launchers/Stop-Overwatch-Minecraft.cmd`、`launchers/Configure-Overwatch-Minecraft.cmd` 保留为旧流程的
手动恢复/设置工具。`launchers/Launch-Overwatch-AoA.cmd`、`launchers/Stop-Overwatch-AoA.cmd` 是独立实验档案专用，
不能与默认会话叠加。所有这些入口的工作目录与 Python 路径均指向项目根目录。

## 本目录的辅助入口

| 文件 | 用途 |
|---|---|
| `launchers/Start-Overwatch-Minecraft.cmd` | 转到根目录统一启动器的兼容别名 |
| `launchers/Stop-Overwatch-Minecraft.cmd` | 默认融合会话的正常结束/恢复 |
| `launchers/Configure-Overwatch-Minecraft.cmd` | 旧版设置窗口 |
| `launchers/Launch-Overwatch-AoA.cmd` | 独立 AoA 实验档案 |
| `launchers/Stop-Overwatch-AoA.cmd` | 正常结束独立 AoA 会话 |

2026-11-02 的整理只移动入口并修正相对路径，没有运行任何游戏。根目录保留主启动入口和
启动器快捷方式。旧设置备份和安装日志在 `../_archive/`；档案路径及仍被工具引用的
`secondary-minecraft-settings.json` 保留原位，明细见 `../research/tidy/T1-report.md`。

## standalone：单独运行

- `Start-Minecraft.cmd`：单独开发 MC 客户端。
- `Start-Minecraft-Prism.cmd`：可选 Prism Launcher。
- `Start-Secondary-Minecraft.cmd`：独立第二 MC 测试窗口。
- `Start-Overwatch-Offline.cmd`：历史独立 OW 研究副本的隔离启动，保留原管理员要求。

## legacy：历史实验

- `Start-Bridge.cmd`：只读姿态诊断桥。
- `Start-Demo-Bridge.cmd`：早期 WebSocket 诊断实验。
- `Start-Combat-Minecraft.cmd`、`Start-Minecraft-Overwatch.cmd`：早期 MC 主窗口武器实验。
- `launchers/Start-Overwatch-Minecraft.cmd`：开发用的原始直接会话入口，路径已适配所在目录。

历史入口保留供研究，不要与当前融合监督器叠加运行。路径已经调整为相对项目根目录，
Python 入口使用项目 `.venv/Scripts/python.exe`。本次只验证入口文件路径，没有启动游戏。
完整交接与暂停状态见 [README](../README.md)。
