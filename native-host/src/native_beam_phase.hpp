#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace passthrough {
// Fed only by the original ChaseVar Begin/End and original script clock.
// Ammo is interpolated by the native engine and committed at End, so an ammo
// delta observer cannot provide continuous damage.
struct NativeBeamPhase {
    bool active=false;
    uint64_t begin=0,cursor=0;
    double budgetMs=0;
    bool start(uint64_t clock,double ammo,double rate){
        if(!clock||!std::isfinite(ammo)||ammo<=0||ammo>100||rate!=20)return false;
        active=true;begin=cursor=clock;budgetMs=ammo/rate*1000;return true;
    }
    double advance(uint64_t clock){
        if(!active)return 0;
        if(clock<cursor){reset();return 0;}
        double elapsed=std::min(double(clock-begin),budgetMs);
        double prior=std::min(double(cursor-begin),budgetMs);
        auto gap=clock-cursor;cursor=clock;
        // A stalled/unavailable source never releases accumulated old damage.
        if(gap>250)return 0;
        return std::max(0.0,elapsed-prior)/1000;
    }
    void reset(){active=false;begin=cursor=0;budgetMs=0;}
};
}
