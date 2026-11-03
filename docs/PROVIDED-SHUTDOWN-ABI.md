# 提供插件的关停返回值修复 — 2026-10-23

本项修复已安装，并通过两次冷启动后的正常关闭验证。它只修复已经证明的
关停 ABI 错误；原生 TIMER 通知生命周期、谁触发主循环退出、偶发猎空
拳头仍是独立开放问题，不能据此宣称长期运行完全稳定。

## 问题和证据

最新旧会话27304的实际报告为执行访问异常0xc0000005、原生RVA825346；
退出码虽为0，仍是实际异常。报告与小转储已按PID、创建时间和应用路径匹配，
证据位于 research/continuous-20261023/shutdown-abi-readonly-audit/。

实际运行代码80efa0先调用System接口虚表slot4(+0x20)，把非零返回值
交给原生池释放；825346会向该指针首qword写空闲链。
原提供插件的PrometheusSystem虚表RVA271820，其slot4数据RVA271840
指向38a00。这个空操作只ret0，不设置RAX，PDB和源码声明却是void。
本次27304的RDI正是该插件虚表地址，因不确定返回值进入释放逻辑而异常。

实际二进制及固定源码还证明：该System实例为CRT new/malloc分配的0x138
单例，注册进当前EntityAdmin；原deallocate故意不析构/不释放。因此不能
改成返回this并交给原生池，也不能任意跳过原生free。

固定作者源码commit：
ad1fea7e6c04c9959c7115cb8ecd9c79c93c1ccb，相关来源与实际RVA、实例、
单例、EA、分配链和新27304报告均保存在audit.json及exit-source.json。

## 最窄修复与安装

仅把该精确类型的slot4指针从38a00改指向同一类型已有的3ef20：
该目标为xor eax,eax;ret，明确返回空指针，保留原先空操作语义。
现存DIR64重定位不变，ASLR后指向实际pluginBase+3ef20。
其他虚表项、共享38a00函数代码、PDB、全部模块代码均未修改。

实际DLL只差2字节：

| 文件身份 | SHA256 |
| --- | --- |
| 原inject.dll | 12a0cf4a105f3e60b36aa9f0186cf82abcd0ab2e6e4354047004ec17a94e2e17 |
| 修复inject.dll | c82f8cea31aca0da8e1cd0b2b4d1a6a1c671a86fa4f1a52120985cbeec2ff2d6 |
| 未修改prometheus.pdb | 6947622a4a38a1b5f75961e65de9ff89a05d9a461e7a7293a837a73cf306159b |

原生EXE哈希仍为AGENTS规定的f73a747b…，未修改。
compositor40/body26/gate9/emission15/bootstrap10/localhero1以及guest JAR
也未变；仍为原六个唯一适配所有者，不新增回调或临时运行时接口覆盖。

工具：tools/repair_provided_shutdown_abi.py。它先核对完整DLL/PDB哈希、
GUID/age、布局、精确符号/目标、零返回代码及该slot的DIR64重定位。
只允许专用私有备份目录，安装拒绝运行中的目标，独占打开实际DLL后重读
校验，单slot写入、刷新和完整回读；短写/刷新/回读失败会在同一句柄内
恢复原slot并验证，回滚失败则明确禁止启动。

私有原文件、修复候选、manifest和安装回执：
<USERPROFILE>/.universal-modder/backups/provided-shutdown-abi-20261023/。
安装前26220已使用现有严格恢复流程停机；未覆盖加载中的DLL。
这个冷态兼容修复在适配器正常恢复后仍有效，不存在“恢复后再次使用坏返回值”
的临时补丁空档。恢复原文件也只能在完整停机后通过同一工具--restore执行。

## 实际验收，成功和失败分开

- 14项工具测试通过，包括真实私有DLL两字节差异、ASLR重定位、未知身份拒绝、
  运行中拒绝、内容竞争、短写、刷新失败、读回不符、回滚失败和幂等。
- 8544初轮：实际ASLR指针与当前EA单例正确，四适配器恢复全部通过；
  WM_CLOSE后原生渲染窗口消失，但20秒进程退出等待超时。本轮保留失败，
  不回写成成功。实际截图已查看，显示Process exit initiazed:0、shutdown
  和“请按任意键继续”。
- 原作者dllmain.cpp的atexit在exit_normal为假时调用system("pause")；
  普通WM_CLOSE不会设置该标志。菜单Exit则直接CRT exit(0)，可能绕过原生
  析构，不能拿它替代这项修复验收。
- 新验证器 tools/verify_provided_shutdown_abi.py 仍使用WM_CLOSE走真实析构。
  如遇原作者pause，只有在确认渲染窗口已消失、PID/创建/路径不变、
  AttachConsole的进程列表包含该PID、实际CONOUT同时出现退出/shutdown/
  任意键等待提示时，才向该精确CONIN发送一组Return。没有全局键盘输入、
  写进程内存或强制结束。缺少证据仍按失败保留。
- 19496实际通过：八组猎空Recall/Pulse/近战/装填/Blink组合后真实开火，
  各目标20→13.999996；三英雄Pharah/Mercy/DVa×四维度12项自然续充
  约4.85–5.13points/s，无F11/授能；恢复后slot仍正确，正常WM_CLOSE、
  精确console确认、实际退出0且无本次匹配错误报告。
- 2424第二次冷启动通过：从桌面启动器实际点击启动到原生选人，关闭UI后
  游戏保留；同样严格恢复、正常WM_CLOSE、精确console确认、实际退出0且
  无本次匹配错误报告。未强制结束。

证据目录：research/continuous-20261023/ 的 abi-close-picker（超时失败）、
abi-tracer-stress、abi-charge-four-worlds、abi-close-after-combat、
abi-close-second-cold、ui-close-gameplay、ui-fixed-entry-accepted。
截图已经实际查看。自然充能回归不等于DVa驾驶员HUD/机甲补齐。

## 下一步

保留该修复及私有原件。若再出现异常，继续匹配本次身份和完整调用链，
不能因同样退出0就推断“仍是关停ABI”。TIMER的分配/排队/释放和不明
Loop Exit Scheduled原因继续有界调查；其他稳定的防御英雄缺口可并行推进。

