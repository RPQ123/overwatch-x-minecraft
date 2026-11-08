#pragma once
#include "native_winston_actions.hpp"

namespace passthrough {
/** Finish a stranded original half-second E pose on the existing logic owner.
 * No key inference, synthetic idle animation, extra callback or skill admission.
 * Native weapon equip/idle and Q/fists remain owned by the original graphs. */
struct NativeWinstonPresentation {
    uintptr_t script=0,graph=0;uint64_t model=0,generation=0,nextSearch=0;
    struct Window {uint64_t tick=0,since=0;bool ended=false;} windows[2];
    std::atomic<uint64_t> ends{0},completed{0},refused{0};
    void clear(){script=graph=0;model=generation=nextSearch=0;windows[0]={};windows[1]={};}
    template<class Read,class Invoke> void update(const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Invoke invoke){
        WeaponSlotReader<Read> r{c.base,read};
        if(h.hero!=0x02e0000000000009ULL||!c.generation||!c.world||!r.owner(r.ptr(c.base+0x17b7f90),h)){clear();return;}
        if(model!=h.modelId||generation!=c.generation){clear();model=h.modelId;generation=c.generation;}
        auto owned=[&](uintptr_t s){return s&&r.ptr(s+0x150)==0x05800000000000faULL&&r.ptr(r.ptr(r.ptr(s+0x10)+0x450)+8)==h.model;};
        auto component=r.scriptComponent(h.model);typename WeaponSlotReader<Read>::List list;
        if(!component||!r.vector(component+0xc0+0xf0,list,256)){clear();return;}
        if(script){
            unsigned matches=0;for(int i=0;i<list.count;i++)if(r.ptr(list.items+i*8)==script)++matches;
            if(matches!=1){script=graph=0;windows[0]={};windows[1]={};}
        }
        if(script&&!owned(script)){script=graph=0;windows[0]={};windows[1]={};}
        if(!script){
            if(c.now<nextSearch)return;
            nextSearch=c.now+250;
            for(int i=0;i<list.count;i++){auto s=r.ptr(list.items+i*8);if(!owned(s))continue;if(script){clear();++refused;return;}script=s;}
            if(!script)return;
            graph=r.ptr(script+0x160);
        }
        uintptr_t items=0;uint64_t count=0;
        if(r.ptr(script+0x160)!=graph||!r.array(graph+0x50,items,count,256)||count!=33
            ||!NativePlacementActions::type(r,r.ptr(items+20*8),0x7fb4bf64)
            ||!NativePlacementActions::type(r,r.ptr(items+23*8),0x6e81f6d4)){clear();++refused;return;}
        auto duration=r.ptr(r.ptr(items+20*8)+0x120);float seconds=0;
        if(!NativePlacementActions::type(r,duration,0x7b13a0d4)||!r.get(duration+16,seconds)||seconds!=.5f){clear();++refused;return;}
        constexpr std::array<unsigned char,32> signature{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        for(unsigned k=0;k<2;k++){
            int node=k?23:20;uint64_t tick=0;bool active=false;auto& w=windows[k];
            if(!NativeDeadeyePresentation::state(c.plugin+0x2d04c0,script,node,tick,active,read)){w={};continue;}
            if(!active){w={};continue;}
            if(!w.since||w.tick!=tick||c.now<w.since){w={tick,c.now,false};continue;}
            if(w.ended||c.now-w.since<500)continue;
            std::array<unsigned char,32> code{};
            if(!r.get(c.plugin+0x7acd0,code)||code!=signature){w.ended=true;++refused;continue;}
            w.ended=true;invoke(c.plugin+0x7acd0,script,node,false);++ends;
            uint64_t after=0;bool holding=true;
            if(NativeDeadeyePresentation::state(c.plugin+0x2d04c0,script,node,after,holding,read)&&!holding&&after>=tick)++completed;else ++refused;
        }
    }
};
}
