#include "../src/provided_debug_ui.hpp"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
using passthrough::ProvidedDebugUi;

// Inert byte storage: no DLL load, process attach, graphics or game calls.
struct Fixture {
    static constexpr uintptr_t base=0x10000000;
    std::vector<unsigned char> bytes=std::vector<unsigned char>(0x2e8000);
    unsigned exchanges=0;
    bool writable=true,race=false;
    template<class T> void put(size_t offset,const T& value){std::memcpy(bytes.data()+offset,&value,sizeof value);}
    Fixture() {
        IMAGE_DOS_HEADER dos{};dos.e_magic=IMAGE_DOS_SIGNATURE;dos.e_lfanew=0x80;put(0,dos);
        IMAGE_NT_HEADERS64 nt{};nt.Signature=IMAGE_NT_SIGNATURE;nt.FileHeader.Machine=IMAGE_FILE_MACHINE_AMD64;
        nt.FileHeader.TimeDateStamp=0x695967ac;nt.OptionalHeader.Magic=IMAGE_NT_OPTIONAL_HDR64_MAGIC;
        nt.OptionalHeader.SizeOfImage=DWORD(bytes.size());nt.OptionalHeader.NumberOfRvaAndSizes=16;
        nt.OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_DEBUG]={0x400,sizeof(IMAGE_DEBUG_DIRECTORY)};put(0x80,nt);
        IMAGE_DEBUG_DIRECTORY debug{};debug.Type=IMAGE_DEBUG_TYPE_CODEVIEW;debug.AddressOfRawData=0x450;debug.SizeOfData=24;put(0x400,debug);
        const std::array<unsigned char,24> rsds{'R','S','D','S',0x62,0x43,0xb6,0x7b,0xb4,0xc6,0x72,0x44,0xb3,0x53,0x23,0xc1,0xdf,0xc3,0xa1,0xa6,1,0,0,0};put(0x450,rsds);
        const std::array<unsigned char,14> toggle{0x80,0x3d,0x26,0x0d,0x29,0,0,0x0f,0x94,0x05,0x1f,0x0d,0x29,0};put(0x3f273,toggle);
        const std::array<unsigned char,14> gate{0x80,0x3d,0xbc,0x0c,0x29,0,0,0x75,0x05,0xe8,0x35,0x60,0x08,0};put(0x3f2dd,gate);
        bytes[ProvidedDebugUi::flagRva+1]=0x5a;bytes[ProvidedDebugUi::flagRva+2]=1; // Neighbor, including isDemo.
    }
    auto read(){return [this](uintptr_t at,void* out,size_t size){
        if(at<base||at-base>bytes.size()||size>bytes.size()-(at-base))return false;
        std::memcpy(out,bytes.data()+at-base,size);return true;
    };}
    auto exchange(){return [this](uintptr_t at,unsigned char expected,unsigned char value,unsigned char& observed){
        assert(at==base+ProvidedDebugUi::flagRva);exchanges++;
        if(!writable)return false;
        auto& byte=bytes[at-base];if(race)byte=1;
        observed=byte;if(byte==expected)byte=value;return true;
    };}
    auto& flag(){return bytes[ProvidedDebugUi::flagRva];}
};

