#include "../src/hanzo_control.hpp"
#include <array>
#include <cassert>
#include <iostream>
using namespace passthrough;
int main(){
    std::array<unsigned char,256> data{};
    auto u32=[&](int at,uint32_t v){std::memcpy(data.data()+at,&v,4);};
    auto u64=[&](int at,uint64_t v){std::memcpy(data.data()+at,&v,8);};
    u32(16,10);u32(20,11);u64(24,12);u64(32,13);u64(136,14);u64(72,1000);
    u32(232,0x315a4e48);u32(236,15);u64(240,1000);u64(248,99);
    assert(!decodeHanzoControl(data.data()).model); // HNZ1 grants no free camera path.
    u32(232,0x325a4e48);auto r=decodeHanzoControl(data.data());
    HanzoControlContext c{10,11,15,12,13,14,1000,0x02e0000000000005ULL,true,true};
    assert(hanzoMotionActive(r,c));assert(r.begin==99);
    for(int i=0;i<10;i++){
        auto bad=c;
        switch(i){case 0:bad.hostPid++;break;case 1:bad.guestPid++;break;case 2:bad.model++;break;case 3:bad.generation++;break;
        case 4:bad.hostGeneration++;break;case 5:bad.world++;break;case 6:bad.foreground=false;break;case 7:bad.cursorHidden=false;break;
        case 8:bad.hero++;break;case 9:bad.now=1151;break;}
        assert(!hanzoMotionActive(r,bad));
    }
    auto zero=r;zero.begin=0;assert(!hanzoMotionActive(zero,c));
    auto stale=r;stale.observed=849;assert(!hanzoMotionActive(stale,c));
    assert(sameHanzoCast(r,r));auto other=r;other.begin++;assert(!sameHanzoCast(r,other));
    u32(232,0);assert(!decodeHanzoControl(data.data()).model);
    std::cout<<"Hanzo HNZ2 native scope PASS; no write/camera-selection API exists\n";
}
