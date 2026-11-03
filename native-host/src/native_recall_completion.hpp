#pragma once
#include "native_deadeye_presentation.hpp"
namespace passthrough {
struct NativeRecallBinding {
    char magic[8];uint32_t version,pid;
    uint64_t creation,admin,localId,modelId,model,script,bag,graph,logger,cast,animation,castVtable,animationVtable,function;
    std::array<unsigned char,32> prefix;
    uint64_t ammoScript,ammoBag,ammo,maximum,ammoGraph,reloadDefinition;
};
static_assert(sizeof(NativeRecallBinding)==208);
struct NativeRecallCompletionAck {
    char magic[8];uint32_t version,pid;
    uint64_t creation,generation,world,modelId,begin,wall;
    uint32_t phase,reserved;
};
static_assert(sizeof(NativeRecallCompletionAck)==72);
struct NativeRecallCompletion {
    uint64_t model=0,world=0,generation=0,last=0,pending=0,pendingWorld=0,awaiting=0,awaitingWorld=0,rootEnd=0;
    std::atomic<uint64_t> calls{0},completed{0},refused{0};
    std::atomic<uint64_t> historyCalls{0},historyCompleted{0};
    bool ammoDue=false;
    template<class Read> static bool owner(const NativeRecallBinding& b,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read){
        auto q=[&](uintptr_t a){uint64_t v=0;read(a,&v,8);return v;};
        const std::array<unsigned char,32> expected{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        std::array<unsigned char,32> code{};
        if(std::memcmp(b.magic,"OWRECL01",8)||b.version!=2||!c.world||!c.generation||b.pid!=c.pid||b.creation!=c.creation||h.hero!=0x02e0000000000003ULL
            ||b.admin!=q(c.base+0x17b7f90)||b.localId!=h.localId||b.modelId!=h.modelId||b.model!=h.model
            ||uint32_t(q(h.reference+0x94))!=h.modelId||q(h.model+0x28)!=b.admin
            ||q(b.script+0x150)!=0x058000000000001aULL||q(b.script+0x160)!=b.graph||q(b.script+0x98)!=b.bag
            ||q(q(q(b.script+0x10)+0x450)+8)!=h.model||b.function!=c.plugin+0x7acd0||b.prefix!=expected
            ||!read(b.function,code.data(),32)||code!=expected||b.castVtable!=c.base+0x1500590||b.animationVtable!=c.base+0x15138c0
            ||q(b.cast)!=b.castVtable||q(b.animation)!=b.animationVtable)return false;
        auto storage=q(b.graph+0x50),flag=q(b.graph+0x58);if(flag!=1&&flag!=2)return false;
        auto items=q(storage+(flag==1?0:8)),count=q(storage+(flag==1?8:0));
        return count==48&&q(items+31*8)==b.cast&&q(items+9*8)==b.animation&&q(q(items+8))==c.base+0x151c678;
    }
    template<class Read,class Invoke> bool update(const NativeRecallBinding* b,const NativeRecallCompletionAck* ack,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Invoke invoke){
        if(!b)return false;
        if(!owner(*b,c,h,read)){model=world=generation=last=pending=awaiting=0;return false;}
        uint64_t begin=0,animation=0;bool casting=false,animating=false;
        if(!NativeDeadeyePresentation::state(b->logger,b->script,31,begin,casting,read)
            ||!NativeDeadeyePresentation::state(b->logger,b->script,9,animation,animating,read))return false;
        if(model!=h.modelId||generation!=c.generation){model=h.modelId;world=c.world;generation=c.generation;last=begin;pending=casting&&animating&&animation==begin?begin:0;pendingWorld=c.world;awaiting=0;return false;}
        // A surviving original pawn needs native cleanup even after MC changes
        // dimension. This grants no MC rewind or damage authority: the server
        // independently cancelled its old world-scoped pending history.
        world=c.world;
        if(awaiting){
            bool cancellation=c.world!=awaitingWorld;
            bool accepted=ack&&!std::memcmp(ack->magic,"OWRECA01",8)&&ack->version==1&&ack->pid==c.pid&&ack->creation==c.creation
                &&ack->generation==c.generation&&ack->world==c.world&&ack->modelId==h.modelId&&ack->begin==awaiting
                &&ack->wall<=c.now+50&&c.now<=ack->wall+1000&&(ack->phase==2||ack->phase==3)&&!ack->reserved;
            uint64_t tick=0;bool active=false;
            if((cancellation||accepted)&&!casting&&NativeDeadeyePresentation::state(b->logger,b->script,1,tick,active,read)&&active&&tick>=rootEnd){
                awaiting=0;++historyCalls;invoke(b->function,b->script,1,false);
                if(NativeDeadeyePresentation::state(b->logger,b->script,1,tick,active,read)&&!active){++historyCompleted;ammoDue=accepted&&!cancellation&&ack->phase==2;}else ++refused;
                return true;
            }
        }
        if(begin>last){last=begin;pending=casting?begin:0;pendingWorld=c.world;}
        if(!casting){pending=0;return false;}
        // Completion follows the actual original animation End, not a guessed
        // elapsed timer, a key, a renderer callback or the quarantined helper.
        if(!pending||animation<pending||animating)return false;
        awaiting=pending;awaitingWorld=pendingWorld;pending=0;++calls;invoke(b->function,b->script,31,false);
        uint64_t after=0;bool active=true;
        if(NativeDeadeyePresentation::state(b->logger,b->script,31,after,active,read)&&!active&&after>=begin){++completed;rootEnd=after;}else{awaiting=0;++refused;}
        return true;
    }
    template<class Read,class Invoke> bool update(const NativeRecallBinding* b,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Invoke invoke){return update(b,nullptr,c,h,read,invoke);}
};
}
