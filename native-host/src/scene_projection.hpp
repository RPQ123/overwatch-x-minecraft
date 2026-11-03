#pragma once
#include "math.hpp"
#include <array>
#include <cstring>

// Observed original beta global camera buffer (VS slot 9, 544 bytes).
// Its first 16 floats are packed projection constants, not a raw 4x4:
// element 3 is a mode flag. The view and inverse-view follow at 16/32.
inline bool decodeSceneProjection(const std::array<float,136>& values,float width,float height,NativeProjection& out) {
    if(width<=0||height<=0||width>16384||height>16384) return false;
    for(unsigned i=0;i<48;i++) if(!std::isfinite(values[i])) return false;
    if(values[0]>=-.01f||values[5]<=.01f||std::abs(values[3]-1)>.0001f
       ||std::abs(values[11]-1)>.0001f||values[14]>=0||std::abs(values[15])>.0001f
       ||!std::isfinite(values[112])||!std::isfinite(values[113])
       ||std::abs(values[112]*width-1)>.001f||std::abs(values[113]*height-1)>.001f
       ||std::abs(-values[0]*width/height-values[5])>.005f) return false;
    for(unsigned i:{1u,2u,4u,6u,7u,8u,9u,12u,13u}) if(std::abs(values[i])>.0001f) return false;
    NativeProjection candidate{};std::memcpy(candidate.worldToView,values.data()+16,64);
    // Validate the paired inverse rather than mistaking object/world constants for a camera.
    for(unsigned row=0;row<4;row++) for(unsigned column=0;column<4;column++) {
        float value=0;for(unsigned k=0;k<4;k++) value+=values[16+row*4+k]*values[32+k*4+column];
        if(std::abs(value-(row==column?1.f:0.f))>.002f) return false;
    }
    candidate.viewToClip[0]=values[0];candidate.viewToClip[5]=values[5];candidate.viewToClip[10]=values[10];
    candidate.viewToClip[11]=values[11];candidate.viewToClip[14]=values[14];candidate.right=width;candidate.bottom=height;
    if(!validProjection(candidate)) return false;
    out=candidate;return true;
}
