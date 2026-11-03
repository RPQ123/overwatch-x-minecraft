"""2026-10-26 support/tanks/builders/symmetra handoff capture matrix.

All watch hints are discovery hints, NOT authorizations. Capture always reads
ALL currently owned controller/model graphs, including newly appearing graphs.
"""
from __future__ import annotations

HEROES = dict(Mercy=4, Zenyatta=0x20, Lucio=0x79, Reinhardt=7, Zarya=0x68,
              DVa=0x7a, Roadhog=0x40, Junkrat=0x65, Torbjorn=6, Symmetra=0x16)


def action(key, seconds=.12, at=0):
    return dict(key=key, at=at, seconds=seconds)


def case(hero, skill, actions, scene, native, watch, *, charge=False, group=None,
         note='', form=False):
    return dict(id=hero.lower()+'-'+skill, hero=hero, skill=skill,
                group=group or hero.lower(), actions=actions, scene=scene,
                nativeScene=native, chargeRequired=charge,
                captureGraphs='全部 graph（controller + model，含新图）',
                watchHints=watch, note=note, postCallForm=form)


CASES = [
    case('Mercy', 'pistol-select-fire', [action('2', .10), action('M1', .12, .8)],
         'mercy-pistol', '原版2切枪；当前Torb专属slot例外不等于天使已放行；不得改slot守卫',
         ['006d:10'], note='同时记录切枪和发射；不拿法杖54当手枪'),
    case('Mercy', 'guardian', [action('SHIFT')], 'mercy-guardian',
         '准星内原版可见且存活友方；MC友方不能满足原版搜索', ['006e:2,25']),
    case('Mercy', 'resurrect', [action('Q')], 'ground-lab',
         '原版死亡友方/尸体及目标身份；非MC尸体替代', ['00ca:4,5,15,36,39,40'], charge=True),
    case('Mercy', 'unknown-e', [action('E')], 'ground-lab',
         '独立E只是负向探测，不能按后续版本命名技能', ['全部 graph']),
    case('Mercy', 'glide', [action('SPACE', 1.5)], 'ground-lab',
         '原版已在空中下落；MC飞行不等于原版空中条件', ['0071:2']),
    case('Mercy', 'self-heal', [], 'mercy-passive',
         '原版真实受击且已接近自疗延时；记录原版HP回升及写入方', ['0071:4', '0033'],
         note='3秒窗口可能不足以覆盖受击延时；可分次等待后重新采样，不用MC伤害冒充原版'),
    case('Zenyatta', 'harmony', [action('SHIFT')], 'zen-harmony',
         '原版可见受伤友方', ['02f3:11,46,62']),
    case('Zenyatta', 'discord', [action('E')], 'zen-discord',
         '原版可见敌方及目标身份', ['0176:6,41']),
    case('Zenyatta', 'transcendence', [action('Q')], 'zen-transcendence',
         '原版可治疗友方；另观测自身真实免疫/HP语义', ['017b:17,19,30,31'], charge=True),
    case('Zenyatta', 'shield-recovery', [], 'ground-lab',
         '原版盾池真实受击、临近恢复；原版HP/盾池回升', ['全部 graph', '0033'],
         note='共享HealthPool存在不是独立恢复提交'),
    case('Lucio', 'boop', [action('M2')], 'lucio-boop',
         '原版近距离可命中敌方', ['0776:28,29,65']),
    case('Lucio', 'song', [action('SHIFT')], 'lucio-support',
         '原版歌曲初始状态已记录；需04/06c7动态路径，未知值不命名HEAL/SPEED', ['0266:3,9']),
    case('Lucio', 'wallride', [action('W', 1.5), action('SPACE', 1.5)], 'lucio-wallride',
         '原版空中贴原版真实墙；MC墙不等于原版判墙', ['0263:25']),
    case('Reinhardt', 'charge-contact', [action('SHIFT')], 'ground-lab',
         '原版近距离敌方/普通撞击；独立冷启动，不接着跑E', ['007d:6,11,20,31,38,63,110,128'],
         group='reinhardt-contact', note='撞击必须落在3秒采样窗内'),
    case('Reinhardt', 'charge-pin', [action('SHIFT')], 'ground-lab',
         '原版敌方+其后近墙，3秒内钉墙；独立冷启动', ['007d:6,11,20,31,38,63,110,128'],
         group='reinhardt-pin'),
    case('Reinhardt', 'fire-strike', [action('E')], 'ground-lab',
         '独立冷启动；无Shift前置动画占用', ['00e2:3'], group='reinhardt-fire'),
    case('Reinhardt', 'shatter', [action('Q')], 'ground-lab',
         '原版可用地面和敌方；独立冷启动', ['00be:1,3,13'], charge=True, group='reinhardt-shatter'),
    case('Zarya', 'projected-barrier', [action('E')], 'ground-lab',
         '原版有效友方及身份', ['025c:24,32,43']),
    case('Zarya', 'energy-absorb', [action('SHIFT')], 'ground-lab',
         '预先安排真实原版来弹在SHIFT后击中原版屏障；MC absorption不是原版受击',
         ['全部 graph', '0241 vars0035/0055'], note='比较屏障前/受击/吸收；数值变化不能自行命名能量'),
    case('Zarya', 'energy-decay', [], 'ground-lab',
         '原版已吸收来弹，衰减阶段；同组同英雄', ['全部 graph', '0241 vars0035/0055']),
    case('DVa', 'call', [action('Q')], 'dva-pilot-attempt',
         '当前已认证驾驶员；记录每次hero/model/controller及新图，不推定呼叫成功',
         ['026a:17,25,39,41,50,77,96,107,109', '全部 graph'], charge=True),
    case('DVa', 'postcall-cannon', [action('M1', 1.5)], 'ground-lab',
         'Claude已另行确认原版呼叫后实际形态；使用--form-from，不重新选驾驶员',
         ['全部 graph'], form=True),
    case('DVa', 'postcall-boost', [action('SHIFT')], 'ground-lab',
         '同一呼叫后的实际形态与原版移动条件', ['全部 graph'], form=True),
    case('DVa', 'postcall-matrix', [action('M2', 1.5)], 'ground-lab',
         '同一呼叫后的实际形态，原版来弹；M2仅探测不预设技能归属', ['全部 graph'], form=True),
    case('DVa', 'postcall-selfdestruct', [action('Q')], 'ground-lab',
         '同一呼叫后的实际形态；另行充满当前形态原版Q', ['全部 graph'], charge=True, form=True),
    case('DVa', 'postcall-unknown-e', [action('E')], 'ground-lab',
         '同一呼叫后的实际形态；只探测E，未确认此Beta有微型飞弹', ['全部 graph'], form=True),
    case('Roadhog', 'hook-damage', [action('SHIFT')], 'ground-lab',
         '原版钩子可命中目标及目标身份，接触在3秒内', ['01c8:19,21']),
    case('Roadhog', 'secondary-split', [action('M2', 1.5)], 'roadhog-split-lab',
         '原版父弹约9m后到期；观察子工厂/owner/父子关联，不能拿近端伤害替代', ['全部 graph'],
         note='只读已有且新鲜的emission诊断；未开启时不能证明无子工厂'),
    case('Junkrat', 'tire-create', [action('Q')], 'ground-lab',
         '原版可放轮胎地面；创建与possess实际提交', ['0232:7,10,11,32', '0233'], charge=True,
         note='10秒结束不在3秒窗内；需后续独立tire-end采样'),
    case('Junkrat', 'tire-end', [], 'ground-lab',
         '同英雄原版轮胎已在控制中，临近真实possess结束；使用--keep-selected', ['0232:7,10,11,32', '0233']),
    case('Junkrat', 'death-passive', [], 'ground-lab',
         '预先安排原版真实致死事件在窗口内发生；不发kill/不伪造MC死亡为原版事件', ['022a:10,11,13,14,15,16', '全部 graph']),
    case('Torbjorn', 'hammer-select', [action('2', .10)], 'ground-lab',
         'Torb专属1/2守卫例外已由集成者认证；未放行也保留无变化证据', ['00f3', '全部 graph']),
    case('Torbjorn', 'hammer-strike', [action('M1')], 'ground-lab',
         '已用原版2真正切锤且面向原版接触目标；--keep-selected', ['00f3:10,23,24,29']),
    case('Torbjorn', 'hammer-repair', [action('M1', 1.5)], 'torb-repair-lab',
         '原版已损坏炮台，已切锤，原版接触距离；MC炮台不满足原版修理目标', ['00f3:10,24,29']),
    case('Torbjorn', 'scrap', [action('W', .5)], 'torb-scrap-lab',
         '原版真实死亡掉落废料在近前；不调用MC资源入账', ['全部 graph'],
         note='MC废料已有明确适配；此项只寻找原版资源写入语义'),
    case('Torbjorn', 'core', [action('Q')], 'ground-lab',
         '原版Q可用；观察原版护甲池/炮台/攻速', ['01c2:17,19,20,21,30', '00f3'], charge=True),
    case('Torbjorn', 'core-end', [], 'ground-lab',
         '原版Core已active且临近真实结束；--keep-selected；首样本active不重放', ['01c2:17,19,20,21,30']),
    case('Symmetra', 'beam-damage', [action('M1', 1.5)], 'symmetra-beam-lab',
         '原版光束可命中敌方，非仅MC UUID', ['0139:16,77,89,107']),
    case('Symmetra', 'photon-shield', [action('E')], 'symmetra-ally-lab',
         '原版有效友方及目标身份；子图01c4在目标运行，当前拥有者不可见时明确标缺口', ['01c3:3,16,27', '01c4:1']),
    case('Symmetra', 'turret', [action('SHIFT'), action('M1', .12, .5)], 'symmetra-placement',
         '准星指向原版可放置近地面，预览后确认', ['017e:2,32,35,47']),
    case('Symmetra', 'teleporter', [action('Q'), action('M1', .12, .4)], 'symmetra-placement',
         '原版可放置近地面；等待2秒，尽早确认以纳入3秒窗', ['0169:2,42,66,74,79'], charge=True),
    case('Symmetra', 'shield-recovery', [], 'ground-lab',
         '原版自身盾池受击后接近恢复；HP/盾池回升而非共享0033存在', ['全部 graph', '0033']),
    case('Symmetra', 'shield-ammo-probe', [action('M1', 1.5)], 'ground-lab',
         '原版敌方护盾可被光束命中；后续版本返弹仅为未知探测', ['全部 graph', '0139']),
]

BY_ID = {row['id']: row for row in CASES}


def markdown_table():
    rows = ['| 会话组 | 英雄/技能 | 原版动作（秒，@起始秒） | 授能 | MC场景 / 原版前提 | 观测 |',
            '|---|---|---|---|---|---|']
    for c in CASES:
        actions = ', '.join(f"{a['key']} {a['seconds']:g}@{a['at']:g}" for a in c['actions']) or '无输入，等待真实事件'
        rows.append(f"| {c['group']} | {c['hero']}/{c['skill']} | {actions} | {'需预充，脚本不写' if c['chargeRequired'] else '否'} | {c['scene']}；{c['nativeScene']} | 全部graph；重点 {'; '.join(c['watchHints'])} |")
    return '\n'.join(rows)
