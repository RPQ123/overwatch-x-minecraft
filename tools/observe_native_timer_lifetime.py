"""Bounded read-only script identities for a future native timer crash.

Reads the already provided logger's map; never subscribes, hooks, calls native
functions, sends input or changes either game. Snapshots are not lossless events.
"""
import argparse
import ctypes
import json
import struct
import time
from pathlib import Path
from observe_overwatch import ROOT,ResearchProcess,PATCHED_SHA256
from provided_plugin_symbols import provided_plugin
from native_map_snapshot import snapshot_map
from native_crash_evidence import wait_native_crash_reports
from stop_passthrough import process_creation


def dump_registers(path):
    path=Path(path)
    if not 32<=path.stat().st_size<=16*1024*1024:raise ValueError('Small dump size bounds')
    with path.open('rb') as stream:data=stream.read(16*1024*1024+1)
    if len(data)>16*1024*1024:raise ValueError('Dump grew beyond the read bound')
    if data[:4]!=b'MDMP':raise ValueError('Not a minidump')
    count,directory=struct.unpack_from('<II',data,8)
    if not 1<=count<=128 or directory+count*12>len(data):raise ValueError('Dump stream bounds')
    matches=[]
    for i in range(count):
        kind,size,rva=struct.unpack_from('<III',data,directory+i*12)
        if kind==6:matches.append((size,rva))
    if len(matches)!=1:raise ValueError('Missing/ambiguous exception stream')
    size,rva=matches[0]
    if size<168 or rva+size>len(data):raise ValueError('Exception stream bounds')
    length,context=struct.unpack_from('<II',data,rva+160)
    if length<256 or context+length>len(data):raise ValueError('Dump context bounds')
    if not struct.unpack_from('<I',data,context+48)[0]&0x100000:raise ValueError('Not an AMD64 context')
    result={'exception':hex(struct.unpack_from('<I',data,rva+8)[0]),'thread':struct.unpack_from('<I',data,rva)[0]}
    for name,offset in (('rax',120),('rcx',128),('rsp',152),('rdi',176),('rip',248)):
        result[name]=struct.unpack_from('<Q',data,context+offset)[0]
    return result


class TimerIdentityReader:
    def __init__(self,process):
        self.process=process
        module,image,pdb=provided_plugin(process)
        self.logger=module+image.symbol_rva(pdb.exact('statescript_logger::s_scriptStates'))
    def sample(self):
        p=self.process;rows=[];failures=0;started=time.monotonic()
        pairs=snapshot_map(p,self.logger,'Q',4096)
        for address,_ in pairs:
            if time.monotonic()-started>.2:raise ValueError('Whole snapshot exceeded200ms')
            try:
                raw=p.read(address,0x170)
                vt,sync=struct.unpack_from('<Q',raw)[0],struct.unpack_from('<Q',raw,0x10)[0]
                rid,graph=struct.unpack_from('<Q',raw,0x150)[0],struct.unpack_from('<Q',raw,0x160)[0]
                if not p.base<=vt<p.base+0x1cd4000 or rid>>48!=0x580 or sync<0x10000 or graph<0x10000:raise ValueError('Script identity bounds')
                row={'address':address,'vtableRva':vt-p.base,'resource':f'{rid:016x}','graph':graph,
                     'instance':struct.unpack_from('<h',raw,0x18)[0],'sync':sync,'queueRoots':[]}
                # Parent/child direction is not inferred; capture only the two
                # measured instance roots, never walk a guessed native list.
                for at in (0xe8,0xf0):
                    node=struct.unpack_from('<Q',raw,at)[0]
                    if not node:continue
                    q={'slot':hex(at),'address':node}
                    try:
                        header=p.read(node,0x38);nvt=struct.unpack_from('<Q',header)[0]
                        q.update(type=header[0x22],vtable=nvt,raw=header.hex())
                        if header[0x22]==1:q.update(timerUserData=struct.unpack_from('<i',header,0x30)[0],stateIndex=struct.unpack_from('<h',header,0x34)[0])
                        q['stableHeader']=p.read(node,0x38)==header
                    except (OSError,ValueError) as e:q['readError']=str(e)
                    row['queueRoots'].append(q)
                try:
                    component=struct.unpack('<Q',p.read(sync+0x450,8))[0]
                    owner=struct.unpack('<Q',p.read(component+8,8))[0]
                    if p.read(component+0x10,1)==b'\x23':row.update(owner=owner,ownerId=struct.unpack('<I',p.read(owner+0x94,4))[0])
                except (OSError,ValueError):pass
                again=p.read(address,0x170)
                if any(raw[a:b]!=again[a:b] for a,b in ((0,8),(0x10,0x1c),(0x150,0x158),(0x160,0x168))):raise ValueError('Script identity changed')
                rows.append(row)
            except (OSError,ValueError):failures+=1
        return {'scripts':rows,'mapCount':len(pairs),'scriptReadFailures':failures,'readMs':round((time.monotonic()-started)*1000,3)}


def write_json(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=True,indent=2)+'\n',encoding='utf-8');temp.replace(path)


