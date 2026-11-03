"""Classify the local THNU catalogue; never fetch audio or touch game profiles.

Run with .venv/Scripts/python.exe tools/classify_voice_catalog.py.
Confidence measures event attribution, NOT recording age/language/authenticity.
Unknown audio and ambiguous subtitles are deliberately left for human review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research/voice-catalog-20261025"
PRIVATE = Path.home() / ".universal-modder/assets/ow1-zhcn-2016/thnu-three"
RULE_VERSION = "2026-10-25.1"
BASE_EVENTS = (
    "select", "ult_cast", "ult_ready", "ult_charge", "kill", "multikill",
    "death", "pain", "jump", "effort", "respawn", "low_health",
    "healing_request", "comm", "idle", "reload", "skip", "uncertain",
)
NAMES = {
    "bastion": "堡垒", "dva": "D.VA|D.Va|d.va", "genji": "源氏",
    "hanzo": "半藏", "junkrat": "狂鼠", "lucio": "卢西奥|卢西歐",
    "mccree": "麦克雷|卡西迪", "mei": "美|小美", "mercy": "天使",
    "pharah": "法老之鹰|法老之鷹", "reaper": "死神",
    "reinhardt": "莱因哈特|莱恩哈特|莱茵哈特", "roadhog": "路霸",
    "soldier76": "士兵:76|士兵：76|士兵76|76", "symmetra": "秩序之光",
    "torbjorn": "托比昂|托比昻", "tracer": "猎空",
    "widowmaker": "黑百合", "winston": "温斯顿",
    "zarya": "查莉娅|查莉雅|查理娅|查利娅", "zenyatta": "禅雅塔|禅亚塔",
}
ALIASES = {unicodedata.normalize("NFKC", n).casefold(): hero
           for hero, names in NAMES.items() for n in names.split("|")}

# Curated source IDs already recorded in the project's private provenance.
# This table contains identifiers only; it does not bundle recordings.
SELECT_HASHES = dict(zip(NAMES, (
    "", "549b3a9d41589cde571567036e95e77f", "810e91d0c24694c6b52666d25bb636b5",
    "efad86eebee631c05da502d8a1de5f07", "bc3a9c99c5e6af2b230f8225d9f5f4c5",
    "23c9f88ddb5262e5e4fc17627bfe90df", "991f3a83f7523027ceb010752fc1da0b",
    "6d1a9b11798fee6551e73ff42df70e1b", "63d5d0b7b9cb5ee8eedcf5aa10802b7a",
    "b1fcb2d37237a7be1899752b6ec36dda", "745365173c284615096c1e26c200f7c1",
    "6c87dc91f63dab388d8c76664c827619", "f10fd491265a331626e914ea8e8e627a",
    "9c56b907c233a6c7c67c0f4de4dc5501", "e6478bb87704cf9449894dc6f1fbf8af",
    "2757b9ccbb57642277609b0c45c6556a", "83cbf1a95ec7b7afaa645565262e2a2e",
    "c663dcb0b5d5ac37c468e241adf568d8", "745a5fa96cd1f868715f884ba6599f54",
    "f4eca151b65b7045040a0ba586d2c25c", "283fc41c9752568460ff4a7d6070dc60",
)))
PINNED = {h: (hero, "select") for hero, h in SELECT_HASHES.items() if h}
PINNED.update({
    "2992ca54981022e7c26eca0293b9370d": ("genji", "ult_cast"),
    "0d90c994cf3f09bc15dfe9e7c9f65620": ("genji", "ability:deflect"),
    "6b9acbf19b0848e29b6eb3837ad1be12": ("genji", "ability:deflect"),
    "0a524e033af327ccfd269b017ab96b02": ("genji", "ability:deflect"),
    "0a3f2602bf353c130e51f4d661624ef9": ("mccree", "ult_cast"),
    "92a63442f332604d59ac4cb18c1e1691": ("mccree", "ability:flashbang"),
    "bb29e935ab59e620480b3ca49f8ea9e8": ("mccree", "ability:flashbang"),
    "8a14c70b59d42fe88c1e0bc2266293bf": ("mccree", "ability:flashbang"),
    "65e50320e5621d5be2792b37e153c171": ("pharah", "ult_cast"),
    "7fd81f959836f68c79fd64c95d26ca22": ("pharah", "ability:jump_jet"),
    "378facda107090face87912925ba6313": ("pharah", "ability:hover"),
})

def compact(text: str) -> str:
    """Compare punctuation variants, never substring-match a classic shout."""
    return "".join(c.casefold() for c in unicodedata.normalize("NFKC", text)
                   if unicodedata.category(c)[0] not in "PZS")

def parsed(text: str) -> tuple[str, list[str], list[str]]:
    text = unicodedata.normalize("NFKC", text).strip()
    owners = []
    # Strip repeated owner prefixes, but retain event annotations such as 【跃】.
    while m := re.match(r"^【([^】]+)】\s*", text):
        owner = ALIASES.get(m[1].casefold())
        if owner is None:
            break
        owners.append(owner)
        text = text[m.end():]
    notes = re.findall(r"\(([^)]*)\)|【([^】]*)】|\[([^\]]*)\]", text)
    notes = [next(v for v in group if v) for group in notes if any(group)]
    core = re.sub(r"\([^)]*\)|【[^】]*】|\[[^\]]*\]", "", text).strip()
    return core, notes, owners

def exact_map(rows: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return {h: {compact(t): e for e, texts in mapping.items() for t in texts.split("|")}
            for h, mapping in rows.items()}

# Only distinctive default-kit lines; vague taunts remain uncertain.
EXACT = exact_map({
    "genji": {"ult_cast": "人龙合一|尝尝神龙之刃", "ability:deflect": "放马过来|放马过来吧|呵来吧|反弹"},
    "mccree": {"ult_cast": "午时已到", "ability:flashbang": "站住别动|别动|好了别动"},
    "pharah": {"ult_cast": "天降正义", "ability:jump_jet": "起飞"},
    "reaper": {"ult_cast": "死吧死吧死吧|正在肃清敌人", "ability:shadow_step": "从阴影中降临|正在转移位置|重新部署"},
    "soldier76": {"ult_cast": "战术目镜启动|我看到你们了|我看见你们了|我看到你了",
                  "ability:biotic_field": "到我这儿来恢复|到我这里来恢复"},
    "tracer": {"ult_cast": "炸弹来喽|炸弹来咯|有人给你送炸弹了"},
    "hanzo": {"ult_cast": "让巨龙吞噬你|巨龙吞噬一切", "ability:scatter_arrow": "散",
              "ability:sonic_arrow": "未知不再神秘|巨龙看透一切"},
    "mei": {"ult_cast": "冻住不许走|冻住不准走|都给我冻住|冻住不许动",
            "ability:ice_wall": "哼哼冰墙升起来吧|冰墙升起来吧"},
    "junkrat": {"ult_cast": "炸弹来啦|女士们先生们炸弹轮胎滚起来啦"},
    "torbjorn": {"ult_cast": "熔火核心", "ability:armor_pack": "护甲包就在这儿|这有护甲包|快来拿护甲|护甲包在这|快来拿护甲包|武装起来",
                 "ability:turret_deploy": "炮台已部署|嘿嘿嘿造完炮台有人就得吃苦头了"},
    "widowmaker": {"ult_cast": "没人可以躲过我的眼睛|没人能躲过我的眼睛"},
    "reinhardt": {"ult_cast": "吃我一锤", "ability:barrier": "屏障激活",
                  "ability:charge": "冲锋"},
    "roadhog": {"ability:chain_hook": "过来吧|唔过来吧"},
    "winston": {"ability:barrier": "屏障激活|屏障已激活"},
    "lucio": {"ult_cast": "哦在这停顿|哦在这停顿吧|哦来点音乐|哦让我们来点音乐|哦在这停顿一下",
              "ability:amp_it_up": "哦加大音量|加大音量|音量到11了",
              "ability:crossfade_speed": "加速|哦喔喔加速|节奏加快喽",
              "ability:crossfade_heal": "啊哈哈音乐疗法"},
    "mercy": {"ability:damage_boost": "伤害已增强|伤害已提高|伤害强化已启动|已强化",
              "ability:heal_beam": "正在治疗你的伤口"},
    "symmetra": {"ult_cast": "传送面板上线我已经打开通路|我的传送面板已上线继续执行任务吧|我的传送面板已上线我们行动会更加迅捷|我的传送面板已上线",
                 "ability:sentry_turret": "正在部署哨戒警卫|哨戒警卫就绪|哨戒炮已就位|哨戒炮就位|哨戒炮已启动|哨戒炮已就绪|哨戒炮部署完毕",
                 "ability:photon_shield": "我会用护盾强化你|护盾启动|护盾序列已生成"},
    "zenyatta": {"ult_cast": "感受宁静|遁入智瞳"},
})

ABILITY_NOTES = {
    "genji": {"反弹": "deflect", "疾风击|迅影突击": "swift_strike"},
    "mccree": {"闪光弹|闪光弹语音": "flashbang", "战术翻滚": "combat_roll"},
    "pharah": {"推进背包|喷气背包|跳跃喷射": "jump_jet", "震荡冲击": "concussive_blast"},
    "reaper": {"暗影步|暗影传送": "shadow_step", "幽灵形态": "wraith"},
    "soldier76": {"生物力场": "biotic_field", "螺旋飞弹|螺旋火箭": "helix_rockets", "疾跑": "sprint"},
    "tracer": {"闪现": "blink", "闪回|回溯": "recall"},
    "hanzo": {"爆裂箭|散射箭": "scatter_arrow", "音|音波箭": "sonic_arrow"},
    "mei": {"冰墙": "ice_wall", "急冻|冰箱|冰封": "cryo_freeze"},
    "junkrat": {"震荡地雷": "concussion_mine", "捕兽夹|陷阱": "steel_trap"},
    "torbjorn": {"丢下护甲包|扔护甲包": "armor_pack", "部署炮台": "turret_deploy"},
    "widowmaker": {"抓钩|钩爪": "grappling_hook", "剧毒诡雷部署": "venom_mine"},
    "reinhardt": {"冲锋": "charge", "烈焰打击": "fire_strike", "屏障激活": "barrier"},
    "roadhog": {"链钩": "chain_hook", "呼吸器|呼吸回血": "take_a_breather"},
    "winston": {"跳跃背包": "jump_pack", "屏障发射器": "barrier"},
    "zarya": {"粒子屏障": "particle_barrier", "投射屏障": "projected_barrier"},
    "lucio": {"加速": "crossfade_speed", "治疗曲": "crossfade_heal", "强音": "amp_it_up"},
    "mercy": {"天使之杖右键": "damage_boost", "治疗光束": "heal_beam", "守护天使技能": "guardian_angel"},
    "symmetra": {"哨戒炮": "sentry_turret", "护盾": "photon_shield"},
    "zenyatta": {"谐|谐之珠": "harmony_orb", "乱|乱之珠": "discord_orb"},
    "dva": {"防御矩阵": "defense_matrix", "推进器": "boosters"},
    "bastion": {"变形": "reconfigure", "自我修复": "self_repair"},
}
ULT_NAMES = {
    "bastion": "坦克|终极技能", "dva": "自爆|呼叫机甲|召唤机甲",
    "genji": "龙刃|神龙之刃", "hanzo": "龙击|开大", "junkrat": "炸弹轮胎|轮胎",
    "lucio": "音障", "mccree": "神射手|午时已到", "mei": "暴雪",
    "mercy": "重生", "pharah": "火箭弹幕|天降正义", "reaper": "死亡绽放|我方大招",
    "reinhardt": "裂地猛击", "roadhog": "鸡飞狗跳|终极技能语音",
    "soldier76": "战术目镜", "symmetra": "传送面板|传送门部署",
    "torbjorn": "熔火之心|熔火核心", "tracer": "脉冲炸弹",
    "widowmaker": "红外侦测", "winston": "原始暴怒|大招怒吼",
    "zarya": "重力喷涌", "zenyatta": "圣|遁入智瞳",
}

CONTEXT = (
    ("later_content", r"守望先锋2|守望先锋归来|OW2|202[0-9]|2019|2\.0版本|5[Vv]5|后期版本|后续版本|新版本"),
    ("later_hero", r"安娜|黑影|奥丽莎|末日铁拳|莫伊拉|布[丽里]吉塔|破坏球|哈蒙德|艾什|鲍[勃伯]|巴蒂斯特|西格玛|回声|索杰恩|雾子|拉玛刹|生命之梭|伊拉锐|毛加|朱诺|骇灾|弗蕾娅|无漾"),
    ("mode", r"怪鼠|狂鼠复仇|弗兰狂|狂斯鼠|科学怪|女巫仆|僵尸|机械僵|亡灵大军|爆破者|召唤师|灭除者|刺杀者|切割者|OR14|叛乱|国王行动|行动档案|威尼斯行动|哈瓦那行动|风暴行动|街机|卢西奥动感|动感斗球|卢西奥足球|卢西奥运动|雪球大炮|雪球攻势|雪球大战|雪球死斗|雪域狩猎|夺旗|旗帜|旗手|运载|载具|货物|目标点|占领|夺取目标|攻击目标|进攻目标|防守目标|保护目标|防御目标|守住目标|目标区域|据点|检查点|进度点|回合|加时|比赛开始|比赛结束|战局|倒计时|五[、,]四|5[、,]4|敌人全部被消灭|全场最佳|最佳表现|特写|五赞|投票|赞赏|获赞|教学|教程|技能演示|演示音效|演示动画|展示动画"),
    ("map", r"直布罗陀|好莱坞|国王大道|花村|沃斯卡娅|伊利奥斯|漓江|尼泊尔|努巴尼|多拉多|66号公路|艾兴瓦尔德|绿洲城|阿努比斯|监测站|南极洲|生态监测站|釜山|暴雪乐园|里阿尔托|巴黎|哈瓦那|渣客镇|吉拉德堡|地平线|月球基地|铁坂|在这里长大|又回家了"),
    ("season_skin", r"万圣|圣诞|铃儿响|新年|春节|新春|恭喜发财|红包|情人节|复活节|夏季运动|奥运|纪念日|周年|皮肤|女巫|魔女|魅魔|魔术师|胜利女神|瓦尔基里|希格露恩|归零堡垒|幺鸡堡垒|爵士|邪鬼|白狼|独狼|黑狼|狼魂|飞龙在天|恶魔|赛博|天狗|七夕|舞狮|铁甲战魂|灾厄女王"),
    ("incompatible_kit", r"女武神|重生E|烈箭|风暴箭|光子屏障|现实由我来掌控|Yahi param|微型飞弹|微型导弹|超负荷|过载技能"),
    ("other_native_condition", r"纳米激素|激素强化|被安娜|被天使|天使复活|另一天使|复活我|复活我们|复活队友|复活他们|队友.*复活|他们复活|敌人复活|需要复活|我需要护盾|需要更多护盾|我需要护甲|需要更多护甲|被强化|被冰冻|被冻住|被冻|被电击|被电|被烫|被燃烧|剧毒诡雷.*咳|触发剧毒诡雷|被钩|被冲撞|睡眠|中毒|debuff|护盾发生器|护盾反应井|敌人.*传送|敌方.*传送|敌人.*炮台|敌方.*炮台|发现.*炮台|炮台.*不是我的|狙击手|左边|右边|正面冲|侧翼|身后|敌人.*来了|发现敌人|看到敌人|看见敌人|敌人就在|发现目标|这里有敌人|发现.*敌|队友.*阵亡|友方.*击杀"),
)

def decision(event: str, confidence: float, reason: str, **extra) -> dict:
    return dict(event=event, confidence=confidence, reason=reason, **extra)

def classify(hero: str, row: dict) -> dict:
    core, notes, owners = parsed(row["text"])
    text = unicodedata.normalize("NFKC", row["text"])
    body = text
    while (m := re.match(r"^【([^】]+)】\s*", body)) and m[1].casefold() in ALIASES:
        body = body[m.end():]
    n = " / ".join(notes)
    c = compact(core)
    if owners and any(owner != hero for owner in owners):
        return decision("skip", 1.0, "other_speaker: 目录英雄与台词说话者前缀不一致")
    pinned = PINNED.get(row["hash"])
    if pinned and pinned[0] == hero:
        if row["hash"] == "378facda107090face87912925ba6313":
            return decision("ability:hover", .82, "project_source: 已有推进背包素材；无字幕，需区分喷气音效与喊声", audio_review=True)
        return decision(pinned[1], .99, "project_source: 项目已记录的经典台词/来源对应；安装和听测状态另查文档")
    for category, pattern in CONTEXT:
        if re.search(pattern, body, re.I):
            return decision("skip", .97, category + ": 此语境不属于当前单人世界的通用本人事件")
    if re.search(r"(?:转移|护送|摧毁|移动|破坏|阻止|夺取|抢夺|守卫|守护|防守|防御|保护|攻下|控制|抵达|到达|前往|推进).{0,8}目标|目标.{0,8}(?:遭到|受损|被摧毁|撑不住|快不行|快完蛋|被严重削弱|正在移动|在移动|动起来|停下|目的地|出站|在路上)|(?:去|到|在).{0,3}目标(?:那|那里|那儿|这里|这儿|位置)|(?:消灭|摧毁|干掉)(?:这个|那个|敌方)?目标[。!！.]*$", body):
        return decision("skip", .93, "objective: 原版护送/攻防目标语境；不是本人 MC 生物击杀")
    if re.search(r"(?:对|回[复应]?|回应|回答|互动|答复).*(?:" + "|".join(NAMES.values()) + r")", n):
        return decision("skip", .98, "interaction: 另一位原生英雄的对话/回应，无真实 MC 触发条件")
    if re.search(r"(?:击杀|杀死|击败|消灭).*(?:" + "|".join(NAMES.values()) + r")", n):
        return decision("skip", .98, "hero_specific_kill: MC 生物不是被点名的原生英雄")
    # Names in the remaining spoken text usually require another native hero.
    other_names = [name for h, names in NAMES.items() if h != hero
                   for name in names.split("|") if len(name) > 1 and name != "小美"]
    if any(name in body for name in other_names):
        return decision("skip", .9, "hero_context: 含另一位原生英雄名字，不能套用于普通 MC 生物")
    if re.search(r"敌方|敌人听到|敌方听到|敌对", n):
        return decision("skip", .94, "perspective: 明确敌方版本；本项目需本人/已批准的中文版本")
    if re.search(r"英语|英文|日语|俄语|韩语|法语|德语|印地语", n) or re.search(r"[ぁ-ゖァ-ヺ가-힣]", core) or re.search(r"[A-Za-z]{3,}(?:[ ,.!]+[A-Za-z]{2,}){2,}", core):
        return decision("uncertain", .95, "language_review: 外语字幕/翻译混排，不能凭文字当作中文版")
    if re.search(r"疑似|可能|不确定|未知|听不清|听译|未使用|未实装|弃用", n) or re.search(r"\?\?|？？", body):
        return decision("uncertain", .95, "source_uncertain: 注释明确存疑或未使用，须听测与版本核对")
    # Ready/charge MUST precede every cast rule (including '(大招)' annotations).
    ult_ref = re.search(r"终[极级]|大招|战术目镜|炸弹轮胎|脉冲炸弹|熔火核心|巨龙|重力喷涌|传送面板|自毁程序|坦克模式|神射手|龙刃|原始暴怒|红外侦测|音障|暴雪", body)
    if (hero == "mercy" and "重生" in n) or (hero == "zenyatta" and re.search("圣.*就绪", body)):
        ult_ref = True
    if ult_ref and re.search(r"充能|准备|就绪|释放", body):
        if re.search(r"正在充能|还在充能|正在准备|还在准备|快|就要|即将|马上|还没|尚未|未就绪|未准备", body):
            return decision("ult_charge", .94, "ultimate_progress: 充能中/即将就绪，不是施放", charge_stage="near" if re.search("快|就要|即将|马上", body) else "charging")
        if re.search(r"准备好|准备就绪|已准备就绪|已就绪|准备完毕|充能完毕|充能完成|已准备好|已准备|就绪", body):
            return decision("ult_ready", .96, "ultimate_ready: 明确大招准备好/充能完毕，不是施放")
    if c in EXACT.get(hero, {}):
        return decision(EXACT[hero][c], .91, "classic_phrase: 该英雄默认技能的辨识性短句；录音版本/声道待音频核验")
    # Ordinary SFX are not character exertion sounds. Explicitly labelled
    # death/pain/jump vocalisations are handled separately below.
    vocal_note = re.search(r"受伤|受击|死亡|阵亡|轻伤|重伤|跃|跳跃|喘|咳|呻吟|喊|语音", body)
    if re.search(r"音效|枪声|开枪|脚步|装弹|换弹|上膛|弹壳|弹匣|子弹|弹药|飞行|滚动|爆炸声|转动|机甲声|切换声|收钩绳|击中声|打击声|敲击|敲炮台|砸炮台|推进器声|背景音|背景声|变形音|武器声", body) and not vocal_note:
        return decision("skip", .96, "sfx: 武器/机械/音乐/移动音效，不是应新增的角色语音")
    if re.search(r"BGM|背景音乐|音乐|铃铛|小鸟|妮妮|啾啾|风滚草|特效", body, re.I) and not c.startswith(("我的", "哦", "来点")):
        return decision("skip", .92, "non_voice: 音乐/伴生物/环境声，不接角色语音事件")
    if re.search(r"坠崖|坠落悬崖|掉落悬崖|地形阵亡|摔死|落崖", body):
        return decision("death", .9, "death_fall: 坠落死亡专用；仅匹配真实致死坠落", variant="fall")
    if re.search(r"死亡|阵亡|濒死|^被击杀$", n) or re.fullmatch(r"(?:死亡|死亡音效|阵亡|被击杀)[。.!]*", body):
        if "濒死" in n:
            return decision("low_health", .88, "low_health_tag: 濒死声，须真实存活低血量", audio_review=True)
        return decision("death", .95, "death_tag: 明确本人死亡声；仅真实死亡触发", audio_review=True)
    if re.search(r"低血量|血量过低|生命垂危", body):
        return decision("low_health", .94, "low_health_tag: 低血量状态，不能与主动求治疗混用")
    if re.search(r"受伤|受击|受到伤害|轻伤|重伤", body):
        return decision("pain", .94, "pain_tag: 明确受击/受伤声；须实际 HP 损失", audio_review=True)
    if re.search(r"^(?:我|谁|有人|快|请|能不能|能|我想|我现在|我得|我还|有谁|这里|这边|帮我|给我|需要|来|治疗)", core) and re.search(r"需要.*治疗|我需要治疗|需要医疗|需要医生|治疗我|给我.*治疗|给我治|来.*治疗我|谁.*治疗|我需要急救|帮我治|我得.*治疗", core):
        return decision("healing_request", .94, "healing_request: 本人明确求治疗；默认由主动交流触发")
    if re.fullmatch(r"(?:我)?需要治疗[。!！.]*", core):
        return decision("healing_request", .96, "healing_request: 明确求治疗")
    if re.search(r"重回战|回到战|返回战|重新加入战斗|再次加入战斗|再战一次|又回来打架|从墓地重生", core) or ("重生" in n and hero != "mercy"):
        return decision("respawn", .9, "respawn: 本人回归战斗/重生；不能用于切维度或闪回")
    if re.search(r"我(?:又|重新)?回(?:来|到)", core):
        return decision("uncertain", .85, "respawn_or_ability: 仅凭我又回来了无法区分重生、回溯、解除冰箱等事件")
    if re.search(r"【跃】|\((?:跃|跳跃|跳)\)|^(?:跳跃|跃)[。.!]*$", body):
        return decision("jump", .94, "jump_tag: 明确跳跃发声；须真实起跳而非空按 Space", audio_review=True)
    if re.search(r"双杀|三杀|四杀|五杀|六杀|多杀|连续击杀|连杀", body):
        return decision("multikill", .93, "multikill: 明确多杀；须同一范围内多次归属击杀", tier=next((k for k in ("双杀", "三杀", "四杀", "五杀", "六杀") if k in body), "multi"))
    if re.search(r"目击|队友.*击杀|友方.*击杀|击杀敌方队伍|团灭|史诗级击杀", body):
        return decision("skip", .92, "witness_or_team: 目击/队友/全队/高光条件，不是本人通用击杀")
    if not re.search(r"就要|快要|将要|准备|得去|需要|应该|必须", body) and re.search(r"击杀|消灭敌人|击败敌人|干掉(?:了)?一个|又干掉|放倒(?:了)?一个|目标(?:已)?(?:倒下|消灭|清除|歼灭)|敌人(?:已)?(?:消灭|倒下)|干掉目标了|敌人被我干掉|解决(?:了)?一个", body):
        return decision("kill", .91, "kill: 通用击杀描述/标注；须 MC 生物真实死亡且归属本人")
    # Only standard wheel actions, not every unlockable cosmetic voice line.
    comm = (
        ("hello", r"^(?:你好(?:啊|呀|哇)?|你们好|大家好|嗨(?:大家好)?|哈喽|您好|Hello|Hi)$"),
        ("thanks", r"^(?:谢(?:谢|了)(?:你|你们|您|各位|老兄|啦|啊)?|多谢(?:你了|啦|了)?|感谢(?:帮忙|你|你们|各位)|非常感谢)$"),
        ("acknowledge", r"^(?:收到|明白(?:了)?|了解(?:了)?|知道(?:了)?|遵命|没问题|好(?:的|吧)?|是(?:的)?|确认|OK|Okay|我明白了)$"),
        ("group_up", r"^(?:在(?:这|这里|这儿)集合|(?:到|来)我(?:这里|这儿)集合|集合(?:吧|起来)?|大家(?:集合|跟紧我)|跟(?:着|紧)我|和我一起(?:行动|前进)|加入我(?:吧)?|我们(?:一起行动|集合吧))$"),
        ("sorry", r"^(?:抱歉(?:了|啦)?|对不起|不好意思)$"),
        ("yes_no", r"^(?:不(?:行|是|要)?|否|绝不|不可能|同意|不同意|好|是|当然)$"),
        ("help", r"^(?:我需要(?:帮助|帮忙|支援)|帮帮我|帮我一把|我需要你们的帮助|快来帮我)$"),
    )
    for action, pattern in comm:
        if re.fullmatch(pattern, c, re.I):
            return decision("comm", .91, "comm:" + action + ": 标准主动交流语句；不得自动当作技能喊话", comm_action=action)
    if re.search(r"待机|无操作|闲置|空闲", n):
        return decision("idle", .85, "idle_tag: 明确待机标注；仍需核对模式/录音版本")
    for patterns, ability in ABILITY_NOTES.get(hero, {}).items():
        if any(re.fullmatch(pattern, note) for note in notes for pattern in patterns.split("|")):
            return decision("ability:" + ability, .88 if c else .8,
                            "ability_tag: 注释指向技能；无字素材须听辨是否纯 SFX", audio_review=not bool(c))
    if any(re.fullmatch(pattern, note) for note in notes for pattern in ULT_NAMES[hero].split("|")):
        return decision("ult_cast", .88 if c else .8,
                        "ultimate_tag: 注释指向施放；无字素材须确认是喊声而非整段音效", audio_review=not bool(c))
    if re.search(r"终极技能语音|大招怒吼", core):
        return decision("ult_cast", .85, "ultimate_vocal_tag: 无字大招发声，需听测", audio_review=True)
    if re.search(r"喘息|喘气|呼吸声|呻吟|用力|咳嗽|咳嗽声|咳声|近战喊声|笑声|狂笑|冷笑|叹息", body) or re.fullmatch(r"[啊呀呃哦噢喔哇唔嗯额哈嘿呵哼喝吼嗷咳哎诶唉噗呸嚯啧嘶噫呼]+", c):
        return decision("effort", .65, "vocal_unspecified: 发声明确，但笑/喘/用力的实际事件不能由文字确认", audio_review=True)
    if not c:
        return decision("uncertain", .99, "no_transcript: 空文本/仅标点/无类别注释，不能区分语音、跳跃、死亡或机械声", audio_review=True)
    if re.search(r"你.*(?:为什么|怎么|觉得|记得|知道|听说|认识)|我听说|你听说|还记得|你说|你问|我们认识|你的父亲|你的母亲|你的哥哥|你的弟弟|你的家人", core):
        return decision("skip", .88, "dialogue: 明显互动问答，单人世界没有原生对话对象")
    if re.search(r"火力全开|火力开了|on fire", core, re.I):
        return decision("skip", .95, "on_fire: 项目没有原版火力全开评分；不是大招/充能事件")
    return decision("uncertain", .5, "no_event_evidence: 台词可能是击杀、闲聊、解锁语音或特定场景；没有可靠类别证据")

def local_assets(root: Path) -> tuple[dict[str, dict], str]:
    """Only count MP3s whose recorded SHA256 matches; directory presence isn't proof."""
    manifest = root / "manifest.json"
    if not manifest.is_file():
        return {}, "private_manifest_missing"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    verified = {}
    for stem, entry in data.items():
        h = entry.get("catalog", {}).get("filehash")
        path = root / (stem + ".mp3")
        if not h or not path.is_file() or not entry.get("sha256"):
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]:
            verified[h] = {"stem": stem, "sha256": entry["sha256"]}
    return verified, hashlib.sha256(manifest.read_bytes()).hexdigest()

