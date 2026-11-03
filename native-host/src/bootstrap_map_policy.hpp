#pragma once
#include <cstdint>
namespace owmc {
constexpr uint64_t hollywoodMap=0x08000000000002afULL;
constexpr uint64_t emptyLobbyMap=0x0800000000000223ULL;
constexpr uint64_t kyotoLoginMap=0x0800000000000664ULL;
constexpr bool bootstrapMapAllowed(uint64_t id){return id==hollywoodMap||id==emptyLobbyMap||id==kyotoLoginMap;}
constexpr bool bootstrapPatchesMap(uint64_t id){return id==hollywoodMap||id==emptyLobbyMap;}
constexpr bool bootstrapMapPrepared(uint64_t id,unsigned failures,unsigned empty,unsigned quiet){
    return !failures&&bootstrapMapAllowed(id)&&(id==kyotoLoginMap||(id==emptyLobbyMap?empty:quiet)==1);
}
}
