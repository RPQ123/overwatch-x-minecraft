"""Guarded temporary Kyoto native sun diagnostics; no camera/input/gameplay writes."""
import ctypes,struct,math,time,json,hashlib
from functools import lru_cache
from pathlib import Path
from ctypes import wintypes as w
from contextlib import contextmanager
from native_bootstrap_maps import read_loaded_map,MAPS
from observe_overwatch import PoseReader

@lru_cache(maxsize=4)
def _owned_symbol(dll,expected_hash):
    """Read the current private build's COFF symbol; no code or data changes."""
    data=Path(dll).read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected_hash:raise ValueError('Loaded compositor file hash changed')
    pe=struct.unpack_from('<I',data,0x3c)[0];symbols,count=struct.unpack_from('<II',data,pe+12)
    sections=pe+24+struct.unpack_from('<H',data,pe+20)[0];section_count=struct.unpack_from('<H',data,pe+6)[0]
    if not symbols or not 0<count<1000000 or symbols+18*count+4>len(data):raise ValueError('Private compositor symbols unavailable')
    strings=symbols+18*count;i=0;found=[]
    while i<count:
        at=symbols+i*18;name=data[at:at+8]
        if name[:4]==bytes(4):
            start=strings+struct.unpack_from('<I',name,4)[0]
            if not strings<=start<len(data):raise ValueError('Private symbol bounds')
            name=data[start:data.index(0,start)]
        else:name=name.rstrip(bytes(1))
        if name==b'_ZN12_GLOBAL__N_1L15nativeViewLightE':
            value,section=struct.unpack_from('<Ih',data,at+8)
            if not 1<=section<=section_count:raise ValueError('Private light symbol section')
            found.append(value+struct.unpack_from('<I',data,sections+(section-1)*40+12)[0])
        i+=1+data[at+17]
    if len(found)!=1:raise ValueError('Private light owner symbol is absent or ambiguous')
    return found[0]

