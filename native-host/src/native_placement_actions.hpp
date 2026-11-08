#pragma once
#include "native_deadeye_presentation.hpp"
#include "native_weapon_slots.hpp"
namespace passthrough {
struct PlacementActionRequest {
    char magic[8];uint32_t version,pid;
    uint64_t creation,sequence,wall,generation,world,model,modelId,script,graph,logger,token;
    uint32_t kind,reserved;
};
static_assert(sizeof(PlacementActionRequest)==112);
struct PlacementActionAck {
    char magic[8]={'O','W','P','L','A','K','0','1'};uint32_t version=1,pid=0;
    uint64_t creation=0,sequence=0,wall=0,generation=0,world=0,modelId=0;
    uint32_t kind=0,phase=0;float remaining=0,duration=0;
};
static_assert(sizeof(PlacementActionAck)==80);
/** Confirmed MC placement starts the original declared cooldown action. Manual
 * grapple cancellation ends only the original current cast stack. */
struct NativePlacementActions {
    PlacementActionAck ack{};uint64_t highWater=0,rejected=0;
    uint64_t pendingSince=0,pendingToken=0;uintptr_t pendingAbility=0;
    struct Token {uint64_t generation=0,world=0,model=0,tick=0;};std::array<Token,4> tokens{};
    struct GrappleClock {uint64_t generation=0,world=0,model=0,last=0;uintptr_t script=0,graph=0,state=0;float seconds=0;} grappleClock;
    std::atomic<uint64_t> calls{0},completed{0},refused{0},counterStarts{0};
    template<class Read> static bool ability(WeaponSlotReader<Read>& r,uintptr_t script,uintptr_t graph,uintptr_t definition,uintptr_t& state,float& remaining){
        typename WeaponSlotReader<Read>::List list;uintptr_t definitions=0;uint64_t count=0;state=0;
        if(!r.vector(script+0xa0,list,4096)||!r.array(graph+0x60,definitions,count,4096))return false;
        for(int i=0;i<list.count;i++){auto p=r.ptr(list.items+i*8);if(r.ptr(p)!=r.base+0x15d7c98)continue;
            int index=-1;if(!r.get(p+0x70,index)||index<0||uint64_t(index)>=count||r.ptr(p+0x78)!=script)return false;
            if(r.ptr(definitions+index*8)!=definition)continue;
            if(state)return false;
            state=p;
        }
        unsigned char ready=0,mirror=0;
        return state&&r.get(state+0x150,remaining)&&std::isfinite(remaining)&&remaining>=0&&remaining<=120
            &&r.get(state+0x144,ready)&&ready<=1&&r.get(state+0x146,mirror)&&mirror<=1;
    }
    template<class Read> static bool type(WeaponSlotReader<Read>& r,uintptr_t obj,uint32_t expected){
        auto fn=r.ptr(r.ptr(obj)+0x28);std::array<unsigned char,8> code{};int32_t delta=0;uint32_t kind=0;
        if(!r.get(fn,code)||code[0]!=0x48||code[1]!=0x8d||code[2]!=5||code[7]!=0xc3)return false;
        std::memcpy(&delta,code.data()+3,4);return r.get(fn+7+delta+0x50,kind)&&kind==expected;
    }
    template<class Read> static bool reference(WeaponSlotReader<Read>& r,uintptr_t object,uint64_t rid){
        uintptr_t items=0;uint64_t count=0;
        return type(r,object,0xf8cc195d)&&r.array(object+16,items,count,2)&&count==1
            &&r.ptr(items)==0xffffffffffffffffULL&&r.ptr(items+8)==rid;
    }
    template<class Read> static bool number(WeaponSlotReader<Read>& r,uintptr_t bag,uint64_t rid,double& value){
        uintptr_t primitive=0;
        for(unsigned bucket=0;bucket<16;bucket++){
            typename WeaponSlotReader<Read>::List list;if(!r.vector(bag+0xa0+bucket*0x30,list,512))return false;
            for(int i=0;i<list.count;i++){std::array<uint64_t,2> pair{};if(!r.get(list.items+i*16,pair))return false;
                if(pair[0]==rid){if(primitive)return false;primitive=pair[1];}}
        }
        std::array<unsigned char,16> payload{};uint32_t kind=0;
        if(!primitive||r.ptr(primitive)!=r.base+0x1608248||r.ptr(primitive+0x80)!=bag||r.ptr(primitive+0x98)!=rid||!r.get(primitive+0xa0,payload))return false;
        std::memcpy(&kind,payload.data()+12,4);
        if(kind==2){int v=0;std::memcpy(&v,payload.data(),4);value=v;}else if(kind==3){float v=0;std::memcpy(&v,payload.data(),4);value=v;}else return false;
        return std::isfinite(value)&&value>=0&&value<=120;
    }
    template<class Read,class Write> void tickGrappleClock(const DeadeyePresentationContext& c,const NativeLocalHero& hero,Read read,Write write){
        auto& clock=grappleClock;if(!clock.state)return;
        WeaponSlotReader<Read> r{c.base,read};uintptr_t items=0,state=0;uint64_t count=0;float actual=0;
        if(hero.hero!=0x02e000000000000aULL||clock.generation!=c.generation||!c.world||clock.model!=hero.modelId||!r.owner(r.ptr(c.base+0x17b7f90),hero)
            ||r.ptr(clock.script+0x150)!=0x058000000000005aULL||r.ptr(clock.script+0x160)!=clock.graph||r.ptr(r.ptr(r.ptr(clock.script+0x10)+0x450)+8)!=hero.model
            ||!r.array(clock.graph+0x50,items,count,256)||count!=91||!type(r,r.ptr(items+83*8),0xf53c5da8)||!ability(r,clock.script,clock.graph,r.ptr(items+83*8),state,actual)||state!=clock.state||actual>12.1f){clock={};return;}
        clock.world=c.world; // timer belongs to the same native pawn, not an MC effect in the old dimension
        // Explicit offline-server clock, on the real original ability state.
        // min(actual, previous-dt) never double-decrements a working engine or
        // the compatible shared clock. A native reset/refill remains authoritative.
        if(actual<=0||actual>clock.seconds+.05f){clock={};return;}
        if(c.now<=clock.last||c.now-clock.last>1000){clock.last=c.now;clock.seconds=actual;return;}
        float next=std::min(actual,std::max(0.f,clock.seconds-float(c.now-clock.last)/1000.f));
        if(next<actual){
            unsigned char ready=0,mirror=0,running=1;r.get(state+0x144,ready);r.get(state+0x146,mirror);
            bool ok=write(state+0x150,&next,4);
            if(next==0)ok=ok&&write(state+0x144,&running,1)&&write(state+0x146,&running,1); // same refresh as verifiedF11
            if(!ok){write(state+0x150,&actual,4);write(state+0x144,&ready,1);write(state+0x146,&mirror,1);clock={};++refused;return;}
        }
        clock.last=c.now;clock.seconds=next;if(next==0)clock={};
    }
    template<class Read,class Invoke,class Write> bool update(const PlacementActionRequest* packet,const DeadeyePresentationContext& c,const NativeLocalHero& hero,Read read,Invoke invoke,Write write){
        tickGrappleClock(c,hero,read,write);
        if(!packet)return false;
        const auto& p=*packet;auto deny=[&](){if(rejected!=p.sequence){rejected=p.sequence;++refused;}return false;};
        if(std::memcmp(p.magic,"OWPLRQ01",8)||p.version!=1||p.pid!=c.pid||p.creation!=c.creation||!p.sequence||!p.token||p.kind<1||p.kind>4||p.reserved
            ||p.wall>c.now+50||c.now>p.wall+250||p.generation!=c.generation||p.world!=c.world||!c.world||p.model!=hero.model||p.modelId!=hero.modelId||p.logger!=c.plugin+0x2d04c0)return deny();
        WeaponSlotReader<Read> r{c.base,read};auto admin=r.ptr(c.base+0x17b7f90);if(!r.owner(admin,hero))return deny();
        const uint64_t expectedHero=p.kind==1?0x02e00000000000ddULL:p.kind==2?0x02e0000000000006ULL:0x02e000000000000aULL;
        const uint64_t resource=p.kind==1?0x0580000000000622ULL:p.kind==2?0x05800000000000f4ULL:0x058000000000005aULL;
        if(hero.hero!=expectedHero||r.ptr(p.script+0x150)!=resource||r.ptr(p.script+0x160)!=p.graph||r.ptr(r.ptr(r.ptr(p.script+0x10)+0x450)+8)!=hero.model)return deny();
        uintptr_t items=0;uint64_t count=0;if(!r.array(p.graph+0x50,items,count,256)||count!=(p.kind==1?104:p.kind==2?60:91))return deny();
        int abilityNode=p.kind==1?28:p.kind==2?55:83;auto definition=r.ptr(items+abilityNode*8);uintptr_t abilityState=0;float actualRemaining=0;
        if(!type(r,definition,0xf53c5da8)||!ability(r,p.script,p.graph,definition,abilityState,actualRemaining))return deny();
        if(p.sequence==ack.sequence&&p.kind==ack.kind&&p.world==ack.world&&p.generation==ack.generation&&p.modelId==ack.modelId){
            if(!ack.phase){
                uint64_t tick=0;bool active=false;
                if(p.kind==3){
                    if(!NativeDeadeyePresentation::state(p.logger,p.script,81,tick,active,read)||active||tick<pendingToken){if(c.now<pendingSince+300)return false;ack.phase=3;++refused;}
                    else {
                        // The missing server can leave cancellation with no
                        // native cooldown at all. Preserve the audited12s in
                        // the real Ability83 counter, on this same owner.
                        const auto& began=tokens[3];bool alreadyBegan=began.generation==p.generation&&began.world==p.world&&began.model==p.modelId&&began.tick==pendingToken;
                        if(actualRemaining<=0&&!alreadyBegan){
                            float seconds=ack.duration;unsigned char running=1,ready=0,mirror=0;
                            r.get(abilityState+0x144,ready);r.get(abilityState+0x146,mirror);
                            bool ok=write(abilityState+0x150,&seconds,4)&&write(abilityState+0x144,&running,1)&&write(abilityState+0x146,&running,1);
                            if(!ok){write(abilityState+0x150,&actualRemaining,4);write(abilityState+0x144,&ready,1);write(abilityState+0x146,&mirror,1);ack.phase=3;++refused;}
                            else{actualRemaining=seconds;++counterStarts;}
                        }
                        if(!ack.phase){if(!alreadyBegan&&actualRemaining>0)grappleClock={c.generation,c.world,hero.modelId,c.now,p.script,p.graph,abilityState,actualRemaining};ack.phase=1;ack.remaining=actualRemaining;++completed;}
                    }
                }else{
                    // The original VM queues State End. Inspect the actual
                    // ability counter on a later logic tick, never local3d.
                    if(actualRemaining<=0&&c.now>=pendingSince+80&&NativeDeadeyePresentation::state(p.logger,p.script,p.kind==1?2:22,tick,active,read)&&!active&&tick>=pendingToken){
                        // Same measured StateAbility150/144/146 channel as
                        // NativeCooldownRefill. Set the real engine counter;
                        // native update owns decay, admission and HUD.
                        float seconds=ack.duration,old=actualRemaining;unsigned char running=1,ready=0,mirror=0;
                        r.get(abilityState+0x144,ready);r.get(abilityState+0x146,mirror);
                        bool ok=abilityState==pendingAbility&&write(abilityState+0x150,&seconds,4)&&write(abilityState+0x144,&running,1)&&write(abilityState+0x146,&running,1);
                        if(!ok){write(abilityState+0x150,&old,4);write(abilityState+0x144,&ready,1);write(abilityState+0x146,&mirror,1);ack.phase=3;++refused;}
                        else{++counterStarts;r.get(abilityState+0x150,actualRemaining);}
                    }
                    bool selectorClosed=true;
                    if(p.kind==2){uint64_t ended=0;bool holding=false;selectorClosed=NativeDeadeyePresentation::state(p.logger,p.script,50,ended,holding,read)&&!holding&&ended>=pendingToken;}
                    if(!ack.phase){if(actualRemaining>0&&actualRemaining<=ack.duration&&selectorClosed){ack.phase=1;ack.remaining=actualRemaining;++completed;}else if(c.now<pendingSince+300)return false;else{ack.phase=3;++refused;}}
                }
                ack.wall=c.now;return true;
            }
            if(c.now<ack.wall+50)return false;
            if(ack.phase==1)ack.remaining=actualRemaining;
            ack.wall=c.now;return true;
        }
        if(p.sequence<=highWater)return deny();
        auto& token=tokens[p.kind-1];
        if(token.generation==p.generation&&token.world==p.world&&token.model==p.modelId&&p.token<=token.tick)return deny();
        auto consume=[&](){token={p.generation,p.world,p.modelId,p.token};};
        const std::array<unsigned char,32> actionPrefix{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xb9,0x60,1,0,0,0x48,0x8b,0xd9,0x48,0x63,0xf2,0x48,0x83,0x7f,0x50};
        const std::array<unsigned char,32> statePrefix{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        std::array<unsigned char,32> code{};uint64_t tick=0;bool active=false;
        auto bag=r.ptr(p.script+0x98);double cooldownConfig=0;
        if(r.ptr(bag)!=c.base+0x1607a90||!number(r,bag,0x0d8000000000003dULL,cooldownConfig))return deny();
        if(p.kind==4){
            // Fire admission starts the real original12s timer for hit, miss,
            // natural arrival and cancellation. Keep Ability83 registered.
            auto initial=r.ptr(items+34*8),set=r.ptr(items+84*8),literal=r.ptr(initial+0xa0);int seconds=0;double configured=0;
            uint64_t root=0,fire=0;bool casting=false,firing=false;
            if(!type(r,initial,0x4698e4b6)||!type(r,set,0x4698e4b6)||!type(r,literal,0x3ae7427e)||!r.get(literal+16,seconds)||seconds!=12
                ||!reference(r,r.ptr(initial+0x90),0x0d800000000001d8ULL)||!reference(r,r.ptr(set+0x90),0x0d8000000000003dULL)||!reference(r,r.ptr(set+0xa0),0x0d800000000001d8ULL)
                ||!number(r,bag,0x0d800000000001d8ULL,configured)||configured!=12||!type(r,r.ptr(items+81*8),0xf7d6498c)||!type(r,r.ptr(items+61*8),0x7fb4bf64)
                ||!NativeDeadeyePresentation::state(p.logger,p.script,81,root,casting,read)||(casting?root!=p.token:root<p.token)
                ||!NativeDeadeyePresentation::state(p.logger,p.script,61,fire,firing,read)||fire<p.token||!r.get(c.plugin+0x7abc0,code)||code!=actionPrefix)return deny();
            uint64_t assigned=0;bool assigning=false;
            if(actualRemaining>0&&(!NativeDeadeyePresentation::state(p.logger,p.script,84,assigned,assigning,read)||assigned<p.token))return deny();
            consume();highWater=p.sequence;ack={};ack.pid=c.pid;ack.creation=c.creation;ack.sequence=p.sequence;ack.wall=c.now;ack.generation=p.generation;ack.world=p.world;ack.modelId=p.modelId;ack.kind=4;ack.phase=3;ack.duration=12;
            if(actualRemaining<=0){
                invoke(c.plugin+0x7abc0,p.script,84,true);++calls;
                if(!number(r,bag,0x0d8000000000003dULL,cooldownConfig)||cooldownConfig!=12){++refused;return true;}
                float secondsValue=12,old=actualRemaining;unsigned char running=1,ready=0,mirror=0;
                r.get(abilityState+0x144,ready);r.get(abilityState+0x146,mirror);
                bool ok=write(abilityState+0x150,&secondsValue,4)&&write(abilityState+0x144,&running,1)&&write(abilityState+0x146,&running,1);
                if(!ok){write(abilityState+0x150,&old,4);write(abilityState+0x144,&ready,1);write(abilityState+0x146,&mirror,1);++refused;return true;}
                ++counterStarts;
            }
            if(!r.get(abilityState+0x150,actualRemaining)||!std::isfinite(actualRemaining)||actualRemaining<=0||actualRemaining>12){++refused;return true;}
            grappleClock={c.generation,c.world,hero.modelId,c.now,p.script,p.graph,abilityState,actualRemaining};
            ack.phase=1;ack.remaining=actualRemaining;++completed;return true;
        }
        if(p.kind==3){
            if(!type(r,r.ptr(items+81*8),0xf7d6498c)||!r.get(c.plugin+0x7acd0,code)||code!=statePrefix
                ||!NativeDeadeyePresentation::state(p.logger,p.script,81,tick,active,read)||(active?tick!=p.token:tick<p.token))return deny();
            consume();highWater=p.sequence;ack={};ack.pid=c.pid;ack.creation=c.creation;ack.sequence=p.sequence;ack.wall=c.now;ack.generation=p.generation;ack.world=p.world;ack.modelId=p.modelId;ack.kind=3;ack.duration=12;pendingSince=c.now;pendingToken=p.token;
            bool casting=false;uint64_t root=0;
            if(!NativeDeadeyePresentation::state(p.logger,p.script,81,root,casting,read)){ack.phase=3;return true;}
            if(casting){invoke(c.plugin+0x7acd0,p.script,81,false);++calls;}
            return false;
        }
        int init=p.kind==1?13:34,assignment=p.kind==1?29:51,preview=p.kind==1?2:22;float seconds=p.kind==1?10.f:8.f;
        auto set=r.ptr(items+assignment*8),initial=r.ptr(items+init*8),literal=r.ptr(initial+0xa0);int duration=0;
        if(!type(r,set,0x4698e4b6)||!type(r,initial,0x4698e4b6)||!type(r,literal,0x3ae7427e)||!r.get(literal+16,duration)||duration!=int(seconds)
            ||!reference(r,r.ptr(initial+0x90),0x0d800000000001d8ULL)||!reference(r,r.ptr(set+0x90),0x0d8000000000003dULL)||!reference(r,r.ptr(set+0xa0),0x0d800000000001d8ULL)
            ||!r.get(c.plugin+0x7abc0,code)||code!=actionPrefix||!NativeDeadeyePresentation::state(p.logger,p.script,preview,tick,active,read)||(active?tick!=p.token:tick<p.token))return deny();
        if(!r.get(c.plugin+0x7acd0,code)||code!=statePrefix||!type(r,r.ptr(items+preview*8),p.kind==1?0x72509d3b:0x6e81f6d4))return deny();
        if(p.kind==2&&!type(r,r.ptr(items+50*8),0xa7213568))return deny();
        double configured=0;if(!number(r,bag,0x0d800000000001d8ULL,configured)||configured!=seconds)return deny();
        consume();highWater=p.sequence;ack={};ack.pid=c.pid;ack.creation=c.creation;ack.sequence=p.sequence;ack.wall=c.now;ack.generation=p.generation;ack.world=p.world;ack.modelId=p.modelId;ack.kind=p.kind;ack.duration=seconds;
        pendingSince=c.now;pendingToken=p.token;pendingAbility=abilityState;
        uint64_t assigned=0;bool assigning=false;
        bool already=actualRemaining>0&&actualRemaining<=seconds&&NativeDeadeyePresentation::state(p.logger,p.script,assignment,assigned,assigning,read)&&assigned>=p.token;
        if(already){
            if(p.kind==2){uint64_t ended=0;bool holding=false;if(!NativeDeadeyePresentation::state(p.logger,p.script,50,ended,holding,read))return deny();
                if(holding){invoke(c.plugin+0x7acd0,p.script,50,false);++calls;return false;}}
            ack.remaining=actualRemaining;ack.phase=1;++completed;return true;
        }
        // The actual ArmorPack cooldown uses flags144/146=1/1 while running.
        // Keep the Ability registered so native update owns decay/readmission.
        invoke(c.plugin+0x7abc0,p.script,assignment,true);invoke(c.plugin+0x7acd0,p.script,p.kind==2?50:preview,false);calls+=2;
        return false;
    }
};
}
