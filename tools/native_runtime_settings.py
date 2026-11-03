"""Read beta INI metadata and run bounded, automatically restored render experiments."""
import ctypes,struct
from contextlib import contextmanager
from observe_overwatch import PoseReader

def settings(process):
    r=PoseReader(process)
    def string(address):
        data=process.read(address,32);pointer,_,size,capacity=struct.unpack_from('<QQii',data)
        if not 0<=size<=capacity<=8192:raise ValueError('Native setting string bounds')
        return (process.read(pointer,size) if capacity>16 else data[:size]).rstrip(b'\0').decode('utf-8',errors='strict')
    array,count,capacity=r.unpack('<Qii',process.base+0x1859ed0)
    if not 0<count<=capacity<=10000:raise ValueError('Native setting registry bounds')
    result={}
    for address, in struct.iter_unpack('<Q',process.read(array,count*8)):
        name=string(address+8)
        if name in result:raise ValueError('Duplicate setting name')
        result[name]={'entry':address,'name':name,'type':r.unpack('<i',address+104)[0],'address':r.pointer(address+144)}
    return result

def render_wait(process,pid,value):
    setting=settings(process)['app.WaitForRenderFrame'];address=setting['address']
    if setting['type']!=1 or value not in (0,1):raise ValueError('Native render wait setting type')
    before=process.read(address,1)
    if before not in (b'\0',b'\1'):raise ValueError('Native render wait boolean payload')
    k=process.kernel;k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
    k.WriteProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=ctypes.c_int
    k.CloseHandle.argtypes=[ctypes.c_void_p];handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        if settings(process)['app.WaitForRenderFrame']!=setting or process.read(address,1)!=before:raise ValueError('Native render wait changed')
        out=ctypes.c_ubyte(value);written=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,address,ctypes.byref(out),1,ctypes.byref(written)) or written.value!=1:raise ctypes.WinError(ctypes.get_last_error())
        if process.read(address,1)!=bytes([value]):raise ValueError('Native render wait readback')
        return before[0]
    finally:k.CloseHandle(handle)


@contextmanager
def temporary_render_settings(process, pid, values):
    """Measured quality/client cap settings; restore every experimental value."""
    limits={'Render.AADetail':(2,0,3),'Render.LocalFogDetail':(2,1,3),
            'Render.DynamicAmbient':(1,0,1),'Render.SinglePointAmbient':(1,0,1),
            'Render.LocalReflections':(1,0,1),
            'Render.FogEnabled':(1,0,1),'Render.ComputeFogEnabled':(1,0,1),
            'Render.DirectionalShadowDetail':(2,0,3),'client.MaxFPS':(3,0,1000)}
    if not values or values.keys()-limits.keys() or any(type(v) is not int or not limits[k][1]<=v<=limits[k][2] for k,v in values.items()):
        raise ValueError('Unsupported render quality experiment')
    registry=settings(process); changes=[]
    for name,value in values.items():
        item=registry[name]
        kind,minimum,maximum=limits[name]
        if item['type']!=kind:raise ValueError('Native quality setting type differs')
        fmt='<B' if kind==1 else '<i'
        before=process.read(item['address'],struct.calcsize(fmt))
        if not minimum<=struct.unpack(fmt,before)[0]<=maximum:raise ValueError('Native quality value differs')
        changes.append((name,item,before,struct.pack(fmt,value)))
    k=process.kernel
    k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
    k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_uint64)]*4;k.GetProcessTimes.restype=ctypes.c_int
    k.GetProcessId.argtypes=[ctypes.c_void_p];k.GetProcessId.restype=ctypes.c_uint32
    k.WriteProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=ctypes.c_int
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    applied=[]
    def created(h):
        times=[ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        return times[0].value
    def write(address,data):
        buffer=ctypes.create_string_buffer(data);written=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,address,buffer,len(data),ctypes.byref(written)) or written.value!=len(data):raise ctypes.WinError(ctypes.get_last_error())
        if process.read(address,len(data))!=data:raise ValueError('Native quality write readback differs')
    try:
        if k.GetProcessId(process.handle)!=pid or created(handle)!=created(process.handle):raise ValueError('Native process identity changed')
        for change in changes:
            name,item,before,after=change
            if settings(process)[name]!=item or process.read(item['address'],len(before))!=before:raise ValueError('Native quality setting changed')
            applied.append(change)
            write(item['address'],after)
        yield {name:struct.unpack('<B' if len(before)==1 else '<i',before)[0] for name,_,before,_ in changes}
    finally:
        try:
            for name,item,before,after in reversed(applied):
                if settings(process)[name]!=item:raise ValueError('Quality metadata changed; restoration requires inspection')
                current=process.read(item['address'],len(before))
                if current==before:continue
                if current!=after:raise ValueError('Quality changed externally; restoration requires inspection')
                write(item['address'],before)
        finally:k.CloseHandle(handle)


