"""离线清退默认语音；不下载、不删除音频。私有清单仅显式 --apply-private 时备份后修剪。"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
from prepare_hanzo_japanese_voice import DERIVED_ID,LOCAL_ENTRY
from restore_voice_ultimates import additions as ultimate_additions,selected as ultimate_selected

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'research/voice-catalog-20261025'
OUT = ROOT / 'research/voice-20261026b'
JAVA = ROOT / 'guest/src/main/java/lab/owmcguest/HeroVoiceDefaultCatalog.java'
PRIVATE = Path(os.environ.get('USERPROFILE', str(Path.home()))) / '.universal-modder/assets/ow1-zhcn-2016/thnu-full/manifest.json'
# 逐条阅读现有技能/大招候选后的保守清退：仅有动作注释，无法证明是台词。
ANNOTATIONS = set('5a449ed3 c081adc6 d0b04b2b b278f6de d0d92b90 f25df564 44d0c192 '
                  '126a4f34 1a6346bb ae499f6c c238cd3d f95d7a5a 6f03fabb '
                  'f257bd94 07398653 c0a32ff0'.split())
# 目前没有对应成功回执；或是位移语气声/无明确音频说明。
UNWIRED = {'ability:staff_channel', 'ability:teleporter_destroyed', 'ability:teleporter_under_attack',
           'ability:teleporter_charges', 'ability:sentry_destroyed', 'ability:armor_pack_reminder'}
MOVEMENT = {'ability:blink', 'ability:recall', 'ability:grappling_hook',
            'jump', 'land', 'landing', 'takeoff', 'effort', 'movement:jump', 'movement:land',
            'ability:jump', 'ability:double_jump', 'ability:super_jump', 'ability:jump_jet',
            'ability:rocket_jump', 'ability:leap', 'ability:wall_climb', 'ability:landing'}
LEGACY_ULT = {'genji','mccree','pharah','reaper','soldier76','tracer'}
LEGACY_ABILITY = {('mccree','ability:flashbang'),('reaper','ability:shadow_step'),('soldier76','ability:biotic_field')}
HANZO_ULT_HASH = DERIVED_ID

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def body(text):
    text = re.sub(r'【[^】]*】', '', text)
    return re.sub(r'（[^）]*）|\([^)]*\)|[\W_]+', '', text)

def reason(hero, row):
    event = row['event']
    if event in MOVEMENT:
        return 'movement_voice'  # 语音挂接：永久清退，旧清单重新生成也不能恢复。
    if ultimate_selected(hero,event,row['hash']):
        return ''  # 语音挂接：用户第五次反馈恢复就绪提示、堡垒Q及已接Begin的漏项。
    if event not in {'select','ult_cast','kill','multikill'} and not event.startswith('ability:'):
        return 'removed_category'
    if event == 'select' and hero in {'tracer','bastion'}:
        return 'selection_muted'
    if hero == 'hanzo' and event == 'ult_cast' and row['hash'] != HANZO_ULT_HASH:
        return 'hanzo_fixed_ultimate'
    if event in UNWIRED:
        return 'no_event_receipt'
    if row['hash'][:8] in ANNOTATIONS:
        return 'annotation_only'
    spoken = body(row.get('text',''))
    if not spoken or re.fullmatch('[啊呀哼哈呵哦噢喔唔呜嗬嘿耶也哟吼咳呼嗯恩嚯]+', spoken):
        return 'nonverbal'
    if row.get('audio_review') or row.get('version_status') == 'post_1_30':
        return 'unverified'
    if event == 'ult_cast' and hero in LEGACY_ULT or (hero,event) in LEGACY_ABILITY:
        return 'legacy_owner'  # 保留旧入口的已认证台词；不重复下载/注册同事件。
    # 治愈束刚连接不能证明满血；该句必须由已删除的状态事件负责。
    if row['hash'].startswith('2a371e49'):
        return 'wrong_event'
    return ''

def filter_manifest(data, identities):
    wrapped = isinstance(data.get('entries'), dict)
    entries = data['entries'] if wrapped else data
    kept, removed = {}, []
    for hash_, entry in entries.items():
        if isinstance(entry,dict) and (entry.get('hero'),entry.get('event'),hash_) in identities:
            kept[hash_] = entry
        else:
            removed.append(dict(hash=hash_,hero=entry.get('hero',''),event=entry.get('event','unknown')))
    return ({**data,'entries':kept} if wrapped else kept), removed

def generate(private=PRIVATE, apply_private=False):
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = OUT / 'download-before.json'
    if not snapshot.exists(): shutil.copyfile(CATALOG / 'download.json', snapshot)
    before = json.loads(snapshot.read_text(encoding='utf-8'))
    classified = json.loads((CATALOG / 'classified.json').read_text(encoding='utf-8'))
    lookup = {(hero,r['hash']):r for hero,rs in classified.items() for r in rs}
    kept, removed = [], []
    for entry in before:
        row = lookup.get((entry['hero'],entry['hash']))
        why = reason(entry['hero'],row) if row else 'unknown_source'
        if why: removed.append(dict(entry, removal=why))
        else: kept.append({key:entry[key] for key in ('hero','hash','url','event')})
    # 语音挂接：本地参考音轨的已确认日语片段；不能交给下载器当成站点MP3抓取。
    kept.append(dict(LOCAL_ENTRY))
    restored=ultimate_additions()
    identities={(r['hero'],r['event'],r['hash']) for r in kept}
    for entry in restored:
        identity=(entry['hero'],entry['event'],entry['hash'])
        if identity not in identities:kept.append(entry);identities.add(identity)
    write(CATALOG / 'download.json', kept)
    write(OUT / 'download-default.json', kept)
    write(OUT / 'removed-default.json', removed)
    identities = {(r['hero'],r['event'],r['hash']) for r in kept}
    lines = '\n'.join('|'.join(r[k] for k in ('hero','event','hash')) for r in kept)
    JAVA.write_text('''package lab.owmcguest;

/** 语音挂接：tools/prune_voice_defaults.py生成；未知hash/错事件/旧可选素材一律不加载。 */
final class HeroVoiceDefaultCatalog {
    private static final String DATA="""
