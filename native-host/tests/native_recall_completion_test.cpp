#include "../src/native_recall_completion.hpp"
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
    auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root){put(at,head);put(at+8,1ULL);put(head+8,root);put(head+25,uint8_t(1));};
    map(b.logger,0x710000,0x720000);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,b.script);
    map(0x720028,0x730000,0x740000);put(0x740000,uintptr_t(0x750000));put(0x740008,uintptr_t(0x730000));put(0x740010,uintptr_t(0x730000));put(0x740020,31u);put(0x740028,1000ULL);put(0x740030,uint8_t(1));
    put(0x750000,uintptr_t(0x760000));put(0x750008,uintptr_t(0x740000));put(0x750010,uintptr_t(0x730000));put(0x750020,9u);put(0x750028,1000ULL);put(0x750030,uint8_t(1));
    put(0x760000,uintptr_t(0x730000));put(0x760008,uintptr_t(0x750000));put(0x760010,uintptr_t(0x730000));put(0x760020,1u);put(0x760028,1000ULL);put(0x760030,uint8_t(1));
    unsigned calls=0;uint64_t clock=2900;auto invoke=[&](auto fn,auto script,int node,bool start){assert(fn==b.function&&script==b.script&&(node==31||node==1)&&!start);calls++;if(node==31){put(0x740028,clock);put(0x740030,uint8_t(1));put(0x760028,clock+1);put(0x760030,uint8_t(0));}else{put(0x760028,clock+20);put(0x760030,uint8_t(1));}};
    NativeRecallCompletion s;assert(!s.update(&b,c,h,read,invoke)); // baseline cannot end an old cast
    put(0x740028,2000ULL);put(0x740030,uint8_t(0));put(0x750028,2000ULL);put(0x750030,uint8_t(0));assert(!s.update(&b,c,h,read,invoke));
    c.now+=900;assert(!s.update(&b,c,h,read,invoke)); // wall time alone never ends it
    put(0x750028,2900ULL);put(0x750030,uint8_t(1));assert(!s.update(nullptr,c,h,read,invoke)); // temporary transport loss preserves admission
    assert(s.update(&b,c,h,read,invoke)&&calls==1&&s.completed==1);assert(!s.update(&b,c,h,read,invoke)&&calls==1);
    NativeRecallCompletionAck ack{};std::memcpy(ack.magic,"OWRECA01",8);ack.version=1;ack.pid=c.pid;ack.creation=c.creation;ack.generation=c.generation;ack.world=c.world;ack.modelId=h.modelId;ack.begin=2000;ack.wall=c.now;ack.phase=2;
    auto wrong=ack;wrong.world++;assert(!s.update(&b,&wrong,c,h,read,invoke)&&calls==1);wrong=ack;wrong.begin++;assert(!s.update(&b,&wrong,c,h,read,invoke));wrong=ack;wrong.wall=c.now-1001;assert(!s.update(&b,&wrong,c,h,read,invoke));
    assert(s.update(&b,&ack,c,h,read,invoke)&&calls==2&&s.historyCompleted==1);assert(!s.update(&b,&ack,c,h,read,invoke)&&calls==2);
    put(0x740028,3000ULL);put(0x740030,uint8_t(0));put(0x750028,3000ULL);put(0x750030,uint8_t(0));assert(!s.update(&b,c,h,read,invoke));
    c.world++;clock=3900;put(0x750028,3900ULL);put(0x750030,uint8_t(1));assert(s.update(&b,c,h,read,invoke)&&calls==3); // surviving native pawn cleaned; no MC authority
    assert(s.update(&b,c,h,read,invoke)&&calls==4&&s.historyCompleted==2); // cancelled world never waits for old MC results
    assert(!s.ammoDue);
    // Empty MC history may cancel an otherwise real original cast. phase3
    // must wait for Anim End, release only this cast, and never refill ammo.
    put(0x740028,4000ULL);put(0x740030,uint8_t(0));put(0x750028,4000ULL);put(0x750030,uint8_t(0));
    auto cancelled=ack;cancelled.world=c.world;cancelled.begin=4000;cancelled.wall=c.now;cancelled.phase=3;
    assert(!s.update(&b,&cancelled,c,h,read,invoke)&&calls==4&&!s.ammoDue);
    c.now+=1000;cancelled.wall=c.now;clock=4900;put(0x750028,4900ULL);put(0x750030,uint8_t(1));
    assert(s.update(&b,&cancelled,c,h,read,invoke)&&calls==5&&s.completed==3&&!s.ammoDue);
    auto rejected=[&](auto mutate){auto receipt=cancelled;mutate(receipt);assert(!s.update(&b,&receipt,c,h,read,invoke)&&calls==5&&!s.ammoDue);};
    rejected([](auto& receipt){receipt.pid++;});rejected([](auto& receipt){receipt.creation++;});
    rejected([](auto& receipt){receipt.generation++;});rejected([](auto& receipt){receipt.world++;});
    rejected([](auto& receipt){receipt.modelId++;});rejected([](auto& receipt){receipt.begin++;});
    rejected([&](auto& receipt){receipt.wall=c.now-1001;});rejected([&](auto& receipt){receipt.wall=c.now+51;});
    rejected([](auto& receipt){receipt.phase=1;});rejected([](auto& receipt){receipt.reserved=1;});
    rejected([](auto& receipt){receipt.version++;});rejected([](auto& receipt){receipt.magic[0]^=1;});
    assert(!s.update(&b,&ack,c,h,read,invoke)&&calls==5); // old successful cast is not this cancellation
    assert(s.update(&b,&cancelled,c,h,read,invoke)&&calls==6&&s.historyCompleted==3&&!s.ammoDue);
    assert(!s.update(&b,&cancelled,c,h,read,invoke)&&calls==6&&!s.ammoDue); // no duplicate cleanup
    // A later successful Recall still follows the normal phase2/ammo path.
    put(0x740028,5000ULL);put(0x740030,uint8_t(0));put(0x750028,5000ULL);put(0x750030,uint8_t(0));
    assert(!s.update(&b,c,h,read,invoke));clock=5900;put(0x750028,5900ULL);put(0x750030,uint8_t(1));
    assert(s.update(&b,c,h,read,invoke)&&calls==7);
    auto successful=cancelled;successful.begin=5000;successful.phase=2;
    assert(s.update(&b,&successful,c,h,read,invoke)&&calls==8&&s.historyCompleted==4&&s.ammoDue);
    auto bad=b;bad.creation++;assert(!s.update(&bad,c,h,read,invoke));bad=b;bad.prefix[0]^=1;assert(!s.update(&bad,c,h,read,invoke));
    std::cout<<"PASS: Recall animation End, exact identity, dimension cleanup, phase3 without ammo, stale receipt refusal and exactly-once completion\n";
}
