#pragma once
#include "native_local_hero.hpp"
#include <array>
#include <cstring>
#include <cmath>
#include <atomic>
namespace passthrough {
// The provided plugin identifies this original Set & Notify method. Production
// invokes it on the existing native logic owner, never the renderer. Raw payload
// writes alone do not notify HUD subscriptions; no new subscriptions are added.
struct NativeMeterDisplay {
    static bool supported(uint64_t hero){
        // Same verified beta roster as the meter adapter, excluding Genji's
        // dedicated original controller. This is not a combat capability list.
        constexpr std::array<uint64_t,20> ids{2,3,4,5,6,7,8,9,10,0x15,0x16,0x20,0x40,0x42,0x65,0x68,0x6e,0x79,0x7a,0xdd};
        for(auto id:ids)if(hero==(0x02e0000000000000ULL|id))return true;
        return false;
    }
    std::atomic<uint64_t> notices{0},refused{0};uintptr_t previous=0;uint32_t previousModel=0;
    std::array<unsigned char,16> last{};bool have=false,failed=false;
    template<class Read,class Write,class Invoke> void update(uintptr_t base,uintptr_t admin,const NativeLocalHero& hero,Read read,Write write,Invoke invoke){
        if(!supported(hero.hero))return;
        auto q=[&](uintptr_t at){uintptr_t v=0;read(at,&v,8);return v;};
        auto component=[&](uintptr_t owner){struct List{uintptr_t items;int count,capacity;} l{};
            if(!read(owner+0x50,&l,sizeof l)||l.count<1||l.count>l.capacity||l.capacity>256)return uintptr_t(0);
            for(int i=0;i<l.count-1;i++){auto p=q(l.items+i*8);unsigned char id=0;if(read(p+0x10,&id,1)&&id==0x23&&q(p+8)==owner)return p;}return uintptr_t(0);};
        auto comp=component(hero.model),sync=comp?comp+0xc0:0,bag=sync?q(sync+0x2e0):0;
        if(!bag||q(bag)!=base+0x1607a90||q(bag+0x3c0)!=sync||q(sync+0x450)!=comp)return;
        uintptr_t primitive=0,cost=0;
        for(unsigned bucket=0;bucket<16;bucket++){
            struct List{uintptr_t items;int count,capacity;} l{};if(!read(bag+0xa0+bucket*0x30,&l,sizeof l)||l.count<0||l.count>l.capacity||l.capacity>512)return;
            for(int i=0;i<l.count;i++){struct Pair{uint64_t rid;uintptr_t value;} p{};if(!read(l.items+i*16,&p,sizeof p))return;
                if(p.rid==0x0d80000000000156ULL){if(primitive)return;primitive=p.value;}
                if(p.rid==0x0d80000000000152ULL){if(cost)return;cost=p.value;}}
        }
        if(!primitive||!cost||q(primitive)!=base+0x1608248||q(cost)!=base+0x1608248
            ||q(primitive+0x80)!=bag||q(primitive+0x98)!=0x0d80000000000156ULL
            ||q(cost+0x80)!=bag||q(cost+0x98)!=0x0d80000000000152ULL)return;
        if(previous!=primitive||previousModel!=hero.modelId){previous=primitive;previousModel=hero.modelId;have=false;failed=false;}
        if(failed)return;
        std::array<unsigned char,16> value{},maximum{};if(!read(primitive+0xa0,value.data(),16)||!read(cost+0xa0,maximum.data(),16))return;
        auto numeric=[](const auto& a){uint32_t kind=0;std::memcpy(&kind,a.data()+12,4);if(kind==2){int v=0;std::memcpy(&v,a.data(),4);return double(v);}if(kind==3){float v=0;std::memcpy(&v,a.data(),4);return double(v);}return -1.;};
        double current=numeric(value),limit=numeric(maximum);
        if(!std::isfinite(current)||!std::isfinite(limit)||limit<=0||limit>100000||current<0||current>limit)return;
        if(have&&last==value)return;
        uint32_t modelId=0,local=0,flags=0;read(hero.reference+0x94,&modelId,4);read(admin+0x220,&local,4);read(primitive+0x94,&flags,4);
        if(modelId!=hero.modelId||local!=hero.localId||q(hero.model+0x28)!=admin||q(comp+8)!=hero.model||q(hero.heroInfo+0x98)!=hero.hero||q(base+0x1608248+0x288)!=base+0xf5f740||(flags!=6&&flags!=14))return;
        const std::array<unsigned char,16> prefix{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};
        std::array<unsigned char,16> code{},again{};if(!read(base+0xf5f740,code.data(),16)||code!=prefix||!read(primitive+0xa0,again.data(),16)||again!=value)return;
        // The disassembled original setter tests flag8 before its equality
        // short-circuit and clears it in the normal notify path. This forces
        // notification of the already-written current value, never an old value.
        uint32_t dirty=flags|8;if(!write(primitive+0x94,&dirty,4))return;
        auto instance=q(bag+0x3b8);
        if(invoke(base+0xf5f740,primitive,sync,instance,value.data(),primitive+0x88)){notices++;last=value;have=true;}
        else {uint32_t now=0;read(primitive+0x94,&now,4);if(now==dirty)write(primitive+0x94,&flags,4);refused++;failed=true;}
    }
};
}
