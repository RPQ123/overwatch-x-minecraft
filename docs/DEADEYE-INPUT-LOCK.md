# 麦克雷确认射击后的移动与视角锁

2026-10-23收尾：用户已暂停持续开发。修改已统一编译、严格正常关停后冷部署，
当前guest928c338c…与compositor42包含本功能；不能继续按下文历史“尚未部署”理解。

三次真实测试的featurePassed、chargingPassed、nativeEndPassed、HInterruptPassed
均为true：确认开火到原生End的移动/视角锁、蓄力正常走动/转向、End后恢复和H中断
成立。live41-final1锁内19样本/920ms，MC与原生坐标/视角变化均0；真实蓄力走动
0.825m/转4.02049°，恢复后走动1.438m/转6.02791°，End漂移0。根线程实际查看
了final1两份原生武器、锁定标记及射击contact，不能以纯数据冒充全程画面复核。

整轮harness仍**未通过**，原始false结果保留：live41-first录像与清理失败；
live41-final1清理/两段录像成功，但最后H切选人首次Host pose stale即失败。
随后同PID/创建时间的只读25样本证实选人帧恢复、年龄1–8ms。harness仅对最终
选人等待添加有界HostPoseGap重试（12纯fixture通过），没有放宽150ms/身份门；
live42-final功能、清理、录像仍成功，但最终Guest body scope stale再次失败。
这是恢复后优先检查的准确生命周期/验收缺口，不能把featurePassed写成整轮passed，
也不能从单世界两次锁定外推四维度/所有中断通过。完整证据在
`research/deadeye-input-lock-20261023/`。实际生产锁定代码在上述测试后未再修改。

## 生命周期与实际修改

蓄力阶段仍能走动和转向。只有既有 NativeDeadeyeEvents 看到同一会话中新
root18 Begin、随后真实 fire44 事件，且既有准入/耗能成功，才进入 firing
阶段；该阶段持续到原生 root18 End。单枪 node69 End 不会提前解锁。
取消、换人、跨维度、失焦、菜单/暂停、来源或读取过期会拒绝当前控制证明。
150ms 新鲜度不因 IO 重试延长。中途绑定到已有 Q 仍只建立基线，不接管旧 fire。

两个端都执行限制：

- MC 键盘输入清除移动、跳跃、蹲下和飞行位；移动适配器清水平惯性，创造
  飞行清残余垂直速度。普通重力仍由 MC 处理，不把空中玩家悬停在世界里。
- 已有唯一 compositor 输入过滤器拒绝 WASD、空格、Ctrl、F6、Shift/左右
  Shift 的按下，以及鼠标位移；原来的数字/滚轮屏蔽保持。没有新全局 hook、
  第二输入所有者、相机内存写入、武器旧帧回放或额外脚本调用线程。
- key-up 放行，避免锁前按下的键留下粘键。H、ESC、F1、原生主射击和 RMB
  取消仍可用。现有 NativeDeadeyeFinish 的原生取消/恢复路线没有被替换。
- 翻滚剩余距离被消费，但保留原 Begin 基线；解锁后同一个仍活跃的 Begin
  不会补跑。普通 NativeMotor 已无累计位移队列，本轮不恢复旧累计运动。

输入过滤器只消费已有 render owner 发布的有界只读证明。每个观察帧重新
匹配原生当前麦克雷模型、原图022f脚本所有者、提供的 inject.dll PE 范围内
logger、真实 root18 活跃且 Begin 相等，以及 fire44 tick 不早于本次 Begin。
fire44 可以已经 End；持续锁由 root18 和同次 firing 准入决定。
读取失败、过期、模型/世界/MC源/host generation 不一致均不锁。

## 向后兼容和所需部署配对

不改变 OWPOSE01 的4096字节/v1外层身份，也不改变已有输入v2：

- 未使用 offset332 新增 `DEY1`（0x31594544）能力位。只有实际输入 hooks
  enabled、未 restored 时广告；旧40或已停止 producer 不提供有效能力。
- 新 HostPoseReader 保留旧 Pose 构造签名，缺少能力位时不启用此次锁。
- OWBODY01 仍是v1/256字节。176..231为可选 DEY1 扩展：flag/model、
  Begin、script、logger、原始观察时间和世界。宿主源/进程/代数继续使用
  原有头字段。inactive会清空证明；cap0或非原生第一人称的尾部全部保持0。
