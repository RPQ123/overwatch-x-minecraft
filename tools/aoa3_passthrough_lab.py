"""Private NeoForge/Connector fusion lab; production Fabric profile is preserved."""
import argparse,ctypes,hashlib,json,os,sys,time,psutil
from pathlib import Path
from modpack.config import paths
import launch_passthrough_session as session
import launch_aoa3_lab as neo
ROOT=Path(__file__).resolve().parents[1]
PROFILE=paths().get('aoaProfile')
WORLD='Overwatch Twilight Switch AoA Compatibility Lab'
SHA='58dfbc95f6e53e8618736c75984a74077d1a0a61c1c76441d1ae5f817ac315b0'

def prepare(visible=True):
    neo.PROFILE=PROFILE
    if hashlib.sha256((PROFILE/'mods/owmc-guest-0.1.0.jar').read_bytes()).hexdigest()!=SHA:raise ValueError('NeoForge lab bridge identity changed')
    connector=PROFILE/'mods/connector-2.0.0-beta.17+1.21.1-full.jar'
    if hashlib.sha256(connector.read_bytes()).hexdigest()!='ca70b57df3a7a4e8d211fea7ff3ae77e768482af374f26bf953ff5fd755564f0':raise ValueError('Official Connector identity changed')
    command,_=neo.prepare()
    values={'frameExport':'true','hostPose':'true','hostMovement':'true','backgroundExport':'false','creativeWorld':'true','survivalWorld':'true','createWorld':'true','worldName':WORLD,'worldSeed':'-490526775015596785','renderDistance':'8','captureFps':'240','dayNightCycle':'true','fullBright':'false','twilightTrial':'true','nativeEventsDirectory':str(ROOT/'native-host/build')}
    values.update({name:str(paths().get(key)) for name,key in [('privateAssetsDirectory','privateAssets'),('meshDirectory','meshAssets'),('heroVoiceDirectory','heroVoiceAssets'),('heroVoiceFfmpeg','ffmpeg')]})
    command[1:1]=['-Dowmc.'+key+'='+value for key,value in values.items()]
    return command

def stop_lab():
    import stop_passthrough_session as stop
    stop.PROFILE=PROFILE
    original=stop.stop_supervisor
    def stop_owners():
        for process in psutil.process_iter(['exe','cmdline']):
            try:
                info=dict(process.info or {});executable=info.get('exe');args=info.get('cmdline') or []
                if process.pid==os.getpid() or not executable or Path(executable).name.lower()!='python.exe':continue
                interpreter=paths().get('python')
                if Path(executable).resolve()==interpreter and (interpreter.parent.parent/'pyvenv.cfg').is_file():continue
                matched=any((Path(a) if Path(a).is_absolute() else Path(process.cwd())/a).resolve()==Path(__file__).resolve() for a in args[1:] if not a.startswith('-'))
                if matched:process.terminate();process.wait(5)
            except (psutil.Error,OSError):continue
        original()
    stop.stop_supervisor=stop_owners
    return stop.stop_session()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stop',action='store_true');args=parser.parse_args()
    if args.stop:stop_lab();raise SystemExit(0)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
    handle=kernel.CreateMutexW(None,False,'Local\\OWMCPassthroughSessionLauncher')
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error()==183:raise SystemExit('An existing supervisor owns the session')
    session.PROFILE=PROFILE;session.prepare=prepare
    settings=json.loads((ROOT/'passthrough-settings.json').read_text(encoding='utf-8'));settings.update(worldName=WORLD,createWorld=True,twilightTrial=True)
    try:session.run(settings)
    except Exception as failure:
        result=dict(ready=False,error=str(failure),heartbeatMs=round(time.time()*1000),experimentalProfile=str(PROFILE))
        if not session.native_pids():result['desktopRestoration']=session.restore_display()
        session.write_status(result);raise
    finally:kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(handle)
