# voice 线程交接：2026-10-27 第三轮

**最新：用户第三次试玩反馈的技能语音10秒冷却、P10日语原声及历史会话审计，见文末追加段；该段覆盖前文041候选的处理。**

## r27-V01 voice-front12 稳定等待修复（最新跟进）

失败英雄已明确：**Hanzo→Junkrat**，狂鼠选人已经通过，尚未执行 Junkrat-skill。原始 `heroes` 只有前12人，没有 Reinhardt；Pharah-select/skill、Reaper、Soldier76、Tracer Q、Hanzo技能均已通过，因此没有证据把本次归因于 Reinhardt 或 Pharah 飞行。原始记录：[result.json](../research/sprint-20261027/r27-V01-voice-front12/result.json)，最后选中 hero=`0x02e0000000000065`、model=`2147486288`，选人快照 `heroVoice.hero=junkrat`，狂鼠技能计数均为0。

旧语音脚本直接继承堡垒主武器测试的 `Suite.aim()`，8秒内必须同时满足 locomotion.ready、主武器 combatReady、armoryVariants 和 modelId；超时发生在这个准备阶段，没有留下逐项条件。狂鼠捕兽夹实际走 `NativeJunkratController → NativeJunkratRuntime` 的独立节点/提交，并不依赖通用主武器发射器。**旧报告不足以确认当时上述哪一项为false**；现存 `native-emissions-24312.json` 已是 cleanup 后的 `enabled=false/restored=true`，不能把它冒充失败瞬间的证据。

改动仅限脚本：

- `verify_hero_voice.py` 的 `VoiceSuite.aim()` 改调新 `tools/voice_aim.py`，不修改共用 `verify_bastion_cannon.py`。
- 预算从旧8秒改为25秒，要求连续稳定至少0.35秒；世界/来源变化或临时未就绪均重建稳定基线。朝向有界重试最多12次，且必须连续观察到水平朝向才返回。
- **Junkrat** 必须满足实际MC朝向、locomotion.ready、当前英雄/模型/世界、heroVoice当前英雄，以及 `junkrat.signals` 的 ready/hero/model/world/source 和 **trap.ready**；不再要求与捕兽夹无关的通用主武器 combatReady。绝不在独立控制器未就绪时强行发E或跳过技能验收。
- 其他英雄继续要求主武器 combatReady、当前hero/model、所需armoryVariants、emission enabled且未restored，另核对MC/语音当前英雄；没有放宽 Pharah 投射物等原有必要门控。
- 新增 `aimDiagnostics`：目标英雄、期望hero/model、路径、每项检查、失败项、MC locomotion/error、原版日志关键值、狂鼠绑定/捕兽夹、flight标志、朝向和校正次数。失败时 `aimTimeout` 同样包含具体英雄及失败条件，原始身份/前台检查仍由 `s.data()` 保留。

未调整轮换顺序，保留触发路径验证，避免通过跳过某英雄掩盖问题。后续技能仍须真实提交并让 heroVoice.events 恰好增加一次；未改语音资产、761条白名单、概率/冷却、大招固定hash或任何Java代码。

新建 `tools/test_voice_aim.py` 的 **7项纯离线回归通过**：通用combatReady=false时真实狂鼠独立绑定可就绪；错英雄/模型/世界/来源与未就绪捕兽夹均拒绝；Pharah仍要求主武器；9秒后才稳定可恢复；超时保存英雄和具体失败条件；等稳后再校正视角；世界变化重启稳定等待。Python AST检查通过，未启动游戏/实测，未构建或部署。

**Claude 只需重跑键 `voice-front12`，不需要重新构建/部署JAR，也不需要重跑已通过的 `voice`。** 若仍失败，直接看 `aimDiagnostics[-1].last.failed` 及对应局部报告，即可区分 locomotion、独立trap绑定或主武器准备问题。

---

遵守 `PARALLEL-ROUND-20261026b.md` 第三轮负责表：只改语音文件、语音工具/清单和语音核验脚本；没有改 NativeHanzo/其他线程的玩法文件、共享注册文件，没有启动游戏、联网、下载、构建 JAR 或部署。

## 击杀语音：全英雄共用10秒硬冷却

保留冷却外的 **35%** 抽样、相邻击杀不超过 **8秒** 的 **3杀保底**，新增 `HeroVoiceKillGate.COOLDOWN_MS=10000`。计时从人声声道接受一次实际 kill/multikill 播放开始，普通击杀与多杀共用，不因英雄不同、切人、死亡、失焦或换世界而重置。

冷却内的新击杀只增加 `cooldownSuppressed`，不抽样、不累计连杀，不在冷却结束后补播。每次真正播出都会清空旧累计。已取得、尚未播出的保底仍尊重高优先级人声；取得声道后才开始这10秒。候选仲裁与实际播放前另有硬门控，保底也不能绕过。保留 MC 服务端真实死亡、攻击者是本玩家、同世界与 UUID 去重的 **MC适配** 击杀信号，没有改为按键或命中即播。

`HeroVoicePolicy.cooldownMs(kill/multikill)` 同步为10000。`heroVoice.killSpeech` 新增 `cooldownMs`、`cooldownRemainingMs`、`cooldownSuppressed`，原概率/保底/播放计数继续保留。`verify_hero_voice.py` 只有看到真实 mcKills 增长和 `cooldownSuppressed` 增长，才将零播放记为 `cooldown_skipped`；这种情况不声称音频验收通过。

## 选人：0.5秒

`HeroSelectCalloutGate.DELAY_MS=500`；保留真实第一人称确认、快速换人取消、同英雄不重复、世界/模型重绑不重复的现有规则。Tracer/Bastion 的选人静音策略不变。

## 半藏大招：唯一条目已固定，语言身份尚需听辨

目录 `catalog.json` 与 `classified.json` 中只找到两条明确的 `ult_cast` 候选，都没有标明实际录音语言：

| hash | 目录原注释 | 本地MP3时长 | 当前处理 |
|---|---|---:|---|
| `041b1e23a19cb344ff2dba19428da7ec` | 【半藏】（开大）让巨龙吞噬你！ | 2.252秒 | 按“开大”标注暂选为自身大招唯一原声 |
| `b3faba0b762d856fb3ab72218a8c87f4` | 【半藏】巨龙吞噬一切。 | 2.900秒 | 退出默认清单与运行时准入 |

已实现固定策略：`HeroVoicePolicy.HANZO_ULT_HASH` 指向 `041b1e23…`；素材加载前拒绝同英雄/同事件的其他hash；播放直接取固定hash，不经过随机/不重复选择；固定文件缺失时报错，不随机回退。旧私有 manifest 即使仍有另一条，也不会加载或播放它。`verify_hero_voice.py` 的 Hanzo 大招用例新增最近hash必须为固定项的断言。

**未完成的内容确认：不能仅由这两个中文注释证明哪段录音实际说日语。** 本机没有可用的本地 Whisper/Vosk 等识别器，本会话工具也不支持音频输入；没有联网识别或下载模型。已向用户异步请求已确认的日语hash，暂按“开大”条目作明确假设。当前只证明了该文件存在、SHA256与私有manifest一致、策略只会播放这一条，**没有把它标成已听辨/已确认日语**。预期台词是 `竜が我が敵を喰らう`；待 Claude 听辨已有 `thnu-full/hanzo/041b1e23a19cb344ff2dba19428da7ec.mp3`，若不是所需日语原声，仍需定位正确hash后替换固定项。证据和限制见 [hanzo-ultimate-pin.json](../research/voice-20261027/hanzo-ultimate-pin.json)。

