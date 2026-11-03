# 2026-10-25 只读代码审查

原审查结论：13项问题（4项P1、9项P2）。按用户通知，Claude已修复F01、F02、F03、F05、F06，以下在对应标题后标注【已修】。这些标记来自用户确认，本轮只恢复报告编码，没有重新审查或实测修复后的代码；行号和文末SHA256仍对应原审查快照。

原审查仅写本报告，未修改受审源码、配置、素材包、存档或其他文档；未启动游戏、注入或读取游戏进程、调用显示设置API、运行构建或会写临时文件的测试套件。验证方式为代码与调用链审查、已保存的离线观测及素材数值、一个完全内存化的显示策略复演。下列“建议复现”不表示本轮已做游戏实测。

审查基线为工作树，HEAD为ac1832a。已对指定路径执行git status、git diff --stat及NativeCombatScene.java的git diff：只有该文件属于已跟踪修改（463行新增、6行删除），其余21个指定文件未跟踪，因此逐文件审查了当前完整内容，未把空diff误当成无改动。

## P1：原审查中的优先修复项

### F01 — 诡雷测试覆盖world，可能删错维度的真实方块并遗留旧实验场【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeCombatScene.java:388；还原分支在478–481行，地面记录在350、360行。
- **问题**：venomTarget()直接令共享world等于玩家当前ServerWorld，却保留先前实验场的blocks。它既不要求原实验场world与当前玩家world一致，也不检查Mine View的world。
- **为什么会出错**：在维度A调用ground-lab或其他造块fixture后换到B，在B粘雷再调用venom-target，A的坐标与原始空气记录仍留在blocks，但还原用的world已变成B。随后cleanup会把B同坐标处的STONE、OBSIDIAN、BEDROCK或GLASS改回A保存的状态，通常为空气；A的实验块反而未清。NativeSessionGuard.resetServerState()虽调用NativeCombatRuntime.resetSession()，后者172行不清理NativeCombatScene，不能阻断此路径。
- **建议修法**：方块还原记录必须绑定创建它的ServerWorld及世界身份；venomTarget在更换world前拒绝不匹配的当前fixture，或先在旧world完成清理。若确需跨维度保留fixture，应使用按world分组的journal。同时验证Mine View的world和新鲜度。
- **建议复现**：A建可逆地板→换B→B粘雷→venom-target→cleanup；断言A地板被还原，B同坐标自然石块完全未变。

### F02 — 冰墙在世界关闭后才撤销，活动屏障可能被保存进存档【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeIceWallRuntime.java:68、74–78；实际注册位置为guest/src/main/java/lab/owmcguest/GuestMod.java:75。
- **问题**：冰墙写入真实BARRIER，原BlockState只在内存中；清理挂在SERVER_STOPPED，而非保存和关闭前。
- **为什么会出错**：本机Fabric生命周期源码表明，STOPPED在MinecraftServer.shutdown尾部触发，此时世界已关闭，玩家及实体已卸载。放墙后在100 tick寿命结束前保存退出，BARRIER可能先被写入区块；事后clear()对关闭世界的修改不能保证再次持久化，也可能访问已关闭区块。NativeCombatRuntime.close()在STOPPING清理的是CombatScene，不会撤销这个独立runtime的冰墙。
- **建议修法**：将会写世界的冰墙clear放到SERVER_STOPPING的服务端线程，在保存前执行；STOPPED只清内存引用。不要靠等待五秒或对已关闭世界再次写块保证清理。
- **建议复现**：确认屏障仍active时立即正常保存退出，再加载同一存档检查原位置及原BlockState。
- **时序依据**：本地fabric-lifecycle-events-v1-common-2.6.0+0865547519-sources.jar内ServerLifecycleEvents.java:55–68及MinecraftServerMixin.java:55–62，分别说明并实现STOPPING在shutdown头部、STOPPED在尾部。没有借用其他版本猜测生命周期。

