#include <windows.h>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>
namespace {
alignas(16) std::array<unsigned char,0x400> instance{},state0{},state1{};
std::array<void*,0x298/8+1> table{};
using Callback=uintptr_t(WINAPI*)(void*);
uintptr_t WINAPI nativeUpdate(void*){assert((*reinterpret_cast<unsigned*>(instance.data()+0x258)&8)!=0);return 33;}
uintptr_t WINAPI nativeShot(void*){assert((*reinterpret_cast<unsigned*>(instance.data()+0x258)&8)!=0);return 44;}
uintptr_t WINAPI nativeBegin(void* state){
    assert((*reinterpret_cast<unsigned*>(instance.data()+0x258)&8)!=0);auto vt=*reinterpret_cast<void***>(state);
    assert(reinterpret_cast<Callback>(vt[0x120/8])(state)==33&&reinterpret_cast<Callback>(vt[0x270/8])(state)==44);return 0xabcdef0123456789ULL;
}
}
void WINAPI nativeEntry(void*,void*,void* state){auto vt=*reinterpret_cast<void***>(state);assert(reinterpret_cast<Callback>(vt[0x110/8])(state)==0xabcdef0123456789ULL);}
int main(int argc,char** argv){
    table.fill(reinterpret_cast<void*>(nativeUpdate));table[1+0x110/8]=reinterpret_cast<void*>(nativeBegin);table[1+0x270/8]=reinterpret_cast<void*>(nativeShot);
    auto ptr=table.data()+1;*reinterpret_cast<unsigned*>(instance.data()+0x258)=0x408001;
    for(auto* s:{&state0,&state1}){std::memcpy(s->data(),&ptr,8);auto ip=reinterpret_cast<uintptr_t>(instance.data());std::memcpy(s->data()+0x78,&ip,8);}
    auto dll=LoadLibraryW(L"native-host/build/owmc-weapon-gate-v6.dll");assert(dll);
    FARPROC attachAddress=GetProcAddress(dll,"OWMC_WeaponGateTestAttach"),stopAddress=GetProcAddress(dll,"OWMC_WeaponGateTestStop");assert(attachAddress&&stopAddress);
    union {FARPROC raw;BOOL(*fn)(uintptr_t,uintptr_t,uintptr_t);} attachCast{attachAddress};
    union {FARPROC raw;BOOL(*fn)();} stopCast{stopAddress};auto attach=attachCast.fn;auto stop=stopCast.fn;
    if(argc>1){
        auto lazyAddress=GetProcAddress(dll,"OWMC_WeaponGateTestLazy");assert(lazyAddress);union {FARPROC raw;BOOL(*fn)(uintptr_t,void**,void**);} lazy{lazyAddress};
        auto* state=std::strcmp(argv[1],"--lazy-right")==0?state1.data():state0.data();int index=state==state0.data()?4:13;std::memcpy(state+0x70,&index,4);
        void* callback=reinterpret_cast<void*>(nativeEntry);assert(lazy.fn(reinterpret_cast<uintptr_t>(instance.data()),ptr,&callback));
        assert(*reinterpret_cast<void***>(state)==ptr);reinterpret_cast<void(WINAPI*)(void*,void*,void*)>(callback)(nullptr,instance.data(),state);
        assert(*reinterpret_cast<void***>(state)!=ptr&&*reinterpret_cast<unsigned*>(instance.data()+0x258)==0x408001);assert(stop());
        assert(callback==reinterpret_cast<void*>(nativeEntry)&&*reinterpret_cast<void***>(state)==ptr);std::cout<<"PASS lazy first original attack: state entry chained, first Begin/Update/Shot gated and all callbacks restored.\n";return 0;
    }
    assert(attach(reinterpret_cast<uintptr_t>(instance.data()),reinterpret_cast<uintptr_t>(state0.data()),reinterpret_cast<uintptr_t>(state1.data())));
    auto vt=*reinterpret_cast<void***>(state0.data());assert(vt!=ptr&&vt[-1]==ptr[-1]);
    assert(reinterpret_cast<Callback>(vt[0x110/8])(state0.data())==0xabcdef0123456789ULL);
    assert(*reinterpret_cast<unsigned*>(instance.data()+0x258)==0x408001&&stop());
    assert(*reinterpret_cast<void***>(state0.data())==ptr&&*reinterpret_cast<void***>(state1.data())==ptr);
    std::cout<<"Original callback returns, nested original update/shot, scoped flag restoration, both vtables and prefix preserved/restored.\n";
}