原韩语/中文/日语的全库分类没有被臆改；此前已禁用的龙吼补充SFX、痛叫、位移语气声、idle/status等仍禁用。半藏的实际施放触发仍为已认证 `NativeHanzoSkillRuntime.dragonCasts`，没有修改原版技能信号，也未接按键。

## 清单及改动文件

默认清单 **762→761**，仅移除另一个半藏 ult_cast（`b3faba0b…`）。`research/voice-catalog-20261025/download.json`、`research/voice-20261026b/download-default.json` 和生成的 `HeroVoiceDefaultCatalog.java` 已同步。其他明确技能/大招台词不变，包括法老之鹰3条震荡冲击台词。此次未写用户目录下的私有manifest，运行时白名单会过滤那一条；全部保留素材已在本地，无需下载。

改动文件：

- common：`HeroVoiceKillGate.java`、`HeroVoicePolicy.java`、`HeroSelectCalloutGate.java`、生成的 `HeroVoiceDefaultCatalog.java`。
- client：`HeroVoiceEvents.java`、`HeroVoiceAssets.java`。
- tests：`HeroVoiceFeedbackCheck.java`、`HeroSelectCalloutGateCheck.java`。
- tools/核验：`prune_voice_defaults.py`、`check_voice_front12.py`、`research/sprint-20261024/verify_hero_voice.py`。
- 本轮证据：`research/voice-20261027/`；新交接文件为本文。

## 离线检查

- `tools/check_environment.py` 通过。
- `compileClientJava --offline` 通过：25秒，2任务执行、1任务缓存；无JAR构建/部署。
- 500ms选人夹具通过，包括499/500ms边界、快速重选、悬停/同英雄/会话保护。
- 击杀夹具通过：10000ms边界、冷却内三次击杀也不能保底、切人/死亡重置不绕过冷却、冷却结束不补播，保留35%抽样（固定种子34980/100000）与冷却外保底；法老首发计数回归仍通过。
- 固定hash准入/旧清单不能恢复另一条、761条清单一致性、前12英雄保留素材与探针、Python AST（4文件）通过。本地固定MP3 SHA256与manifest一致；语言听辨仍未完成。

证据：[compile.log](../research/voice-20261027/compile.log)、[offline-checks.json](../research/voice-20261027/offline-checks.json)、[front12-audit.json](../research/voice-20261027/front12-audit.json)。

## Claude 后续

无需新增注册行，无需改共享文件。 [已集成 integrator]（核对既有注册、voice/voice-front12；固定候选的日语听辨仍未确认）首先听辨上述固定候选是否确为所需日语；不能把“固定hash夹具通过”当作语言确认。如果确认，需要同步私有清单时执行下面的纯本地修剪（保留备份及MP3，不联网）：

```powershell
.\.venv\Scripts\python.exe tools/prune_voice_defaults.py --apply-private
```

若确认的是另一hash，需同步修改 `HeroVoicePolicy.HANZO_ULT_HASH` 与 `tools/prune_voice_defaults.py` 的 `HANZO_ULT_HASH`；若它不在旧download-before来源表，还需将那条已确认目录记录加入生成输入，再重新生成清单和编译。不要只改私有manifest，运行时会拒绝未准入的hash。

统一打包命令（本线程未执行）：

```powershell
$env:JAVA_HOME="$PWD\minecraft-1.21.1\runtime\java-runtime-delta\windows-x64\java-runtime-delta"
$env:GRADLE_USER_HOME="$PWD\tools\gradle-cache"
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon remapJar
```

按既有dev_cycle部署后建议重跑键 **`voice`、`voice-front12`**，另实测：先观察一次真实击杀人声，再在其后10秒内连续真实击杀、切英雄继续击杀，确认 `events.kill + events.multikill` 不增加而 `cooldownSuppressed` 增加；到期无自动补播，新的冷却外击杀才允许抽样/保底。连续多次半藏真实Q应始终为同一hash并确认为所需日语；19人选人应在确认后约0.5秒（另有客户端tick调度）播放。所有实机项仍待 Claude 执行。

## 用户第三次试玩反馈：技能冷却与半藏日语原声（最新，覆盖041候选）

### A. 所有新旧技能语音共用英雄+事件10秒冷却

新建纯策略类 `HeroVoiceSkillCooldowns`，覆盖 **全部 ability:* 与 ult_cast**，按 `hero+event` 分别计。计时只在声道接受实际播放后开始；冷却内不播、不排队补播。不同英雄、不同技能互不影响；切人、换世界、声道结束/重置不清除计时。

准入放在 `HeroVoiceChannel`，因此 EarlyChineseVoices、GenjiUltimateVoice、MccreeVoice 的旧Q/E也同样受限；通用 HeroVoiceEvents 在候选仲裁前先过滤已冷却技能，避免它阻挡其他可播事件。`HeroVoicePolicy.cooldownMs` 同步10000ms。原有击杀的全英雄10秒冷却、35%概率/连杀保底，以及0.5秒选人延迟不变。

`/combat.heroVoice.skillCooldowns` 输出 `cooldownMs`、`remainingMs` 和按英雄+事件的 `suppressed`。这只限人声，未修改实际技能冷却、伤害或技能SFX。

### B. 已纠正上轮误选的中文041：改用本地P10日语参考片段

上轮把标注“开大”的 `041b1e23…` 暂当所需原声，用户本次已确认它是中文；现在它和 `b3faba0b…` 都从默认库与运行时半藏大招准入中排除，不再作任何回退。

真正找到的语言证据来自已下载文件：

- 源：`~/.universal-modder/assets/ow1-zhcn-2016/bili-BV1Hs411q779/P10-audio.m4s`，8秒左右，源SHA256 `fff56d05c362f3dd43869b4d32e781aecdb0da3ea41b92e574d7459261578e1d`，与旧reference-manifest吻合。
- 本地既有识别记录：`four-dps-20261023/actual-reference-audio-asr.json` 的 **P10-audio.m4s** 条目为 `language=ja`、`probability=0.8734037280082703`，0–2.4秒文本 **“リュウガー、我が敵を喰らう!”**。这是既存ASR记录，不是本轮联网识别，也不是按视频手部/目录汉字推测语言。
- 从0截到 **2.65秒**，保留语句尾部余量；生成MP3实际解码 **2.6720625秒**，约22ms编码器前导延迟。与相同源窗口对齐后的PCM相关性 **0.985336**，阈值仍为0.97；源文件与裁剪文件SHA、窗口、编码延迟、识别证据完整写在 [hanzo-japanese-proof.json](../research/voice-20261027-feedback3/hanzo-japanese-proof.json)。
- 唯一播放ID改为 **`ea38b68ebfa92aaa527c958f81edcb31`**。这是 `SHA256(owmc-hanzo-ja-v1:<源SHA>:0.000:2.650)[:32]` 的本地裁剪配方标识，**不是原站目录hash**；实际MP3另以完整SHA256校验。固定选取，不随机、不回退。

源是历史实录，可能含同期轻微技能音效，**不能称为完全分离的干净人声**；本轮没有合成/TTS或伪造台词。现有ASR和同源PCM已支持日语识别，但最终听感仍应试听。音频一直留在系统Temp/私有素材目录，不进入仓库、JAR或提交。