int main(int argc,char** argv) {
    {
        auto* page=static_cast<unsigned char*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));assert(page);
        page[1]=0x5a;unsigned char observed=9;const auto at=reinterpret_cast<uintptr_t>(page);
        assert(ProvidedDebugUi::exchangeByte(at,0,1,observed)&&observed==0&&page[0]==1&&page[1]==0x5a);
        assert(ProvidedDebugUi::exchangeByte(at,0,0,observed)&&observed==1&&page[0]==1);
        assert(ProvidedDebugUi::exchangeByte(at,1,0,observed)&&observed==1&&page[0]==0);
        DWORD old=0;assert(VirtualProtect(page,4096,PAGE_READONLY,&old));
        assert(!ProvidedDebugUi::exchangeByte(at,0,1,observed)&&page[0]==0&&page[1]==0x5a);
        assert(VirtualFree(page,0,MEM_RELEASE));
    }
    {
        Fixture f;const auto original=f.bytes;ProvidedDebugUi ui;
        assert(ui.acquire(f.base,f.read(),f.exchange())&&ui.verified&&ui.hidden&&ui.owned&&!ui.restored);
        auto expected=original;expected[ProvidedDebugUi::flagRva]=1;assert(f.bytes==expected);
        assert(!ui.acquire(f.base,f.read(),f.exchange())&&f.exchanges==1);
        assert(ui.release(f.read(),f.exchange())&&ui.restored&&!ui.owned&&f.bytes==original);
        assert(ui.release(f.read(),f.exchange())&&f.exchanges==2);
    }
    {
        Fixture f;f.flag()=1;ProvidedDebugUi ui;
        assert(ui.acquire(f.base,f.read(),f.exchange())&&ui.hidden&&!ui.owned&&ui.restored&&f.exchanges==0);
        f.flag()=0;ui.sample(f.read());assert(!ui.hidden); // Keep the original manual toggle.
        assert(ui.release(f.read(),f.exchange())&&f.flag()==0&&f.exchanges==0);
    }
    {
        Fixture f;ProvidedDebugUi ui;assert(ui.acquire(f.base,f.read(),f.exchange()));
        f.flag()=0;ui.sample(f.read());assert(!ui.hidden);
        assert(ui.release(f.read(),f.exchange())&&f.flag()==0&&ui.restored);
    }
    {
        Fixture f;ProvidedDebugUi ui;assert(ui.acquire(f.base,f.read(),f.exchange()));
        f.flag()=7;const auto changed=f.bytes;
        assert(!ui.release(f.read(),f.exchange())&&f.bytes==changed&&!ui.restored);
        f.flag()=1;assert(ui.release(f.read(),f.exchange())&&f.flag()==0);
    }
    {
        Fixture f;ProvidedDebugUi ui;assert(ui.acquire(f.base,f.read(),f.exchange()));
        f.bytes[0x454]^=1;const auto changed=f.bytes;
        assert(!ui.release(f.read(),f.exchange())&&f.bytes==changed&&f.exchanges==1&&!ui.restored);
        f.bytes[0x454]^=1;assert(ui.release(f.read(),f.exchange()));
    }
    // Every modified identity, draw gate or unexpected flag must refuse before
    // an exchange. Compare the entire inert image, including adjacent flags.
    unsigned refused=0;
    for(size_t offset:{size_t(0),size_t(0x3c),size_t(0x80),size_t(0x84),size_t(0x88),
        size_t(0x98),size_t(0xd0),size_t(0x104),size_t(0x138),size_t(0x13c),
        size_t(0x40c),size_t(0x413),size_t(0x414),size_t(0x450),size_t(0x454),size_t(0x464),
        size_t(0x3f273),size_t(0x3f279),size_t(0x3f27d),size_t(0x3f2dd),size_t(0x3f2e4),size_t(0x3f2ea),ProvidedDebugUi::flagRva}) {
        Fixture f;if(offset==0x104)f.put(offset,DWORD(0));else f.bytes[offset]^=0x80;
        const auto before=f.bytes;ProvidedDebugUi ui;
        assert(!ui.acquire(f.base,f.read(),f.exchange())&&f.exchanges==0&&f.bytes==before&&!ui.owned);refused++;
    }
    for(bool race:{false,true}) {
        Fixture f;f.race=race;f.writable=race;ProvidedDebugUi ui;
        assert(!ui.acquire(f.base,f.read(),f.exchange())&&!ui.owned&&ui.restored);
        assert(ui.release(f.read(),f.exchange())&&f.flag()==(race?1:0));
    }
    if(argc==2) {
        // Read the local provided PE into an ordinary vector, without executing
        // it. This proves the production guards accept the actual local identity.
        std::ifstream input(argv[1],std::ios::binary);assert(input);
        const std::vector<unsigned char> file{std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
        IMAGE_DOS_HEADER dos{};assert(file.size()>=sizeof dos);std::memcpy(&dos,file.data(),sizeof dos);
        assert(dos.e_lfanew>0&&size_t(dos.e_lfanew)+sizeof(IMAGE_NT_HEADERS64)<file.size());
        IMAGE_NT_HEADERS64 nt{};std::memcpy(&nt,file.data()+dos.e_lfanew,sizeof nt);
        Fixture f;f.bytes.assign(nt.OptionalHeader.SizeOfImage,0);
        assert(nt.OptionalHeader.SizeOfHeaders<=file.size()&&nt.OptionalHeader.SizeOfHeaders<=f.bytes.size());
        std::memcpy(f.bytes.data(),file.data(),nt.OptionalHeader.SizeOfHeaders);
        size_t offset=dos.e_lfanew+offsetof(IMAGE_NT_HEADERS64,OptionalHeader)+nt.FileHeader.SizeOfOptionalHeader;
        for(unsigned n=0;n<nt.FileHeader.NumberOfSections;n++,offset+=sizeof(IMAGE_SECTION_HEADER)) {
            IMAGE_SECTION_HEADER section{};assert(offset+sizeof section<=file.size());std::memcpy(&section,file.data()+offset,sizeof section);
            assert(size_t(section.PointerToRawData)+section.SizeOfRawData<=file.size());
            assert(size_t(section.VirtualAddress)+section.SizeOfRawData<=f.bytes.size());
            std::memcpy(f.bytes.data()+section.VirtualAddress,file.data()+section.PointerToRawData,section.SizeOfRawData);
        }
        ProvidedDebugUi ui;const auto before=f.bytes;
        assert(ui.acquire(f.base,f.read(),f.exchange())&&ui.verified&&ui.hidden);
        assert(ui.release(f.read(),f.exchange())&&f.bytes==before);
        std::cout<<"Local provided PE identity/draw gate accepted in inert byte storage; no DLL loaded.\n";
    }
    std::cout<<"Provided debug UI: hide/restore/manual-toggle/neighbor preservation, "<<refused<<" refusal cases and write/race failures passed.\n";
}