### F03 — 散射箭与榴弹先命中实体、后判墙，会打中遮挡后的目标【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeHanzoSkillRuntime.java:55–60；guest/src/main/java/lab/owmcguest/NativeJunkratRuntime.java:65–69。
- **问题**：两条模拟都先对整段from→next查实体并扣血、分裂或爆炸，再做方块raycast，没有比较最近方块与最近实体的距离。
- **为什么会出错**：散射父箭每tick走4.5米。若这一段依次经过墙和墙后目标，firstMob仍返回后者，56行已扣血，父箭57行直接分裂并continue，根本不会执行挡在前面的墙碰撞。榴弹遇薄碰撞形状或紧靠墙后的目标同样会先扣血。另外，榴弹爆炸仍使用旧b.pos，而非实际实体交点，爆心会偏移至上一个tick的位置。
- **建议修法**：先取方块截断点，仅在该点之前查询实体；或比较两个HitResult距离，只提交最近一次碰撞。将实际命中点写回投射物位置后，再结算分裂或爆炸，不要先伤害再回头做遮挡。
- **建议复现**：在一个4.5米箭步长内布置近墙和远靶；隔墙目标HP必须不变，分裂点必须在近墙表面。另用薄墙验证榴弹真实爆心。

### F04 — 拉钩来源过期后仍继续接管玩家移动【已修】

- **文件:行号**：guest/src/client/java/lab/owmcguest/NativeGrappleController.java:24、27、46–54；调用点为同目录mixin/NativeDashTravelMixin.java:34。
- **问题**：frame超过150ms未更新时tick直接return，reader失败也只是return；两条路径都保留pull。travel只检查存活、载具和hero，不检查host frame或reader新鲜度。
- **为什么会出错**：拉钩开始后，原版帧发布停止，但最后flags仍为1，MC客户端travel还会不断执行move并取消普通MC travel，直到最多1600ms超时或到达锚点。已经超过150ms新鲜度门限的控制源仍驱动真实玩家。
- **建议修法**：来源过期或无法验证时取消pull，清掉本技能残留速度；travel入口本身也验证本次Scope与新鲜度，不能只依赖可能提前return的tick。正常到达的释放动量与不可信来源取消应区分。
- **建议复现**：开始拉钩后停止host frame更新但保持MC tick，超过150ms后不得再由pull产生位移。

## P2：功能、状态与实测一致性

### F05 — 狂鼠爆炸没有遮挡测试，隔墙范围目标仍会掉血【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeJunkratRuntime.java:105–108。
- **问题**：explode只判断实体到爆心的距离，直接调用explosionDamage，没有实体可见点、爆炸暴露率或方块raycast。
- **为什么会出错**：即使F03修好最近碰撞，在墙一侧爆炸仍会对另一侧两米内的目标扣血，与项目既有覆盖物及爆炸遮挡实测契约冲突。
- **建议修法**：复用已验证的爆炸遮挡解析策略，在独立的爆心和目标几何上计算暴露率或LOS，再应用两环伤害；不要把投射物碰撞射线等同于所有范围目标可见。
- **建议复现**：同距离无遮挡、完整石墙遮挡两靶，墙后靶保持原HP。

### F06 — 宣称使用原版两环爆炸，却把外圈伤害错误降到0【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeJunkratRuntime.java:100、107。
- **问题**：表达式1-(d-INNER)/(OUTER-INNER)在2米边缘为0；已保存的当前022b:30、31、38声明是outerScale=.125，边缘应仍有非零伤害。
- **为什么会出错**：以80原版HP为例，边缘应为10原版HP，而当前传入0会被伤害入口直接拒绝。文件声明了引信等MC适配值，但这里的注释明确声称原版两环，不能把数值差异隐含成未声明策略。
- **建议修法**：保存并使用已验证的outerScale，按1→.125插值。若刻意改成0，应明确改变规格及对应验收，不再称为原版声明。
- **依据**：research/sprint-20261024/junkrat-current-calibration1/current-volleys.json内022b对应rows的blast.outerScale=.125。

### F07 — 连续伤害fixture覆盖原始快照，cleanup恢复错误HP和游戏规则【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeCombatScene.java:84–88、484。
- **问题**：injureForHealing每次都覆盖savedHealth和savedRegeneration；recallHurt为了保留场景直接重入它，没有先释放旧快照。
- **为什么会出错**：初始20HP、自然恢复true时，调用两次recall-hurt，第二次保存的是2HP和false。cleanup最终也恢复2和false，丢失最初的世界规则及健康状态。
- **建议修法**：同一owner和world首次进入才保存快照，后续受伤操作保留最初快照；不同owner或world应先还原旧状态或拒绝。不要仅为避免重入而无条件cleanup，删掉仍需保留的实验地板。
- **建议复现**：连续两次recall-hurt→cleanup，比较最初HP与NATURAL_REGENERATION。
- **2026-10-25修复与验证**：同一玩家及世界仅首次保存HP/自然恢复快照；跨玩家或世界重入拒绝（含wraithHit入口），保留实验地板；cleanup无条件恢复已保存的自然恢复值。指定的compileClientJava已通过，未进行游戏实测，未构建或部署JAR。