`7e6b10c9…` 源文件199920字节、解码7.156秒。其前段与P10日语参考的可靠匹配未成立（P10前2.2秒在该文件中的最高相关约0.081），所以不能宣称“龙吼头部就是所需日语”，也没有恢复整段龙吼。已单独裁出前2.65秒供听辨。

**试听只给以下2个候选：**

1. 已选的P10日语参考片段：[01-hanzo-P10-japanese-0-2p65.mp3](</<USERPROFILE>/AppData/Local/Temp/owmc-voice-review-20261027/01-hanzo-P10-japanese-0-2p65.mp3>)。
2. 未确认语言、未挂接的龙吼前段：[02-hanzo-7e6-prefix-0-2p65-unconfirmed.mp3](</<USERPROFILE>/AppData/Local/Temp/owmc-voice-review-20261027/02-hanzo-7e6-prefix-0-2p65-unconfirmed.mp3>)。

重建试听片段只需 `.venv/Scripts/python.exe tools/prepare_hanzo_japanese_voice.py`，纯本地、只写系统Temp与研究元数据。thnu-three仅有半藏选人；four-dps中没有另一条半藏Q，但保存了上述P10的实际音轨ASR。原版来源也已查：现有154088缓存只有Genji语音；`ow_asset_chain.py` 当前追踪24919模型/材质链，没有语音解码路径；旧154504提取日志明确TRG provider不兼容，并曾在所谓offline尝试中读远端keyring。本轮没有再次运行这个会联网/已失败的回退，也没有启动、附加或改动原版客户端。

### 上次试玩究竟播放哪条：已证事实与缺失证据

当前工作区找不到用户给出的 `research/integration-results/play-20261027`。指定 `guest-passthrough-client/logs/latest.log` 共411行，没有 heroVoice/hash 播放记录；旧代码原本就只更新诊断计数、不记录逐句播放，因此**不能据无日志断言“大招没触发”，也不能从该日志证明当次实际hash**。

能证实的是：当前安装JAR经 `javap -constants` 检查，`HANZO_ULT_HASH` 仍为 **041b1e23…**；私有运行时资源包缓存该声音定义为 `replace=true`、唯一文件 `owmcguest:private/full/041b1e23…`，没有另一条半藏大招缓存定义。资源包运行时启用不一定写回options.txt，故不把静态options当作当次启用顺序。另一个独立自动会话 `r27-V01-voice/result.json` 的 Hanzo-ult 已实际记录 `lastHash=041b1e23…`、passed=true；它**不是**缺失的人工试玩会话。

据此可以解释旧安装策略为什么仍指向中文041；目前没有“另一条随机大招覆盖”的证据，但不能伪称已从人工试玩日志反查动态事件。完整记录见 [previous-session-audit.json](../research/voice-20261027-feedback3/previous-session-audit.json)。

已补新日志：每句成功交给声道的播放都会在MC日志写 `heroVoice played hero=… event=… hash=… origin=… asset=… resolved=…`；诊断新增 `lastResolvedSound`。后续可同时核对事件、固定ID和实际解析的资源文件，识别同名资源被覆盖。这里的日志证明播放请求已被声道接受；物理输出仍由原MC进程音频相关性验收。

### Claude 安装、打包与重跑

**必须在统一部署前执行一次以下纯本地命令，无需下载：**

```powershell
.\.venv\Scripts\python.exe tools/prune_voice_defaults.py --apply-private
```

它现在会调用已测的日语裁剪安装器：核对源/ASR、生成片段，复制到 `thnu-full/hanzo/ea38b68ebfa92aaa527c958f81edcb31.mp3`，备份manifest并替换旧半藏ult_cast，再执行默认准入修剪。保留原MP3、其他英雄和已有备份，不覆盖用户修改的音频。原manifest为761条，本地替换后仍为 **761条：760条站点素材+1条本地派生片段**。默认下载表同步含localOnly标记，下载器不会把B站页面当MP3抓取。

本线程可写范围不含真实 `~/.universal-modder`，所以只生成系统Temp试听文件；上述真实私有安装由Claude执行。若仅更新JAR而没有安装新片段，加载器会明确报缺少半藏日语片段、assetsReady=false，**不会静默回退041**。打包命令沿用前文remapJar，未新增任何共享注册行。 [已集成 integrator]（核对既有声道已接技能冷却与新P10加载；无需共享改动，私有片段未由本轮安装）

本次改动：HeroVoiceSkillCooldowns（新增）、HeroVoicePolicy、HeroVoiceDefaultCatalog（生成）、HeroVoiceChannel、HeroVoiceEvents、HeroVoiceAssets、HeroVoiceFeedbackCheck；新增HeroVoiceSkillCooldownCheck、prepare_hanzo_japanese_voice.py、test_prepare_hanzo_japanese_voice.py；调整prune_voice_defaults.py、voice_download.py及默认清单。没有改其他英雄技能/世界共享文件。

离线：`compileClientJava --offline --rerun-tasks` **通过，26秒/3任务实际执行**；新旧技能10秒边界/独立事件/不同英雄/未播不占冷却夹具、原击杀冷却与法老首发夹具通过；纯Temp中的安装幂等、备份、用户修改保护、自定义目标目录及同源PCM校验通过；前12人素材/探针、Python AST（6文件）通过。证据目录 `research/voice-20261027-feedback3/`；没有开游戏、下载、构建或部署JAR。

安装后重跑键 **`voice`、`voice-front12`**；额外用真实技能重复触发检查同一hero+event在10秒内 `events` 不增、`skillCooldowns.suppressed` 增，而另一技能/英雄仍可说话。连续真实半藏Q的日志应只有固定 `ea38…`，resolved文件同ID，process-audio与已安装派生MP3匹配；同时试听候选1确认所需日语和混入SFX是否可接受。

第三轮集成索引：[INTEGRATION-20261027.md](INTEGRATION-20261027.md)。上述标记只指源码接线/删除旧行/既有接线核对，不表示实机验收。全量compileClientJava --rerun-tasks通过（27秒，3任务实际执行），未遇Loom锁、未删锁文件；未开游戏、打包JAR/DLL或部署。原“待接线”段落保留交接时历史，最新结果以本补记为准。

## 用户第四次试玩反馈：半藏Begin提前与起落语气声（最新补记）

本轮仅离线读归档、源码及现有MC日志；**未开游戏、未附加进程、未联网、未构建/部署JAR**。P10日语唯一hash、所有技能按英雄+事件10秒冷却、击杀规则和0.5秒选人延迟均保留。证据：[audit.json](../research/voice-20261027-feedback4/audit.json)、[compile.log](../research/voice-20261027-feedback4/compile.log)。

### 半藏：用原版大招消息入口新tick，删除放龙计数接线

原来 `HeroVoiceSignals` 消费 `NativeHanzoSkillRuntime.status.dragonCasts`；原controller在 `b9:76 STUStatescriptStateWeaponVolley` 新tick后才生成MC龙/增加计数，因此人声等到了发射阶段。

