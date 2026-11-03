#pragma once
#include <array>
#include <cmath>
#include <cstdint>

namespace passthrough {
// Actual compositor41 evidence: current original Tracer Blink moves its hand
// projection through1.74013..1.98089; its simultaneous world stays1.30595..1.38181.
// This recognizes that SAME FRAME's original draw, never modifies native FOV,
// requests an animation, watches Shift, guesses a duration or replays hand pixels.
inline bool isTracerBlinkViewmodelLens(const std::array<float,136>& values,uint64_t hero,unsigned viewMode){
    if(hero!=0x02e0000000000003ULL||viewMode!=1)return false;
    for(unsigned i=0;i<16;i++)if(!std::isfinite(values[i]))return false;
    // Small measured margins; upper bound overlaps the existing Genji/50deg
    // recognizer's2.003 lower bound, preventing a classification seam.
    if(values[5]<1.738f||values[5]>2.005f)return false;
    if(std::abs(-values[0]*16.f/9-values[5])>=.002f
       ||std::abs(values[3]-1)>=.0001f||std::abs(values[11]-1)>=.0001f
       ||std::abs(values[10]-1.00005f)>=.0001f
       ||std::abs(values[14]+.100005f)>=.0001f||std::abs(values[15])>=.0001f)return false;
    for(unsigned i:{1u,2u,4u,6u,7u,8u,9u,12u,13u})if(std::abs(values[i])>=.0001f)return false;
    return true;
}
}
