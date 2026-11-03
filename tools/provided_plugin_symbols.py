"""Resolve symbols from the user's provided plugin only after PE/PDB identity match.

No native calls or process writes. No game code or symbols are downloaded.
"""
from modpack.config import paths
import ctypes,math,struct
from functools import lru_cache
from pathlib import Path
from observe_overwatch import ROOT

class PeImage:
    def __init__(self,path,data=None):
        self.path=Path(path);self.data=self.path.read_bytes() if data is None else data;d=self.data
        if d[:2]!=b'MZ':raise ValueError('Not a PE image')
        pe=struct.unpack_from('<I',d,0x3c)[0]
        if d[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',d,pe+4)[0]!=0x8664:raise ValueError('Expected x64 PE')
        self.timestamp=struct.unpack_from('<I',d,pe+8)[0];self.image_size=struct.unpack_from('<I',d,pe+24+56)[0]
        opts=struct.unpack_from('<H',d,pe+20)[0];self.sections=[]
        for i in range(struct.unpack_from('<H',d,pe+6)[0]):
            at=pe+24+opts+i*40;vs,va,size,raw=struct.unpack_from('<4I',d,at+8);flags=struct.unpack_from('<I',d,at+36)[0]
            self.sections.append((va,vs,raw,size,flags))
        dr,ds=struct.unpack_from('<II',d,pe+24+112+6*8);self.identity=None
        if ds>4096 or ds%28:raise ValueError('Debug directory bounds')
        for offset in range(0,ds,28):
            typ,size,rva,raw=struct.unpack_from('<4I',d,self.file_offset(dr)+offset+12)
            if typ==2 and size>=24 and d[raw:raw+4]==b'RSDS':self.identity=(d[raw+4:raw+20],struct.unpack_from('<I',d,raw+20)[0])
        if self.identity is None:raise ValueError('No CodeView identity')
    def file_offset(self,rva):
        for va,vs,raw,size,_ in self.sections:
            if va<=rva<va+size:return raw+rva-va
        raise ValueError('RVA outside file-backed sections')
    def symbol_rva(self,location):
        section,offset=location
        if not 1<=section<=len(self.sections):raise ValueError('Symbol section')
        va,vs,_,_,flags=self.sections[section-1]
        if offset>=vs:raise ValueError('Symbol offset')
        return va+offset
    def function_prefix(self,location,size=32):
        rva=self.symbol_rva(location)
        va,vs,raw,length,flags=self.sections[location[0]-1]
        if not flags&0x20000000 or location[1]+size>min(vs,length):raise ValueError('Function is not executable and file-backed')
        prefix=self.data[raw+location[1]:raw+location[1]+size]
        if len(prefix)!=size:raise ValueError('Truncated function prefix')
        return rva,prefix

class PdbSymbols:
    def __init__(self,path,data=None):
        data=Path(path).read_bytes() if data is None else data
        if not data.startswith(b'Microsoft C/C++ MSF 7.00'):raise ValueError('Expected MSF7 PDB')
        bs,_,blocks,ds,_,bm=struct.unpack_from('<6I',data,32)
        if bs not in (512,1024,2048,4096,8192) or ds>64*1024*1024:raise ValueError('PDB directory bounds')
        def pages(ids,size):
            if any(i>=blocks or (i+1)*bs>len(data) for i in ids):raise ValueError('PDB page bounds')
            return b''.join(data[i*bs:(i+1)*bs] for i in ids)[:size]
        ids=struct.unpack_from('<'+str(math.ceil(ds/bs))+'I',data,bm*bs);directory=pages(ids,ds)
        count=struct.unpack_from('<I',directory)[0]
        if count>65536:raise ValueError('PDB stream count')
        sizes=struct.unpack_from('<'+str(count)+'I',directory,4);at=4+count*4;streams=[]
        for size in sizes:
            n=0 if size==0xffffffff else math.ceil(size/bs)
            ids=struct.unpack_from('<'+str(n)+'I',directory,at);at+=n*4;streams.append(pages(ids,size))
        self.identity=(streams[1][12:28],struct.unpack_from('<I',streams[1],8)[0]);self.symbols={}
        records=streams[struct.unpack_from('<H',streams[3],20)[0]];at=0
        while at+4<=len(records):
            size,kind=struct.unpack_from('<HH',records,at)
            if size<2 or at+size+2>len(records):raise ValueError('PDB symbol record bounds')
            if kind in (0x110c,0x110d,0x110e):
                _,offset,section=struct.unpack_from('<IIH',records,at+4)
                name=records[at+14:at+size+2].split(b'\0')[0].decode('utf-8',errors='replace')
                self.symbols.setdefault(name,set()).add((section,offset))
            at+=size+2
    def exact(self,name):
        if name not in self.symbols:raise ValueError('Required original plugin symbol missing')
        matches=self.symbols[name]
        if len(matches)!=1:raise ValueError('Required original plugin symbol is ambiguous')
        return next(iter(matches))

@lru_cache(maxsize=2)
def _metadata(image_path,pdb_path,image_bytes,pdb_bytes):
    # Cache exact immutable CONTENT, not timestamps/guessed addresses. Symbol
    # parsing used to repeat for every channel and delayed a cold skill bind.
    image=PeImage(image_path,image_bytes);pdb=PdbSymbols(pdb_path,pdb_bytes)
    if image.identity!=pdb.identity:raise ValueError('Provided plugin PE/PDB GUID or age mismatch')
    return image,pdb

def provided_plugin(process):
    base=paths().get('owExecutable').parent
    image_path=base/'inject.dll';pdb_path=base/'prometheus.pdb'
    image,pdb=_metadata(str(image_path.resolve()),str(pdb_path.resolve()),image_path.read_bytes(),pdb_path.read_bytes())
    k=process.kernel;k.K32GetModuleFileNameExW.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32]
    modules=(ctypes.c_void_p*512)();needed=ctypes.c_uint32()
    if not k.K32EnumProcessModulesEx(process.handle,modules,ctypes.sizeof(modules),ctypes.byref(needed),2) or needed.value>ctypes.sizeof(modules):raise ValueError('Module enumeration failed')
    found=[]
    for module in list(modules)[:needed.value//8]:
        path=ctypes.create_unicode_buffer(32768)
        if not k.K32GetModuleFileNameExW(process.handle,module,path,32768):raise ValueError('Module path unavailable')
        # Resolving hundreds of unrelated Windows DLL paths touched the file
        # system on every channel bind. Only the supplied plugin's filename can
        # be a match; its absolute resolved path and uniqueness still must pass.
        if Path(path.value).name.casefold()!=image.path.name.casefold():continue
        if Path(path.value).resolve()==image.path.resolve():found.append(module)
    if len(found)!=1:raise ValueError('Provided original plugin not uniquely loaded from its workspace path')
    return found[0],image,pdb