现在新增只读 `HeroVoiceHanzoBegin`，注册独立 `NativeSkillReader.Spec`：英雄 `02e0000000000005`、图 `05800000000000b9`、`castBegin=79`、`release=76`。**触发源是79号 `STUStatescriptEntryGameMessage` 的新原版时间戳**，日志 `signal=native:hanzo-b9-entry79`；76仅保留为发射时刻对照，不触发人声。不读Q按键、不提前生成MC龙、不修改技能runtime/伤害。旧 `dragonCasts→ult_cast` 行已在本线程负责的 `HeroVoiceSignals` 删除，没有双入口或晚触发回退。

依据是已有真实Q校准归档 [hanzo-dragon-calibration1/result.json](../research/sprint-20261024/hanzo-dragon-calibration1/result.json)：同一原版实例的79/76/80号tick分别为 **18928 / 20328 / 20528**。对应图归档 [sonic-config.json](../research/sprint-20261024/hanzo-current-calibration1/sonic-config.json) 确认117个节点，79类型 `be49a4c2`、76类型 `860ee5fc`，80号Wait字面量0.2秒。76→80的200个时间戳单位对应0.2秒，据此79比76早1400单位，**预期比旧接线提前约1.4秒，另有客户端tick/音频调度延迟；这是归档推算，并非本轮实机测量**。

消息入口通常同tick已finished，故只消费时间戳边沿，不要求active持续一帧；初样本、换英雄/世界后的旧值仅作基线，重复tick不再播放。绑定继续沿用原读取器对PID、generation、本地owner、英雄、model、script、图及节点地址/vtable的校验，读失败不发声。

新增 `tools/prepare_hero_hanzo_voice.py`，只读核对实际图/节点类型，原子写 `native-heroVoiceHanzoBegin-request-<pid>.json`，不改 `native-hanzoSkills` 请求或内存。现有 `launch_passthrough_session.py` 已自动发现 `prepare_hero_*.py` 中的HERO+prepare，因此**半藏无新增共享Java/启动器注册行**；应在正常重启会话启动器后由现有绑定刷新调用。若复用已启动且尚未import新模块的启动器，可由Claude在核实当前原版PID、当前英雄为半藏后单独运行：

```powershell
.\.venv\Scripts\python.exe tools/prepare_hero_hanzo_voice.py --pid $verifiedNativePid
```

`/combat.heroVoice.signals.hanzoBegin` 增加 `ready/error/beginNode/beginTick/entryActive/releaseTick/newEdge/offered/lastOffered/releaseTickAtOffer/offeredWall`；发声记录新增 `lastSignal` 与日志signal。`releaseTickAtOffer`锁存当时所见值，避免HTTP读到后续帧丢证据。核验脚本在Q用例前等待该绑定ready，超时保留signals并报错；发声后要求唯一P10hash、Begin信号和 `lastOffered > releaseTickAtOffer`，不能用晚到的发射阶段播放冒充通过。原有前缀/全段音频相关阈值未降低。

现有日志还确认本次改动前的已装版本确实在15:44:26播放 `ea38b68ebfa92aaa527c958f81edcb31`，resolved同ID；故本轮只改触发时机，没有再次替换日语素材。

### 起跳、跳跃、落地：可确认来源与删除清单

**已排除当前默认素材库为直接来源**：下载白名单与真实私有manifest均761条，jump/landing/takeoff/effort/movement类为0；现有MC日志13条人声记录也没有这些事件。已装JAR的 `HeroVoiceEvents.onJump` 字节码为直接return，源码同为空入口。仅凭这些不能断言用户听到的原版进程语气声已经消失。

历史2713条来源表中有以下 **8条jump**，前轮已从默认库/私有manifest移除，本轮逐条复核仍未恢复；**本轮当前库新增删除素材数为0，清单仍761条**：

| 英雄 | 旧条目hash | 目录说明 |
| --- | --- | --- |
| Hanzo | `04dc926e40520d4ab80c3d10994b9da0` | 【跃】 |
| Hanzo | `55ca9269a47ed187031bd696a98b596d` | 【跃】 |
| Hanzo | `598b45d2f4e2b6215cccaf8fbe9a150f` | 【跃】 |
| Hanzo | `93c82cc9aab6ce8ae48e896123ac012c` | 【跃】 |
| Hanzo | `e16636d1909a908c878eb082860989a4` | 【跃】 |
| Junkrat | `1c27a08da7214c94fd10ddba01ed39fd` | 跳跃时 |
| Tracer | `34bb1e9a60c88627a80a4e612a5575c9` | 跳 |
| Widowmaker | `41ad6468b8de0886d30ac5279199204d` | 起跳时的喊声 |

`HeroVoicePolicy` 和 `prune_voice_defaults.py` 同步永久拒绝 jump/land/landing/takeoff/effort、movement:jump/land，以及 ability:jump/double_jump/super_jump/jump_jet/rocket_jump/leap/wall_climb/landing，防止改事件前缀或重新生成清单恢复；原有blink/recall/grappling_hook禁用也保留。当前白名单中没有这些新增别名对应条目，现有明确技能台词不受影响。默认清单生成的全部761个hero+event+hash与现有清单离线逐一一致，本轮无需再次apply-private。

**MC侧本轮新增直接删除（待以下共享注册）**：

- `HeroVoiceMovementSoundMixin` 在 `SoundSystem.play(SoundInstance)` 入口取消本玩家绑定有效期间的PLAYERS/VOICE类 `minecraft:entity.player.small_fall`、`minecraft:entity.player.big_fall`，共2个MC落地声音事件；同时拒绝未来 `owmcguest` 命名空间里明确标作jump/jumpjet/landing/land/takeoff/effort/exertion/grunt的同类补充声音。当前没有找到已注册的此类自定义起跳声音文件，故不能把这部分写成实际删掉了多少MP3。
- `HeroVoicePlayerFallSoundMixin` 在 `PlayerEntity.getHurtSound` 对**本人且DamageTypeTags.IS_FALL**直接返回null，删除落地损伤附带的玩家hurt语气声这一调用来源；普通受击、怪物、脚步及武器/技能SFX不改。两处均为播放前删除，未添加冷却，未改跳跃/重力/落地伤害。
- `/combat.heroVoice.movementMute.blocked` 按被拦声音ID累加，fall hurt记为 `minecraft:fall_damage_hurt_vocal`。MC声音过滤仅作用当前原版英雄对应的MC玩家绑定范围，离开该绑定即失效。

**原版进程来源仍未解决，不能声称“所有跳跃声已全删”**：`native-host/src/map_audio_data.hpp` / `empty_stage_data.hpp` 及 `docs/MAP-AUDIO.md` 明确只过滤地图环境声，原版英雄音频/声音系统保持原样；本轮未找到已认证的原版英雄起跳/落地语气声资源ID或可单独禁止的声音接口。现有MC人声日志不会记录原版进程的音频；没有本次跳跃的分进程录音，无法在不开游戏的条件下最终认定用户所听来自原版英雄还是MC落地损伤。**没有盲写原版地址、没有将整个原版进程静音，也没有把MC过滤等同于原版删除**。若新MC计数保持0且异响随英雄声线变化，需原版/音频线程继续做精确声音事件资源定位；这项不能由本次Java过滤代替。

### Claude 需要的共享行（本线程未改共享文件）

1. `guest/src/main/resources/owmcguest.mixins.json` 的 `client` 数组加入原样两项（包已是 `lab.owmcguest.mixin`）：

```json
"HeroVoiceMovementSoundMixin",
"HeroVoicePlayerFallSoundMixin",
```

[已集成 integrator]

