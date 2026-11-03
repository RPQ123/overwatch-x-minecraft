"""Offline builders evidence summary; never attaches to or drives either game."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import json
import hashlib
from pathlib import Path
from inspect_hanzo_dragon_assets import FlatGraph

ROOT = Path(__file__).resolve().parents[2]


def scalar_tree(value, path=''):
    if isinstance(value, dict):
        if 'literal' in value:
            yield path, value['literal']
        for field in value.get('fields', []):
            key = path + '/' + field['hash']
            for name in ('int', 'float', 'guid'):
                if name in field:
                    yield key, field[name]
            if 'object' in field:
                yield from scalar_tree(field['object'], key)


def main():
    base = ROOT / 'research/sprint-20261024'
    d = json.loads((base/'torb-kit-calibration1/changed-definitions.json').read_text())
    proof=dict(liveAcceptance=False,mcAdaptation=['tire physics/control/camera/non-damaging expiry','MC death edge and bomb fuse/blast',
               'turret contact/repair/upgrade','scrap pickup/budget/display','armor absorption and Core effects'],
               hammerDamageLiterals=list(scalar_tree(d['05800000000000f3:24'])),graphs={})
    cache=ROOT/'research/asset-cache/builders-graphs'
    for guid in ('0580000000000232','0580000000000233','058000000000022a','05800000000000f3','05800000000001c2'):
        raw=(cache/(guid+'.raw')).read_bytes();g=FlatGraph(raw)
        proof['graphs'][guid]=dict(sha256=hashlib.sha256(raw).hexdigest(),nodes=len(g.nodes))
        if guid.endswith('0232'):
            n=g.node(32,0x1bb99c36);entity=g.typed(g.q(n+0x88),0xe53c2921)
            assert g.q(entity+24)==0x040000000000039c
            proof['tireCreation']=dict(graph=guid,node=32,type='1bb99c36',fieldOffset='0x88',entity='040000000000039c')
        if guid.endswith('0233'):
            observed=base/'junk-detonate-calibration1/definitions.json'
            local_graphs=json.loads(observed.read_text())
            proof['tireDetonation']=dict(childGraph=guid,logicalButtonNodes=[i for i,n in enumerate(g.nodes) if g.kind(n)==0xff77458c],
                modifyHealthNodes=[i for i,n in enumerate(g.nodes) if g.kind(n)==0x619d9e95],
                observedDefinitions=str(observed),childInObservedLocalModel=guid in local_graphs,
                nativeCommitAuthenticated=False,attackEnabled=False,
                limitation='Existing local-model capture is not a RIP-Tire detonation calibration. No authenticated child-entity/logger ownership or commit-node mapping; declarations/buttons alone do not authorize damage.')
    folder=base/'builders-offline';folder.mkdir(exist_ok=True)
    (folder/'evidence.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(liveAcceptance=False,graphs=5,tireNode=32,hammerDamage=75,output=str(folder/'evidence.json'))))


if __name__ == '__main__':
    main()
