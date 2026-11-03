#include "../src/native_deadeye_input.hpp"
#include <vector>
#include <cassert>
#include <iostream>
int main(){
    using namespace passthrough;std::vector<unsigned char> memory(0x900000);
    auto read=[&](uintptr_t at,void* out,size_t size){if(at>memory.size()||size>memory.size()-at)return false;std::memcpy(out,memory.data()+at,size);return true;};
    auto put=[&](uintptr_t at,auto value){std::memcpy(memory.data()+at,&value,sizeof value);};
    GuestBody b;b.hostPid=77;b.sourcePid=88;b.generation=9;b.hostGeneration=10;b.worldId=11;b.wallMs=5000;
    b.deadeyeFiring=true;b.deadeyeModel=19;b.deadeyeBegin=1000;b.deadeyeScript=0x500000;b.deadeyeLogger=0x700000;b.deadeyeObserved=4999;b.deadeyeWorld=11;
    NativeLocalHero h;h.hero=0x02e0000000000042ULL;h.modelId=19;h.model=0x400000;
    DeadeyeInputContext c{77,88,9,10,11,5000,0x600000,0x800000};
    put(b.deadeyeScript+0x10,uintptr_t(0x510000));put(0x510450,uintptr_t(0x520000));put(0x520008,h.model);put(b.deadeyeScript+0x150,0x058000000000022fULL);
    auto map=[&](uintptr_t at,uintptr_t head,uintptr_t root,unsigned count){put(at,head);put(at+8,uint64_t(count));put(head+8,root);put(head+25,uint8_t(1));};
    map(b.deadeyeLogger,0x710000,0x720000,1);put(0x720000,uintptr_t(0x710000));put(0x720008,uintptr_t(0x710000));put(0x720010,uintptr_t(0x710000));put(0x720020,b.deadeyeScript);
    map(0x720028,0x730000,0x740000,2);put(0x740000,uintptr_t(0x730000));put(0x740008,uintptr_t(0x730000));put(0x740010,uintptr_t(0x750000));put(0x740020,18u);put(0x740028,1000ULL);put(0x740030,uint8_t(0));
    put(0x750000,uintptr_t(0x730000));put(0x750008,uintptr_t(0x740000));put(0x750010,uintptr_t(0x730000));put(0x750020,44u);put(0x750028,1010ULL);put(0x750030,uint8_t(1));
    auto admitted=[&](){return nativeDeadeyeInputActive(b,c,h,read);};assert(admitted());
    // A fire request is insufficient without the actual same-cast logger event.
    put(0x750028,999ULL);assert(!admitted());put(0x750028,1010ULL);assert(admitted());
    put(0x740030,uint8_t(1));assert(!admitted());put(0x740030,uint8_t(0));assert(admitted()); // immediate original root End
    put(0x740028,2000ULL);assert(!admitted());put(0x740028,1000ULL);assert(admitted()); // old cast during a new Q
    for(int change=0;change<13;change++){
        auto oldB=b;auto oldC=c;auto oldH=h;
        if(change==0)b.deadeyeFiring=false;
        if(change==1)h.hero++;
        if(change==2)h.modelId++;
        if(change==3)c.pid++;
        if(change==4)c.sourcePid++;
        if(change==5)c.generation++;
        if(change==6)c.hostGeneration++;
        if(change==7)c.world++;
        if(change==8)c.now=5151;
        if(change==9)b.wallMs=5001;
        if(change==10)b.deadeyeObserved=5001;
        if(change==11)b.deadeyeLogger=c.pluginEnd;
        if(change==12)b.deadeyeWorld++;
        assert(!admitted());b=oldB;c=oldC;h=oldH;
    }
    put(b.deadeyeScript+0x150,0x0580000000000044ULL);assert(!admitted());put(b.deadeyeScript+0x150,0x058000000000022fULL);
    put(0x520008,h.model+1);assert(!admitted());put(0x520008,h.model);assert(admitted());
    std::cout<<"PASS: confirmed native fire to original root End, charging/new cast, exact world/model/source, freshness and read-only script/logger guards\n";
}
