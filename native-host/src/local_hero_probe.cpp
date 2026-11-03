// One original-plugin Spawn action on its normal Present/UI thread.
// No renderer, entity deletion, native movement or state-script replacement.
#include "native_client_paths.hpp"
#include "local_hero_spawn.hpp"
#include <windows.h>
#include <dxgi.h>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <cstring>
#include <algorithm>
extern "C" size_t traceSwapCount();
using namespace passthrough;
namespace {
struct Request {
    char magic[8];uint32_t version,size,pid,reserved;
    uint64_t moduleBase;uint32_t spawnRva,imageSize,imageTimestamp,prefixLen;
    std::array<uint8_t,16> guid;uint32_t age,reserved2;
    uint64_t expectedEA,hero,model;std::array<uint8_t,32> prefix;
    uint64_t creation,map;
};
static_assert(sizeof(Request)==144&&offsetof(Request,prefix)==96);
HMODULE ownModule;IDXGISwapChain* swap=nullptr;void **original=nullptr,**owned=nullptr;
std::atomic<bool> active{false},finished{false},cancelled{false};
bool fixture=false,restored=false,called=false;unsigned frames=0,failures=0;DWORD callbackThread=0;
Request request{};SpawnerAbi spawner{};SpawnPairAbi result{};OriginalSpawnFn spawnFn=nullptr;
template<class T> bool read(uintptr_t address,T& out) {SIZE_T n=0;return address>=0x10000&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&out,sizeof out,&n)&&n==sizeof out;}
uintptr_t pointer(uintptr_t a) {uintptr_t p=0;return read(a,p)?p:0;}
bool stableWorld() {
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));auto ea=pointer(base+0x17b7f90);
    uint32_t local=1;uint64_t list=0;int32_t count=0,capacity=0;
    if(ea!=request.expectedEA||!read(ea+0x220,local)||local||!read(ea+0xd8,list)||!read(ea+0xe0,count)||!read(ea+0xe4,capacity)||count<1||count>capacity||capacity>128)return false;
    unsigned found=0;
    for(int32_t i=0;i<count;i++) {auto system=pointer(list+i*8);if(pointer(system)==base+0x15c3118) {uint8_t state=0;uint64_t map=0;if(pointer(system+8)!=ea||!read(system+0x10,state)||state!=8||!read(system+0x20,map)||map!=request.map)return false;found++;}}
    return found==1&&pointer(base+0x17b7f90)==ea;
}
bool validate(const std::filesystem::path& executable,const std::filesystem::path& file) {
    std::ifstream in(file,std::ios::binary);in.read(reinterpret_cast<char*>(&request),sizeof request);
    if(!in||in.peek()!=EOF||memcmp(request.magic,"OWSPWN01",8)||request.version!=1||request.size!=sizeof request||request.pid!=GetCurrentProcessId()||request.reserved||request.reserved2||request.prefixLen!=32)return false;
    FILETIME creation{},exit{},kernel{},user{},now{};GetSystemTimeAsFileTime(&now);
    if(!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user))return false;
    uint64_t created=0;memcpy(&created,&creation,8);if(created!=request.creation)return false;
    WIN32_FILE_ATTRIBUTE_DATA attrs{};if(!GetFileAttributesExW(file.c_str(),GetFileExInfoStandard,&attrs))return false;
    uint64_t current=0,written=0;memcpy(&current,&now,8);memcpy(&written,&attrs.ftLastWriteTime,8);
    if(current<written||current-written>200000000ULL)return false;
    if(!owmc::loadedClientCompanion(reinterpret_cast<HMODULE>(request.moduleBase),executable,L"inject.dll"))return false;
    IMAGE_DOS_HEADER dos{};if(!read(request.moduleBase,dos)||dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<0||dos.e_lfanew>4096)return false;
    IMAGE_NT_HEADERS64 nt{};if(!read(request.moduleBase+dos.e_lfanew,nt)||nt.Signature!=IMAGE_NT_SIGNATURE||nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64||nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC||nt.OptionalHeader.SizeOfImage!=request.imageSize||nt.FileHeader.TimeDateStamp!=request.imageTimestamp||request.spawnRva>=request.imageSize-32)return false;
    auto debug=nt.OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_DEBUG];if(debug.Size>4096||debug.Size%sizeof(IMAGE_DEBUG_DIRECTORY)||debug.VirtualAddress>request.imageSize-debug.Size)return false;
    bool identity=false;
    for(unsigned offset=0;offset<debug.Size;offset+=sizeof(IMAGE_DEBUG_DIRECTORY)) {IMAGE_DEBUG_DIRECTORY d{};if(!read(request.moduleBase+debug.VirtualAddress+offset,d))return false;if(d.Type!=IMAGE_DEBUG_TYPE_CODEVIEW)continue;
        std::array<uint8_t,24> cv{};if(d.AddressOfRawData>request.imageSize-cv.size()||!read(request.moduleBase+d.AddressOfRawData,cv))return false;uint32_t age=0;memcpy(&age,cv.data()+20,4);
        if(!memcmp(cv.data(),"RSDS",4)&&std::equal(request.guid.begin(),request.guid.end(),cv.begin()+4)&&age==request.age)identity=true;
    }
    std::array<uint8_t,32> prefix{};if(!identity||!read(request.moduleBase+request.spawnRva,prefix)||prefix!=request.prefix)return false;
    MEMORY_BASIC_INFORMATION mem{};if(!VirtualQuery(reinterpret_cast<void*>(request.moduleBase+request.spawnRva),&mem,sizeof mem)||mem.AllocationBase!=reinterpret_cast<void*>(request.moduleBase)||!(mem.Protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)))return false;
    spawner=localHeroSpawner(request.hero,request.model);spawnFn=reinterpret_cast<OriginalSpawnFn>(request.moduleBase+request.spawnRva);return stableWorld();
}
bool labCallback(void* address) {
    HMODULE owner=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(address),&owner))return true;
    GetModuleFileNameW(owner,path,32768);auto name=std::filesystem::path(path).filename().wstring();return name.rfind(L"owmc-",0)==0||name.rfind(L"owhero-",0)==0;
}
void stop() {
    active=false;InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),original,owned);
    restored=*reinterpret_cast<void***>(swap)==original;swap->Release();swap=nullptr;finished=true;
}
HRESULT WINAPI present(IDXGISwapChain* s,UINT interval,UINT flags) {
    auto hr=reinterpret_cast<decltype(&present)>(original[8])(s,interval,flags);
    if(active&&!(flags&DXGI_PRESENT_TEST)) {
        frames++;
        if(!called&&!cancelled) {called=true;callbackThread=GetCurrentThreadId();try {if(!fixture&&!stableWorld())throw std::runtime_error("World changed before original spawn");result=invokeOriginalSpawn(spawnFn,spawner);}catch(const std::exception&) {failures++;}}
        if(frames>=3||cancelled)stop();
    }
    return hr;
}
bool attach(IDXGISwapChain* s) {
    if(!s||swap||finished)return false;
    original=*reinterpret_cast<void***>(s);if(!fixture&&labCallback(original[8]))return false;
    owned=new void*[traceSwapCount()];SIZE_T count=0;if(!ReadProcessMemory(GetCurrentProcess(),original,owned,traceSwapCount()*sizeof(void*),&count)||count!=traceSwapCount()*sizeof(void*))return false;
    owned[8]=reinterpret_cast<void*>(present);swap=s;s->AddRef();active=true;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(s),owned,original)!=original) {active=false;swap=nullptr;s->Release();return false;}return true;
}
void report(const std::filesystem::path& dir,const char* status) {
    auto file=dir/("local-hero-"+std::to_string(GetCurrentProcessId())+".json"),temp=file;temp+=L".tmp";std::ofstream out(temp);
    out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"status\":\""<<status<<"\",\"called\":"<<(called?"true":"false")<<",\"restored\":"<<(restored?"true":"false")<<",\"failures\":"<<failures<<",\"frames\":"<<frames<<",\"callbackThread\":"<<callbackThread<<",\"controller\":"<<result.controller<<",\"model\":"<<result.model<<"}";out.close();MoveFileExW(temp.c_str(),file.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(ownModule,dll))return 0;
    auto dir=dll.parent_path();
    try {
        if(!validate(exe,dir/("local-hero-request-"+std::to_string(GetCurrentProcessId())+".bin"))) {failures++;report(dir,"request-refused");return 0;}
        auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),engine=pointer(base+0x181e3e0),a=pointer(engine+0x900),b=pointer(a+0x2e0),c=pointer(b);
        if(!attach(reinterpret_cast<IDXGISwapChain*>(pointer(c+8)))) {failures++;report(dir,"attach-refused");return 0;}
        auto started=GetTickCount64();while(!finished) {if(GetTickCount64()-started>15000)cancelled=true;Sleep(5);}
        report(dir,failures?"original-spawn-incomplete":"original-spawn-completed");
    }catch(const std::exception&) {failures++;report(dir,"validation-failed");}return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_LocalHeroTestAttach(IDXGISwapChain* s,OriginalSpawnFn fn) {
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-local-hero-test.exe")return FALSE;
    fixture=true;spawnFn=fn;spawner=localHeroSpawner(0x02e0000000000029ULL,0x0400000000000225ULL);return attach(s);
}
extern "C" __declspec(dllexport) BOOL OWMC_LocalHeroTestVerify() {return finished&&restored&&called&&frames==3&&!failures&&callbackThread==GetCurrentThreadId()&&result.controller==spawner.controllerEntity&&result.model==spawner.modelEntity;}
BOOL WINAPI DllMain(HMODULE m,DWORD reason,LPVOID) {if(reason==DLL_PROCESS_ATTACH) {ownModule=m;DisableThreadLibraryCalls(m);HANDLE t=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(t)CloseHandle(t);}return TRUE;}