# Startup profiles are applied to the verified offline research client only.
# They live in the client process and disappear when that process exits; the
# original installation/configuration is never rewritten.
RENDER_PROFILES={
    'low':{
        'Render.AADetail':0,
        'Render.LocalFogDetail':1,
        'Render.DirectionalShadowDetail':0,
        # Keep the neutral material-lighting pair used by Medium; only geometry,
        # fog and shadow stay reduced so metallic viewmodels retain contrast.
        'Render.DynamicAmbient':1,
        'Render.SinglePointAmbient':0,
    },
    'medium':{
        'Render.AADetail':1,
        'Render.LocalFogDetail':2,
        'Render.DirectionalShadowDetail':1,
        'Render.DynamicAmbient':1,
        'Render.SinglePointAmbient':0,
    },
}


def apply_render_profile(process, pid, name):
    """Apply one bounded OW video profile and verify every write.

    This is intentionally a one-way startup operation.  The process is the
    exact SHA-guarded offline research build, and the values are restored by
    the game's own process lifetime when the session is stopped.
    """
    if name not in RENDER_PROFILES:
        raise ValueError('Unknown native render profile: '+str(name))
    limits={'Render.AADetail':(2,0,3),'Render.LocalFogDetail':(2,1,3),
            'Render.DynamicAmbient':(1,0,1),'Render.SinglePointAmbient':(1,0,1),
            'Render.DirectionalShadowDetail':(2,0,3)}
    registry=settings(process);changes=[]
    for setting_name,value in RENDER_PROFILES[name].items():
        item=registry.get(setting_name)
        if not item:raise ValueError('Native quality setting is missing: '+setting_name)
        kind,minimum,maximum=limits[setting_name]
        if item['type']!=kind:raise ValueError('Native quality setting type differs: '+setting_name)
        if not minimum<=value<=maximum:raise ValueError('Native quality profile value is out of bounds: '+setting_name)
        fmt='<B' if kind==1 else '<i';before=process.read(item['address'],struct.calcsize(fmt))
        current=struct.unpack(fmt,before)[0]
        if not minimum<=current<=maximum:raise ValueError('Native quality value differs: '+setting_name)
        changes.append((setting_name,item,before,struct.pack(fmt,value),current))
    k=process.kernel
    k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
    k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_uint64)]*4;k.GetProcessTimes.restype=ctypes.c_int
    k.GetProcessId.argtypes=[ctypes.c_void_p];k.GetProcessId.restype=ctypes.c_uint32
    k.WriteProcessMemory.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=ctypes.c_int
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=k.OpenProcess(0x428,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    def created(h):
        times=[ctypes.c_uint64() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        return times[0].value
    def write(address,data):
        buffer=ctypes.create_string_buffer(data);written=ctypes.c_size_t()
        if not k.WriteProcessMemory(handle,address,buffer,len(data),ctypes.byref(written)) or written.value!=len(data):raise ctypes.WinError(ctypes.get_last_error())
        if process.read(address,len(data))!=data:raise ValueError('Native quality write readback differs')
    applied=[]
    try:
        if k.GetProcessId(process.handle)!=pid or created(handle)!=created(process.handle):raise ValueError('Native process identity changed')
        for setting_name,item,before,after,current in changes:
            if settings(process).get(setting_name)!=item or process.read(item['address'],len(before))!=before:
                raise ValueError('Native quality setting changed: '+setting_name)
            write(item['address'],after);applied.append(setting_name)
        return {'profile':name,'before':{n:current for n,_,_,_,current in changes},
                'applied':{n:value for n,value in RENDER_PROFILES[name].items()}}
    finally:
        k.CloseHandle(handle)