- 原 body26 解码源码只读取到 FLY1 的172字段，不校验176尾部。因此可
  保留现有 body26；新 compositor 自己解析可选尾部，不共享 C++对象 ABI。
- 旧40＋新guest：没有能力位、尾部保持原0，不会只冻结 MC而仍允许原生视角。
  新compositor＋旧guest：没有扩展，不锁，保持原有功能。
  **完整效果需要新compositor（拟41）与新guest共同冷部署。**

本子任务没有修改版本中心、stop SHA pin、已加载 DLL、安装 JAR 或当前
settings/profile。根线程需统一更新 compositor version选择、build脚本允许
版本列表、构建后严格恢复SHA pin和对应文档。body脚本通知所有权仍在既有
逻辑线程；本轮只读取，不把通知或动画调用移入渲染线程。

## 本轮专属验证

`tools/verify_deadeye_input_fixtures.ps1` 只在 research 输出隔离 exe/classes，
不构建生产 DLL/JAR、不发游戏输入。实际18步通过，证据在
research/deadeye-input-lock-20261023/fixtures-20261023-181202-470/result.json：

- 六个 C++ fixture 编译及运行：native fire/root End/旧事件与身份守卫、
  body兼容/尾部清理、移动键策略、仅本fixture进程的真实MinHook安装/恢复
  和消息队列、HostPose能力位、128帧数值ring。
- pose_observer 用 C++17/Wall/Wextra/Werror 做 syntax-only，未生成 DLL。
- 纯Java编译，Events、InputLock、Roll、HostPose四项检查通过：蓄力不锁、
  fire持有到Root End、150ms边界、跨世界/模型/源拒绝、原Begin不补跑、旧能力0。

最后边界复核还覆盖已 firing 后实际 root End、Ctrl/左右Ctrl/Shift/F6
keyup放行、ESC与RMB保留、absolute raw位移与RMB同包时归零位移但保留取消、
左右Ctrl实际GetAsyncKeyState过滤。普通重力保留是当前明确实现，空中纵向
位移并未冻结；根线程实测需同时覆盖锁前水平惯性和翻滚预算，确认解锁不补跑。

完整 MC client 编译、实际原生 Q 逐枪期间移动/视角锁、原生 End 后恢复、
取消/H/菜单/失焦、四维度和混合版本运行仍由根线程实测。以上 fixture
不能冒充完整游戏内验收；也不证明旧 TIMER、历史猎空拳头等根因已解决。

## 可选的手部数值取证

同一 compositor 源已接入 defense 子任务提供的 HandMaskTrace。默认关闭；
冷attach前存在 `research/enable-hand-mask-trace.txt` 才启用。此文件不由
本子任务创建。开启后记录最近128帧的数值：候选镜头、拒绝计数、手部组
开始/续组/depth变化、mask决定及实际是否提交合成；报告使用immutable快照。
未知镜头诊断仅增加同渲染线程上的只读stage查询，不改mask/渲染规则，不
增加GPU读回或旧图回放。诊断数据不是原生枪械存在与否的最终证明，需要
与实际原生/融合画面对照，且其性能应与默认关闭模式分开记录。

## 首轮真实验收脚本（尚未由子任务执行）

`tools/verify_deadeye_input_lock.py` 复用现有 Identity/PersistentDrive，要求
新鲜 PID、两个进程创建时间、已安装 guest SHA、一次性 evidence 目录和
`--profile-backed-up`。只接受模组齐全的隔离 Twilight Switch 存档，不新建
或载入用户存档；原生 client 必须为既有坐标2560×1440。只有开始时显式
focus，后续失焦直接停止，不自动重试换人或施法。

流程是空中可恢复地面 lane 的蓄力步行/转向与 RMB 取消，再启用创造飞行
后建真实12怪 crowd（该动作会清除 lane），实际确认开火期间注入 W、Shift、
Space、F6 和相对鼠标，检查150ms/原模型/原世界/原 root证明及真实 MC 位移、
原生摄像机 basis、原生坐标。之后验证原始 End、静止无补跑、重新步行转向
与实际普攻，再一轮实际 fire 后按 H，检查锁释放并保留原生选人界面。
诊断充能默认 typed lab grant，可显式选 F11；这不属于自然充能验收。

