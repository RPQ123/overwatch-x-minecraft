#pragma once
#include "native_armory.hpp"

namespace passthrough {
constexpr uint64_t roadHogHero=0x02e0000000000040ULL;
inline bool roadhogFactory(uint64_t hero,uint64_t resource,uint32_t status,uintptr_t result,uint32_t type,float speed,float life,float range){
    if(hero!=roadHogHero)return true;
    if(range!=100)return false;
    if(resource==0x040000000000029aULL)return status==0&&result&&type==2&&speed==80&&life==5;
    if(resource==0x0400000000000295ULL)return status==8&&!result&&type==1&&speed==60&&std::abs(life-.15f)<1e-6f;
    return resource==0x0400000000000405ULL&&status==0&&result&&type==3&&speed==0&&life==0;
}
/** Validate actual current declarations, including the otherwise unexecuted
 * on-expiry child. No native timer/script invocation and no diagnostic toggle. */
template<class Read> bool roadhogDefinition(const ArmoryHeader& h,const ArmorySpec& s,Read read){
    if(h.hero!=roadHogHero)return true;
    auto pointer=[&](uintptr_t at){uintptr_t p=0;read(at,p);return p;};
    auto literal=[&](uintptr_t at,float expected){float value=0;return armoryLiteral(pointer(at),read,value)&&std::abs(value-expected)<1e-6f;};
    uint64_t resource=0,items=0,count=0;
    if(!read(s.script+0x150,resource)||resource!=0x05800000000001c6ULL||s.effect||s.gravity||s.splash||s.radius||s.fuse||s.terrain||s.bounces
       ||!armoryArray(s.graph+0x50,read,items,count)||count!=60||s.node>=count||pointer(items+s.node*8)!=s.definition
       ||!armoryType(s.definition,read,0x860ee5fc)||!literal(s.definition+304,100))return false;
    if(s.resource==0x0400000000000405ULL){
        return s.node==37&&literal(s.definition+400,16)&&literal(s.definition+408,8)&&!pointer(s.definition+320)&&!pointer(s.definition+296);
    }
    bool primary=s.resource==0x040000000000029aULL;
    if(!primary&&s.resource!=0x0400000000000295ULL)return false;
    if(s.node!=(primary?30u:34u)||!literal(s.definition+320,primary?80:60)||!literal(s.definition+296,primary?5:.15f)
       ||!literal(s.definition+400,primary?25:1))return false;
    if(primary)return true;
    auto split=pointer(s.definition+384),child=pointer(split+144),entity=pointer(pointer(child+272)+24),impact=pointer(child+360);
    uint64_t childResource=0;
    return armoryType(split,read,0x07e34e24)&&armoryType(child,read,0x860ee5fc)&&armoryType(entity,read,0xe53c2921)
        &&read(entity+24,childResource)&&childResource==0x040000000000029aULL
        &&literal(split+136,10)&&literal(child+320,80)&&literal(child+296,5)&&literal(child+304,100)&&literal(child+400,25)
        &&armoryType(impact,read,0x4ef1dd7e)&&literal(pointer(impact+56)+56,9);
}
}