def downloadable(row: dict) -> bool:
    return (row["event"] not in {"skip", "uncertain", "effort", "idle"}
            and row["confidence"] >= .88)

def classify_catalog(data: dict, existing: dict | None = None) -> dict:
    existing = existing or {}
    if set(data) != set(NAMES):
        raise ValueError("Expected exactly the original 21 hero keys")
    result = {}
    seen = set()
    for hero, rows in data.items():
        result[hero] = []
        for row in rows:
            if not re.fullmatch(r"[0-9a-f]{32}", row["hash"]) or row["hash"] in seen:
                raise ValueError("Invalid/duplicate catalogue hash: " + row["hash"])
            seen.add(row["hash"])
            out = {**row, **classify(hero, row)}
            out["version_status"] = ("excluded_context" if out["event"] == "skip"
                                     else "project_classic_reference_recording_date_unverified" if row["hash"] in PINNED
                                     else "unverified_no_catalog_version_metadata")
            out["audio_verified"] = False  # No audio listening happens in this tool.
            out["local_asset_verified"] = row["hash"] in existing
            out["download_recommended"] = downloadable(out) and not out["local_asset_verified"]
            out["deployment_allowed"] = False  # Classification is not live audio acceptance.
            result[hero].append(out)
    return result

def summarize(data: dict, source: Path, private_manifest_sha: str) -> dict:
    totals = Counter({event: 0 for event in BASE_EVENTS})
    heroes = {}
    manifest = []
    for hero, rows in data.items():
        counts = Counter(row["event"] for row in rows)
        totals.update(counts)
        downloads = [row for row in rows if row["download_recommended"]]
        for row in downloads:
            manifest.append({"hero": hero, **{k: row[k] for k in ("hash", "text", "url", "sourcePage", "event", "confidence", "reason")},
                             "optional": row.get("optional", False), "connection": row.get("connection", "round_one_candidate")})
        heroes[hero] = {"total": len(rows), "events": dict(sorted(counts.items())),
                        "review_required": counts["uncertain"],
                        "local_assets_verified": sum(row["local_asset_verified"] for row in rows),
                        "download_count": len(downloads), "estimated_bytes": len(downloads) * 25000}
    downloads_by_event = Counter(row["event"] for row in manifest)
    for item in heroes.values():
        item["events"] = {event: item["events"].get(event, 0) for event in sorted(totals)}
    review_reasons = Counter(row["reason"].split(":", 1)[0]
                             for rows in data.values() for row in rows if row["event"] == "uncertain")
    return {
        "schema_version": 1, "rule_version": RULE_VERSION,
        "catalog_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "private_manifest_sha256": private_manifest_sha,
        "classification_basis": "local subtitles/annotations + curated project references; no network/audio playback",
        "version_policy": "Exclude explicit later-content/hero/skin/mode/incompatible-kit evidence. Unlabelled age remains unverified; never infer 2016 from wording/hash/order.",
        "download_policy": "Semantic acquisition candidates only: confidence>=0.88, event known, no verified local copy. Explicitly labelled death/pain/jump vocals may be acquired for listening; unlabelled grunts/empty audio may not. Downloading does NOT approve playback; all require language/date/clean-audio/native-overlap review.",
        "total": sum(map(len, data.values())), "events": dict(sorted(totals.items())),
        "download_by_event": {event: downloads_by_event[event] for event in sorted(totals)},
        "download_count": len(manifest), "average_bytes_assumed": 25000,
        "estimated_bytes": len(manifest) * 25000,
        "estimated_MB_decimal": round(len(manifest) * .025, 3),
        "estimated_MiB": round(len(manifest) * 25000 / 1048576, 3),
        "all_catalog_estimated_MB_decimal": round(sum(map(len, data.values())) * .025, 3),
        "uncertain_reasons": dict(sorted(review_reasons.items())),
        "selection_baseline": {"installed_roster_documented": 21,
                               "matched_catalog_select_hashes": sum(row["hash"] in set(SELECT_HASHES.values()) for rows in data.values() for row in rows),
                               "catalog_select_classifications": totals["select"],
                               "installed_hashes_absent_from_catalog": [hero for hero, h in SELECT_HASHES.items()
                                   if h and not any(row["hash"] == h for row in data[hero])],
                               "external_bastion_select_preserved": True},
        "heroes": heroes, "download_manifest": manifest,
    }

