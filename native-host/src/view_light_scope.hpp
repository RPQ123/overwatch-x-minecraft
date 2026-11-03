#pragma once
#include <cstdint>
namespace passthrough {
// Render-owner state only. Worker candidates carry this epoch, so a packet
// sampled for a departed hero/world cannot reacquire a new light ownership.
struct ViewLightIdentity {
    uint64_t hero=0,model=0,source=0,generation=0,world=0;
    bool operator==(const ViewLightIdentity& b) const{return hero==b.hero&&model==b.model&&source==b.source&&generation==b.generation&&world==b.world;}
    bool valid() const{return hero&&model&&source&&generation&&world;}
};
struct ViewLightScope {
    ViewLightIdentity identity{};uint64_t epoch=0,poseBarrier=0;
    bool transition(ViewLightIdentity next,uint64_t pose){
        if(next==identity)return false;
        identity=next;++epoch;poseBarrier=pose;return true;
    }
    bool accepts(uint64_t candidateEpoch,uint64_t sampled,uint64_t now,uint64_t pose)const{
        return identity.valid()&&candidateEpoch==epoch&&sampled<=now&&now-sampled<=250&&pose>poseBarrier;
    }
};
}
