#pragma once
#include "native_placement_actions.hpp"

namespace passthrough {
/** Native local cast -> real cooldown receipt -> MC action. Runs on the existing
 * body logic owner only. The absent server's TrackMovement/Pet is not required.
 * Mailboxes5/6 are separate so simultaneous Jump/Barrier cannot overwrite ACKs. */
struct NativeWinstonActions {
    PlacementActionAck ack{};
    uint64_t highWater=0,handledTick=0,handledGeneration=0,handledWorld=0,handledModel=0,rejected=0;
    std::atomic<uint64_t> calls{0},completed{0},refused{0},clockWrites{0};
    struct Clock {uintptr_t script=0,graph=0,state=0;uint64_t generation=0,world=0,model=0,wall=0;uint32_t kind=0;float value=0,duration=0;uint64_t assigned=0;} clock;
    template<class Read,class Write> void advance(const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Write write){
        if(!clock.state)return;
        WeaponSlotReader<Read> r{c.base,read};uintptr_t items=0,state=0;uint64_t count=0;float current=0;
        bool jump=clock.kind==5;
        if(h.hero!=0x02e0000000000009ULL||clock.generation!=c.generation||clock.model!=h.modelId||!c.world
            ||!r.owner(r.ptr(c.base+0x17b7f90),h)||r.ptr(clock.script+0x150)!=(jump?0x058000000000010aULL:0x05800000000000faULL)
            ||r.ptr(clock.script+0x160)!=clock.graph||r.ptr(r.ptr(r.ptr(clock.script+0x10)+0x450)+8)!=h.model
            ||!r.array(clock.graph+0x50,items,count,256)||count!=(jump?65u:33u)
            ||!NativePlacementActions::ability(r,clock.script,clock.graph,r.ptr(items+(jump?58:26)*8),state,current)||state!=clock.state){clock={};return;}
        clock.world=c.world; // the native pawn's cooldown survives an MC dimension change
        if(jump){
            uint64_t assigned=0,cast=0;bool assigning=false,active=false;
            // A real native recast may consume its cooldown between MC polls.
            // Retire the OLD fallback clock before it can compress/deny the new
            // native timer. Anim End alone has no newer matching SetVar59.
            if(NativeDeadeyePresentation::state(c.plugin+0x2d04c0,clock.script,59,assigned,assigning,read)
                &&NativeDeadeyePresentation::state(c.plugin+0x2d04c0,clock.script,32,cast,active,read)
                &&assigned>clock.assigned&&cast>handledTick&&assigned>=cast){clock={};return;}
        }
        if(current<=0||current>clock.duration+.05f){clock={};return;}
        if(c.now<=clock.wall||c.now-clock.wall>1000){clock.wall=c.now;clock.value=current;return;}
        float next=std::min(current,std::max(0.f,clock.value-float(c.now-clock.wall)/1000.f));
        unsigned char ready=0,mirror=0;r.get(state+0x144,ready);r.get(state+0x146,mirror);
        if(next<current){
            // Like the verified native Ability refresh, keep it registered
            // during cooldown; 0/0 strands animation/stack cleanup offline.
            unsigned char flag=1;
            bool ok=write(state+0x150,&next,4)&&write(state+0x144,&flag,1)&&write(state+0x146,&flag,1);
            if(!ok){write(state+0x150,&current,4);write(state+0x144,&ready,1);write(state+0x146,&mirror,1);++refused;clock={};return;}
            ++clockWrites;
        }
        clock.wall=c.now;clock.value=next;if(next==0)clock={};
    }
    template<class Read,class Invoke,class Write> bool update(const PlacementActionRequest* packet,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Invoke invoke,Write write){
        advance(c,h,read,write);if(!packet)return false;
        const auto& p=*packet;auto deny=[&](){if(rejected!=p.sequence){rejected=p.sequence;++refused;}return false;};
        if(std::memcmp(p.magic,"OWPLRQ01",8)||p.version!=1||p.pid!=c.pid||p.creation!=c.creation||!p.sequence||!p.token||(p.kind!=5&&p.kind!=6)||p.reserved
            ||p.wall>c.now+50||c.now>p.wall+250||p.generation!=c.generation||p.world!=c.world||!c.world||h.hero!=0x02e0000000000009ULL
            ||p.model!=h.model||p.modelId!=h.modelId||p.logger!=c.plugin+0x2d04c0)return deny();
        WeaponSlotReader<Read> r{c.base,read};bool jump=p.kind==5;uintptr_t items=0,state=0;uint64_t count=0;float remaining=0;
        if(!r.owner(r.ptr(c.base+0x17b7f90),h)||r.ptr(p.script+0x150)!=(jump?0x058000000000010aULL:0x05800000000000faULL)
            ||r.ptr(p.script+0x160)!=p.graph||r.ptr(r.ptr(r.ptr(p.script+0x10)+0x450)+8)!=h.model
            ||!r.array(p.graph+0x50,items,count,256)||count!=(jump?65u:33u)
            ||!NativePlacementActions::type(r,r.ptr(items+(jump?58:26)*8),0xf53c5da8)
            ||!NativePlacementActions::ability(r,p.script,p.graph,r.ptr(items+(jump?58:26)*8),state,remaining))return deny();
        if(p.sequence==ack.sequence&&p.kind==ack.kind&&p.generation==ack.generation&&p.world==ack.world&&p.modelId==ack.modelId){
            ack.remaining=remaining;ack.wall=c.now;return true;
        }
        if(clock.state&&remaining>0)return deny(); // Anim End/Pet Begin of the same cast cannot launch twice.
        if(p.sequence<=highWater||(handledGeneration==c.generation&&handledWorld==c.world&&handledModel==h.modelId&&p.token<=handledTick))return deny();
        auto init=r.ptr(items+(jump?5:4)*8),set=r.ptr(items+(jump?59:27)*8),literal=r.ptr(init+0xa0),bag=r.ptr(p.script+0x98);
        int duration=0;double configured=0;
        if(!NativePlacementActions::type(r,init,0x4698e4b6)||!NativePlacementActions::type(r,set,0x4698e4b6)||!NativePlacementActions::type(r,literal,0x3ae7427e)
            ||!r.get(literal+16,duration)||duration!=(jump?8:13)||!NativePlacementActions::reference(r,r.ptr(init+0x90),0x0d800000000001d8ULL)
            ||!NativePlacementActions::reference(r,r.ptr(set+0x90),0x0d8000000000003dULL)||!NativePlacementActions::reference(r,r.ptr(set+0xa0),0x0d800000000001d8ULL)
            ||r.ptr(bag)!=c.base+0x1607a90||!NativePlacementActions::number(r,bag,0x0d800000000001d8ULL,configured)
            ||(jump?(configured!=8&&configured!=2):configured!=13))return deny();
        uint64_t castTick=0,effectTick=0;bool castActive=false,effectActive=false;
        auto cast=r.ptr(items+(jump?32:20)*8),effect=r.ptr(items+(jump?14:22)*8);
        if(!NativePlacementActions::type(r,cast,0x7fb4bf64)||!NativePlacementActions::type(r,effect,jump?0x8de7e50f:0x4cced352)
            ||!NativeDeadeyePresentation::state(p.logger,p.script,jump?32:20,castTick,castActive,read)
            ||!NativeDeadeyePresentation::state(p.logger,p.script,jump?14:22,effectTick,effectActive,read)
            ||!((castTick==p.token&&(castActive||castTick>0))||(effectTick==p.token&&(effectActive||effectTick>0))))return deny();
        constexpr std::array<unsigned char,32> signature{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xb9,0x60,1,0,0,0x48,0x8b,0xd9,0x48,0x63,0xf2,0x48,0x83,0x7f,0x50};
        std::array<unsigned char,32> code{};if(!r.get(c.plugin+0x7abc0,code)||code!=signature)return deny();
        uint64_t assigned=0;bool assigning=false;
        if(remaining>0&&(!NativeDeadeyePresentation::state(p.logger,p.script,jump?59:27,assigned,assigning,read)||assigned<p.token||remaining>configured))return deny();
        highWater=p.sequence;handledGeneration=c.generation;handledWorld=c.world;handledModel=h.modelId;handledTick=p.token;
        ack={};ack.pid=c.pid;ack.creation=c.creation;ack.sequence=p.sequence;ack.wall=c.now;ack.generation=c.generation;ack.world=c.world;ack.modelId=h.modelId;ack.kind=p.kind;ack.phase=3;ack.duration=float(configured);
        if(remaining<=0){
            invoke(c.plugin+0x7abc0,p.script,jump?59:27,true);++calls;
            double actualConfig=0;if(!NativePlacementActions::number(r,bag,0x0d8000000000003dULL,actualConfig)||actualConfig!=configured){++refused;return true;}
            float seconds=float(configured);unsigned char ready=0,mirror=0,running=1;r.get(state+0x144,ready);r.get(state+0x146,mirror);
            bool ok=write(state+0x150,&seconds,4)&&write(state+0x144,&running,1)&&write(state+0x146,&running,1);
            if(!ok){write(state+0x150,&remaining,4);write(state+0x144,&ready,1);write(state+0x146,&mirror,1);++refused;return true;}
        }
        if(!r.get(state+0x150,remaining)||remaining<=0||remaining>configured){++refused;return true;}
        clock={p.script,p.graph,state,c.generation,c.world,h.modelId,c.now,p.kind,remaining,float(configured)};
        bool assigningNow=false;NativeDeadeyePresentation::state(p.logger,p.script,jump?59:27,clock.assigned,assigningNow,read);
        ack.phase=1;ack.remaining=remaining;++completed;return true;
    }
};
}
