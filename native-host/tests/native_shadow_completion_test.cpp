#include "../src/native_shadow_completion.hpp"
#include <vector>
#include <map>
#include <functional>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> m(0x2000000);
    auto read=[&](uintptr_t a,void* out,size_t n){if(a+n>m.size())return false;std::memcpy(out,m.data()+a,n);return true;};
    auto put=[&](uintptr_t a,auto v){std::memcpy(m.data()+a,&v,sizeof v);};
    DeadeyePresentationContext c{77,111,5000,222,333,0x100000,0x200000};NativeLocalHero h;h.hero=0x02e0000000000002ULL;h.model=0x400000;h.modelId=19;h.localId=17;h.reference=0x410000;
    NativeShadowBinding b{};std::memcpy(b.magic,"OWSHAD01",8);b.version=2;b.pid=77;b.creation=111;b.admin=0x300000;b.localId=17;b.modelId=19;b.model=h.model;b.script=0x500000;b.graph=0x600000;b.bag=0x660000;b.logger=0x700000;b.cast=0x630000;b.animation=0x640000;b.castVtable=c.base+0x150b738;b.animationVtable=c.base+0x15138c0;b.function=c.plugin+0x7acd0;b.query=0x641000;b.confirm=0x642000;b.arrival=0x643000;b.waitOut=0x644000;b.waitIn=0x645000;b.aimAnimation=0x646000;b.priority=0x647000;b.ready=0x648000;b.action=c.plugin+0x7abc0;
    const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};std::memcpy(b.prefix.data(),prefix,32);std::memcpy(m.data()+b.function,prefix,32);
    put(c.base+0x17b7f90,b.admin);put(h.reference+0x94,19u);put(h.model+0x28,b.admin);put(b.script+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(b.script+0x150,0x05800000000000f2ULL);put(b.script+0x160,b.graph);put(b.script+0x98,b.bag);
    put(b.graph+0x50,uintptr_t(0x610000));put(b.graph+0x58,1ULL);put(0x610000,uintptr_t(0x620000));put(0x610008,89ULL);
    for(auto n:std::array<std::array<uint64_t,3>,10>{{{52,b.cast,0x150b738},{25,b.animation,0x15138c0},{2,b.query,0x151a868},{47,b.confirm,0x1517770},{26,b.arrival,0x15138c0},{17,b.waitOut,0x150bd08},{18,b.waitIn,0x150bd08},{53,b.aimAnimation,0x15138c0},{16,b.priority,0x150b738},{5,b.ready,0x1500590}}}){put(0x620000+n[0]*8,n[1]);put(n[1],c.base+n[2]);}
    const unsigned char actionCode[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xb9,0x60,1,0,0,0x48,0x8b,0xd9,0x48,0x63,0xf2,0x48,0x83,0x7f,0x50};std::memcpy(b.actionPrefix.data(),actionCode,32);std::memcpy(m.data()+b.action,actionCode,32);put(0x620000+60*8,uintptr_t(0x649000));put(0x649000,c.base+0x1519170);
    auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root,uint64_t count){put(at,head);put(at+8,count);put(head+8,root);put(head+25,uint8_t(1));};
    map(b.logger,0x710000,0x720000,1);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,b.script);
    std::vector<unsigned> keys{2,17,18,25,26,47,52};std::map<unsigned,uintptr_t> rows;
    std::function<uintptr_t(int,int,uintptr_t)> tree=[&](int lo,int hi,uintptr_t parent){if(lo>=hi)return uintptr_t(0x730000);int mid=(lo+hi)/2;uintptr_t at=0x740000+mid*0x100;put(at+8,parent);put(at+32,keys[mid]);put(at+40,100ULL);put(at+48,uint8_t(1));rows[keys[mid]]=at+40;put(at,tree(lo,mid,at));put(at+16,tree(mid+1,hi,at));return at;};
    auto root=tree(0,7,0x730000);map(0x720028,0x730000,root,7);
    auto state=[&](unsigned key,uint64_t tick,bool active){put(rows[key],tick);put(rows[key]+8,uint8_t(!active));};
    unsigned calls=0;auto invoke=[&](auto fn,auto script,int node,bool start){assert(script==b.script);calls++;if(node==60){assert(fn==b.action);return;}assert(fn==b.function);if(node==2){assert(!start);state(2,301,false);}else if(node==25){assert(start);state(25,301,true);}else if(node==26){assert(start);state(26,401,true);}else assert((node==16&&!start)||(node==53&&!start)||(node==5&&start));};
    NativeShadowCompletion gate;assert(!gate.update(&b,nullptr,c,h,read,invoke));state(2,200,true);state(47,300,false);
    NativeShadowAck ack{};std::memcpy(ack.magic,"OWSHDA01",8);ack.version=1;ack.pid=c.pid;ack.creation=c.creation;ack.generation=c.generation;ack.world=c.world;ack.model=h.modelId;ack.aim=200;ack.confirm=300;ack.wall=c.now;ack.phase=1;
    auto bad=ack;bad.world++;assert(!gate.update(&b,&bad,c,h,read,invoke));bad=ack;bad.wall-=251;assert(!gate.update(&b,&bad,c,h,read,invoke));
    assert(gate.update(&b,&ack,c,h,read,invoke)&&calls==4&&gate.admissions==1);assert(!gate.update(&b,&ack,c,h,read,invoke)&&calls==4);
    c.now+=10000;assert(!gate.update(&b,nullptr,c,h,read,invoke)); // wall time never completes animation
    state(25,400,false);ack.phase=2;ack.wall=c.now;assert(gate.update(&b,&ack,c,h,read,invoke)&&calls==5);assert(!gate.update(&b,&ack,c,h,read,invoke));
    state(26,500,false);state(18,500,false);assert(!gate.update(nullptr,&ack,c,h,read,invoke));assert(gate.update(&b,&ack,c,h,read,invoke)&&calls==7&&gate.completed==1);assert(!gate.update(&b,&ack,c,h,read,invoke)&&calls==7);
    auto binding=b;binding.creation++;assert(!gate.update(&binding,&ack,c,h,read,invoke));
    NativeShadowCompletion unadmitted;state(2,600,true);state(47,700,false);assert(!unadmitted.update(&b,nullptr,c,h,read,invoke));c.world++;
    assert(unadmitted.update(&b,nullptr,c,h,read,invoke)&&unadmitted.cancelledAim==1&&unadmitted.admissions==0&&calls==9);
    assert(!unadmitted.update(&b,&ack,c,h,read,invoke)&&calls==9); // old-world receipt cannot admit a warp
    std::cout<<"PASS: Shadow Step real confirm plus MC receipt, exact owner/world/freshness, actual two animation Ends, no wall-time completion/replay\n";
}