2. `guest/src/client/java/lab/owmcguest/mixin/NativeDashTravelMixin.java` **删除原样这3行**，移除已经无功能的跳跃通知，其他移动接线保持原样：

```java
    // 语音挂接：LivingEntity真正执行jump后通知，绝不从Space按键制造起跳。
    @Inject(method="jump",at=@At("TAIL"))
    private void owmc$voiceJump(CallbackInfo ci){lab.owmcguest.HeroVoiceEvents.onJump((LivingEntity)(Object)this);}
```

[已集成 integrator]

`onJump`空ABI暂留，保证共享删除前本分支仍可编译；不再注册或生产任何jump语音。无需新增GuestMod/WorldFrameExporter调用。集成应在添加处保留“语音挂接”说明；JSON不支持注释，说明留交接和Java类注释。

### 验证与改动范围

`compileClientJava --offline --rerun-tasks` **通过，37秒，3任务实际执行**；新mixin类已编译，但**未注册运行/未做实机Mixin启动验收**。归档节点类型/时差与清单防恢复Python2例通过；Java的原击杀规则、10秒技能冷却、起落过滤/消息边沿三套夹具通过；新增/修改Python4文件AST通过。没有执行remapJar。

新增：`HeroVoiceHanzoBegin.java`、`HeroVoiceMovementSounds.java`、上述两个 `HeroVoice*Mixin.java`、`HeroVoiceMovementCheck.java`、`tools/prepare_hero_hanzo_voice.py`、`tools/test_voice_hanzo_begin.py`。修改：`HeroVoiceSignals.java`、`HeroVoiceEvents.java`、`HeroVoicePolicy.java`、`tools/prune_voice_defaults.py`、`research/sprint-20261024/verify_hero_voice.py` 和本交接。没有改NativeHanzo*、移动共享类或mixin注册表。

统一打包/部署仍由Claude沿用前文命令。建议重跑键 **`voice`、`voice-front12`**；重点保存Hanzo Q时 `signals.hanzoBegin`、`lastSignal`、P10hash及MC进程音频，确认人声先于76放龙。跳跃需额外同时分开录原版和MC进程音频，反复原地跳/普通落地/会摔伤落地，记录 `movementMute.blocked`；MC计数能证明拦截请求，静音必须以实际音频判断。原版独立语气声的删除仍待定位，不能把本轮编译通过作为该项验收。

## 用户第五次试玩反馈：全英雄开大时机、就绪提示、抢占与堡垒恢复（最新）

本节覆盖前文“ult_ready已退出”和“堡垒技能素材不恢复/抽查跳过”的旧结论。**本轮未开游戏、未附加进程、未联网、未下载、未改真实私有manifest、未构建/部署JAR**。现有私有库仍761条；源码默认白名单已为 **785条**，必须先执行下方素材恢复命令再统一部署。元数据与证据：[audit.json](../research/voice-20261027-feedback5/audit.json)、[24条完整hash/字幕](../research/voice-20261027-feedback5/selected-lines.md)。

### 21英雄 ult_cast 的信号与提前量

提前量指相对原来等待的原版阶段/MC回执，**不是物理Q按键到音箱的实测延迟**。所有“Begin”均为已有原版节点新tick且active，不从Q按键、满能量、弹体出现或击中倒推。瞬时消息/动作/Volley允许同tick已finished，依靠新tick和原有10秒冷却去重。正常20TPS下仍有客户端tick及音频缓冲调度；未测的时差明确保留未知，不写成零延迟。

| 英雄 | 当前 ult_cast 最早已知信号 | 相对旧入口的预期提前量/限制 |
| --- | --- | --- |
| 源氏 | `0317:17` active Begin，原 `NativeUltimateController→GenjiUltimateVoice` | **0**：原来已用该起手；保留原所有者/素材 |
| 麦克雷 | `022f:18` ultimate Begin，原 `NativeDeadeyeController→MccreeVoice` | **0**：原来已用该起手，不等44开枪 |
| 法老之鹰 | `002b:12` barrage Stack Begin，`EarlyChineseVoices` | **0**：原来已用12；不等13蓄力或2开火 |
| 死神 | `0044:49` ultimate active Begin，仍播原Early素材 | 不再等48开火、9动画同时active及MC phase回执；**缺同场时差，未量化**；Q电影锁仍可读此原版节点 |
| 士兵76 | `0259:15` ultimate Stack Begin，仍播原Early素材 | 不再等12瞄准active；**缺同场时差，未量化** |
| 猎空 | `0034:3` cast Anim Begin，仍播原Early素材 | 比1投掷tick早约 **0.15秒**，另省MC回执等待；旧q-probe为68128→68278 |
| 堡垒 | `012f:105` Tank State Begin，直接读原已认证表 | **旧库没有可播Q，无法比较旧音频**；现在105新Begin即请求，不再依赖充能worker的active布尔边沿 |
| 半藏 | `00b9:79` EntryGameMessage新tick，沿用第四次修复 | 比76发龙约早 **1.4秒**；本轮不回退，不改P10唯一hash |
| 狂鼠 | `0232:7` windup Anim Begin | 新恢复缺失Q素材；不等32创建轮胎；**无旧播放时差可量化** |
| 美 | `064a:1` windup Anim Begin | 比10投掷约早 **0.50秒**，另省MC回执等待；18624→19124 |
| 托比昂 | `01c2:21` ultimate Stack Begin | 21/30/19/20/17归档同tick；原版相位差 **0**，省充能worker/布尔状态发布等待，调度差未量化 |
| 黑百合 | `0067:18` ultimate Stack Begin | 比6动画/13效果/10计时器约早 **0.65秒**；18640→19290 |
| D.Va | **未接已认证施放Begin** | 当前是驾驶员；`026a:41`只是未解析召机尝试，不当自毁/成功召机。**不可估算** |
| 莱因哈特 | **未接已认证施放Begin** | `00be:1` Shockwave仅有声明、缺成功Q起手执行证据。**不可估算** |
| 路霸 | `01c6:37` WholeHog连续Volley状态Begin | 原版相位差 **0**；不等MC qCasts回执，省一次跨线程/服务器交付，时长未量化 |
| 温斯顿 | **未接已认证施放Begin** | 无原始暴怒Begin绑定；不靠满能量播放怒吼。**不可估算** |
| 查莉娅 | `025f:2` Volley新tick，瞬时事件 | 与归档中最早Q消息/SetVar同为31728；原版相位差 **0**，不等MC弹体；**归档只采到瞬时E，未声称另有更早动画Begin** |
| 卢西奥 | `073a:9` windup Anim Begin，新独立只读voice绑定 | 比0号Aura早约 **0.66秒**；31552→32212，不再等落地上盾/MC barrierCasts |
| 天使 | **未接已认证施放Begin** | `00ca:36`只有目标搜索，空搜索不能当复活施放；**不可估算** |
| 秩序之光 | `0169:66` 原版放置提交新tick | 不等MC portalBuilds；**不在42预览就喊“上线”**。提交执行仍待实机补证，无可信时间差；这是放置型语义约束，不宣称预览即施放成功 |
| 禅雅塔 | `017b:19` windup Stack Begin | 新恢复Q素材；原版归档已见31936的起手B，不等17治疗/30 Aura；**无旧播放时差可量化** |

