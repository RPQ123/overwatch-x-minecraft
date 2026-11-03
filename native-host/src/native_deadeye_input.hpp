#pragma once
#include "guest_body.hpp"
#include "native_deadeye_presentation.hpp"
namespace passthrough {
struct DeadeyeInputContext {
    uint32_t pid=0,sourcePid=0;uint64_t generation=0,hostGeneration=0,world=0,now=0;
    uintptr_t pluginBegin=0,pluginEnd=0;
};
// Read-only admission; called by the existing render owner once per observed
// frame. The input hooks consume only its bounded snapshot, never game scripts.
template<class Read> bool nativeDeadeyeInputActive(const GuestBody& b,const DeadeyeInputContext& c,const NativeLocalHero& h,Read read){
    if(!b.deadeyeFiring||h.hero!=0x02e0000000000042ULL||!h.modelId||h.modelId!=b.deadeyeModel
        ||b.hostPid!=c.pid||b.sourcePid!=c.sourcePid||b.generation!=c.generation||b.hostGeneration!=c.hostGeneration
        ||!c.world||b.worldId!=c.world||b.deadeyeWorld!=c.world||b.wallMs>c.now||c.now-b.wallMs>150
        ||b.deadeyeObserved>c.now||c.now-b.deadeyeObserved>150||!b.deadeyeBegin
        ||!c.pluginBegin||c.pluginEnd<=c.pluginBegin||b.deadeyeLogger<c.pluginBegin||b.deadeyeLogger>c.pluginEnd-16)return false;
    auto q=[&](uintptr_t at){uint64_t v=0;read(at,&v,8);return v;};
    if(q(b.deadeyeScript+0x150)!=0x058000000000022fULL
        ||q(q(q(b.deadeyeScript+0x10)+0x450)+8)!=h.model)return false;
    uint64_t begin=0,fire=0;bool active=false,firing=false;
    return NativeDeadeyePresentation::state(b.deadeyeLogger,b.deadeyeScript,18,begin,active,read)&&active&&begin==b.deadeyeBegin
        &&NativeDeadeyePresentation::state(b.deadeyeLogger,b.deadeyeScript,44,fire,firing,read)&&fire>=begin;
}
}
