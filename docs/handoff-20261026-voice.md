# voice 线程交接 · 2026-10-26

本轮遵守 `PARALLEL-ROUND-20261026.md` 与 `HERO-MODULE-GUIDE.md`：只改本线程负责的语音文件与新文件，**没有运行编译、单元/离线测试、实机脚本，没有启动游戏、部署或下载**。仅运行 `tools/build_voice_optional_catalog.py` 生成任务要求的素材元数据与Java准入表。新代码均待Claude统一编译/测试，不能标记为已验收。

既有基线：Hanzo选人/散射/大招/击杀/受伤与Mei选人已由Claude实测通过；上一轮冰墙锁存修复待测。本轮保留击杀参考开头跳过0.6秒、`mei-lab-silent`、冰墙失败轨迹/确认回执、资源就绪等待和20秒窗口尺寸重试。

## 1. 文件与职责

改动：

- `guest/src/main/java/lab/owmcguest/HeroVoicePolicy.java`：新事件优先级/冷却、装弹锁存器。
- `guest/src/main/java/lab/owmcguest/HeroVoiceRuntime.java`：MC效果边沿、真实回血/闪电损血、控制回执入口、闲聊战斗版本号。
- `guest/src/client/java/lab/owmcguest/HeroVoiceEvents.java`：可选素材准入/路由、状态变体筛选、新客户端信号和诊断。
- `research/sprint-20261024/verify_hero_voice.py`：21人抽查、装弹/状态用例，保留原有回归与音频判据。

新增：

- `HeroVoiceAmmoReader.java`：读取原版弹匣与满弹赋值节点，只读进程内存。
- `HeroVoiceOptionalClient.java`：装弹读数门控、低频闲聊策略；不增加原版callback owner。
- `HeroVoiceOptionalCatalog.java`：生成的hash级路由白名单，不包含台词或音频。
- `HeroVoiceStatusLab.java`：受隔离Switch世界限制的真实MC效果实验入口；不直接调用语音offer。
- `tools/prepare_hero_voice_ammo.py`：固定当前原版模型/脚本/弹药变量/节点地址，不写原版内存。
- `tools/build_voice_optional_catalog.py`：从1135条可选项生成采集表、暂缓表、Java准入表与2361条分析任务。
- `tools/assets/analyze_voice_unsubtitled.py`：纯本地声学特征、可选本地Vosk、已听辨参考近邻；仅给候选，不自动启用。
- `research/voice-20261026/`：本轮生成的JSON，属于忽略的本地研究元数据。

未改WorldFrameExporter、GuestMod、NativeCombatScene/Runtime、HeroServerModules/ClientModules、NativeDashTravelMixin、NativeSessionGuard、run_batch.py或其他线程文件。

## 2. 新事件来源及边界

### reload

定义为：**实际读到原版部分弹匣，再读到同一弹匣回满，同时观察到对应原版满值赋值节点的新tick**。回满与节点先后采到均可，在500ms内锁存配对。不是R按键触发，不从MC物品栏猜弹药。

准备器按原版反射字段把 `WeaponVolley.m_out_Ammo` 动态路径，连接到真实ConfigSet满值赋值的目标/最大值。最大值只接受同bag数值或已声明s32字面量；未知表达式不猜。当前模型、controller引用、hero、script/graph/bag、数字对象及其bag成员、节点定义/vtable/最大值引用、进程创建时间每次读时检查；未知结构/读失败/换模型均只建基线或报错。只读权限，没有执行getter/原生函数或安装新hook。

Tracer有既有研究证据：`0580000000000016:30`、current `0d80000000000035`、maximum `0d800000000000c6`；排除装备初始化节点14。其余英雄的准备器只证明**类型/路径匹配的原版弹药补满赋值**，尚未逐英雄实测确认手动/自动装弹全部生命周期，JSON的evidence明确保留 `live calibration pending`。绑定不出弹药槽时保持关闭，不能把“支持21人选人”写成“21人装弹已认证”。

初读就是满弹、最大值改变、读失败/重绑不喊；排除容量1和Hanzo弓装箭，不把无限弓箭循环当R装弹。施放技能/大招后的2秒、已知Recall/Roll/Shadow活动阶段屏蔽回填，避免把技能回填当装弹。多个同批或500ms内的槽合并为一次完成计数；同一弹药目标若有不同最大值变体则暂不绑定，待形态校准。提供 `/combat.heroVoice.optional.reload`：ready、error、slots(ammo/maximum/commitTick/evidence)、completions、abilityRefillBlocked。