### F08 — 读取失败或长断档后不重建节点基线，会从当前姿态补发旧施法【已修】

- **文件:行号**：guest/src/client/java/lab/owmcguest/NativeSkillReader.java:254–258；同目录NativeMeiSkillController.java:25–29、NativeJunkratController.java:25–27、NativeHanzoSkillController.java:18–23、NativeGrappleController.java:27及40–43。
- **问题**：Reader失败会close绑定，但控制器保留lastVolley、last[]、lastScatter等水位；恢复后只检查当前logger tick大于旧水位，没有技能事件发生时间及最大准入延迟。
- **为什么会出错**：logger保留最近一次状态，不是仅含当前帧事件的队列。断档期间原版完成一次技能，数秒后恢复时，就会从玩家现在的眼睛和方向补造那次旧投掷。host当前帧新鲜，不等于logger那条旧状态新鲜。
- **建议修法**：失去可信读取或超过允许断档后，使节点水位失效，恢复的第一份一致快照重新作基线；或使用具有原版时钟关联、过期门限和去重的事件序列。不要简单要求Volley的active=true：瞬时Volley可在同一原版tick完成，正常采样只看到finished=true。
- **建议复现**：已有基线→阻断读取→期间施法一次→移动、转向→恢复读取，不得从新位置迟发旧技能。

### F09 — 冰墙预览更新不发布，实测状态可能一直看不到previewing【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeIceWallRuntime.java:49–52、61。
- **问题**：preview写previewing、previews、scope并产生粒子，但没有publish；尚未建墙时，tick因wall==null立即返回。
- **为什么会出错**：只打开预览、取消或找不到地面时，status可一直为旧的空对象或旧previewing值，依赖状态的测试会超时或误判。
- **建议修法**：预览状态变化时，以及所有需要反映取消或拒绝的返回路径，都发布一致快照，避免把发布只系在已建成墙的tick上。

### F10 — 最后一个中毒目标死亡时，poisoned状态不会清零发布【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeVenomRuntime.java:89、51。
- **问题**：死亡或找不到目标的分支从map移除后直接continue，没有publish。
- **为什么会出错**：若此时没有mine，移除的又是最后一个poison，外层51行因map已空也不publish并返回。status可能一直保留poisoned=1，直到下次投雷或全局reset；这是状态失真，不是仍有实际伤害。
- **建议修法**：记录dirty，在tick末或早退前统一发布；所有移除路径都需要反映到状态。
- **建议复现**：雷触发后杀死唯一中毒目标，下一server tick的poisoned应为0。

### F11 — 龙击起始箭没有进入渲染快照，已安装箭包仍不会显示Q起始箭【已修】

- **文件:行号**：guest/src/main/java/lab/owmcguest/NativeHanzoSkillRuntime.java:46–48、68、94；guest/src/client/java/lab/owmcguest/JunkratRenderer.java:29–34。
- **问题**：dragon()只创建Dragon对象；未released时模拟20m/s起始箭，约10个MC tick达到10米，但arrowViews只遍历散射arrows。
- **为什么会出错**：renderer也只读arrowViews，因此这一阶段没有箭模型，装好hanzo-arrow资源包不能改变这个事实。
- **建议修法**：把未released的Dragon起始箭作为带身份的ArrowView发布，转换成龙阶段时移除；不需要伪造尚未认证的原版龙体模型。
- **2026-10-25修复与验证**：ArrowView携带Scope；publish将未released的Dragon起始箭按当前位置及起始速度加入同一渲染列表，转成龙后不再发布箭。沿用现有hanzo-arrow绘制路径；指定的compileClientJava已通过，未实测可见像素，未构建或部署JAR。本文原行号及文末SHA256仍为原审查快照。

### F12 — 通用渲染器不校验视图世界和身份，换维度会画旧世界快照【已修】

- **文件:行号**：guest/src/client/java/lab/owmcguest/JunkratRenderer.java:18、24、29–40；guest/src/main/java/lab/owmcguest/NativeJunkratRuntime.java:28、NativeHanzoSkillRuntime.java:34。
- **问题**：暴雪和冰墙View已有world字段，但renderer只看时间；狂鼠和箭View连world、owner、source、model及发布时间都不携带。
- **为什么会出错**：客户端已切到新world、排队的服务端reset尚未执行时，旧坐标仍会按新相机和光照绘制。服务端停顿时，狂鼠和箭也没有快照过期裁剪。全局reset能缩短窗口，不能让跨线程已发布的快照天然具备新世界身份。
- **建议修法**：像VenomMineRenderer一样校验当前world及owner；为批量箭和狂鼠快照补齐完整Scope及发布时间，使用同一不可变Snapshot原子发布，再按当前原版身份和新鲜度过滤。
- **建议复现**：有飞行物或冰墙时快速跨维度，并延迟server任务；新世界不得出现旧快照。

