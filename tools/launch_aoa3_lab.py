"""Isolated official NeoForge AoA3/Aether client. OW fusion is NOT validated here."""
import argparse,hashlib,json,subprocess,zipfile,time
from pathlib import Path
from modpack.config import paths
from modpack.account import launch_options
import launch_minecraft as minecraft
ROOT=Path(__file__).resolve().parents[1]
PROFILE=paths().get('neoProfile')
def prepare(*,account_provider=None):
    info=json.loads(paths().get('neoInstallSource').read_text())
    version='neoforge-'+info['version'];metadata=minecraft.GAME/'versions'/version/(version+'.json')
    if not metadata.is_file():raise ValueError('Official NeoForge client installation is incomplete')
    mods=PROFILE/'mods';aoa=mods/'AoA3-1.21.1-3.7.16.1.jar'
    if hashlib.sha256(aoa.read_bytes()).hexdigest()!='16da1e00373bd854f0397c28d5b0d2c376e6eeec97135b35cac48607e4bfe66b':raise ValueError('AoA3 package identity changed')
    with zipfile.ZipFile(aoa) as z:
        for name in ['geckolib-neoforge-1.21.1-4.8.2.jar','TslatModdingExtensions-neoforge-1.21.1-1.0.0.jar','SmartBrainLib-neoforge-1.21.1-1.16.10.jar']:
            if 'META-INF/jarjar/'+name not in z.namelist():raise ValueError('Official bundled dependency absent')
    staged=json.loads((PROFILE/'staged-mods.json').read_text())
    extra=json.loads((PROFILE/'required-mods-extra.json').read_text())
    for row in [r for r in staged['mods'] if r.get('project')=='aether']+extra:
        target=mods/row['file']
        if target.parent.resolve()!=mods.resolve() or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Official NeoForge mod/dependency identity changed: '+row['file'])
    data=json.loads(metadata.read_text())
    if data.get('inheritsFrom')!='1.21.1' or data.get('mainClass')!='cpw.mods.bootstraplauncher.BootstrapLauncher':raise ValueError('NeoForge launch schema differs')
    identity,development=launch_options(paths(),account_provider)
    arguments=['-Xms1G','-Xmx4G']+(['-Dminecraft.api.session.host=http://127.0.0.1:9','-Dminecraft.api.services.host=http://127.0.0.1:9'] if development else [])
    options=dict(identity,executablePath=str(paths().get('java')),jvmArguments=arguments,disableMultiplayer=True,customResolution=True,resolutionWidth='1920',resolutionHeight='1080')
    command=minecraft.get_minecraft_command(version,minecraft.GAME,options);command[command.index('--gameDir')+1]=str(PROFILE)
    # The older vendored launcher assumes every selected version owns a JAR.
    # Modern NeoForge inherits vanilla and supplies the patched client via its
    # own libraries. Remove only that exact nonexistent selected-version entry.
    at=command.index('-cp')+1;absent=minecraft.GAME/'versions'/version/(version+'.jar')
    command[at]=';'.join(part for part in command[at].split(';') if Path(part).resolve()!=absent.resolve())
    for part in command[at].split(';'):
        if not Path(part).is_file():raise ValueError('Missing actual NeoForge classpath entry: '+part)
    for flag in (['--clientId','--xuid'] if development else []):
        if flag in command:
            i=command.index(flag);del command[i:i+2]
    command=[v.replace('${library_directory}',str(minecraft.GAME/'libraries')).replace('${classpath_separator}',';') for v in command]
    if any('${' in v for v in command):raise ValueError('Unresolved NeoForge argument')
    for flag,value in [('--width','1920'),('--height','1080')]:
        if flag in command:command[command.index(flag)+1]=value
    if not (PROFILE/'options.txt').exists():(PROFILE/'options.txt').write_text('onboardAccessibility:false\ntutorialStep:none\npauseOnLostFocus:false\nrenderDistance:8\nsimulationDistance:5\nfullscreen:false\nmaxFps:180\nparticles:0\n',encoding='utf-8')
    return command,dict(profile=str(PROFILE),loader=version,aoa='3.7.16.1',aether='1.5.10-neoforge',fusionAccepted=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();command,status=prepare()
    if not a.check:
        import psutil
        if any('aoa3-neoforge-client' in ' '.join(p.info.get('cmdline') or []) for p in psutil.process_iter(['cmdline']) if p.pid!=__import__('os').getpid()):raise ValueError('Isolated client already exists')
        folder=ROOT/'research/sprint-20261024'/('aoa3-client-'+time.strftime('%H%M%S'));folder.mkdir()
        with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
            child=subprocess.Popen(command,cwd=PROFILE,stdout=out,stderr=err)
        status.update(pid=child.pid,creation=psutil.Process(child.pid).create_time(),evidence=str(folder),launched=True)
        (PROFILE/'last-launch.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print(json.dumps(status))
