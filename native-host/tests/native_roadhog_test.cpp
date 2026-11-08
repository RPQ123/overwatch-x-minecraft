#include "../src/native_roadhog.hpp"
#include <cassert>
#include <unordered_map>
#include <iostream>
using namespace passthrough;
int main(){
    assert(assaultDefenseHero(roadHogHero));
    assert(!assaultDefenseHero(0x02e0000000000007ULL)); // other tanks remain out of armory scope.
    assert(roadhogFactory(roadHogHero,0x040000000000029aULL,0,1,2,80,5,100));
    assert(roadhogFactory(roadHogHero,0x0400000000000295ULL,8,0,1,60,.15f,100));
    assert(roadhogFactory(roadHogHero,0x0400000000000405ULL,0,1,3,0,0,100));
    assert(!roadhogFactory(roadHogHero,0x040000000000029aULL,8,0,2,80,5,100));
    assert(!roadhogFactory(roadHogHero,0x0400000000000295ULL,0,1,1,60,.15f,100));
    assert(!roadhogFactory(roadHogHero,0x0400000000000295ULL,8,1,1,60,.15f,100));
    assert(!roadhogFactory(roadHogHero,0x0400000000000405ULL,0,1,3,80,5,100));
    std::unordered_map<uintptr_t,unsigned char> memory;
    auto put=[&](uintptr_t at,auto value){auto p=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++)memory[at+i]=p[i];};
    auto read=[&](uintptr_t at,auto& value){auto p=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++){auto it=memory.find(at+i);if(it==memory.end())return false;p[i]=it->second;}return true;};
    uintptr_t storage=0x1000000;
    auto type=[&](uintptr_t object,uint32_t kind){
        uintptr_t vt=storage,fn=storage+0x100,info=storage+0x200;storage+=0x1000;
        put(object,vt);put(vt+0x28,fn);
        std::array<uint8_t,8> code{0x48,0x8d,0x05,0,0,0,0,0xc3};int32_t relative=int32_t(info-fn-7);std::memcpy(code.data()+3,&relative,4);put(fn,code);put(info+0x50,kind);
    };
    auto literal=[&](uintptr_t at,float value){uintptr_t obj=storage;storage+=0x1000;type(obj,0x7b13a0d4);put(obj+16,value);put(at,obj);};
    ArmoryHeader h{};h.hero=roadHogHero;ArmorySpec s{};s.script=0x10000;s.graph=0x20000;s.definition=0x30000;s.node=34;s.resource=0x0400000000000295ULL;
    put(s.script+0x150,uint64_t(0x05800000000001c6ULL));put(s.graph+0x50,uintptr_t(0x40000));put(s.graph+0x58,uint64_t(1));put(0x40000,uintptr_t(0x50000));put(0x40008,uint64_t(60));put(0x50000+s.node*8,s.definition);
    type(s.definition,0x860ee5fc);literal(s.definition+304,100);literal(s.definition+320,60);literal(s.definition+296,.15f);literal(s.definition+400,1);
    uintptr_t split=0x60000,child=0x70000,ref=0x80000,entity=0x90000,impact=0xa0000,health=0xb0000;
    put(s.definition+384,split);type(split,0x07e34e24);put(split+144,child);literal(split+136,10);type(child,0x860ee5fc);
    put(child+272,ref);put(ref+24,entity);type(entity,0xe53c2921);put(entity+24,uint64_t(0x040000000000029aULL));
    literal(child+320,80);literal(child+296,5);literal(child+304,100);literal(child+400,25);put(child+360,impact);type(impact,0x4ef1dd7e);put(impact+56,health);literal(health+56,9);
    assert(roadhogDefinition(h,s,read));
    literal(child+400,24);assert(!roadhogDefinition(h,s,read));literal(child+400,25);
    literal(health+56,50);assert(!roadhogDefinition(h,s,read));literal(health+56,9);
    put(entity+24,uint64_t(0x0400000000000405ULL));assert(!roadhogDefinition(h,s,read));put(entity+24,uint64_t(0x040000000000029aULL));
    s.effect=4;assert(!roadhogDefinition(h,s,read));s.effect=0;
    assert(roadhogDefinition(h,s,read));
    h.hero=0x02e0000000000002ULL;assert(roadhogDefinition(h,s,read));
    std::cout<<"PASS: Roadhog original factory status/flight, nested child count/damage/resource guards; existing heroes unchanged.\n";
}