原版机械装弹SFX保留。本轮29条reload中28条是机械声/注释，不叠在人声通道；仅Reaper“重新补给”的一条台词进入候选表。没有台词的英雄在验证中只能记 `signal_only`，不能宣称已听到装弹人声。

### status:*（MC适配）

| 事件 | 真实来源 | 说明 |
|---|---|---|
| status:slowed | 本玩家新出现SLOWNESS | 只使用已筛出的通用不适台词，别名路由到status:debuffed素材；不是眩晕 |
| status:debuffed | 新出现WEAKNESS | 不用任意负面效果泛化为“力量削弱” |
| status:poisoned | 新出现POISON | 不将凋零等同中毒 |
| status:damage_boosted | 新出现STRENGTH | 仅证明MC力量状态；不宣称所有原版投射物已有30%增伤；排除明确纳米激素台词 |
| status:burning | 真正isOnFire上升沿 | 与OW“火力全开/表现评分on_fire”分开 |
| status:cold / frozen | 冻结ticks>0 / 真正isFrozen | MC受寒/冻伤；不冒充Mei对本玩家施加的原版硬控 |
| status:healed | 同一生命/最大HP稳定时实际HP增加 | 40tick内连续回血合并；台词另有30秒冷却；满血/痊愈类只在实际达到满血时可选 |
| status:electrocuted | 实际闪电DamageType造成HP损失 | 不从电粒子或普通Slowness推断电击/眩晕 |

只对当前绑定的单人玩家采样。首样本、重绑、失焦恢复、死亡/重生均建立基线，不把初始效果或满血重生当受治疗。状态解除后再出现才产生新边沿。诊断位于 `heroVoice.optional.mcStatus`，含active、frozenTicks、health/maxHealth、source/model/world、计数。

眩晕、被钩、击退、被复活、OW表现评分、技能就绪、废料量均**没有在本线程伪造**。提供 `HeroVoiceRuntime.controlCommitted(ServerPlayerEntity victim,String event,long receipt)` 供已认证“本玩家实际控制成功”生产者将来接入；目前没有共享生产者接它，相关素材仍暂缓。该API必须在服务器线程、成功提交后调用，receipt须来自同一种单调序列，不要混用不同来源时钟。它不是把搜索节点/右键/减速改名为眩晕的接口。

### idle（MC适配策略，默认关闭）

启动参数 `-Dowmc.heroVoiceIdle=true` 才启用。90–180秒无战斗、静止、没有界面/飞行/低血量/活动效果，且独立人声与空间SFX均空闲、有当前英雄的已准入闲聊素材时，随机不重复播放；后续至少120–240秒间隔。实际入场、施法、原版已接受射击、击中/受伤/击杀/状态、移动均推迟闲聊。不是原版OW的闲聊触发器/交流轮盘。

新优先级：status45（在ready50与pain40之间）、reload32、idle10。旧事件相对顺序保留。未下载/不可路由的可选声不抢占已有可播放pain等事件；素材缺失仍有计数诊断。统一人声通道与私有素材转换继续复用，声音不进JAR。

## 3. 需要Claude加的共享行

### A. 普通游戏中刷新当前英雄的弹药绑定

**无需重复注册HeroVoiceRuntime或HeroVoiceEvents.tick**，旧轮已注册。客户端新代码已经在该tick内部工作。 [已集成 integrator]（核对既有注册，不重复添加）

在 `tools/launch_passthrough_session.py`（stability负责）引入：

```python
from prepare_hero_voice_ammo import prepare as prepare_voice_ammo
```

[已集成 integrator]

在当前英雄/模型的其他native绑定准备完成、`prepare_locomotion`身份校验通过的同一段，追加可选旁路：

```python
try:
    record['heroVoiceAmmo'] = prepare_voice_ammo(process, pid)
except Exception as voice_error:
    record['heroVoiceAmmo'] = {'optional': True, 'error': str(voice_error)}
```

[已集成 integrator]

未知英雄弹药绑定失败不应阻塞主会话恢复/移动。该工具无HERO常量，不加入单英雄prepare插件表。验证脚本的 `--optional-events reload` 自己也会准备当前绑定；普通游玩则需要上面这条刷新接线。

也可对已核实PID/创建时间的原版手动准备，命令仅留给Claude，本轮未执行：

```powershell
./.venv/Scripts/python.exe tools/prepare_hero_voice_ammo.py --pid <native-pid> --created <native-created>
```

### B. 新状态实验端点

