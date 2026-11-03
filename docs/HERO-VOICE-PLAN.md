# 全英雄语音分类与真实事件接入方案

2026-10-25。前两轮完成本地分类；第三轮按用户授权已实现并注册语音接线，`compileClientJava` 与离线素材检查通过，未开游戏、部署或联网下载。沿用原版 OW 负责英雄/手部/HUD、MC 负责世界/碰撞/保存的双进程路线。下文分类记录保留；当前实现、注册与验收边界见末节。

## 第二轮修订：直接语义阅读

按用户新要求，原 uncertain 7,511 条已逐英雄按至多150条/批直接阅读；另复核576条旧 skip 的状态/装弹候选，共66批、8,087个独立hash。每条决定有原文SHA256和批次，保存在 `research/voice-catalog-20261025/round2-decisions.json`；输入快照分别是 `round2-source.json` / `round2-extra-source.json`。新脚本 `tools/review_voice_catalog_round2.py` 仅重放这些判断，不调用模型/API或重新用关键词猜分类。`tools/classify_voice_catalog.py` 默认应用完整覆盖表；`--round-one` 才明确回到旧规则。

最终数量和体积以更新后的 summary 为准。击杀嘲讽/胜利感叹已按语义补入 kill，闲聊/自言自语补入 idle，新增 reload 和细分 status。空字幕仍保留 uncertain，不能将未知音频改叫 effort/skip 来达成小于10%的数字目标。

用户指定的新紧凑清单为 `research/voice-catalog-20261025/download.json`：核心项只有 `{hero,hash,url,event}`，reload/status/idle 额外标 `optional:true`。**可选只表示可以另行采集听辨，不表示已经实现播放触发。** 已有21人选人保留；主动 comm/求治疗缺UI生产者、D.Va机甲、attempt-only 成功喊话、未认证切歌等不进入核心清单。全英雄击杀核心候选依据已有 `(player,victim,actualLoss)` 伤害入口与MC真死亡，仍需新增通用归属账本，不能宣称当前 Genji-only 队列已覆盖全英雄。

SymmetraServer 已有真实构造物生命、传送门 `uses=6` 和使用递减，可加销毁/受击/次数回执；语音剩余次数7至10与当前MC实现不符，排除采集。TorbjornRuntime 的炮台 health 目前没有真实受击/升级接入，不能同样放行“炮台快碎/升级”等成功喊话；未领取护甲包则可读现有包的存续/年龄做提醒。

reload 必须接原版当前武器的真实装弹阶段/确认回执；本轮查到的客户端代码尚无通用 reload 事件生产者。弹药增加可能来自闪回、F11或补给，不能代替装弹证据。原生装弹音效可能已经播放，因此新增装弹素材只列可选，不能叠播整段 SFX。

status 分开记录 healed/frozen/electrocuted/controlled/knocked_back/burning/poisoned/damage_boosted 等；电击不等于眩晕，自然重生不等于被复活。可对应MC实际HP、冻结值、伤害来源、效果变化或已准入控制阶段；on_fire、碎片量、技能就绪等未有对应读数时继续关闭。idle 只允许审定独白，在真实非战斗/无输入空闲后可选播放，不用地图/模式对话充数。原生是否已经有同一痛叫/状态声仍需分进程收音检查；本轮没有新live证据。

## 交付和分类边界

