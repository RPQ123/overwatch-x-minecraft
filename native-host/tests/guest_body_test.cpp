#include "../src/guest_body.hpp"
#include <cassert>
#include <iostream>
#include <limits>
using namespace passthrough;
template<class T> void put(std::array<unsigned char,256>& b,size_t n,T v){std::memcpy(b.data()+n,&v,sizeof v);}
int main(){
    std::array<unsigned char,256> b{};std::memcpy(b.data(),"OWBODY01",8);
    put(b,8,1u);put(b,12,256u);put(b,16,42u);put(b,20,43u);put(b,24,uint64_t(2));put(b,32,uint64_t(3));
    put(b,64,uint64_t(2));put(b,72,uint64_t(1000));put(b,80,1u);
    put(b,96,-275.5);put(b,104,71.);put(b,112,-309.5);
    put(b,136,uint64_t(12345));
    auto s=decodeGuestBody(b.data(),1100,42);assert(s.grounded&&s.foot.y==71&&s.worldId==12345);
    assert(!s.deadeyeFiring); // Legacy producer: extension absent.
    auto fire=b;put(fire,176,0x31594544u);put(fire,180,1u);put(fire,184,0x80000123u);put(fire,192,100ULL);
    put(fire,200,0x500000ULL);put(fire,208,0x700000ULL);put(fire,216,1000ULL);put(fire,224,12345ULL);
    auto locked=decodeGuestBody(fire.data(),1100,42);assert(locked.deadeyeFiring&&locked.deadeyeModel==0x80000123u&&locked.deadeyeBegin==100);
    // Expired control proof is rejected by its control gate, not by the body
    // position channel, whose existing independent deadline remains250ms.
    assert(decodeGuestBody(fire.data(),1200,42).foot.y==71);
    for(int change=0;change<5;change++){
        auto bad=fire;
        if(change==0)put(bad,180,2u);
        if(change==1)put(bad,184,0u);
        if(change==2)put(bad,188,1u);
        if(change==3)put(bad,224,12346ULL);
        if(change==4)put(bad,180,0u); // Inactive must clear all fields.
        bool rejected=false;try{decodeGuestBody(bad.data(),1100,42);}catch(...){rejected=true;}assert(rejected);
    }
    BodyAnchor anchor;auto first=anchor.target(s);assert(first.x==1000&&first.y==1000&&first.z==1000);
    s.foot.y+=1.25f;s.grounded=false;s.velocity.y=4;
    assert(anchor.target(s).y==1001.25f&&(bodyFlags(0x20200,s)&0x2050d)==5);
    s.grounded=true;assert((bodyFlags(0x2008d,s)&0x2028d)==0x200);
    auto climb=b;put(climb,80,0u);put(climb,144,0x324d4c43u);put(climb,148,1u);put(climb,152,0x80000123u);
    auto wall=decodeGuestBody(climb.data(),1100,42);assert(wall.climbing&&wall.climbModel==0x80000123u);
    assert((bodyFlags(0x2028d,wall)&0x2028d)==0x88);
    wall.velocity.y=4;assert((bodyFlags(0x2028d,wall)&0x2028d)==0x85);
    for(int kind=0;kind<4;kind++){
        auto broken=climb;
        if(kind==0)put(broken,144,0x314d4c43u); // Retired, unproven normal-vector experiment.
        if(kind==1)put(broken,148,2u);
        if(kind==2)put(broken,152,0u);
        if(kind==3)put(broken,80,1u);
        bool rejected=false;try{decodeGuestBody(broken.data(),1100,42);}catch(...){rejected=true;}assert(rejected);
    }
    for(int kind=0;kind<7;kind++){
        auto broken=b;
        if(kind==0)put(broken,64,uint64_t(3));
        if(kind==1)put(broken,72,uint64_t(1200));
        if(kind==2)put(broken,72,uint64_t(500));
        if(kind==3)put(broken,16,99u);
        if(kind==4)put(broken,96,std::numeric_limits<double>::quiet_NaN());
        if(kind==5)put(broken,80,2u);
        if(kind==6)put(broken,136,uint64_t(0));
        bool rejected=false;try{decodeGuestBody(broken.data(),1100,42);}catch(...){rejected=true;}assert(rejected);
    }
    auto dimension=s;dimension.worldId=54321;dimension.foot={-700.f,73.f,120.f};
    auto rebased=anchor.target(dimension);assert(anchor.worldChanged&&rebased.x==1000&&rebased.y==1000&&rebased.z==1000);
    dimension.foot.y+=1.f;auto continued=anchor.target(dimension);assert(!anchor.worldChanged&&continued.y==1001);
    dimension.generation++;bool rejected=false;try{anchor.target(dimension);}catch(...){rejected=true;}assert(rejected);
    auto legacy=s;legacy.worldId=0;assert(!anchor.resumeSameWorld(legacy));
    BodyAnchor reconnect;auto current=s;current.worldId=17;reconnect.target(current);
    current.sourcePid++;current.generation++;current.foot.y+=2;
    assert(reconnect.resumeSameWorld(current)&&reconnect.target(current).y==1002);
    current.worldId++;assert(!reconnect.resumeSameWorld(current));current.worldId--;
    current.hostGeneration++;assert(!reconnect.resumeSameWorld(current));
    current.hostGeneration--;current.worldId++;current.sourcePid++;current.generation++;current.foot={9000,80,-7000};
    assert(reconnect.resumeSession(current));auto switched=reconnect.target(current);
    assert(reconnect.worldChanged&&switched.x==1000&&switched.y==1000&&switched.z==1000);
    current.hostGeneration++;assert(!reconnect.resumeSession(current));current.hostGeneration--;
    auto absent=current;absent.worldId=0;assert(!reconnect.resumeSession(absent));
    absent=current;absent.sourcePid=0;assert(!reconnect.resumeSession(absent));
    BodyStability settling;current.sequence=2;
    assert(!settling.observe(current,true));
    for(int repeat=0;repeat<100;repeat++)assert(!settling.observe(current,true));
    current.sequence=4;assert(settling.observe(current,true));
    assert(!settling.observe(current,false));assert(!settling.observe(current,true));
    current.sequence=6;assert(settling.observe(current,true));
    current.generation++;current.sequence=2;assert(!settling.observe(current,true));
    current.sequence=4;assert(settling.observe(current,true));
    std::cout<<"Guest body identity, age, seqlock, finite coordinates, virtual anchor, jump/ground flags and session refusal passed.\n";
}
