#pragma once
#include "native_local_hero.hpp"
#include <cstring>
namespace passthrough {
// Native engine lookup scans the whole unordered bucket; the supplied plugin
// inlines a first-record-only lookup. Preserve the multiset and its count while
// making current local owners visible to that legacy code on its owner thread.
template<class Read,class Write>
bool localBucketCompatibility(uintptr_t admin,const NativeLocalHero& hero,Read read,Write write,unsigned& promotions){
    struct Slot{uintptr_t entries;int count,pad;};struct Entry{uint32_t id,pad;uintptr_t owner;};
    uintptr_t table=0;if(!read(admin+0x10,&table,8))return false;
    auto promote=[&](uint32_t id,uintptr_t owner){
        Slot slot{};auto address=table+(id&4095u)*16;
        if(!read(address,&slot,sizeof slot)||!slot.entries||slot.count<1||slot.count>4096)return false;
        Entry first{};if(!read(slot.entries,&first,sizeof first))return false;
        if(first.id==id)return first.owner==owner;
        for(int index=1;index<slot.count;index++){
            auto at=slot.entries+index*sizeof(Entry);Entry selected{};
            if(!read(at,&selected,sizeof selected))return false;
            if(selected.id!=id)continue;
            uint32_t current=0,actualId=0;uintptr_t actualAdmin=0;Slot check{};Entry checkFirst{},checkSelected{};
            if(selected.owner!=owner||!read(admin+0x220,&current,4)||current!=hero.localId
               ||!read(owner+0x94,&actualId,4)||actualId!=id||!read(owner+0x28,&actualAdmin,8)||actualAdmin!=admin
               ||!read(address,&check,sizeof check)||std::memcmp(&slot,&check,sizeof slot)
               ||!read(slot.entries,&checkFirst,sizeof first)||std::memcmp(&first,&checkFirst,sizeof first)
               ||!read(at,&checkSelected,sizeof selected)||std::memcmp(&selected,&checkSelected,sizeof selected))return false;
            if(!write(slot.entries,&selected,sizeof selected)||!write(at,&first,sizeof first)){
                write(slot.entries,&first,sizeof first);write(at,&selected,sizeof selected);return false;
            }
            ++promotions;return true;
        }
        return false;
    };
    return promote(hero.localId,hero.controller)&&promote(hero.modelId,hero.model);
}
}
