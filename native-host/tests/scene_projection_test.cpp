#include "../src/scene_projection.hpp"
#include <cassert>
#include <iostream>
int main() {
    std::array<float,136> values{};
    values[0]=-.803333223f;values[3]=1;values[5]=1.42814779f;values[10]=1.00004995f;values[11]=1;values[14]=-.100005f;
    for(int i=0;i<4;i++) {values[16+i*5]=1;values[32+i*5]=1;}
    values[112]=1.f/2560;values[113]=1.f/1440;NativeProjection decoded{};
    assert(decodeSceneProjection(values,2560,1440,decoded));
    auto clip=projectNative({1,0,4},decoded,2560,1440);
    assert(std::abs(clip.x+.803333223f)<.00001f&&clip.w==4); // Packed mode flag must not enter clip W.
    NativeProjection crosshair=decoded;crosshair.viewToClip[0]=-1.12820041f;crosshair.viewToClip[5]=2.00568986f;
    auto wrong=projectNative({1,0,4},crosshair,2560,1440);
    assert(wrong.x/clip.x>1.4f); // Reproduces the observed magnification mismatch.
    auto bad=values;bad[32]=2;assert(!decodeSceneProjection(bad,2560,1440,decoded));
    assert(!decodeSceneProjection(values,1280,720,decoded));
    bad=values;bad[5]=NAN;assert(!decodeSceneProjection(bad,2560,1440,decoded));
    bad=values;bad[0]=.8f;assert(!decodeSceneProjection(bad,2560,1440,decoded));
    values[28]=-10;values[44]=10;assert(decodeSceneProjection(values,2560,1440,decoded));
    auto translated=projectNative({10,0,4},decoded,2560,1440);assert(std::abs(translated.x)<.0001f);
    std::cout<<"Actual scene versus crosshair magnification regression, packed flag, inverse/view, viewport, finite/sign and world translation passed.\n";
}
