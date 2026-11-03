"""Read reflected camera definitions for the 21 locally verified beta heroes.

Roster presence grants no MC combat binding. Values are read from the actual
current model, with declared field/type/offset checks; no getters are executed.
"""
import struct
from native_weapon_binding import WeaponBindingReader

HERO_IDS=frozenset(0x02e0000000000000+x for x in
    (2,3,4,5,6,7,8,9,10,0x15,0x16,0x20,0x29,0x40,0x42,0x65,0x68,0x6e,0x79,0x7a,0xdd))


def camera_definition(reader,model):
    r=reader
    definition=r.pointer(r.pointer(model+0x30)&~63)
    if r.metadata(definition)[1]!=0xec23fffd:raise ValueError('Camera model definition type')
    header,flag=r.unpack('<QQ',definition+0x28)
    if flag!=2:raise ValueError('Camera component map representation')
    buckets,ends,items=r.unpack('<i4xQQ',header)
    if not 1<=buckets<=256:raise ValueError('Camera component map bucket bounds')
    count=r.unpack('<i',ends+4*(buckets-1))[0]
    if not 1<=count<=256:raise ValueError('Camera component map count bounds')
    candidates=[obj for kind,obj in struct.iter_unpack('<I4xQ',r.memory.read(items,count*16)) if kind==0xdaf7a654]
    if len(candidates)!=1:raise ValueError('Expected one STUFirstPersonComponent')
    obj=candidates[0];values={}
    info,kind,size=r.metadata(obj)
    if kind!=0xdaf7a654 or size!=40:raise ValueError('First-person metadata layout')
    arguments=r.pointer(info+0x28);fields=r.unpack('<i',info+0x54)[0]
    if not 3<=fields<=512:raise ValueError('First-person metadata field bounds')
    declarations={key:(offset,constraint) for key,offset,constraint in
        (r.unpack('<IiQ',arguments+i*0xa0+8) for i in range(fields))}
    for key,offset,label in ((0x23b74fe6,0x18,'fov'),(0x9c200bc4,0x1c,'eyeHeight')):
        declared_offset,constraint=declarations.get(key,(None,None))
        if declared_offset!=offset or not constraint or r.constraint_identity(constraint)!=0x8fa75a30:
            raise ValueError('First-person declared field/type differs')
        values[label]=r.unpack('<f',obj+offset)[0]
    if not 40<=values['fov']<=67 or not .5<=values['eyeHeight']<=2.5:
        raise ValueError('First-person calibration bounds')
    return values