把以下分支放在WorldFrameExporter的通用 `/combat/test/` POST分支之前。没有新增HTTP服务或callback owner；实验类自己再次检查隔离Switch/creative/线程/已有效果，效果60tick自然到期，不覆盖已有同类效果。

```java
} else if(exchange.getRequestURI().getPath().startsWith("/combat/test/voice-status-")
        && exchange.getRequestMethod().equals("POST")) {
    var kind=exchange.getRequestURI().getPath().substring("/combat/test/voice-status-".length());
    if(!java.util.Set.of("slowed","poisoned","debuffed","damage_boosted").contains(kind)) {
        code=400;result="{\"error\":\"unsupported voice status fixture\"}";
    } else {
        MinecraftClient.getInstance().execute(()->{
            var c=MinecraftClient.getInstance();var server=c.getServer();
            if(server==null||c.player==null)return;
            var owner=c.player.getUuid();
            server.execute(()->HeroVoiceStatusLab.apply(server,owner,kind));
        });
        code=202;result="{\"queued\":true}";
    }
```

[已集成 integrator]

诊断已经从语音自身输出到 `heroVoice.optional.statusLab`，不需另加/combat字段。没有接这个分支时，新状态用例会404，不能跳过后仍记通过。

### C. run_batch键名与参数

保留已有 `voice` 回归键，给run_batch.py的TESTS追加，勿覆盖其他线程条目：

```python
TESTS += [
    ('voice-roster', ['verify_hero_voice.py', '--mode', 'roster', '--heroes', 'all']),
    ('voice-optional', ['verify_hero_voice.py', '--mode', 'roster', '--heroes', 'Reaper', 'Genji',
                        '--select-only', '--optional-events', 'reload', 'status', '--status-effect', 'slowed']),
]
```

[已集成 integrator]

需要场景：既有mei-lab、mei-lab-silent、mercy-support、lucio-support、reinhardt-lab、roadhog-hook、zarya-lab、symmetra-placement及cleanup；唯一新HTTP场景就是上面的voice-status-*。场景只放实际MC效果，不调用语音方法，不伪造节点或装弹。

## 4. 可选素材下载交接

由1135条原可选记录生成，保留原表不回写：

| 类别 | 候选条数 |
|---|---:|
| idle | 736 |
| status:healed | 86 |
| status:damage_boosted | 53 |
| status:frozen | 58 |
| status:debuffed（部分可别名slowed） | 35 |
| status:electrocuted | 18 |
| status:poisoned | 9 |
| status:burning | 7 |
| status:cold | 4 |
| reload（人声） | 1 |
| 总计 | **1007** |

- 完整：[download-optional.json](../research/voice-20261026/download-optional.json)，按25,000bytes/条估计 **25.175MB**。
- 起步：[download-starter.json](../research/voice-20261026/download-starter.json)，每英雄/事件最多2条，共 **203条，5.075MB**。
- 暂缓：[download-deferred.json](../research/voice-20261026/download-deferred.json)，**128条**，逐条解释：28条机械装弹、44条OW评分on_fire、控制/复活/盾/废料等无信号、明确皮肤/纳米强化等语境。
- [optional-summary.json](../research/voice-20261026/optional-summary.json) 是数值总表。候选仍标human_review_required；字面/语境过滤不是录音年代、语言或干净声道认证。

由Claude下载，**本轮没有执行**：

```powershell
./.venv/Scripts/python.exe tools/voice_download.py --optional --list research/voice-20261026/download-starter.json
# 起步批完成后，再按需补全：
./.venv/Scripts/python.exe tools/voice_download.py --optional --list research/voice-20261026/download-optional.json
```

目标仍是 `~/.universal-modder/assets/ow1-zhcn-2016/thnu-full/<hero>/<hash>.mp3`，合并同一个hash→hero/event/sha256 manifest。私有加载器继续校验SHA并转换，不需把音频放进JAR或跑模型打包。先完成下载，再等 `assetsReady=true && pendingResourceReload=false` 开始用例。`status:healed`的满血变体和slowed别名来自生成的hash准入表，无需修改下载器的manifest格式。

修改采集策略后重生成（生产元数据操作，不是测试）：

```powershell
./.venv/Scripts/python.exe tools/build_voice_optional_catalog.py
```

## 5. 2361条无字幕的本地处理方案

[unvoiced-jobs.json](../research/voice-20261026/unvoiced-jobs.json) 精确保留旧分类 `event=uncertain && audio_review=true` 的 **2361条**，包括仅英雄名/只有注记的条目；不靠空字符串判断漏项。

