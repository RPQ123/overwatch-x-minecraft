"""Install a pinned official Fabric beta into the stopped private MC profile."""
from modpack.config import paths
import argparse,hashlib,json,shutil,urllib.request,zipfile
from pathlib import Path
import psutil
from configure_passthrough import ROOT,SETTINGS,SAVES,world_name

NAME='twilightforest-fabric-1.21.1-4.8.754.jar'
SHA256='7f4bf512341bda95eeec0343d1233e8ef733ea599f489d60b27db13b2226fb42'
SOURCE='https://edge.forgecdn.net/files/9091/40/'+NAME
PAGE='https://www.curseforge.com/minecraft/mc-mods/the-twilight-forest/files/9091040'
PROFILE=paths().get('profile')
SNAPSHOT=ROOT/'research/twilight-settings-before.json'

def stopped():
    for proc in psutil.process_iter(['name','cmdline']):
        try:
            info=dict(proc.info or {});args=info.get('cmdline') or []
            if (info.get('name') or '').lower() in ('java.exe','javaw.exe') and str(PROFILE) in args:
                raise RuntimeError('Save and stop the project session before changing its mod profile')
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue

def validate(path):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA256:raise ValueError('Twilight Forest SHA256 differs from the pinned package')
    with zipfile.ZipFile(path) as archive:
        meta=json.loads(archive.read('fabric.mod.json'))
    if meta['id']!='twilightforest' or meta['version']!='4.8.754':raise ValueError('Unexpected mod identity')
    return meta

def install(name):
    stopped();name=world_name(name)
    if not name.startswith('Overwatch Twilight '):raise ValueError('Use a separate Overwatch Twilight lab save')
    if (SAVES/name/'level.dat').exists():raise FileExistsError('Trial save already exists; select it with configure_passthrough --world')
    target=PROFILE/'mods'/NAME
    others=[p for p in target.parent.glob('twilightforest*.jar') if p.name!=NAME]
    if others:raise ValueError('Another Twilight Forest version is installed; preserve and inspect it first')
    if not SNAPSHOT.exists():
        SNAPSHOT.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SETTINGS,SNAPSHOT)
    stage=ROOT/'research/mod-downloads'/NAME;stage.parent.mkdir(parents=True,exist_ok=True)
    if not stage.exists():
        with urllib.request.urlopen(urllib.request.Request(SOURCE,headers={'User-Agent':'OWMC-Local-Lab/1.0'}),timeout=30) as response:
            data=response.read(45*1024*1024)
        if len(data)>=45*1024*1024:raise ValueError('Unexpected package size')
        pending=stage.with_suffix('.part');pending.write_bytes(data);validate(pending);pending.replace(stage)
    meta=validate(stage)
    api=list((PROFILE/'mods').glob('fabric-api-*.jar'))
    if len(api)!=1:raise ValueError('Expected one installed Fabric API')
    with zipfile.ZipFile(api[0]) as archive:api_meta=json.loads(archive.read('fabric.mod.json'))
    # This pinned build is the project's verified loader/API combination.
    if api_meta['version']!='0.116.17+1.21.1':raise ValueError('Recheck Twilight dependencies against the changed Fabric API')
    pending=target.with_suffix('.part');shutil.copy2(stage,pending);validate(pending);pending.replace(target)
    settings=json.loads(SETTINGS.read_text(encoding='utf-8'))
    settings.update(worldName=name,createWorld=True,twilightTrial=True,shaders='off',renderDistance=8)
    pending=SETTINGS.with_suffix('.tmp');pending.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8');pending.replace(SETTINGS)
    manifest=dict(source=PAGE,download=SOURCE,sha256=SHA256,version=meta['version'],world=name,backupSettings=str(SNAPSHOT))
    (ROOT/'research/twilight-install.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install',metavar='NEW_TRIAL_WORLD')
    parser.add_argument('--restore-settings',action='store_true',help='Restore previous settings; keep the mod and its saves intact')
    parser.add_argument('--build-portal',action='store_true',help='Build an active grass/flower portal ahead in the separate creative trial')
    args=parser.parse_args()
    if args.build_portal:
        req=urllib.request.Request('http://127.0.0.1:32133/world/twilight/portal',method='POST')
        with urllib.request.urlopen(req,timeout=3) as response:result=json.load(response)
    elif args.install:result=install(args.install)
    elif args.restore_settings:
        stopped();data=SNAPSHOT.read_bytes();json.loads(data);pending=SETTINGS.with_suffix('.tmp');pending.write_bytes(data);pending.replace(SETTINGS);result={'restored':str(SNAPSHOT),'modPreserved':True}
    else:
        target=PROFILE/'mods'/NAME
        result={'installed':target.exists(),'source':PAGE,'sha256':SHA256}
        if target.exists():result['version']=validate(target)['version']
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
