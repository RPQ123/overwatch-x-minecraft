#pragma once
#include <windows.h>
#include <intrin.h>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstring>

namespace passthrough {
// The provided offline plugin's window_manager UI, separate from the game's
// native HUD and the tiny DEV ENABLED label. Only its data flag is changed;
// no draw suppression, code patch, new hook or screen-space cover is needed.
class ProvidedDebugUi {
    uintptr_t module=0;
    unsigned char original=0;
    bool changed=false;
public:
    static constexpr uintptr_t flagRva=0x2cffa0;
    std::atomic<bool> attempted{false},verified{false},hidden{false},owned{false},restored{true};

    static bool exchangeByte(uintptr_t at,unsigned char expected,unsigned char value,unsigned char& observed) {
        MEMORY_BASIC_INFORMATION page{};
        if(!VirtualQuery(reinterpret_cast<void*>(at),&page,sizeof page)||page.State!=MEM_COMMIT
            ||(page.Protect&(PAGE_GUARD|PAGE_NOACCESS))
            ||!(page.Protect&(PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)))return false;
        observed=static_cast<unsigned char>(_InterlockedCompareExchange8(reinterpret_cast<volatile char*>(at),char(value),char(expected)));
        return true;
    }

    template<class Read> static bool matches(uintptr_t base,Read read) {
        if(base<0x10000||base>0x7fffffffffffULL-0x2e8000)return false;
        IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};
        if(!read(base,&dos,sizeof dos)||dos.e_magic!=IMAGE_DOS_SIGNATURE
            ||dos.e_lfanew<LONG(sizeof dos)||dos.e_lfanew>4096
            ||!read(base+dos.e_lfanew,&nt,sizeof nt)||nt.Signature!=IMAGE_NT_SIGNATURE
            ||nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64
            ||nt.FileHeader.TimeDateStamp!=0x695967ac
            ||nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC
            ||nt.OptionalHeader.SizeOfImage!=0x2e8000
            ||nt.OptionalHeader.NumberOfRvaAndSizes<=IMAGE_DIRECTORY_ENTRY_DEBUG)return false;
        const auto& dir=nt.OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_DEBUG];
        if(!dir.Size||dir.Size>16*sizeof(IMAGE_DEBUG_DIRECTORY)||dir.Size%sizeof(IMAGE_DEBUG_DIRECTORY)
            ||dir.VirtualAddress>nt.OptionalHeader.SizeOfImage-dir.Size)return false;
        // GUID+age from the locally matched inject.dll/prometheus.pdb pair.
        const std::array<unsigned char,24> identity{'R','S','D','S',
            0x62,0x43,0xb6,0x7b,0xb4,0xc6,0x72,0x44,0xb3,0x53,0x23,0xc1,0xdf,0xc3,0xa1,0xa6,1,0,0,0};
        unsigned matches=0;
        for(UINT offset=0;offset<dir.Size;offset+=sizeof(IMAGE_DEBUG_DIRECTORY)) {
            IMAGE_DEBUG_DIRECTORY entry{};
            if(!read(base+dir.VirtualAddress+offset,&entry,sizeof entry))return false;
            if(entry.Type!=IMAGE_DEBUG_TYPE_CODEVIEW)continue;
            std::array<unsigned char,24> found{};
            if(entry.SizeOfData<found.size()||entry.SizeOfData>nt.OptionalHeader.SizeOfImage
                ||entry.AddressOfRawData>nt.OptionalHeader.SizeOfImage-entry.SizeOfData
                ||!read(base+entry.AddressOfRawData,found.data(),found.size())||found!=identity)return false;
            matches++;
        }
        if(matches!=1)return false;
        // Exact loads of ui_invisible in PresentHook: the original hotkey's
        // toggle, and the conditional call to window_manager::render().
        const std::array<unsigned char,14> toggle{0x80,0x3d,0x26,0x0d,0x29,0,0,0x0f,0x94,0x05,0x1f,0x0d,0x29,0};
        const std::array<unsigned char,14> drawGate{0x80,0x3d,0xbc,0x0c,0x29,0,0,0x75,0x05,0xe8,0x35,0x60,0x08,0};
        std::array<unsigned char,14> a{},b{};
        return read(base+0x3f273,a.data(),a.size())&&a==toggle
            &&read(base+0x3f2dd,b.data(),b.size())&&b==drawGate;
    }

    // Read/exchange are injected so identity/refusal/restoration can be tested
    // with an inert memory image. Production calls this once on its render owner.
    template<class Read,class Exchange> bool acquire(uintptr_t base,Read read,Exchange exchange) {
        if(attempted.exchange(true)||!matches(base,read))return false;
        verified=true;
        unsigned char value=0;
        if(!read(base+flagRva,&value,1)||value>1)return false;
        if(!value) {
            unsigned char observed=0;
            if(!exchange(base+flagRva,0,1,observed)||observed!=0)return false;
        }
        module=base;original=value;changed=!value;owned=changed;restored=!changed;hidden=true;
        return true;
    }
    template<class Read> void sample(Read read) {
        unsigned char value=0;
        if(module)hidden=read(module+flagRva,&value,1)&&value==1;
    }
    template<class Read,class Exchange> bool release(Read read,Exchange exchange) {
        if(!module)return true;
        if(!matches(module,read)){restored=false;return false;}
        if(changed) {
            unsigned char observed=0;
            if(!exchange(module+flagRva,1,original,observed)||observed>1){restored=false;return false;}
            // A manual toggle back to visible is already the original value.
            // The compare/exchange never overwrites a foreign/non-boolean edit.
        }
        sample(read);module=0;owned=false;restored=true;return true;
    }
};
}
