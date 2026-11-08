#pragma once
#include "native_placement_actions.hpp"
namespace passthrough {
/** The absent offline server leaves real Ability150 counters frozen. Advance
 * only running counters on the existing native logic thread, retaining faster
 * original decay, fresh scope, all typed memberships and the original HUD. */
struct NativeAbilityClock {
    struct Sample {uintptr_t state=0;uint64_t wall=0;float value=0;};
    std::array<Sample,128> samples{};uint64_t generation=0,world=0,model=0,next=0;
    std::atomic<uint64_t> writes{0},refused{0};
    template<class Read,class Write> unsigned update(const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Write write){
        if(!c.world||!c.generation||(h.hero!=0x02e0000000000040ULL&&h.hero!=0x02e00000000000ddULL&&h.hero!=0x02e0000000000006ULL&&h.hero!=0x02e000000000000aULL))return 0;
        WeaponSlotReader<Read> r{c.base,read};if(!r.owner(r.ptr(c.base+0x17b7f90),h))return 0;
        if(generation!=c.generation||world!=c.world||model!=h.modelId){samples={};generation=c.generation;world=c.world;model=h.modelId;next=0;}
        if(c.now<next)return 0;
        next=c.now+200;
        auto component=r.scriptComponent(h.model);typename WeaponSlotReader<Read>::List scripts;
        if(!component||!r.vector(component+0x1b0,scripts,512))return 0;
        unsigned changed=0,inspected=0;
        for(int i=0;i<scripts.count;i++){
            auto script=r.ptr(scripts.items+i*8);if(!script||r.ptr(r.ptr(r.ptr(script+0x10)+0x450)+8)!=h.model)continue;
            auto graph=r.ptr(script+0x160);if((r.ptr(script+0x150)>>48)!=0x0580)continue;
            uintptr_t definitions=0;uint64_t count=0;typename WeaponSlotReader<Read>::List states;
            if(!r.array(graph+0x60,definitions,count,4096)||!r.vector(script+0xa0,states,4096))continue;
            if((inspected+=states.count)>32768)return changed;
            for(int j=0;j<states.count;j++){
                auto state=r.ptr(states.items+j*8);if(r.ptr(state)!=c.base+0x15d7c98)continue;
                int index=-1;float current=0;unsigned char ready=0,mirror=0;
                if(r.ptr(state+0x78)!=script||!r.get(state+0x70,index)||index<0||uint64_t(index)>=count
                    ||!NativePlacementActions::type(r,r.ptr(definitions+index*8),0xf53c5da8)||!r.get(state+0x150,current)||!std::isfinite(current)||current<0||current>120
                    ||!r.get(state+0x144,ready)||ready>1||!r.get(state+0x146,mirror)||mirror>1){++refused;continue;}
                Sample* slot=nullptr;for(auto& s:samples){if(s.state==state){slot=&s;break;}if(!s.state&&!slot)slot=&s;}
                if(!slot)continue;
                if(ready||mirror||current==0){*slot={};continue;}
                float wanted=current;
                if(slot->state&&c.now>=slot->wall&&c.now-slot->wall<=1000&&current<=slot->value+.05f)
                    wanted=std::min(current,std::max(0.f,slot->value-float(c.now-slot->wall)/1000.f));
                if(wanted<current){
                    if(!r.owner(r.ptr(c.base+0x17b7f90),h))return changed;
                    unsigned char one=1;
                    bool ok=write(state+0x150,&wanted,4);
                    if(ok&&wanted==0)ok=write(state+0x144,&one,1)&&write(state+0x146,&one,1);
                    if(!ok){write(state+0x150,&current,4);write(state+0x144,&ready,1);write(state+0x146,&mirror,1);++refused;*slot={};continue;}
                    ++writes;++changed;
                }
                *slot={state,c.now,wanted};
            }
        }
        return changed;
    }
};
}
