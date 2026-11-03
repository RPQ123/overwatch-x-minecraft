#pragma once
#include "native_local_hero.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <atomic>
#include <cmath>
namespace passthrough {
struct DeadeyePresentationRequest {
    char magic[8];uint32_t version,pid;
    uint64_t creation,sequence,wall,generation,world,admin,model,modelId,script,graph,function,logger,begin;
    uint32_t node,ordinal;std::array<unsigned char,32> prefix;
    uint64_t acknowledged;
};
static_assert(sizeof(DeadeyePresentationRequest)==168);
struct DeadeyePresentationAck {
    char magic[8]={'O','W','D','E','Y','E','0','1'};uint32_t version=1,pid=0;
    uint64_t creation=0,sequence=0,wall=0,generation=0,world=0,modelId=0,begin=0,animationTick=0;
    uint32_t phase=0,ordinal=0;
};
static_assert(sizeof(DeadeyePresentationAck)==88);
struct DeadeyePresentationContext {uint32_t pid;uint64_t creation,now,generation,world,base,plugin;};
struct NativeDeadeyePresentation {
    DeadeyePresentationRequest current{};DeadeyePresentationAck ack{};uint64_t previousTick=0,shotStarted=0,lastBegin=0;
    std::atomic<uint64_t> calls{0},completed{0},refused{0};
    template<class Read> static bool state(uintptr_t logger,uintptr_t script,int index,uint64_t& tick,bool& active,Read read){
        auto find=[&](uintptr_t map,uint64_t wanted,bool wide,uintptr_t& value){
            std::array<uint64_t,2> h{},again{};std::array<unsigned char,40> row{};
            if(!read(map,h.data(),16)||h[1]>4096||!read(h[0],row.data(),40)||row[25]!=1)return false;
            uintptr_t at=0,parent=h[0];std::memcpy(&at,row.data()+8,8);value=0;
            for(unsigned n=0;at!=h[0];n++){
                uint64_t key=0;uintptr_t owner=0;
                if(n>=64||!read(at,row.data(),40)||row[25])return false;
                std::memcpy(&owner,row.data()+8,8);if(owner!=parent)return false;
                std::memcpy(&key,row.data()+32,wide?8:4);
                if(key==wanted){value=at+40;break;}
                parent=at;std::memcpy(&at,row.data()+(wanted<key?0:16),8);
            }
            return read(map,again.data(),16)&&again==h;
        };
        uintptr_t inner=0,row=0;std::array<unsigned char,9> a{},b{};
        if(!find(logger,script,true,inner)||!inner)return false;
        if(!find(inner,uint64_t(index),false,row))return false;
        if(!row){tick=0;active=false;return true;}
        if(!read(row,a.data(),9)||!read(row,b.data(),9)||a!=b||a[8]>1)return false;
        std::memcpy(&tick,a.data(),8);active=a[8]==0;return true;
    }
    template<class Read> static bool owner(const DeadeyePresentationRequest& r,const DeadeyePresentationContext& c,const NativeLocalHero& hero,Read read){
        auto q=[&](uintptr_t at){uint64_t v=0;read(at,&v,8);return v;};
        auto arr=[&](uintptr_t at,uintptr_t& items,uint64_t& count){uint64_t storage=q(at),flag=q(at+8);if(flag!=1&&flag!=2)return false;items=q(storage+(flag==1?0:8));count=q(storage+(flag==1?8:0));return items>=0x10000&&count<=4096;};
        if(std::memcmp(r.magic,"OWDEYE01",8)||r.version!=2||r.acknowledged>r.sequence||r.pid!=c.pid||r.creation!=c.creation||!r.sequence||!r.begin||r.node!=69||!r.ordinal||r.ordinal>64
           ||r.wall>c.now+50||c.now>r.wall+150||r.generation!=c.generation||r.world!=c.world||!c.world||r.admin!=q(c.base+0x17b7f90)
           ||r.model!=hero.model||r.modelId!=hero.modelId||hero.hero!=0x02e0000000000042ULL||uint32_t(q(hero.reference+0x94))!=hero.modelId
           ||q(hero.model+0x28)!=r.admin||q(q(q(r.script+0x10)+0x450)+8)!=hero.model||q(r.script+0x150)!=0x058000000000022fULL||q(r.script+0x160)!=r.graph
           ||r.function!=c.plugin+0x7acd0)return false;
        const std::array<unsigned char,32> expected{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        std::array<unsigned char,32> code{};if(r.prefix!=expected||!read(r.function,code.data(),32)||code!=expected)return false;
        uintptr_t items=0;uint64_t count=0;if(!arr(r.graph+0x50,items,count)||count!=101)return false;
        auto definition=q(items+69*8),alias=q(definition+0x100);uint32_t index=0;
        if(!read(definition+0x68,&index,4)||index!=69||q(alias+0x18)!=0x0c8000000000019fULL)return false;
        // Original server target loop:71 -> Wait72(.1333s) ->73 ->66.
        // The .33s animation envelope is not the per-target firing interval.
        auto wait=q(items+72*8),interval=q(wait+0x100);float seconds=0;
        if(q(wait)!=c.base+0x150bd08||q(interval)!=c.base+0x1558ba8
           ||!read(interval+16,&seconds,4)||!std::isfinite(seconds)||std::abs(seconds-.1333f)>1e-6f)return false;
        uint64_t tick=0;bool active=false;return state(r.logger,r.script,18,tick,active,read)&&active&&tick==r.begin;
    }
    template<class Read,class Invoke> bool update(const DeadeyePresentationRequest* r,const DeadeyePresentationContext& c,const NativeLocalHero& hero,Read read,Invoke invoke){
        if(ack.phase==1){
            if(c.generation!=current.generation||c.world!=current.world||hero.modelId!=current.modelId||hero.hero!=0x02e0000000000042ULL){ack.phase=3;ack.wall=c.now;return true;}
            uint64_t tick=0;bool active=true;
            if(state(current.logger,current.script,69,tick,active,read)&&!active&&tick>=ack.animationTick){
                // Keep the proven original Begin until MC has acknowledged
                // that exact sequence. An early End must not overwrite it in
                // the single-slot file transport before the reader sees it.
                // Never refresh Begin's wall time to manufacture fresh damage.
                bool received=r&&r->begin==current.begin&&r->script==current.script&&r->modelId==current.modelId
                    &&r->world==current.world&&r->generation==current.generation&&r->acknowledged>=ack.sequence&&owner(*r,c,hero,read);
                if(!received){if(c.now>shotStarted+1000){ack.phase=3;ack.wall=c.now;return true;}return false;}
                ack.phase=2;ack.animationTick=tick;ack.wall=c.now;++completed;return true;
            }
        }
        if(!r)return false;
        if(r->sequence==ack.sequence){
            // A reader can miss the short-lived End packet during Windows
            // file contention. Re-observe the same original End for a fresh
            // matching request; never start the animation or damage twice.
            uint64_t tick=0;bool active=true;
            if(ack.phase==2&&c.now>=ack.wall+30&&r->begin==current.begin&&r->ordinal==current.ordinal&&r->script==current.script
               &&r->modelId==current.modelId&&r->world==current.world&&r->generation==current.generation
               &&owner(*r,c,hero,read)&&state(r->logger,r->script,69,tick,active,read)&&!active&&tick==ack.animationTick){
                ack.wall=c.now;return true;
            }
            return false;
        }
        if(!owner(*r,c,hero,read)){++refused;return false;}
        bool same=current.begin==r->begin&&current.script==r->script&&current.modelId==r->modelId&&current.generation==r->generation&&current.world==r->world;
        if((same&&(r->sequence<=current.sequence||r->acknowledged<current.sequence||(ack.phase!=1&&ack.phase!=2)||r->ordinal!=current.ordinal+1))||(!same&&r->ordinal!=1))return false;
        if(same&&(c.now<shotStarted||c.now-shotStarted<134))return false;
        uint64_t tick=0;bool active=true;if(!state(r->logger,r->script,69,tick,active,read))return false;
        previousTick=same?lastBegin:tick;
        if(active){
            if(!same||ack.phase!=1)return false;
            // The engine, on its original logic thread, releases our previous
            // animation before the next original shot starts. No timer/object
            // is freed manually and no second callback owns this sequence.
            invoke(r->function,r->script,69,false);
            if(!state(r->logger,r->script,69,tick,active,read)||active||tick<lastBegin){++refused;return false;}
            ++completed;
        }
        current=*r;
        // This is the provided plugin's own StartStopState UI action. The
        // original engine owns the animation and its natural completion.
        invoke(r->function,r->script,69,true);++calls;
        if(!state(r->logger,r->script,69,tick,active,read)||!active||tick<=previousTick){++refused;ack.sequence=r->sequence;ack.phase=3;ack.wall=c.now;return true;}
        shotStarted=c.now;lastBegin=tick;
        ack={};ack.pid=c.pid;ack.creation=c.creation;ack.sequence=r->sequence;ack.wall=c.now;ack.generation=r->generation;ack.world=r->world;ack.modelId=r->modelId;ack.begin=r->begin;ack.animationTick=tick;ack.phase=1;ack.ordinal=r->ordinal;return true;
    }
};
}
