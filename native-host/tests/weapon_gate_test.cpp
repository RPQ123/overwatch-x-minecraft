#include "../src/weapon_gate.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main(){
    assert(passthrough::measuredWeaponGateFlags(0x408001)&&passthrough::measuredWeaponGateFlags(0x400081)&&passthrough::measuredWeaponGateFlags(0x400089));
    assert(passthrough::measuredWeaponGateFlags(0x400001)&&passthrough::measuredWeaponGateFlags(0x400009));
    assert(!passthrough::measuredWeaponGateFlags(0x400101)&&!passthrough::measuredWeaponGateFlags(0xffffffff));
    constexpr uint64_t bastion=0x02e0000000000015ULL,tank=0x058000000000024fULL;
    assert(!measuredWeaponGateFlags(0x408003)&&!measuredWeaponGateFlags(0x40800b));
    assert(measuredBastionTankGateFlags(bastion,tank,25,0x408003));
    assert(measuredBastionTankGateFlags(bastion,tank,25,0x40800b));
    assert(measuredBastionTankGateFlags(bastion,tank,25,0x400083)); // actual native Begin callback
    assert(measuredBastionTankGateFlags(bastion,tank,25,0x40008b)); // nested authority
    assert(!measuredBastionTankGateFlags(0x02e0000000000042ULL,tank,25,0x408003));
    assert(!measuredBastionTankGateFlags(bastion,0x058000000000012eULL,25,0x408003));
    assert(!measuredBastionTankGateFlags(bastion,tank,24,0x408003));
    assert(!measuredBastionTankGateFlags(bastion,tank,11,0x408003)); // runtime state index is not node index
    for(uint32_t flags:{0x400003u,0xc00083u,0xc08003u,0x408023u,0x408001u,0xffffffffu})
        assert(!measuredBastionTankGateFlags(bastion,tank,25,flags));
    volatile LONG flags=0x408001;
    auto value=withWeaponGate(&flags,[&]{
        assert(flags==0x408009);
        auto nested=withWeaponGate(&flags,[&]{assert(flags==0x408009);return 27;});
        assert(nested==27&&flags==0x408009);InterlockedOr(&flags,0x100);return uintptr_t(0x123456789);
    });
    assert(value==0x123456789&&flags==0x408101);
    flags=0x408009;withWeaponGate(&flags,[&]{assert(flags==0x408009);return 0;});assert(flags==0x408009);
    flags=0x408001;try{withWeaponGate(&flags,[]{throw 1;return 0;});}catch(int){}assert(flags==0x408001);
    std::cout<<"Scoped native weapon bit, nested ownership, original return, unrelated changes and exception restoration passed.\n";
}
