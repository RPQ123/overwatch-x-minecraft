"""Choose a private MC save and flight key without editing launcher source."""
from modpack.config import paths
import argparse,hashlib,json,os,shutil,subprocess,sys
from minecraft_shaders import MODES
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SAVES=paths().get('profile')/'saves'
SETTINGS=ROOT/'passthrough-settings.json'
OW_QUALITY={'low':'守望先锋低','medium':'守望先锋中'}
FLIGHT_KEYS=('F6',)
RESERVED_FLIGHT_KEYS={'F7':'地狱门','F8':'末地传送门','F9':'暮色森林门','F10':'随机怪物','F11':'大招充满','F12':'暮色Boss直达菜单'}

FACTORY_WORLD='Overwatch World'
FACTORY_SEED=20261014


def factory_settings():
    """A new pack never inherits the developer's world or display settings."""
    from modpack.first_run import DEFAULT_SETTINGS
    return {**DEFAULT_SETTINGS,'worldName':FACTORY_WORLD,'worldSeed':FACTORY_SEED,
            'createWorld':True,'twilightTrial':False,'shaders':'off','renderDistance':12,
            'startupParallel':True,'showMinecraft':False}


def factory_options(resource_packs=()):
    """Only new profiles get these defaults; existing player choices survive."""
    values={
        'version':'3955','lang':'zh_cn','onboardAccessibility':'false','narrator':'0',
        'tutorialStep':'none','joinedFirstServer':'true','skipMultiplayerWarning':'true',
        'hideBundleTutorial':'true','realmsNotifications':'false',
        'soundCategory_music':'0.0','soundCategory_master':'1.0',
        'pauseOnLostFocus':'false','renderDistance':'12','simulationDistance':'5',
        'fullscreen':'false','maxFps':'165','enableVsync':'false','fov':'0.0',
        'bobView':'false','graphicsMode':'0','renderClouds':'"false"',
        'entityShadows':'false','entityDistanceScaling':'0.75','particles':'0',
        'resourcePacks':json.dumps(['vanilla','fabric',*resource_packs],separators=(',',':')),
        'incompatibleResourcePacks':'[]',
    }
    return '\n'.join(key+':'+value for key,value in values.items())+'\n'

def validate_flight_key(value):
    """Reject a legacy conflicting assignment; never silently migrate it."""
    if not isinstance(value,str):raise ValueError('飞行键必须是 F6。')
    value=value.upper()
    if value in RESERVED_FLIGHT_KEYS:
        raise ValueError(f'{value} 已用于{RESERVED_FLIGHT_KEYS[value]}，不能兼作飞行键。请明确选择 F6 后保存；原设置不会自动迁移。')
    if value not in FLIGHT_KEYS:raise ValueError('当前支持的独立飞行键是 F6。')
    return value

def flight_key_argument(value):
    try:return validate_flight_key(value)
    except ValueError as failure:raise argparse.ArgumentTypeError(str(failure)) from failure

def world_name(value):
    if not isinstance(value,str) or not value or value in ('.','..') or any(c in value for c in '<>:"/\\|?*') or value.rstrip(' .')!=value or any(ord(c)<32 for c in value):
        raise ValueError('World name must be one save folder name')
    if value.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
        raise ValueError('Reserved Windows folder name')
    return value

def available():
    return sorted(p.name for p in SAVES.iterdir() if p.is_dir() and (p/'level.dat').is_file()) if SAVES.exists() else []