因此是 **17人具有原版事件接线，4人缺认证施放Begin**；17人中查莉娅是最早已见瞬时Volley，秩序之光是确认放置提交，不能把这两项也宣传成“所有21人均已认证Q动画首帧”。缺口与更早信号要由Claude后续实机采样补证，本轮不按键伪造、不新加坦克/辅助效果。

证据来自已有归档：`pulse-bomb-20261021/q-probe.json`，`hanzo-dragon-calibration1`、`mei-blizzard-calibration2`、`torb-core-calibration1`、`widow-infra-calibration1`、`generic2-{Lucio,Roadhog,Zarya,Zenyatta,Symmetra}` 的result/definitions。原版时间戳单位沿用已校验Wait80=0.2秒对应200单位的标度；本轮没有新测量音频提前量。Python夹具直接复核Tracer/Mei/Widow/Lucio的上述差值。

新增 `HeroVoiceUltimateSignals` 只读复用原请求；旧MC casts/qCasts/gravitons/portalBuilds/barrierCasts和充能active布尔对应Q接线均删除，避免早晚两条入口。`/combat.heroVoice.signals.ultBegin` 输出当前节点、tick、active、ready/error、offered/lastOffered/offeredWall及source/model/world。旧请求缺windup等字段时明确拒绝并提示刷新，避免空字段崩主线程。

`EarlyChineseVoices` 只前移士兵/猎空/死神的原触发，仍由旧素材所有者发声；源氏/麦克雷/法鸡没有另造一份Q。所有成功播放日志和 `lastSignal` 均标明实际节点。半藏保留独立 `signals.hanzoBegin`；P10唯一ID、10秒技能冷却、0.5秒选人不变。

### ult_ready：21人每次未满→满只播一次

- 非源氏20人消费 `NativeChargeController.status` 的原版charge/cost，要求ready且hero/modelId/worldId/hostGeneration全部匹配当前绑定，数据来自 `ALL-HERO-CHARGE` 同一原版变量路径。
- 源氏通过独立**只读** `NativeAbilityReader(true).ultimate` 取实际charge/cost，同时核对source/model；不使用缺少身份标签的旧静态charge快照，不创建第二个充能写入者。
- 初读已满、换英雄/模型/世界初读满、费用改变或失效后重连满值仅建基线，不播；已知未满→满播一次，持续满不重复。**99%→100%同样算新周期**，不再要求先降到90%；用原有数值容差过滤浮点抖动。
- `ult_ready`不套10秒/20秒时间冷却，由充满边沿去重；每轮可播一次。`ult_cast`与所有 `ability:*`仍按hero+event共享10秒硬冷却。运行时读取/客户端调度仍有延迟，不承诺与变量写入零毫秒同步。
- `/combat.heroVoice.signals.ultReady` 保留ready、charge、cost、crossedFull、source/model/world、hasClip。初始已满不算测试成功；脚本 `--ult-ready` 用已观测未满的真实原版计量，经已有实验授能填满，逐项录音/计数；若初读已满明确记 `not_exercised_initial_full`，不伪造下降/不冒充自然充能实测。

每人只恢复一条目录语义明确的原版就绪提示，完整字幕/来源/full hash见 [selected-lines.md](../research/voice-20261027-feedback5/selected-lines.md)。**堡垒本来是官方电子提示音，没有“我的大招准备就绪”的普通中文对白**，故保留其“坦克模式就绪”目录对应电子音，不能称为中文配音说话；没有TTS或借其他英雄代读。其余20人选择该英雄中文就绪台词，不恢复战术邀请、闲聊、状态或语气声。目录无完整录音版本元数据，实际语言/听感仍应按音频验收，不把目录字幕等同于本轮听测。

### 声道：只有开大/就绪能抢占

`HeroVoiceChannel` 是新旧入口共同的最终准入：**ult_cast=101、ult_ready=100**，这两类到达即停止本声道持有的当前语音并播放新句；同一帧同时到达时先选ult_cast。两者都可覆盖任何已经播放的项目语音，包括另一条大招提示。10秒同技能冷却仍先执行，不允许用抢占绕过。

其他事件即使数字优先级高于当前句，也不抢占；忙时直接丢弃，不延后补播。已保留的击杀连杀保底可按原规则等待空声道，仍受全英雄10秒击杀冷却。英雄/世界身份失效时原本的声道撤销仍保留；没有停止原版进程音频/其他MC音效。

### 堡垒 Q 丢失的根因与修复

1. 目录仅有 `5a449ed346d47a7e0180fdda14770b6e`，字幕“【堡垒】坦克模式”；旧 `prune_voice_defaults.py.ANNOTATIONS` 中明确包含前缀 `5a449ed3`，因此被判 **annotation_only** 并从默认表/JAR白名单/私有manifest清掉。当前私有MP3仍在，所以可以复用，非下载丢失。
2. `selectionAllowed`仅在event=select时检查；堡垒/猎空选人静音**没有误伤ult_cast**，不应把selectionMuted改回true。已加夹具验证两者可拥有就绪/Q、同时继续静音选人。
3. 旧Q用充能worker的active布尔边沿；本轮改为已有认证 `012f:105` 新Tank Begin，跳过模型/状态旧值，失效后重建基线。默认表仅对这条已明确用途的堡垒Q作例外，不恢复其选人、机械闲聊或跳跃。
4. `verify_hero_voice.py` 的roster原先也主动跳过Bastion。现在 `Bastion-skill` 会检查真实Tank绑定ready、素材可用，授能后按原版Q，并要求计数+1与 `lastSignal=native:bastion-012f:105-begin`；所以 `voice-front12` 不会再因旧“无字幕全跳过”期望漏验堡垒。

### 素材恢复命令与网络预算（由Claude执行）

新增 `tools/restore_voice_ultimates.py` 保存逐条阅读后的固定名单，`prune_voice_defaults.py`生成默认JSON和 `HeroVoiceDefaultCatalog.java`时也合并它，之后重新修剪不会再次删掉就绪/Bastion Q。新增 **24条=21 ult_ready+3 ult_cast（Bastion/Junkrat/Zenyatta）**，默认761→785；仍为784条站点录音+1条本地P10派生片段。其他无字幕、jump/idle/status/pain等类别仍禁用。

本机只读dry-run：**22条可复用本地MP3，只有以下2条不存在**：

- Junkrat ult_cast `b0ae530103d62c2092581cd00b8e3cc6`：“炸弹来啦”。
- Zenyatta ult_cast `374032df1e8ffb5bcad2af2b695274d9`：“感受宁静”。

24条按25KB/条预算约600KB，但22条无需重复下载，**新增网络预算约50KB**，实际以服务器文件为准。本线程没有执行网络下载；真实manifest仍761，不能只部署新JAR就宣称全部恢复。

源码白名单与清单已生成。Claude先在本工作区执行：

```powershell
# 可选：不联网、不写私有目录，只看本地缺失统计
.\.venv\Scripts\python.exe tools/voice_download.py --list research/voice-20261027-feedback5/download-additions.json --dry-run
# 必需：复用22个旧MP3并补回manifest，只有2个缺失文件才访问批准来源
.\.venv\Scripts\python.exe tools/voice_download.py --list research/voice-20261027-feedback5/download-additions.json
```

若从源码重新生成元数据，先运行 `tools/restore_voice_ultimates.py` 与 `tools/prune_voice_defaults.py`（不带apply-private）即可。**本次不需要再apply-private裁P10**；现有日语片段保持原样。下载器仍写 `~/.universal-modder/assets/ow1-zhcn-2016/thnu-full/<hero>/<hash>.mp3` 与hash→hero/event/sha256的manifest；所有音频不进JAR/提交。

