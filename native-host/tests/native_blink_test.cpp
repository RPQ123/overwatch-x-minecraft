#include "../src/native_blink.hpp"
#include <cassert>
#include <iostream>
#include <unordered_map>
using namespace passthrough;
struct Memory {
    std::unordered_map<uintptr_t,unsigned char> bytes;
    template<class T>void put(uintptr_t p,const T& value){auto raw=reinterpret_cast<const unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++)bytes[p+i]=raw[i];}
    template<class T>bool get(uintptr_t p,T& value){auto raw=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++){auto found=bytes.find(p+i);if(found==bytes.end())return false;raw[i]=found->second;}return true;}
};
int main(){
    Memory m;auto read=[&](uintptr_t p,auto& value){return m.get(p,value);};
    NativeBlinkBinding b{};std::memcpy(b.magic,"OWBLK001",8);b.version=1;b.admin=0x10000;b.localId=12;b.modelId=13;b.model=0x20000;b.script=0x30000;b.graph=0x50000;b.bag=0x55000;b.logger=0x90000;b.first=0x80000;b.second=0x80100;b.definitionVtable=0xa0000;
    m.put(b.admin+0x220,uint32_t(12));m.put(b.model+0x94,uint32_t(13));m.put(b.model+0x28,b.admin);
    m.put(b.script+0x150,uint64_t(0x0580000000000024ULL));m.put(b.script+0x98,b.bag);m.put(b.script+0x160,b.graph);
    m.put(b.script+0x10,uintptr_t(0x40000));m.put(0x40450,uintptr_t(0x41000));m.put(0x41008,b.model);
    m.put(b.first,b.definitionVtable);m.put(b.second,b.definitionVtable);m.put(b.graph+0x50,uintptr_t(0x60000));m.put(b.graph+0x58,uint64_t(1));
    m.put(0x60000,uintptr_t(0x70000));m.put(0x60008,uint64_t(64));m.put(0x70000+5*8,b.first);m.put(0x70000+10*8,b.second);
    assert(blinkOwner(b,b.admin,12,13,b.model,read));
    m.put(b.script+0x150,uint64_t(0x058000000000001aULL));assert(!blinkOwner(b,b.admin,12,13,b.model,read));m.put(b.script+0x150,uint64_t(0x0580000000000024ULL));
    m.put(0x70000+10*8,b.first);assert(!blinkOwner(b,b.admin,12,13,b.model,read));m.put(0x70000+10*8,b.second);
    assert(!blinkOwner(b,b.admin,12,14,b.model,read));
    // Native ordered-map lookup: logger -> script -> action5 and action10.
    auto node=[&](uintptr_t at,uintptr_t parent,uint64_t key,bool nil,uintptr_t right){std::array<unsigned char,40> raw{};std::memcpy(raw.data()+8,&parent,8);std::memcpy(raw.data()+16,&right,8);std::memcpy(raw.data()+32,&key,8);raw[25]=nil;m.put(at,raw);};
    m.put(b.logger,std::array<uint64_t,2>{0x90400,1});node(0x90400,0x91000,0,true,0);node(0x91000,0x90400,b.script,false,0x90400);
    m.put(0x91028,std::array<uint64_t,2>{0x92000,2});node(0x92000,0x93000,0,true,0);node(0x93000,0x92000,5,false,0x94000);node(0x94000,0x93000,10,false,0x92000);
    auto stamp=[&](uintptr_t at,uint64_t tick,unsigned char done){std::array<unsigned char,9> raw{};std::memcpy(raw.data(),&tick,8);raw[8]=done;m.put(at,raw);};
    stamp(0x93028,100,1);stamp(0x94028,200,0);uint64_t tick=0;assert(blinkStateTick(b.logger,b.script,read,tick)&&tick==200);
    stamp(0x94028,200,2);assert(!blinkStateTick(b.logger,b.script,read,tick));stamp(0x94028,200,1);
    NativeBlinkAccumulator f;GuestBody s;s.generation=4;s.worldId=8;
    assert(!f.capture(s,13,200,1000,{1000,1000,1000}));f.applied({1000,1000,1000});
    assert(!f.capture(s,13,200,1001,{1000,1000,992.52f})); // old action cannot teleport
    assert(f.capture(s,13,300,1010,{1000,1000.2f,992.52f}));f.applied({1000,1000,1000});assert(f.captures==1);
    assert(!f.capture(s,13,300,1011,{1000,1000,992.52f})); // replay
    assert(!f.capture(s,13,310,1020,{1000,1000,1000})); // End log without displacement
    assert(!f.capture(s,13,310,1200,{1000,1000,992.52f})); // stale End cannot admit recall
    assert(!f.capture(s,13,400,1300,{1000,1000,1000}));
    assert(f.capture(s,13,400,1305,{1007.48f,1000,1000})); // action before original mover
    f.applied({1000,1000,1000});assert(!f.capture(s,13,500,1400,{1009,1000,1000}));
    s.worldId=9;assert(!f.capture(s,13,600,1500,{1000,1000,992.52f})&&f.total[0]==0&&f.total[2]==0);
    f.applied({1000,1000,1000});s.generation=5;assert(!f.capture(s,13,700,1600,{1000,1000,992.52f}));
    std::cout<<"PASS: Blink actual action/owner/graph guards, exact-once displacement, stale recall and world/source refusal.\n";
}
