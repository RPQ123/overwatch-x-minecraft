#include "native_client_paths.hpp"
#include "weapon_gate.hpp"
#include <array>
#include <atomic>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <vector>

namespace {
struct Request {
    char magic[8];uint32_t version,size,pid,reserved;
    uint64_t creation,admin,localId,modelId,instance,state0,state1,flags,entryPointer,entryOriginal;
};
static_assert(sizeof(Request)==104);
using Entry=void(WINAPI*)(void*,void*,void*);
Entry entryOriginal=nullptr;std::atomic<uintptr_t> liveStates[2]{};
void** fixtureTable=nullptr;
using Callback=uintptr_t(WINAPI*)(void*);
constexpr size_t slots=0x298/8;
HMODULE module;Request request{};bool fixture=false;
void** original=nullptr;std::array<void*,slots+1> owned{};
std::array<Callback,3> callbacks{};
std::atomic<bool> active{false},restored{false};
std::atomic<unsigned> failures{0},inFlight{0},flagScopes{0},beginCalls{0},updateCalls{0},shotCalls{0},dropped{0};
std::atomic<DWORD> callbackThread{0};
struct Row {uint64_t clock,state,id,pointer,definition,projectileConfig;uint32_t operation,before,after,index,count;bool permitted,identity;};
std::mutex rowLock;std::vector<Row> rows;
uintptr_t base=0;
template<class T> bool read(uintptr_t p,T& v){SIZE_T n=0;return p>=0x10000&&p<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&v,sizeof v,&n)&&n==sizeof v;}
uintptr_t ptr(uintptr_t p){uintptr_t v=0;return read(p,v)?v:0;}
bool identity(){
    for(auto& value:liveStates){auto state=value.load();if(state&&ptr(state+0x78)!=request.instance)return false;}
    if(fixture)return true;
    uint32_t id=0;uint64_t resource=0;
    if(ptr(base+0x17b7f90)!=request.admin||!read(request.admin+0x220,id)||id!=request.localId||!read(request.instance+0x150,resource)||resource!=0x0580000000000304)return false;
    auto component=ptr(ptr(request.instance+0x10)+0x450),model=ptr(component+8);
    return read(model+0x94,id)&&id==request.modelId&&ptr(model+0x28)==request.admin;
}
uintptr_t dispatch(void* state,unsigned operation){
    inFlight++;
    struct Leave{~Leave(){--inFlight;}}leave;
    const auto address=reinterpret_cast<uintptr_t>(state);uint32_t flags=0;
    DWORD expected=0;callbackThread.compare_exchange_strong(expected,GetCurrentThreadId());
    bool sameIdentity=identity(),readFlags=read(request.instance+0x258,flags);
    bool permitted=active&&(address==liveStates[0]||address==liveStates[1])&&sameIdentity
        &&callbackThread==GetCurrentThreadId()&&readFlags&&passthrough::measuredWeaponGateFlags(flags);
    Row row{};row.clock=GetTickCount64();row.state=address;row.operation=operation;row.before=flags;row.permitted=permitted;row.identity=sameIdentity;
    if(!permitted){if(active){++failures;active=false;std::lock_guard<std::mutex> lock(rowLock);rows.push_back(row);}return callbacks[operation](state);}
    if(operation==0)++beginCalls;else if(operation==1)++updateCalls;else ++shotCalls;
    if(!(flags&8))++flagScopes;
    read(address+0xa8,row.id);read(address+0xd0,row.pointer);
    row.definition=ptr(row.pointer+0xc0);row.projectileConfig=ptr(row.definition+0x28);
    auto result=passthrough::withWeaponGate(reinterpret_cast<volatile LONG*>(request.instance+0x258),[&]{return callbacks[operation](state);});
    read(request.instance+0x258,row.after);read(address+0x110,row.index);read(address+0x128,row.count);
    {std::lock_guard<std::mutex> lock(rowLock);if(rows.size()<2048)rows.push_back(row);else ++dropped;}
    return result;
}
uintptr_t WINAPI begin(void* state){return dispatch(state,0);}
uintptr_t WINAPI update(void* state){return dispatch(state,1);}
uintptr_t WINAPI shot(void* state){return dispatch(state,2);}
void WINAPI entry(void* sync,void* script,void* state){
    inFlight++;struct Leave{~Leave(){--inFlight;}}leave;
    if(active&&reinterpret_cast<uintptr_t>(script)==request.instance&&identity()){
        auto address=reinterpret_cast<uintptr_t>(state);int index=-1;
        if(ptr(address+0x78)==request.instance&&ptr(address)==reinterpret_cast<uintptr_t>(original)&&read(address+0x70,index)&&(index==4||index==13)){
            auto& slot=liveStates[index==4?0:1];uintptr_t previous=slot.load();
            if((!previous||previous==address)&&InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(state),owned.data()+1,original)==original)slot=address;
        }
    }
    entryOriginal(sync,script,state);
}
bool install(){
    liveStates[0]=request.state0;liveStates[1]=request.state1;
    if(!identity())return false;
    original=fixture?(fixtureTable?fixtureTable:reinterpret_cast<void**>(ptr(request.state0))):reinterpret_cast<void**>(base+0x15d2450);
    if(!read(reinterpret_cast<uintptr_t>(original)-8,owned))return false;
    callbacks={reinterpret_cast<Callback>(original[0x110/8]),reinterpret_cast<Callback>(original[0x120/8]),reinterpret_cast<Callback>(original[0x270/8])};
    owned[1+0x110/8]=reinterpret_cast<void*>(begin);owned[1+0x120/8]=reinterpret_cast<void*>(update);owned[1+0x270/8]=reinterpret_cast<void*>(shot);
    rows.reserve(2048);active=true;
    for(auto& slot:liveStates){auto address=slot.load();if(address&&InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(address),owned.data()+1,original)!=original){active=false;return false;}}
    if(request.entryPointer){entryOriginal=reinterpret_cast<Entry>(request.entryOriginal);if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(request.entryPointer),reinterpret_cast<void*>(entry),reinterpret_cast<void*>(entryOriginal))!=reinterpret_cast<void*>(entryOriginal)){active=false;return false;}}
    return true;
}
void stop(){
    active=false;bool all=true;
    if(request.entryPointer){auto old=InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(request.entryPointer),reinterpret_cast<void*>(entryOriginal),reinterpret_cast<void*>(entry));all=old==reinterpret_cast<void*>(entryOriginal)||old==reinterpret_cast<void*>(entry);}
    for(auto& slot:liveStates){auto address=slot.load();if(!address)continue;
        if(!address||ptr(address+0x78)!=request.instance){all=false;continue;}
        auto previous=InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(address),original,owned.data()+1);
        all=all&&(previous==original||previous==owned.data()+1);
    }
    for(unsigned i=0;i<200&&inFlight;i++)Sleep(10);
    uint32_t flags=8;all=all&&!inFlight&&read(request.instance+0x258,flags)&&!(flags&8);restored=all;
}
void report(const std::filesystem::path& directory){
    auto path=directory/(L"weapon-gate-"+std::to_wstring(GetCurrentProcessId())+L".json"),temp=path;temp+=L".tmp";
    std::ofstream o(temp);o<<"{\"pid\":"<<GetCurrentProcessId()<<",\"probeVersion\":6,\"enabled\":"<<(active?"true":"false")<<",\"restored\":"<<(restored?"true":"false")
      <<",\"failures\":"<<failures<<",\"beginCalls\":"<<beginCalls<<",\"updateCalls\":"<<updateCalls<<",\"shotCalls\":"<<shotCalls
      <<",\"flagScopes\":"<<flagScopes<<",\"callbackThread\":"<<callbackThread<<",\"dropped\":"<<dropped<<",\"projectileEmissionVerified\":false,\"mcDamageSent\":false,\"rows\":[";
    {std::lock_guard<std::mutex> lock(rowLock);for(size_t i=0;i<rows.size();i++){if(i)o<<',';auto r=rows[i];o<<"{\"clock\":"<<r.clock<<",\"state\":"<<r.state<<",\"operation\":"<<r.operation<<",\"before\":"<<r.before<<",\"after\":"<<r.after<<",\"permitted\":"<<(r.permitted?"true":"false")<<",\"identity\":"<<(r.identity?"true":"false")<<",\"volleyIdBefore\":"<<r.id<<",\"volleyPointerBefore\":"<<r.pointer<<",\"definition\":"<<r.definition<<",\"projectileConfig\":"<<r.projectileConfig<<",\"indexAfter\":"<<r.index<<",\"countAfter\":"<<r.count<<'}';}}
    o<<"]}";o.close();MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*){
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(module,dll))return 0;
    auto directory=dll.parent_path();
    std::ifstream input(directory/(L"weapon-gate-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);input.read(reinterpret_cast<char*>(&request),sizeof request);
    FILETIME creation,exit,kernel,user;ULARGE_INTEGER when{};
    if(!input||input.peek()!=std::char_traits<char>::eof()||std::memcmp(request.magic,"OWGATE02",8)||request.version!=2||request.size!=104||request.pid!=GetCurrentProcessId()||request.reserved||request.flags!=0x408001||!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user))return 0;
    when.LowPart=creation.dwLowDateTime;when.HighPart=creation.dwHighDateTime;if(request.creation!=when.QuadPart)return 0;
    base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    if((request.state0&&ptr(request.state0)!=base+0x15d2450)||(request.state1&&ptr(request.state1)!=base+0x15d2450)||!request.entryPointer||ptr(request.entryPointer)!=request.entryOriginal)return 0;
    auto vt=base+0x15d2450;
    if(ptr(vt+0x110)!=base+0xd44b50||ptr(vt+0x120)!=base+0xd44d60||ptr(vt+0x270)!=base+0xd456c0)return 0;
    HANDLE halt=CreateEventW(nullptr,TRUE,FALSE,(L"Local\\OWMCWeaponGateStop_"+std::to_wstring(GetCurrentProcessId())).c_str());if(!halt)return 0;
    if(!install()){++failures;stop();report(directory);CloseHandle(halt);return 0;}
    for(unsigned i=0;i<28800&&active;i++){if(WaitForSingleObject(halt,1000)!=WAIT_TIMEOUT)break;if(!identity()){++failures;break;}report(directory);}
    stop();report(directory);CloseHandle(halt);return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_WeaponGateTestAttach(uintptr_t instance,uintptr_t state0,uintptr_t state1){
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-weapon-gate-lifecycle-test.exe"||original)return FALSE;
    fixture=true;request.instance=instance;request.state0=state0;request.state1=state1;request.flags=0x408001;return install();
}
extern "C" __declspec(dllexport) BOOL OWMC_WeaponGateTestStop(){if(!fixture)return FALSE;stop();return restored&&beginCalls==1&&updateCalls==1&&shotCalls==1&&flagScopes==1&&!failures;}
extern "C" __declspec(dllexport) BOOL OWMC_WeaponGateTestLazy(uintptr_t instance,void** table,void** callback){
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-weapon-gate-lifecycle-test.exe"||original)return FALSE;
    fixture=true;fixtureTable=table;request.instance=instance;request.flags=0x408001;request.entryPointer=reinterpret_cast<uintptr_t>(callback);request.entryOriginal=reinterpret_cast<uintptr_t>(*callback);return install();
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void*){if(reason==DLL_PROCESS_ATTACH){module=instance;DisableThreadLibraryCalls(instance);HANDLE thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread)CloseHandle(thread);}return TRUE;}
