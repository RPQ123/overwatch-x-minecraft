"""File-only 24919 Winston declarations; SHA-guarded owned archive, no process."""
import hashlib
import json
from pathlib import Path
from ow_asset_chain import Archive,scan_refs
from inspect_hanzo_dragon_assets import FlatGraph
from prepare_hero_winston import GRAPHS

ROOT=Path(__file__).resolve().parents[1]

def audit():
    archive=Archive('winston-audit');archive.load_package('02e0000000000009')
    result=dict(offlineOnly=True,inGameVerified=False,graphs={},parameters={},assets={})
    graphs={}
    for _,rid,count,states in GRAPHS:
        guid=f'{rid:016x}';row=archive.resolve(guid);raw=archive.fetch(row['ckey'],guid+'.raw')
        if hashlib.md5(raw).hexdigest()!=row['ckey']:raise ValueError('Winston graph content key')
        graph=FlatGraph(raw)
        if len(graph.nodes)!=count:raise ValueError('Winston node count')
        for _,index,kind in states:graph.node(index,kind)
        graphs[guid[-4:]]=graph;result['graphs'][guid]=dict(sha256=hashlib.sha256(raw).hexdigest(),nodes=count)
    def assignment(s,index,value):
        g=graphs[s];node=g.node(index,0x4698e4b6)
        actual=g.literal(g.q(node+160))
        if actual!=value:raise ValueError(f'Original {s}:{index} differs')
        return dict(graph=s,node=index,variable=g.dynamic(g.q(node+144)),value=actual)
    for name,s,i,value in [('jumpCooldown','010a',5,8),
            ('jumpSpeed15','010a',6,15),('jumpSpeed30','010a',7,30),('jumpDamage','010a',39,50),
            ('barrierHp','00fa',1,1000),('barrierCooldown','00fa',4,13),('barrierSeconds','00fa',9,6),
            ('rageSeconds','0109',8,10),('rageHealth','0109',33,500),('teslaAmmo','00fe',13,100),
            ('teslaReload','00fe',25,1.5),('teslaRange','00fe',36,8),('teslaAngle','00fe',37,40)]:
        result['parameters'][name]=assignment(s,i,value)
    # StateStack inherits the same out_Var/value fields but has a different type.
    g=graphs['010a'];stack=g.node(3,0xf7d6498c)
    result['parameters']['primalJumpCooldown']=dict(graph='010a',node=3,variable=g.dynamic(g.q(stack+0x100)),value=g.literal(g.q(stack+0x110)))
    if result['parameters']['primalJumpCooldown']['value']!=2:raise ValueError('Primal jump cooldown')
    for s,index,label in [('00fa',22,'barrierPet'),('00fa',23,'projectorHand')]:
        g=graphs[s];node=g.nodes[index];refs=[]
        for at in sorted(g.objects):
            if node<=at<node+2500 and g.kind(at)==0xe53c2921:
                refs.append(f'{g.q(at+24):016x}')
        result['assets'][label]=refs
    for s in ('010a','0109'):
        g=graphs[s];effects=[]
        for at in sorted(g.objects):
            if g.kind(at)==0xb709560a:
                effects.append(f'{g.q(at+24):016x}')
        result['assets'][s+'Effects']=list(dict.fromkeys(effects))
    row=archive.resolve('02e0000000000009');raw=archive.fetch(row['ckey'],'02e0000000000009.raw')
    result['assets']['heroRefs']=[r['guid'] for r in scan_refs(raw,'02e0000000000009',archive.records) if r['guid'].startswith('0400')]
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'research/winston/evidence/declarations.json');a=p.parse_args()
    result=audit();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS Winston original graph audit; '+json.dumps(result['assets']))