- 入口：[classify_voice_catalog.py](../tools/classify_voice_catalog.py)。使用 `.venv/Scripts/python.exe tools/classify_voice_catalog.py`，没有网络代码；只写输出目录，只读私有资产清单与已存 MP3。
- 输入：[catalog.json](../research/voice-catalog-20261025/catalog.json)，21 英雄、11,361 个不同 hash。每条原始字段完整保留，新增 `event/confidence/reason`，以及版本、资产、下载、部署状态。
- 输出：[classified.json](../research/voice-catalog-20261025/classified.json)、[summary.json](../research/voice-catalog-20261025/summary.json)、[summary.md](../research/voice-catalog-20261025/summary.md)、[download-manifest.json](../research/voice-catalog-20261025/download-manifest.json)。逐英雄逐事件计数、下载数量和体积在 summary；下载清单不是部署许可。
- `confidence` 表示对分类决定的把握，不表示音频版本、语言或干净程度。`uncertain` 的高置信度表示能确定“文字证据不足”。空字幕不猜痛叫/死亡/起跳；笑声/喘息仅归低置信度 effort。技能标签明确但无字的机械/发声混合素材不自动下载。
- 第二轮直接语义决定的采集阈值为 >=0.85，另受真实信号/可选类别/语言检查约束；已由私有 manifest 的 SHA256 核实存在的 MP3 不重复建议下载。idle/reload/status 仅列可选；effort、uncertain、skip 不采集。按 **25,000 bytes/条** 估算，MB 为十进制，同时给 MiB；不包含转换后的 OGG/容器开销。
- 目录没有版本/录音日期字段。有明确后期英雄、2019/202x、皮肤、地图、模式、语音视角或现有技能版本不符证据的排除；无标注项仍为 `unverified_no_catalog_version_metadata`。**无法仅凭台词/hash/顺序保证所有候选录音早于 1.30。** 没有把“没有发现后期标记”当作年代认证。
- “重生E”、女武神、烈箭、光子屏障等另标现有技能不符，不武断声称它们全是 1.30 之后才出现。原版 beta 的天使大招重生、秩序之光大招传送面板，与后来的技能位置不可混用。
- 固定项目来源 ID 优先保留已研究的选人/技能对应，不把未知 taunt 硬归成技能。目录里只匹配到 17 条已装选人原始 hash；麦克雷、黑百合、查莉娅的已装中文选人 hash 不在本目录，堡垒已装选人来自另一站。第二轮另有选人字幕变体归类，因此17是既有来源hash匹配数，不再等同于select分类总数；已有21人选人仍完整，不需重装。
- 所有条目 `deployment_allowed=false`。待人工校验录音语言、版本、本人/友方/敌方声道、是否含别人台词及 SFX 后，才可进入私有播放库。`uncertain` 是必须复核的待办，不代表分类器补齐了相应资产。

## 全部事件的真实信号与准入

“可接”表示源码已有真实信号或 MC 权威事件可以加监听；不是本轮已接线或已完成听测。具体英雄仍看下一表。

