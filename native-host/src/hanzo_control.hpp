#pragma once
#include <cstdint>
#include <cstring>

namespace passthrough {
// HNZ2 is a fresh same-cast suppression request. Never selects/writes a native camera.
struct HanzoControlRequest {
    uint32_t hostPid=0,guestPid=0,model=0;uint64_t generation=0,hostGeneration=0,world=0,wall=0,observed=0,begin=0;
};
inline HanzoControlRequest decodeHanzoControl(const unsigned char* b){
    auto u32=[&](int at){uint32_t v=0;std::memcpy(&v,b+at,4);return v;};
    auto u64=[&](int at){uint64_t v=0;std::memcpy(&v,b+at,8);return v;};
    if(u32(232)!=0x325a4e48)return {};
    return {u32(16),u32(20),u32(236),u64(24),u64(32),u64(136),u64(72),u64(240),u64(248)};
}
struct HanzoControlContext {
    uint32_t hostPid=0,guestPid=0,model=0;uint64_t generation=0,hostGeneration=0,world=0,now=0,hero=0;
    bool foreground=false,cursorHidden=false;
};
inline bool sameHanzoCast(const HanzoControlRequest& a,const HanzoControlRequest& b){
    return a.begin&&a.begin==b.begin&&a.model==b.model&&a.hostPid==b.hostPid&&a.guestPid==b.guestPid
        &&a.generation==b.generation&&a.hostGeneration==b.hostGeneration&&a.world==b.world;
}
inline bool hanzoMotionActive(const HanzoControlRequest& r,const HanzoControlContext& c){
    return c.foreground&&c.cursorHidden&&c.hero==0x02e0000000000005ULL&&r.begin>0&&r.model&&r.model==c.model
        &&c.hostPid&&c.guestPid&&c.generation&&c.hostGeneration&&c.world
        &&r.hostPid==c.hostPid&&r.guestPid==c.guestPid&&r.generation==c.generation&&r.hostGeneration==c.hostGeneration&&r.world==c.world
        &&r.wall&&r.wall<=c.now&&c.now-r.wall<=150&&r.observed&&r.observed<=c.now&&c.now-r.observed<=150;
}
}
