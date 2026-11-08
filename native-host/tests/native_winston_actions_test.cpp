#include "../src/native_winston_actions.hpp"
#include "../src/native_winston_presentation.hpp"
#include <vector>
#include <map>
#include <functional>
#include <cassert>
#include <iostream>
using namespace passthrough;
struct Fixture {
    std::vector<unsigned char> memory=std::vector<unsigned char>(0x2000000);
    DeadeyePresentationContext c{33,44,2000,55,66,0x100000,0x200000};NativeLocalHero h;
    uintptr_t script=0x500000,graph=0x600000,bag=0x660000,items=0x620000;unsigned types=0,calls=0;int kind;
    std::map<int,uintptr_t> rows;
    PlacementActionRequest p{};NativeWinstonActions gate;
    template<class T> void put(uintptr_t at,T v){std::memcpy(memory.data()+at,&v,sizeof v);}
    bool read(uintptr_t at,void* out,size_t n){if(at+n>memory.size())return false;std::memcpy(out,memory.data()+at,n);return true;}
    void type(uintptr_t object,uint32_t kindValue){uintptr_t vt=0x900000+types++*0x1000,fn=vt+0x100,meta=vt+0x200;put(object,vt);put(vt+0x28,fn);std::array<unsigned char,8> code{0x48,0x8d,5,0,0,0,0,0xc3};int32_t delta=int32_t(meta-fn-7);std::memcpy(code.data()+3,&delta,4);std::memcpy(memory.data()+fn,code.data(),8);put(meta+0x50,kindValue);}
    void ref(uintptr_t object,uint64_t rid){type(object,0xf8cc195d);put(object+16,object+0x100);put(object+24,1ULL);put(object+0x100,object+0x200);put(object+0x108,1ULL);put(object+0x200,~0ULL);put(object+0x208,rid);}
    void state(int index,uint64_t tick,bool active){put(rows[index],tick);put(rows[index]+8,uint8_t(!active));}
    explicit Fixture(int role,int cooldown=0):kind(role){
        bool jump=kind==5;int duration=jump?8:13;
        h.hero=0x02e0000000000009ULL;h.model=0x400000;h.modelId=19;h.localId=17;h.reference=0x410000;h.heroInfo=0x420000;h.controller=0x430000;
        uintptr_t admin=0x300000;put(c.base+0x17b7f90,admin);put(admin+0x220,h.localId);put(h.reference+0x94,h.modelId);put(h.reference+8,h.controller);put(h.model+0x28,admin);put(h.heroInfo+0x98,h.hero);
        put(script+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(script+0x150,jump?0x058000000000010aULL:0x05800000000000faULL);put(script+0x160,graph);put(script+0x98,bag);
        put(graph+0x50,uintptr_t(0x610000));put(graph+0x58,1ULL);put(0x610000,items);put(0x610008,jump?65ULL:33ULL);put(bag,c.base+0x1607a90);
        put(bag+0xa0,uintptr_t(0x680000));put(bag+0xa8,2);put(bag+0xac,2);
        for(unsigned i=0;i<2;i++){uint64_t rid=i?0x0d800000000001d8ULL:0x0d8000000000003dULL;uintptr_t primitive=0x690000+i*0x1000;
            put(0x680000+i*16,rid);put(0x680008+i*16,primitive);put(primitive,c.base+0x1608248);put(primitive+0x80,bag);put(primitive+0x98,rid);put(primitive+0xa0,i?(cooldown?cooldown:duration):0);put(primitive+0xac,2);}
        type(0x800000,0x4698e4b6);type(0x801000,0x4698e4b6);type(0x802000,0x3ae7427e);put(0x802010,duration);
        ref(0x803000,0x0d800000000001d8ULL);ref(0x804000,0x0d8000000000003dULL);ref(0x805000,0x0d800000000001d8ULL);
        put(0x800090,uintptr_t(0x803000));put(0x8000a0,uintptr_t(0x802000));put(0x801090,uintptr_t(0x804000));put(0x8010a0,uintptr_t(0x805000));
        put(items+(jump?5:4)*8,uintptr_t(0x800000));put(items+(jump?59:27)*8,uintptr_t(0x801000));
        type(0x807000,0xf53c5da8);type(0x808000,jump?0x8de7e50f:0x4cced352);type(0x809000,0x7fb4bf64);
        put(items+(jump?58:26)*8,uintptr_t(0x807000));put(items+(jump?14:22)*8,uintptr_t(0x808000));put(items+(jump?32:20)*8,uintptr_t(0x809000));
        put(graph+0x60,uintptr_t(0x670000));put(graph+0x68,1ULL);put(0x670000,uintptr_t(0x671000));put(0x670008,1ULL);put(0x671000,uintptr_t(0x807000));
        put(script+0xa0,uintptr_t(0x672000));put(script+0xa8,1);put(script+0xac,1);put(0x672000,uintptr_t(0x673000));put(0x673000,c.base+0x15d7c98);put(0x673070,0);put(0x673078,script);put(0x673150,0.f);
        const unsigned char signature[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xb9,0x60,1,0,0,0x48,0x8b,0xd9,0x48,0x63,0xf2,0x48,0x83,0x7f,0x50};std::memcpy(memory.data()+c.plugin+0x7abc0,signature,32);
        auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root,uint64_t count){put(at,head);put(at+8,count);put(head+8,root);put(head+25,uint8_t(1));};
        uintptr_t logger=c.plugin+0x2d04c0;map(logger,0x710000,0x720000,1);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,script);
        std::vector<int> keys{14,20,22,23,27,32,59};std::function<uintptr_t(int,int,uintptr_t)> tree=[&](int lo,int hi,uintptr_t parent){if(lo>=hi)return uintptr_t(0x730000);int mid=(lo+hi)/2;uintptr_t at=0x740000+mid*0x100;put(at+8,parent);put(at+32,keys[mid]);put(at+40,0ULL);put(at+48,uint8_t(1));rows[keys[mid]]=at+40;put(at,tree(lo,mid,at));put(at+16,tree(mid+1,hi,at));return at;};
        auto root=tree(0,int(keys.size()),0x730000);map(0x720028,0x730000,root,keys.size());state(jump?32:20,300,true);
        std::memcpy(p.magic,"OWPLRQ01",8);p.version=1;p.pid=c.pid;p.creation=c.creation;p.sequence=1000;p.wall=c.now;p.generation=c.generation;p.world=c.world;p.model=h.model;p.modelId=h.modelId;p.script=script;p.graph=graph;p.logger=logger;p.token=300;p.kind=kind;
    }
    bool step(bool packet=true,bool fail=false){
        auto readFn=[&](uintptr_t at,void* out,size_t n){return read(at,out,n);};
        auto invoke=[&](uintptr_t fn,uintptr_t owner,int node,bool start){assert(fn==c.plugin+0x7abc0&&owner==script&&start&&node==(kind==5?59:27));++calls;int configured=0;read(0x6910a0,&configured,4);put(0x6900a0,configured);state(node,p.token+1,false);};
        auto write=[&](uintptr_t at,const void* data,size_t n){assert(at>=0x673000&&at<0x674000);if(fail&&at==0x673146)return false;std::memcpy(memory.data()+at,data,n);return true;};
        p.wall=c.now;return gate.update(packet?&p:nullptr,c,h,readFn,invoke,write);
    }
};
void presentation(){
    Fixture f(6);NativeWinstonPresentation pose;unsigned ends=0;
    f.put(f.h.model+0x50,uintptr_t(0x810000));f.put(f.h.model+0x58,2);f.put(f.h.model+0x5c,2);
    f.put(0x810000,uintptr_t(0x811000));f.put(0x811008,f.h.model);f.put(0x811010,uint8_t(0x23));
    f.put(0x8111b0,uintptr_t(0x812000));f.put(0x8111b8,1);f.put(0x8111bc,1);f.put(0x812000,f.script);
    f.type(0x80b000,0x7b13a0d4);f.put(0x80b010,.5f);f.put(0x809120,uintptr_t(0x80b000));
    f.type(0x80c000,0x6e81f6d4);f.put(f.items+23*8,uintptr_t(0x80c000));f.state(23,300,true);
    const unsigned char endSignature[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
    std::memcpy(f.memory.data()+f.c.plugin+0x7acd0,endSignature,32);
    auto step=[&](){pose.update(f.c,f.h,[&](uintptr_t at,void* out,size_t n){return f.read(at,out,n);},[&](uintptr_t fn,uintptr_t script,int node,bool start){
        assert(fn==f.c.plugin+0x7acd0&&script==f.script&&!start&&(node==20||node==23));++ends;
        uint64_t tick=0;f.read(f.rows[node],&tick,8);f.state(node,tick+1,false);
    });};
    step();f.c.now+=499;step();assert(!ends); // preserve original cast interval
    f.c.now++;step();assert(ends==2&&pose.completed==2);step();assert(ends==2); // native idle, no replay
    f.state(20,400,true);step();f.c.now+=600;f.h.modelId++;step();assert(ends==2); // old pose must never cross pawn ID
    f.put(f.h.reference+0x94,f.h.modelId);step();
    f.c.now+=499;step();assert(ends==2);f.c.now++;step();assert(ends==3); // new owner baseline observes a full interval
    f.state(20,500,true);step();f.c.now+=600;f.put(f.c.plugin+0x7acd0,uint8_t(0xcc));step();assert(ends==3&&pose.refused==1);
    f.c.now+=600;step();assert(ends==3); // no unsafe retry after a signature mismatch
    f.h.hero++;step();assert(!pose.script);
}
int main(){
    for(int kind:{5,6}){
        Fixture f(kind);assert(f.step()&&f.gate.ack.phase==1&&f.calls==1&&f.gate.ack.remaining==(kind==5?8:13));
        uint8_t registered=0;f.read(0x673144,&registered,1);assert(registered==1);f.read(0x673146,&registered,1);assert(registered==1);
        // W1 required movement14/Pet22; these never ran in this fixture. The
        // actual local cast plus real counter ACK must still authorize MC once.
        f.c.now+=100;assert(f.step()&&f.calls==1&&f.gate.ack.remaining<(kind==5?8:13));
        ++f.p.sequence;f.p.token=301;assert(!f.step()&&f.calls==1); // native End/Pet Begin cannot repeat action
        f.c.now+=100;assert(!f.step(false));float current=0;f.read(0x673150,&current,4);assert(current<(kind==5?7.91f:12.91f));
        f.c.world++;f.c.now+=100;assert(!f.step(false)&&f.gate.clock.state&&f.gate.clock.world==f.c.world);
        f.c.generation++;f.c.now+=100;assert(!f.step(false)&&!f.gate.clock.state);
        Fixture noCast(kind);noCast.state(kind==5?32:20,0,false);assert(!noCast.step()&&noCast.calls==0);
        Fixture badOwner(kind);badOwner.p.modelId++;assert(!badOwner.step()&&badOwner.calls==0);
        Fixture badCreation(kind);badCreation.p.creation++;assert(!badCreation.step()&&badCreation.calls==0);
        Fixture badCode(kind);badCode.put(badCode.c.plugin+0x7abc0,uint8_t(0xcc));assert(!badCode.step()&&badCode.calls==0);
        Fixture changedDuration(kind);changedDuration.put(0x802010,10);assert(!changedDuration.step()&&changedDuration.calls==0);
        Fixture rollback(kind);assert(rollback.step(true,true)&&rollback.gate.ack.phase==3);float value=1;rollback.read(0x673150,&value,4);assert(value==0);assert(rollback.step()&&rollback.calls==1&&rollback.gate.ack.phase==3);
        Fixture completed(kind);completed.state(kind==5?32:20,300,false);assert(completed.step()&&completed.gate.ack.phase==1);
    }
    Fixture primal(5,2);assert(primal.step()&&primal.gate.ack.duration==2&&primal.gate.ack.remaining==2);
    for(int cooldown:{8,2}){
        Fixture recast(5,cooldown);assert(recast.step());
        recast.c.now+=2000;recast.state(32,400,true);recast.state(59,401,false);recast.put(0x673150,float(cooldown)-.05f);
        ++recast.p.sequence;recast.p.token=400;
        assert(recast.step()&&recast.gate.ack.phase==1&&recast.calls==1&&recast.gate.completed==2);
        assert(recast.gate.ack.remaining==float(cooldown)-.05f); // do not compress the new original timer
        recast.c.now+=100;recast.state(32,450,false);++recast.p.sequence;recast.p.token=450;
        assert(!recast.step()&&recast.calls==1); // an End is not a new native CD assignment
    }
    presentation();
    std::cout<<"PASS Winston native casts without movement/Pet;8/2/13 real counter ACK,decay,rollback,End/replay and exact owner/code/graph guards\n";
}
