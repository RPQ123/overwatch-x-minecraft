#include "../src/movement_types.hpp"
#include <windows.h>
#include <cassert>
#include <iostream>

MotionPose fixture{};
uintptr_t WINAPI fakeTick(void*,UINT cf) {fixture.foot.x+=1;fixture.scene=fixture.foot;fixture.state1Tick=cf;fixture.state2Tick=cf;return 0x12345678+cf;}
void WINAPI before(void*) {}
void WINAPI fakeAfter(void*) {fixture.eye=fixture.foot+Vec3{0,1.2f,0};}
bool sample(MotionPose& pose) {pose=fixture;return true;}
int main(int argc,char** argv) {
    void* table[]{reinterpret_cast<void*>(fakeTick),reinterpret_cast<void*>(before),reinterpret_cast<void*>(fakeAfter)};
    struct Object { void** table; } object{table};
    assert(argc==2);HMODULE module=LoadLibraryA(argv[1]);assert(module);
    auto attach=reinterpret_cast<BOOL(*)(void*,bool(*)(MotionPose&))>(GetProcAddress(module,"OWMC_MotionTestAttach"));
    auto verify=reinterpret_cast<BOOL(*)()>(GetProcAddress(module,"OWMC_MotionTestVerify"));assert(attach&&verify&&attach(&object,sample));
    for(UINT frame=1;frame<=2;frame++) {
        auto tick=reinterpret_cast<uintptr_t(WINAPI*)(void*,UINT)>(object.table[0]);assert(tick(&object,frame)==0x12345678+frame);
        reinterpret_cast<void(WINAPI*)(void*)>(object.table[2])(&object);
    }
    assert(verify()&&object.table==table&&fixture.foot.x==2&&fixture.eye.x==2);
    std::cout<<"Read-only movement stage observation, native return values, unchanged fixture results and table restoration passed.\n";
}
