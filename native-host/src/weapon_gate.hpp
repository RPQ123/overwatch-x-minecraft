#pragma once
#include <windows.h>
#include <array>
#include <cstdint>
#include <utility>

namespace passthrough {
inline bool measuredWeaponGateFlags(uint32_t flags) {
    // Exact idle and OnBegin values read in the supplied Genji build. The
    // original dispatcher changes its execution bits before the callback.
    auto original=flags&~8u;return original==0x408001u||original==0x400081u||original==0x400001u;
}
inline bool measuredBastionTankGateFlags(uint64_t hero,uint64_t script,unsigned node,uint32_t flags) {
    // Actual beta Tank024f has the extra execution bit2. This is NOT a
    // general permission for server-only scripts or other Bastion weapons.
    // The already-owned nested authority bit8 does not change this identity.
    auto original=flags&~8u;
    return hero==0x02e0000000000015ULL&&script==0x058000000000024fULL
        &&node==25&&(original==0x408003u||original==0x400083u);
}
template<class Read> bool measuredBastionTankVolleyScope(uint64_t hero,uint64_t resource,
        uintptr_t state,uintptr_t instance,uintptr_t model,uintptr_t admin,
        uintptr_t expectedTable,uint32_t flags,Read read) {
    if(!measuredBastionTankGateFlags(hero,resource,25,flags))return false;
    auto pointer=[&](uintptr_t at){uintptr_t value=0;return read(at,value)?value:uintptr_t(0);};
    uint32_t actualFlags=0;int stateIndex=-1;
    if(!expectedTable||pointer(state)!=expectedTable||pointer(state+0x78)!=instance
       ||pointer(pointer(pointer(instance+0x10)+0x450)+8)!=model||pointer(model+0x28)!=admin
       ||!read(instance+0x258,actualFlags)||actualFlags!=flags||pointer(instance+0x150)!=resource
       ||!read(state+0x70,stateIndex)||stateIndex!=19)return false;
    auto graph=pointer(instance+0x160);
    auto list=[&](uintptr_t at,uintptr_t& items,uint64_t& count){
        std::array<uint64_t,2> storage{},values{};
        if(!read(at,storage)||(storage[1]!=1&&storage[1]!=2)||!read(storage[0],values))return false;
        items=values[storage[1]==1?0:1];count=values[storage[1]==1?1:0];
        return items>=0x10000&&count>0&&count<=4096;
    };
    uintptr_t states=0,nodes=0;uint64_t stateCount=0,nodeCount=0;
    if(!graph||!list(graph+0x60,states,stateCount)||stateCount!=22
       ||!list(graph+0x50,nodes,nodeCount)||nodeCount!=29)return false;
    // Runtime state+70 indexes m_states, NOT m_nodes. The measured Tank
    // node25 is m_states[19] in the current-owned native graph. Definition+6c
    // contains11 but is NOT the m_states index; its meaning is unproved and it
    // must not select a runtime state. Cross-check both actual original lists.
    auto definition=pointer(states+uintptr_t(stateIndex)*8);int node=-1;
    return definition&&pointer(nodes+25*8)==definition&&read(definition+0x68,node)&&node==25
        &&pointer(instance+0x160)==graph&&pointer(state)==expectedTable&&pointer(state+0x78)==instance;
}
// The bit is present only during this original native callback. Nested calls
// inherit it; only its owner clears it, preserving other native flag changes.
class ScopedWeaponGate {
    volatile LONG* flags=nullptr;
public:
    explicit ScopedWeaponGate(volatile LONG* value) {
        LONG before=InterlockedOr(value,8);if(!(before&8))flags=value;
    }
    ~ScopedWeaponGate(){if(flags)InterlockedAnd(flags,~LONG(8));}
    bool ownsBit()const{return flags!=nullptr;}
    ScopedWeaponGate(const ScopedWeaponGate&)=delete;
    ScopedWeaponGate& operator=(const ScopedWeaponGate&)=delete;
};
template<class Fn> auto withWeaponGate(volatile LONG* flags,Fn&& call) {
    ScopedWeaponGate scope(flags);return std::forward<Fn>(call)();
}
}
