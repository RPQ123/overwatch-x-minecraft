// Native feature initialization, without OS input. Same original DP Load call
// and map state transition as the supplied plugin, on its Present/UI owner.
#include "native_client_paths.hpp"
#include <windows.h>
#include <dxgi.h>
#include <array>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <cstring>
#include "empty_stage_data.hpp"
#include "map_daylight_data.hpp"
#include "bootstrap_map_policy.hpp"
extern "C" size_t traceSwapCount();
namespace {
struct Request{char magic[8];uint32_t version,size,pid,reserved;uint64_t creation,module;uint32_t imageSize,timestamp,demo,load;std::array<unsigned char,32> prefix;uint64_t map;};
static_assert(sizeof(Request)==96);
HMODULE own;Request req{};uintptr_t base=0;IDXGISwapChain* swap=nullptr;void **original=nullptr,**owned=nullptr;
std::atomic<bool> enabled{false},restored{false};std::atomic<unsigned> phase{0},failures{0};uint64_t started=0;
void** mapSlot=nullptr;void* mapOriginal=nullptr;std::atomic<unsigned> mapsEmptied{0},mapsQuieted{0},mapFailures{0};
void WINAPI mapConstruct(void* entry);
void restoreMap(){if(mapSlot)InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(mapSlot),mapOriginal,reinterpret_cast<void*>(mapConstruct));}

