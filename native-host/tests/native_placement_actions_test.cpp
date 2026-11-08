#include "../src/native_placement_actions.hpp"
#include <vector>
#include <map>
#include <functional>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> m(0x2000000);
    auto read=[&](uintptr_t at,void* out,size_t n){if(at+n>m.size())return false;std::memcpy(out,m.data()+at,n);return true;};
    auto put=[&](uintptr_t at,auto v){std::memcpy(m.data()+at,&v,sizeof v);};
    DeadeyePresentationContext c{33,44,2000,55,66,0x100000,0x200000};
    NativeLocalHero h;h.hero=0x02e00000000000ddULL;h.model=0x400000;h.modelId=19;h.localId=17;h.reference=0x410000;h.heroInfo=0x420000;h.controller=0x430000;
    uintptr_t admin=0x300000,script=0x500000,graph=0x600000,bag=0x660000,items=0x620000;
    put(c.base+0x17b7f90,admin);put(admin+0x220,h.localId);put(h.reference+0x94,h.modelId);put(h.reference+8,h.controller);put(h.model+0x28,admin);put(h.heroInfo+0x98,h.hero);
    put(script+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(script+0x150,0x0580000000000622ULL);put(script+0x160,graph);put(script+0x98,bag);
    put(graph+0x50,uintptr_t(0x610000));put(graph+0x58,1ULL);put(0x610000,items);put(0x610008,104ULL);put(bag,c.base+0x1607a90);
    put(bag+0xa0,uintptr_t(0x680000));put(bag+0xa8,2);put(bag+0xac,2);
    constexpr uint64_t cooldown=0x0d8000000000003dULL,configured=0x0d800000000001d8ULL;
    for(unsigned i=0;i<2;i++){auto rid=i?configured:cooldown;uintptr_t primitive=0x690000+i*0x1000;put(0x680000+i*16,rid);put(0x680008+i*16,primitive);put(primitive,c.base+0x1608248);put(primitive+0x80,bag);put(primitive+0x98,rid);put(primitive+0xa0,i?10:0);put(primitive+0xac,2);}
    unsigned typeCount=0;
    auto type=[&](uintptr_t object,uint32_t kind){uintptr_t vt=0x900000+typeCount*0x1000,fn=vt+0x100,meta=vt+0x200;typeCount++;put(object,vt);put(vt+0x28,fn);std::array<unsigned char,8> code{0x48,0x8d,5,0,0,0,0,0xc3};int32_t delta=int32_t(meta-fn-7);std::memcpy(code.data()+3,&delta,4);std::memcpy(m.data()+fn,code.data(),8);put(meta+0x50,kind);};
    auto ref=[&](uintptr_t object,uint64_t rid){type(object,0xf8cc195d);put(object+16,object+0x100);put(object+24,1ULL);put(object+0x100,object+0x200);put(object+0x108,1ULL);put(object+0x200,~0ULL);put(object+0x208,rid);};
    uintptr_t init=0x800000,set=0x801000,literal=0x802000;
    type(init,0x4698e4b6);type(set,0x4698e4b6);type(literal,0x3ae7427e);put(literal+16,10);
    ref(0x803000,configured);ref(0x804000,cooldown);ref(0x805000,configured);
    put(init+0x90,uintptr_t(0x803000));put(init+0xa0,literal);put(set+0x90,uintptr_t(0x804000));put(set+0xa0,uintptr_t(0x805000));
    put(items+13*8,init);put(items+29*8,set);put(items+34*8,init);put(items+51*8,set);put(items+81*8,uintptr_t(0x806000));type(0x806000,0xf7d6498c);
    type(0x807000,0xf53c5da8);type(0x808000,0x72509d3b);type(0x809000,0x6e81f6d4);
    for(int node:{28,55,83})put(items+node*8,uintptr_t(0x807000));
    put(items+2*8,uintptr_t(0x808000));put(items+22*8,uintptr_t(0x809000));
    put(items+50*8,uintptr_t(0x80a000));type(0x80a000,0xa7213568);put(items+61*8,uintptr_t(0x80b000));type(0x80b000,0x7fb4bf64);put(items+84*8,set);
    put(graph+0x60,uintptr_t(0x670000));put(graph+0x68,1ULL);put(0x670000,uintptr_t(0x671000));put(0x670008,1ULL);put(0x671000,uintptr_t(0x807000));
    put(script+0xa0,uintptr_t(0x672000));put(script+0xa8,1);put(script+0xac,1);put(0x672000,uintptr_t(0x673000));
    put(0x673000,c.base+0x15d7c98);put(0x673070,0);put(0x673078,script);put(0x673150,0.f);
    const unsigned char action[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xb9,0x60,1,0,0,0x48,0x8b,0xd9,0x48,0x63,0xf2,0x48,0x83,0x7f,0x50};
    const unsigned char stateCode[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
    std::memcpy(m.data()+c.plugin+0x7abc0,action,32);std::memcpy(m.data()+c.plugin+0x7acd0,stateCode,32);
    auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root,uint64_t count){put(at,head);put(at+8,count);put(head+8,root);put(head+25,uint8_t(1));};
    uintptr_t logger=c.plugin+0x2d04c0;map(logger,0x710000,0x720000,1);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,script);
    std::vector<unsigned> keys{2,22,28,29,50,51,55,61,81,83,84};std::map<unsigned,uintptr_t> rows;
    std::function<uintptr_t(int,int,uintptr_t)> tree=[&](int lo,int hi,uintptr_t parent){if(lo>=hi)return uintptr_t(0x730000);int mid=(lo+hi)/2;uintptr_t at=0x740000+mid*0x100;put(at+8,parent);put(at+32,keys[mid]);put(at+40,100ULL);put(at+48,uint8_t(1));rows[keys[mid]]=at+40;put(at,tree(lo,mid,at));put(at+16,tree(mid+1,hi,at));return at;};
    auto root=tree(0,int(keys.size()),0x730000);map(0x720028,0x730000,root,keys.size());
    auto state=[&](unsigned node,uint64_t tick,bool active){put(rows[node],tick);put(rows[node]+8,uint8_t(!active));};state(2,300,true);state(22,300,true);
    PlacementActionRequest p{};std::memcpy(p.magic,"OWPLRQ01",8);p.version=1;p.pid=c.pid;p.creation=c.creation;p.sequence=1000;p.wall=c.now;p.generation=c.generation;p.world=c.world;p.model=h.model;p.modelId=h.modelId;p.script=script;p.graph=graph;p.logger=logger;p.token=300;p.kind=1;
    unsigned calls=0;std::vector<int> queued;
    auto invoke=[&](uintptr_t fn,uintptr_t owner,int node,bool start){assert(owner==script);++calls;
        if(fn==c.plugin+0x7acd0){assert(!start);queued.push_back(node);}
        else{assert(fn==c.plugin+0x7abc0&&start&&(node==29||node==51||node==84));put(0x6900a0,p.kind==4?12:p.kind==1?10:8);state(node,p.token+1,false);}};
    auto flush=[&](bool nativeCounter){for(int node:queued){state(node,p.token+1,false);if(node==50)state(22,p.token+1,false);if(nativeCounter&&(node==2||node==22||node==28||node==55||node==50))put(0x673150,p.kind==1?10.f:8.f);}queued.clear();};
    auto write=[&](uintptr_t at,const void* data,size_t n){assert(at>=0x673000&&at<0x674000);std::memcpy(m.data()+at,data,n);return true;};
    NativePlacementActions gate;
    assert(!gate.update(&p,c,h,read,invoke,write)&&calls==2&&gate.ack.phase==0); // VM Stop is queued, not an immediate End
    flush(true);c.now+=20;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==1&&gate.ack.remaining==10);
    c.now+=60;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&calls==2); // repeated mailbox never resets cooldown
    ++p.sequence;put(0x673150,9.5f);assert(!gate.update(&p,c,h,read,invoke,write)&&calls==2); // same original preview cannot be reissued under a new sequence
    NativePlacementActions alreadyNative;assert(alreadyNative.update(&p,c,h,read,invoke,write)&&calls==2&&alreadyNative.ack.remaining==9.5f); // adopt actual original counter on first request
    ++p.sequence;p.token=500;state(2,500,true);auto refuse=[&](){assert(!gate.update(&p,c,h,read,invoke,write)&&calls==2);};
    p.world++;refuse();p.world--;p.creation++;refuse();p.creation--;p.wall-=251;refuse();p.wall=c.now;
    put(0x805208,0x0d80000000000099ULL);refuse();put(0x805208,configured);put(literal+16,11);refuse();put(literal+16,10);
    put(c.plugin+0x7abc0,uint8_t(0xcc));refuse();put(c.plugin+0x7abc0,uint8_t(0x48));put(h.reference+0x94,20u);refuse();put(h.reference+0x94,h.modelId);
    put(0x673150,0.f);state(28,300,true);auto fail=[&](auto...){++calls;};
    assert(!gate.update(&p,c,h,read,fail,write)&&calls==4);c.now+=301;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==3);
    c.now+=60;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&calls==4&&gate.ack.phase==3);
    ++p.sequence;p.kind=2;h.hero=0x02e0000000000006ULL;put(h.heroInfo+0x98,h.hero);put(script+0x150,0x05800000000000f4ULL);put(0x610008,60ULL);put(literal+16,8);put(0x6910a0,8);
    p.token=700;state(22,700,true);assert(!gate.update(&p,c,h,read,invoke,write)&&calls==6);flush(false);c.now+=90;p.wall=c.now;
    assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==1&&gate.ack.duration==8&&gate.ack.remaining==8&&gate.counterStarts==1); // measured actual counter fallback
    ++p.sequence;p.token=1000;state(22,1000,true);put(0x673150,0.f);put(0x673144,uint8_t(1));put(0x673146,uint8_t(1));
    assert(!gate.update(&p,c,h,read,invoke,write)&&calls==8);flush(false);c.now+=90;p.wall=c.now;bool failOnce=true;
    auto partialWrite=[&](uintptr_t at,const void* data,size_t n){if(at==0x673146&&failOnce){failOnce=false;return false;}return write(at,data,n);};
    assert(gate.update(&p,c,h,read,invoke,partialWrite)&&gate.ack.phase==3);float restored=1;read(0x673150,&restored,4);assert(restored==0&&m[0x673144]==1&&m[0x673146]==1);
    c.now+=60;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&calls==8&&gate.ack.phase==3); // write failure rolls back and is terminal
    ++p.sequence;p.kind=3;p.token=1200;h.hero=0x02e000000000000aULL;put(h.heroInfo+0x98,h.hero);put(script+0x150,0x058000000000005aULL);put(0x610008,91ULL);state(81,1200,true);
    assert(!gate.update(&p,c,h,read,invoke,write)&&calls==9);flush(false);state(81,1201,false);c.now+=20;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==1&&gate.ack.remaining==12);c.now+=60;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&calls==9);
    ++p.sequence;p.token=1400;state(81,1500,true);assert(!gate.update(&p,c,h,read,invoke,write)&&calls==9); // cannot stop a different cast
    // T6: ending only cosmetic22 must not acknowledge a still-held turret.
    ++p.sequence;p.kind=2;p.token=1700;h.hero=0x02e0000000000006ULL;put(h.heroInfo+0x98,h.hero);put(script+0x150,0x05800000000000f4ULL);put(0x610008,60ULL);put(literal+16,8);put(0x6910a0,8);put(0x673150,0.f);state(22,1700,true);state(50,1700,true);
    assert(!gate.update(&p,c,h,read,invoke,write)&&calls==11);state(22,1701,false);put(0x673150,8.f);c.now+=20;p.wall=c.now;
    assert(!gate.update(&p,c,h,read,invoke,write)); // original preview parent still holding
    flush(false);c.now+=20;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==1&&calls==11);
    // T6: every actual native fire gets12s before MC pull, even a later miss.
    ++p.sequence;p.kind=4;p.token=2000;h.hero=0x02e000000000000aULL;put(h.heroInfo+0x98,h.hero);put(script+0x150,0x058000000000005aULL);put(0x610008,91ULL);put(literal+16,12);put(0x6910a0,12);put(0x673150,0.f);state(81,2000,true);state(61,2001,true);
    assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==1&&gate.ack.remaining==12&&calls==12&&m[0x673144]==1&&m[0x673146]==1);
    put(0x673150,11.4f);c.now+=60;p.wall=c.now;assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.remaining==11.4f&&calls==12);
    ++p.sequence;p.kind=3;assert(!gate.update(&p,c,h,read,invoke,write)&&calls==13);flush(false);put(0x673150,10.9f);c.now+=20;p.wall=c.now;
    assert(gate.update(&p,c,h,read,invoke,write)&&gate.ack.phase==1&&gate.ack.remaining==10.9f&&calls==13);
    ++p.sequence;p.kind=4;p.token=2100;state(81,2100,true);state(61,2101,true);assert(!gate.update(&p,c,h,read,invoke,write)&&calls==13); // old cooldown blocks another cast
    c.now+=500;assert(!gate.update(nullptr,c,h,read,invoke,write));float timed=0;read(0x673150,&timed,4);assert(std::abs(timed-10.4f)<.001f); // still ticks after mailbox clear
    c.generation++;c.now+=500;assert(!gate.update(nullptr,c,h,read,invoke,write));read(0x673150,&timed,4);assert(std::abs(timed-10.4f)<.001f&&!gate.grappleClock.state); // cannot clock another native session
    std::cout<<"PASS: T6 original turret selector50 End before receipt;grapple fire12s,Begin/finish separation,miss/arrival/cancel,replay and running-counter guards\n";
    std::cout<<"PASS: original Mei10/Torb8,queued-VM End/real ability counter/readback,existing cooldown adoption,no reset/replay,failed-call terminal ack,scope/type/code guards,Widow current-stack cancel\n";
}