''' + lines + '\n""";\n' + '''    private static final java.util.Set<String> ALLOWED=java.util.Set.of(DATA.strip().split("\\n"));
    static boolean allowed(String hero,String event,String hash){return HeroVoicePolicy.clipAllowed(hero,event,hash)&&ALLOWED.contains(hero+"|"+event+"|"+hash);}
}
''', encoding='utf-8')
    # 旧可选下载入口退役，历史语义分类及无字幕研究素材仍保留，均不再默认播放。
    for name in ('download-optional.json','download-starter.json'):
        path = ROOT / 'research/voice-20261026' / name
        if path.exists():
            archive = OUT / (name.removesuffix('.json') + '-retired.json')
            if not archive.exists(): shutil.copyfile(path, archive)
            write(path, [])
    summary = dict(before=len(before), addedLocal=1, restoredUltimates=len(restored), downloadable=len(kept)-1, kept=len(kept), removed=len(removed),
                   removedEvents=dict(sorted(Counter(r['event'] for r in removed).items())),
                   removalReasons=dict(Counter(r['removal'] for r in removed)),
                   keptEvents=dict(sorted(Counter(r['event'] for r in kept).items())),
                   excludedUnsubtitledResearch=sum(bool(r.get('audio_review')) and r['event']=='uncertain' for rs in classified.values() for r in rs))
    if private.is_file():
        if apply_private:
            from prepare_hanzo_japanese_voice import prepare
            prepare(install=True,quiet=True,target_manifest=private)
        original=json.loads(private.read_text(encoding='utf-8'))
        filtered, excluded=filter_manifest(original,identities)
        entries=filtered.get('entries',filtered)
        summary['private']=dict(before=len(entries)+len(excluded),kept=len(entries),removed=len(excluded),
                               removedEvents=dict(sorted(Counter(r['event'] for r in excluded).items())),
                               keptBytes=sum(r.get('bytes',0) for r in entries.values()))
        write(OUT/'removed-private-manifest.json',excluded)
        if apply_private:
            backup=private.with_name('manifest.before-20261026b-voice.json')
            if not backup.exists(): shutil.copyfile(private,backup)
            temp=private.with_name('manifest.voice-prune.tmp')
            write(temp,filtered); temp.replace(private)
    write(OUT/'cleanup-summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in {'removedEvents','keptEvents'}},ensure_ascii=False))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-manifest',type=Path,default=PRIVATE)
    parser.add_argument('--apply-private',action='store_true',help='仅Claude执行；保留备份和MP3文件，只修剪清单')
    args=parser.parse_args()
    generate(args.private_manifest,args.apply_private)
