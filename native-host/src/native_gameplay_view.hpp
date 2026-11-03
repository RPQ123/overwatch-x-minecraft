#pragma once
#include <cstdint>
namespace passthrough {
// Same exact original camera owner/state proof used by the launcher. Native
// initial picker keeps its own actor pose until the first gameplay selection.
template<class Read> bool nativeGameplayView(uintptr_t base,uintptr_t admin,Read read){
    auto ptr=[&](uintptr_t at){uintptr_t value=0;read(at,&value,8);return value;};
    struct List{uintptr_t items;int count,capacity;} list{};
    auto iterators=ptr(admin+0xb0);
    if(!iterators||!read(iterators+0x4f*24,&list,sizeof list)||list.count<1||list.count>list.capacity||list.capacity>256)return false;
    auto component=ptr(list.items),camera=ptr(component+0x40),active=ptr(camera+0x260),normal=ptr(component+0x50);
    return active&&active==normal&&ptr(active)==base+0x15c7000;
}
}
