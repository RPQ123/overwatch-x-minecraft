#pragma once
#include "math.hpp"
#include <cstdint>
struct CreativeFlight {
    bool enabled=false,jumpHeld=false;uint64_t lastJump=0;
    void update(unsigned buttons,uint64_t milliseconds) {
        bool jump=(buttons&0x100)!=0;
        if(jump&&!jumpHeld) {
            if(lastJump&&milliseconds>=lastJump&&milliseconds-lastJump<=350) {enabled=!enabled;lastJump=0;}
            else lastJump=milliseconds;
        }jumpHeld=jump;
    }
    float vertical(unsigned buttons) const {return enabled?((buttons&0x100?1.f:0)-(buttons&0x200?1.f:0))*6.f*.016f:0;}
};