强制保存两个60fps视频及所有输入/样本/错误，视频退出成功且真实文件存在
才可通过脚本门；最终画面仍需根线程查看，脚本标记 `visualAcceptance`
为待审。五个纯字节/判据测试通过（`test_verify_deadeye_input_lock.py`），
没有运行该脚本的实际 Suite，也没有发送本轮游戏输入。四维度扩展不在这
个首轮脚本范围。

### live41-first：功能数据成立，整轮仍失败

根线程实际运行 `research/deadeye-input-lock-20261023/live41-first/result.json`：
`featurePassed`、`chargingPassed`、`nativeEndPassed`、`HInterruptPassed` 均为真。
303个样本中，实际确认开火输入区间有20个锁内样本、跨815ms；MC与原生
坐标的最大位移均0，MC与原生 yaw/pitch 最大变化也均0；DEY1原始观察证明
年龄16–71ms。蓄力期间实际地面走动0.824817m、原生转向4.022959°；原生
End后空闲最大漂移0。来源为MC5612、host generation67791441329065、
世界16712565632985609587；这些是该轮身份，不用于后续目标识别。

**该轮 `passed=false` 保留。** 独立失败包括：停在原生选人界面后cleanup
HTTP202只排队，因第一人称host guard未实际清理，`cleaned=false`；两段
录影命令都缺少窗口选择参数，工具退出1并报告需要exe/hwnd/title，没有
视频文件。坐标统计不能替代可见画面，不把此轮改记为完整通过。

测试脚本现已修复：只有已通过H中断的当前suite才在清理时用验证后的
麦克雷回到第一人称、等待当前scope，确认对象真实清空后H回选人；失败
pawn不自动替换、失焦不refocus。录影明确指定原生exe画面与当前MC PID
音频。9个纯fixture通过，新一轮实际复跑仍由根线程执行，旧结果不覆盖。

### live41-final1：功能与清理通过，最终选人观察过渡仍失败

根线程第二次实际执行记录在 `live41-final1/result.json`：功能四项仍为
真、`cleaned=true`、两段真实视频均退出0。19个锁内样本跨920ms，MC/原生
位置及各自yaw/pitch变化全部0；蓄力走动0.825000m/原生转4.020495°，
原生End后漂移0，恢复后能移动1.438057m/转6.027907°并实际普攻。
`two-attempt-review.json` 保存两轮指标与各原始结果SHA，旧结果未改。

整轮依然 `passed=false`：清理后最后H，已有4个过渡样本中的最后相机
frame174473停在wall1792752343431，最后成功样本观察年龄126ms，下一次
超过150ms即报 `Host pose stale`。原测试wait遇此异常会立刻退出，尚未
等待完既定3秒。它支持“某次切选人过渡内短暂停更”，尚不能仅凭此证明
持续故障。随后子任务对同PID15548/MC5612及创建时间做25次只读采样，
约2.43秒内pose持续推进、年龄1–8ms、原生第一人称为false、inputActive=0；
证据 `final1-readonly-state.json`。没有发送输入、重新聚焦或操作进程。

测试harness仅在清理后最终选人等待增加特定 `HostPoseGap` 的有界观察重试，
保留150ms新鲜度和全部身份条件，不重试来源/模型/维度错误；战斗中不放宽。
持续停更仍在原3秒deadline失败，12个纯fixture已通过。新一轮完整结果
尚待根线程复跑。两段contact已从真实视频导出并打开检查，画面可见原生
手部、锁标、MC目标和射击效果；稀疏contact不能替代最终选人及完整时序
的视频审查，因此没有将这一失败轮次改成成功。

### 2026-10-24：最终选人等待的body失鲜分类

只将结构、PID、非零generation/world和偶数seqlock均有效、时间不在未来的
过期body标记为GuestScopeExpired；仍拒绝使用该样本。harness核对既定MC
来源及guest/host/world完整身份后，仅在原先明确开启的最终选人观察等待中
重试。原3秒deadline不延长，不发送补键或重新聚焦；战斗默认立即失败。
未来时间、损坏格式、奇数序号、另一来源/世界不进入这一重试。Host未来
时间也改为不可重试的硬失败。生产body250ms和攻击/pose150ms门槛不变。

7个scope及14个harness fixture通过。真实整轮复测仍待融合画面恢复后执行，
不能将测试代码改善记为旧失败轮次通过。
