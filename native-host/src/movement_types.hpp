#pragma once
#include "math.hpp"
struct MotionPose {
    Vec3 foot,scene,eye,state1Foot,delta,gravity,copiedEye;
    int state1Tick=0,state2Tick=0;unsigned flags=0;
};
