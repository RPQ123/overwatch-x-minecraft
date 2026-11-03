"""Build a one-shot request from matched provided-plugin symbols; never calls game code."""
import struct
from observe_overwatch import ROOT,PoseReader
from provided_plugin_symbols import provided_plugin

def prepare(process,pid,creation,empty_scene=False):
    base,image,pdb=provided_plugin(process)
    rva,prefix=image.function_prefix(pdb.exact('?spawn@player_spawner@@QEAA?AU?$pair@PEAUEntity@@PEAU1@@std@@XZ'))
    if process.read(base+rva,32)!=prefix:raise ValueError('Provided plugin function differs in memory')
    reader=PoseReader(process);ea=reader.pointer(process.base+0x17b7f90)
    if reader.unpack('<I',ea+0x220)[0]:raise ValueError('A local controller already exists; never spawn another')
    systems,count,capacity=reader.unpack('<Qii',ea+0xd8)
    if not 1<=count<=capacity<=128:raise ValueError('Native system list bounds')
    worlds=[]
    for system, in struct.iter_unpack('<Q',process.read(systems,count*8)):
        if reader.pointer(system)==process.base+0x15c3118:
            if reader.pointer(system+8)!=ea or reader.unpack('<B',system+0x10)[0]!=8:raise ValueError('Native world not ready')
            worlds.append(reader.unpack('<Q',system+0x20)[0])
    if len(worlds)!=1 or (not worlds[0] and not empty_scene):raise ValueError('Expected one ready native world')
    if empty_scene:
        import json
        record=json.loads((ROOT/f'research/native-empty-scene-{pid}.json').read_text(encoding='utf-8'))
        if worlds[0] or record['pid']!=pid or record['wantedLoaded']!=[0,0] or record['worldState']!=8:raise ValueError('No matching cold zero-map scene record')
    data=struct.pack('<8sIIIIQIIII16sIIQQQ32sQQ',b'OWSPWN01',1,144,pid,0,base,rva,image.image_size,image.timestamp,32,*image.identity[:1],image.identity[1],0,ea,0x02e0000000000029,0x0400000000000225,prefix,creation,worlds[0])
    if len(data)!=144:raise AssertionError('Request ABI')
    path=ROOT/f'native-host/build/local-hero-request-{pid}.bin';path.write_bytes(data)
    return path
