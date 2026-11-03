#pragma once
#include "native_recall_completion.hpp"
#include <utility>
namespace passthrough {
struct NativeRecallAmmo {
    std::atomic<uint64_t> restored{0},refused{0};
    template<class Read,class Notify> bool restore(const NativeRecallBinding& b,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Notify notify){
        auto q=[&](uintptr_t at){uint64_t v=0;read(at,&v,8);return v;};
        if(!NativeRecallCompletion::owner(b,c,h,read)||q(b.ammoScript+0x150)!=0x0580000000000016ULL||q(b.ammoScript+0x160)!=b.ammoGraph
            ||q(b.ammoScript+0x98)!=b.ammoBag||q(q(q(b.ammoScript+0x10)+0x450)+8)!=h.model
            ||q(b.ammoBag)!=c.base+0x1607a90||q(b.ammoBag+0x3b8)!=b.ammoScript||q(b.ammo+0x80)!=b.ammoBag
            ||q(b.ammo+0x98)!=0x0d80000000000035ULL||q(b.maximum+0x80)!=b.ammoBag||q(b.maximum+0x98)!=0x0d800000000000c6ULL
            ||q(b.ammo)!=c.base+0x1608248||q(b.maximum)!=c.base+0x1608248)return false;
        for(auto pair:std::array<std::pair<uint64_t,uint64_t>,2>{{{0x0d80000000000035ULL,b.ammo},{0x0d800000000000c6ULL,b.maximum}}}){
            unsigned bucket=pair.first==0x0d80000000000035ULL?5:6;
            struct List{uintptr_t items;int count,capacity;} l{};
            if(!read(b.ammoBag+0xa0+bucket*0x30,&l,sizeof l)||l.count<1||l.count>l.capacity||l.capacity>512)return false;
            bool found=false;for(int i=0;i<l.count;i++)if(q(l.items+i*16)==pair.first&&q(l.items+i*16+8)==pair.second)found=true;
            if(!found)return false;
        }
        auto storage=q(b.ammoGraph+0x50),flag=q(b.ammoGraph+0x58);if(flag!=1&&flag!=2)return false;
        auto items=q(storage+(flag==1?0:8)),count=q(storage+(flag==1?8:0));if(count<=30||count>4096||q(items+30*8)!=b.reloadDefinition)return false;
        std::array<unsigned char,16> value{},maximum{},code{};
        if(!read(b.ammo+0xa0,value.data(),16)||!read(b.maximum+0xa0,maximum.data(),16))return false;
        int current=0,full=0,kind=0,maxKind=0;std::memcpy(&current,value.data(),4);std::memcpy(&full,maximum.data(),4);std::memcpy(&kind,value.data()+12,4);std::memcpy(&maxKind,maximum.data()+12,4);
        if(kind!=2||maxKind!=2||full!=40||current<0||current>full)return false;
        if(current==full)return true;
        const std::array<unsigned char,16> expected{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};
        if(q(c.base+0x1608248+0x288)!=c.base+0xf5f740||!read(c.base+0xf5f740,code.data(),16)||code!=expected)return false;
        // Original Set&Notify owns the value change and HUD subscription. No
        // renderer call, raw payload write, guessed maximum or new writer loop.
        auto sync=q(b.ammoBag+0x3c0);
        if(!sync||!notify(c.base+0xf5f740,b.ammo,sync,b.ammoScript,maximum.data(),b.ammo+0x88)){++refused;return false;}
        int after=0;if(!read(b.ammo+0xa0,&after,4)||after!=40){++refused;return false;}++restored;return true;
    }
};
}
