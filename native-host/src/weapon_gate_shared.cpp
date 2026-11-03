// Shared native Volley table: scope each call to the current local supported
// hero. No state-object vtable is retained across native hero destruction.
#include "native_client_paths.hpp"
#include "weapon_gate.hpp"
#include "native_local_hero.hpp"
#include <atomic>
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <vector>

namespace {
struct Request{char magic[8];uint32_t version,size,pid,reserved;uint64_t creation,admin,localId,modelId,hero,script,entryPointer,entryOriginal,finishPointer,finishOriginal,tickPointer,tickOriginal,skillMask;};
static_assert(sizeof(Request)==128);
using Callback=uintptr_t(WINAPI*)(void*);
using Entry=void(WINAPI*)(void*,void*,void*);
Entry entryOriginal=nullptr,finishOriginal=nullptr;
using Tick=intptr_t(WINAPI*)(void*,void*);
Tick tickOriginal=nullptr;
std::atomic<unsigned> skillTickScopes{0};
std::atomic<uint64_t> skillMask{0};std::atomic<unsigned> skillScopes{0};
HMODULE module;Request request{};uintptr_t base=0;bool fixture=false;
void** table=nullptr;std::array<Callback,3> originals{};
constexpr std::array<unsigned,3> offsets{0x110/8,0x120/8,0x270/8};
std::atomic<bool> active{false},restored{false};
std::atomic<unsigned> failures{0},inFlight{0},beginCalls{0},updateCalls{0},shotCalls{0},flagScopes{0},filtered{0},dropped{0},rebindings{0};
std::atomic<DWORD> callbackThread{0};passthrough::NativeLocalHero local;
std::atomic<uint64_t> currentHero{0},currentModel{0};
struct Row{uint64_t clock,hero,script,state;uint32_t operation,before,after;int index;};
std::mutex rowLock;std::vector<Row> rows,tankRefusedRows;
std::mutex identityLock;
bool read(uintptr_t p,void* data,size_t size){SIZE_T n=0;return p>=0x10000&&p<0x7fffffffffffULL&&size<=65536&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),data,size,&n)&&n==size;}
template<class T> bool get(uintptr_t p,T& value){return read(p,&value,sizeof value);}
uintptr_t ptr(uintptr_t p){uintptr_t result=0;get(p,result);return result;}
bool refresh(){
    if(!fixture&&ptr(base+0x17b7f90)!=request.admin)return false;
    auto previous=local.modelId;
    if(!local.refresh(request.admin,read))return false;
    if(previous&&previous!=local.modelId)++rebindings;
    currentHero=local.hero;currentModel=local.modelId;return true;
}
uintptr_t dispatch(void* object,unsigned operation){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    if(!active)return originals[operation](object);
    uintptr_t state=reinterpret_cast<uintptr_t>(object),instance=ptr(state+0x78);uint64_t resource=0;
    if(!get(instance+0x150,resource)){++filtered;return originals[operation](object);}
    passthrough::NativeLocalHero target;bool ready=false;
    {std::lock_guard<std::mutex> lock(identityLock);ready=refresh();if(ready)target=local;}
    if(!ready){++filtered;return originals[operation](object);}
    auto component=ptr(ptr(instance+0x10)+0x450),owner=ptr(component+8);
    uint32_t flags=0;int index=-1;
    if((resource>>48)!=0x0580||owner!=target.model||ptr(owner+0x28)!=request.admin||!get(instance+0x258,flags)
       ||!get(state+0x70,index)||index<0||index>4096){++filtered;return originals[operation](object);}
    // A different entity's first callback must not choose the local hero's
    // owner thread. Bind only after native ownership has been established.
    DWORD expected=0;callbackThread.compare_exchange_strong(expected,GetCurrentThreadId());
    if(callbackThread!=GetCurrentThreadId()){++filtered;return originals[operation](object);}
    // Winston's measured additional bit is preserved. No other flag set gains
    // native execution authority merely by resembling a supported weapon.
    // The original shared table dispatch establishes the Volley class; the
    // actual script->component->current-model ownership establishes locality.
    // Unknown execution-bit patterns remain untouched rather than disabling
    // all other heroes' already-established callbacks.
    bool flash=target.hero==0x02e0000000000042ULL&&resource==0x05800000000001e9ULL;
    bool measured=passthrough::measuredWeaponGateFlags(flags&~0x800000u&~(flash?2u:0u));
    // Tank's observed bit2 is admitted only for its actual node25 definition,
    // original shared class and current native owner. Keep unknown flags and
    // every other graph on the existing policy; do not widen the general mask.
    bool tank=!measured&&passthrough::measuredBastionTankVolleyScope(target.hero,resource,state,instance,
        target.model,request.admin,reinterpret_cast<uintptr_t>(table),flags,
        [](uintptr_t at,auto& value){return get(at,value);});
    if(!measured&&!tank){
        if(target.hero==0x02e0000000000015ULL&&resource==0x058000000000024fULL){
            std::lock_guard<std::mutex> lock(rowLock);
            if(tankRefusedRows.size()<32)tankRefusedRows.push_back(Row{GetTickCount64(),target.hero,resource,state,operation,flags,flags,index});
        }
        ++filtered;return originals[operation](object);
    }
    if(operation==0)++beginCalls;else if(operation==1)++updateCalls;else ++shotCalls;
    if(!(flags&8))++flagScopes;
    auto result=passthrough::withWeaponGate(reinterpret_cast<volatile LONG*>(instance+0x258),[&]{return originals[operation](object);});
    uint32_t after=0;get(instance+0x258,after);
    Row row{GetTickCount64(),target.hero,resource,state,operation,flags,after,index};
    {std::lock_guard<std::mutex> lock(rowLock);if(rows.size()<2048)rows.push_back(row);else ++dropped;}
    return result;
}
uintptr_t WINAPI begin(void* object){return dispatch(object,0);}
uintptr_t WINAPI update(void* object){return dispatch(object,1);}
uintptr_t WINAPI shot(void* object){return dispatch(object,2);}
void skillDispatch(void* sync,void* scriptObject,void* stateObject,bool finish){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    auto original=finish?finishOriginal:entryOriginal;
    if(!active||!(skillMask.load()&1)){original(sync,scriptObject,stateObject);return;}
    uintptr_t script=reinterpret_cast<uintptr_t>(scriptObject),state=reinterpret_cast<uintptr_t>(stateObject);uint64_t resource=0;uint32_t flags=0;
    passthrough::NativeLocalHero target;bool ready=false;
    {std::lock_guard<std::mutex> lock(identityLock);ready=refresh();if(ready)target=local;}
    auto component=ptr(ptr(script+0x10)+0x450),owner=ptr(component+8);
    int index=-1;
    if(!ready||target.hero!=0x02e0000000000002ULL||owner!=target.model||ptr(owner+0x28)!=request.admin||ptr(state+0x78)!=script
       ||!get(script+0x150,resource)||resource!=0x0580000000000020ULL||!get(script+0x258,flags)
       ||!passthrough::measuredWeaponGateFlags(flags&~2u)||!get(state+0x70,index)||index<0||index>4096){original(sync,scriptObject,stateObject);return;}
    DWORD expected=0;callbackThread.compare_exchange_strong(expected,GetCurrentThreadId());
    if(callbackThread!=GetCurrentThreadId()){original(sync,scriptObject,stateObject);return;}
    ++skillScopes;
    passthrough::withWeaponGate(reinterpret_cast<volatile LONG*>(script+0x258),[&]{original(sync,scriptObject,stateObject);});
    uint32_t after=0;get(script+0x258,after);
    Row row{GetTickCount64(),target.hero,resource,state,finish?4u:3u,flags,after,index};
    {std::lock_guard<std::mutex> lock(rowLock);if(rows.size()<2048)rows.push_back(row);else ++dropped;}
}
void WINAPI skillEntry(void* sync,void* script,void* state){skillDispatch(sync,script,state,false);}
void WINAPI skillFinish(void* sync,void* script,void* state){skillDispatch(sync,script,state,true);}
intptr_t WINAPI skillTick(void* scriptObject,void* notification){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    if(!active||!(skillMask.load()&2))return tickOriginal(scriptObject,notification);
    uintptr_t script=reinterpret_cast<uintptr_t>(scriptObject);uint64_t resource=0;uint32_t flags=0;
    passthrough::NativeLocalHero target;bool ready=false;
    {std::lock_guard<std::mutex> lock(identityLock);ready=refresh();if(ready)target=local;}
    auto owner=ptr(ptr(ptr(script+0x10)+0x450)+8);
    if(!ready||target.hero!=0x02e0000000000002ULL||owner!=target.model||ptr(owner+0x28)!=request.admin
       ||!get(script+0x150,resource)||resource!=0x0580000000000020ULL||!get(script+0x258,flags)
       ||!passthrough::measuredWeaponGateFlags(flags&~2u))return tickOriginal(scriptObject,notification);
    DWORD expected=0;callbackThread.compare_exchange_strong(expected,GetCurrentThreadId());
    if(callbackThread!=GetCurrentThreadId())return tickOriginal(scriptObject,notification);
    ++skillTickScopes;
    return passthrough::withWeaponGate(reinterpret_cast<volatile LONG*>(script+0x258),[&]{return tickOriginal(scriptObject,notification);});
}
template<class Function> bool exchangeEntry(uintptr_t address,Function before,Function after){
    if(!address)return true;
    auto previous=InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(address),reinterpret_cast<void*>(after),reinterpret_cast<void*>(before));
    return previous==reinterpret_cast<void*>(before)||previous==reinterpret_cast<void*>(after);
}
const std::array<Callback,3> replacements{begin,update,shot};
bool exchange(unsigned slot,Callback before,Callback after){
    DWORD protection=0;auto address=table+offsets[slot];
    if(!VirtualProtect(address,sizeof(void*),PAGE_READWRITE,&protection))return false;
    auto previous=InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(address),reinterpret_cast<void*>(after),reinterpret_cast<void*>(before));
    DWORD ignored=0;bool protectedAgain=VirtualProtect(address,sizeof(void*),protection,&ignored)!=FALSE;
    return protectedAgain&&(previous==reinterpret_cast<void*>(before)||previous==reinterpret_cast<void*>(after));
}
bool install(){
    if(!refresh()||local.hero!=request.hero||local.localId!=request.localId||local.modelId!=request.modelId||!passthrough::heroWeapon(request.hero,request.script))return false;
    for(unsigned i=0;i<3;i++)originals[i]=reinterpret_cast<Callback>(table[offsets[i]]);
    rows.reserve(2048);active=true;
    for(unsigned i=0;i<3;i++)if(!exchange(i,originals[i],replacements[i])){active=false;return false;}
    skillMask=request.skillMask;entryOriginal=reinterpret_cast<Entry>(request.entryOriginal);finishOriginal=reinterpret_cast<Entry>(request.finishOriginal);
    tickOriginal=reinterpret_cast<Tick>(request.tickOriginal);
    if(!exchangeEntry(request.entryPointer,entryOriginal,skillEntry)||!exchangeEntry(request.finishPointer,finishOriginal,skillFinish)){active=false;return false;}
    if(request.tickPointer&&!exchangeEntry(request.tickPointer,tickOriginal,skillTick)){active=false;return false;}
    return true;
}
void stop(){
    active=false;bool ok=true;
    for(unsigned i=0;i<3;i++)if(originals[i])ok=exchange(i,replacements[i],originals[i])&&ok;
    if(entryOriginal)ok=exchangeEntry(request.entryPointer,skillEntry,entryOriginal)&&ok;
    if(finishOriginal)ok=exchangeEntry(request.finishPointer,skillFinish,finishOriginal)&&ok;
    if(tickOriginal)ok=exchangeEntry(request.tickPointer,skillTick,tickOriginal)&&ok;
    for(unsigned i=0;i<200&&inFlight;i++)Sleep(10);
    restored=ok&&!inFlight;
}
void report(const std::filesystem::path& directory){
    auto path=directory/(L"weapon-gate-"+std::to_wstring(GetCurrentProcessId())+L".json"),temp=path;temp+=L".tmp";
    std::ofstream o(temp);o<<"{\"pid\":"<<GetCurrentProcessId()<<",\"probeVersion\":11,\"enabled\":"<<(active?"true":"false")<<",\"restored\":"<<(restored?"true":"false")
      <<",\"failures\":"<<failures<<",\"beginCalls\":"<<beginCalls<<",\"updateCalls\":"<<updateCalls<<",\"shotCalls\":"<<shotCalls<<",\"flagScopes\":"<<flagScopes
      <<",\"filtered\":"<<filtered<<",\"rebindings\":"<<rebindings<<",\"hero\":"<<currentHero<<",\"modelId\":"<<currentModel<<",\"callbackThread\":"<<callbackThread
      <<",\"dropped\":"<<dropped<<",\"skillMask\":"<<skillMask<<",\"skillScopes\":"<<skillScopes<<",\"skillEntryInstalled\":"<<(entryOriginal?"true":"false")<<",\"skillTickScopes\":"<<skillTickScopes<<",\"skillTickInstalled\":"<<(tickOriginal?"true":"false")<<",\"projectileEmissionVerified\":false,\"mcDamageSent\":false,\"rows\":[";
    {std::lock_guard<std::mutex> lock(rowLock);for(size_t i=0;i<rows.size();i++){if(i)o<<',';auto r=rows[i];o<<"{\"clock\":"<<r.clock<<",\"hero\":"<<r.hero<<",\"script\":"<<r.script<<",\"state\":"<<r.state<<",\"operation\":"<<r.operation<<",\"before\":"<<r.before<<",\"after\":"<<r.after<<",\"index\":"<<r.index<<'}';}}
    o<<"],\"tankRefusedRows\":[";
    {std::lock_guard<std::mutex> lock(rowLock);for(size_t i=0;i<tankRefusedRows.size();i++){if(i)o<<',';auto r=tankRefusedRows[i];o<<"{\"clock\":"<<r.clock<<",\"hero\":"<<r.hero<<",\"script\":"<<r.script<<",\"state\":"<<r.state<<",\"operation\":"<<r.operation<<",\"before\":"<<r.before<<",\"index\":"<<r.index<<'}';}}
    o<<"]}";o.close();MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*){
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(module,dll))return 0;
    auto directory=dll.parent_path();
    std::ifstream input(directory/(L"weapon-gate-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);input.read(reinterpret_cast<char*>(&request),sizeof request);
    FILETIME creation,exit,kernel,user;ULARGE_INTEGER when{};
    if(!input||input.peek()!=std::char_traits<char>::eof()||std::memcmp(request.magic,"OWGATE05",8)||request.version!=5||request.size!=128||request.pid!=GetCurrentProcessId()||request.reserved||request.skillMask&~3ULL||!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user))return 0;
    when.LowPart=creation.dwLowDateTime;when.HighPart=creation.dwHighDateTime;if(request.creation!=when.QuadPart)return 0;
    base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));table=reinterpret_cast<void**>(base+0x15d2450);
    if(bool(request.entryPointer)!=bool(request.entryOriginal)||bool(request.finishPointer)!=bool(request.finishOriginal)||bool(request.entryPointer)!=bool(request.finishPointer)
       ||(request.entryPointer&&ptr(request.entryPointer)!=request.entryOriginal)||(request.finishPointer&&ptr(request.finishPointer)!=request.finishOriginal))return 0;
    if(bool(request.tickPointer)!=bool(request.tickOriginal)||(request.tickPointer&&ptr(request.tickPointer)!=request.tickOriginal))return 0;
    const std::array<uintptr_t,3> rvas{0xd44b50,0xd44d60,0xd456c0};for(unsigned i=0;i<3;i++)if(ptr(reinterpret_cast<uintptr_t>(table+offsets[i]))!=base+rvas[i])return 0;
    HANDLE halt=CreateEventW(nullptr,TRUE,FALSE,(L"Local\\OWMCWeaponGateStop_"+std::to_wstring(GetCurrentProcessId())).c_str());if(!halt)return 0;
    if(!install()){++failures;stop();report(directory);CloseHandle(halt);return 0;}
    for(unsigned i=0;i<28800&&active;i++){
        if(WaitForSingleObject(halt,1000)!=WAIT_TIMEOUT)break;
        uint64_t identity=0,mask=0;std::ifstream control(directory/(L"native-skill-authority-"+std::to_wstring(GetCurrentProcessId())+L".txt"));
        skillMask=(control>>identity>>mask)&&identity==request.creation&&!(mask&~3ULL)&&(!(mask&2)||tickOriginal)&&(!(mask&1)||(entryOriginal&&finishOriginal))?mask:request.skillMask;report(directory);
    }
    stop();report(directory);CloseHandle(halt);return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_SharedGateTestAttach(uintptr_t admin,void** input){
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-weapon-gate-shared-test.exe"||table)return FALSE;
    fixture=true;request.admin=admin;table=input;
    if(!refresh())return FALSE;
    request.hero=local.hero;request.localId=local.localId;request.modelId=local.modelId;
    for(auto p:passthrough::heroWeapons)if(p.hero==local.hero)request.script=p.script;
    return install();
}
extern "C" __declspec(dllexport) BOOL OWMC_SharedGateTestStop(){if(!fixture)return FALSE;stop();return restored&&!failures;}
extern "C" __declspec(dllexport) BOOL OWMC_SharedGateTestEntries(void** entry,void** finish){
    if(!fixture||!active||request.entryPointer||!entry||!finish||!*entry||!*finish)return FALSE;
    request.entryPointer=reinterpret_cast<uintptr_t>(entry);request.entryOriginal=reinterpret_cast<uintptr_t>(*entry);
    request.finishPointer=reinterpret_cast<uintptr_t>(finish);request.finishOriginal=reinterpret_cast<uintptr_t>(*finish);
    entryOriginal=reinterpret_cast<Entry>(*entry);finishOriginal=reinterpret_cast<Entry>(*finish);skillMask=1;
    return exchangeEntry(request.entryPointer,entryOriginal,skillEntry)&&exchangeEntry(request.finishPointer,finishOriginal,skillFinish);
}
extern "C" __declspec(dllexport) BOOL OWMC_SharedGateTestTick(void** tick){
    if(!fixture||!active||request.tickPointer||!tick||!*tick)return FALSE;
    request.tickPointer=reinterpret_cast<uintptr_t>(tick);request.tickOriginal=reinterpret_cast<uintptr_t>(*tick);tickOriginal=reinterpret_cast<Tick>(*tick);
    return exchangeEntry(request.tickPointer,tickOriginal,skillTick);
}
extern "C" __declspec(dllexport) BOOL OWMC_SharedGateTestSkillMask(uint64_t mask){if(!fixture||mask&~3ULL)return FALSE;skillMask=mask;return TRUE;}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void*){if(reason==DLL_PROCESS_ATTACH){module=instance;DisableThreadLibraryCalls(instance);HANDLE thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread)CloseHandle(thread);}return TRUE;}
