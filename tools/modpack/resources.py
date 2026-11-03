"""Optional private resources: report missing/invalid inputs without loading them."""
from __future__ import annotations

from pathlib import Path

from genji_voice_assets import prepare as genji
from mccree_voice_assets import prepare as mccree
from combat_feedback_assets import prepare as feedback
from early_chinese_voice_assets import prepare as chinese
from four_dps_voice_assets import prepare as skills
from pack_pharah_barrage import prepare as barrage
from pulse_bomb_assets import prepare as pulse

from .config import paths, write_json

REPORT = 'research/launcher/resource-status.json'


def prepare_optional(profile: Path) -> dict:
    rows = []
    for module, label, prepare in (
        ('genji_voice_assets', '源氏语音', genji), ('mccree_voice_assets', '麦克雷语音', mccree),
        ('combat_feedback_assets', '命中反馈', feedback), ('early_chinese_voice_assets', '中文选人语音', chinese),
        ('four_dps_voice_assets', '技能语音', skills), ('pack_pharah_barrage', '法老之鹰语音', barrage),
        ('pulse_bomb_assets', '脉冲炸弹模型', lambda _: pulse()),
    ):
        try:
            result = prepare(profile)
            ready = bool(result.get('ready')) if isinstance(result, dict) else bool(result)
            reason = '' if ready else '未找到完整且有效的本地资源'
        except (OSError, ValueError, KeyError, TypeError) as error:
            ready, reason = False, f'资源未启用：{error}'
        row = dict(component=module, label=label, ready=ready)
        if not ready:
            row['warning'] = f'{label}不可用：{reason}；继续启动，保留技能与原生表现。'
            print(row['warning'], flush=True)
        rows.append(row)
    configured = paths()
    for key, label in (('meshAssets', '英雄附加模型'), ('heroVoiceAssets', '完整英雄语音')):
        location = configured.get(key)
        ready = location.is_dir() and (any(location.glob('*/pack.json')) if key == 'meshAssets' else (location / 'manifest.json').is_file())
        row = dict(component=key, label=label, ready=ready)
        if not ready:
            row['warning'] = f'{label}缺失；继续启动，对应附加语音或模型将停用。'
            print(row['warning'], flush=True)
        rows.append(row)
    summary=configured.get('privateAssets')/'bundle-summary.json'
    if summary.is_file():
        from .config import read_json
        try:
            bundle=read_json(summary)
            for key,label in (('missingVoices','白名单语音'),('missingModels','模型组')):
                count=len(bundle.get(key,[]))
                if count:
                    warning=f'私有包缺少 {count} 项{label}；继续启动，对应资源将停用。'
                    print(warning,flush=True)
                    rows.append(dict(component=key,label=label,ready=False,warning=warning))
        except (OSError,ValueError,TypeError):
            pass  # Java still validates actual assets, never trusts this UI summary.
    value = dict(schemaVersion=1, profile=str(Path(profile).resolve()), components=rows,
                 warnings=[r['warning'] for r in rows if 'warning' in r])
    write_json(configured.root / REPORT, value)
    return value
