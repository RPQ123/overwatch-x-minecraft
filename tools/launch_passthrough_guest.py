"""Run only the isolated MC full-world frame proof, without any OW attachment."""
from modpack.config import paths
from pathlib import Path
import argparse,json,os,shutil,subprocess,urllib.request
from launch_minecraft import ROOT,GAME,build_command
from configure_passthrough import factory_options,world_name

PROFILE=paths().get('profile')


def _write_changed(path,text):
    if not path.is_file() or path.read_text(encoding='utf-8')!=text:
        path.write_text(text,encoding='utf-8')


def _copy_changed(source,target):
    from modpack.config import sha256
    if source.resolve()==target.resolve():return
    if target.is_file() and source.stat().st_size==target.stat().st_size and sha256(source)==sha256(target):return
    shutil.copy2(source,target)


def background_java(command):
    """Use the sibling GUI launcher; callers also suppress a fallback console."""
    java=Path(command[0])
    javaw=java.with_name('javaw.exe')
    if java.name.casefold()=='java.exe' and javaw.is_file():command[0]=str(javaw)
    return command
def prepare(visible=False,pose_test=False,daylight=False,superflat=False,survival=False,*,timeline=None):
    if timeline:timeline.mark('guest_prepare_started')
    if not pose_test:
        from render_optimization import verify
        verify()
    settings=json.loads((ROOT/'passthrough-settings.json').read_text(encoding='utf-8'))
    if settings.get('twilightTrial',False) and not pose_test:
        from twilight_forest import NAME,validate
        if not settings.get('worldName','').startswith('Overwatch Twilight '):raise ValueError('Twilight trial requires its separate lab save')
        validate(PROFILE/'mods'/NAME) # Never open the trial save without its pinned dimension mod.
    shaders=settings.get('shaders','off') if not pose_test else 'off'
    if not pose_test:
        from minecraft_shaders import prepare as prepare_shaders
        prepare_shaders(shaders)
    width,height=int(settings['width']),int(settings['height']);fps=int(settings['captureFps'])
    if not 320<=width<=2560 or not 180<=height<=1440 or not 30<=fps<=360:raise ValueError('Invalid persistent source resolution/frame rate')
    profile=paths().get('poseProfile') if pose_test else PROFILE
    if not pose_test:
        from boss_mods import verify as verify_boss_mods
        verify_boss_mods(profile)
    (profile/'mods').mkdir(parents=True,exist_ok=True)
    jar=ROOT/'guest/build/libs/owmc-guest-0.1.0.jar'
    if not jar.is_file():raise FileNotFoundError('Build guest with tools/build_guest.ps1 first')
    _copy_changed(jar,profile/'mods'/jar.name)
    api,=(GAME/'mods').glob('fabric-api-*.jar');_copy_changed(api,profile/'mods'/api.name)
    if not pose_test and not superflat:
        from modpack.startup_template import install as install_startup_template
        startup_template=install_startup_template(ROOT,profile,settings)
        if timeline:timeline.mark('guest_startup_template',**startup_template)
    options=profile/'options.txt'
    if not options.exists():options.write_text(factory_options(),encoding='utf-8')
    lines=options.read_text(encoding='utf-8').splitlines()
    if not any(line.startswith('resourcePacks:') for line in lines):
        options.write_text('\n'.join(lines+['resourcePacks:[]'])+'\n',encoding='utf-8')
    if not pose_test:
        from modpack.private_assets import prepared_profile_resources
        if not prepared_profile_resources(profile):
            from modpack.resources import prepare_optional
            prepare_optional(profile)
    # Combat trails and potion feedback remain visible at every graphics preset.
    values={'particles':'0'}
    if not visible:values.update(pauseOnLostFocus='false',fullscreen='false')
    if not pose_test and settings.get('performanceGraphics',False):
        values.update(graphicsMode='0',renderClouds='"false"',entityShadows='false',entityDistanceScaling='0.75',simulationDistance='5')
    lines=[line for line in options.read_text(encoding='utf-8').splitlines() if line.split(':',1)[0] not in values]
    _write_changed(options,'\n'.join(lines+[key+':'+value for key,value in values.items()])+'\n')
    command=build_command();command[command.index('--gameDir')+1]=str(profile)
    if not pose_test and paths().packaged and settings.get('startupCompilerBudget',False):
        inherited=os.environ.get('JAVA_TOOL_OPTIONS','')+' '+os.environ.get('JDK_JAVA_OPTIONS','')
        if 'CompilerDirectives' not in inherited and 'CompileCommand' not in inherited:
            compiler_file=profile/'config/owmc-startup-compiler-budget.json'
            directive='[{"match":"*::*","c2":{"Exclude":true}}]'
            compiler_file.parent.mkdir(parents=True,exist_ok=True)
            if compiler_file.exists() and compiler_file.read_text(encoding='utf-8').strip()!=directive:
                raise ValueError('启动编译配置已有外部改动，已保留。')
            if not compiler_file.exists():compiler_file.write_text(directive+'\n',encoding='utf-8')
            command[1:1]=['-XX:+UnlockDiagnosticVMOptions','-XX:CompilerDirectivesFile='+str(compiler_file),
                          '-Dowmc.startupCompilerBudget=true','-Dowmc.startupCompilerBudgetFile='+str(compiler_file)]
    for flag,value in (('--width',str(width)),('--height',str(height))):
        if flag in command:command[command.index(flag)+1]=value
        else:command.extend([flag,value])
    command[1:1]=['-Dowmc.frameExport=true','-Dowmc.hostPose=true','-Dowmc.hostMovement=true','-Dowmc.backgroundExport='+str(not visible).lower()]
    if not visible:command[1:1]=['-Dowmc.startHidden=true','-Dowmc.allowWindowShow=false']
    command.insert(1,'-Dowmc.nativeEventsDirectory='+str(ROOT/'native-host/build'))
    configured=paths()
    for property,key in (('owmc.privateAssetsDirectory','privateAssets'),('owmc.meshDirectory','meshAssets'),
                         ('owmc.heroVoiceDirectory','heroVoiceAssets'),('owmc.heroVoiceFfmpeg','ffmpeg')):
        command.insert(1,'-D'+property+'='+str(configured.get(key)))
    if settings.get('twilightTrial',False) and not pose_test:
        command.insert(1,'-Dowmc.twilightTrial=true')
    command.insert(1,'-Dowmc.fullBright='+str(shaders=='off' and settings.get('fullBright',True)).lower())
    if settings.get('dayNightCycle',False):command.insert(1,'-Dowmc.dayNightCycle=true')
    command.insert(1,'-Dowmc.captureFps='+str(fps))
    distance=int(settings.get('renderDistance',12))
    if not 8<=distance<=32:raise ValueError('Render distance must be 8..32 chunks')
    command.insert(1,'-Dowmc.renderDistance='+str(distance))
    if not pose_test and not superflat:
        selected_world=world_name(settings.get('worldName','Overwatch Survival World'))
        command.insert(1,'-Dowmc.worldName='+selected_world)
        # The existing native experimental-world backup prompt otherwise stalls
        # unattended cold starts even with twilightTrial=false. Consent is scoped
        # to this exact existing save; Java still uses vanilla backup-and-load.
        if settings.get('createWorld',False) or (profile/'saves'/selected_world/'level.dat').is_file():
            command.insert(1,'-Dowmc.startupBackupWorldName='+selected_world)
        command.insert(1,'-Dowmc.worldSeed='+str(int(settings.get('worldSeed',20261014))))
        command.insert(1,'-Dowmc.createWorld='+str(bool(settings.get('createWorld',False))).lower())
    if pose_test:command.insert(1,'-Dowmc.poseTest=true')
    if daylight:command.insert(1,'-Dowmc.daylightLab=true')
    if not pose_test and not superflat:command.insert(1,'-Dowmc.survivalWorld=true')
    if not survival and not pose_test and not superflat:command.insert(1,'-Dowmc.creativeWorld=true')
    if not pose_test and not superflat and settings.get('villagePortals',False):command.insert(1,'-Dowmc.villagePortals=true')
    if timeline:timeline.mark('guest_prepare_finished')
    return background_java(command)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--visible',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--pose-test',action='store_true',help='Isolated marker world; allows explicitly synthetic pose packets');parser.add_argument('--daylight',action='store_true',help='Set the private test save to midday and clear weather once on entry');parser.add_argument('--superflat',action='store_true',help='Reopen the previous creative test save instead of the natural world');parser.add_argument('--survival',action='store_true',help='Opt back into survival damage; default is natural creative with invulnerability');args=parser.parse_args()
    if not args.check:
        try:
            status=json.load(urllib.request.urlopen('http://127.0.0.1:32133/health',timeout=.5))
        except (OSError,ValueError):status=None
        if status and status.get('mode')=='full-world-frame-proof':raise SystemExit('The isolated passthrough guest is already running. Preserve it or stop it normally before relaunching.')
    command=prepare(args.visible,args.pose_test,args.daylight,args.superflat,args.survival);profile=paths().get('poseProfile') if args.pose_test else PROFILE
    if args.check:print(json.dumps({'profile':str(profile),'world':'Overwatch Pose Test' if args.pose_test else 'Overwatch Passthrough World' if args.superflat else 'Overwatch Survival World','owAttached':False}))
    else:
        (profile/'logs').mkdir(exist_ok=True)
        with (profile/'logs/launch.log').open('w',encoding='utf-8') as log:raise SystemExit(subprocess.call(command,cwd=profile,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
