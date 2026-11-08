#pragma once
#include <array>
#include <vector>
#include <cstring>
#include <cmath>
#include <cstdint>

namespace passthrough {
struct ArmoryHeader {
    char magic[8];uint32_t version,size,pid,reserved;
    uint64_t creation,admin,localId,modelId,model,hero,hostGeneration,reserved2;
    uint32_t count,reserved3;
};
struct ArmorySpec {
    uint64_t resource,resourceAddress,script,graph,bag,definition,amountObject,amountValue,amountVtable,resourceGuard,damageConfig,damageRid;
    uint32_t node,amountKind,effect,bounces;
    float eyeHeight,gravity,splash,radius,fuse,terrain;
    uint32_t volleyKey;float reserved2;
};
static_assert(sizeof(ArmoryHeader)==96&&sizeof(ArmorySpec)==144);
inline bool assaultDefenseHero(uint64_t hero){
    constexpr std::array<uint64_t,13> suffixes{0x29,0x42,8,2,0x6e,3,0x15,5,0x65,0xdd,6,10,0x40};
    for(auto suffix:suffixes)if(hero==(0x02e0000000000000ULL|suffix))return true;
    return false;
}

template<class Read> bool armoryConstantExpression(uintptr_t object,uintptr_t value,unsigned kind,Read read,float& amount){
    auto array=[&](uintptr_t at,uintptr_t& items,uint64_t& count){
        std::array<uint64_t,2> storage{},list{};
        if(!read(at,storage)||(storage[1]!=1&&storage[1]!=2)||!read(storage[0],list))return false;
        items=list[storage[1]==1?0:1];count=list[storage[1]==1?1:0];return items>=0x10000&&count>0&&count<=256;
    };
    uintptr_t code=0,constants=0;uint64_t length=0,count=0;
    if(!array(object+0x20,code,length)||!array(object+0x40,constants,count))return false;
    unsigned first=0,second=0;
    if(kind==4){std::array<uint8_t,3> bytes{};if(length!=3||!read(code,bytes)||bytes[0]!=70||bytes[2]!=0)return false;first=second=bytes[1];}
    else if(kind==5){
        std::array<uint8_t,11> bytes{};if(length!=11||!read(code,bytes)||bytes[0]!=31||bytes[2]!=4||bytes[3]!=6||bytes[4]!=70||bytes[6]!=1||bytes[7]!=4||bytes[8]!=70||bytes[10]!=0)return false;
        first=bytes[5];second=bytes[9];
    }else return false;
    uint32_t a=0,b=0;
    if(first>=count||second>=count||value!=constants+first*4||!read(value,a)||!read(constants+second*4,b)||a!=b)return false;
    std::memcpy(&amount,&a,4);return std::isfinite(amount)&&amount>=0&&amount<=10000;
}
template<class Read> bool armoryArray(uintptr_t at,Read read,uintptr_t& items,uint64_t& count){
    std::array<uint64_t,2> storage{},values{};
    if(!read(at,storage)||(storage[1]!=1&&storage[1]!=2)||!read(storage[0],values))return false;
    items=values[storage[1]==1?0:1];count=values[storage[1]==1?1:0];return (count==0||items>=0x10000)&&count<=4096;
}
template<class Read> bool armoryPureProduct(const ArmorySpec& s,Read read){
    uintptr_t code=0,constants=0,dynamics=0;uint64_t length=0,count=0,variables=0;
    std::array<uint8_t,6> bytes{};
    if(!armoryArray(s.amountObject+0x20,read,code,length)||length!=6||!read(code,bytes)
       ||bytes[0]!=70||bytes[2]!=31||bytes[4]!=102||bytes[5]!=0
       ||!armoryArray(s.amountObject+0x40,read,constants,count)||count>256||bytes[1]>=count
       ||!armoryArray(s.amountObject+0x30,read,dynamics,variables)||variables>256||bytes[3]>=variables)return false;
    float constant=0;uintptr_t dynamic=0;uint64_t pathCount=0;uintptr_t path=0;
    if(!read(constants+bytes[1]*4,constant)||!std::isfinite(constant)||constant<=0||constant>10000
       ||!read(dynamics+bytes[3]*8,dynamic)||!armoryArray(dynamic+0x10,read,path,pathCount)||pathCount!=1)return false;
    uint64_t rid=0;return read(path+8,rid)&&rid!=0;
}
using ArmoryEvaluate=bool(*)(const ArmorySpec&,float&);

// Decode only the pinned beta's literal STU metadata; no native getter runs.
template<class Read> bool armoryType(uintptr_t object,Read read,uint32_t expected){
    uintptr_t vt=0,getter=0;std::array<uint8_t,8> code{};int32_t displacement=0;uint32_t kind=0;
    if(!read(object,vt)||!read(vt+0x28,getter)||!read(getter,code)||code[0]!=0x48||code[1]!=0x8d||code[2]!=5||code[7]!=0xc3)return false;
    std::memcpy(&displacement,code.data()+3,4);auto info=getter+7+displacement;
    return read(info+0x50,kind)&&kind==expected;
}
template<class Read> bool armoryLiteral(uintptr_t object,Read read,float& value){
    uint32_t kind=armoryType(object,read,0x3ae7427e)?0x3ae7427e:armoryType(object,read,0x7b13a0d4)?0x7b13a0d4:armoryType(object,read,0xec502a81)?0xec502a81:0;
    if(kind==0x3ae7427e){int n=0;if(!read(object+16,n))return false;value=float(n);}
    else if(kind==0x7b13a0d4){if(!read(object+16,value))return false;}
    else if(kind==0xec502a81){
        uintptr_t constants=0,program=0;uint64_t count=0,length=0;std::array<uint8_t,3> ops{};
        if(!armoryArray(object+0x40,read,constants,count)||count>256||!armoryArray(object+0x20,read,program,length)
           ||length!=3||!read(program,ops)||ops[0]!=70||ops[2]!=0||ops[1]>=count||!armoryConstantExpression(object,constants+ops[1]*4,4,read,value))return false;
    }else return false;
    return std::isfinite(value);
}
struct ArmoryBlast {float splash=0,inner=0,outer=0,scale=0;};
template<class Read> bool armoryFlash(const ArmoryHeader& h,const ArmorySpec& s,Read read){
    if(s.effect==3){
        auto pointer=[&](uintptr_t at){uintptr_t p=0;read(at,p);return p;};
        auto explosion=pointer(s.definition+0x160),health=pointer(explosion+0x60);uintptr_t rings=0;uint64_t count=0;std::array<uintptr_t,2> values{};float radius=0,scale=0,amount=0;
        return h.hero==0x02e0000000000008ULL&&s.resource==0x040000000000010fULL&&s.node==3&&pointer(s.script+0x150)==0x058000000000007bULL
            &&s.gravity==0&&s.radius==8&&s.splash==0&&s.bounces==0&&s.fuse==0&&s.terrain==0
            &&armoryType(explosion,read,0x66bd247b)&&armoryArray(explosion+8,read,rings,count)&&count==1&&read(rings,values)
            &&armoryLiteral(values[0],read,radius)&&armoryLiteral(values[1],read,scale)&&radius==8&&scale==1
            &&armoryLiteral(pointer(health+0x38),read,amount)&&amount==1;
    }
    if(s.effect!=2)return true;
    auto pointer=[&](uintptr_t at){uintptr_t p=0;read(at,p);return p;};
    uintptr_t rings=0;uint64_t count=0;std::array<uintptr_t,2> values{};float radius=0,scale=0;
    auto explosion=pointer(s.definition+0x160);
    return h.hero==0x02e0000000000042ULL&&s.resource==0x040000000000037dULL&&s.node==7
        &&s.gravity==20&&s.radius==3&&s.splash==0&&s.bounces==0&&s.fuse==0&&s.terrain==0
        &&armoryType(explosion,read,0x66bd247b)&&armoryArray(explosion+8,read,rings,count)&&count==1&&read(rings,values)
        &&armoryLiteral(values[0],read,radius)&&armoryLiteral(values[1],read,scale)&&radius==3&&scale==1;
}
template<class Read> bool barrageDefinition(const ArmorySpec& s,Read read);
template<class Read> bool armoryGravity(const ArmorySpec& s,Read read){
    uintptr_t motions=0,motion=0,config=0;uint64_t count=0;float gravity=0;
    if(!armoryArray(s.definition+0x100,read,motions,count))return false;
    if(count==2)return barrageDefinition(s,read);
    if(count>1)return false;
    if(count==0)return s.gravity==0;
    return read(motions,motion)&&armoryType(motion,read,0xc2b6ce4b)&&read(motion+8,config)
        &&armoryLiteral(config,read,gravity)&&gravity>=0&&gravity<=30&&s.gravity==gravity;
}
template<class Read> bool armoryBlast(const ArmorySpec& s,Read read,ArmoryBlast& result){
    auto pointer=[&](uintptr_t at){uintptr_t p=0;read(at,p);return p;};
    auto explosion=pointer(s.definition+0x160),health=pointer(explosion+0x60),amount=pointer(health+0x38);
    uintptr_t rings=0;uint64_t count=0;std::array<uintptr_t,4> values{};float first=0;
    if(s.effect!=1||!armoryArray(explosion+8,read,rings,count)||count!=2||!read(rings,values)
       ||!armoryLiteral(amount,read,result.splash)||!armoryLiteral(values[0],read,result.inner)||!armoryLiteral(values[1],read,first)
       ||!armoryLiteral(values[2],read,result.outer)||!armoryLiteral(values[3],read,result.scale))return false;
    return result.splash>0&&result.splash<=1000&&result.splash==s.splash&&result.outer==s.radius
        &&result.inner>=0&&result.inner<result.outer&&result.outer<=10&&first==1&&result.scale>=0&&result.scale<=1;
}
template<class Read> bool armoryAmount(const ArmoryHeader& h,const ArmorySpec& s,Read read,float& amount,ArmoryEvaluate evaluate=nullptr){
    auto pointer=[&](uintptr_t address){uintptr_t value=0;read(address,value);return value;};
    uint64_t resource=0;uint32_t owner=0;
    if(!read(h.model+0x94,owner)||owner!=h.modelId||pointer(h.model+0x28)!=h.admin
       ||pointer(pointer(pointer(s.script+0x10)+0x450)+8)!=h.model||pointer(s.script+0x98)!=s.bag||pointer(s.script+0x160)!=s.graph
       ||!read(s.resourceAddress,resource)||resource!=s.resource||pointer(s.amountObject)!=s.amountVtable)return false;
    if(s.amountKind&0x20000){
        auto ref=pointer(s.definition+0x110);uintptr_t items=0;uint64_t count=0;
        if(pointer(ref)!=s.resourceGuard||!armoryArray(ref+8,read,items,count)||count>64)return false;
        bool found=false;for(uint64_t i=0;i<count;i++)if(items+i*16+8==s.resourceAddress)found=true;
        if(!found)return false;
    }else if(pointer(s.resourceAddress-24)!=s.resourceGuard)return false;
    uint64_t graphFlag=0,count=0;auto storage=pointer(s.graph+0x50);
    if(!read(s.graph+0x58,graphFlag)||(graphFlag!=1&&graphFlag!=2)||!read(storage+(graphFlag==1?8:0),count)||count>4096||s.node>=count
       ||pointer(pointer(storage+(graphFlag==1?0:8))+s.node*8)!=s.definition)return false;
    uintptr_t definitions=0;uint64_t definitionCount=0;int16_t instance=0;
    unsigned stateIndex=(s.volleyKey>>8)&255;
    if(!armoryArray(s.graph+0x60,read,definitions,definitionCount)||stateIndex>=definitionCount
       ||pointer(definitions+stateIndex*8)!=s.definition||!read(s.script+0x18,instance)
       ||s.volleyKey!=((uint32_t(uint16_t(int(instance)*8))<<16)|(stateIndex<<8)))return false;
    bool control=s.effect==2||s.effect==3;
    auto impact=pointer(s.definition+(control?0x160:0x168)),health=pointer(impact+(control?0x60:0x38));
    if(pointer(health+0x38)!=s.damageConfig)return false;
    unsigned kind=s.amountKind&255;
    if(kind==3){
        unsigned bucket=(s.amountKind>>8)&255;if(bucket>=16||s.amountValue!=s.amountObject+0xa0)return false;
        auto bag=s.bag;
        if(s.amountKind&0x10000){
            struct Components{uintptr_t items;int count,capacity;} components{};
            if(!read(h.model+0x50,components)||components.count<1||components.count>components.capacity||components.capacity>256)return false;
            bag=0;
            for(int i=0;i<components.count-1;i++){
                auto component=pointer(components.items+i*8);uint8_t id=0;
                if(read(component+0x10,id)&&id==0x23&&pointer(component+8)==h.model){bag=pointer(component+0xc0+0x2e0);break;}
            }
            if(!bag)return false;
        }
        struct Values{uintptr_t items;int count,capacity;} values{};
        if(!read(bag+0xa0+bucket*0x30,values)||values.count<1||values.count>values.capacity||values.capacity>512)return false;
        bool found=false;
        for(int i=0;i<values.count;i++){std::array<uint64_t,2> pair{};if(!read(values.items+i*16,pair))return false;if(pair[0]==s.damageRid&&pair[1]==s.amountObject)found=true;}
        if(!found)return false;
        struct Primitive{uint64_t raw;uint32_t unused,type;} value{};
        if(!read(s.amountValue,value))return false;
        if(value.type==2)amount=float(int32_t(value.raw));
        else if(value.type==3){uint32_t bits=uint32_t(value.raw);std::memcpy(&amount,&bits,4);}else return false;
    }else{
        if(s.damageConfig!=s.amountObject)return false;
        if(kind==1){int value=0;if(s.amountValue!=s.amountObject+16||!read(s.amountValue,value))return false;amount=float(value);}
        else if(kind==2){if(s.amountValue!=s.amountObject+16||!read(s.amountValue,amount))return false;}
        else if(kind==4||kind==5){if(!armoryConstantExpression(s.amountObject,s.amountValue,kind,read,amount))return false;}
        else if(kind==6||kind==7){
            if(pointer(s.amountObject+8)!=s.amountValue||pointer(s.amountValue)!=s.damageRid)return false;
            if(kind==7&&!armoryPureProduct(s,read))return false;
            if(kind==6){
                uintptr_t items=0;uint64_t count=0,rid=0;
                if(!armoryType(s.amountObject,read,0xf8cc195d)||!armoryArray(s.amountObject+0x10,read,items,count)||count!=1||!read(items+8,rid)
                   ||(rid!=0x0d800000000001dcULL&&rid!=0x0d80000000000e33ULL))return false;
            }
            // Structural loading runs on a worker. The original pure getter is
            // evaluated only inside the original factory callback/context.
            if(!evaluate){amount=0;return true;}
            if(!evaluate(s,amount))return false;
        }
        else return false;
    }
    return std::isfinite(amount)&&amount>=0&&amount<=10000;
}
template<class Read> bool armoryBastionTank(const ArmoryHeader& h,const ArmorySpec& s,Read read){
    if(s.resource!=0x04000000000003ceULL)return true;
    auto pointer=[&](uintptr_t at){uintptr_t value=0;read(at,value);return value;};
    if(h.hero!=0x02e0000000000015ULL||s.node!=25||pointer(s.script+0x150)!=0x058000000000024fULL
       ||s.amountKind!=1||s.effect!=1||s.gravity!=0||s.splash!=140||s.radius!=4||s.bounces||s.fuse!=0||s.terrain!=0
       ||((s.volleyKey>>8)&255)!=19||!armoryType(s.definition,read,0x860ee5fc)
       ||!armoryType(s.amountObject,read,0x3ae7427e))return false;
    uintptr_t items=0;uint64_t count=0;
    if(!armoryArray(s.graph+0x50,read,items,count)||count!=29
       ||!armoryArray(s.graph+0x60,read,items,count)||count!=22
       ||!armoryArray(s.definition+0x100,read,items,count)||count!=0)return false;
    float direct=0;
    auto impact=pointer(s.definition+0x168),directHealth=pointer(impact+0x38);
    if(!armoryType(impact,read,0x4ef1dd7e)||!armoryType(directHealth,read,0x06a06f4e)
       ||!armoryAmount(h,s,read,direct)||direct!=50)return false;
    auto typed=[&](uintptr_t object,uint32_t type,float expected){
        float actual=0;return armoryType(object,read,type)&&armoryLiteral(object,read,actual)&&actual==expected;
    };
    if(!typed(pointer(s.definition+0x128),0x3ae7427e,5)
       ||!typed(pointer(s.definition+0x130),0x7b13a0d4,100)
       ||!typed(pointer(s.definition+0x190),0x3ae7427e,1)
       ||!typed(pointer(s.definition+0x198),0x3ae7427e,1))return false;
    // Speed is the original script variable18e0, evaluated by the real native
    // factory. Its resolved60 is separately checked at that exact callback.
    auto speed=pointer(s.definition+0x140);uint64_t rid=0;
    if(!armoryType(speed,read,0xf8cc195d)||!armoryArray(speed+0x10,read,items,count)||count!=1
       ||!read(items+8,rid)||rid!=0x0d800000000018e0ULL)return false;
    auto explosion=pointer(s.definition+0x160),health=pointer(explosion+0x60);
    ArmoryBlast blast{};std::array<uintptr_t,4> rings{};
    if(!armoryType(explosion,read,0x66bd247b)||!armoryType(health,read,0x06a06f4e)
       ||!typed(pointer(health+0x38),0x3ae7427e,140)||!armoryBlast(s,read,blast)
       ||blast.inner!=1||blast.outer!=4||blast.scale!=.3f
       ||!armoryArray(explosion+8,read,items,count)||count!=2||!read(items,rings))return false;
    // These are the actual two damage rings. Do not invent a self-impulse or
    // reinterpret the separate four-slot knockback rings from similar values.
    return typed(rings[0],0x3ae7427e,1)&&typed(rings[1],0x3ae7427e,1)
        &&typed(rings[2],0x3ae7427e,4)&&typed(rings[3],0x7b13a0d4,.3f);
}
inline bool armoryBastionTankFlight(uint64_t hero,uint64_t resource,uint32_t status,uintptr_t result,
        uint32_t type,float speed,float lifetime,float range){
    if(resource!=0x04000000000003ceULL)return true;
    return hero==0x02e0000000000015ULL&&status==8&&result==0&&type==1&&speed==60&&lifetime==5&&range==100;
}
inline bool armorySpecBounds(const ArmorySpec& s){
    return (s.resource>>48)==0x0400&&s.resourceAddress>=0x10018&&s.script>=0x10000&&s.graph>=0x10000&&s.bag>=0x10000&&s.definition>=0x10000
        &&s.node<4096&&(s.amountKind&255)>=1&&(s.amountKind&255)<=7&&!(s.amountKind&~0x30f0fu)&&s.effect<=16&&s.bounces<=8
        &&std::isfinite(s.eyeHeight)&&s.eyeHeight>=.5f&&s.eyeHeight<=2.5f&&std::isfinite(s.gravity)&&s.gravity>=0&&s.gravity<=30
        &&std::isfinite(s.splash)&&s.splash>=0&&s.splash<=1000&&std::isfinite(s.radius)&&s.radius>=0&&s.radius<=10
        &&std::isfinite(s.fuse)&&s.fuse>=0&&s.fuse<=10&&std::isfinite(s.terrain)&&s.terrain>=0&&s.terrain<=4
        &&(s.volleyKey&255)==0&&s.reserved2==0;
}
}
#include "native_barrage_motion.hpp"
