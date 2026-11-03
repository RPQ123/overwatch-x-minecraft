#include "../src/math.hpp"
#include <cassert>
#include <cmath>

int main() {
    Camera camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f};
    auto center = project({0,0,4}, camera, 16.f/9);
    assert(std::abs(center.x) < 1e-6f && std::abs(center.y) < 1e-6f && center.w == 4);
    auto right = project({1,0,4}, camera, 16.f/9);
    assert(right.x > 0 && right.z > 0 && right.z < right.w);
    auto up = project({0,1,4}, camera, 16.f/9);
    assert(up.y > 0);
    camera.position.x = 1;
    auto moved = project({0,0,4}, camera, 16.f/9);
    assert(moved.x < 0); // Fixed world marker must move on screen as the host moves.
    camera.position = {0,0,0}; camera.forward = {1,0,0};
    auto rotated = project({4,0,0}, camera, 16.f/9);
    assert(std::abs(rotated.x) < 1e-6f);
    camera.up = {1,0,0};
    assert(!validCamera(camera));
    // A native host may carry a signed horizontal projection and a different FOV.
    // Retain those exact matrices rather than rebuilding them from guessed axes.
    NativeProjection native{{1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1},
                            {-1,0,0,0, 0,2,0,0, 0,0,1,1, 0,0,-.1f,0},0,0,128,72};
    assert(validProjection(native));
    auto nativeRight=projectNative({1,0,4},native,128,72);
    assert(nativeRight.x==-1 && nativeRight.y==0 && nativeRight.w==4);
    auto nativeUp=projectNative({0,1,4},native,128,72);assert(nativeUp.y==2);
    native.worldToView[12]=-1;
    auto translated=projectNative({1,0,4},native,128,72);assert(translated.x==0);
    native.worldToView[12]=0;native.left=64;
    auto partialViewport=projectNative({0,0,4},native,128,72);assert(partialViewport.x==2);
    native.viewToClip[0]=NAN;assert(!validProjection(native));
}
