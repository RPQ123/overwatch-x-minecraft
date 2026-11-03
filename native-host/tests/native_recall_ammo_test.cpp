#include "../src/native_recall_ammo.hpp"
#include <vector>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> m(0x2000000);
    auto read=[&](uintptr_t a,void* out,size_t n){if(a+n>m.size())return false;std::memcpy(out,m.data()+a,n);return true;};
    auto put=[&](uintptr_t a,auto v){std::memcpy(m.data()+a,&v,sizeof v);};
    DeadeyePresentationContext c{77,111,5000,222,333,0x100000,0x200000};NativeLocalHero h;h.hero=0x02e0000000000003ULL;h.model=0x400000;h.modelId=19;h.localId=17;h.reference=0x410000;
    NativeRecallBinding b{};std::memcpy(b.magic,"OWRECL01",8);b.version=2;b.pid=77;b.creation=111;b.admin=0x300000;b.localId=17;b.modelId=19;b.model=h.model;b.script=0x500000;b.graph=0x600000;b.bag=0x660000;b.logger=0x700000;b.cast=0x630000;b.animation=0x640000;b.castVtable=c.base+0x1500590;b.animationVtable=c.base+0x15138c0;b.function=c.plugin+0x7acd0;
    const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};std::memcpy(b.prefix.data(),prefix,32);std::memcpy(m.data()+b.function,prefix,32);
    put(c.base+0x17b7f90,b.admin);put(h.reference+0x94,19u);put(h.model+0x28,b.admin);put(b.script+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(b.script+0x150,0x058000000000001aULL);put(b.script+0x160,b.graph);put(b.script+0x98,b.bag);
    put(b.graph+0x50,uintptr_t(0x610000));put(b.graph+0x58,1ULL);put(0x610000,uintptr_t(0x620000));put(0x610008,48ULL);put(0x620000+31*8,b.cast);put(0x620000+9*8,b.animation);put(b.cast,b.castVtable);put(b.animation,b.animationVtable);put(0x620008,uintptr_t(0x650000));put(0x650000,c.base+0x151c678);
    b.ammoScript=0x800000;b.ammoBag=0x810000;b.ammoGraph=0x820000;b.ammo=0x830000;b.maximum=0x840000;b.reloadDefinition=0x8d0000;
    put(b.ammoScript+0x150,0x0580000000000016ULL);put(b.ammoScript+0x160,b.ammoGraph);put(b.ammoScript+0x98,b.ammoBag);put(b.ammoScript+0x10,uintptr_t(0x860000));put(0x860450,uintptr_t(0x870000));put(0x870008,h.model);
    put(b.ammoBag,c.base+0x1607a90);put(b.ammoBag+0x3b8,b.ammoScript);put(b.ammoBag+0x3c0,uintptr_t(0x850000));
    put(b.ammo,c.base+0x1608248);put(b.maximum,c.base+0x1608248);put(b.ammo+0x80,b.ammoBag);put(b.maximum+0x80,b.ammoBag);put(b.ammo+0x98,0x0d80000000000035ULL);put(b.maximum+0x98,0x0d800000000000c6ULL);
    put(b.ammoBag+0xa0+5*0x30,uintptr_t(0x890000));put(b.ammoBag+0xa8+5*0x30,1u);put(b.ammoBag+0xac+5*0x30,1u);put(0x890000,0x0d80000000000035ULL);put(0x890008,b.ammo);
    put(b.ammoBag+0xa0+6*0x30,uintptr_t(0x8a0000));put(b.ammoBag+0xa8+6*0x30,1u);put(b.ammoBag+0xac+6*0x30,1u);put(0x8a0000,0x0d800000000000c6ULL);put(0x8a0008,b.maximum);
    put(b.ammoGraph+0x50,uintptr_t(0x8b0000));put(b.ammoGraph+0x58,1ULL);put(0x8b0000,uintptr_t(0x8c0000));put(0x8b0008,31ULL);put(0x8c0000+30*8,b.reloadDefinition);
    put(b.ammo+0xa0,22);put(b.ammo+0xac,2);put(b.maximum+0xa0,40);put(b.maximum+0xac,2);put(c.base+0x1608248+0x288,c.base+0xf5f740);
    const unsigned char setter[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};std::memcpy(m.data()+c.base+0xf5f740,setter,16);
    unsigned calls=0;auto notify=[&](auto fn,auto primitive,auto sync,auto script,const void* value,auto user){assert(fn==c.base+0xf5f740&&primitive==b.ammo&&sync==0x850000&&script==b.ammoScript&&user==b.ammo+0x88);calls++;std::memcpy(m.data()+primitive+0xa0,value,16);return true;};
    NativeRecallAmmo a;assert(a.restore(b,c,h,read,notify)&&calls==1&&a.restored==1);assert(a.restore(b,c,h,read,notify)&&calls==1);
    put(b.ammo+0xa0,20);put(b.maximum+0xa0,39);assert(!a.restore(b,c,h,read,notify)&&calls==1);put(b.maximum+0xa0,40);
    put(0x890000,123ULL);assert(!a.restore(b,c,h,read,notify));put(0x890000,0x0d80000000000035ULL);
    put(0x8c0000+30*8,0ULL);assert(!a.restore(b,c,h,read,notify));put(0x8c0000+30*8,b.reloadDefinition);
    auto wrong=h;wrong.modelId++;assert(!a.restore(b,c,wrong,read,notify)&&calls==1);
    std::cout<<"PASS: original typed magazine/max, reload membership, native Set&Notify, full-value no-op and stale-owner refusal\n";
}