下载器只接受默认白名单身份与批准的 `vo.kaikai.men`/`ow.thnuclub.com` MP3路径，跳转在发出下一请求前也检查；本地已有文件校验MP3并重建SHA元数据，避免修剪后重复下载；失败返回非零。缺就绪/恢复Q素材时加载器明确把assetsReady置false并列出缺项，避免安静地“恢复成功”。下载后应有manifest785及 `assetsReady=true`，才能录音验收。

### 注册、验证与重跑

**本轮没有新增共享Java/GuestMod/WorldFrameExporter登记行**。[已集成 integrator] 已核对现有 helper 自动发现、前轮 Mixin 与 jump 删除；无需重复注册。785 条私有同步命令已收入集成报告，尚未执行下载或私有写入。新 `tools/prepare_hero_lucio_voice.py` 与前轮Hanzo voice helper一样由现有启动器HERO+prepare自动发现；必须正常重启启动器使其import新helper，之后在英雄绑定刷新时生成 `native-heroVoiceLucioBegin-request-<pid>.json`。它只读核对073a的41个节点与9/0类型，不改原卢西奥绑定、效果或callback。复用旧启动器时可在核实当前原版PID且当前英雄为Lucio后手动：

```powershell
.\.venv\Scripts\python.exe tools/prepare_hero_lucio_voice.py --pid $verifiedNativePid
```

上轮起落声音的两行mixin共享注册/删除旧空jump通知仍见第四次补记，本次没有改动这些文件，也没有把原版跳跃语气声缺口当作已解决。

离线 `compileClientJava --offline --rerun-tasks`通过，3任务实际执行（耗时以 [compile.log](../research/voice-20261027-feedback5/compile.log) 为准）；Python的恢复清单/批准域名与跳转/只读dry-run/归档时间戳及Hanzo/清单夹具通过；Java四套策略夹具涵盖充满边沿、抢占矩阵、Bastion/Tracer事件隔离、10秒边界和旧击杀规则；另1套真实MP3→OGG/缓存损坏/源SHA/就绪素材缺项检查通过。临时复制的测试音频已删；系统Temp的Java toRealPath被沙盒拒绝，改用已确认git忽略的工作区证据临时目录后通过，未改真实私有素材。Python7文件AST通过。没有打包、部署或实机音频验收。

改动：HeroVoicePolicy/Channel/Signals/Assets/Events、EarlyChineseVoices、HeroVoiceDefaultCatalog（生成）、新增HeroVoiceUltimateSignals；prune_voice_defaults/voice_download、restore_voice_ultimates、prepare_hero_lucio_voice；对应离线夹具、verify_hero_voice.py、默认清单/本交接。没有修改Native*英雄controller/runtime或原英雄模块。

[已集成 integrator] 既有 `voice`、`voice-front12` 保留；新增 `voice-ult-ready` 完整接入本节 21 人就绪录音参数，并把 Reinhardt 放在该批最后，保留尾部选项。

下载后按前文统一remapJar/部署，建议重跑键 **`voice`、`voice-front12`**（现在包括堡垒Q）。21人就绪抽查可复用同一精确身份参数调用 `verify_hero_voice.py --mode roster --heroes all --select-only --ult-ready --roster-audio`，使用独立output；初满项必须另在真实消费大招后补测，不能把未覆盖标作通过。重点另测：普通技能不能打断kill/选人，Q/充满能立即覆盖它们；满值长持只增加1次就绪，真实未满再满可再增1；Q 10秒内重复不增加。21人Q的四个认证缺口与放置/瞬时限制仍按上表保留，不以编译或满能量成功替代施放验收。

## 用户第六次试玩反馈：堡垒变形起手、死神恢复；最终采用已验证中文

**最新用户追加：“中文 大招语音也可以。”最终方案固定死神中文“正在肃清敌人”。三个英文候选已被用户全部否定，均未安装，不再推荐；英文目标句未确认。** 已撤掉待确认英文槽及其加载要求，默认表和真实私有manifest均保持 **785条**，本轮无需下载、裁剪或安装新语音素材。没有开游戏、附加游戏进程、构建/部署JAR或修改真实私有manifest。

### 堡垒：旧105是变形完成后的形态，改123动画Begin

当前安装的最新MC日志确实记录 `hash=5a449ed346d47a7e0180fdda14770b6e`、`signal=native:bastion-012f:105-begin`（20:00:56、20:07:24、20:07:40），因此不是误等首发炮弹：**代码一直等105进入Tank形态后才播**。

[bastion-tank-20261021/q-probe.json](../research/bastion-tank-20261021/q-probe.json) 的同次原版Q实测记录：`123 StateAnim Begin=60848`，`123 End=62348`，`105 State Begin=62348`；也就是先变形 **1500个原版时间戳单位，约1.5秒**，才进入Tank。图 [graphs.json](../research/bastion-tank-20261021/graphs.json) 确认共192节点，123类型 `7fb4bf64`、105类型 `a7213568`。原5a MP3按8%峰值RMS测得声音起点约 **0.05秒**，主要延迟不是素材头部空白。

现在 `HeroVoiceUltimateSignals` 改读独立 `heroVoiceBastionBegin` 的 **123变形动画active新tick**，日志源改为 `native:bastion-012f:123-transform-begin`；105只作形态见证，输出tankTick/tankActive，完全不参与触发。预计比旧接线早约 **1.5秒**，仍有客户端tick/音频调度；这是已有归档推算，非本轮实机计时。动画End、105到达、第一发炮弹都不补播；10秒技能语音冷却不变。

新 `tools/prepare_hero_bastion_voice.py` 只读核对当前PID/model/hero/图及123/105节点类型，写 `native-heroVoiceBastionBegin-request-<pid>.json`。不改堡垒controller/runtime、炮弹或实际技能冷却。

### 死神：资源未删，修复触发与电影锁生命周期

已确认的事实：

- 最新日志有20:07:58/20:09:54选人、20:07:59/20:08:06/20:09:54就绪、20:10:20传送语音，**没有任何被声道接受的Reaper ult_cast记录**。
- 私有源 `four-dps-20261023/reaper-blossom-ally.ogg` 和当前profile内对应OGG均存在；30487字节，SHA256均为 **`1d5aff1b7998a24aa681627cb26d21f4397d427b51f1c9a6524cb61523e031da`**。资源包 `reaper.blossom` 定义只有这一项，且同包传送语音已实际播放。旧素材没有被修剪删除。
- `prune`不把Reaper Q放进通用银行，是因为 `legacyOwned(2,"ult_cast")=true`，原本由Early负责；这是防双声，不能简单再加一份中文Q到通用银行。
- 第五次把旧的已认证 `NativeReaperRuntime.View` Begin改成了独立读取49.active；该新分支既不保存reader错误，也不保存49/9状态。**能确定回归发生在触发链；当次究竟是49窗口未采到还是独立读取失败，没有遥测可唯一还原，不能伪称日志已经证明其中一个。** 既有 [blossom-core-v3/result.json](../research/reaper-kit-20261023/blossom-core-v3/result.json) 则实际证明原runtime回执路径曾令 `reaper.blossom` 计数0→1，且真实Q完成。

