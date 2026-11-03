# 猎空 Recall 空历史收尾修复 — 2026-10-23

当前验收：**修复前真实复现已经通过；主世界、地狱、末地、暮色森林均已完成
修复后空历史取消→真实普攻→正常回溯→真实普攻的完整实测，并已清理夹具。**
这不是原生 TIMER 故障、
不明 Loop Exit 或历史偶发“拳头/武器消失”的全部根因修复。

## 已证明的故障链

`NativeRecallRuntime.begin` 已通过当前 owner/world/source/model、真实原生
Begin、新鲜度、去重及无其他活动 Recall 的检查后，会查询 Begin 时刻以前的
MC 历史。原实现遇到空候选只更新 lastBegin、增加 refused，然后返回。

客户端已经记下本次真实原生施法，动画 End 后仍会调用 finish，但 MC 没有
Pending，finish 再次拒绝。原生逻辑所有者会按照真实动画 End 结束 root31，
随后等待本次 phase2/3 回执才结束 history1；相同世界没有回执时，history1
持续占用原生武器状态，不能开火。

空候选包括完全没有采样，以及现存采样全晚于原生 Begin 的情况。此处没有
把“按过 E”或看到动画当成技能准入。实测同时记录真实 root31 Begin/End、
原生动画 End、MC 实际准入 wall、服务器状态、原生 history1、计数和真实伤害。

## 最小改动和权限边界

只在上述原有准入检查全部通过后的空候选分支，产生精确本次的
`Completion(scope, begin, now, false)`。没有 MC 回溯候选就取消 MC 玩法，
仍保留给原生的收尾回执。

现有客户端继续等待真实原生 End，再传 phase3。现有原生逻辑线程中的
completion 所有者按本次回执结束 history1；phase3 不设置 ammoDue。
没有新增 native hook、脚本调用线程或回调所有者，也没有盲停其他节点。
本项未修改原生生产 completion 代码或 NativeRecallController 的权限规则。

该 MC 空历史分支不建立 Pending、不授予保护、不移动或治疗玩家，也不请求
适配器补弹。错误身份、过期、重复或活动施法期间的 Begin 拒绝不会生成
可取消另一技能的 terminal。不同确定身份仍按既有 session 规则隔离。

**原生弹药与适配器补弹必须分开观察。**修复前真实测试中，原脚本自行把
32 发变为40发，适配器 recallAmmoRestored 始终为0。因此测试不能把任何
弹量上升都判为适配器授弹，也不能强制要求空历史前后总弹量不变。
phase3 验收检查适配器补弹计数不增长，同时记录原生实际弹量。正常 phase2
回溯要求最终实际40发；原生已经补满时适配器可以是 no-op，确实需要补弹
时才增加一次，不允许重复补弹。

## 窄复现入口

`POST /combat/test/recall-empty-history` 只在以下条件满足时清空并暂停
当前 Recall Scope 的 MC 历史采样固定500ms：

- 配置明确启用 twilightTrial，存档名以 `Overwatch Twilight Switch ` 开头；
- 集成单人服务器，调用在服务器线程，当前玩家存活且为创造模式；
- 捕获的 owner/world/source/model 与当前已确认的猎空 session 完全一致；
- 当前没有活动 MC Recall，也没有尚未结束的同类暂停。

入口不接受外部时长、不伪造 native Begin/End、不直接调用 begin/finish、
不修改原生状态或 lastBegin，不清理其他英雄的技能历史。暂停使用单调时钟，
500ms 后自动恢复采样；重置、停服和测试清理会清除暂停。重复请求不会
延长已生效的暂停，普通游玩不会自动启用该入口。

HTTP202 只表示 queued。实测必须先核对当前 Scope 的 historyTestPaused、
零采样和截止时间，再由已经启动并聚焦的唯一 UM WinDrive stdin 进程发 E。
Runtime 的 lastBeginWall 必须处于 `[historyTestUntil-500, historyTestUntil)`，
且 lastBeginTick 与观察到的真实原生 Begin 一致。错过窗口或 E 未被准入
不能记为复现或通过。

