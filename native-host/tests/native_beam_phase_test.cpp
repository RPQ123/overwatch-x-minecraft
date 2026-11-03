#include "../src/native_beam_phase.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
int main(){
    passthrough::NativeBeamPhase p;
    assert(p.advance(50)==0&&p.start(1000,100,20));
    double seconds=0;for(unsigned t=1016;t<=2024;t+=16)seconds+=p.advance(t);
    assert(std::abs(seconds-1.024)<1e-8);assert(p.advance(2024)==0);
    p.reset();assert(p.advance(2040)==0);
    assert(p.start(3000,100,20));assert(std::abs(p.advance(3016)-.016)<1e-8);p.reset();
    assert(p.start(4000,.1,20));assert(std::abs(p.advance(4016)-.005)<1e-8);assert(p.advance(4032)==0);
    assert(p.start(5000,100,20));assert(p.advance(5400)==0);assert(std::abs(p.advance(5416)-.016)<1e-8);
    assert(p.advance(10)==0&&!p.active);assert(!p.start(0,100,20));assert(!p.start(10,101,20));
    std::cout<<"Native beam phase: continuous clock, short release, depletion, duplicate, stall and clock-reset checks passed.\n";
}
