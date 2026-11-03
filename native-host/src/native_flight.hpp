#pragma once
#include "guest_body.hpp"
namespace passthrough {
inline bool nativeMotorHero(uint64_t hero){
    for(uint64_t suffix:{2ULL,5ULL,6ULL,10ULL,0x15ULL,0xddULL,0x6eULL})if(hero==(0x02e0000000000000ULL|suffix))return true;
    return false;
}
inline bool validNativeFlight(Vec3 position,Vec3 velocity,Vec3 gravity){
    return std::isfinite(dot(position,position))&&std::isfinite(dot(velocity,velocity))&&std::isfinite(dot(gravity,gravity))
        &&dot(velocity,velocity)<=10000&&dot(gravity,gravity)<=10000;
}
struct NativeFlightAccumulator {
    bool ready=false;uint32_t model=0;uint64_t world=0,generation=0;
    Vec3 previous{};std::array<double,3> total{};
    bool capture(const GuestBody& guest,uint32_t currentModel,Vec3 nativePosition,Vec3 nativeVelocity){
        if(!guest.nativeFlight||guest.flightModel!=currentModel){ready=false;return false;}
        if(!ready||model!=currentModel||world!=guest.worldId||generation!=guest.generation){
            ready=false;model=currentModel;world=guest.worldId;generation=guest.generation;total={};return false;
        }
        auto delta=nativePosition-previous;
        if(!std::isfinite(dot(delta,delta))||dot(delta,delta)>9||!std::isfinite(dot(nativeVelocity,nativeVelocity))||dot(nativeVelocity,nativeVelocity)>10000){ready=false;return false;}
        total[0]+=delta.x;total[1]+=delta.y;total[2]+=delta.z;return true;
    }
    void applied(Vec3 position){previous=position;ready=true;}
};
}