## 修复前实际证据

私有目录：`research/recall-empty-history-20261023/before-actual-ammo/`。

该轮 native2016（创建1792736299.9128425）/ MC28956
（创建1792736282.5474803），诊断 baseline JAR 为
`d864e0f369eb8d09435c218d85ca20a67495df4d70fbaa1ae3cdc0a91e58f8ef`。
这是加入窄 fixture 和诊断、但保留旧空历史拒绝行为的受控构建，不能与固定版混淆。

- 暂停截止1792736826801ms；实际 MC/native Begin 为19312，wall 为
  1792736826367ms，确实位于500ms内。
- MC completionPhase0、completionBegin0；真实动画和 root31 已 End，
  body recallCompleted1→2，但 recallHistoryCompleted0→0，history1 仍 active。
- MC HP2→2，实际位置不变；原生弹药32→40，adapter recallAmmoRestored0→0。
- 不换掉失败原生 pawn，随后真实左键：MC 目标20→20，原生 factory16→16，
  弹药没有因普攻减少，真实武器被锁，测试对象已清理。

该轮 `passed=true/featurePassed=false/cleaned=true` 的含义是**成功复现旧故障**，
不是玩法通过。保存了完整原生状态/图和截图。实际截图已查看：原生双枪仍在，
技能 HUD 呈红色锁定，不能据此把这个缺口等同于历史“拳头”表现。

## 修复后主世界完整通过

私有目录：`research/recall-empty-history-20261023/fixed-overworld-v3/`。

该轮 native22116（创建1792736907.0493207）/ MC19532
（创建1792736889.7193532），实际固定 JAR 为
`8ea5e757a77aa57451e633482e9aaf99c62fb8ced76398f56397b97e752d139e`。
这些历史身份仅用于解释本次证据，不作为下次运行目标。

空历史取消：

- 实际 Begin19280、wall1792737199850ms，暂停截止1792737200309ms；
  本次 MC/native Begin 确实在固定窗口内。
- 真实动画与 root31 End，phase3 对应同一 Begin；原生 root 和 history
  完成计数各增加一次，history1 确实变为 inactive。
- MC HP2→2、位置不变；原生弹药32→32，适配器补弹0→0。
- 随后真实普攻：目标20→15.199997，factory48→56，原生实际耗弹，
  不是用快照或动画代替伤害。

随后正常 Recall：

- 没有授能、改冷却或伪造历史；等待原生12秒冷却并积累真实健康位置历史，
  实际移动后由夹具受伤到2HP，再按一次真实 E。
- 本次 Begin36240，真实 End 后 phase2；实际 MC 回到健康历史位置，
  HP2→20、原生弹药16→40；root/history 各完成一次，适配器补弹0→1。
- 结束后再次真实普攻：目标20→15.199997，factory64→72。
- 整轮 passed=true、featurePassed=true、cleaned=true，sourceSuspensions=[]。

实际 before/after、空历史后的开火图和正常回溯/开火图已查看，原生双枪、
HUD 和真实 MC 床岩测试场/靶可见，满弹与耗弹画面与数值一致。截图是可见
表现证据；真实伤害和生命周期由上述独立状态与战斗数据证明。

## 保留的失败与观察限制

- `before/`：创建时间参数经过 PowerShell 未加引号的数值格式化，精确身份
  检查失败，没有有效游戏测试。必须给 CLI 创建时间使用带引号的完整精度值。
- `before-quoted-time/`：真实复现到了 history1 占用，但旧测试误以为
  原生弹药必须保持32，遇到原脚本32→40而失败。后来对同一未换人的失败
  pawn 补测普攻仍0伤害，证据另外保留，不把初次失败改写为成功。