def owned_live_light(process,pid):
    """Read the actual calibrated owner's bound light outside CPU recording."""
    from observe_overwatch import ROOT
    from stop_passthrough import read_report
    status=read_report(ROOT/'research/session-status.json');live=read_report(ROOT/f'native-host/build/world-live-{pid}.json')
    version=live.get('probeVersion')
    if status.get('nativePid')!=pid or version not in (30,31,32,33,34,35,36,37,38,39,40) or not live.get('enabled') or not live.get('viewLightOwned'):raise ValueError('No current calibrated light owner')
    name=f'owmc-live-passthrough-v{version}.dll';dll=ROOT/'native-host/build'/name
    expected=status['loadedFiles']['native-host\\build\\'+name];rva=_owned_symbol(str(dll),expected)
    modules=(ctypes.c_void_p*512)();needed=w.DWORD();k=process.kernel
    if not k.K32EnumProcessModulesEx(process.handle,modules,ctypes.sizeof(modules),ctypes.byref(needed),2) or needed.value>ctypes.sizeof(modules):raise ValueError('Native modules changed')
    k.K32GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD];k.K32GetModuleFileNameExW.restype=w.DWORD
    found=[]
    for module in modules[:needed.value//ctypes.sizeof(ctypes.c_void_p)]:
        path=ctypes.create_unicode_buffer(32768)
        if k.K32GetModuleFileNameExW(process.handle,module,path,len(path)) and Path(path.value).resolve()==dll.resolve():found.append(module)
    if len(found)!=1:raise ValueError('Current compositor mapping differs')
    address=struct.unpack('<Q',process.read(found[0]+rva,8))[0]
    result=locate_live(process,address,allow_hollywood=version>=31)
    if version>=31 and read_loaded_map(process)['mapId']!=live.get('viewLightMapId'):raise ValueError('Native light map owner differs')
    return result

def locate(process,*,allow_hollywood=False):
    loaded=read_loaded_map(process);guid=loaded['mapId'];r=PoseReader(process)
    accepted=(MAPS['kyoto-login'],MAPS['hollywood']) if allow_hollywood else (MAPS['kyoto-login'],)
    if loaded['state']!=8 or guid not in accepted:raise ValueError('Verified Kyoto/Hollywood native map required')
    buckets=r.pointer(process.base+0x18a19a8);count=r.unpack('<I',process.base+0x18a19b8)[0]
    if not 16<=count<=1048576 or count&(count-1):raise ValueError('Native resource-cache bounds')
    h=0x811c9dc5
    for byte in struct.pack('<Q',guid):h=((h^byte)*0x1000193)&0xffffffffffffffff
    node=r.unpack('<Q',buckets+(h&(count-1))*8)[0];seen=set()
    while node:
        if node in seen or len(seen)>=128:raise ValueError('Native resource-cache chain changed')
        seen.add(node);data,key,next_node=r.unpack('<Q8xQQ',node)
        if key==guid:
            direction=r.unpack('<3f',data+0x14c);color=r.unpack('<3f',data+0x158)
            if not all(math.isfinite(x) for x in (*direction,*color)) or abs(sum(x*x for x in direction)-1)>.001 or any(not 0<=x<=8 for x in color):raise ValueError('Kyoto native sun layout/bounds differ')
            return {'node':node,'data':data,'direction':direction,'color':color}
        node=next_node
    raise ValueError('Kyoto resource is not in the current native cache')

def checked_vector(value,direction=False):
    if len(value)!=3 or not all(math.isfinite(x) for x in value):raise ValueError('Sun vector must contain three finite values')
    if direction:
        if abs(sum(x*x for x in value)-1)>.001:raise ValueError('Sun direction must be normalized')
    elif any(not 0<=x<=8 for x in value):raise ValueError('Sun color outside calibrated bounds')
    return struct.pack('<3f',*value)

def locate_live(process,address=None,*,allow_hollywood=False):
    """Verified render-frame path, or an explicit private calibration address."""
    original=locate(process,allow_hollywood=allow_hollywood);r=PoseReader(process)
    if address is None:
        engine=r.pointer(process.base+0x181e3e0)
        if r.pointer(engine)!=process.base+0x1589e58:raise ValueError('Native engine class differs')
        deadline=time.monotonic()+1.5
        while True:
            found=set()
            try:
                matrices=r.pointer(engine+0x78);packet=process.read(matrices-0x13f00,0x800)
                for i in range(48,len(packet)-7,8):
                    direction=struct.unpack_from('<3f',packet,i-48);candidate=struct.unpack_from('<Q',packet,i)[0]
                    if not all(math.isfinite(x) for x in direction) or abs(sum(x*x for x in direction)-1)>.001 or not 0x10000<=candidate<0x7fffffffffff or candidate&15:continue
                    try:table=r.unpack('<Q',candidate)[0]
                    except OSError:continue
                    if table==process.base+0x158adb8:found.add(candidate)
            except (OSError,ValueError):pass
            if len(found)==1:address=found.pop();break
            if len(found)>1 or time.monotonic()>=deadline:raise ValueError('Current native frame sun binding is absent or ambiguous')
            time.sleep(.002)
    if address&15 or r.pointer(address)!=process.base+0x158adb8:
        raise ValueError('Calibrated native environment object differs')
    color=r.unpack('<3f',address+0x28);direction=r.unpack('<3f',address+0x40)
    checked_vector(color);checked_vector(direction,True)
    # This class is the live environment, not the cached map header. Its second
    # RGB triplet is checked but deliberately not modified by this diagnostic.
    secondary=r.unpack('<3f',address+0x34);checked_vector(secondary)
    return {'node':address,'data':address,'direction':direction,'color':color,
            'secondary':secondary,'mapData':original['data']}

@contextmanager
def temporary_light(process,pid,*,color=None,direction=None,live_object=None,irradiance=None,allow_hollywood=False):
    locator=(lambda p:locate_live(p,live_object,allow_hollywood=allow_hollywood)) if live_object is not None else (lambda p:locate(p,allow_hollywood=allow_hollywood)) if allow_hollywood else locate
    offsets=(0x40,0x28) if live_object is not None else (0x14c,0x158)
    changes=[]
    for offset,value,is_direction in [(offsets[0],direction,True),(offsets[1],color,False)]:
        if value is not None:changes.append((offset,checked_vector(value,is_direction)))
    if irradiance is not None:
        if live_object is None:raise ValueError('Derived RGB requires the calibrated live environment object')
        changes.append((0x34,checked_vector(irradiance)))
    if not changes:raise ValueError('No light diagnostic requested')
    binding=locator(process);k=process.kernel
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.GetProcessId.argtypes=[w.HANDLE];k.GetProcessId.restype=w.DWORD
    k.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=w.BOOL
    k.WriteProcessMemory.argtypes=[w.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=w.BOOL
    k.CloseHandle.argtypes=[w.HANDLE]
    def creation(handle):
        times=[ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        return times[0].value
    def write(address,value):
        data=ctypes.create_string_buffer(value);written=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,address,data,len(value),ctypes.byref(written)) or written.value!=len(value):raise ctypes.WinError(ctypes.get_last_error())
        if process.read(address,len(value))!=value:raise ValueError('Sun write readback differs')
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    applied=[]
    try:
        if k.GetProcessId(process.handle)!=pid or creation(handle)!=creation(process.handle):raise ValueError('Native process creation changed')
        if locator(process)!=binding:raise ValueError('Native light binding changed')
        for offset,after in changes:
            address=binding['data']+offset;before=process.read(address,12);applied.append((address,before,after));write(address,after)
        yield binding
    finally:
        try:
            if applied:
                current=locator(process)
                if (current['node'],current['data'])!=(binding['node'],binding['data']):raise ValueError('Native map changed; do not restore a departed resource')
                for address,before,after in reversed(applied):
                    value=process.read(address,12)
                    if value==before:continue
                    if value!=after:raise ValueError('Native light changed externally; restoration requires inspection')
                    write(address,before)
        finally:k.CloseHandle(handle)
