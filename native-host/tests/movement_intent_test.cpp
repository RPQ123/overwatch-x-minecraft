#include "../src/movement_intent.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main() {
    MovementIntent input;assert(!input.snapshot(1,true));
    input.key(4,true,10);input.key(4,false,11);assert(input.snapshot(50,true)==16);assert(!input.snapshot(110,true));
    input.key(0,true,200);assert(input.snapshot(900,true)==1);input.key(0,false,901);assert(!input.snapshot(901,true));
    input.key(0,true,1000);input.key(3,true,1000);assert(input.snapshot(1001,true)==9);
    assert(!input.snapshot(1002,false)&&!input.snapshot(1003,true));input.key(99,true,2000);assert(!input.snapshot(2001,true));
    std::cout<<"PASS: render/tick gap retains short jump tap, held movement, bounded release, diagonal intent and immediate focus-loss flush.\n";
}
