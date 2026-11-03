#pragma once
#include "map_audio_data.hpp"

namespace owmc {
// Owned 24919 Hollywood header. Neutral daylight keeps the original directional
// light's linear luminance; only its RGB white point changes. Geometry, shadow
// transforms, probe resources and all hero materials remain native.
inline bool daylightHollywoodHeader(std::array<unsigned char,0x320>& header) {
    auto prepared=header;
    if(!quietHollywoodHeader(prepared))return false;
    float original[3]{};
    std::memcpy(original,header.data()+0x158,sizeof original);
    const float luminance=.2126f*original[0]+.7152f*original[1]+.0722f*original[2];
    const float neutral[3]{luminance,luminance,luminance};
    std::memcpy(prepared.data()+0x158,neutral,sizeof neutral);
    header=prepared;
    return true;
}
}
