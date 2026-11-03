#pragma once
#include "native_recall_completion.hpp"
namespace passthrough {
// Same bounded owner fields as Recall, without its history/ammo extension.
struct NativeWraithBinding {
    char magic[8];uint32_t version,pid;
    uint64_t creation,admin,localId,modelId,model,script,bag,graph,logger,cast,animation,castVtable,animationVtable,function;
    std::array<unsigned char,32> prefix;
};
static_assert(sizeof(NativeWraithBinding)==160);
struct NativeWraithCompletion {
    uint64_t model=0,generation=0,last=0,pending=0,admitted=0;
    std::atomic<uint64_t> calls{0},completed{0},refused{0};
    std::atomic<uint64_t> starts{0};
    template<class Read> static bool owner(const NativeWraithBinding& b,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read){
        auto q=[&](uintptr_t a){uint64_t v=0;read(a,&v,8);return v;};
        const std::array<unsigned char,32> expected{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        std::array<unsigned char,32> code{};
        if(std::memcmp(b.magic,"OWWRTH01",8)||b.version!=1||!c.world||!c.generation||b.pid!=c.pid||b.creation!=c.creation||h.hero!=0x02e0000000000002ULL
            ||b.admin!=q(c.base+0x17b7f90)||b.localId!=h.localId||b.modelId!=h.modelId||b.model!=h.model
            ||uint32_t(q(h.reference+0x94))!=h.modelId||q(h.model+0x28)!=b.admin
            ||q(b.script+0x150)!=0x0580000000000020ULL||q(b.script+0x160)!=b.graph||q(b.script+0x98)!=b.bag
            ||q(q(q(b.script+0x10)+0x450)+8)!=h.model||b.function!=c.plugin+0x7acd0||b.prefix!=expected||!read(b.function,code.data(),32)||code!=expected
            ||b.castVtable!=c.base+0x1500590||b.animationVtable!=c.base+0x15138c0||q(b.cast)!=b.castVtable||q(b.animation)!=b.animationVtable)return false;
        auto storage=q(b.graph+0x50),flag=q(b.graph+0x58);if(flag!=1&&flag!=2)return false;
        auto items=q(storage+(flag==1?0:8)),count=q(storage+(flag==1?8:0));
        return count==28&&q(items+20*8)==b.cast&&q(items+3*8)==b.animation&&q(q(items+2*8))==c.base+0x151c748&&q(q(items+4*8))==c.base+0x150bd08;
    }
    template<class Read,class Invoke> bool update(const NativeWraithBinding* b,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Invoke invoke){
        if(!b)return false;
        if(!owner(*b,c,h,read)){model=generation=last=pending=admitted=0;return false;}
        uint64_t begin=0,animation=0;bool casting=false,animating=false;
        if(!NativeDeadeyePresentation::state(b->logger,b->script,20,begin,casting,read)||!NativeDeadeyePresentation::state(b->logger,b->script,3,animation,animating,read))return false;
        if(model!=h.modelId||generation!=c.generation){model=h.modelId;generation=c.generation;last=begin;pending=admitted=0;return false;}
        if(begin>last){last=begin;pending=casting?begin:0;}
        if(!casting){pending=0;return false;}
        // Original zero-duration server-request state2 gates Wait4, whose
        // state output owns physical form1/5 and weapon-priority9 for3s.
        // A fresh real cast admits this native transition once. It grants no
        // MC effects: those independently require the fresh MC phase/scope.
        uint64_t requestTick=0;bool requesting=false;
        if(pending&&admitted!=pending&&animating&&animation>=pending&&NativeDeadeyePresentation::state(b->logger,b->script,2,requestTick,requesting,read)&&requesting&&requestTick>=pending){
            admitted=pending;++starts;invoke(b->function,b->script,2,false);return true;
        }
        // Only this observed original animation End completes the root. A
        // dimension change cancels MC effects independently, but the surviving
        // native pawn still needs its own weapons released. No elapsed helper.
        uint64_t physicalEnd=0;bool physicalWaiting=false;
        if(!pending||animation<pending||animating||!NativeDeadeyePresentation::state(b->logger,b->script,4,physicalEnd,physicalWaiting,read)||physicalWaiting||physicalEnd<pending)return false;
        pending=0;++calls;invoke(b->function,b->script,20,false);
        uint64_t after=0;bool active=true;
        if(NativeDeadeyePresentation::state(b->logger,b->script,20,after,active,read)&&!active&&after>=begin)++completed;else ++refused;
        return true;
    }
};
}
