#pragma once
#include <array>
#include <cmath>

inline bool isGenjiViewmodelLens(const std::array<float,136>& values) {
    for(unsigned i=0;i<16;i++)if(!std::isfinite(values[i]))return false;
    // Actual Genji idle and Dragonblade draw-in narrowed the viewmodel lens
    // continuously from 2.005690 to 2.355852. The world lens stays 1.428148.
    return values[5]>=2.003f&&values[5]<=2.358f
        &&std::abs(-values[0]*16.f/9-values[5])<.002f
        &&std::abs(values[3]-1)<.0001f&&std::abs(values[11]-1)<.0001f
        &&std::abs(values[10]-1.00005f)<.0001f
        &&std::abs(values[14]+.100005f)<.0001f&&std::abs(values[15])<.0001f;
}
