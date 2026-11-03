#include "../src/creative_motion.hpp"
#include <cassert>
#include <iostream>
int main() {
    CreativeFlight flight;flight.update(0x100,1000);assert(!flight.enabled);
    flight.update(0x100,1100);assert(!flight.enabled); // Holding jump is not double tap.
    flight.update(0,1150);flight.update(0x100,1200);assert(flight.enabled&&flight.vertical(0x100)>0);
    assert(flight.vertical(0)==0&&flight.vertical(0x200)<0&&flight.vertical(0x300)==0);
    flight.update(0,1250);flight.update(0x100,2000);assert(flight.enabled);
    flight.update(0,2100);flight.update(0x100,2200);assert(!flight.enabled);
    std::cout<<"Creative flight double-tap, hold debounce, ascent/descent/hover and toggle-off passed.\n";
}
