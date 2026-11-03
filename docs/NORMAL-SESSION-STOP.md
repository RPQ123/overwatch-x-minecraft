# 生产正常停止与重启 — 2026-10-24

本项把已验收的关停路线接入生产 `tools/stop_passthrough_session.py`。
源码与故障 fixture 已完成；主线程已通过真实选人正常停止和启动器重启的关闭段。
**战斗后重启和 MC 来源退出仍待实测**。初始小窗/黑画面没有算作可见融合通过。
不把旧 ABI 验证器的历史成功当作这次生产接线已完成验收。

## 路径和所有权

桌面启动器原有 Stop/Restart 已调用该脚本；不另加原生模块或回调所有者。
新增 `tools/native_normal_close.py` 负责停机顺序：

1. 先核对真实 PID、创建时间、准确 EXE 路径及 SHA256，保存内核 FILETIME。
   保持同一个可等待的内核进程句柄直到退出，避免 PID 重用污染退出结果。
2. 在任何游戏状态改变前，核对 MC 健康接口、PID、创建时间、Java 路径和准确
   `--gameDir` 参数。HTTP 不可用但同 profile JVM 仍在时，保留进程并明确失败。
3. 停止现有准确 supervisor；不注入第二个 owner，不恢复隔离实验。
4. 读取实际提供插件接口，确认已安装并映射两数据字节 ABI 修复。
5. 按 emission、weapon gate、body、compositor 顺序停止四个长期 owner。
   每个终态必须来自本 PID／本次创建后的报告；有 creation 字段时必须匹配
   FILETIME。compositor37+ 还必须分别证明全局、输入钩子、光照和帧限制恢复。
6. 恢复后再次确认提供插件接口，再向准确原生窗口发送 WM_CLOSE，走原生析构。
7. 先等3秒；如原作者 atexit 进入 pause，只在旧渲染 HWND 已消失、准确控制台
   同时有 `Process exit initiazed: 0`、shutdown 和任意键提示时，向该控制台
   CONIN 写入一组 Return。没有全局键盘输入。之后最多再等20秒。
8. 检查同 PID／创建时间／Application 对应错误报告。即使退出码0，有本次
   匹配报告也判失败；报告查询失败同样不能冒充正常关闭。
9. 只有原生正常关闭通过，才请求已验证 MC 的原有 shutdown 并等45秒保存退出。
   `--keep-minecraft` 保持现有 MC 存活，便于受控冷启动对照。

WM_CLOSE、精确 console pause 和映射接口检查直接复用原已验收验证器的函数，
不另复制一份低层窗口／控制台实现。验证器文件保持原字节：
`f401296b19f48e7e2d9e28271471e3ed1a20d08e236fb31725d8faaa7be11ba8`。
helper 加载前检查此 SHA256，不修改该文件。

## 失败语义

没有原生 terminate/kill，也不以菜单 Exit 绕过析构。所有者未恢复、报告缺失、
原生窗口仍存在、控制台提示不完整、等待超时、身份改变或匹配崩溃报告时，
写 `stop-failed`，抛出异常并返回非零。启动器 checked_command 会阻止后续重启。
此时 MC 不会收到 shutdown，不能谎报已保存；已停的 supervisor 不自动重启。
维护人员先读证据，不能在仍加载的 DLL 上重叠新回调或强杀后回写成功。

部分启动恢复补充：实际独占全屏试验仅加载bootstrap/localhero/compositor，
其余长期owner根本尚未加载。现在在supervisor停止后枚举准确映射的四个回调
模块族；只对确实没有映射的族记录ownerNotMapped，映射了却缺报告仍拒绝。
原生关闭前再次比对模块族，过程中出现新owner则拒绝关闭。23项helper fixture
与实际partial-start正常关停通过，未跳过一个真实加载中的owner。

选人或失焦没有有效 Present 时，原 owner 恢复可能仍超时；本接线保留严格
失败，**没有放宽恢复条件，也没有用输入操作激活 Present**。若真实复测复现，
应保留本次报表与画面另行处理，不能称该分支已经修复。

证据默认写入 `research/normal-session-stop/<ns>-<observerPid>/`：
`session-result.json` 记录完整会话结论，各 `native-<pid>/result.json` 记录逐 owner
恢复、WM_CLOSE HWND、控制台证明、真实退出码和匹配错误报告。目录必须为新目录。

## 无游戏 fixture

使用 `.venv/Scripts/python.exe`：

```powershell
.venv/Scripts/python.exe -m unittest discover -s tools -p 'test_native_normal_close.py' -v
.venv/Scripts/python.exe -m unittest discover -s tools -p 'test_stop_passthrough_session.py' -v
```

当前21+17项通过：包括逐 owner 顺序、中间恢复快照拒绝、缺失/旧报告、FILETIME
变化、同一内核句柄等待、控制台无证明、退出0伴报告、报告读取失败、超时、MC
身份改变和保存超时。全部是 fixture，不发送真实输入、不结束真实进程。

## 主线程实际验收步骤

先备份当前 profile，重新盘点真实身份／模块哈希。游戏输入只由主线程控制。

1. 启动桌面 UI，确认原生选人和真实 MC 背景；用 UI 的停止操作。查看新增生产
   evidence，要求四 owner 严格恢复、WM_CLOSE／原生析构、精确 pause（若需要）、
   实际退出0、无本次匹配报告、MC 实际保存退出；不使用旧 verifier 替生产操作。
2. UI 再次启动，进入英雄，实际移动／射击和一个技能结束后，用 UI 重启。
   确认旧 PID 真正退出，再产生一套新 PID／六个唯一模块；恢复普通攻击和可见融合。
3. 在已保存的受控世界中验证 MC 来源结束后的原生正常 stop：若 owner 无法恢复，
   如实保留失败，禁止强杀或以它为成功重启。部分启动、报告缺失亦保持失败。
4. 可单独运行 `tools/stop_passthrough_session.py --keep-minecraft` 测 MC 保留路径，
   确认 MC PID／创建时间未变，再由主线程正常冷启动原生；不能把默认 Stop 测试
   与保留 MC 的测试混为一项。

备份：`~/.universal-modder/backups/normal-session-stop-20261024/`，保存任务入口
stop 脚本、已有测试及未改动验证器和 manifest；未删除任何既有脏文件或证据。
原生 TIMER 写坏来源、未知 Loop Exit 仍是独立开放项，本接线不宣称修好。