def gui():
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    settings_raw=SETTINGS.read_bytes();settings=json.loads(settings_raw.decode('utf-8'));settings_sha=hashlib.sha256(settings_raw).hexdigest();window=tk.Tk();window.title('守望先锋 × 我的世界 — 设置');window.geometry('650x680');window.minsize(620,660)
    world=tk.StringVar(value=settings.get('worldName','Overwatch Survival World'));key=tk.StringVar(value=settings.get('flightKey','F6'))
    panel=ttk.Frame(window,padding=20);panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='Minecraft 地图存档').pack(anchor='w')
    chooser=ttk.Combobox(panel,textvariable=world,values=available(),state='readonly',width=55);chooser.pack(fill='x',pady=6)
    def invoke(*arguments):
        nonlocal settings_sha
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),*arguments,'--expected-settings-sha256',settings_sha],capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
        if result.returncode:messagebox.showerror('未保存',result.stderr);return False
        settings_raw=SETTINGS.read_bytes();settings_sha=hashlib.sha256(settings_raw).hexdigest();settings.update(json.loads(settings_raw.decode('utf-8')))
        return True
    def import_map():
        source=filedialog.askdirectory(title='选择包含 level.dat 的 Java 版地图文件夹')
        if source and invoke('--import-world',source):chooser['values']=available();world.set(Path(source).name)
    ttk.Button(panel,text='导入地图副本…',command=import_map).pack(anchor='w')
    ttk.Label(panel,text='飞行开关（空格上升，Ctrl 下降）').pack(anchor='w',pady=(12,2))
    ttk.Combobox(panel,textvariable=key,values=FLIGHT_KEYS,state='readonly',width=10).pack(anchor='w')
    ttk.Label(panel,text='F7/F8 传送门 · F9 暮色门 · F10 随机怪 · F11 充能 · F12 暮色Boss菜单，不能兼作飞行键。',wraplength=520).pack(anchor='w',pady=4)
    if key.get().upper() not in FLIGHT_KEYS:
        ttk.Label(panel,text='旧飞行键与工具键冲突；请手动选择 F6 后保存。',foreground='#a03020').pack(anchor='w')
    shader=tk.StringVar(value=MODES.get(settings.get('shaders','off'),MODES['off']))
    ttk.Label(panel,text='Minecraft 光影（重启生效）').pack(anchor='w',pady=(12,2))
    ttk.Combobox(panel,textvariable=shader,values=list(MODES.values()),state='readonly',width=35).pack(anchor='w')
    ttk.Label(panel,text='开启光影会降低帧率；关闭可保留原来的清晰画面。').pack(anchor='w',pady=4)
    resolution=tk.StringVar(value='1440p' if settings.get('height')==1440 else '1080p')
    distance=tk.StringVar(value=str(settings.get('renderDistance',16)))
    ttk.Label(panel,text='画面清晰度').pack(anchor='w',pady=(10,2))
    ttk.Combobox(panel,textvariable=resolution,values=['1080p','1440p'],state='readonly',width=16).pack(anchor='w')
    ttk.Label(panel,text='区块视野').pack(anchor='w',pady=(8,2))
    ttk.Combobox(panel,textvariable=distance,values=['8','12','15','16','20','24','32'],state='readonly',width=16).pack(anchor='w')
    owquality=tk.StringVar(value=OW_QUALITY.get(settings.get('nativeRenderProfile','medium'),OW_QUALITY['medium']))
    ttk.Label(panel,text='守望先锋视频画质').pack(anchor='w',pady=(10,2))
    ttk.Combobox(panel,textvariable=owquality,values=list(OW_QUALITY.values()),state='readonly',width=16).pack(anchor='w')
    saved_status=tk.StringVar()
    def save():
        mode=next(k for k,v in MODES.items() if v==shader.get())
        quality=next(k for k,v in OW_QUALITY.items() if v==owquality.get())
        selected='--new-world' if settings.get('createWorld') and world.get()==settings.get('worldName') and not (SAVES/world.get()/'level.dat').is_file() else '--world'
        if invoke(selected,world.get(),'--flight-key',key.get(),'--shaders',mode,'--resolution',resolution.get(),'--render-distance',distance.get(),'--ow-quality',quality):saved_status.set('已保存；设置在下一次正常重启生效。可使用启动器的“正常重启”。')
    ttk.Button(panel,text='保存设置',command=save).pack(anchor='e',pady=8)
    ttk.Label(panel,textvariable=saved_status,wraplength=520).pack(anchor='w')
    from project_launcher import show_launcher_window
    show_launcher_window(window)
    window.mainloop()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gui',action='store_true')
    parser.add_argument('--settings-owned',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--expected-settings-sha256',help=argparse.SUPPRESS)
    parser.add_argument('--list-worlds',action='store_true')
    parser.add_argument('--world',help='Existing folder under guest-passthrough-client/saves')
    parser.add_argument('--new-world',help='Create a new natural creative world with the configured seed')
    parser.add_argument('--import-world',type=Path,help='Copy an unpacked Java 1.21.1-compatible save, preserving the source')
    parser.add_argument('--flight-key',type=flight_key_argument,choices=FLIGHT_KEYS,help='F6 only; F7..F11 are reserved tool keys. Legacy conflicts require an explicit choice.')
    parser.add_argument('--shaders',choices=list(MODES),help='off, low or medium; applies on the next game startup')
    parser.add_argument('--resolution',choices=['1080p','1440p'])
    parser.add_argument('--render-distance',type=int,choices=range(8,33))
    parser.add_argument('--ow-quality',choices=['low','medium'])
    args=parser.parse_args();settings_raw=SETTINGS.read_bytes();settings=json.loads(settings_raw.decode('utf-8'))
    if args.settings_owned and not args.gui:raise ValueError('--settings-owned is only valid for the coordinated GUI')
    if args.gui:
        if args.settings_owned:return gui()
        from project_launcher import SessionBackend,run_action
        import time
        backend=SessionBackend(ROOT)
        return run_action(backend,'settings',backend.logs/(time.strftime('%Y%m%d-%H%M%S')+'-settings.log'))
    editing=bool(args.import_world or args.new_world or args.world or args.flight_key or args.shaders or args.resolution or args.render_distance or args.ow_quality)
    if editing:
        if args.expected_settings_sha256 and hashlib.sha256(settings_raw).hexdigest()!=args.expected_settings_sha256:
            raise ValueError('设置已被其他操作更改，请重新打开设置后再保存；本次没有覆盖新设置。')
        # Do this before copying a map or editing any setting. An unrelated
        # graphics change must not preserve a flight/portal double binding.
        validate_flight_key(args.flight_key or settings.get('flightKey','F6'))
    if args.import_world:
        source=args.import_world.resolve(strict=True);name=world_name(args.world or source.name);target=SAVES/name
        if not (source/'level.dat').is_file():raise ValueError('Select the save folder containing level.dat')
        if target.exists():raise FileExistsError('Destination exists; choose a different --world name')
        if source==target or source in target.parents:raise ValueError('Destination cannot be inside source')
        SAVES.mkdir(exist_ok=True,parents=True);shutil.copytree(source,target);args.world=name
    if args.new_world:
        name=world_name(args.new_world)
        if (SAVES/name/'level.dat').is_file():raise FileExistsError('Destination exists; choose --world to reuse it')
        settings['worldName']=name;settings['createWorld']=True
    if args.world:
        name=world_name(args.world)
        if not (SAVES/name/'level.dat').is_file():raise ValueError('World is not installed; use --list-worlds or --import-world')
        settings['worldName']=name;settings['createWorld']=False
    if args.flight_key:settings['flightKey']=args.flight_key
    if args.shaders:settings['shaders']=args.shaders
    if args.resolution:settings['width'],settings['height']=(2560,1440) if args.resolution=='1440p' else (1920,1080)
    if args.render_distance:settings['renderDistance']=args.render_distance
    if args.ow_quality:settings['nativeRenderProfile']=args.ow_quality
    if args.new_world or args.world or args.flight_key or args.shaders or args.resolution or args.render_distance or args.ow_quality:
        if (args.new_world or args.world) and not settings.get('worldName','').startswith('Overwatch Twilight '):settings['twilightTrial']=False
        if args.expected_settings_sha256 and hashlib.sha256(SETTINGS.read_bytes()).hexdigest()!=args.expected_settings_sha256:
            raise ValueError('保存期间设置被其他操作更改；本次没有覆盖新设置。')
        temporary=SETTINGS.with_name(SETTINGS.name+f'.{os.getpid()}.tmp');temporary.write_text(json.dumps(settings,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');temporary.replace(SETTINGS)
    print(json.dumps({'selectedWorld':settings.get('worldName','Overwatch Survival World'),'createWorld':settings.get('createWorld',False),'flightKey':settings.get('flightKey','F6'),'shaders':settings.get('shaders','off'),'nativeRenderProfile':settings.get('nativeRenderProfile','medium'),'resolution':[settings.get('width'),settings.get('height')],'renderDistance':settings.get('renderDistance',16),'worlds':available(),'apply':'Restart the game from the launcher ow x mc 启动器.exe'},ensure_ascii=False,indent=2))

if __name__=='__main__':raise SystemExit(main())
