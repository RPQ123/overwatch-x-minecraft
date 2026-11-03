#pragma once
#include "native_wraith_completion.hpp"
namespace passthrough {
struct NativeShadowBinding : NativeWraithBinding {uint64_t query,confirm,arrival,waitOut,waitIn,aimAnimation,priority,ready,action;std::array<unsigned char,32> actionPrefix;};
static_assert(sizeof(NativeShadowBinding)==264);
struct NativeShadowAck {
    char magic[8];uint32_t version,pid;
    uint64_t creation,generation,world,model,aim,confirm,wall;
    uint32_t phase,reserved;
};
static_assert(sizeof(NativeShadowAck)==80);
struct NativeShadowCompletion {
    uint64_t model=0,generation=0,world=0,last=0,pending=0,pendingWorld=0;bool arrivalStarted=false;
    std::atomic<uint64_t> admissions{0},completed{0},refused{0},cancelledAim{0};
    template<class Read> static bool owner(const NativeShadowBinding& b,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read){
        auto q=[&](uintptr_t a){uint64_t v=0;read(a,&v,8);return v;};
        const std::array<unsigned char,32> expected{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        std::array<unsigned char,32> code{};
        if(std::memcmp(b.magic,"OWSHAD01",8)||b.version!=2||!c.world||!c.generation||b.pid!=c.pid||b.creation!=c.creation||h.hero!=0x02e0000000000002ULL
            ||b.admin!=q(c.base+0x17b7f90)||b.localId!=h.localId||b.modelId!=h.modelId||b.model!=h.model
            ||uint32_t(q(h.reference+0x94))!=h.modelId||q(h.model+0x28)!=b.admin
            ||q(b.script+0x150)!=0x05800000000000f2ULL||q(b.script+0x160)!=b.graph||q(b.script+0x98)!=b.bag
            ||q(q(q(b.script+0x10)+0x450)+8)!=h.model||b.function!=c.plugin+0x7acd0||b.prefix!=expected||!read(b.function,code.data(),32)||code!=expected)return false;
        auto storage=q(b.graph+0x50),flag=q(b.graph+0x58);if(flag!=1&&flag!=2)return false;
        auto items=q(storage+(flag==1?0:8)),count=q(storage+(flag==1?8:0));if(count!=89)return false;
        for(auto node:std::array<std::array<uint64_t,3>,10>{{{52,b.cast,0x150b738},{25,b.animation,0x15138c0},{2,b.query,0x151a868},{47,b.confirm,0x1517770},{26,b.arrival,0x15138c0},{17,b.waitOut,0x150bd08},{18,b.waitIn,0x150bd08},{53,b.aimAnimation,0x15138c0},{16,b.priority,0x150b738},{5,b.ready,0x1500590}}})
            if(q(items+node[0]*8)!=node[1]||q(node[1])!=c.base+node[2])return false;
        const std::array<unsigned char,32> actionCode{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0xb9,0x60,1,0,0,0x48,0x8b,0xd9,0x48,0x63,0xf2,0x48,0x83,0x7f,0x50};
        return b.castVtable==c.base+0x150b738&&b.animationVtable==c.base+0x15138c0&&q(q(items+60*8))==c.base+0x1519170
            &&b.action==c.plugin+0x7abc0&&b.actionPrefix==actionCode&&read(b.action,code.data(),32)&&code==actionCode;
    }
    static bool receipt(const NativeShadowAck* a,const DeadeyePresentationContext& c,const NativeLocalHero& h){
        return a&&!std::memcmp(a->magic,"OWSHDA01",8)&&a->version==1&&a->pid==c.pid&&a->creation==c.creation&&a->generation==c.generation&&a->world==c.world&&a->model==h.modelId
            &&a->aim&&a->confirm>=a->aim&&a->wall<=c.now+50&&c.now<=a->wall+250&&a->phase>=1&&a->phase<=3&&!a->reserved;
    }
    template<class Read,class Invoke> bool update(const NativeShadowBinding* b,const NativeShadowAck* ack,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Invoke invoke){
        if(!b)return false;
        if(!owner(*b,c,h,read)){model=generation=world=last=pending=0;return false;}
        uint64_t confirm=0,aim=0,root=0;bool confirmed=false,aiming=false,casting=false;
        if(!NativeDeadeyePresentation::state(b->logger,b->script,47,confirm,confirmed,read)||!NativeDeadeyePresentation::state(b->logger,b->script,2,aim,aiming,read)||!NativeDeadeyePresentation::state(b->logger,b->script,52,root,casting,read))return false;
        if(model!=h.modelId||generation!=c.generation){model=h.modelId;generation=c.generation;world=c.world;last=confirm;pending=0;return false;}
        if(world!=c.world){
            world=c.world;
            // The MC confirmation can precede its file receipt. If a portal
            // wins that race, no native departure was admitted, but the
            // original selector still owns the gun priority. Cancel that
            // current native selector; do not activate an old-world warp.
            if(!pending&&aiming){last=confirm;invoke(b->function,b->script,16,false);invoke(b->function,b->script,5,true);++cancelledAim;return true;}
        }
        bool accepted=receipt(ack,c,h);
        if(!pending&&confirm>last&&accepted&&ack->phase==1&&ack->confirm==confirm&&ack->aim==aim&&aiming){
            last=pending=confirm;pendingWorld=c.world;arrivalStarted=false;++admissions;
            // Only isolated original client animations are replayed. Do not
            // execute the original server coordinate-warp subtree with absent
            // OW-map target outputs. MC has already validated its real ground.
            invoke(b->function,b->script,2,false);invoke(b->function,b->script,53,false);
            invoke(b->function,b->script,25,true);invoke(b->action,b->script,60,true);return true;
        }
        if(!pending)return false;
        bool cancellation=c.world!=pendingWorld;
        uint64_t departure=0,arrival=0;bool departing=false,arriving=false;
        if(!NativeDeadeyePresentation::state(b->logger,b->script,25,departure,departing,read)||departure<pending||departing)return false;
        if(!arrivalStarted){
            if(!cancellation&&!(accepted&&ack->confirm==pending&&ack->phase>=2))return false;
            arrivalStarted=true;invoke(b->function,b->script,26,true);return true;
        }
        if(!NativeDeadeyePresentation::state(b->logger,b->script,26,arrival,arriving,read)||arrival<pending||arriving)return false;
        pending=0;invoke(b->function,b->script,16,false);invoke(b->function,b->script,5,true);++completed;
        return true;
    }
};
}
