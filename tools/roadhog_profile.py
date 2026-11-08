"""Exact typed 24919 Roadhog weapon declarations, read-only on the existing owner."""
import math

HERO=0x02e0000000000040
RESOURCES={30:(0x040000000000029a,9,80,5,25),34:(0x0400000000000295,50,60,.15000000596046448,1),37:(0x0400000000000405,7,0,0,16)}

def validate_weapon(r,script,index,node,resource,gravity,amount):
    from inspect_native_control_skills import ref,literal
    b=r.bindings
    if script!=0x05800000000001c6 or index not in RESOURCES or gravity!=0:
        raise ValueError('Roadhog original graph/node/gravity differs')
    expected,damage,speed,life,count=RESOURCES[index]
    if resource!=expected or amount!=damage:
        raise ValueError('Roadhog original resource/damage differs')
    def field(obj,key,kind):return ref(b,obj,key,kind,0xbfd9aadd)
    def number(obj,key,kind):
        owner,at,category,declared=b.field(obj,key)
        if (owner,category,declared)!=(kind,2,0xbfd9aadd):raise ValueError('Roadhog original numeric declaration differs')
        # The generic pointer helper deliberately rejects nullptr. Q has two
        # genuinely absent fields; inspect the field value before dereferencing.
        value=r.unpack('<Q',at)[0]
        return 0 if not value else literal(b,value)
    for key,wanted in ((0x308e35d5,100),(0xac2f916a,speed),(0x5257be73,life),(0x472bec0c,count)):
        if abs(number(node,key,0x860ee5fc)-wanted)>1e-6:
            raise ValueError('Roadhog original flight/count differs')
    if index==34:
        split=ref(b,node,0x3ac99059,0x860ee5fc,0x07e34e24)
        child=ref(b,split,0x3c26d198,0x07e34e24,0x860ee5fc)
        if number(split,0x3626f286,0x07e34e24)!=10:
            raise ValueError('Roadhog original split cone differs')
        for key,wanted in ((0x308e35d5,100),(0xac2f916a,80),(0x5257be73,5),(0x472bec0c,25)):
            if number(child,key,0x860ee5fc)!=wanted:raise ValueError('Roadhog original split child differs')
        spawn=ref(b,child,0xf7329268,0x860ee5fc,0x84d05911)
        entity=r.pointer(spawn+24)
        if b.metadata(entity)[1]!=0xe53c2921 or b.unpack('<Q',entity+24)[0]!=0x040000000000029a:
            raise ValueError('Roadhog original split resource differs')
        damage=b.impact_damage(child)
        if damage.get('configType')!='STUConfigVarInt' or damage.get('value')!=9:
            raise ValueError('Roadhog original split damage differs')