| 事件 | 真正来源与接法 | 禁止误触发、限制和建议节流 |
|---|---|---|
| select | 保留 `EarlyChineseVoices` + `HeroSelectCalloutGate`；原生 source/hero 变化、真实第一人称确认、原生前台、MC 活玩家等满足后等 1000ms | 已有唯一所有者；悬停、H 同英雄返回、维度/模型重绑、复活均不重播；失焦/取消等待即撤销 |
| ult_cast | 使用各英雄已准入的原生新 Begin tick、实际部署/发射回执或已认证的 Active 上升沿；施放确认与效果成功分开命名 | 首样本只基线；Active 每帧不是新事件；End 只结束窗口和重置下轮资格，不再喊一次；充能归零、Q 键、固定持续时间均不能证明施放 |
| ult_ready | `ALL-HERO-CHARGE` 已有 21 人真实 charge/cost；源氏用 `NativeUltimateController.charge/cost`，其余用 `NativeMeterReader`/`NativeChargeController` 的带身份快照 | 校验有限值和正 cost；同一身份从低于满值跨到满值才发一次；首读就是满、重连、跨维度、读失败后恢复均只基线。读取不增加第二个计量写入者；现有 status 不是独立事件 API |
| ult_charge | 同一 meter 的实际百分比；字幕“快好了”与“还在充能”分为 `charge_stage=near/charging` | 默认主动查询才说；可选 near 一次穿越 90% 的项目策略，注明不是原版阈值。普通充能句不可反复每 1% 播，建议 >=15s；完整百分比播报无现成数字拼接，不合成语音 |
| ability:* | 各 controller 的新 tick/边沿，或对应 server 已接受的动作/部署/命中回执；两者使用同一个 cast token | 持续光束/自疗/举盾只在真实开始边沿；预览、搜索、失败尝试不是技能成功；子弹/炮台每次攻击不可重复技能施放声。不能直接读取 Shift/E/右键播放 |
| kill | 新增 `HeroVoiceRuntime.AFTER_DEATH`；真正死亡的 LivingEntity，其 `DamageSource.getAttacker()` 是绑定的单人玩家 | **MC 适配，全英雄通用**。没有消费 `NativeEliminationRuntime.poll()`，原源氏重置队列保留。按 victim UUID 去重，卸载/移除、他人击杀不算；宠物/环境延迟归功未扩展 |
| multikill | 对上述真实归属击杀另计窗口/本命累计 | 原版没有现成 MC 多杀评分。“多杀”短窗与“连杀”本命累计分开；窗口/门槛需作为项目策略声明。已有通用击杀通知之前不可接，不能按受击次数/命中总数推断 |
| pain | MC 服务器真正的玩家 HP/有效伤害损失；复用 `GuestMod` 已有 `ServerLivingEntityEvents.AFTER_DAMAGE` 监听位置设计新增旁路通知 | ALLOW_DAMAGE 是尝试，不是损血；格挡、护盾、无敌、创造模式均不假喊。致死伤优先 death，建议 1.5–2s 冷却；已有监听不得覆盖 |
| death | MC 服务器 `AFTER_DEATH` 的本地玩家实体，保留死亡前 source/hero/world/model 和玩家身份 | 与生命世代去重；每次死亡一次，不从黑屏/无 player 推断；fall 变体仅匹配实际致死坠落，普通死亡不能随机到坠崖音。死亡界面的 inputActive 例外需另审 |
| respawn | MC 服务器真实重生成功且玩家重新存活的回执（新增 AFTER_RESPAWN 类监听，签名以本地 Fabric 依赖为准） | 必须有前一死亡世代；不能由模型替换、世界切换、满血、闪回、冰箱结束推断。“我回来了”单独字幕不足以区分这些场景 |
| low_health | MC 权威玩家实际 HP/maxHP；建议 <=25% 入、>=40% 出的迟滞 | 这是项目阈值；存活且真的低血量，每次低血周期一次，>=15s。先确认原生 HP 同步是否也产生原版喘息。创造无敌不制造损血 |
| healing_request | 显式交流轮盘“需要治疗”请求，或经用户同意的真实低血边沿策略 | 与 low_health 分开；“到我这里治疗”是给别人治疗，不可归求治疗。目前没有通用交流事件生产者 |
| comm | 新增项目主动交流动作 hello/thanks/group_up/acknowledge 等；只在确认动作时生成事件 | 这类按键本身就是交流动作，可作为真实交流请求；不同于用技能按键猜施放。当前未实现交流轮盘；不能把战斗对话/可购买语音全自动当 idle |
| jump | MC 实际起跳，结合上一帧 grounded、正向跳跃起速与原生/MC 输入准入；更好是在真实 `jump()` 成功回执处发一次 | `HostMovementMixin` 的 jumping 位只是意图；游泳上浮、创造飞行、下落、击退、被弹起和连按 Space 不算起跳。需旁路事件钩子，默认 >=1.5s |
| effort | 只有明确到近战/攀爬/负重等真实动作的听测素材才接对应动作开始 | 当前“哈哈/喘气/空白”不能判断具体动作；低置信度不自动接、不轮询随机播放 |
| idle | 有可靠待机标记、身份稳定、玩家存活、无菜单、无施放/受伤/战斗且实际无输入 >=45–60s 时，可设计空闲事件 | 本目录暂未可靠识别 idle，默认关闭；计时只能判断空闲，不能把名言/地图对话变成待机台词 |
| skip / uncertain | 不生成播放事件 | skip 保留原因；uncertain 保留供听测/版本复核，不当作“其他随机台词”池 |

21 人的 meter 已被本机历史实测，不等于 21 人大招 Active/End 都能读。`NativeChargeController.skillGate/requiresSkills` 当前只覆盖部分英雄；它给其它英雄的 `active=false` 不是“没有施放”的认证。新模块的施放窗口必须从其真实 controller/server 读取，不能只看通用 charge.status。

ready 应保留“本次充能周期已播”锁存；浮点误差或一次重读不能重新武装。真实消耗或连续可靠样本降到明显低于满值才开启下一周期，身份变化则重新基线且不补播；用原始 charge/cost，不能从整数 HUD 百分比 OCR 判定满能量。

