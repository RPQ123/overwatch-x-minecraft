"""Inspect original Dragonblade's charge gate; optional single bounded lab grant.

The grant changes one existing typed integer payload, never code, pointers,
input, callbacks or damage. Normal charge feedback is a separate feature.
"""
import argparse,ctypes,json,struct,time,math
from ctypes import wintypes
from observe_overwatch import ROOT,ResearchProcess
from observe_native_weapon_states import WeaponStates

ENTITY=0x0d80000000000004
CHARGE=0x0d80000000000156
COST=0x0d80000000000152

def numeric(raw):
    kind=struct.unpack_from('<I',raw,12)[0]
    if kind not in (2,3):raise ValueError('Ultimate primitive is not numeric')
    value=struct.unpack_from('<i' if kind==2 else '<f',raw)[0]
    if not math.isfinite(value):raise ValueError('Ultimate primitive is not finite')
    return value,kind

def inspect(process):
    r=WeaponStates(process);sample=r.sample_weapon()
    instance,graph,_=next(k for k in r.graph_cache if k[2]==0x0580000000000317)
    node=r.stu_list(graph+0x50)[11]
    button=r.pointer(r.bindings.field(node,0xa6a8d263)[1])
    if r.unpack('<I',button+16)[0]!=0x79:raise ValueError('Original ultimate button differs')
    # Reflection locates m_startCondition. The supplied expression layout and
    # opcode definitions prove charge >= cost, rather than naming a guessed 0.
    import zlib
    condition=r.pointer(r.bindings.field(node,zlib.crc32(b'm_startcondition'))[1])
    def data(address,stride):
        storage,flag=r.unpack('<QQ',address);a,b=r.unpack('<QQ',storage)
        items,count=(a,b) if flag==1 else (b,a)
        if not 0<=count<=256:raise ValueError('Ultimate expression list bounds')
        return process.read(items,count*stride) if count else b''
    if data(condition+0x20,1)!=bytes((31,0,31,1,142,0)):raise ValueError('Ultimate start expression changed')
    paths=[r.bindings.dynamic_path(v) for v, in struct.iter_unpack('<Q',data(condition+0x30,8))]
    if paths!=[[f'{ENTITY:016x}',f'{CHARGE:016x}'],[f'{ENTITY:016x}',f'{COST:016x}']]:raise ValueError('Ultimate charge paths changed')
    admin=r.pointer(process.base+0x17b7f90);model=r.entity(process.read(r.pointer(admin+0x10),65536),sample['modelId'])
    inner=r.component(model,0x23)+0xc0;bag=r.pointer(inner+0x2e0);values={}
    for bucket in range(16):
        for rid,value in struct.iter_unpack('<QQ',r.vector(bag+0xa0+bucket*0x30,16)):
            if rid not in (CHARGE,COST):continue
            if rid in values or r.pointer(value)!=process.base+0x1608248:raise ValueError('Ultimate primitive identity changed')
            number,kind=numeric(process.read(value+0xa0,16));values[rid]=(value,number,kind)
    if set(values)!={CHARGE,COST} or not 0<=values[CHARGE][1]<=values[COST][1]<=100000 or values[COST][1]<=0:raise ValueError('Ultimate numeric bounds')
    return r,{'localId':sample['localId'],'modelId':sample['modelId'],'script':instance,'chargeAddress':values[CHARGE][0]+0xa0,'charge':values[CHARGE][1],'chargeType':values[CHARGE][2],'cost':values[COST][1]}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--grant-for-test',action='store_true');args=parser.parse_args()
    process=ResearchProcess(args.pid);handle=None
    try:
        reader,result=inspect(process);result.update(pid=args.pid,readOnly=not args.grant_for_test,nativeCalls=False,labGrant=False)
        if args.grant_for_test:
            if result['charge']!=0:raise ValueError('Lab grant requires an empty meter; preserve existing charge')
            k=process.kernel;k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
            k.WriteProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.WriteProcessMemory.restype=wintypes.BOOL
            k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
            # The verified process handle remains open, preventing PID reuse.
            handle=k.OpenProcess(0x400|0x10|0x20|0x8,False,args.pid)
            if not handle:raise ctypes.WinError(ctypes.get_last_error())
            _,again=inspect(process)
            if any(again[key]!=result[key] for key in ('localId','modelId','script','chargeAddress','charge','chargeType','cost')):raise ValueError('Ultimate changed before grant')
            value=ctypes.c_int32(int(result['cost'])) if result['chargeType']==2 else ctypes.c_float(result['cost']);written=ctypes.c_size_t()
            if not k.WriteProcessMemory(handle,result['chargeAddress'],ctypes.byref(value),4,ctypes.byref(written)) or written.value!=4:raise ctypes.WinError(ctypes.get_last_error())
            result.update(labGrant=True,payloadBytesWritten=4,chargeAfter=numeric(process.read(result['chargeAddress'],16))[0])
        result['wallMs']=round(time.time()*1000)
        (ROOT/f'research/native-ultimate-binding-{args.pid}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result))
    finally:
        if handle:process.kernel.CloseHandle(handle)
        process.close()
