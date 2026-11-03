#pragma once
#include <windows.h>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <cmath>

namespace passthrough {
// The verified beta's default native frame-controller limit, separate from
// client.MaxFPS. Change only its aligned data value, never executable code.
class NativeFrameLimit {
    volatile LONG* value=nullptr;
    DWORD protection=PAGE_READWRITE;
    LONG originalValue=original;
    static constexpr LONG original=0x42c80000; // 100.0f
    static constexpr LONG raised=0x43700000;   // 240.0f
public:
    std::atomic<bool> owned{false},restored{true};
    bool acquire(volatile LONG* candidate){
        if(value||!candidate||reinterpret_cast<uintptr_t>(candidate)%4)return false;
        if(InterlockedCompareExchange(candidate,raised,originalValue)!=originalValue)return false;
        value=candidate;owned=true;restored=false;return true;
    }
    bool release(){
        if(!value)return true;
        DWORD previous=0;bool writable=VirtualProtect(const_cast<LONG*>(value),sizeof(LONG),PAGE_READWRITE,&previous);
        auto prior=writable?InterlockedCompareExchange(value,originalValue,raised):0;
        if(writable){DWORD ignored=0;VirtualProtect(const_cast<LONG*>(value),sizeof(LONG),protection,&ignored);}
        bool ok=writable&&(prior==raised||prior==originalValue);
        restored=ok;if(ok){owned=false;value=nullptr;}return ok;
    }
    bool bindVerifiedBeta(uintptr_t base){
        auto read=[](uintptr_t at,void* out,size_t size){SIZE_T count=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),out,size,&count)&&count==size;};
        for(uintptr_t rva:{uintptr_t(0x7e76d5),uintptr_t(0x7e75f9)}){
            std::array<unsigned char,8> code{};int32_t displacement=0;
            if(!read(base+rva,code.data(),code.size())||code[0]!=0xf3||code[1]!=0x0f||code[2]!=0x10||code[3]!=(rva==0x7e76d5?0x05:0x35))return false;
            std::memcpy(&displacement,code.data()+4,4);
            if(rva+8+displacement!=0x179f130)return false;
        }
        std::array<float,2> controls{};
        if(!read(base+0x179f138,controls.data(),sizeof controls)||controls[0]!=-1||controls[1]!=60)return false;
        MEMORY_BASIC_INFORMATION page{};auto address=reinterpret_cast<volatile LONG*>(base+0x179f130);
        // The provided offline loader leaves this data section writable+executable.
        // Preserve its protection; the two verified loads identify only four data bytes.
        float initial=0; if(!read(reinterpret_cast<uintptr_t>(address),&initial,sizeof initial)
                ||!std::isfinite(initial)||initial<30.f||initial>120.f)return false;
        std::memcpy(&originalValue,&initial,sizeof originalValue);
        if(!VirtualQuery(const_cast<LONG*>(address),&page,sizeof page)||page.State!=MEM_COMMIT)return false;
        DWORD writableProtection=0;
        if(!VirtualProtect(const_cast<LONG*>(address),sizeof(LONG),PAGE_READWRITE,&writableProtection))return false;
        protection=page.Protect;
        bool acquired=acquire(address);
        DWORD ignored=0;VirtualProtect(const_cast<LONG*>(address),sizeof(LONG),protection,&ignored);
        return acquired;
    }
};
}