## 按英雄核对已有节点与不能冒充的成功

源码基准包括 `HeroClientModules`/`HeroServerModules` 注册的八个模块；这些不能因类名没有 Controller 后缀而漏查。下表“待验收”一律不声称本轮或既有记录已验证完整技能。所有节点是当前源码声明，运行时仍须原有绑定和身份校验通过。

| 英雄 | 可以复用的信号 | 仍不能接成“成功喊话”的条件 |
|---|---|---|
| Genji | `NativeUltimateController` Dragonblade Begin17 及 timer End；`NativeDashController` 真疾风击开始、`NativeDeflectController` deflect tick/active；现击杀账本 | Q 现由 `GenjiUltimateVoice` 播，不再加一层；已有中文/日语等权变体授权保留；技能语气声仍须确认类别 |
| McCree | `NativeDeadeyeController` 已有 Q；`NativeFlashbangRuntime` 实际 E；`NativeRollController` 实际翻滚 | `MccreeVoice` 已负责 E/Q；勿读 F11 授能当 Q。新版磁雷台词与旧闪光弹不混用 |
| Pharah | `EarlyChineseVoices` 已对 barrage node12 Begin；现 flight/hover/concussive 控制器的已准入起始回执 | Q 已有唯一喊话；推进音效不等于中文技能喊话。持续喷气不能每帧说“起飞” |
| Reaper | `NativeReaperRuntime.view.begin`；`NativeShadowRuntime.receipt.phase==2` 的已确认抵达；Wraith 真边沿 | Q 与传送当前已有语音。Q 动画禁用正常输入，必须保留现有已准入服务端阶段例外；通用前台门控不能吞掉该 Q |
| Soldier76 | 实际 visor 与 ultimate 阶段；`NativeBioticRuntime.view.nativeTick`；现 sprint/helix 真事件 | 目镜/生物力场现已有语音，不能与草稿并播；“战术目镜准备就绪”是 ready |
| Tracer | `NativePulseRuntime.view.nativeTick`；`NativeBlinkController` actionTick/captures；`NativeRecallController` 真施放 | 炸弹现已有语音；“我回来了”未有类别时不硬归复活或闪回；闪现机械声不得重复覆盖原音 |
| Bastion | `NativeSkillReader` recon/sentry/tank 互斥形态变化，tank 新进入；`NativeSustainController` 自修复阶段 | 转换/冲突/空状态不算坦克开始；目录大量空白不能推选人或大招，现选人 AA64 继续保留 |
| Hanzo | `NativeHanzoSkillController` graph00b9 scatter26、dragon76 的新 tick | 新读取只基线；龙击/散射 MC 实现代码就绪的实测状态看 TAKEOVER；音波箭需 `HanzoSonicArrowRuntime` 的实际生效回执；不换成烈箭 |
| Junkrat | `NativeJunkratController` graph022b volley31、096a throw12、09ba throw7；MC 成功布置雷/夹可另发成功事件 | 遥控引爆未校准；没有可靠 RIP-Tire 施放/结束来源，不用 Q 键播轮胎喊话 |
| Mei | `NativeMeiSkillController` 0622 preview2→confirm19；064a volley10；`NativeSustainController` 冰箱 heal30 | 冰墙喊话等真正 MC 放置成功后，不能在预览播；暴雪投掷可由 volley 新 tick 确认；喷雾冻住、冰箱结束和复活分开 |
| Torbjorn | `NativeTorbjornController` 00f4 anim29 End + ghost22 后实际 MC deploy；01cc throw5；原生 core 的21/30/19/20/计时阶段 | 旧交接的“节点未接”已被当前源码推进，但不因此声称实测通过。炮台放置用 MC 适配成功回执，隐藏 OW 地面原版 commit 仍未见；护甲每个领取提醒与 throw 分开 |
| Widowmaker | `NativeGrappleController` fire61+window57、venom throw1/cast24；`NativeInfraSightController` infraAnimation6/effect13/timer10/ultimate18 | 钩索空放与命中后拉动分开；“诡雷被触发”若是受害者咳嗽不可接成投掷喊话；红外 Q 新阶段可新增，现无中文 Q 所有者 |
| Mercy | `MercyClient` staff006b heal7/boost19 的真实通道边沿；guardian006e search25、resurrect00ca search36/wait40 | `MercyServer` 明写复活、飞行只有 attempt/no commit；不能用搜索成功次数播“英雄不朽”或“已复活”。本 beta 大招重生不是后期 E |
| Zenyatta | `ZenyattaClient` harmony02f3 search46、discord0176 search41、transcendence017b windup19 | `ZenyattaServer` 标明 attempt only，未见 health17/Aura30/protection；不能把起手候选当已进入圣，更不能随机套低血/治疗成功语音 |
| Reinhardt | `ReinhardtClient` barrier0095 Pet58；charge007d anim110+movement6；MC 举盾/移动接受回执 | fire00e2 volley3、shatter00be shockwave1 目前记候选；优先等实际效果阶段认证。“屏障快碎”需要盾耐久，MC 当前屏障没有该耐久 |
| Zarya | `ZaryaClient` self0244 aura15、projected025c search24/aura43、graviton025f volley2；MC 自盾/重力效果实际接受回执 | 投射搜索不等于成功保护别人；能量与原版尚未同步，不能播能量满/增伤归功句。当前目录未找到可确认的中文施放台词，不能用“重力喷涌准备好了”替代 |
| Roadhog | `RoadhogClient/Server` 01c8 cast11/search19 的真链钩、0240 heal23、01c6 wholeHog37；`qCasts/hookCasts/healCasts` 及实际阶段 | 钩命中、拉动和投钩分开；node21 伤害未进入，不用钩伤害喊话冒充；Q 要首次 token，不能每颗弹丸播放 |
| D.Va | `DVaClient` 02b8 firing12；026a attempt41、`callMechAttempts` | **只有驾驶员；Q41 未解决前置、无机甲 commit**。自爆、矩阵、推进器、机甲激活/召回成功都不可接；400/400 满能量只证明驾驶员计量，不证明机甲可用 |
| Symmetra | `SymmetraClient/Server` 017e preview32/ghost35、0169 preview42/ghost74，结合 MC `confirmPlacement` 的实际对象创建 | 不能按 confirmPlacement 的 LMB 请求直接播放“已上线”；护盾01c3 search27 仅尝试，光束 serverOnly16/89/107 未执行。没有成功回执就不播护盾成功或传送门上线；不用新版本屏障大招 |
| Lucio | `LucioClient/Server` 0277 ampCast6/window11、073a barrier0；实际 barrierCasts/shieldGrants | 0266 songCommit3 只认证变量提交，歌曲 HEAL/SPEED 语义未校准且保持 UNKNOWN，**不能播“加速/治疗曲”**；音爆65只有动作候选，28/29未执行；滑墙无认证节点 |

