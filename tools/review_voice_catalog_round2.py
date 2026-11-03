"""Human/model semantic review ledger. No network, audio playback or game access.

prepare freezes round-one uncertain IDs; show presents <=150 original entries;
record stores explicit reviewed decisions. Empty transcripts stay uncertain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from collections import Counter

import classify_voice_catalog as base

FOLDER = base.DEFAULT
SOURCE = FOLDER / "round2-source.json"
LEDGER = FOLDER / "round2-decisions.json"
KINDS = {
    "I": ("idle", .85, "自言自语、闲聊、口头禅或独立感叹，无特定战局条件"),
    "Z": ("select", .94, "该英雄已知经典选人宣言的字幕变体；已有选人所有者继续保留"),
    "K": ("kill", .88, "击杀嘲讽、对败者的评价、胜利感叹或击杀结果"),
    "M": ("multikill", .9, "明确一次/连续击败多个敌人的感叹"),
    "X": ("skip", .96, "objective: 目标、攻防、推车、比赛时间或队伍胜负语境"),
    "O": ("skip", .94, "context: 地图/剧情互动/特定英雄/模式皮肤/纯机械音效，不自动接入"),
    "C": ("comm", .9, "可由本人主动发出的交流、战术请求或确认"),
    "R": ("reload", .92, "装填弹药/重新装弹提示；只作可选采集，待原生装弹事件接线"),
    "P": ("pain", .9, "本人受到真实伤害的发声或反应"),
    "D": ("death", .9, "本人死亡/失败临终发声"),
    "J": ("jump", .9, "明确跳跃发声"),
    "E": ("effort", .8, "明确语气声/笑声/喘息；动作类别待听辨，不自动播放"),
    "N": ("respawn", .87, "本人重生、再次加入战斗或再来一次"),
    "L": ("low_health", .9, "本人生命危险或急需救治状态"),
    "Q": ("healing_request", .92, "本人请求治疗"),
    "T": ("ult_cast", .9, "该英雄本人的大招施放喊话"),
    "Y": ("ult_ready", .93, "大招已就绪，非施放"),
    "G": ("ult_charge", .92, "大招仍在充能/即将就绪"),
    "U": ("uncertain", .45, "字幕缺失，或仅据文字仍无法判断事件/说话者/语音内容"),
    "h": ("status:healed", .91, "本人接受治疗或生命恢复的反应"),
    "f": ("status:frozen", .92, "本人受冰冻/寒冷控制的反应"),
    "s": ("status:stunned", .91, "本人被眩晕/击倒/冲撞等控制的反应"),
    "b": ("status:damage_boosted", .9, "本人获得增伤强化的反应；不是施放技能"),
    "a": ("status:speed_boosted", .9, "本人获得加速的反应"),
    "w": ("status:burning", .91, "本人被灼烧的反应"),
    "p": ("status:poisoned", .91, "本人中毒/呛咳反应"),
    "v": ("status:revived", .91, "本人被他人复活的反应，与自然重生分开"),
    "m": ("status:shielded", .9, "本人受到护盾/护甲保护的反应"),
    "c": ("status:debuffed", .88, "本人受到负面状态的反应"),
    "o": ("status:on_fire", .9, "本人火力全开/表现状态感叹；无MC评分来源，不自动接入"),
    "l": ("status:cold", .87, "寒冷/解冻后的状态感叹；与受伤及死亡分开，可选听辨"),
    "e": ("status:electrocuted", .91, "受到电击的状态发声，不能等同眩晕"),
    "k": ("status:knocked_back", .9, "本人被冲撞或击退的状态反应"),
    "t": ("status:controlled", .87, "被晕/被钩等受控状态，标签未细分，不混作普通受伤"),
    "y": ("status:ability_ready", .86, "技能冷却结束提示，具体技能与声音类型待听辨"),
    "r": ("status:scrap_low", .9, "托比昂碎片资源不足/耗尽；可选，需真实资源读数"),
    "u": ("status:falling", .87, "坠落/掉落发声；标签未证明死亡，只作可选状态素材"),
}
ABILITIES = {
    "bastion": ["reconfigure", "self_repair"], "dva": ["call_mech", "defense_matrix", "boosters"],
    "genji": ["deflect", "swift_strike"], "hanzo": ["scatter_arrow", "sonic_arrow"],
    "junkrat": ["concussion_mine", "steel_trap", "steel_trap_trigger"],
    "lucio": ["amp_it_up", "crossfade_speed", "crossfade_heal", "soundwave", "crossfade_switch"],
    "mccree": ["flashbang", "combat_roll"], "mei": ["ice_wall", "cryo_freeze", "freeze_target"],
    "mercy": ["heal_beam", "damage_boost", "guardian_angel", "staff_channel"],
    "pharah": ["jump_jet", "concussive_blast", "hover"],
    "reaper": ["shadow_step", "wraith"], "reinhardt": ["barrier", "charge", "fire_strike", "barrier_broken", "barrier_low"],
    "roadhog": ["chain_hook", "take_a_breather", "chain_hook_hit"],
    "soldier76": ["biotic_field", "helix_rockets", "sprint"],
    "symmetra": ["sentry_turret", "photon_shield", "teleporter", "photon_barrier", "teleporter_charges", "teleporter_destroyed", "teleporter_under_attack", "sentry_destroyed"],
    "torbjorn": ["turret_deploy", "armor_pack", "turret_under_attack", "turret_destroyed", "turret_upgrade", "turret_low", "armor_pack_reminder", "turret_repair"],
    "tracer": ["blink", "recall", "pulse_attach"],
    "widowmaker": ["grappling_hook", "venom_mine", "venom_trigger"],
    "winston": ["jump_pack", "barrier", "barrier_low"], "zarya": ["particle_barrier", "projected_barrier"],
    "zenyatta": ["harmony_orb", "discord_orb"],
}

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def body(row):
    text = unicodedata.normalize("NFKC", row["text"])
    while (m := re.match(r"^【([^】]+)】\s*", text)) and base.ALIASES.get(m[1].casefold()):
        text = text[m.end():]
    return text.strip()

def empty(row):
    return not base.compact(body(row))

def prepare():
    if SOURCE.exists():
        raise ValueError("Preserve existing frozen review source")
    data = read(FOLDER / "classified.json")
    write(SOURCE, {hero: [{"hash": r["hash"], "text": r["text"]} for r in rows
                         if r["event"] == "uncertain"] for hero, rows in data.items()})
    write(LEDGER, {"method": "逐英雄，每批至多150条直接阅读原文；重复字幕合并显示，空白保留待听辨", "batches": {}, "decisions": {}})

def show(hero, batch):
    rows = read(FOLDER / "round2-extra-source.json") if hero == "_extra" else read(SOURCE)[hero]
    start = (batch - 1) * 150
    groups = {}
    blanks = []
    for i, row in enumerate(rows[start:start + 150], start + 1):
        if empty(row):
            blanks.append(i)
        else:
            groups.setdefault((row.get("hero", "") + " " + body(row)).strip(), []).append(i)
    print(f"{hero} batch={batch} range={start+1}..{min(start+150,len(rows))} total={len(rows)}")
    print("空字幕", ",".join(map(str, blanks)))
    for text, ids in groups.items():
        print(",".join(map(str, ids)) + " " + text)

def indexes(spec):
    result = []
    for part in spec.split(","):
        ends = part.split("-")
        if len(ends) == 1:
            result.append(int(ends[0]))
        else:
            result.extend(range(int(ends[0]), int(ends[1]) + 1))
    return result

def record(hero, batch, default, overrides):
    rows = read(FOLDER / "round2-extra-source.json") if hero == "_extra" else read(SOURCE)[hero]
    start = (batch - 1) * 150
    selected = rows[start:start + 150]
    ledger = read(LEDGER)
    codes = {i: "U" if empty(row) else default for i, row in enumerate(selected, start + 1)}
    for code, spec in overrides.items():
        for i in indexes(spec):
            if i not in codes:
                raise ValueError(f"Index outside batch: {hero}/{batch}/{i}")
            codes[i] = code
    for i, row in enumerate(selected, start + 1):
        code = codes[i]
        if code.isdigit():
            event = "ability:" + ABILITIES[row.get("hero", hero)][int(code) - 1]
            confidence, reason = .9, "该英雄明确技能动作、放置/施放/生效提醒"
        else:
            event, confidence, reason = KINDS[code]
        ledger["decisions"][row["hash"]] = dict(hero=row.get("hero", hero), event=event, confidence=confidence,
            reason="round2.semantic: " + reason, batch=f"{hero}/{batch}",
            text_sha256=hashlib.sha256(row["text"].encode()).hexdigest())
    ledger["batches"][f"{hero}/{batch}"] = {"count": len(selected), "codes": "".join(codes.values()),
        "review": "direct_semantic_read", "default": default, "overrides": overrides}
    write(LEDGER, ledger)
    print(f"recorded {hero}/{batch}: {len(selected)}")

# Read from the existing controller/server implementations, not from catalogue
# keyword matching. Missing commit/effect states deliberately have no entry.
CONNECTED_ABILITIES = {
    "bastion": {"reconfigure", "self_repair"},
    "genji": {"deflect", "swift_strike"}, "mccree": {"flashbang", "combat_roll"},
    "pharah": {"jump_jet", "concussive_blast", "hover"},
    "reaper": {"shadow_step", "wraith"},
    "soldier76": {"biotic_field", "helix_rockets", "sprint"},
    "tracer": {"blink", "recall", "pulse_attach"},
    "hanzo": {"scatter_arrow", "sonic_arrow"},
    "mei": {"ice_wall", "cryo_freeze", "freeze_target"},
    "junkrat": {"concussion_mine", "steel_trap", "steel_trap_trigger"},
    "torbjorn": {"turret_deploy", "armor_pack", "armor_pack_reminder"},
    "widowmaker": {"grappling_hook", "venom_mine", "venom_trigger"},
    "mercy": {"heal_beam", "damage_boost", "staff_channel"},
    "reinhardt": {"barrier", "charge"}, "zarya": {"particle_barrier"},
    "roadhog": {"chain_hook", "take_a_breather", "chain_hook_hit"},
    "symmetra": {"sentry_turret", "teleporter", "teleporter_charges", "teleporter_destroyed", "teleporter_under_attack", "sentry_destroyed"},
    "lucio": {"amp_it_up", "crossfade_switch"},
}
CONNECTED_ULTS = {"genji", "mccree", "pharah", "reaper", "soldier76", "tracer",
    "bastion", "hanzo", "mei", "torbjorn", "widowmaker", "zarya", "roadhog",
    "symmetra", "lucio"}

def connection(hero, event):
    if event in {"skip", "uncertain", "effort"}:
        return "excluded", False
    if event == "select":
        return "existing_21_select_preserved", False
    if event == "idle" or event == "reload" or event.startswith("status:"):
        return "optional_not_wired", True
    if event in {"ult_ready", "ult_charge"}:
        return "existing_typed_meter_needs_voice_edge", False
    if event in {"kill", "multikill"}:
        # NativeDamageTargets already has (player,victim,actualLoss) for all
        # supported damage paths. A general ledger/listener is still required;
        # the current Genji-only elimination queue must not be consumed twice.
        return "mc_attributed_damage_death_needs_general_ledger", False
    if event in {"pain", "death", "respawn", "jump", "low_health"}:
        return "mc_authoritative_event_needs_listener", False
    if event in {"comm", "healing_request"}:
        return "missing_active_comm_producer", False
    if event == "ult_cast":
        return ("native_admitted_phase_needs_voice_listener", False) if hero in CONNECTED_ULTS else ("missing_success_commit", False)
    if event.startswith("ability:"):
        return ("native_or_mc_accepted_action_needs_voice_listener", False) if event[8:] in CONNECTED_ABILITIES.get(hero, set()) else ("missing_success_commit", False)
    return "excluded", False

def apply_review(data):
    """Apply hash+text-pinned human/model decisions. No reclassification regex.

    The few regexes below only flag language for the download gate; they cannot
    assign semantic events. Every changed event comes from the persisted ledger.
    """
    ledger = read(LEDGER)
    source = read(SOURCE)
    extra = read(FOLDER / "round2-extra-source.json")
    expected = {row["hash"] for rows in source.values() for row in rows} | {row["hash"] for row in extra}
    if expected != set(ledger["decisions"]):
        raise ValueError("Incomplete/extra semantic review decisions")
    actual = {row["hash"]: (hero, row) for hero, rows in data.items() for row in rows}
    for h, decision in ledger["decisions"].items():
        hero, row = actual[h]
        if hero != decision["hero"] or hashlib.sha256(row["text"].encode()).hexdigest() != decision["text_sha256"]:
            raise ValueError("Catalogue text/hero changed after review: " + h)
        if empty(row) and decision["event"] != "uncertain":
            raise ValueError("An empty subtitle cannot acquire a guessed event: " + h)
    result = {}
    for hero, rows in data.items():
        result[hero] = []
        for original in rows:
            row = dict(original)
            decision = ledger["decisions"].get(row["hash"])
            row["classification_round"] = 1
            if decision:
                row.update({key: decision[key] for key in ("event", "confidence", "reason")})
                row["classification_round"] = 2
                row["review_batch"] = decision["batch"]
                row["version_status"] = "excluded_context" if row["event"] == "skip" else "unverified_no_catalog_version_metadata"
            core = body(row)
            # An English/Japanese transcription is not proof of Mandarin audio.
            language = (original.get("needs_language_review", False) or original["reason"].startswith("language_review:")
                or bool(re.search(r"英语|英文|日语|俄语|韩语|法语|德语|台配|[ぁ-ゖァ-ヺ가-힣]", core))
                or bool(re.search(r"[A-Za-z]{2}", core) and not re.search(r"[\u3400-\u9fff]", core)))
            row["needs_language_review"] = language
            route, optional = connection(hero, row["event"])
            if row["event"] == "ability:teleporter_charges":
                # These ten individual captions were read in the semantic
                # batches, not inferred from substring rules. MC's real portal
                # starts with six uses (SymmetraServer); 7..10 cannot trigger.
                source_rows = source["symmetra"]
                counts = {153: 3, 183: 6, 197: 8, 222: 1, 260: 5, 283: 4,
                          305: 10, 329: 7, 331: 2, 343: 9}
                count_by_hash = {source_rows[i-1]["hash"]: count for i, count in counts.items()}
                row["remaining_uses"] = count_by_hash[row["hash"]]
                if row["remaining_uses"] > 6: route = "unreachable_counter_value"
            row["connection"] = route
            row["optional"] = optional
            eligible = (route not in {"excluded", "existing_21_select_preserved", "missing_active_comm_producer", "missing_success_commit", "unreachable_counter_value"}
                        and row["confidence"] >= .85 and not language)
            row["download_recommended"] = eligible and not row["local_asset_verified"]
            row["deployment_allowed"] = False
            result[hero].append(row)
    return result

def enrich_summary(summary, data):
    ledger = read(LEDGER)
    rows = [row for group in data.values() for row in group]
    pending = [row for row in rows if row["event"] == "uncertain"]
    selected = [row for row in rows if row["download_recommended"]]
    optional = [row for row in selected if row["optional"]]
    core = [row for row in selected if not row["optional"]]
    summary["rule_version"] = "2026-10-25.2-semantic-ledger"
    summary["classification_basis"] = "66 batches directly read and labelled by semantic judgement; hash/text-pinned override ledger, no LLM/API/network call in scripts"
    summary["semantic_review"] = {
        "initial_uncertain": sum(map(len, read(SOURCE).values())),
        "reviewed_decisions": len(ledger["decisions"]), "batches": len(ledger["batches"]),
        "reviewed_status_reload_additions": len(read(FOLDER / "round2-extra-source.json")),
        "ledger_sha256": hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
        "uncertain_remaining": len(pending), "uncertain_blank": sum(empty(row) for row in pending),
        "uncertain_with_text": sum(not empty(row) for row in pending),
        "uncertain_pct": round(100 * len(pending) / len(rows), 3),
        "target_limitation": "Empty/untranscribed recordings remain uncertain. Do not relabel them as effort/skip merely to reach <10%.",
    }
    summary["download_policy"] = "Existing real signal or MC authoritative hook; generic all-hero kill attribution needs a new ledger. Comm UI and unsupported skill commits excluded. reload/status/idle are OPTIONAL acquisition only. All dates/audio/overlap still require verification. Local hash-verified MP3s excluded."
    summary["core_download_count"] = len(core)
    summary["optional_download_count"] = len(optional)
    summary["core_estimated_MB_decimal"] = round(.025 * len(core), 3)
    summary["optional_estimated_MB_decimal"] = round(.025 * len(optional), 3)
    summary["core_download_by_event"] = dict(sorted(Counter(row["event"] for row in core).items()))
    summary["optional_download_by_event"] = dict(sorted(Counter(row["event"] for row in optional).items()))
    for hero, group in data.items():
        summary["heroes"][hero]["core_download_count"] = sum(row["download_recommended"] and not row["optional"] for row in group)
        summary["heroes"][hero]["optional_download_count"] = sum(row["download_recommended"] and row["optional"] for row in group)
    return summary

def compact_download(data):
    result = []
    for hero, rows in data.items():
        for row in rows:
            if row["download_recommended"]:
                item = {"hero": hero, **{key: row[key] for key in ("hash", "url", "event")}}
                if row["optional"]: item["optional"] = True
                result.append(item)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "show", "record"])
    parser.add_argument("hero", nargs="?")
    parser.add_argument("batch", type=int, nargs="?", default=1)
    parser.add_argument("--default", default="I")
    parser.add_argument("--overrides", default="{}")
    args = parser.parse_args()
    if args.action == "prepare": prepare()
    elif args.action == "show": show(args.hero, args.batch)
    else: record(args.hero, args.batch, args.default, json.loads(args.overrides))

if __name__ == "__main__": main()
