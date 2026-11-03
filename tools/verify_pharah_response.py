"""Real Pharah Space latency, native fuel/jet and primary visual evidence in a clone."""
import argparse,ctypes,json,struct,subprocess,time
from ctypes import wintypes as w
from calibrate_hero_roster import api,drive,report,ROOT
from calibrate_hero_actions import select
from verify_world_hero_switch import ready
from verify_genji_elimination_reset import post
from observe_overwatch import ResearchProcess
from observe_native_weapon_states import WeaponStates
from inspect_pharah_abilities import snapshot
from native_hover_response import inspect as hover_delay

def pulse(address,reader,mover,commands,seconds):
    cmd=subprocess.Popen(['um','win','drive','--proc','GameClientApp.patched.exe','focus',*commands],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    start=time.monotonic();rows=[]
    while cmd.poll() is None or time.monotonic()-start<seconds:
        if time.monotonic()-start>12:raise ValueError('Input deadline')
        raw=ctypes.string_at(address,4096);p=api('health')['player'];c=api('combat');rows.append({'t':time.monotonic()-start,'bits':struct.unpack_from('<I',raw,324)[0],'p':p,'flight':c['flight'],'velocity':reader.unpack('<3f',mover+0x7e0+0x230)})
        time.sleep(.012)
    stdout,stderr=cmd.communicate(timeout=1)
    if cmd.returncode or b'-> fail' in stdout:raise ValueError((stdout+stderr).decode(errors='replace'))
    return rows

def metrics(rows):
    first=next(v for v in rows if v['bits']&16);floor=first['p']['feetY'];started=first['t']
    moved=next(v for v in rows if v['p']['feetY']>floor+.002)
    return {'riseDelayMs':(moved['t']-started)*1000,'rise':max(v['p']['feetY'] for v in rows)-floor,'maxSpeed':max(v['flight'].get('appliedVerticalSpeed',0) for v in rows),'creativeFlight':any(v['p']['flying'] for v in rows)}

def main(output=None):
    folder=(ROOT/output).resolve() if output else ROOT/'research'
    if ROOT/'research'!=folder and ROOT/'research' not in folder.parents:raise ValueError('Private research output required')
    folder.mkdir(parents=True,exist_ok=True)
    assert api('health')['worldName'].startswith('Overwatch Twilight Switch ')
    pid=report(ROOT/'research/session-status.json')['nativePid'];out={'pid':pid,'passed':False};process=None;address=None;handle=None
    k=ctypes.windll.kernel32;k.OpenFileMappingW.argtypes=[w.DWORD,w.BOOL,w.LPCWSTR];k.OpenFileMappingW.restype=w.HANDLE;k.MapViewOfFile.argtypes=[w.HANDLE,w.DWORD,w.DWORD,w.DWORD,ctypes.c_size_t];k.MapViewOfFile.restype=ctypes.c_void_p
    try:
        select(pid,'Pharah');ready(pid);process=ResearchProcess(pid);out['nativeDelay']=hover_delay(process);assert out['nativeDelay']['delay']==0
        reader=WeaponStates(process);s=reader.sample_weapon(False,True);admin=reader.pointer(process.base+0x17b7f90);table=process.read(reader.pointer(admin+16),65536);mover=reader.component(reader.entity(table,s['modelId']),0x15)
        handle=k.OpenFileMappingW(4,False,'Local\\OWMCHostPose');address=k.MapViewOfFile(handle,4,0,0,4096)
        if not address:raise ValueError('Actual host input mapping unavailable')
        post('flight-open');time.sleep(.5);out['fixture']=api('combat');assert not out['fixture']['testError']
        if api('health')['player']['flying']:drive('focus','key 0x75','sleep 650')
        assert api('health')['player']['onGround'] and not api('health')['player']['flying']
        out['fuelBefore']=snapshot(process);out['pulses']=[]
        for duration in [1200,700,700]:
            rows=pulse(address,reader,mover,['sleep 300',f'hold 0x20 {duration}','sleep 2300'],3.8)
            result=metrics(rows);out['pulses'].append({'rows':rows,'metrics':result});print(json.dumps(result),flush=True)
            assert result['riseDelayMs']<160 and result['rise']>.6 and not result['creativeFlight']
            assert 7.5<result['maxSpeed']<=8.01,'requested faster hover speed missing or overshooting'
        out['fuelAfter']=snapshot(process)
        c=api('combat');drive('focus',f'rel 0 {round(-c["pitch"]/.1)}','sleep 200')
        out['beforeFire']=api('combat')
        rec=subprocess.Popen(['um','win','record','--pid',str(pid),'--exe','GameClientApp.patched.exe','--out',str(folder/'pharah-primary-after'),'--seconds','7','--fps','60'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:drive('focus','sleep 1000','mdown 1280 720','sleep 130','mup','sleep 1200','mdown 1280 720','sleep 130','mup','sleep 1200','mdown 1280 720','sleep 130','mup','sleep 900')
        finally:a,b=rec.communicate(timeout=15);out['recordingExit']=rec.returncode
        out['afterFire']=api('combat');out['nativeReport']=report(ROOT/f'native-host/build/native-emissions-{pid}.json')
        out['flashCount']=out['afterFire']['muzzleFlashesShown']-out['beforeFire']['muzzleFlashesShown']
        out['shotCount']=out['afterFire']['admitted']-out['beforeFire']['admitted'];assert out['flashCount']==out['shotCount']==3
        post('replay');time.sleep(.3);out['replay']=api('combat');assert out['replay']['muzzleFlashesShown']==out['afterFire']['muzzleFlashesShown'] and not out['afterFire']['pharahVisualError']
        out['passed']=True
    except Exception as failure:out['error']=str(failure)
    finally:
        if process:process.close()
        if address:k.UnmapViewOfFile.argtypes=[ctypes.c_void_p];k.UnmapViewOfFile(address)
        if handle:k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle(handle)
        try:
            drive('focus','key 0x20 up','mup')
            if not api('health')['player']['flying']:drive('focus','key 0x75','sleep 200')
        except Exception as failure:out['inputCleanupError']=str(failure)
        try:post('cleanup');time.sleep(.3);out['cleaned']=api('combat')['wallBlocks']==0
        except Exception as failure:out['cleaned']=False;out['cleanupError']=str(failure)
        (folder/'pharah-response-after.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':out['passed'],'cleaned':out.get('cleaned'),'shots':out.get('shotCount'),'flashes':out.get('flashCount')}),flush=True)
    if not out['passed'] or not out.get('cleaned'):raise ValueError(out.get('error',out.get('cleanupError','Pharah regression failed')))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output');main(parser.parse_args().output)
