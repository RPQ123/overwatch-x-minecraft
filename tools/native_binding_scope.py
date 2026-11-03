"""Fresh read-only guest scope for low-latency, identity-checked rebinding."""
import ctypes,struct,time

class GuestScopeExpired(ValueError):
    """Valid nonfuture identity whose sample is too old; never usable state."""
    def __init__(self, scope, age):
        super().__init__('Guest body scope stale')
        self.scope = scope
        self.age = age

def decode_scope(data,pid,now):
    if len(data)!=256 or data[:8]!=b'OWBODY01':raise ValueError('Guest body scope format')
    u32=lambda n:struct.unpack_from('<I',data,n)[0]
    u64=lambda n:struct.unpack_from('<Q',data,n)[0]
    if (u32(8),u32(12),u32(16))!=(1,256,pid) or not u32(20):raise ValueError('Guest body scope process')
    if not u64(64) or u64(64)&1 or u64(72)>now:raise ValueError('Guest body scope stale')
    if not all(u64(n) for n in (24,32,136)):raise ValueError('Guest body scope identity')
    scope = dict(sourcePid=u32(20),guestGeneration=u64(24),hostGeneration=u64(32),worldId=u64(136),sequence=u64(64))
    if now-u64(72)>250:raise GuestScopeExpired(scope, now-u64(72))
    return scope

class GuestBindingScope:
    def __init__(self):self.kernel=None;self.handle=None;self.view=None
    def close(self):
        if self.view:self.kernel.UnmapViewOfFile(self.view)
        if self.handle:self.kernel.CloseHandle(self.handle)
        self.handle=self.view=None
    def read(self,pid):
        if self.view is None:
            k=self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            k.OpenFileMappingW.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_wchar_p];k.OpenFileMappingW.restype=ctypes.c_void_p
            k.MapViewOfFile.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_size_t];k.MapViewOfFile.restype=ctypes.c_void_p
            k.UnmapViewOfFile.argtypes=[ctypes.c_void_p];k.CloseHandle.argtypes=[ctypes.c_void_p]
            self.handle=k.OpenFileMappingW(4,False,'Local\\OWMCPassthroughFrame')
            if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
            self.view=k.MapViewOfFile(self.handle,4,0,0,4096)
            if not self.view:self.close();raise ctypes.WinError(ctypes.get_last_error())
        for _ in range(3):
            start=ctypes.string_at(self.view+1536+64,8);data=ctypes.string_at(self.view+1536,256)
            if start==data[64:72]==ctypes.string_at(self.view+1536+64,8):return decode_scope(data,pid,round(time.time()*1000))
        raise ValueError('Guest scope changed during read')

def current_body(body,emission,scope,pid):
    if body.get('pid')!=pid or emission.get('pid')!=pid or not emission.get('enabled') or emission.get('failures'):raise ValueError('Current native binding provenance differs')
    if not body.get('worldStable'):raise ValueError('Waiting for stable guest dimension')
    if any(body.get(k)!=scope[k] for k in ('sourcePid','guestGeneration','hostGeneration','worldId')):raise ValueError('Waiting for native body to acknowledge current guest scope')
    if emission.get('hostGeneration')!=scope['hostGeneration']:raise ValueError('Emission owner has another host session')
    hero,model=emission.get('hero'),emission.get('modelId')
    if not hero or not model:raise ValueError('Waiting for actual native hero')
    # The observer checks the actual local entity every20ms. Body JSON is a
    # one-second diagnostic; never use its old model to prepare a departed hero.
    return {**body,'hero':hero,'modelId':model}
