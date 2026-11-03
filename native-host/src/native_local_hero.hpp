#pragma once
#include <array>
#include <cstdint>
#include <cstddef>

namespace passthrough {
struct HeroWeaponProfile {uint64_t hero,script;uint32_t extraFlags;};
inline constexpr std::array<HeroWeaponProfile,4> heroWeapons{{
    {0x02e0000000000029ULL,0x0580000000000304ULL,0},
    {0x02e0000000000042ULL,0x05800000000001d2ULL,0},
    {0x02e0000000000009ULL,0x05800000000000feULL,0x800000},
    {0x02e0000000000008ULL,0x0580000000000023ULL,0}
}};
inline const HeroWeaponProfile* heroWeapon(uint64_t hero,uint64_t script){
    for(const auto& p:heroWeapons)if(p.hero==hero&&p.script==script)return &p;
    return nullptr;
}
struct NativeLocalHero {
    uint32_t localId=0,modelId=0;
    uintptr_t controller=0,reference=0,model=0,heroInfo=0;
    uint64_t hero=0;
    template<class Read> bool refresh(uintptr_t admin,Read read){
        auto ptr=[&](uintptr_t address){uintptr_t result=0;read(address,&result,8);return result;};
        uint32_t local=0,nextModel=0;uint64_t nextHero=0;
        if(!read(admin+0x220,&local,4)||!local)return false;
        auto component=[&](uintptr_t owner,unsigned wanted){
            struct List{uintptr_t items;int count,capacity;} list{};
            if(!read(owner+0x50,&list,sizeof list)||list.count<1||list.count>list.capacity||list.capacity>256)return uintptr_t(0);
            for(int i=0;i<list.count-1;i++){auto p=ptr(list.items+i*8);unsigned char id=0;if(read(p+0x10,&id,1)&&id==wanted&&ptr(p+8)==owner)return p;}
            return uintptr_t(0);
        };
        const bool heroRead=heroInfo&&read(heroInfo+0x98,&nextHero,8);
        if(local!=localId||!reference||!read(reference+0x94,&nextModel,4)||nextModel!=modelId||!heroRead||(hero&&nextHero!=hero)){
            struct Slot{uintptr_t entry;int used,pad;};std::array<Slot,4096> slots{};
            if(!read(ptr(admin+0x10),slots.data(),sizeof slots))return false;
            auto entity=[&](uint32_t id){
                auto find=[&](const auto& slot){
                    if(slot.used<0||slot.used>4096||(!slot.entry&&slot.used))return uintptr_t(0);
                    for(int i=0;i<slot.used;i++){struct Entry{uint32_t id,pad;uintptr_t owner;} e{};if(!read(slot.entry+i*sizeof e,&e,sizeof e))return uintptr_t(0);if(e.id==id)return e.owner;}
                    return uintptr_t(0);
                };
                auto preferred=id&4095u;if(auto owner=find(slots[preferred]))return owner;
                for(unsigned i=0;i<slots.size();i++)if(i!=preferred)if(auto owner=find(slots[i]))return owner;
                return uintptr_t(0);
            };
            NativeLocalHero candidate;candidate.localId=local;candidate.controller=entity(local);
            candidate.reference=component(candidate.controller,0x20);candidate.heroInfo=component(candidate.controller,0x3f);
            if(!candidate.reference||!candidate.heroInfo||!read(candidate.reference+0x94,&candidate.modelId,4))return false;
            candidate.model=entity(candidate.modelId);
            if(!candidate.controller||!candidate.model)return false;
            *this=candidate;
        }
        uint32_t controllerId=0,modelIdentifier=0,referenceId=0,currentLocal=0;
        return read(controller+0x94,&controllerId,4)&&controllerId==localId&&ptr(controller+0x28)==admin
            &&read(model+0x94,&modelIdentifier,4)&&modelIdentifier==modelId&&ptr(model+0x28)==admin
            &&ptr(reference+8)==controller&&read(reference+0x94,&referenceId,4)&&referenceId==modelId
            &&ptr(heroInfo+8)==controller&&read(heroInfo+0x98,&hero,8)
            &&read(admin+0x220,&currentLocal,4)&&currentLocal==localId;
    }
};
}
