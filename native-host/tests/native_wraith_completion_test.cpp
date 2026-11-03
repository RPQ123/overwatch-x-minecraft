#include "../src/native_wraith_completion.hpp"
#include <vector>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> m(0x2000000);
    auto read=[&](uintptr_t a,void* out,size_t n){if(a+n>m.size())return false;std::memcpy(out,m.data()+a,n);return true;};
    auto put=[&](uintptr_t a,auto v){std::memcpy(m.data()+a,&v,sizeof v);};
    DeadeyePresentationContext c{77,111,5000,222,333,0x100000,0x200000};NativeLocalHero h;h.hero=0x02e0000000000002ULL;h.model=0x400000;h.modelId=19;h.localId=17;h.reference=0x410000;
    NativeWraithBinding b{};std::memcpy(b.magic,"OWWRTH01",8);b.version=1;b.pid=77;b.creation=111;b.admin=0x300000;b.localId=17;b.modelId=19;b.model=h.model;b.script=0x500000;b.graph=0x600000;b.bag=0x660000;b.logger=0x700000;b.cast=0x630000;b.animation=0x640000;b.castVtable=c.base+0x1500590;b.animationVtable=c.base+0x15138c0;b.function=c.plugin+0x7acd0;
    const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};std::memcpy(b.prefix.data(),prefix,32);std::memcpy(m.data()+b.function,prefix,32);
    put(c.base+0x17b7f90,b.admin);put(h.reference+0x94,19u);put(h.model+0x28,b.admin);put(b.script+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(b.script+0x150,0x0580000000000020ULL);put(b.script+0x160,b.graph);put(b.script+0x98,b.bag);
    put(b.graph+0x50,uintptr_t(0x610000));put(b.graph+0x58,1ULL);put(0x610000,uintptr_t(0x620000));put(0x610008,28ULL);put(0x620000+20*8,b.cast);put(0x620000+3*8,b.animation);put(b.cast,b.castVtable);put(b.animation,b.animationVtable);put(0x620008,uintptr_t(0x650000));put(0x650000,c.base+0x151c678);
    auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root){put(at,head);put(at+8,1ULL);put(head+8,root);put(head+25,uint8_t(1));};
    map(b.logger,0x710000,0x720000);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,b.script);
    map(0x720028,0x730000,0x740000);put(0x740000,uintptr_t(0x750000));put(0x740008,uintptr_t(0x730000));put(0x740010,uintptr_t(0x730000));put(0x740020,20u);put(0x740028,1000ULL);put(0x740030,uint8_t(1));
    put(0x750000,uintptr_t(0x760000));put(0x750008,uintptr_t(0x740000));put(0x750010,uintptr_t(0x730000));put(0x750020,3u);put(0x750028,1000ULL);put(0x750030,uint8_t(1));
    put(0x760000,uintptr_t(0x730000));put(0x760008,uintptr_t(0x750000));put(0x760010,uintptr_t(0x730000));put(0x760020,1u);put(0x760028,1000ULL);put(0x760030,uint8_t(1));
    put(0x760020,2u);
    put(0x620010,uintptr_t(0x670000));put(0x670000,c.base+0x151c748);

    put(0x620020,uintptr_t(0x680000));put(0x680000,c.base+0x150bd08);
    put(0x750010,uintptr_t(0x770000));put(0x770000,uintptr_t(0x730000));put(0x770008,uintptr_t(0x750000));put(0x770010,uintptr_t(0x730000));put(0x770020,4u);put(0x770028,2000ULL);put(0x770030,uint8_t(0));
    unsigned calls=0;auto invoke=[&](auto fn,auto script,int node,bool start){assert(fn==b.function&&script==b.script&&(node==20||node==2)&&!start);if(node==2){put(0x760028,2001ULL);put(0x760030,uint8_t(1));}else{calls++;put(0x740028,2900ULL);put(0x740030,uint8_t(1));}};
    NativeWraithCompletion gate;assert(!gate.update(&b,c,h,read,invoke));
    put(0x740028,2000ULL);put(0x740030,uint8_t(0));put(0x750028,2000ULL);put(0x750030,uint8_t(0));put(0x760028,2000ULL);put(0x760030,uint8_t(0));assert(gate.update(&b,c,h,read,invoke)&&gate.starts==1);
    c.now+=10000;assert(!gate.update(&b,c,h,read,invoke)); // no wall-time synthetic End
    c.world++;put(0x750028,2900ULL);put(0x750030,uint8_t(1));assert(!gate.update(nullptr,c,h,read,invoke));
    assert(!gate.update(&b,c,h,read,invoke));put(0x770028,2900ULL);put(0x770030,uint8_t(1));
    assert(gate.update(&b,c,h,read,invoke)&&calls==1&&gate.completed==1);assert(!gate.update(&b,c,h,read,invoke)&&calls==1);
    auto bad=b;bad.creation++;assert(!gate.update(&bad,c,h,read,invoke));bad=b;bad.prefix[0]^=1;assert(!gate.update(&bad,c,h,read,invoke));
    NativeWraithCompletion reconnect;put(0x740030,uint8_t(0));assert(!reconnect.update(&b,c,h,read,invoke)&&calls==1); // a baseline never ends an old cast
    std::cout<<"PASS: exact Wraith owner, real animation End, native world cleanup, transport gaps, no wall-time completion or replay\n";
}