## 原版是否已经发声：现有证据及双声约束

本轮不开游戏，不能新确认所有原生语音输出。静态读码只能证明“哪些 MC 播放器已存在/哪些原生阶段可读”；图中的 SoundPlay 或音频资产存在也不能证明当前 offline 场景实际听到。用户第三轮明确要求接 MC 生命/起跳事件，现已接入；这项授权不等于已证明原版无同类声音。

1. [EARLY-CHINESE-VOICE.md](EARLY-CHINESE-VOICE.md) 记录过本机 21 人选人及 Genji/McCree/Pharah 对应录音的实际混音相关性；另有约185秒原生单进程收音未检测到语音。这只是历史样本范围内的未检出，不是所有英雄/受伤/跳跃/死亡都无原声。本轮没有重用其中 PID 作为当前进程证据。
2. 现存 MC 播放所有者共三处：`EarlyChineseVoices`（21 select、Pharah Q、Soldier76 Q/biotic、Tracer Q、Reaper Q/shadow）、`GenjiUltimateVoice`（由 `NativeUltimateController` 调用）、`MccreeVoice`（E/Q）。已有 gate 的基线、身份、时效和数量日志必须保留。新增服务默认屏蔽上述 hero/event，不双注册。
3. 第三轮已将三处旧播放器与新事件统一经过 `HeroVoiceChannel.play()`。全部在 MC 客户端线程仲裁，只停止总线自己持有的声音；高优先级中断低优先级，其他忙时丢弃。旧素材、gate 和源氏中/日语等权选择保留，新服务屏蔽同 hero/event，不用 `.status.playing` 猜所有权。
4. 原生手部、移动、施法 SFX 已随原版保留。[PHARAH-BARRAGE.md](PHARAH-BARRAGE.md) 另有 MC 历史混合录音循环和喊话时 ducking，循环不是干净原音分轨。不能再下载整段技能视频声当干净台词；不能全局静音 SFX、stop-all 或剪掉武器声来假装没有双声。
5. 逐英雄/事件做短的 OW 进程独立收音和 MC 进程独立收音，事件前后各留缓冲；保存事件 token、两个声轨、录音 SHA256、相关性/时间轴和是否重叠。VAD 无检出不足以排除短痛叫/非语言声；还要与对应素材做相关性并实际听辨。发现原生已播同一语音则让原生独占；确需中文替换时，只抑制该条原生语音，保留其它 SFX，再做混音验收。
6. pain/jump 是高重叠风险：原生身体随 MC 高度/生命同步可能已触发对应声音；当前没有逐事件无原声证据，`/combat.heroVoice.nativeOverlapVerified=false`。若发现原生已经播对应台词，用 `-Dowmc.heroVoiceNativeOwned=mei:pain,genji:jump` 或全英雄 `pain,jump` 排除新入口；effort 未接。验证脚本按用户要求仅验 MC 声轨，不据此宣称 OW/MC 无双声。