def markdown(summary: dict) -> str:
    events = list(summary["events"])
    acquisition = (f"目录 {summary['total']} 条；核心建议 {summary['core_download_count']} 条 / {summary['core_estimated_MB_decimal']} MB，可选 {summary['optional_download_count']} 条 / {summary['optional_estimated_MB_decimal']} MB，合计 {summary['estimated_MB_decimal']} MB（25,000 bytes/条）。"
                   if "semantic_review" in summary else
                   f"目录 {summary['total']} 条；建议新增下载 {summary['download_count']} 条，按 25,000 bytes/条约 {summary['estimated_MB_decimal']} MB / {summary['estimated_MiB']} MiB。")
    lines = ["# 英雄语音分类（离线静态候选）", "", "置信度仅表示事件归属；无版本字段不代表早期录音。所有候选部署前仍需听测、版本与双声检查。", "",
             acquisition, "",
             "| 事件 | 全目录条数 | 建议新增下载 |", "|---|---:|---:|"]
    for event in events:
        lines.append(f"| {event} | {summary['events'][event]} | {summary['download_by_event'].get(event, 0)} |")
    lines += ["", "| 英雄 | 总条数 | 本地已核 hash | 建议新增下载 | 估算 MB |", "|---|---:|---:|---:|---:|"]
    for hero, item in summary["heroes"].items():
        lines.append(f"| {hero} | {item['total']} | {item['local_assets_verified']} | {item['download_count']} | {item['estimated_bytes']/1e6:.3f} |")
    lines += ["", "逐英雄逐事件计数见 summary.json 的 heroes.*.events；下载清单见 download-manifest.json。",
              "空字幕不猜 death/pain/jump；effort 只说明是语气声，默认不下载。Bastion 已装选人来自另一站，不强行给本目录的无字素材指定选人。",
              "分类只排除有证据的后期内容；无法从字幕证明录音早于 1.30，未标注项保留 unverified。", ""]
    if "semantic_review" in summary:
        lines += ["## 逐英雄事件数（省略零值；JSON 保留全部零值）", ""]
        for hero, item in summary["heroes"].items():
            counts = "，".join(f"`{event}` {count}" for event, count in item["events"].items() if count)
            lines.append(f"- **{hero}**：{counts}。")
        lines += [""]
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT / "catalog.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT)
    parser.add_argument("--asset-root", type=Path, default=PRIVATE)
    parser.add_argument("--round-one", action="store_true", help="Explicitly omit the local second-round semantic review ledger")
    args = parser.parse_args()
    existing, private_sha = local_assets(args.asset_root)
    data = json.loads(args.catalog.read_text(encoding="utf-8"))
    classified = classify_catalog(data, existing)
    reviewed = not args.round_one and (DEFAULT / "round2-decisions.json").is_file()
    if reviewed:
        from review_voice_catalog_round2 import apply_review, enrich_summary, compact_download
        classified = apply_review(classified)
    summary = summarize(classified, args.catalog, private_sha)
    if reviewed:
        summary = enrich_summary(summary, classified)
    manifest = summary.pop("download_manifest")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in (("classified.json", classified), ("summary.json", summary),
                          ("download-manifest.json", manifest)):
        (args.output_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = markdown(summary)
    if reviewed:
        compact = compact_download(classified)
        (args.output_dir / "download.json").write_text(json.dumps(compact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        audit = summary["semantic_review"]
        report += ("\n## 第二轮直接语义复核\n\n"
            f"逐英雄 {audit['batches']} 批直接阅读，覆盖原 uncertain {audit['initial_uncertain']} 条；另读旧 skip 的状态/装弹 {audit['reviewed_status_reload_additions']} 条。逐 hash 判断保存在 round2-decisions.json，来源原文与批次在 round2-source.json / round2-extra-source.json。脚本只重放这些判断，不调用模型或网络。\n\n"
            f"剩余 uncertain {audit['uncertain_remaining']} 条（{audit['uncertain_pct']}%），其中空字幕 {audit['uncertain_blank']} 条、有文字仍待判 {audit['uncertain_with_text']} 条。仅空字幕已超过10%，未用 effort/skip 掩盖未知录音；达到全目录<10%还需音频听辨。\n\n"
            f"核心建议 {summary['core_download_count']} 条 / {summary['core_estimated_MB_decimal']} MB；可选 {summary['optional_download_count']} 条 / {summary['optional_estimated_MB_decimal']} MB；合计 {summary['download_count']} 条 / {summary['estimated_MB_decimal']} MB（25,000 bytes/条）。download.json 的 optional=true 仅用于 reload/status/idle；不意味着已接线。\n\n"
            "核心清单只保留已有真实原生阶段或MC权威来源可加监听的事件。全英雄击杀仍需扩展归属账本；主动交流/求治疗缺UI生产者、D.Va机甲、attempt-only成功喊话、未认证切歌等不进核心清单。传送面板剩余次数严格匹配当前MC上限6次，7..10次不下载。既有21人选人保留。\n")
    (args.output_dir / "summary.md").write_text(report, encoding="utf-8")
    keys = ("total", "download_count", "estimated_MB_decimal")
    out = {k: summary[k] for k in keys}
    if reviewed: out.update({"kill": summary["events"].get("kill"), "semantic_review": summary["semantic_review"], "core_download_count": summary["core_download_count"], "optional_download_count": summary["optional_download_count"]})
    else: out["events"] = summary["events"]
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