`tools/assets/analyze_voice_unsubtitled.py` 默认处理最多32条已存在的音频，缺文件只出缺失清单，不联网。特征包含时长、RMS/峰值、活动比例、起音、频谱平坦度/重心、过零率、8段能量包络、解码PCM SHA。少量规则只产生短语气声样、长叫声/连续声样、噪声/机械声样、可能说话等听辨优先级，**不把短声音硬改成jump、不把长叫声硬改成death**。

可输入同英雄、已人工听辨且源SHA匹配的参考表，做精确PCM重复/声学近邻；非精确近邻置信度最多0.5。可选Vosk仅接受已存在的本地模型目录，不传lang/model_name，不触发模型下载。模型/依赖不在本机时由Claude另行准备，脚本不会pip安装或联网。高置信中文识别仅给少量词句候选（求治疗/就绪/交流/装弹），不自动解释击杀语境。

输出所有 `event` 仍为uncertain、deployment_allowed=false，另有suggested_event、features、ASR文本与requires_listen。不会回写classified或播放manifest。缺失音频清单只用于独立试听/分析目录，**不要直接导入现有播放库下载器**。

Claude后续本地命令示例，均未执行：

```powershell
./.venv/Scripts/python.exe tools/assets/analyze_voice_unsubtitled.py --limit 32
./.venv/Scripts/python.exe tools/assets/analyze_voice_unsubtitled.py --limit 32 --asr-model C:/local-models/vosk-cn --reviewed-reference research/voice-20261026/reviewed-reference.json
```

参考表格式：`[{"hero":"genji","hash":"<32位hash>","event":"pain","sha256":"<实际源SHA256>","human_verified":true}]`。`--audio-root <已有本地目录>` 可重复传入；`--limit 0` 才分析全部已存在文件。ASR不能识别纯喘息/叫声时，继续听辨，不以“压低uncertain比例”为目标强制归类。

## 6. 验证模式与待统一检查项

- 默认命令仍是Hanzo+Mei旧回归，保留原有音频相关性/时间窗以及击杀0.6秒suffix逻辑。
- `--heroes all` 自动进入roster；也可显式 `--mode roster --heroes Genji Reaper ...`。21人选人都测试；每人最多抽一个已有语音生产者的技能。DVa/Winston/Zenyatta等无已接语音源、Bastion/Zarya等缺相应素材会明确写 `skipped_not_wired` / `skipped_no_asset`，不冒充通过。
- roster默认只看 `/combat.heroVoice.events`；`--roster-audio` 才录MC进程音频。`--numeric-only` 显式取消物理音频验收；`--select-only` 可隔离选人/可选事件用例。
- `--optional-events reload status --status-effect slowed`：先真实消耗部分原版弹匣，再按R，必须出现真实读数；无装弹台词仅记signal_only。状态用例请求上面的MC效果端点，之后由普通服务器效果采样产生语音。没有素材就明确skip；不把admitted/MC builds混进播放次数。
- `voiceCases` 的passed只表示已执行用例通过；另有skillCoverage/optionalCases和 `rosterSkillCoverageComplete`，跳过不会变成技能覆盖通过。

Claude统一验证顺序建议：合并共享接线→离线compileClientJava→先跑旧voice基线与冰墙→起步素材+voice-optional→voice-roster→按需扩大素材/音频检查。特别检查装弹“节点先到/回满后到”与反序、首读满弹、F11/Recall/Roll/形态回填、切人/模型重建/失焦、状态首样本/解除再上、满血重生不触发healed、idle默认关闭及战斗推迟。原版是否已经播同类状态声仍须分进程核验；若已播，沿用 `owmc.heroVoiceNativeOwned` 让原版独占。

未解决/未宣称：本轮全部新增代码未编译未测；原版眩晕等本人提交尚缺；通用装弹节点的每英雄语义/自动换弹待实测；736条idle并非逐条重新听辨；录音年代不保证早于1.30；无字幕自动分析不等于事件认证；没有完成21人全部技能/声音覆盖。


集成补记：共享源码接线已完成；voice-roster 注册元组原样保留，run_batch 执行时展开21人并将 Reinhardt 移到最后，批后直接正常停止会话。[已集成 integrator]


Integrator 统一离线结果：全量 `compileClientJava --rerun-tasks` 已通过（26s，3任务实际执行）；未遇Loom锁、未删除锁文件。以上标记只表示源码已集成；打包/下载/部署/实机测试尚未执行，统一命令与分批计划见 [INTEGRATION-20261026.md](INTEGRATION-20261026.md)。