- `fixed-overworld/` 与 `fixed-overworld-v2/`：各自空历史取消和真实普攻局部
  通过；后续正常 Recall 准备阶段遇到 HTTP hostGeneration0，整轮仍保留失败。
  v2 保存了实际 mismatch：共享内存仍为原正数身份，HTTP 暂时为未知0。
  不能凭这条数据无证据归因于用户、GPU 或某个原生技能。
- 实测脚本对未知 HTTP generation0 仅在相同共享内存/进程身份下有界观察
  最多250ms，期间不发送输入并记录 sourceSuspensions；出现正数的外来身份
  立即失败。没有把0转换成新世界权限。主世界v3 没有发生这种暂停。

## 四维度完整回归

除上述主世界v3外，`fixed-nether/`、`fixed-end/`、`fixed-twilight/` 的
result.json 均为 passed=true、featurePassed=true、cleaned=true；
`remaining-worlds.json` 记录三个真实维度的增量调用和实际退出0。
同一 native22116/MC19532、固定 JAR8ea5e757…，每轮都重新确认当前维度和
新猎空模型的完整 Scope，没有把旧世界或旧模型事件继续授权到新世界。

| 实际维度 | 空历史真实 Begin | 随后正常 Recall Begin | history 完成计数，空取消前→后→正常后 | 适配器补弹计数，同样三时点 |
| --- | --- | --- | --- | --- |
| 主世界 | 19280 | 36240 | 2→3→4 | 0→0→1 |
| 地狱 | 19216 | 36208 | 4→5→6 | 1→1→2 |
| 末地 | 19296 | 36272 | 6→7→8 | 2→2→3 |
| 暮色森林 | 19360 | 36320 | 8→9→10 | 3→3→4 |

四轮共同结果：

- 空历史实际 Begin 均在各自固定500ms窗口内；真实动画/root End后只发
  对应 Begin 的 phase3，root/history 各完成一次，history1 不再占用。
- 空取消均为 MC HP2→2、位置不变、原生弹药32→32，适配器补弹不增加；
  随后真实普攻均使 MC 目标20→15.199997并产生原生 factory与实际耗弹。
- 正常 Recall 均为自己的 phase2、实际历史位置回溯、HP2→20、弹药16→40，
  适配器确实补弹一次；结束后再次实际普攻均使目标20→15.199997。
- 每轮测试对象和暂停已清理。四维度实际 post-primary-normal 图像已查看，
  原生双枪/HUD与MC场景可见；末地原版龙血条也实际可见。

末地轮保存了一次 HTTP hostGeneration0 的独立观察：27.5879ms后恢复同一
正数身份，sourceSuspensions 明确记 inputSent=false，其间没有发输入。
这是有界未知状态观察，不是把身份校验放宽成通配，也不是来源间断或长期
稳定性已经根治的证明。前两轮失败仍按前节保留。

## 工具、备份与剩余验收

来源备份和初始哈希：
`research/recall-empty-history-20261023/backup.json` 及 `backup/`。
持续 stdin 实测工具：`tools/verify_recall_empty_history.py`。
现有 `NativeRecallHistoryCheck` 增加真正空候选和全为未来采样的检查；
原生 completion fixture 增加 phase3 等真实 End、精确身份/新鲜度拒绝、
只清理一次且不置 ammoDue，以及后续 phase2 正常路径的检查。

工具要求每次使用新的 research 输出目录，明确 mode=before 或 fixed，
并传入本次精确 PID/创建时间、存档和安装 JAR SHA。护栏还核对真实 Java
gameDir/运行参数、profile/JAR、TF 模组、原生 request 创建 FILETIME、
共享内存和当前模型；失败时先保存原生 pawn，不用换人或重启冒充修复。

后续待完成：超出本次控制场景的换人/中断组合回归、最终正常场景和独立
后台状态审计。其他尚未复现的锁枪或历史拳头问题继续单独追踪。