### F13 — 显示租约对注册表刷新率使用矛盾判定，非temporary启动会误失败

- **文件:行号**：tools/native_display_mode.py:214；同类严格比较还在164、229、235行。
- **问题**：42–45行已承认本机驱动可将注册表200Hz回读为60Hz，定义了按尺寸和色深比较的same_registered，但改变模式后的acquire和bind仍用完整signature比较注册表。
- **为什么会出错**：nativeDisplayTemporary=false时，即使当前桌面已正确为1920×1080@200，注册表尺寸和色深也正确，仅回读Hz=60仍会抛错，receipt停在preparing，阻断正常启动。
- **内存验证**：抽取当前Mode、signature、same_registered及DisplayLease执行，仅使用内存Display、MemoryPath和身份桩；结果为Fullscreen display readback differs; normal stop must restore the receipt，current=[1920,1080,200,32]、registered=[1920,1080,60,32]，same_registered却为true。未触碰真实屏幕、进程或磁盘备份。
- **建议修法**：统一各分支的注册表size和bits规则；当前模式仍必须完整匹配Hz，不能为了修此项放宽实际桌面刷新率。保留existing temporary路径及原始备份完整性检查。

## 未接线项与排除的误报

- **NativeTorbjornRuntime**：原审查时，全源树未找到deploy或throwPack调用，也没有GuestMod tick、停止事件或NativeSessionGuard reset注册。文件注释本来就写触发节点待校准后接入。现状无法做原版触发的炮台和护甲包实测，应列为未接入，不冒充已完成路线的回归bug。未来接入还需炮台受伤、维修及升级路由，原审查时private health没有扣减入口。
- **狂鼠遥爆**：原审查时detonateMine没有调用者，控制器注释也明确待校准；不把已声明的未接项包装成右键偶发失效。
- **线程**：已追到WorldFrameExporter的client tick→server.execute，以及NativeSessionGuard的resetServerState。所列server容器常规写入在服务端线程，发布的View和List为volatile不可变快照。没有发现可直接证实的常规并发修改异常，不因为存在两个线程就泛报ConcurrentModificationException。F01是world归属错误，F12是快照身份缺失，不是容器本身不线程安全。
- **节点Begin和End**：已保存的暴雪及散射校准确有瞬时Volley最终finished=true；prepare_native_grapple也明示同tick Begin和End。没有证据支持tick变化必然每次双发，因此未如此定性；F08针对断档恢复的旧状态重放。
- **直击加爆炸无敌帧**：原审查时data/minecraft/tags/damage_type/bypasses_cooldown.json已包含native_projectile及native_explosion，没有把原版i-frame默认机制当成本工程的必现吞伤问题。
- **冰柱加载上限与渲染比例**：原审查只读查看的已安装mei-pillar/pack.json为19980顶点、maxAbs=1.991055727、Y=0..1.991055727；乘2约3.982米，与4格墙相容。它已不是早先1150顶点、4.94米的候选导出，因此没有据旧素材断言OriginalMeshPack的4米校验必失败，或当前柱高一定9.9米。
- **其余指定文件**：四个prepare脚本的profile与NativeSkillReader对应，所有权、进程创建、节点vtable验证及按文件原子替换均已阅读，未确认其他独立缺陷。OriginalMeshPack和VenomMineRenderer的正常素材路径未发现可证实矩阵错误。这不等于已完成游戏或所有异常输入验收。

## 验证建议顺序

1. 对标记已修的F01、F02，优先在可丢弃存档复验跨世界与退出清理，确认不会改错或遗留方块。
2. 复验F03、F05、F06的最近碰撞、真实爆心、爆炸遮挡及外圈边界数值。
3. 处理拉钩源过期取消、Reader失败恢复不补发历史技能。
4. 核对预览、中毒、起始箭快照发布及跨世界渲染过滤。
5. 仅用内存后端覆盖注册表Hz回读差异；真实显示变更仍由主负责人按已有正常启动和恢复流程执行。

## 审查版本指纹