## 第三轮：已实现的私有素材与调度

入口 [HeroVoiceEvents.java](../guest/src/client/java/lab/owmcguest/HeroVoiceEvents.java)，默认开启；`-Dowmc.heroVoices=false` 关闭新事件，已有选人/施法播放器保留。共享改动共七个文件，每处标记“语音挂接”：`GuestMod`、`WorldFrameExporter`、`NativeSessionGuard`、`NativeDashTravelMixin`、`EarlyChineseVoices`、`MccreeVoice`、`GenjiUltimateVoice`。没有修改技能 controller、原生 callback owner、源氏击杀重置或共享构建配置。

`HeroVoiceAssets` 从实际 Windows `USERPROFILE/.universal-modder/assets/ow1-zhcn-2016/thnu-full/manifest.json` 读取 hash→hero/event/sha256（也接受 entries 包裹），仅加载本地且 SHA256 相符的 `<hero>/<hash>.mp3`，不联网。可用 `-Dowmc.heroVoiceDirectory=<dir>` 改目录。分类文件中的 deployment_allowed=false 是前两轮的历史审定状态；本轮按用户指定下载 manifest 装载，不直接消费 classified.json。

后台单线程调用本机 ffmpeg，优先 `LOCALAPPDATA/universal-modder/ffmpeg/bin/ffmpeg.exe`，支持 `-Dowmc.heroVoiceFfmpeg=<exe>`。转换 mono/24kHz OGG，放进实际 MC profile 的 `resourcepacks/owmc-private-full-voice`（资源格式34），素材与缓存均不进 JAR。每条独立 sound ID，缓存回执固定源/OGG 两份 SHA256；未经本工具创建或被改动的缓存保留并报错。manifest 变更或下载未齐时至少15秒间隔重试，声道空闲后才注册/重载资源包；已经启用的包允许再次刷新。

`HeroVoiceChannel` 在客户端线程统一仲裁新旧人声：`ult_cast > ability > kill > death > respawn > ult_ready > pain > healing_request > jump`；选人置于 ult 与 ability 之间。高优先级可中断，低/同优先级忙时丢弃，只停止总线持有的声音，不影响武器/SFX。使用 VOICE 音量与相对听者坐标。按 hero+event 随机排除上一 hash；只有一条时允许再用。冷却：kill 3.5秒、pain 2.5秒、jump 4秒、ready/求治疗20秒，其余1秒。

