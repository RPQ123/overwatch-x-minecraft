#include "native_client_paths.hpp"
#include <windows.h>
#include <array>
#include <atomic>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <vector>
#include "math.hpp"
#include "movement_types.hpp"

namespace {
using Tick=uintptr_t(WINAPI*)(void*,UINT);using After=void(WINAPI*)(void*);
HMODULE moduleHandle;void* hooked=nullptr;void **original=nullptr,**copy=nullptr;
void* character=nullptr;void **characterOriginal=nullptr,**characterCopy=nullptr;
std::atomic<bool> active{false};std::atomic<unsigned> calls{0};
using Pose=MotionPose;
bool(*fakeReader)(MotionPose&)=nullptr;
struct Row { unsigned stage,commandFrame;ULONGLONG clock;Pose pose; };
std::array<Row,32768> rows;size_t written=0;std::mutex rowMutex;
Pose previous{};bool havePrevious=false;ULONGLONG lastChange=0,lastHeartbeat=0;
template<class T> bool read(uintptr_t address,T& value) {
    SIZE_T count=0;return address>=0x10000&&address<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&count)&&count==sizeof(value);
}
uintptr_t pointer(uintptr_t address) { uintptr_t result=0;return read(address,result)?result:0; }
uintptr_t entity(uintptr_t admin,unsigned id) {
    struct Slot { uintptr_t intermediate;int occupied,pad; };std::array<Slot,4096> table{};
    if(!read(pointer(admin+0x10),table)) return 0;
    for(const auto& slot:table) if(slot.occupied&&slot.intermediate) {
        struct Entry { unsigned id,pad;uintptr_t entity; } entry{};
        if(read(slot.intermediate,entry)&&entry.id==id) return entry.entity;
    }return 0;
}
uintptr_t component(uintptr_t owner,unsigned char wanted) {
    struct List { uintptr_t items;int count,capacity; } list{};
    if(!read(owner+0x50,list)||list.count<1||list.count>256||list.capacity<list.count||list.capacity>256) return 0;
    for(int i=0;i<list.count-1;i++) {
        uintptr_t item=pointer(list.items+i*8);unsigned char id=0;
        if(read(item+0x10,id)&&id==wanted&&pointer(item+8)==owner) return item;
    }return 0;
}
bool finite(Vec3 p) { return std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z)&&std::abs(p.x)<1e6&&std::abs(p.y)<1e6&&std::abs(p.z)<1e6; }
bool pose(Pose& result) {
    if(fakeReader) return fakeReader(result);
    uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointer(base+0x17b7f90);unsigned localId=0,modelId=0;
    if(!read(admin+0x220,localId)) return false;
    uintptr_t controller=entity(admin,localId),reference=component(controller,0x20);
    if(!read(reference+0x94,modelId)) return false;
    uintptr_t model=entity(admin,modelId),mover=component(model,0x15),local=component(controller,0x2f),scene=component(model,1);
    return mover&&local&&scene&&read(mover+0xa50+0x220,result.foot)&&read(scene+0x60,result.scene)&&read(local+0x1500,result.eye)
        &&read(mover+0x7e0+0x220,result.state1Foot)&&read(mover+0xa50+0x230,result.delta)
        &&read(mover+0xa50+0x250,result.gravity)&&read(local+0x1510,result.copiedEye)
        &&read(mover+0x7e0+0x1a0,result.state1Tick)&&read(mover+0xa50+0x1a0,result.state2Tick)&&read(mover+0xa50+0x198,result.flags)
        &&finite(result.foot)&&finite(result.scene)&&finite(result.eye)&&pointer(base+0x17b7f90)==admin;
}
void record(unsigned stage,unsigned cf) {
    if(!active) return;Pose value{};if(!pose(value)) return;
    std::lock_guard<std::mutex> guard(rowMutex);
    const auto now=GetTickCount64();
    auto different=[](Vec3 a,Vec3 b){return std::abs(a.x-b.x)>.00001f||std::abs(a.y-b.y)>.00001f||std::abs(a.z-b.z)>.00001f;};
    if(!havePrevious||different(value.foot,previous.foot)||different(value.scene,previous.scene)
       ||different(value.eye,previous.eye)||different(value.state1Foot,previous.state1Foot)
       ||different(value.delta,previous.delta)||different(value.gravity,previous.gravity)||different(value.copiedEye,previous.copiedEye)) lastChange=now;
    previous=value;havePrevious=true;
    // Retain all stages near motion, but idle time cannot erase a short test.
    if(fakeReader||now-lastChange<1000||now-lastHeartbeat>=1000) {
        rows[written++%rows.size()]={stage,cf,now,value};lastHeartbeat=now;
    }
}
uintptr_t WINAPI tick(void* object,UINT cf) {
    record(0,cf);auto result=reinterpret_cast<Tick>(original[0])(object,cf);record(1,cf);++calls;return result;
}
void WINAPI after(void* object) {
    record(2,0);reinterpret_cast<After>(original[2])(object);record(3,0);
}
uintptr_t WINAPI characterTick(void* object,UINT cf) {
    record(4,cf);auto result=reinterpret_cast<Tick>(characterOriginal[0])(object,cf);record(5,cf);return result;
}
void stop() {
    active=false;uintptr_t current=0;
    if(hooked&&read(reinterpret_cast<uintptr_t>(hooked),current)&&current==reinterpret_cast<uintptr_t>(copy))
        InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(hooked),original,copy);
    if(character&&read(reinterpret_cast<uintptr_t>(character),current)&&current==reinterpret_cast<uintptr_t>(characterCopy))
        InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(character),characterOriginal,characterCopy);
    // Code/table stays resident until normal exit for callbacks already in flight.
}
void writeReport(const std::filesystem::path& directory,bool stopped) {
    {std::ofstream status(directory/(L"motion-"+std::to_wstring(GetCurrentProcessId())+L".json"));
    status<<"{\"pid\":"<<GetCurrentProcessId()<<",\"active\":"<<(active?"true":"false")<<",\"calls\":"<<calls<<",\"restored\":"<<(stopped?"true":"false")<<",\"playerWrites\":false}";}
    std::vector<Row> saved;size_t total;
    {std::lock_guard<std::mutex> guard(rowMutex);total=written;
     size_t begin=written>rows.size()?written-rows.size():0;
     for(size_t i=begin;i<written;i++) saved.push_back(rows[i%rows.size()]);}
    const auto destination=directory/(L"motion-samples-"+std::to_wstring(GetCurrentProcessId())+L".json");
    auto temporary=destination;temporary+=L".tmp";std::ofstream out(temporary);
    out<<std::setprecision(9)<<"{\"playerWrites\":false,\"totalSamples\":"<<total<<",\"samples\":[";
    for(size_t i=0;i<saved.size();i++) {
        if(i) out<<',';const auto& r=saved[i];
        out<<"{\"stage\":"<<r.stage<<",\"commandFrame\":"<<r.commandFrame<<",\"clock\":"<<r.clock
           <<",\"stateTicks\":["<<r.pose.state1Tick<<','<<r.pose.state2Tick<<"],\"flags\":"<<r.pose.flags;
        auto vec=[&](const char* name,Vec3 v){out<<",\""<<name<<"\":["<<v.x<<','<<v.y<<','<<v.z<<']';};
        vec("foot",r.pose.foot);vec("scene",r.pose.scene);vec("eye",r.pose.eye);
        vec("state1Foot",r.pose.state1Foot);vec("delta",r.pose.delta);vec("gravity",r.pose.gravity);vec("copiedEye",r.pose.copiedEye);out<<'}';
    }out<<"]}";out.close();MoveFileExW(temporary.c_str(),destination.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dll))return 0;
    auto dir=dll.parent_path();
    uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointer(base+0x17b7f90);
    struct List { uintptr_t items;int count,capacity; } list{};
    if(!read(admin+0xf0,list)||list.count<1||list.count>32||list.capacity<list.count||list.capacity>32) return 0;
    for(int i=0;i<list.count;i++) {auto object=pointer(list.items+i*8);
        if(pointer(object)==base+0x15c4e28) hooked=reinterpret_cast<void*>(object);
        if(pointer(object)==base+0x15c1c30) character=reinterpret_cast<void*>(object);
    }
    if(!hooked||!character) return 0;
    original=*reinterpret_cast<void***>(hooked);
    if(original[0]!=reinterpret_cast<void*>(base+0xca0960)||original[1]!=reinterpret_cast<void*>(base+0xca0800)||original[2]!=reinterpret_cast<void*>(base+0xca09c0)) return 0;
    characterOriginal=*reinterpret_cast<void***>(character);
    if(characterOriginal[0]!=reinterpret_cast<void*>(base+0xc22c30)||characterOriginal[1]!=reinterpret_cast<void*>(base+0x5a0c20)||characterOriginal[2]!=reinterpret_cast<void*>(base+0x5a0c20)) return 0;
    copy=new void*[3]{reinterpret_cast<void*>(tick),original[1],reinterpret_cast<void*>(after)};
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(hooked),copy,original)!=original) return 0;
    characterCopy=new void*[3]{reinterpret_cast<void*>(characterTick),characterOriginal[1],characterOriginal[2]};
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(character),characterCopy,characterOriginal)!=characterOriginal) {stop();return 0;}
    active=true;
    std::wstring name=L"Local\\OWMCMotionStop_"+std::to_wstring(GetCurrentProcessId());HANDLE halt=CreateEventW(nullptr,TRUE,FALSE,name.c_str());
    if(!halt) {stop();return 0;}
    for(unsigned iteration=0;iteration<1200;iteration++) {
        if(WaitForSingleObject(halt,500)!=WAIT_TIMEOUT) break;
        if(iteration%4==0) writeReport(dir,false);
    }
    stop();writeReport(dir,true);CloseHandle(halt);return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_MotionTestAttach(void* object,bool(*reader)(MotionPose&)) {
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);
    if(std::filesystem::path(exe).filename()!=L"owmc-movement-test.exe"||hooked||!object||!reader) return FALSE;
    fakeReader=reader;hooked=object;original=*reinterpret_cast<void***>(object);
    copy=new void*[3]{reinterpret_cast<void*>(tick),original[1],reinterpret_cast<void*>(after)};
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(object),copy,original)!=original) return FALSE;
    active=true;return TRUE;
}
extern "C" __declspec(dllexport) BOOL OWMC_MotionTestVerify() {
    if(!fakeReader||written!=8) return FALSE;
    stop();return rows[0].pose.foot.x==0&&rows[1].pose.foot.x==1&&rows[1].pose.eye.x==0
        &&rows[3].pose.eye.x==1&&rows[5].pose.foot.x==2&&rows[7].pose.eye.x==2;
}
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH) {moduleHandle=module;DisableThreadLibraryCalls(module);HANDLE thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread) CloseHandle(thread);}return TRUE;
}
