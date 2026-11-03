#pragma once
#include "genji_viewmodel_lens.hpp"

inline bool isSupportedViewmodelLens(const std::array<float,136>& values){
    if(isGenjiViewmodelLens(values))return true;
    for(unsigned i=0;i<16;i++)if(!std::isfinite(values[i]))return false;
    // Original McCree crosshair projection (60deg) and Winston's actual draw
    // trace (55deg). Keep narrow windows, excluding the 70deg world camera.
    // All 21 loaded beta hero definitions were read on this PC. Additional
    // original first-person FOVs are45/50/65;50 is within Genji's existing range.
    bool hero=std::abs(values[5]-1.73205078f)<.002f||std::abs(values[5]-1.920982f)<.002f
        ||std::abs(values[5]-2.41421356f)<.002f||std::abs(values[5]-1.56968558f)<.002f;
    return hero&&std::abs(-values[0]*16.f/9-values[5])<.002f
        &&std::abs(values[3]-1)<.0001f&&std::abs(values[11]-1)<.0001f
        &&std::abs(values[10]-1.00005f)<.0001f
        &&std::abs(values[14]+.100005f)<.0001f&&std::abs(values[15])<.0001f;
}
