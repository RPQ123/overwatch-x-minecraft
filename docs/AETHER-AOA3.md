# 天堂与虚无世界3：兼容边界和实际接入

用户2026-10-24约11:41调整优先级：暂后排托比昂/暮色战斗，先接入虚无世界3与
天堂，并扩展F12随机Boss和解决旧Boss血条残留。原13:00计划已结束；用户
13:20重新要求继续全部Boss与F8传送门，当前仅保留单线程约束。最新实际范围
见ALL-INSTALLED-BOSSES.md、PORTAL-MENU.md和TAKEOVER最新节；下文含历史状态。

## 当前实际包

天堂为作者官方Fabric1.21.1版本1.5.11，实际安装到既有停止后的独立profile；
SHA256 `5909f195eb995f3760de5acff197e4c32029c5941d32320bc4a84c90bee79faf`。
下载自[官方Modrinth版本](https://modrinth.com/mod/aether/version/NSqdh1i9)，
API文件SHA512、实际Fabric元数据和整个文件SHA256均已核对。嵌入Accessories、
Cumulus、ForgeConfigApiPort等6个依赖；所需owo使用稳定版0.12.15.4+1.21，
SHA256 `825180ce17bc012fb450653b14df9f32479dcdd073fc3f133bb47462f5a63cec`。
最初仅缓存的owo alpha没有装入生产。`tools/boss_mods.py`在开存档前检查安装
清单/哈希/实际Fabric ID版本，缺失或换包拒绝开图；原世界和profile已完整备份。

虚无世界3作者[官方文件7424722](https://www.curseforge.com/minecraft/mc-mods/advent-of-ascension-nevermine/files/7424722)
实际下载为AoA3-1.21.1-3.7.16.1.jar，139631628字节，CRC通过，SHA256
`16da1e00373bd854f0397c28d5b0d2c376e6eeec97135b35cac48607e4bfe66b`。
实际neoforge.mods.toml要求NeoForge>=21.1.200，没有fabric.mod.json，不能直接
装入当前Fabric融合profile。原包已经嵌入GeckoLib4.8.2、TslatModdingExtensions
1.0.0、SmartBrainLib1.16.10、hsqldb2.7.4；不需要另放较新的GeckoLib去覆盖它。
单独准备的`aoa3-neoforge-client`仅为隔离兼容profile，尚未证明OW融合可用。

NeoForge21.1.264官方安装器和官方Maven SHA1已经核对。Java下载多个库超时的
失败日志保留；Python在既有网络设置下，按原安装器的URL/SHA1预取46个缺失库，
随后同一个官方安装器真实exit0并报告安装成功。只结束过精确匹配的安装器Java，
没有强杀游戏或修改系统代理。

`aoa3-neoforge-client`已经实际加载AoA和天堂到原生NeoForge主菜单，正常关闭通过。
天堂NeoForge版为1.5.10，和Fabric的1.5.11分别记录，不混称同包。其外部依赖为
官方owo NeoForge0.12.15.6-beta.1与Forgified Fabric API0.116.15+2.3.6。
`required-mods-extra.json`保存官方版本/URL/SHA512/SHA256；没有NeoForge稳定owo，
因此这里使用作者明确标记的beta，不冒充稳定版。

实际融合使用单独的`aoa3-connector-client`、[官方Connector](https://connector.sinytra.org/)
2.0.0-beta.17+1.21.1，原JAR SHA256
`ca70b57df3a7a4e8d211fea7ff3ae77e768482af374f26bf953ff5fd755564f0`。
它把未修改的Fabric桥接转换到NeoForge；没有移植/降版AoA，没有降低桥接依赖检查，
没有开启隔离的旧原生实验。实际新建`Overwatch Twilight Switch AoA Compatibility Lab`，
已存在13个真实维度（包括AoA和天堂），真实MC画面/depth输出、六原生适配器和麦克雷
原生扣弹/真实MC掉血已通过。它是基础接入验收，非所有英雄/所有AoA Boss完整验收。

专用入口`launchers/Launch-Overwatch-AoA.cmd`与`launchers/Stop-Overwatch-AoA.cmd`调用
`tools/aoa3_passthrough_lab.py`，复用原生产监督/严格恢复/正常关停，PROFILE限定为
NeoForge隔离世界。入口已实际启动，专用Stop已实际保存并正常退出，关闭失败不强杀。
原默认Fabric设置和旧暮色存档保留；NeoForge环境绝不打开缺暮色模组的旧世界。
两套启动入口互斥；换环境先用当前环境的Stop正常关闭，再使用另一套Launch。

包、原元数据、源码检查和下载日志在
`~/.universal-modder/mod-cache/boss-mods-20261024/`，不进入提交。
完整开工前备份：`~/.universal-modder/backups/aether-random-boss-20261024-114658`。

## F12和血条策略

保留1–8原暮色入口。9随机尝试各已加载维度的真实Boss，识别已校准根实体、
作者`c:bosses`标签及AoA Boss基类；不包含测试Boss、不按高血量猜Boss。
没有可用已加载Boss时随机定位已验证的原暮色目录及随机查询扇区。
未加载Boss的AoA祭坛/原生召唤流程尚未接通；不能把这部分称作任意AoA Boss直达。
没有暮色模组时，9可定位已实测的原天堂铜地牢；必须观察到真正活Boss才成功。
0为天堂随机原生地牢入口：定位作者实际bronze/silver/gold结构与实际BossRoom，
等真实区块/实体载入，检查原地板与空间，绝不挖空落点或召唤替代Boss。

`aether-dungeon-live1`失败：GoldBossRoom的FULL/实体载入后未找到Boss；
`live2`失败：到真实SilverBossRoom并等玩家区块票后仍无Boss。两份失败保留。
原包NBT确有slider/valkyrie_queen/sun_spirit实体及正生命值，缺失来源尚未证明。
后续0入口只可按真实原房间/安全落点记传送成功，`bossPresent=false`明确保留；
不能将其记为Boss战或原生Boss生成通过。`live3`真实通过的是入口传送，不是Boss。
后续NeoForge的`aoa3-aether-travel1`则真实找到原BronzeBossRoom与Slider原实体UUID；
`aoa3-boss-hud-roundtrip2`在9号随机入口又找到另一真实Slider，生成/定位证据通过。
没有召唤替代Boss，也没有认证Slider的完整战斗/奖励/重置。

血条保持原版BossBarHud绘制和原数据包。传送选择时只退役旧UUID，旧进度包
不恢复显示；原服务器REMOVE清理、真正ADD允许再显示同一Boss。传送失败回滚
本次退役，不改Boss实体/生命/原血条Map；渲染过滤同步覆盖MC窗口与融合导出。
异步PBO读回额外核对传送epoch，旧缓存不能重新发表。纯生命周期fixture通过，
`boss-hud-roundtrip1`已在Fabric真实通过：原End龙血条→9离开后旧UUID消失→实际
回End同UUID由原服务器ADD重新显示。`aoa3-boss-hud-roundtrip2`在NeoForge又真实
通过同样闭环，画面都已查看。不要只凭JSON计数冒充可见血条验收。

## 当前版本和未完成范围

最终菜单修正候选guest为`04a79a38e8e9e9109856ad1e56c04dad1b4cf7b6d5e1704c054bcb58e491d608`，
源码/构建/两个profile已冷部署；未安装的暮色/天堂菜单项置灰，拒绝发送无效服务端
请求。56Gradle任务通过。最终实际CMD冷启动后，`aoa3-final-boss-menu3`通过缺失
暮色入口的本地拒绝/不发服务端请求、9号真实Slider与原End血条往返；`aoa3-final-hit3`
通过原生麦克雷扣弹/真实MC伤害/清理。`aoa3-final-ground-picker2`通过恢复自然地面、
关闭测试飞行、实际W移动、20HP和最终原生选人画面。六42/26/11/16/10/1模块不变。
原ground-picker1只在最后使用已关闭的测试driver失败；地面/移动已过，未改写，
第二轮使用新的独立driver完成收尾。最终索引为aether-aoa3-acceptance.json。

最终实时线索为native22548(created1792815905.3526216)、MC2016(created1792815884.6385078)，
专用独立监督32060/33648；下一轮必须重核，不能复用历史PID当授权。原生麦克雷
动画选人/主世界村庄背景已实际查看；20HP、自然地面、测试对象/方块已清理。
启动入口实际点开后已通过这轮测试；再次点击已有监督时由同一mutex拒绝重复所有者。

失败保留：AoA基础hit1普通目标位置未就绪，未验证攻击；hit2改用既有可逆空中场景
后真实扣弹/掉血通过。原Fabric天堂空房根因仍未证明，不用NeoForge铜地牢成功
宣称它已修复。AoA所有未加载Boss祭坛/召唤、战斗阶段、弱点/计分、全部英雄跨13
维度、NeoForge性能和完整早期技能声音仍待验证。保留原Boss伤害免疫/弱点，不绕过。
13:00截止不变，12:20后只收尾既有兼容回归，12:40冻结。
最终源码/配置/构建/验收索引备份为
`~/.universal-modder/backups/accepted-aoa3-fusion-20261024-123220`（239个文件校验登记）；
默认`passthrough-settings.json`已逐字节对比开工前备份，保持相同。
