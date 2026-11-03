#include "../src/native_armory.hpp"
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <unordered_map>
using namespace passthrough;
int main(){
    std::unordered_map<uintptr_t,unsigned char> memory;
    auto put=[&](uintptr_t at,auto value){auto p=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++)memory[at+i]=p[i];};
    auto read=[&](uintptr_t at,auto& value){auto p=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++){auto it=memory.find(at+i);if(it==memory.end())return false;p[i]=it->second;}return true;};
    ArmoryHeader h{};h.admin=0x10000;h.model=0x20000;h.modelId=0x80001039;
    ArmorySpec s{};s.resource=0x040000000000004a;s.resourceAddress=0x30018;s.resourceGuard=0x40000;s.script=0x50000;s.graph=0x60000;s.bag=0x70000;s.definition=0x80000;s.amountObject=0x90000;s.amountValue=0x90010;s.amountVtable=0xa0000;s.damageConfig=s.amountObject;s.amountKind=1;s.eyeHeight=1.55f;
    put(h.model+0x94,uint32_t(h.modelId));put(h.model+0x28,h.admin);put(s.script+0x10,uintptr_t(0xb0000));put(0xb0450,uintptr_t(0xc0000));put(0xc0008,h.model);put(s.script+0x98,s.bag);put(s.script+0x160,s.graph);
    put(s.resourceAddress,s.resource);put(s.resourceAddress-24,s.resourceGuard);put(s.amountObject,s.amountVtable);put(s.amountValue,int(7));
    put(s.graph+0x50,uintptr_t(0xd0000));put(s.graph+0x58,uint64_t(1));put(0xd0000,uintptr_t(0xe0000));put(0xd0008,uint64_t(1));put(0xe0000,s.definition);
    put(s.script+0x18,int16_t(0));put(s.graph+0x60,uintptr_t(0xd1000));put(s.graph+0x68,uint64_t(1));put(0xd1000,uintptr_t(0xe1000));put(0xd1008,uint64_t(1));put(0xe1000,s.definition);
    put(s.definition+0x168,uintptr_t(0xf0000));put(0xf0038,uintptr_t(0x110000));put(0x110038,s.damageConfig);
    float amount=0;assert(armorySpecBounds(s)&&armoryAmount(h,s,read,amount)&&amount==7);
    s.volleyKey=0x10000;assert(!armoryAmount(h,s,read,amount));s.volleyKey=0;
    put(h.model+0x94,uint32_t(h.modelId+1));assert(!armoryAmount(h,s,read,amount));put(h.model+0x94,uint32_t(h.modelId));
    put(s.resourceAddress,s.resource+1);assert(!armoryAmount(h,s,read,amount));put(s.resourceAddress,s.resource);
    put(0xe0000,s.definition+8);assert(!armoryAmount(h,s,read,amount));put(0xe0000,s.definition);
    auto oldAddress=s.resourceAddress,oldGuard=s.resourceGuard;
    s.amountKind=0x20001;s.resourceAddress=0x220008;s.resourceGuard=0x230000;
    put(s.definition+0x110,uintptr_t(0x240000));put(0x240000,s.resourceGuard);put(0x240008,uintptr_t(0x250000));put(0x240010,uint64_t(2));
    put(0x250000,uint64_t(1));put(0x250008,uintptr_t(0x220000));put(s.resourceAddress,s.resource);
    assert(armorySpecBounds(s)&&armoryAmount(h,s,read,amount)&&amount==7);
    put(0x240000,s.resourceGuard+8);assert(!armoryAmount(h,s,read,amount));put(0x240000,s.resourceGuard);
    put(0x250000,uint64_t(0));assert(!armoryAmount(h,s,read,amount));
    s.amountKind=1;s.resourceAddress=oldAddress;s.resourceGuard=oldGuard;
    put(s.amountValue,int(-1));assert(!armoryAmount(h,s,read,amount));
    s.amountKind=5;s.amountValue=0x170000;put(s.amountObject+0x20,uintptr_t(0x120000));put(s.amountObject+0x28,uint64_t(2));
    put(0x120000,uint64_t(11));put(0x120008,uintptr_t(0x130000));
    put(s.amountObject+0x40,uintptr_t(0x140000));put(s.amountObject+0x48,uint64_t(1));put(0x140000,s.amountValue);put(0x140008,uint64_t(2));
    auto code=std::array<uint8_t,11>{31,0,4,6,70,0,1,4,70,1,0};put(0x130000,code);put(s.amountValue,17.f);put(s.amountValue+4,17.f);
    assert(armorySpecBounds(s)&&armoryAmount(h,s,read,amount)&&amount==17);
    put(s.amountValue+4,20.f);assert(!armoryAmount(h,s,read,amount));put(s.amountValue+4,17.f);
    code[3]=5;put(0x130000,code);assert(!armoryAmount(h,s,read,amount));code[3]=6;put(0x130000,code);
    s.amountValue+=4;assert(!armoryAmount(h,s,read,amount));s.amountValue-=4;
    // Scalar product is validated on a worker but evaluated only by the
    // factory-thread callback supplied by the caller.
    s.amountKind=7;s.amountValue=0x180000;s.damageRid=0x190000;put(s.amountObject+8,s.amountValue);put(s.amountValue,s.damageRid);
    put(0x120000,uint64_t(6));auto product=std::array<uint8_t,6>{70,0,31,0,102,0};put(0x130000,product);
    put(s.amountObject+0x30,uintptr_t(0x1a0000));put(s.amountObject+0x38,uint64_t(1));put(0x1a0000,uintptr_t(0x1b0000));put(0x1a0008,uint64_t(1));put(0x1b0000,uintptr_t(0x1c0000));
    put(0x1c0010,uintptr_t(0x1d0000));put(0x1c0018,uint64_t(1));put(0x1d0000,uintptr_t(0x1e0000));put(0x1d0008,uint64_t(1));put(0x1e0008,uint64_t(0x0d800000000009b9));
    assert(armoryAmount(h,s,read,amount)&&amount==0);
    auto evaluate=+[](const ArmorySpec&,float& value){value=119.99999f;return true;};
    assert(armoryAmount(h,s,read,amount,evaluate)&&amount>119);
    product[4]=206;put(0x130000,product);assert(!armoryAmount(h,s,read,amount,evaluate));
    // Actual two-ring shape, with each scalar metadata decoded rather than invoked.
    auto literal=[&](uintptr_t object,uint32_t kind,uint32_t raw){
        auto vt=object+0x100,getter=object+0x200,info=object+0x300;
        put(object,vt);put(vt+0x28,getter);std::array<uint8_t,8> prefix{0x48,0x8d,5,0,0,0,0,0xc3};
        int32_t offset=int32_t(info-getter-7);std::memcpy(prefix.data()+3,&offset,4);put(getter,prefix);put(info+0x50,kind);put(object+16,raw);
    };
    auto fbits=[](float f){uint32_t n;std::memcpy(&n,&f,4);return n;};
    s.effect=1;s.splash=80;s.radius=3;
    put(s.definition+0x160,uintptr_t(0x300000));put(0x300060,uintptr_t(0x310000));put(0x310038,uintptr_t(0x320000));
    put(0x300008,uintptr_t(0x330000));put(0x300010,uint64_t(2));put(0x330000,uint64_t(2));put(0x330008,uintptr_t(0x340000));
    put(0x340000,std::array<uintptr_t,4>{0x350000,0x360000,0x370000,0x380000});
    literal(0x320000,0x3ae7427e,80);literal(0x350000,0x3ae7427e,1);literal(0x360000,0x3ae7427e,1);literal(0x370000,0x3ae7427e,3);literal(0x380000,0x7b13a0d4,fbits(.5f));
    ArmoryBlast blast{};assert(armoryBlast(s,read,blast)&&blast.splash==80&&blast.inner==1&&blast.outer==3&&blast.scale==.5f);
    put(0x320010,uint32_t(81));assert(!armoryBlast(s,read,blast));put(0x320010,uint32_t(80));
    put(0x380010,fbits(std::nanf("")));assert(!armoryBlast(s,read,blast));put(0x380010,fbits(.5f));
    put(0x330000,uint64_t(4097));assert(!armoryBlast(s,read,blast));put(0x330000,uint64_t(2));
    put(0x370350,uint32_t(123));assert(!armoryBlast(s,read,blast));
    // Empty motion arrays explicitly mean zero gravity; known gravity motion
    // supplies the original scalar and changed/multiple motions are refused.
    put(s.definition+0x100,uintptr_t(0x400000));put(s.definition+0x108,uint64_t(2));put(0x400000,uint64_t(0));put(0x400008,uintptr_t(0));
    s.gravity=0;assert(armoryGravity(s,read));s.gravity=9.8f;assert(!armoryGravity(s,read));
    put(0x400000,uint64_t(1));put(0x400008,uintptr_t(0x410000));put(0x410000,uintptr_t(0x420000));
    literal(0x420000,0xc2b6ce4b,0);put(0x420008,uintptr_t(0x430000));literal(0x430000,0x7b13a0d4,fbits(9.8f));
    assert(armoryGravity(s,read));s.gravity=0;assert(!armoryGravity(s,read));s.gravity=9.8f;
    put(0x400000,uint64_t(2));assert(!armoryGravity(s,read));put(0x400000,uint64_t(1));
    // Contextual dynamic damage is structural on a worker, never evaluated there.
    s.amountKind=6;literal(s.amountObject,0xf8cc195d,0);put(s.amountObject+8,s.amountValue);
    put(s.amountObject+0x10,uintptr_t(0x440000));put(s.amountObject+0x18,uint64_t(1));put(0x440000,uintptr_t(0x450000));put(0x440008,uint64_t(1));put(0x450008,uint64_t(0x0d800000000001dc));
    s.amountVtable=s.amountObject+0x100;
    assert(armorySpecBounds(s)&&armoryAmount(h,s,read,amount)&&amount==0);
    assert(armoryAmount(h,s,read,amount,evaluate)&&amount>119);
    put(0x450008,uint64_t(0x0d80000000000152));assert(!armoryAmount(h,s,read,amount,evaluate));
    s.eyeHeight=std::nanf("");assert(!armorySpecBounds(s));
    // Non-damaging gameplay E still has the beta's typed amount1 receipt.
    // It cannot inherit Flashbang, another projectile or a changed blast ring.
    ArmoryHeader pharah=h;pharah.hero=0x02e0000000000008ULL;ArmorySpec e=s;e.effect=3;e.node=3;e.resource=0x040000000000010fULL;e.gravity=0;e.radius=8;e.splash=0;e.bounces=0;e.fuse=0;e.terrain=0;
    put(e.script+0x150,uint64_t(0x058000000000007b));
    literal(0x300000,0x66bd247b,0);put(0x300010,uint64_t(2));put(0x330000,uint64_t(1));
    literal(0x350000,0x3ae7427e,8);literal(0x360000,0x3ae7427e,1);literal(0x320000,0x3ae7427e,1);
    assert(armoryFlash(pharah,e,read));e.radius=7;assert(!armoryFlash(pharah,e,read));e.radius=8;
    e.resource++;assert(!armoryFlash(pharah,e,read));e.resource--;pharah.hero++;assert(!armoryFlash(pharah,e,read));pharah.hero--;
    put(0x320010,uint32_t(2));assert(!armoryFlash(pharah,e,read));put(0x320010,uint32_t(1));
    put(e.script+0x150,uint64_t(0x058000000000002b));assert(!armoryFlash(pharah,e,read));
    // Bastion's actual factory03ce is admitted only with its typed original
    // Tank declarations. The generic two-ring shape already preserves .3.
    ArmoryHeader tank=h;tank.hero=0x02e0000000000015ULL;
    ArmorySpec shell{};shell.resource=0x04000000000003ceULL;shell.resourceAddress=0x510018;shell.resourceGuard=0x510100;
    shell.script=0x520000;shell.graph=0x530000;shell.bag=0x540000;shell.definition=0x550000;
    shell.amountObject=0x560000;shell.amountValue=0x560010;shell.damageConfig=shell.amountObject;shell.amountKind=1;
    shell.node=25;shell.effect=1;shell.eyeHeight=1.82f;shell.gravity=0;shell.splash=140;shell.radius=4;
    shell.volleyKey=(24u<<16)|(19u<<8);
    put(shell.resourceAddress,shell.resource);put(shell.resourceAddress-24,shell.resourceGuard);
    put(shell.script+0x10,uintptr_t(0x730000));put(0x730450,uintptr_t(0x740000));put(0x740008,tank.model);
    put(shell.script+0x98,shell.bag);put(shell.script+0x160,shell.graph);put(shell.script+0x150,uint64_t(0x058000000000024f));put(shell.script+0x18,int16_t(3));
    put(shell.graph+0x50,uintptr_t(0x570000));put(shell.graph+0x58,uint64_t(1));put(0x570000,uintptr_t(0x580000));put(0x570008,uint64_t(29));put(0x580000+25*8,shell.definition);
    put(shell.graph+0x60,uintptr_t(0x590000));put(shell.graph+0x68,uint64_t(1));put(0x590000,uintptr_t(0x5a0000));put(0x590008,uint64_t(22));put(0x5a0000+19*8,shell.definition);
    auto typeAt=[&](uintptr_t object,uint32_t kind,uintptr_t vt){
        auto getter=vt+0x100,info=vt+0x200;put(object,vt);put(vt+0x28,getter);
        std::array<uint8_t,8> prefix{0x48,0x8d,5,0,0,0,0,0xc3};int32_t delta=int32_t(info-getter-7);
        std::memcpy(prefix.data()+3,&delta,4);put(getter,prefix);put(info+0x50,kind);
    };
    typeAt(shell.definition,0x860ee5fc,0xa00000);
    literal(shell.amountObject,0x3ae7427e,50);shell.amountVtable=shell.amountObject+0x100;
    put(shell.definition+0x168,uintptr_t(0x6b0000));typeAt(0x6b0000,0x4ef1dd7e,0xa01000);put(0x6b0038,uintptr_t(0x6c0000));typeAt(0x6c0000,0x06a06f4e,0xa02000);put(0x6c0038,shell.amountObject);
    put(shell.definition+0x160,uintptr_t(0x6d0000));typeAt(0x6d0000,0x66bd247b,0xa03000);put(0x6d0060,uintptr_t(0x6e0000));typeAt(0x6e0000,0x06a06f4e,0xa04000);
    put(0x6e0038,uintptr_t(0x6f0000));literal(0x6f0000,0x3ae7427e,140);
    put(0x6d0008,uintptr_t(0x760000));put(0x6d0010,uint64_t(2));put(0x760000,uint64_t(2));put(0x760008,uintptr_t(0x770000));
    put(0x770000,std::array<uintptr_t,4>{0x780000,0x790000,0x7a0000,0x7b0000});
    literal(0x780000,0x3ae7427e,1);literal(0x790000,0x3ae7427e,1);literal(0x7a0000,0x3ae7427e,4);literal(0x7b0000,0x7b13a0d4,fbits(.3f));
    put(shell.definition+0x100,uintptr_t(0x750000));put(shell.definition+0x108,uint64_t(2));put(0x750000,uint64_t(0));put(0x750008,uintptr_t(0));
    put(shell.definition+0x140,uintptr_t(0x700000));literal(0x700000,0xf8cc195d,0);
    put(0x700010,uintptr_t(0x710000));put(0x700018,uint64_t(1));put(0x710000,uintptr_t(0x720000));put(0x710008,uint64_t(1));put(0x720008,uint64_t(0x0d800000000018e0));
    for(auto pair:std::array<std::pair<uintptr_t,uintptr_t>,4>{{{0x128,0x7c0000},{0x130,0x7d0000},{0x190,0x7e0000},{0x198,0x7f0000}}})put(shell.definition+pair.first,pair.second);
    literal(0x7c0000,0x3ae7427e,5);literal(0x7d0000,0x7b13a0d4,fbits(100.f));literal(0x7e0000,0x3ae7427e,1);literal(0x7f0000,0x3ae7427e,1);
    assert(armorySpecBounds(shell)&&armoryAmount(tank,shell,read,amount)&&amount==50&&armoryBastionTank(tank,shell,read));
    assert(armoryBlast(shell,read,blast)&&blast.inner==1&&blast.outer==4&&blast.scale==.3f&&blast.splash==140);
    assert(armoryBastionTankFlight(tank.hero,shell.resource,8,0,1,60,5,100));
    assert(!armoryBastionTankFlight(tank.hero,shell.resource,0,0,1,60,5,100));
    assert(!armoryBastionTankFlight(tank.hero,shell.resource,8,1,1,60,5,100));
    assert(!armoryBastionTankFlight(tank.hero,shell.resource,8,0,2,60,5,100));
    assert(!armoryBastionTankFlight(tank.hero,shell.resource,8,0,1,59,5,100));
    assert(!armoryBastionTankFlight(tank.hero,shell.resource,8,0,1,60,4,100));
    assert(!armoryBastionTankFlight(tank.hero,shell.resource,8,0,1,60,5,99));
    assert(armoryBastionTankFlight(pharah.hero,0x0400000000000052ULL,8,0,1,45,5,100));
    tank.hero=pharah.hero;assert(!armoryBastionTank(tank,shell,read));tank.hero=0x02e0000000000015ULL;
    shell.node=24;assert(!armoryBastionTank(tank,shell,read));shell.node=25;
    shell.volleyKey^=0x100;assert(!armoryBastionTank(tank,shell,read));shell.volleyKey^=0x100;
    put(shell.script+0x150,uint64_t(0x058000000000012e));assert(!armoryBastionTank(tank,shell,read));put(shell.script+0x150,uint64_t(0x058000000000024f));
    put(shell.amountValue,uint32_t(49));assert(!armoryBastionTank(tank,shell,read));put(shell.amountValue,uint32_t(50));
    put(0x6f0010,uint32_t(139));assert(!armoryBastionTank(tank,shell,read));put(0x6f0010,uint32_t(140));
    put(0x7b0010,fbits(.31f));assert(!armoryBastionTank(tank,shell,read));put(0x7b0010,fbits(.3f));
    put(0x720008,uint64_t(0x0d800000000018e1));assert(!armoryBastionTank(tank,shell,read));put(0x720008,uint64_t(0x0d800000000018e0));
    put(0x7c0010,uint32_t(6));assert(!armoryBastionTank(tank,shell,read));put(0x7c0010,uint32_t(5));
    put(0x7d0010,fbits(99.f));assert(!armoryBastionTank(tank,shell,read));put(0x7d0010,fbits(100.f));
    put(0x750000,uint64_t(1));assert(!armoryBastionTank(tank,shell,read));put(0x750000,uint64_t(0));
    shell.terrain=1;assert(!armoryBastionTank(tank,shell,read));shell.terrain=0;
    shell.radius=5;assert(!armoryBastionTank(tank,shell,read));shell.radius=4;
    put(tank.model+0x94,uint32_t(tank.modelId+1));assert(!armoryBastionTank(tank,shell,read));put(tank.model+0x94,uint32_t(tank.modelId));
    assert(armoryBastionTank(tank,shell,read));
    std::cout<<"PASS: armory expressions, actual two-ring metadata, current owner/node/resource, altered values and nonfinite guards.\n";
}
