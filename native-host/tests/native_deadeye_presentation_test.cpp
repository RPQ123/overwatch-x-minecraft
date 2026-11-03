#include "../src/native_deadeye_presentation.hpp"
#include <vector>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> m(0x2000000);
    auto read=[&](uintptr_t at,void* out,size_t n){if(at+n>m.size())return false;std::memcpy(out,m.data()+at,n);return true;};
    auto put=[&](uintptr_t at,auto v){std::memcpy(m.data()+at,&v,sizeof v);};
    DeadeyePresentationContext c{77,111,5000,222,333,0x100000,0x200000};
    NativeLocalHero h;h.hero=0x02e0000000000042ULL;h.model=0x400000;h.modelId=19;h.reference=0x410000;
    DeadeyePresentationRequest r{};std::memcpy(r.magic,"OWDEYE01",8);r.version=2;r.pid=77;r.creation=111;r.sequence=1;r.wall=5000;r.generation=222;r.world=333;r.admin=0x300000;r.model=h.model;r.modelId=19;r.script=0x500000;r.graph=0x600000;r.function=c.plugin+0x7acd0;r.logger=0x700000;r.begin=1000;r.node=69;r.ordinal=1;
    const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};std::memcpy(r.prefix.data(),prefix,32);std::memcpy(m.data()+r.function,prefix,32);
    put(c.base+0x17b7f90,r.admin);put(h.reference+0x94,19u);put(h.model+0x28,r.admin);put(r.script+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(r.script+0x150,0x058000000000022fULL);put(r.script+0x160,r.graph);
    put(r.graph+0x50,uintptr_t(0x610000));put(r.graph+0x58,1ULL);put(0x610000,uintptr_t(0x620000));put(0x610008,101ULL);put(0x620000+69*8,uintptr_t(0x630000));put(0x630068,69u);put(0x630100,uintptr_t(0x640000));put(0x640018,0x0c8000000000019fULL);
    put(0x620000+72*8,uintptr_t(0x650000));put(0x650000,c.base+0x150bd08);put(0x650100,uintptr_t(0x660000));put(0x660000,c.base+0x1558ba8);put(0x660010,.1333f);
    // The supplied logger's two-level map, containing native Q and animation.
    auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root,unsigned count){put(at,head);put(at+8,uint64_t(count));put(head+8,root);put(head+25,uint8_t(1));};
    map(r.logger,0x710000,0x720000,1);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,r.script);
    map(0x720028,0x730000,0x740000,2);put(0x740000,uintptr_t(0x730000));put(0x740008,uintptr_t(0x730000));put(0x740010,uintptr_t(0x750000));put(0x740020,18u);put(0x740028,1000ULL);put(0x740030,uint8_t(0));
    put(0x750000,uintptr_t(0x730000));put(0x750008,uintptr_t(0x740000));put(0x750010,uintptr_t(0x730000));put(0x750020,69u);put(0x750028,900ULL);put(0x750030,uint8_t(1));
    unsigned invoked=0;uint64_t nextNative=1001;auto invoke=[&](auto fn,auto script,int node,bool start){assert(fn==r.function&&script==r.script&&node==69&&start);invoked++;put(0x750028,nextNative);nextNative+=1000;put(0x750030,uint8_t(0));};
    NativeDeadeyePresentation p;assert(p.update(&r,c,h,read,invoke)&&invoked==1&&p.ack.phase==1);
    r.acknowledged=1;assert(!p.update(&r,c,h,read,invoke)&&invoked==1);put(0x750028,1330ULL);put(0x750030,uint8_t(1));c.now=5330;r.wall=c.now;
    assert(p.update(&r,c,h,read,invoke)&&p.ack.phase==2&&p.completed==1);
    c.now=5530;r.wall=c.now;
    assert(p.update(&r,c,h,read,invoke)&&p.ack.phase==2&&p.ack.wall==5530&&invoked==1&&p.completed==1);
    auto wrongReceipt=r;wrongReceipt.ordinal++;c.now+=40;
    assert(!p.update(&wrongReceipt,c,h,read,invoke)&&invoked==1);
    r.sequence=2;r.ordinal=2;r.wall=c.now;auto bad=r;bad.world++;
    assert(!p.update(&bad,c,h,read,invoke)&&invoked==1);bad=r;bad.node=68;assert(!p.update(&bad,c,h,read,invoke));bad=r;bad.wall=5000;assert(!p.update(&bad,c,h,read,invoke));
    bad=r;bad.prefix[0]^=1;assert(!p.update(&bad,c,h,read,invoke));put(0x740030,uint8_t(1));assert(!p.update(&r,c,h,read,invoke));put(0x740030,uint8_t(0));
    assert(p.update(&r,c,h,read,invoke)&&invoked==2);auto changed=h;changed.modelId++;
    assert(p.update(&r,c,changed,read,invoke)&&p.ack.phase==3&&invoked==2);
    NativeDeadeyePresentation fast;r.sequence=1;r.ordinal=1;c.now=6000;r.wall=c.now;
    put(0x750028,2900ULL);put(0x750030,uint8_t(1));unsigned starts=0,stops=0;uint64_t nativeClock=3000;
    auto cycle=[&](auto fn,auto script,int node,bool start){assert(fn==r.function&&script==r.script&&node==69);if(start)starts++;else stops++;put(0x750028,nativeClock);put(0x750030,uint8_t(!start));};
    assert(fast.update(&r,c,h,read,cycle)&&starts==1&&stops==0);
    r.sequence=2;r.ordinal=2;c.now=6100;r.wall=c.now;nativeClock=3100;
    assert(!fast.update(&r,c,h,read,cycle)&&starts==1&&stops==0);
    c.now=6134;r.wall=c.now;nativeClock=3134;
    assert(fast.update(&r,c,h,read,cycle)&&starts==2&&stops==1&&fast.completed==1&&fast.ack.phase==1);
    assert(!fast.update(&r,c,h,read,cycle)&&starts==2);
    r.sequence=3;r.ordinal=3;r.acknowledged=2;c.now=6268;r.wall=c.now;nativeClock=3268;
    put(0x660010,.001f);assert(!fast.update(&r,c,h,read,cycle)&&starts==2);put(0x660010,.1333f);
    assert(fast.update(&r,c,h,read,cycle)&&starts==3&&stops==2&&fast.completed==2);
    r.acknowledged=3;put(0x750028,3598ULL);put(0x750030,uint8_t(1));c.now=6598;r.wall=c.now;
    assert(fast.update(&r,c,h,read,cycle)&&fast.ack.phase==2&&fast.completed==3);
    // An End may arrive before the worker/MC observes Begin. Preserve the
    // original fresh Begin without replaying or extending its damage timestamp.
    NativeDeadeyePresentation early;r.sequence=20;r.ordinal=1;r.acknowledged=19;c.now=7000;r.wall=c.now;nativeClock=4000;
    put(0x750028,3999ULL);put(0x750030,uint8_t(1));assert(early.update(&r,c,h,read,cycle));
    put(0x750028,4001ULL);put(0x750030,uint8_t(1));c.now=7016;r.wall=c.now;
    assert(!early.update(&r,c,h,read,cycle)&&early.ack.phase==1&&early.ack.wall==7000&&early.completed==0);
    auto wrongAck=r;wrongAck.world++;wrongAck.acknowledged=20;assert(!early.update(&wrongAck,c,h,read,cycle)&&early.ack.phase==1);
    r.acknowledged=20;c.now=7060;r.wall=c.now;assert(early.update(&r,c,h,read,cycle)&&early.ack.phase==2&&early.completed==1);
    // A six-round revolver is not a six-target cap on the adapted target list.
    // Retain every sequence/owner/ack/cadence guard past the seventh target.
    NativeDeadeyePresentation crowd;r.sequence=100;r.ordinal=1;r.acknowledged=99;c.now=10000;r.wall=c.now;nativeClock=10000;
    put(0x750028,9999ULL);put(0x750030,uint8_t(1));assert(crowd.update(&r,c,h,read,cycle));
    for(unsigned i=2;i<=64;i++){
        r.acknowledged=r.sequence;r.sequence++;r.ordinal=i;c.now+=134;r.wall=c.now;nativeClock+=134;
        assert(crowd.update(&r,c,h,read,cycle)&&crowd.ack.ordinal==i&&crowd.ack.phase==1);
    }
    r.acknowledged=r.sequence;r.sequence++;r.ordinal=65;c.now+=134;r.wall=c.now;
    assert(!crowd.update(&r,c,h,read,cycle));
    std::cout<<"PASS: original Wait72 cadence, acknowledged1..64 target loop, final End, replay/order and identity guards\n";
}
