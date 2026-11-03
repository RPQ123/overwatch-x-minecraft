#include "../src/native_flight.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main(){
    assert(nativeMotorHero(0x02e000000000006eULL)&&nativeMotorHero(0x02e0000000000015ULL));
    assert(!nativeMotorHero(0x02e0000000000029ULL)&&!nativeMotorHero(0x02e0000000000008ULL));
    assert(validNativeFlight({1000,1000,1000},{0,20,0},{0,0,0}));
    assert(!validNativeFlight({1000,1000,1000},{0,std::nanf(""),0},{0,0,0}));
    assert(!validNativeFlight({1000,1000,1000},{0,20,0},{0,std::nanf(""),0}));
    NativeFlightAccumulator f;GuestBody s;s.nativeFlight=true;s.flightModel=12;s.worldId=20;s.generation=30;
    assert(!f.capture(s,12,{1000,1000,1000},{0,20,0}));f.applied({1000,1000,1000});
    assert(f.capture(s,12,{1000,1000.25,1000},{0,19.8f,0}));f.applied({1000,1000,1000});
    assert(f.capture(s,12,{1000,1000.25,1000},{0,19.6f,0})&&f.total[1]==.5);
    s.worldId=21;assert(!f.capture(s,12,{1000,1000,1000},{})&&f.total[1]==0);f.applied({1000,1000,1000});
    assert(!f.capture(s,13,{1000,1000,1000},{}));
    assert(!f.capture(s,12,{1000,1000,1000},{}));f.applied({1000,1000,1000});
    assert(!f.capture(s,12,{1000,1020,1000},{}));
    s.nativeFlight=false;assert(!f.capture(s,12,{1000,1000,1000},{}));
    std::cout<<"PASS: native flight accumulates frames once, rebases dimensions/models and rejects stale enable/teleport.\n";
}
