#include "../src/native_state_lifetime.hpp"
#include <unordered_map>
#include <cassert>
#include <iostream>
using namespace passthrough;
struct Memory {
    std::unordered_map<uintptr_t,unsigned char> bytes;
    template<class T>void put(uintptr_t p,const T& value){auto raw=reinterpret_cast<const unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++)bytes[p+i]=raw[i];}
    template<class T>bool get(uintptr_t p,T& value){auto raw=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++){auto found=bytes.find(p+i);if(found==bytes.end())return false;raw[i]=found->second;}return true;}
};
int main(){
    Memory m;auto read=[&](uintptr_t p,auto& value){return m.get(p,value);};
    NativeLifetimeRequest r{};std::memcpy(r.magic,"OWLIFE01",8);r.version=1;r.pid=42;r.creation=99;r.sequence=5;r.wall=1000;r.hostGeneration=7;r.world=8;r.admin=0x10000;r.modelId=13;r.hero=0x02e0000000000002ULL;r.script=0x30000;r.graph=0x50000;r.definition=0x80000;r.state=0x81000;r.logger=0x90000;r.nativeTick=100;r.node=2;r.stateIndex=1;
    r.callbackThread=7;NativeLifetimeContext c{42,7,99,r.admin,13,0x20000,r.hero,7,8,1100,0x1000000,r.logger};
    m.put(c.model+0x28,c.admin);m.put(r.script+0x10,uint64_t(0x40000));m.put(0x40450,uint64_t(0x41000));m.put(0x41008,c.model);
    m.put(r.script+0x150,uint64_t(0x0580000000000020ULL));m.put(r.script+0x160,r.graph);m.put(r.state+0x78,r.script);m.put(r.state+0x70,r.stateIndex);m.put(r.state+0x40,uint32_t(9));m.put(r.state,uint64_t(0xa0000));m.put(0xa0110,c.base+0xd67920);
    for(unsigned offset:{0x50,0x60}){auto storage=uint64_t(0x60000+offset*16),items=uint64_t(0x70000+offset*16);m.put(r.graph+offset,std::array<uint64_t,2>{storage,1});m.put(storage,std::array<uint64_t,2>{items,32});m.put(items+(offset==0x50?2:r.stateIndex)*8,r.definition);}
    struct List{uintptr_t items;int count,capacity;} states{0x85000,1,1};m.put(r.script+0xa0,states);m.put(states.items,r.state);
    auto node=[&](uintptr_t at,uintptr_t parent,uint64_t key,bool nil){std::array<unsigned char,40> raw{};std::memcpy(raw.data()+8,&parent,8);std::memcpy(raw.data()+32,&key,8);raw[25]=nil;m.put(at,raw);};
    m.put(r.logger,std::array<uint64_t,2>{0x90400,1});node(0x90400,0x91000,0,true);node(0x91000,0x90400,r.script,false);
    m.put(0x91028,std::array<uint64_t,2>{0x92000,1});node(0x92000,0x93000,0,true);node(0x93000,0x92000,2,false);
    std::array<unsigned char,9> stamp{};std::memcpy(stamp.data(),&r.nativeTick,8);m.put(0x93028,stamp);
    assert(nativeLifetimeOwner(r,c,read));
    auto copy=r;copy.creation++;assert(!nativeLifetimeOwner(copy,c,read));copy=r;copy.world++;assert(!nativeLifetimeOwner(copy,c,read));copy=r;copy.nativeTick++;assert(!nativeLifetimeOwner(copy,c,read));copy=r;copy.node=3;assert(!nativeLifetimeOwner(copy,c,read));
    auto changed=c;changed.now=2600;assert(!nativeLifetimeOwner(r,changed,read));changed=c;changed.hero=0x02e0000000000029ULL;assert(!nativeLifetimeOwner(r,changed,read));changed=c;changed.modelId++;assert(!nativeLifetimeOwner(r,changed,read));changed=c;changed.thread++;assert(!nativeLifetimeOwner(r,changed,read));
    stamp[8]=1;m.put(0x93028,stamp);assert(!nativeLifetimeOwner(r,c,read));stamp[8]=0;m.put(0x93028,stamp);
    m.put(states.items,uint64_t(0));assert(!nativeLifetimeOwner(r,c,read));m.put(states.items,r.state);
    m.put(r.state+0x40,uint32_t(0));assert(!nativeLifetimeOwner(r,c,read));m.put(r.state+0x40,uint32_t(9));
    m.put(0xa0110,c.base+0xd67921);assert(!nativeLifetimeOwner(r,c,read));m.put(0xa0110,c.base+0xd67920);
    assert(nativeLifetimeOwner(r,c,read));
    std::cout<<"PASS: private original lifetime command, exact owner/node/graph/runtime, active logger/creation/world/time guards.\n";
}
