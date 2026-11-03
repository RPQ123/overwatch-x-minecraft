#pragma once
#include <array>
#include <cstdint>
#include <cstring>

namespace owmc {
// Exact owned 24919 Hollywood map, before relative-pointer fixups. Only its
// STUSoundSpace (0x7ddbb13b) and type-12 SOUND range are removed in memory.
// Sky, light probes, geometry, entities and hero audio stay byte-identical.
inline bool quietHollywoodHeader(std::array<unsigned char,0x320>& header) {
    uint64_t hash=14695981039346656037ULL;
    for(auto byte:header)hash=(hash^byte)*1099511628211ULL;
    if(hash!=0x845f1cd9031e5cd6ULL)return false;
    std::memset(header.data()+0x120,0,8);
    for(auto offset:{0x240,0x280,0x2c0})std::memset(header.data()+offset,0,4);
    return true;
}
}
