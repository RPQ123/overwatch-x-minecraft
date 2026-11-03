"""Validate a supported original hero before installing the shared Volley gate."""
import struct,os
from observe_overwatch import ROOT
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin

def request_data(process,pid,creation):
    reader=WeaponStates(process);sample=reader.sample_weapon();matches=[]
    admin=reader.pointer(process.base+0x17b7f90)
    controller=reader.entity(process.read(reader.pointer(admin+0x10),65536),sample['localId'])
    hero=reader.unpack('<Q',reader.component(controller,0x3f)+0x98)[0]
    profiles={0x02e0000000000029:(0x0580000000000304,[6,31],0x408001),
              0x02e0000000000042:(0x05800000000001d2,[33,38],0x408001),
              0x02e0000000000009:(0x05800000000000fe,[10],0xc08001),
              0x02e0000000000008:(0x0580000000000023,[10],0x408001)}
    if hero not in profiles:raise ValueError('No calibrated initial weapon gate profile for this hero')
    weapon,nodes,flags=profiles[hero]
    for (instance,graph,resource),definition in reader.graph_cache.items():
        if resource!=weapon:continue
        if definition['volleyNodes']!=nodes or reader.unpack('<I',instance+0x258)[0]!=flags:raise ValueError('Unexpected native hero flags/Volley nodes')
        definitions=reader.stu_list(graph+0x60);states={}
        for state, in struct.iter_unpack('<Q',reader.vector(instance+0xa0,8,4096)):
            if not state:continue
            index=reader.unpack('<i',state+0x70)[0]
            if not 0<=index<len(definitions):raise ValueError('Native state definition index')
            if reader.stu_type(definitions[index]).get('hash')!='860ee5fc':continue
            if reader.pointer(state+0x78)!=instance or reader.pointer(state)!=process.base+0x15d2450:raise ValueError('Original native Volley implementation changed')
            for offset,rva in [(0x110,0xd44b50),(0x120,0xd44d60),(0x270,0xd456c0)]:
                if reader.pointer(process.base+0x15d2450+offset)!=process.base+rva:raise ValueError('Original Volley callback changed')
            states[index]=state
        matches.append(instance)
    if len(matches)!=1:raise ValueError('Expected exactly one calibrated original base weapon script')
    for offset,rva in [(0x110,0xd44b50),(0x120,0xd44d60),(0x270,0xd456c0)]:
        if reader.pointer(process.base+0x15d2450+offset)!=process.base+rva:raise ValueError('Original Volley callback changed')
    plugin,image,pdb=provided_plugin(process)
    # Failed research scopes stay out of ordinary sessions entirely. These
    # owner slots are only observed during an explicitly enabled private lab.
    entry_probe=os.getenv('OWMC_REAPER_ENTRY_PROBE')=='1'
    entry=plugin+image.symbol_rva(pdb.exact('statescript_logger::StateEntry_orig')) if entry_probe else 0
    finish=plugin+image.symbol_rva(pdb.exact('statescript_logger::StateFinish_orig')) if entry_probe else 0
    original_entry=reader.pointer(entry) if entry else 0;original_finish=reader.pointer(finish) if finish else 0
    tick=plugin+image.symbol_rva(pdb.exact('statescript_logger::TickScript_orig')) if os.getenv('OWMC_REAPER_TICK_PROBE')=='1' else 0
    original_tick=reader.pointer(tick) if tick else 0
    data=struct.pack('<8sIIII13Q',b'OWGATE05',5,128,pid,0,creation,admin,sample['localId'],sample['modelId'],hero,weapon,entry,original_entry,finish,original_finish,tick,original_tick,0)
    if len(data)!=128:raise AssertionError('Weapon gate request size')
    return data

def prepare(process,pid,creation):
    data=request_data(process,pid,creation)
    path=ROOT/f'native-host/build/weapon-gate-request-{pid}.bin';path.write_bytes(data);return path