队列64项、300ms时效；绑定 epoch/source/model/world/hero/player。原版前台、新鲜 host frame 与当前原版英雄必须一致；断流/失焦/切人/模型或世界变化清队列并重建基线，不补播积压。首样本、计数回退、首读满充能不发声；满值抖动不重新武装，低于90%才允许下一次满充能。Reaper真实 Q 电影阶段和 MC 死亡界面有狭窄例外，普通菜单没有。客户端停顿超过200ms也重建原生基线。

## 已接信号与保留缺口

| 事件 | 本轮已接的实际来源 |
|---|---|
| select / 旧施法 | 旧gate保留：21选人，Genji/McCree/Pharah/Soldier76/Tracer/Reaper Q，McCree闪光弹、Soldier治疗场、Reaper传送。只改播放总线与汇总计数；新入口按hero/event屏蔽 |
| ult_cast 新增 | Mei Blizzard.casts、Hanzo dragonCasts、Widow InfraSight begin+active、Roadhog qCasts、Zarya gravitons、Symmetra portalBuilds、Lucio barrierCasts；Bastion/Torb NativeCharge.active上升沿。只消费现有适配器已接受状态 |
| ability 新增 | Genji dash begins/deflect新tick；McCree roll starts；Pharah concussive detonations；Tracer blink/recall starts、Pulse黏住实体（排除墙）；Reaper wraith starts；Mei wall builds/cryo阶段/实际freeze；Hanzo scatters/sonic admitted；Junkrat mines/traps/trapTriggers；Torb deploys/packsThrown；Widow grapple casts/venom throws+detonations；Bastion自修复；Mercy有目标的HEAL/BOOST通道新tick；Rein barrierCasts/chargeStarts；Zarya selfLastBeginTick+selfActive；Roadhog hookCasts/hookHits/healCasts；Symmetra turretBuilds；Lucio ampCasts/songCommits（不猜治疗/加速） |
| ult_ready | 21人 ALL-HERO-CHARGE真实charge/cost跨满值；Genji读NativeUltimateController，其余校验NativeCharge身份快照；不增加计量写入者 |
| kill | HeroVoiceRuntime：服务端LivingEntity真死亡且DamageSource攻击者为当前单人玩家；全英雄、按受害者UUID去重，明确标“MC 适配” |
| pain / death | ALLOW_DAMAGE仅快照，AFTER_DAMAGE确认真实HP损失且存活才pain；AFTER_DEATH才death。致死坠落单独variant路由，普通死亡不会随机到坠崖叫声 |
| respawn | AFTER_RESPAWN确认真正死亡后的重生；随后当前原版身份/新世界与活玩家一致才发声，3秒失效。不把切维度当重生 |
| jump | 既有LivingEntity jump mixin的TAIL；本地玩家实际起跳且向上，排除飞行/水/岩浆/乘坐，不读Space |
| healing_request | 服务端真实损血跨到最大HP的35%以下，一次武装，恢复到50%以上才重新武装。痛叫结束、声道空闲后再核实服务端仍低血量，避免被pain吞掉 |

没有对应素材时报告missingClips，不借用其他事件。D.Va机甲、Winston、Zenyatta、Mercy复活、Rein地震/烈焰击等缺认证成功回执的施法关闭。Symmetra销毁/受击/剩余次数缺精确variant路由，Torb护甲提醒缺年龄回执，Mercy泛化staff_channel没有单独持续提醒，均未塞进随机施法池。reload/status/idle、ult_charge、comm、multikill/effort未接；不用按键、弹药增加、计时或搜索尝试伪造成功信号。

## 注册、诊断与验证

**注册已写入，Claude无需重复添加：**

```java
// GuestMod 的 frameExport 初始化块
HeroVoiceRuntime.register();
// WorldFrameExporter END_CLIENT_TICK，现有适配器更新之后
HeroVoiceEvents.INSTANCE.tick(client);
// NativeSessionGuard 客户端会话清理
HeroVoiceEvents.INSTANCE.resetSession();
// WorldFrameExporter.close
HeroVoiceEvents.INSTANCE.close();
```

起跳已挂入现有NativeDashTravelMixin，无需增加mixin配置。新旧入口共用总线，无需另注册播放器。

