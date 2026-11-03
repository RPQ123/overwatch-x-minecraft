#pragma once
#include "math.hpp"
#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>

namespace passthrough {
struct GuestBody {
    uint64_t sequence{},wallMs{},generation{},hostGeneration{},worldId{};
    uint32_t sourcePid{},hostPid{};
    Vec3 foot{},velocity{};bool grounded=false;
    uint32_t climbModel=0;bool climbing=false;
    uint32_t flightModel=0,blockedAxes=0;bool nativeFlight=false;
    uint32_t deadeyeModel=0;bool deadeyeFiring=false;
    uint64_t deadeyeBegin=0,deadeyeScript=0,deadeyeLogger=0,deadeyeObserved=0,deadeyeWorld=0;
};
inline GuestBody decodeGuestBody(const unsigned char* b,uint64_t now,uint32_t pid) {
    auto u32=[&](size_t n){uint32_t v;std::memcpy(&v,b+n,4);return v;};
    auto u64=[&](size_t n){uint64_t v;std::memcpy(&v,b+n,8);return v;};
    if(std::memcmp(b,"OWBODY01",8)||u32(8)!=1||u32(12)!=256||u32(16)!=pid||!u32(20)||!u64(24)||!u64(32))throw std::runtime_error("Guest body identity");
    GuestBody s;s.hostPid=pid;s.sourcePid=u32(20);s.generation=u64(24);s.hostGeneration=u64(32);s.sequence=u64(64);s.wallMs=u64(72);
    if(!s.sequence||(s.sequence&1)||s.wallMs>now||now-s.wallMs>250||u32(80)>1||u32(84)!=0)throw std::runtime_error("Guest body stale/flags");
    s.grounded=u32(80)!=0;
    s.worldId=u64(136);
    if(!s.worldId)throw std::runtime_error("Guest body world is not ready");
    std::array<float,3> position{},velocity{};
    for(unsigned i=0;i<3;i++) {
        double p;float v;std::memcpy(&p,b+96+i*8,8);std::memcpy(&v,b+120+i*4,4);
        if(!std::isfinite(p)||std::abs(p)>30000000||!std::isfinite(v)||std::abs(v)>100)throw std::runtime_error("Guest body numeric bounds");
        position[i]=float(p);velocity[i]=v;
    }
    s.foot={position[0],position[1],position[2]};s.velocity={velocity[0],velocity[1],velocity[2]};
    // CLM2 is a contact-state extension, ignored by legacy v1 body consumers.
    // There is deliberately no guessed native contact vector or profile index.
    if(u32(144)){
        if(u32(144)!=0x324d4c43||u32(148)>1)throw std::runtime_error("Guest climb extension");
        s.climbing=u32(148)!=0;s.climbModel=u32(152);
        if(s.climbing&&(!s.climbModel||s.grounded))throw std::runtime_error("Guest climb identity/ground");
    }
    if(u32(160)){
        if(u32(160)!=0x31594c46||u32(164)>1||u32(172)>7)throw std::runtime_error("Guest native flight extension");
        s.nativeFlight=u32(164)!=0;s.flightModel=u32(168);s.blockedAxes=u32(172);
        if(s.nativeFlight&&!s.flightModel)throw std::runtime_error("Guest native flight model absent");
    }
    // DEY1 is control suppression after an actual same-cast native fire.
    // Legacy body consumers ignore this otherwise unused tail. No script call
    // or attack is authorized by this extension.
    if(u32(176)){
        if(u32(176)!=0x31594544||u32(180)>1||u32(188))throw std::runtime_error("Guest Deadeye input extension");
        s.deadeyeFiring=u32(180)!=0;s.deadeyeModel=u32(184);s.deadeyeBegin=u64(192);s.deadeyeScript=u64(200);
        s.deadeyeLogger=u64(208);s.deadeyeObserved=u64(216);s.deadeyeWorld=u64(224);
        if(s.deadeyeFiring&&(!s.deadeyeModel||!s.deadeyeBegin||s.deadeyeScript<0x10000||s.deadeyeScript>0x7fffffffffffULL
            ||s.deadeyeLogger<0x10000||s.deadeyeLogger>0x7fffffffffffULL||!s.deadeyeObserved
            ||s.deadeyeWorld!=s.worldId))throw std::runtime_error("Guest Deadeye input identity");
        if(!s.deadeyeFiring&&(s.deadeyeModel||s.deadeyeBegin||s.deadeyeScript||s.deadeyeLogger||s.deadeyeObserved||s.deadeyeWorld))
            throw std::runtime_error("Guest Deadeye inactive input payload");
    }
    return s;
}
// MC is the sole position authority. Native uses a small virtual coordinates
// region clear of the old map; no MC coordinate is written by this adapter.
struct BodyAnchor {
    bool ready=false;uint64_t generation=0,hostGeneration=0,worldId=0;uint32_t sourcePid=0;Vec3 first{};
    // Set for the packet which first arrives from a different MC dimension.
    // The native hook uses this edge to hold one callback while the new
    // dimension's pose and hero binding settle.
    bool worldChanged=false;
    Vec3 target(const GuestBody& s) {
        worldChanged=false;
        if(!s.worldId)throw std::runtime_error("Guest body world identity absent");
        if(!ready){first=s.foot;generation=s.generation;hostGeneration=s.hostGeneration;worldId=s.worldId;sourcePid=s.sourcePid;ready=true;}
        if(s.worldId!=worldId){
            // A real Nether/End transfer keeps the same guest process and
            // native host generation. Rebase the MC displacement origin at
            // the first body packet in the new dimension instead of applying
            // the old Overworld offset to the new world.
            if(s.hostGeneration!=hostGeneration||s.sourcePid!=sourcePid)throw std::runtime_error("Guest body world session changed");
            first=s.foot;worldId=s.worldId;generation=s.generation;
            worldChanged=true;
        }
        if(s.generation!=generation||s.hostGeneration!=hostGeneration||s.sourcePid!=sourcePid)throw std::runtime_error("Guest body session changed");
        auto d=s.foot-first;
        if(dot(d,d)>4096.f*4096.f)throw std::runtime_error("Guest body rebase required");
        return Vec3{1000,1000,1000}+d;
    }
    // Explicit opt-in by the v4 adapter after the packet's freshness, PID and
    // host identity have passed. Preserve the original displacement anchor.
    bool resumeSameWorld(const GuestBody& s) {
        if(!ready||!worldId||s.worldId!=worldId||s.hostGeneration!=hostGeneration)return false;
        if(dot(s.foot-first,s.foot-first)>4096.f*4096.f)return false;
        generation=s.generation;sourcePid=s.sourcePid;return true;
    }
    bool resumeSession(const GuestBody& s) {
        if(!ready||!s.worldId||!s.generation||!s.sourcePid||s.hostGeneration!=hostGeneration)return false;
        if(s.worldId==worldId)return resumeSameWorld(s);
        // A validated replacement MC process may open another save/dimension.
        // Keep worldId until target() observes/rebases that real world edge.
        generation=s.generation;sourcePid=s.sourcePid;return true;
    }
};
struct BodyStability {
    uint64_t world=0,generation=0,sequence=0;uint32_t source=0;unsigned ticks=0;
    bool observe(const GuestBody& s,bool fresh){
        if(!fresh){ticks=0;sequence=0;return false;}
        if(world!=s.worldId||generation!=s.generation||source!=s.sourcePid){
            world=s.worldId;generation=s.generation;source=s.sourcePid;ticks=0;sequence=0;
        }
        if(s.sequence!=sequence){sequence=s.sequence;if(ticks<3)++ticks;}
        return ticks>=2;
    }
};
inline unsigned bodyFlags(unsigned previous,const GuestBody& s) {
    // Source MovementState: 0x200 default, 0x5 jumping, 0x8 falling.
    // Preserve crouch/ability bits; clear known air and wall-contact bits.
    previous&=~(0x28du|0x20000u);
    const unsigned motion=s.grounded?0x200u:(s.velocity.y>0?0x5u:0x8u);
    return previous|motion|(s.climbing?0x80u:0u);
}
}
