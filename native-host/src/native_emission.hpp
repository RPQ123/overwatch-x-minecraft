#pragma once
#include "guest_body.hpp"
#include "native_barrage_motion.hpp"
#include <mutex>
#include <vector>
#include <unordered_set>
#include <deque>
#include <set>

namespace passthrough {
inline bool emissionResourceMatches(uint64_t hero,uint64_t resource){
    return (hero==0x02e0000000000029ULL&&resource==0x04000000000007caULL)
        || (hero==0x02e0000000000042ULL&&resource==0x04000000000002a7ULL)
        || (hero==0x02e0000000000009ULL&&resource==0x05800000000000feULL)
        || (hero==0x02e0000000000008ULL&&resource==0x0400000000000033ULL);
}
struct NativeEmission {
    uint64_t id=0,wallMs=0,resource=0;
    uint64_t volley=0;uint32_t kind=0;float range=0;
    uint32_t entity=0,owner=0,tick=0,shot=0,pellet=0,flags=0,result=0,componentOwner=0;
    Vec3 position{},direction{},scenePosition{},nativeFeet{},velocity{};
    GuestBody guest{};
    float damage=0,lifetime=0;
    float splashDamage=0,innerRadius=0,outerRadius=0,outerScale=0;
    uint64_t hero=0;uint32_t effect=0,bounces=0,flight=0,factoryType=0;
    float eyeHeight=0,gravity=0,fuse=0,terrain=0;
    uint32_t waveCount=0;
    std::array<BarrageWave,2> waves{};
    std::array<unsigned char,176> context{};
    std::array<unsigned char,512> projectile{};
};
template<size_t Capacity> class EmissionJournal {
    mutable std::mutex lock;
    std::deque<NativeEmission> entries;
    std::set<std::array<uint64_t,6>> entities;
    bool overflow=false;
    uint64_t nextId=0,ack=0;
public:
    EmissionJournal()=default;
    enum class Result{Accepted,Duplicate,Full};
    Result append(NativeEmission event){
        std::lock_guard<std::mutex> held(lock);
        std::array<uint64_t,6> key=event.kind!=0?std::array<uint64_t,6>{event.kind,event.owner,event.volley,event.tick,event.shot,event.pellet}:std::array<uint64_t,6>{0,event.entity,0,0,0,0};
        if(entities.count(key))return Result::Duplicate;
        if(entries.size()==Capacity||entities.size()>=1048576){overflow=true;return Result::Full;}
        event.id=++nextId;entries.push_back(event);entities.insert(key);return Result::Accepted;
    }
    bool acknowledge(uint64_t value){
        std::lock_guard<std::mutex> held(lock);if(value<ack||value>nextId)return false;
        while(!entries.empty()&&entries.front().id<=value)entries.pop_front();
        ack=value;return true;
    }
    uint64_t acknowledged()const{std::lock_guard<std::mutex> held(lock);return ack;}
    std::vector<NativeEmission> snapshot()const{std::lock_guard<std::mutex> held(lock);return {entries.begin(),entries.end()};}
    bool overflowed()const{std::lock_guard<std::mutex> held(lock);return overflow;}
};
inline std::array<unsigned char,256> encodeEmission(const NativeEmission& e){
    std::array<unsigned char,256> b{};
    auto put=[&](size_t at,const auto& value){std::memcpy(b.data()+at,&value,sizeof value);};
    put(0,e.id*2);put(8,e.id);put(16,e.wallMs);put(24,e.entity);put(28,e.owner);put(32,e.resource);
    put(40,e.position);put(52,e.direction);put(64,e.scenePosition);put(76,e.nativeFeet);
    put(88,e.guest.foot);put(100,e.guest.sourcePid);put(104,e.guest.generation);put(112,e.guest.worldId);put(120,e.guest.hostGeneration);
    put(128,e.result);put(132,e.tick);put(136,e.shot);put(140,e.pellet);put(144,e.componentOwner);put(148,e.flags);
    put(152,e.velocity);
    put(164,e.damage);put(168,e.lifetime);
    return b;
}
}