`/combat.heroVoice` 提供 `loadedClips/manifestEntries/missingFiles/loading/error`、`events/heroEvents/admitted/available`、`lastHero/lastEvent/lastHash/lastAsset/lastOrigin`、`playing/observedPlayingTicks`、声道抢占/拒绝、过期/重复/缺素材、`mcKills/mcPains` 与求治疗延后状态。events是取到声道后的播放请求计数，实际输出需再验音频。当前始终注明nativeOverlapVerified=false。

核心1578条下载清单不含healing_request，新增 [hero-voice-extra-download.json](../research/voice-catalog-20261025/hero-voice-extra-download.json)：75条，按25KB约1.875MB。Claude下载到同一私有目录，将真实SHA256写入同一manifest；无需改download.json或将音频放进JAR。核心中没有本轮有效信号的素材可保留待后续接线。

[verify_hero_voice.py](../research/sprint-20261024/verify_hero_voice.py) 默认Hanzo+Mei，可加McCree；要求已启动的隔离Switch实验世界、精确原版/MC PID与创建时间、JAR SHA。脚本再备份profile配置，复用既有输入/清理链，不启动、构建或部署游戏。依次测select/ability/ult/mei-lab真击杀/pain；Q明确用已有实验授能，击杀用原生武器，不用/kill。每项要求heroVoice计数恰好+1，记录MC java.exe进程音频，与最近hash素材做归一化相关性（默认>=0.5）和QPC时间窗校验；不把截图或技能计数当语音验收。

Claude用现有dev_cycle启动、取得新身份后运行：

```powershell
./.venv/Scripts/python.exe research/sprint-20261024/verify_hero_voice.py --pid <native-pid> --created <native-created> --mc-pid <mc-pid> --mc-created <mc-created> --world "Overwatch Twilight Switch <isolated-lab>" --guest-sha256 <installed-jar-sha256> --output research/sprint-20261024/hero-voice-live --heroes Hanzo Mei
```

本轮通过：只读环境检查、离线compileClientJava、HeroVoiceCheck（优先级/旧所有者/随机不连续/计量边沿/真实MP3转OGG/默认ffmpeg位置/缓存篡改拒绝/源SHA拒绝）。Python脚本只运行help和离线音频样本，相关性0.972829、定位偏差0秒。fixture与日志留在忽略的research目录。**未部署、开游戏、下载、实际触发语音或完成原生无双声验收。**

## batch-voice1 后：半藏龙吼与重叠音频核验

原实测Hanzo select/scatter通过，ult全段相关性0.338；旧末影龙吼与后半句叠加。现删除NativeHanzoSkillRuntime的末影龙吼，在起始箭真正到达10m、双龙released边沿发一次带scope/位置/序号的有界回执。HeroVoiceEffects复用同一私有manifest/MP3校验/OGG注册，播放 `hanzo:sfx:dragon_roar`（hash `7e6b10c991611aff98a6ff24708ab5e9`），使用PLAYERS分类、LINEAR衰减和释放位置，不占用或抢占人声。300ms时效与原版/玩家/世界身份校验仍适用；缺素材报错，不回退末影龙声。`/combat.heroVoice.sfx` 独立记录播放计数、位置、hash与错误，不覆盖最近人声。

`heroVoice.lastPlayedNanos` 是人声交给SoundManager的时刻，`sampledNanos` 是同JVM的诊断采样时刻；脚本通过两者差值映射到HTTP接收的Python单调时刻，不假设Java/Python计时原点一致。新脚本要求这些字段，旧JAR须重新部署。

ult_cast与ability改用参考前0.5秒（`--prefix-seconds`可设0.25–1秒）相关性，**原阈值0.5不变**。只在播放时刻前0.15秒至后0.35秒内搜索匹配，另记录全段 `fullCorrelation/fullAudioAtSeconds`、`correlationMode/referenceWindowSeconds/playDeltaSeconds`。其他事件继续全段核验。历史batch录音离线重算：前缀0.5973、全段0.3379、起点距旧计数观测约+36ms；旧记录没有新时间字段，仅作回放分析，不能当作本次替换后的实机验收。合成检查同时覆盖后半段强SFX、错误时刻的正确音频拒绝、选人保持全段核验。
