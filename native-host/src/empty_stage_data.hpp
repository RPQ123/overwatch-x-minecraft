#pragma once
#include <array>
#include <cstdint>
#include <cstring>

namespace owmc {
// Exact owned 24919 Lobby_Final map header before the native relative-pointer
// fixup. The original archive is never modified. Map instances use 16 typed
// placeable ranges at 0x210/0x250/0x290; auxiliary geometry follows at 0x2d0.
inline bool emptyStageHeader(std::array<unsigned char,0x320>& header) {
    uint64_t hash=14695981039346656037ULL;
    for(auto byte:header)hash=(hash^byte)*1099511628211ULL;
    if(hash!=0x51b0e353051a410dULL)return false;
    // Environment effect/model-look and the map-only sound-space resource.
    // Hero audio resources and the native sound system are untouched.
    std::memset(header.data()+0x110,0,24);
    std::memset(header.data()+0x200,0,0x120);
    return true;
}
}
