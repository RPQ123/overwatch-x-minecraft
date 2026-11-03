#include "../src/native_meter_display.hpp"
#include <vector>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> memory(0x2000000);
    auto read=[&](uintptr_t at,void* out,size_t n){if(at+n>memory.size())return false;std::memcpy(out,memory.data()+at,n);return true;};
    auto put=[&](uintptr_t at,auto value){std::memcpy(memory.data()+at,&value,sizeof value);};
    unsigned writes=0,calls=0;
    auto write=[&](uintptr_t at,const void* p,size_t n){assert(at==0x700094&&n==4);writes++;std::memcpy(memory.data()+at,p,n);return true;};
    uintptr_t base=0x100000,admin=0x300000,model=0x400000,comp=0x500000,sync=comp+0xc0,bag=0x600000,primitive=0x700000,cost=0x710000;
    NativeLocalHero h;h.hero=0x02e0000000000042ULL;h.model=model;h.modelId=19;h.localId=17;h.reference=0x720000;h.heroInfo=0x730000;
    put(model+0x50,uintptr_t(0x740000));put(model+0x58,2);put(model+0x5c,2);put(0x740000,comp);put(comp+0x10,uint8_t(0x23));put(comp+8,model);put(model+0x28,admin);
    put(sync+0x2e0,bag);put(sync+0x450,comp);put(bag,base+0x1607a90);put(bag+0x3c0,sync);
    put(bag+0xa0,uintptr_t(0x750000));put(bag+0xa8,2);put(bag+0xac,2);
    put(0x750000,0x0d80000000000156ULL);put(0x750008,primitive);put(0x750010,0x0d80000000000152ULL);put(0x750018,cost);
    put(primitive,base+0x1608248);put(cost,base+0x1608248);put(primitive+0x80,bag);put(primitive+0x98,0x0d80000000000156ULL);put(primitive+0x94,6u);
    put(cost+0x80,bag);put(cost+0x98,0x0d80000000000152ULL);
    put(primitive+0xa0,17);put(primitive+0xac,2);put(cost+0xa0,1200);put(cost+0xac,2);
    put(h.reference+0x94,19u);put(h.heroInfo+0x98,h.hero);put(admin+0x220,17u);put(base+0x1608248+0x288,base+0xf5f740);
    const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};std::memcpy(memory.data()+base+0xf5f740,prefix,16);
    auto invoke=[&](uintptr_t fn,uintptr_t var,uintptr_t s,uintptr_t instance,const void*,uintptr_t user){assert(fn==base+0xf5f740&&var==primitive&&s==sync&&instance==0&&user==primitive+0x88);calls++;put(primitive+0x94,6u);return true;};
    NativeMeterDisplay display;display.update(base,admin,h,read,write,invoke);assert(calls==1&&writes==1&&display.notices==1);
    display.update(base,admin,h,read,write,invoke);assert(calls==1);
    put(primitive+0xa0,50);display.update(base,admin,h,read,write,invoke);assert(calls==2);
    put(primitive+0xa0,70);put(h.reference+0x94,20u);display.update(base,admin,h,read,write,invoke);assert(calls==2);put(h.reference+0x94,19u);
    put(base+0xf5f740,uint8_t(0xcc));display.update(base,admin,h,read,write,invoke);assert(calls==2);put(base+0xf5f740,uint8_t(0x48));
    h.hero=0x02e0000000000029ULL;display.update(base,admin,h,read,write,invoke);assert(calls==2);h.hero=0x02e0000000000042ULL;
    put(primitive+0xa0,1201);display.update(base,admin,h,read,write,invoke);assert(calls==2);put(primitive+0xa0,80);
    display.update(base,admin,h,read,write,[](auto...){return false;});assert(display.refused==1&&calls==2);unsigned flags=0;read(primitive+0x94,&flags,4);assert(flags==6);
    display.update(base,admin,h,read,write,invoke);assert(calls==2);
    // Regress both actual defects: a different hero and a different cost must
    // notify the original HUD. Integer and float meters share the exact setter.
    for(auto id:std::array<uint64_t,20>{2,3,4,5,6,7,8,9,10,0x15,0x16,0x20,0x40,0x42,0x65,0x68,0x6e,0x79,0x7a,0xdd}){
        h.hero=0x02e0000000000000ULL|id;put(h.heroInfo+0x98,h.hero);
        NativeMeterDisplay next;auto prior=calls;
        put(cost+0xa0,2250);put(primitive+0xa0,43);put(primitive+0xac,2);put(cost+0xac,2);
        next.update(base,admin,h,read,write,invoke);assert(calls==prior+1);
        next.update(base,admin,h,read,write,invoke);assert(calls==prior+1);
        put(primitive+0xa0,43.5f);put(primitive+0xac,3);put(cost+0xa0,900.f);put(cost+0xac,3);
        next.update(base,admin,h,read,write,invoke);assert(calls==prior+2);
        put(primitive+0xa0,901.f);next.update(base,admin,h,read,write,invoke);assert(calls==prior+2);
        put(primitive+0xa0,44.f);put(cost+0xa0,0.f);next.update(base,admin,h,read,write,invoke);assert(calls==prior+2);
        put(cost+0xa0,900.f);put(cost+0x80,uintptr_t(0));next.update(base,admin,h,read,write,invoke);assert(calls==prior+2);put(cost+0x80,bag);
    }
    assert(!NativeMeterDisplay::supported(0)&&!NativeMeterDisplay::supported(0x02e0000000000029ULL)&&!NativeMeterDisplay::supported(0x02e00000000000ffULL));
    std::cout<<"PASS: meter notice current owner, exact virtual/code/payload, change dedupe, bounds and failed force-flag restoration\n";
}
