#include "../src/native_emission.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main(){
    constexpr uint64_t heroes[]={0x02e0000000000029ULL,0x02e0000000000042ULL,0x02e0000000000009ULL,0x02e0000000000008ULL};
    constexpr uint64_t resources[]={0x04000000000007caULL,0x04000000000002a7ULL,0x05800000000000feULL,0x0400000000000033ULL};
    for(int a=0;a<4;a++)for(int b=0;b<4;b++)assert(emissionResourceMatches(heroes[a],resources[b])==(a==b));
    assert(!emissionResourceMatches(0,resources[0])&&!emissionResourceMatches(heroes[0],0));
    NativeEmission e{};e.entity=4;e.owner=3;e.resource=0x04000000000007ca;e.direction={0,0,-1};
    EmissionJournal<2> journal;
    using Result=EmissionJournal<2>::Result;
    assert(journal.append(e)==Result::Accepted);
    assert(journal.append(e)==Result::Duplicate&&!journal.overflowed());
    e.entity++;assert(journal.append(e)==Result::Accepted);
    e.entity++;assert(journal.append(e)==Result::Full&&journal.overflowed());
    auto rows=journal.snapshot();assert(rows.size()==2&&rows[0].id==1&&rows[1].id==2);
    assert(rows[0].resource==e.resource);
    // Native entity IDs include generation; repeated reads/returns of one
    // original projectile cannot become additional damage events.
    assert(rows[0].entity!=rows[1].entity&&rows[0].id!=rows[1].id);
    auto bytes=encodeEmission(rows[0]);uint64_t id=0;std::memcpy(&id,bytes.data()+8,8);assert(id==1);
    assert(!journal.acknowledge(3)&&journal.snapshot().size()==2);
    assert(journal.acknowledge(1)&&journal.snapshot().size()==1);
    e.entity=4;assert(journal.append(e)==Result::Duplicate);
    e.entity=6;assert(journal.append(e)==Result::Accepted);
    rows=journal.snapshot();assert(rows[0].id==2&&rows[1].id==3);
    assert(journal.acknowledge(3)&&journal.snapshot().empty()&&journal.acknowledged()==3);
    EmissionJournal<8> rays;NativeEmission ray{};ray.kind=1;ray.owner=12;ray.volley=99;ray.tick=100;
    assert(rays.append(ray)==EmissionJournal<8>::Result::Accepted);
    assert(rays.append(ray)==EmissionJournal<8>::Result::Duplicate);
    assert(rays.acknowledge(1));
    assert(rays.append(ray)==EmissionJournal<8>::Result::Duplicate);
    ++ray.tick;assert(rays.append(ray)==EmissionJournal<8>::Result::Accepted);
    ++ray.pellet;assert(rays.append(ray)==EmissionJournal<8>::Result::Accepted);
    ++ray.owner;assert(rays.append(ray)==EmissionJournal<8>::Result::Accepted);
    // Failed native spawns all have entity=0; their real firing identities differ.
    assert(rays.snapshot().size()==3);
    std::cout<<"Native emission identities, retained ordering, fail-closed capacity and fixed wire offsets passed.\n";
}
