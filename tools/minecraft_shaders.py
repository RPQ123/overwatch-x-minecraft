"""Pinned Iris/MakeUp options for the private MC profile; originals stay private."""
from modpack.config import paths
import hashlib,json,urllib.request,zipfile,io
from pathlib import Path
import psutil

ROOT=Path(__file__).resolve().parents[1]
PROFILE=paths().get('profile')
MODES={'off':'关闭（优先帧率）','low':'光影：低','medium':'光影：中'}
IRIS=('iris-fabric-1.8.14-beta.1+mc1.21.1.jar','https://cdn.modrinth.com/data/YL57xq9U/versions/bAo1Qhte/iris-fabric-1.8.14-beta.1%2Bmc1.21.1.jar',2791343,'a7fbb629793c52f0be8b049f787cb598879239b1ad8e1de62e103c8b9efff140e3232b93ef1f14e505d262897d8cf9505b1126396429ad4056bff969c8674e52')
PACK=('MakeUp-UltraFast-9.5g.zip','https://cdn.modrinth.com/data/izsIPI7a/versions/pgb0JjoN/MakeUp-UltraFast-9.5g.zip',405096,'90a2f75eb073eaae5fe65f2ea5f8d656c122760c07ff75306728df4b162c42f88be531f026d174e035fea153f0ac5e227e8885d8b199335d3beadb6a58f79239')

def stopped():
    for p in psutil.process_iter(['cmdline']):
        try:
            info=dict(p.info or {})
            if str(PROFILE) in (info.get('cmdline') or []):raise RuntimeError('先关闭两款游戏，再切换光影')
        except (psutil.AccessDenied,psutil.NoSuchProcess):pass

def artifact(folder,item):
    name,url,size,digest=item;path=folder/name
    data=path.read_bytes() if path.exists() else urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'OWMC-local-lab/1.0'}),timeout=45).read(size+1)
    if len(data)!=size or hashlib.sha512(data).hexdigest()!=digest:raise ValueError('Artifact size/SHA512 mismatch: '+name)
    if not path.exists():
        folder.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
    return path

def prepare(mode):
    if mode not in MODES:raise ValueError('Unknown shader option')
    stopped()
    # Off removes only our exact known loader, preserving the current fast path.
    active=PROFILE/'mods'/IRIS[0];parked=PROFILE/'owmc-disabled-mods'/IRIS[0]
    if mode=='off':
        if active.exists():
            artifact(active.parent,IRIS);parked.parent.mkdir(exist_ok=True)
            if parked.exists():
                artifact(parked.parent,IRIS);active.unlink()
            else:active.replace(parked)
    else:
        if parked.exists() and not active.exists():artifact(parked.parent,IRIS);active.parent.mkdir(exist_ok=True);parked.replace(active)
        artifact(active.parent,IRIS);pack=artifact(PROFILE/'shaderpacks',PACK)
        # Use the pack's own named profile, then explicitly disable blur/DOF.
        with zipfile.ZipFile(pack) as archive:
            lines=archive.read('shaders/shaders.properties').decode().splitlines()
        profile=next(x.split('=',1)[1] for x in lines if x.startswith('profile.'+mode+'='))
        options={}
        for token in profile.split():
            if '=' in token:k,v=token.split('=',1)
            else:k,v=token.lstrip('!'),str(not token.startswith('!')).lower()
            options[k]=v
        options.update(MOTION_BLUR='false',DOF='false',AA_TYPE='0')
        Path(str(pack)+'.txt').write_text('\n'.join(k+'='+v for k,v in options.items())+'\n',encoding='utf-8')
    config=PROFILE/'config/iris.properties';config.parent.mkdir(parents=True,exist_ok=True)
    previous={}
    if config.exists():
        for line in config.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):k,v=line.split('=',1);previous[k]=v
    previous.update(enableShaders=str(mode!='off').lower(),shaderPack=PACK[0],maxShadowRenderDistance='8')
    config.write_text('\n'.join(k+'='+v for k,v in previous.items())+'\n',encoding='utf-8')
    return mode

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=MODES);a=p.parse_args();print(prepare(a.mode))
