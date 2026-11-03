#include "../src/native_barrage_motion.hpp"
#include <cassert>
#include <unordered_map>
#include <iostream>
using namespace passthrough;
int main(){
    BarrageScope scope;
    assert(!scope.admit(1,2,10,1,3,4,5));
    assert(scope.admit(1,2,10,0,3,4,5)&&scope.admit(1,2,11,1,3,4,5));
    assert(!scope.admit(1,2,12,2,30,4,5));
    assert(!scope.admit(1,2,13,3,3,4,5)); // returning cannot revive old permission
    assert(!scope.admit(1,2,10,0,30,4,5)); // duplicate first event cannot rebind
    assert(!scope.admit(1,2,13,3,3,40,5));
    assert(!scope.admit(10,2,14,4,3,4,5));
    assert(scope.admit(1,2,20,0,30,4,5)&&scope.admit(1,2,21,1,30,4,5));
    std::unordered_map<uintptr_t,uint8_t> bytes;
    auto put=[&](uintptr_t at,auto value){auto p=reinterpret_cast<uint8_t*>(&value);for(size_t i=0;i<sizeof value;i++)bytes[at+i]=p[i];};
    auto read=[&](uintptr_t at,auto& value){auto p=reinterpret_cast<uint8_t*>(&value);for(size_t i=0;i<sizeof value;i++){auto found=bytes.find(at+i);if(found==bytes.end())return false;p[i]=found->second;}return true;};
    uintptr_t base=0x10000000,config=0x20000,arg=0x30000,holder=0x40000,items=0x50000;
    put(config+0x68,holder);put(config+0x70,uint64_t(1));put(holder,items);put(holder+8,std::array<int,2>{2,2});put(arg+0x40,uint16_t(17));
    for(unsigned j=2;j<=6;j++)put(base+0x18449f0+(17+j)*4,uint32_t(0x40000000));
    for(unsigned i=0;i<2;i++){uintptr_t at=0x60000+i*0x100;put(items+i*8,at);put(at,base+0x16142c0);put(at+0x20,std::array<float,12>{0,.2f,i==0?1.f:0.f,.5f,0,1,.1f,1,.2f,1.5f,10,360});}
    std::array<BarrageWave,2> waves{};assert(barrageResolved(base,config,arg,read,waves));
    assert(waves[0].spiral==1&&waves[1].spiral==0&&waves[0].frequency<0&&waves[0].phase==.25f);
    auto a=barrageWaveOffset(BarrageWave{0,.2f,.25f,.5f,1,90,1},{0,0,1},.2f);
    assert(std::abs(a[0]+.809016994f)<.000001f&&std::abs(a[1]+.587785252f)<.000001f&&a[2]==0);
    put(0x60020,std::array<float,12>{0,.2f,1,.5f,0,1,.1f,1,.2f,99,10,360});assert(!barrageResolved(base,config,arg,read,waves));
    put(holder+8,std::array<int,2>{3,3});assert(!barrageResolved(base,config,arg,read,waves));
    std::cout<<"PASS: actual-seed Wave sampling, native-axis golden displacement and changed-profile refusal.\n";
}
