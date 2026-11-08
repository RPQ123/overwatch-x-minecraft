#include "../src/native_pickup_scrap.hpp"
#include <cassert>
#include <iostream>
#include <vector>
int main(){
    using namespace passthrough;
    std::vector<unsigned char> memory(0x2000000);
    auto read=[&](uintptr_t at,void* out,size_t size){if(at+size>memory.size())return false;std::memcpy(out,memory.data()+at,size);return true;};
    auto put=[&](uintptr_t at,auto value){std::memcpy(memory.data()+at,&value,sizeof value);};
    uintptr_t base=0x100000,admin=0x300000,model=0x400000,comp=0x500000,sync=comp+0xc0,bag=0x600000,primitive=0x700000;
    NativeLocalHero h;h.hero=0x02e0000000000006ULL;h.model=model;h.modelId=19;h.localId=17;h.reference=0x720000;h.heroInfo=0x730000;h.controller=0x310000;
    put(base+0x17b7f90,admin);put(admin+0x220,h.localId);put(model+0x28,admin);put(h.reference+8,h.controller);put(h.reference+0x94,h.modelId);put(h.heroInfo+0x98,h.hero);
    put(model+0x50,uintptr_t(0x740000));put(model+0x58,2);put(model+0x5c,2);put(0x740000,comp);put(comp+0x10,uint8_t(0x23));put(comp+8,model);
    put(sync+0x2e0,bag);put(sync+0x450,comp);put(bag,base+0x1607a90);put(bag+0x3c0,sync);
    put(bag+0xa0+9*0x30,uintptr_t(0x750000));put(bag+0xa8+9*0x30,1);put(bag+0xac+9*0x30,1);
    put(0x750000,0x0d80000000000409ULL);put(0x750008,primitive);
    put(primitive,base+0x1608248);put(primitive+0x80,bag);put(primitive+0x98,0x0d80000000000409ULL);put(primitive+0x94,6u);put(primitive+0xa0,100);put(primitive+0xac,2);
    put(base+0x1608248+0x288,base+0xf5f740);
    const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};std::memcpy(memory.data()+base+0xf5f740,prefix,16);
    unsigned calls=0;
    auto notify=[&](uintptr_t fn,uintptr_t var,uintptr_t owner,uintptr_t instance,const void* value,uintptr_t user){
        assert(fn==base+0xf5f740&&var==primitive&&owner==sync&&instance==0&&user==primitive+0x88);
        ++calls;std::memcpy(memory.data()+primitive+0xa0,value,16);return true;
    };
    ScrapCreditRequest p{};std::memcpy(p.magic,"OWSCRP01",8);p.version=1;p.pid=33;p.creation=44;p.sequence=1000;p.wall=2000;p.generation=55;p.world=66;p.model=model;p.modelId=h.modelId;p.quantity=25;
    DeadeyePresentationContext c{33,44,2000,55,66,base,0};NativePickupScrap worker;
    assert(worker.update(&p,c,h,read,notify)&&calls==1&&worker.ack.phase==1&&worker.ack.before==100&&worker.ack.after==125&&worker.ack.credited==25);
    c.now+=60;p.wall=c.now;assert(worker.update(&p,c,h,read,notify)&&calls==1); // lost ack/retry never grants twice
    --p.sequence;assert(!worker.update(&p,c,h,read,notify)&&calls==1);p.sequence=1001;
    auto refused=[&](){assert(!worker.update(&p,c,h,read,notify)&&calls==1);};
    p.quantity=200;refused();p.quantity=25;p.world=67;refused();p.world=66;
    p.wall=c.now-251;refused();p.wall=c.now;h.hero=0x02e0000000000002ULL;refused();h.hero=0x02e0000000000006ULL;
    put(h.reference+0x94,20u);refused();put(h.reference+0x94,h.modelId);
    put(primitive+0x98,0x0d80000000000156ULL);refused();put(primitive+0x98,0x0d80000000000409ULL);
    put(base+0xf5f740,uint8_t(0xcc));refused();put(base+0xf5f740,uint8_t(0x48));
    put(primitive+0xa0,190);assert(worker.update(&p,c,h,read,notify)&&calls==2&&worker.ack.credited==10&&worker.ack.after==200);
    ++p.sequence;assert(worker.update(&p,c,h,read,notify)&&calls==2&&worker.ack.phase==2&&worker.ack.credited==0);
    // A failed native call is a terminal failed receipt for that exact request.
    // A transport retry cannot invoke an uncertain grant a second time.
    put(primitive+0xa0,50);++p.sequence;
    auto fail=[&](auto...){++calls;return false;};
    assert(worker.update(&p,c,h,read,fail)&&calls==3&&worker.ack.phase==3);
    c.now+=60;p.wall=c.now;assert(worker.update(&p,c,h,read,notify)&&calls==3&&worker.ack.phase==3);
    ++p.sequence;put(primitive+0xa0,50.f);put(primitive+0xac,3);
    assert(worker.update(&p,c,h,read,notify)&&calls==4&&worker.ack.after==75&&worker.credits==3);
    std::cout<<"PASS: exact native Scrap0409 Set&Notify,25 credit/cap200,receipt readback,replay/failed-call dedupe,hero/world/freshness/owner/code refusal,integer/float\n";
}