本轮改成：优先读 **`0044:9` 大招动画active新tick**；读取失败/未收到时，可使用**原来已实测的、当前owner/source/model/world完全匹配且≤150ms的 `NativeReaperRuntime.View.begin`**。View只在实际活动期发布，结束即清空，不用按键或猜测时长。两个来源分别做初样本基线、Begin去重，最后共用既有hero+ult_cast的10秒冷却；同次Q先后收到两源只实际播放一次。

另一个可直接从代码证实的生命周期问题也修了：原版Q电影阶段inputActive=false；在MC View尚未送达时，`HeroVoiceEvents.current()`原先会返回null、清空声道。现在仅对**刚认证的9号动画、同source/model/world且≤150ms**保留绑定，避免原版起手已经准入的语音被下一步马上停掉；没有放宽普通菜单、其他英雄或断流门控。

统一诊断新增 **`/combat.heroVoice.reaperBegin`**（Early状态也有同名节点）：rawReady/rawError、rootTick/rootActive、animationTick/animationActive、directEdge、runtimeFreshScope/runtimeFreshActive/runtimeBegin/fallbackEdge、source/model/world、clipReady、fixedUltHash、voiceLanguage。后续失败前后都保存这些信息，避免再次只能猜资源还是信号问题。实际日志会明确写 `native:reaper-0044:9-animation-begin` 或 `native:reaper-runtime-cast-begin`。

### 死神最终素材：只用现有中文这一条

固定 **`a81b42c757722f46f7e007d3916caa1f`**，目录字幕“正在肃清敌人（我方大招）”，本人中文友方版本。私有MP3 SHA256 `219bbf31a75aa2a61d161ac7268ab80bdffb0b20bb0d3b77bb332773dc9186c8`；实际播放仍用上面的固定OGG。既有本地识别 `reaper-ally-asr.json` 为zh、概率0.965159、文本“正在肅清敵人”，时长约2.71秒；该旧路径也已有实际播放计数验收。

`HeroVoicePolicy.REAPER_ULT_HASH` 固定此ID；Early继续是唯一播放所有者，资源定义为单条，不随机、不选择别的Q。补齐旧入口的lastHash记录，核验脚本直接使用已钉SHA的中文OGG参考。就绪提示仍为原中文；所有技能10秒冷却、最高大招优先级、击杀规则和0.5秒选人保持。

**英文研究结果仅留证，不是正式素材**：已用SHA守卫的本地CascLib读取器，从24919的英文speech manifest、Reaper专属VoiceSet `07a0000000000001` 和关联音频定义提取、解码88个本地WEM。普通FFmpeg不能解码旧Wwise Vorbis，故复用本机OWLib源码/码本，在忽略的研究目录编译了独立转换CLI，没有运行DataTool的CASC初始化、远端keyring、模型下载或原版游戏。ASR包目录访问被拒绝，未自动确认目标句；按重复发声特征筛出的 `08d…aedf / a1d9 / af02` 三条已被用户逐一否定，记录 `userRejected=true` / rejectedWems。它们从未进入私有manifest/JAR，英文安装入口已移除；研究工具后续筛选也排除这些ID。用户允许中文后不继续盲挑英文。

证据/研究工具： [audit.json](../research/voice-20261027-feedback6/audit.json)、[reaper-candidates.json](../research/voice-20261027-feedback6/reaper-candidates.json)、[reaper-native-clips.json](../research/voice-20261027-feedback6/reaper-native-clips.json)；`voice_wem_decode.py`、`find_reaper_english_voice.py`、`prepare_reaper_english_voice.py` 仅作本地研究。**不要运行任何先前待确认英文槽的安装命令。**

### Claude 需执行的命令/登记

**不用下载、不用apply-private、不用安装新声音。** 现有中文profile资源已验SHA。按前文统一构建/部署JAR，并正常重启启动器，让HERO+prepare自动发现新的Bastion voice helper；**无需新增共享Java调用或mixin行**。[已集成 integrator] 已核对既有自动发现路径、123变形Begin及统一reaperBegin诊断/电影期声道保护；没有修改 project_launcher.py，也没有重复注册。

Claude统一构建命令（本线程未执行remapJar，部署仍沿用现有dev_cycle流程）：

```powershell
$env:JAVA_HOME="$PWD\minecraft-1.21.1\runtime\java-runtime-delta\windows-x64\java-runtime-delta"
$env:GRADLE_USER_HOME="$PWD\tools\gradle-cache"
& tools/gradle/gradle-8.10.2/bin/gradle.bat -p guest --offline --console=plain --no-daemon remapJar
```

仅当继续使用旧启动器进程、它尚未import新helper时，在核实当前原版PID且当前英雄为Bastion后可只读刷新：

```powershell
.\.venv\Scripts\python.exe tools/prepare_hero_bastion_voice.py --pid $verifiedNativePid
```

仅当后续诊断显示 `reaperBegin.clipReady=false`，可在正常停机后从现有私有源重新准备该profile的旧资源包（无网络；确认当前profile路径后运行）：

```powershell
.\.venv\Scripts\python.exe -c "import sys; from pathlib import Path; sys.path.insert(0,'tools'); from four_dps_voice_assets import prepare; assert prepare(Path('guest-passthrough-client'))"
```

`verify_hero_voice.py --reaper-ult` 为roster模式单独检查Reaper Q，保留before/after的reaperBegin和统一计数，检查固定中文hash、两种认证来源之一及MC进程音频；不再只测Reaper传送。Bastion抽查也已把旧105期望改成123。

共享 `research/sprint-20261024/run_batch.py` 未由本线程修改；如需键 **voice-reaper**，请Claude原样加入：

```python
TESTS += [('voice-reaper', ['verify_hero_voice.py', '--mode', 'roster', '--heroes', 'Reaper', '--reaper-ult', '--roster-audio'])]
```

[已集成 integrator] 已将上述键原样加入 run_batch.TESTS，保留既有键、精确身份参数、莱因哈特末尾顺序与失败/BLOCKED 汇总。

安装后重跑 **voice-front12、voice-reaper**（后者先加上述键）。也可沿用当前已经核实的native/MC进程身份、world、JAR SHA，单独执行：

```powershell
.\.venv\Scripts\python.exe research/sprint-20261024/verify_hero_voice.py `
  --pid $verifiedNativePid --created $verifiedNativeCreated `
  --mc-pid $verifiedMcPid --mc-created $verifiedMcCreated `
  --world $verifiedWorld --guest-sha256 $verifiedGuestSha256 `
  --mode roster --heroes Reaper --reaper-ult --roster-audio `
  --output research/sprint-20261027/r27-V06-voice-reaper
```

本轮离线：compileClientJava强制重编通过（最终日志见 [compile.log](../research/voice-20261027-feedback6/compile.log)）；Python9例、Java5套策略夹具通过，覆盖真实123→105时差、固定中文唯一性/源SHA、初样本/换世界及同次Q两个来源的10秒去重；Python10文件语法检查通过。上述都不等于实机播放已验收。

最终生产改动仅限HeroVoiceUltimateSignals、EarlyChineseVoices、HeroVoiceEvents、HeroVoicePolicy与verify脚本，新增Bastion voice只读helper/第六次夹具；HeroVoiceDefaultCatalog重新生成后保持785。其他英雄controller/runtime/共享注册表未改。英文研究脚本和临时转换器留作证据，未成为正式语音依赖。