template<class T> bool read(uintptr_t p,T& out){SIZE_T n=0;return p>=0x10000&&p<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&out,sizeof out,&n)&&n==sizeof out;}
uintptr_t ptr(uintptr_t p){uintptr_t result=0;read(p,result);return result;}
uintptr_t world(){
    auto admin=ptr(base+0x17b7f90);uint32_t local=1;struct List{uintptr_t items;int count,capacity;} list{};
    if(!read(admin+0x220,local)||local||!read(admin+0xd8,list)||list.count<1||list.count>list.capacity||list.capacity>128)return 0;
    uintptr_t result=0;for(int i=0;i<list.count;i++){auto system=ptr(list.items+i*8);if(ptr(system)==base+0x15c3118){if(result||ptr(system+8)!=admin)return 0;result=system;}}return result;
}
void stop(){enabled=false;restoreMap();if(swap){InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),original,owned);restored=*reinterpret_cast<void***>(swap)==original&&(!mapSlot||*mapSlot==mapOriginal);swap->Release();swap=nullptr;}}
void WINAPI mapConstruct(void* entry){
    auto address=reinterpret_cast<uintptr_t>(entry);uint64_t id=0;uintptr_t data=0;
    if(read(address+0x50,id)&&id==req.map){
        std::array<unsigned char,0x320> header{};uint32_t flags=0;
        if(!read(address+0x20,flags)||(flags&4)||!read(address+0x40,data)||!read(data,header)
           ||!(id==0x0800000000000223ULL?owmc::emptyStageHeader(header):owmc::daylightHollywoodHeader(header)))mapFailures++;
        else{memcpy(reinterpret_cast<void*>(data),header.data(),header.size());
            if(id==0x0800000000000223ULL)mapsEmptied++;else mapsQuieted++;}
    }
    reinterpret_cast<void(WINAPI*)(void*)>(mapOriginal)(entry);
}
HRESULT WINAPI present(IDXGISwapChain* s,UINT interval,UINT flags){
    if(enabled&&!(flags&DXGI_PRESENT_TEST)){
        auto now=GetTickCount64();if(now-started>60000){failures++;stop();}
        else if(phase==0){
            unsigned char demo=0;std::array<unsigned char,32> prefix{};
            if(!read(req.module+req.demo,demo)||demo||!read(base+req.load,prefix)||prefix!=req.prefix){failures++;stop();}
            else{
                if(owmc::bootstrapPatchesMap(req.map)){
                    auto manager=ptr(base+0x182c940+18*8);
                    if(manager!=base+0x17aa6d0||ptr(manager+0x40)!=base+0x9d78a0){failures++;stop();return reinterpret_cast<decltype(&present)>(original[8])(s,interval,flags);}
                    mapSlot=reinterpret_cast<void**>(manager+0x40);mapOriginal=*mapSlot;
                    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(mapSlot),reinterpret_cast<void*>(mapConstruct),mapOriginal)!=mapOriginal){failures++;stop();return reinterpret_cast<decltype(&present)>(original[8])(s,interval,flags);}
                }
                *reinterpret_cast<unsigned char*>(req.module+req.demo)=1;phase=1;char payload[128]{};reinterpret_cast<int64_t(WINAPI*)(int64_t,int64_t,char*)>(base+req.load)(0,0,payload);}
        }else if(auto system=world()){
            unsigned char state=0;uint64_t wanted=0,loaded=0;
            if(!read(system+0x10,state)||!read(system+0x18,wanted)||!read(system+0x20,loaded)){failures++;stop();}
            else if(phase==1&&now-started>=3000){
                if(wanted||loaded){failures++;stop();}
                else{*reinterpret_cast<uint64_t*>(system+0x18)=req.map;*reinterpret_cast<unsigned char*>(system+0x10)=2;phase=2;}
            }else if(phase==2&&state==8&&loaded==req.map){if(!owmc::bootstrapMapPrepared(req.map,mapFailures.load(),mapsEmptied.load(),mapsQuieted.load())){failures++;stop();}
                else{phase=3;stop();}}
        }
    }
    return reinterpret_cast<decltype(&present)>(original[8])(s,interval,flags);
}
void report(const std::filesystem::path& dir){
    auto file=dir/("session-bootstrap-"+std::to_string(GetCurrentProcessId())+".json"),temp=file;temp+=L".tmp";
    std::ofstream out(temp);out<<"{\"probeVersion\":10,\"mapsEmptied\":"<<mapsEmptied<<" ,\"mapsQuieted\":"<<mapsQuieted<<",\"mapFailures\":"<<mapFailures<<",\"mapId\":"<<req.map<<",\"mapHeaderPatched\":"<<(owmc::bootstrapPatchesMap(req.map)?"true":"false")<<",\"pid\":"<<GetCurrentProcessId()<<",\"phase\":"<<phase<<",\"enabled\":"<<(enabled?"true":"false")<<",\"restored\":"<<(restored?"true":"false")<<",\"failures\":"<<failures<<",\"nativeCalls\":true}";out.close();MoveFileExW(temp.c_str(),file.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*){
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(own,dll))return 0;
    auto dir=dll.parent_path();
    std::ifstream in(dir/("session-bootstrap-request-"+std::to_string(GetCurrentProcessId())+".bin"),std::ios::binary);in.read(reinterpret_cast<char*>(&req),sizeof req);
    FILETIME creation{},exit{},kernel{},user{};uint64_t created=0;
    if(!in||in.peek()!=EOF||memcmp(req.magic,"OWBOOT01",8)||req.version!=10||req.size!=96||req.pid!=GetCurrentProcessId()||req.reserved||!owmc::bootstrapMapAllowed(req.map)||req.load!=0xc7f090||!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user))return 0;
    memcpy(&created,&creation,8);if(created!=req.creation||!owmc::loadedClientCompanion(reinterpret_cast<HMODULE>(req.module),exe,L"inject.dll"))return 0;
    IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};
    if(!read(req.module,dos)||dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<0||dos.e_lfanew>4096||!read(req.module+dos.e_lfanew,nt)||nt.Signature!=IMAGE_NT_SIGNATURE||nt.OptionalHeader.SizeOfImage!=req.imageSize||nt.FileHeader.TimeDateStamp!=req.timestamp||req.demo>=req.imageSize)return 0;
    base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));auto engine=ptr(base+0x181e3e0),a=ptr(engine+0x900),b=ptr(a+0x2e0),c=ptr(b);swap=reinterpret_cast<IDXGISwapChain*>(ptr(c+8));if(!swap)return 0;
    original=*reinterpret_cast<void***>(swap);owned=new void*[traceSwapCount()];SIZE_T bytes=0;
    if(!ReadProcessMemory(GetCurrentProcess(),original,owned,traceSwapCount()*8,&bytes)||bytes!=traceSwapCount()*8)return 0;
    owned[8]=reinterpret_cast<void*>(present);swap->AddRef();started=GetTickCount64();enabled=true;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),owned,original)!=original){enabled=false;failures++;stop();report(dir);return 0;}
    while(enabled){report(dir);Sleep(100);}report(dir);return 0;
}
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD reason,void*){if(reason==DLL_PROCESS_ATTACH){own=h;DisableThreadLibraryCalls(h);auto thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread)CloseHandle(thread);}return TRUE;}
