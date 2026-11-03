"""Prepare Hanzo-only private mesh jobs; no game launch, JAR build or install.

--extract calls the SHA-guarded ow_asset_chain reader for the listed roots.
The Sonic bundle explicitly associates the calibrated impact script c3 with
0149: this is a research association, NOT a fabricated raw archive reference.
Run build_mesh_pack --batch on the printed JSON separately (Claude owns install).
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from ow_asset_chain import CACHE, ROOT

ARROWS = ['040000000000' + suffix for suffix in ['0144', '020b', '0149', '020d', '01a4', '020c', '014a', '01b9']]
SCRIPT = '05800000000000c3'
EFFECTS = ['030000000000' + suffix for suffix in ['0297', '0295', '02fe']]
OUT = ROOT / 'research/hanzo-arrows-20261025'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(guid):
    path = CACHE / guid / 'chain.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if data['entity'] != guid or data['build'] != '0.8.0.24919' or not data['complete']:
        raise ValueError('Incomplete/wrong asset chain: ' + guid)
    for resource in data['resources'].values():
        if resource['status'] != 'read' or sha(path.parent / resource['file']) != resource['sha256']:
            raise ValueError('Raw asset hash/status: ' + guid)
    return path, data


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    chains = {g: load(g) for g in ARROWS + [SCRIPT] + EFFECTS}
    script_path, script = chains[SCRIPT]
    script_raw = (script_path.parent / script['resources'][SCRIPT]['file']).read_bytes()
    effect_offsets = {}
    for effect in EFFECTS:
        at = script_raw.find(struct.pack('<Q', int(effect, 16)))
        if at < 0 or at % 8:
            raise ValueError('Effect not aligned in original c3: ' + effect)
        effect_offsets[effect] = at

    # Bundle an original effect with its original arrow, preserving the normal
    # packer contract (04 root). Every imported source and the association are
    # recorded; do not pretend this was a direct raw-entity GUID reference.
    destination, sonic = chains['0400000000000149']
    for guid in [SCRIPT] + EFFECTS:
        path, data = chains[guid]
        if data['executableSha256'] != sonic['executableSha256']:
            raise ValueError('Different offline executable in bundle')
        for resource, row in data['resources'].items():
            if resource in sonic['resources']:
                if sonic['resources'][resource]['sha256'] != row['sha256']:
                    raise ValueError('Conflicting original resource')
                continue
            sonic['resources'][resource] = row
            names = [row['file']]
            for field in ['model', 'texture']:
                if row.get(field, {}).get('file'):
                    names.append(row[field]['file'])
            for name in names:
                if Path(name).name != name:
                    raise ValueError('Asset path')
                shutil.copy2(path.parent / name, destination.parent / name)
        for export in data.get('meshExports', []):
            # Only selected original effect/material pairs are pack candidates.
            if not export.get('material') or not export.get('file'):
                continue
            shutil.copy2(path.parent / export['file'], destination.parent / export['file'])
            existing = [e for e in sonic['meshExports'] if (e['model'], e.get('material')) == (export['model'], export.get('material'))]
            if not existing:
                sonic['meshExports'].append(export)
    sonic['researchAssociations'] = dict(
        kind='calibrated Sonic impact script association; not a raw 0149 GUID edge',
        nativeSnapshot='research/sprint-20261024/hanzo-current-calibration2/current-c3.json',
        nativeSnapshotSha256=sha(ROOT / 'research/sprint-20261024/hanzo-current-calibration2/current-c3.json'),
        script=SCRIPT, scriptEffectOffsets=effect_offsets,
        sourceChains={g: sha(chains[g][0]) for g in [SCRIPT] + EFFECTS},
        shaderPlaybackVerified=False)
    destination.write_text(json.dumps(sonic, indent=2) + '\n', encoding='utf-8')

    jobs = [dict(name='hanzo-arrow-' + name, entity='040000000000' + suffix, model='0d00000000000b8d')
            for name, suffix in [('primary', '0144'), ('sonic', '0149'), ('scatter', '01a4')]]
    jobs += [dict(name='hanzo-sonic-' + name, entity='0400000000000149', model=model, material=material)
             for name, model, material in [('pulse', '0d00000000001385', '0e0000008a92fe7f'),
                                            ('sense', '0d00000000000dbf', '0e0000007b543afe')]]
    jobs += [dict(name='hanzo-arrow-' + name, entity='040000000000' + entity, model='0d0000000000' + model, material='0e000000' + material)
             for name, entity, model, material in [
                 ('primary-glow', '0144', '0801', '9537fc6e'),
                 ('primary-trail', '0144', '075d', '98d4b643'),
                 ('sonic-glow', '0149', '0801', '6966f477'),
                 ('scatter-glow', '01a4', '0801', '2ded6c3b'),
                 ('scatter-trail', '01a4', '075d', '181b690c')]]
    jobs_path = OUT / 'mesh-jobs.json'
    jobs_path.write_text(json.dumps(jobs, indent=2) + '\n', encoding='utf-8')
    evidence = dict(build='0.8.0.24919', gameStarted=False, installed=False, jobs=jobs,
                    oldHanzoArrowEntity='04000000000001a4', model='0d00000000000b8d',
                    arrowSubmeshSelection=dict(primary=[0, 1, 4], sonic=[1, 3, 4], scatter=[1, 2, 4]),
                    selectionEvidence='extracted geometry and one part contact sheet; native animation/hide masks unverified',
                    originalChildResources=['04000000000001a4', '040000000000020c'],
                    pulseAssociation=sonic['researchAssociations'],
                    limits='Static original geometry/UV/mask only; color, cadence, expansion and attachment are MC adaptation')
    (OUT / 'assets.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(jobs=str(jobs_path), count=len(jobs), installed=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', action='store_true')
    args = parser.parse_args()
    if args.extract:
        for guid in ARROWS + [SCRIPT] + EFFECTS:
            subprocess.run([sys.executable, str(ROOT / 'tools/ow_asset_chain.py'), guid], check=True, cwd=ROOT)
    prepare()