def main(args):
    output=(ROOT/args.output).resolve()
    if ROOT/'research' not in output.parents:raise ValueError('Use a private research folder')
    output.mkdir(parents=True,exist_ok=True)
    p=ResearchProcess(args.pid);creation=process_creation(p);created=creation/1e7-11644473600
    kernel=p.kernel;kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
    mutex=kernel.CreateMutexW(None,False,f'Local\\OWMCReadOnlyTimerObserver-{args.pid}-{creation}')
    if not mutex:p.close();raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error()==183:kernel.CloseHandle(mutex);p.close();raise ValueError('A reader already owns this process identity')
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    header={'pid':args.pid,'creation':creation,'exe':str(p.path),'sha256':PATCHED_SHA256,'processWrites':False,'nativeCalls':False,'input':False,'newHooks':False,'startedMs':round(time.time()*1000),'maximumSeconds':args.seconds,'intervalSeconds':1}
    write_json(output/'identity.json',header)
    samples=errors=timerRoots=0;history={};journal=None;segment=0;start=time.monotonic();last_index=0;last_error='';last_sample=0;reason='deadline';code=ctypes.c_ulong(259)
    try:
        reader=TimerIdentityReader(p)
        while time.monotonic()-start<args.seconds:
            tick=time.monotonic()
            if (output/'STOP').exists():reason='stop-file';break
            if not kernel.GetExitCodeProcess(p.handle,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
            if code.value!=259:reason='process-exit';break
            try:
                row=reader.sample();row['wallMs']=round(time.time()*1000);last_sample=row['wallMs'];samples+=1
                for script in row['scripts']:
                    key=str(script['address']);identity={k:v for k,v in script.items() if k!='queueRoots'}
                    versions=history.setdefault(key,[])
                    signature=(identity['resource'],identity['instance'],identity['graph'],identity['sync'],identity.get('owner'))
                    if not versions or tuple(versions[-1]['signature'])!=signature:
                        versions.append({'signature':signature,'firstMs':row['wallMs'],'lastMs':row['wallMs'],**identity})
                        del versions[:-4]
                    else:versions[-1]['lastMs']=row['wallMs']
                    timerRoots+=sum(q.get('type')==1 and q.get('stableHeader') is True for q in script['queueRoots'])
                if len(history)>8192:
                    oldest=sorted(history,key=lambda k:history[k][-1]['lastMs'])[:len(history)-8192]
                    for key in oldest:del history[key]
                if journal is None or journal.tell()>=8*1024*1024:
                    if journal:journal.close()
                    journal=(output/f'timer-{segment%4}.jsonl').open('w',encoding='utf-8');segment+=1
                journal.write(json.dumps(row,ensure_ascii=True,separators=(',',':'))+'\n');journal.flush()
                if time.monotonic()-last_index>=10:
                    write_json(output/'script-index.json',{'identity':header,'history':history});last_index=time.monotonic()
                write_json(output/'status.json',{'pid':args.pid,'running':True,'samples':samples,'errors':errors,'timerRootsObserved':timerRoots,'lastSampleMs':last_sample,'heartbeatMs':round(time.time()*1000),'lastReadMs':row['readMs'],'lastMapCount':row['mapCount'],'scriptReadFailures':row['scriptReadFailures'],'lastError':last_error})
            except (OSError,ValueError) as e:
                errors+=1;last_error=str(e)
                write_json(output/'status.json',{'pid':args.pid,'running':True,'samples':samples,'errors':errors,'lastSampleMs':last_sample,'heartbeatMs':round(time.time()*1000),'lastError':last_error})
            if args.once:reason='one-sample';break
            time.sleep(max(0,1-(time.monotonic()-tick)))
        final={'pid':args.pid,'running':False,'reason':reason,'samples':samples,'errors':errors,'timerRootsObserved':timerRoots,'exitCode':code.value,'lastError':last_error,'finishedMs':round(time.time()*1000)}
        if code.value!=259:
            final['crashReports']=wait_native_crash_reports(args.pid,created,p.path)
            for evidence in final['crashReports']:
                if 'minidump' not in evidence:continue
                try:
                    registers=dump_registers(evidence['minidump']);evidence['registers']=registers
                    # RDI is preserved by the measured f4f5b0 caller. These are
                    # time-stamped candidate identities, not proof of the writer.
                    evidence['rdiScriptCandidates']=history.get(str(registers['rdi']),[])
                except (OSError,ValueError,struct.error) as e:evidence['dumpReadError']=str(e)
        write_json(output/'script-index.json',{'identity':header,'history':history});write_json(output/'status.json',final)
        print(json.dumps(final,ensure_ascii=True))
    finally:
        if journal:journal.close()
        kernel.CloseHandle(mutex);p.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int,required=True);parser.add_argument('--output',required=True);parser.add_argument('--seconds',type=int,default=3600);parser.add_argument('--once',action='store_true');args=parser.parse_args()
    if not 1<=args.seconds<=7200:parser.error('Seconds must be1..7200')
    main(args)