以下保留原报告中的22个指定文件SHA256，针对原审查快照，不是修复后的重新校验结果。关联调用方和本地Fabric source jar仅用于证明路径及生命周期，不在原审查修改范围内。

| 指定文件 | SHA256 |
|---|---|
| `guest/src/main/java/lab/owmcguest/NativeVenomRuntime.java` | `9cd543f5de83def1e1000ca761ed06168b0f3575511f1b1f289457b01bb31818` |
| `guest/src/main/java/lab/owmcguest/NativeBlizzardRuntime.java` | `f09a705c067bfa42e0a75fbae8712916809d78c6d83097b7a453e968034349b6` |
| `guest/src/main/java/lab/owmcguest/NativeIceWallRuntime.java` | `51d991ddc7bd3d269780b36dcffb4e6616149b7f100cf93c8c74f8d9f641d529` |
| `guest/src/main/java/lab/owmcguest/NativeJunkratRuntime.java` | `e55679e64f734f869c0b4d09c7fc624d70152a06ed8230b633f50385661937ca` |
| `guest/src/main/java/lab/owmcguest/NativeHanzoSkillRuntime.java` | `f46e797d21def30eeee5b98b8bc2e93afc7099bda1b456e653d2828f63dd888e` |
| `guest/src/main/java/lab/owmcguest/NativeTorbjornRuntime.java` | `656dda3ec0e727cddb80cfe0da7f8c2da09c63b24b875c9304d580711cb3b8e7` |
| `guest/src/main/java/lab/owmcguest/NativeMeiFreezeRuntime.java` | `6c548c4905078e397faeefeeb536555460eb84044dc1d6cec03e6aeb60d0d27e` |
| `guest/src/main/java/lab/owmcguest/NativeCombatScene.java` | `ef0b43cafceeaf97bc0001bdc217557e3446f4806a3c274aca4b0d38f872f7a8` |
| `guest/src/client/java/lab/owmcguest/NativeGrappleController.java` | `73011f2c66467c10f6124f4aa211243b866e87515e4b099595db742091e82593` |
| `guest/src/client/java/lab/owmcguest/WidowGrapplePull.java` | `7022fef18c1331ecc9c65a80d3098f16d6bc31b4d965a46e97ce76155e4aa093` |
| `guest/src/client/java/lab/owmcguest/NativeMeiSkillController.java` | `9789bf2030d3b9e9d838fd05a4ae91ca7a0c8fd882eb78d4a6d95863296729d7` |
| `guest/src/client/java/lab/owmcguest/NativeJunkratController.java` | `ed5264d5a0853b74fd68fdd410d0c1bd1592af9280c60a911d2f433a0afebb0e` |
| `guest/src/client/java/lab/owmcguest/NativeHanzoSkillController.java` | `e14e0a440aedecfceebbfc566c249a93022191c718ec0e4f40277f1f27afade1` |
| `guest/src/client/java/lab/owmcguest/NativeSkillReader.java` | `7c568705e803796c2ed3edd5a39166980e40d807ab593cc7627528069703ea46` |
| `guest/src/client/java/lab/owmcguest/OriginalMeshPack.java` | `05839176a44ccf9e0aac0925fba8d00b4f564c42eb5eec37eb9ec7c82fb13443` |
| `guest/src/client/java/lab/owmcguest/JunkratRenderer.java` | `02284714f9061559b825ee1674dfcc8e6c4953f345c28431540cff073ed670f4` |
| `guest/src/client/java/lab/owmcguest/VenomMineRenderer.java` | `c95435e28103369d5f47c18efd62b0dc3e46d58d36bc58c7470fb133a0ed7027` |
| `tools/prepare_native_grapple.py` | `353caec1a2ba2dbe35ee6998946d7e56e47ec95e4e08292453011357986585fd` |
| `tools/prepare_native_mei.py` | `e3c204ee4d3d5d8f92e9f7b8312232f89ad2fc960a96d9295c0f13e5c9dd89fa` |
| `tools/prepare_native_junkrat.py` | `3197358b804382bc5a48662f7bc638a105d69f79711c431ec97d260b107f3eb2` |
| `tools/prepare_native_hanzo.py` | `ccd96c0ee3baf08e6a95ebaab50be17a45d61da2c487972030de4cb0a1ccabc6` |
| `tools/native_display_mode.py` | `a232ec111334d54982f598791e9e1e230de556629b67a6783c58095f6aa6c35f` |

编码修复说明：UTF-8，本轮仅重写报告并标注用户告知的修复状态。
