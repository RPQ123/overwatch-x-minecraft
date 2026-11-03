#include "native_client_paths.hpp"
#include "native_emission.hpp"
#include "native_beam_phase.hpp"
#include "native_local_hero.hpp"
#include "native_armory.hpp"
#include <windows.h>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <vector>
#include <map>

using namespace passthrough;
namespace {
struct Request{char magic[8];uint32_t version,size,pid,reserved;uint64_t creation,admin,localId,modelId,model,hostGeneration,resource,script,bag,damageValue,damageRid;uint32_t bucket,reserved2;uint64_t hero,secondaryDamageValue,ammoValue,rangeValue,angleValue,periodValue;};
static_assert(sizeof(Request)==168);
using Factory=uintptr_t(WINAPI*)(uintptr_t,uintptr_t,uintptr_t,uintptr_t);
using Create=int(WINAPI*)(void*,void*,void**);using Toggle=int(WINAPI*)(void*);
HMODULE module;Request request{};uintptr_t base=0,target=0;Factory original=nullptr;Toggle disable=nullptr;
uint64_t epoch=0;
std::mutex bindingMutex;NativeLocalHero local;
std::atomic<bool> combatReady{false};std::atomic<unsigned> rebindings{0};
ArmoryHeader armory{};std::vector<ArmorySpec> armorySpecs;std::atomic<unsigned> armoryRebindings{0},armoryAccepted{0};
std::atomic<unsigned> nativeDamageEvaluations{0};
bool fixture=false,installed=false;std::atomic<bool> active{false},restored{false};
std::atomic<unsigned> calls{0},accepted{0},filtered{0},refused{0},failures{0},inFlight{0};
const char* failureStage="";
EmissionJournal<512> journal;
const unsigned char* body=nullptr;HANDLE bodyMapping=nullptr;
std::array<unsigned char,24> before{};
uintptr_t factoryTarget=0;Factory factoryOriginal=nullptr;bool factoryInstalled=false;
std::array<unsigned char,24> factoryBefore{};
struct FactoryRow{uint64_t wall,volley,resource,result,hero;uint32_t owner,tick,shot,pellet,status,type;Vec3 position,direction;float speed=0,lifetime=0,range=0,evaluatedDamage=0;};
// Diagnostic observations must not grow the transport JSON beyond the guest's
// bounded524KiB decoder. This is separate from the acknowledged attack journal.
std::deque<FactoryRow> factoryRows;std::atomic<unsigned> factoryCalls{0},factoryDropped{0};
// Bounded private calibration snapshots of the actual resolved native config.
// They never create/admit a shot and remain separate from the attack journal.
struct FactoryConfigSnapshot {
    std::array<uint8_t,0x110> config{};std::array<uint8_t,16> flowHeader{};std::vector<uint8_t> flowValues;
    std::map<unsigned,std::vector<uint8_t>> nested;
};
std::map<uint64_t,FactoryConfigSnapshot> factoryConfigs;
std::atomic<bool> captureFactoryConfig{false};
using BeamCallback=uintptr_t(WINAPI*)(void*);
void** beamTable=nullptr;std::array<BeamCallback,2> beamOriginal{};
NativeBeamPhase beamPhase;GuestBody beamWorld{};
const unsigned char* poseBytes=nullptr;HANDLE poseMapping=nullptr;
std::atomic<unsigned> beamBegins{0},beamEnds{0},beamIntervals{0},beamRejected{0};
template<class T> bool read(uintptr_t p,T& v){SIZE_T n=0;return p>=0x10000&&p<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&v,sizeof v,&n)&&n==sizeof v;}
uintptr_t ptr(uintptr_t p){uintptr_t v=0;return read(p,v)?v:0;}
uint64_t nowMs(){FILETIME f;GetSystemTimeAsFileTime(&f);ULARGE_INTEGER t;t.LowPart=f.dwLowDateTime;t.HighPart=f.dwHighDateTime;return(t.QuadPart-116444736000000000ULL)/10000;}
uintptr_t component(uintptr_t owner,unsigned wanted){
    struct List{uintptr_t items;int count,capacity;} l{};
    if(!read(owner+0x50,l)||l.count<1||l.count>l.capacity||l.capacity>256)return 0;
    for(int i=0;i<l.count-1;i++){auto p=ptr(l.items+i*8);unsigned char id=0;if(read(p+0x10,id)&&id==wanted&&ptr(p+8)==owner)return p;}return 0;
}
bool refreshHero(){
    if(!fixture&&ptr(base+0x17b7f90)!=request.admin)return false;
    return local.refresh(request.admin,[](uintptr_t p,void* out,size_t size){SIZE_T n=0;return p>=0x10000&&p<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),out,size,&n)&&n==size;});
}
bool matches(const Request& binding){
    return local.hero==binding.hero&&local.localId==binding.localId&&local.modelId==binding.modelId&&local.model==binding.model;
}
bool identity(){return refreshHero()&&matches(request);}
bool numeric(uintptr_t address,float& result){
    struct Value{uint64_t raw;uint32_t reserved,type;} v{};
    if(ptr(address)!=base+0x1608248||!read(address+0xa0,v))return false;
    if(v.type==2)result=float(int32_t(v.raw));else if(v.type==3){auto bits=uint32_t(v.raw);std::memcpy(&result,&bits,4);}else return false;
    return std::isfinite(result);
}
bool literal(uintptr_t address,int expected){int value=0;return ptr(address)==base+0x1565f40&&read(address+0x10,value)&&value==expected;}
bool literalFloat(uintptr_t address,float expected){float value=0;return ptr(address)==base+0x1558ba8&&read(address+0x10,value)&&value==expected;}
bool damage(const Request& binding,float& value){
    if(fixture){value=binding.hero==0x02e0000000000042ULL?70:binding.hero==0x02e0000000000008ULL?40:35;return true;}
    uint64_t resource=0;
    if(binding.bucket>=16||ptr(ptr(ptr(binding.script+0x10)+0x450)+8)!=binding.model||ptr(binding.script+0x98)!=binding.bag||!read(binding.script+0x150,resource)||resource!=(binding.hero==0x02e0000000000029ULL?0x0580000000000304ULL:binding.hero==0x02e0000000000042ULL?0x05800000000001d2ULL:binding.hero==0x02e0000000000008ULL?0x0580000000000023ULL:0x05800000000000feULL))return false;
    if(binding.hero==0x02e0000000000008ULL){
        auto volley=binding.rangeValue,graph=ptr(binding.script+0x160),storage=ptr(graph+0x50);uint64_t flag=0;
        if(!read(graph+0x58,flag)||(flag!=1&&flag!=2))return false;
        auto items=ptr(storage+(flag==1?0:8));uint64_t count=0;
        if(!read(storage+(flag==1?8:0),count)||count<=10||count>4096||ptr(items+10*8)!=volley)return false;
        auto impact=ptr(volley+0x168),explosion=ptr(volley+0x160),rings=ptr(explosion+8);uint64_t ringFlag=0,ringCount=0;
        if(!read(explosion+16,ringFlag)||(ringFlag!=1&&ringFlag!=2)||!read(rings+(ringFlag==1?8:0),ringCount)||ringCount!=2)return false;
        auto ringItems=ptr(rings+(ringFlag==1?0:8));
        if(binding.resource!=0x0400000000000033ULL||ptr(ptr(impact+0x38)+0x38)!=binding.damageValue
           ||ptr(ptr(explosion+0x60)+0x38)!=binding.secondaryDamageValue||ringItems!=binding.damageRid
           ||ptr(ringItems)!=binding.ammoValue||ptr(ringItems+16)!=binding.angleValue||ptr(ringItems+24)!=binding.periodValue
           ||!literal(binding.damageValue,40)||!literal(binding.secondaryDamageValue,80)||!literal(ptr(ringItems+8),1)
           ||!literalFloat(binding.ammoValue,.5f)||!literalFloat(binding.angleValue,2.5f)||!literalFloat(binding.periodValue,.125f))return false;
        value=40;return true;
    }
    if(binding.hero==0x02e0000000000009ULL){
        float radius=0,angle=0,ammo=0;
        if(binding.resource!=0x05800000000000feULL||!literal(binding.damageValue,60)||!literal(binding.secondaryDamageValue,20)||!literal(binding.periodValue,1)
           ||!numeric(binding.rangeValue,radius)||radius!=8||!numeric(binding.angleValue,angle)||angle!=40||!numeric(binding.ammoValue,ammo)||ammo<0||ammo>100)return false;
        value=60;return true;
    }
    if(binding.hero==0x02e0000000000042ULL){
        int a=0,b=0;
        if(binding.resource!=0x04000000000002a7ULL||ptr(binding.damageValue)!=base+0x1565f40||ptr(binding.secondaryDamageValue)!=base+0x1565f40
           ||!read(binding.damageValue+0x10,a)||!read(binding.secondaryDamageValue+0x10,b)||a!=70||b!=a)return false;
        value=float(a);return true;
    }
    struct List{uintptr_t items;int count,capacity;} l{};
    if(!read(binding.bag+0xa0+binding.bucket*0x30,l)||l.count<1||l.count>l.capacity||l.capacity>512)return false;
    bool found=false;
    for(int i=0;i<l.count;i++){std::array<uint64_t,2> pair{};if(!read(l.items+i*16,pair))return false;if(pair[0]==binding.damageRid&&pair[1]==binding.damageValue)found=true;}
    if(!found||ptr(binding.damageValue)!=base+0x1608248)return false;
    struct Value{uint64_t raw;uint32_t reserved,type;} v{};if(!read(binding.damageValue+0xa0,v))return false;
    if(v.type==2)value=float(int32_t(v.raw));else if(v.type==3){auto raw=uint32_t(v.raw);std::memcpy(&value,&raw,4);}else return false;
    return std::isfinite(value)&&value>0&&value<=10000;
}
bool adopt(const Request& candidate){
    if(std::memcmp(candidate.magic,request.magic,8)||candidate.version!=request.version||candidate.size!=request.size
       ||candidate.pid!=request.pid||candidate.creation!=request.creation||candidate.admin!=request.admin
       ||candidate.hostGeneration!=request.hostGeneration||candidate.reserved||candidate.reserved2
       ||!emissionResourceMatches(candidate.hero,candidate.resource)
       ||!refreshHero()||!matches(candidate))return false;
    float amount=0;if(!damage(candidate,amount))return false;
    beamPhase.reset();request.ammoValue=candidate.ammoValue;request.rangeValue=candidate.rangeValue;request.angleValue=candidate.angleValue;request.periodValue=candidate.periodValue;
    request.hero=candidate.hero;request.resource=candidate.resource;request.secondaryDamageValue=candidate.secondaryDamageValue;
    request.localId=candidate.localId;request.modelId=candidate.modelId;request.model=candidate.model;
    request.script=candidate.script;request.bag=candidate.bag;request.damageValue=candidate.damageValue;request.damageRid=candidate.damageRid;request.bucket=candidate.bucket;
    combatReady=true;++rebindings;return true;
}
bool loadRequest(const std::filesystem::path& directory,Request& result){
    auto path=directory/(L"native-emissions-request-"+std::to_wstring(GetCurrentProcessId())+L".bin");
    HANDLE file=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return false;
    LARGE_INTEGER size{};DWORD count=0;
    bool ok=GetFileSizeEx(file,&size)&&size.QuadPart==sizeof result&&ReadFile(file,&result,sizeof result,&count,nullptr)&&count==sizeof result;
    CloseHandle(file);return ok;
}
bool armoryMatches(){return !armorySpecs.empty()&&local.hero==armory.hero&&local.localId==armory.localId&&local.modelId==armory.modelId&&local.model==armory.model;}
bool loadArmory(const std::filesystem::path& directory){
    ArmoryHeader header{};auto path=directory/(L"native-armory-request-"+std::to_wstring(GetCurrentProcessId())+L".bin");
    std::ifstream input(path,std::ios::binary);input.read(reinterpret_cast<char*>(&header),sizeof header);
    if(!input||std::memcmp(header.magic,"OWARM002",8)||header.version!=2||header.pid!=request.pid||header.creation!=request.creation
       ||header.admin!=request.admin||header.hostGeneration!=request.hostGeneration||header.reserved||header.reserved2||header.reserved3
       ||!assaultDefenseHero(header.hero)||header.count<1||header.count>64||header.size!=sizeof header+header.count*sizeof(ArmorySpec)
       ||header.hero!=local.hero||header.modelId!=local.modelId||header.localId!=local.localId||header.model!=local.model)return false;
    std::vector<ArmorySpec> specs(header.count);input.read(reinterpret_cast<char*>(specs.data()),specs.size()*sizeof(ArmorySpec));
    if(!input||input.peek()!=std::char_traits<char>::eof())return false;
    std::set<std::pair<uint64_t,uint32_t>> resources;
    for(const auto& spec:specs){float amount=0;ArmoryBlast blast{};if(!armorySpecBounds(spec)||!resources.insert({spec.resource,spec.volleyKey}).second||!armoryAmount(header,spec,[](uintptr_t at,auto& value){return read(at,value);},amount)
        ||!armoryGravity(spec,[](uintptr_t at,auto& value){return read(at,value);})||!armoryFlash(header,spec,[](uintptr_t at,auto& value){return read(at,value);})
        ||(spec.splash>0&&!armoryBlast(spec,[](uintptr_t at,auto& value){return read(at,value);},blast))
        ||!armoryBastionTank(header,spec,[](uintptr_t at,auto& value){return read(at,value);}))return false;}
    armory=header;armorySpecs=std::move(specs);++armoryRebindings;return true;
}
void synchronize(const std::filesystem::path& directory){
    std::lock_guard<std::mutex> lock(bindingMutex);
    uint64_t calibrationCreation=0;std::ifstream calibration(directory/(L"native-factory-calibration-"+std::to_wstring(GetCurrentProcessId())+L".txt"));
    bool enabled=bool(calibration>>calibrationCreation)&&calibrationCreation==request.creation;
    if(captureFactoryConfig&&!enabled){factoryConfigs.clear();factoryRows.clear();}
    captureFactoryConfig=enabled;
    combatReady=identity();
    if(!combatReady&&(local.hero==0x02e0000000000029ULL||local.hero==0x02e0000000000042ULL||local.hero==0x02e0000000000009ULL||local.hero==0x02e0000000000008ULL)){
        Request candidate{};if(loadRequest(directory,candidate))adopt(candidate);
    }
    if(!armoryMatches())loadArmory(directory);
    combatReady=bool(combatReady)||armoryMatches();
}
bool guest(GuestBody& result){
    if(!body)return false;
    std::array<unsigned char,256> bytes{};
    for(unsigned i=0;i<3;i++){
        uint64_t seq=0;std::memcpy(&seq,body+64,8);if(!seq||(seq&1))continue;
        std::atomic_thread_fence(std::memory_order_seq_cst);std::memcpy(bytes.data(),body,256);std::atomic_thread_fence(std::memory_order_seq_cst);
        uint64_t after=0;std::memcpy(&after,body+64,8);if(seq!=after)continue;
        try{result=decodeGuestBody(bytes.data(),nowMs(),GetCurrentProcessId());return result.sequence==seq&&result.hostGeneration==request.hostGeneration&&result.worldId;}catch(...){return false;}
    }return false;
}
bool finite(Vec3 v){return std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z)&&std::abs(v.x)<30000000&&std::abs(v.y)<30000000&&std::abs(v.z)<30000000;}
bool beamClock(uint64_t& clock){return read(ptr(request.script+0x10)+0x2d0,clock)&&clock>0&&clock<=0xffffffffULL;}
bool beamState(uintptr_t state){
    if(!identity()||request.hero!=0x02e0000000000009ULL||ptr(state)!=base+0x15c8e30||ptr(state+0x78)!=request.script)return false;
    int index=-1;if(!read(state+0x70,index)||index<0||index>4096)return false;
    auto graph=ptr(request.script+0x160),storage=ptr(graph+0x60);uint64_t flag=0;
    if(!read(graph+0x68,flag)||flag>2)return false;
    auto items=ptr(storage+(flag==1?0:8));auto definition=ptr(items+index*8);int node=-1;
    return read(definition+0x68,node)&&node==34;
}
bool beamDirection(Vec3& result){
    if(!poseBytes)return false;
    std::array<unsigned char,256> copy{};
    for(unsigned tries=0;tries<3;tries++){
        uint64_t before=0,after=0;std::memcpy(&before,poseBytes+64,8);if(!before||(before&1))continue;
        std::atomic_thread_fence(std::memory_order_seq_cst);std::memcpy(copy.data(),poseBytes,copy.size());std::atomic_thread_fence(std::memory_order_seq_cst);std::memcpy(&after,poseBytes+64,8);
        if(before!=after)continue;
        auto u32=[&](size_t at){uint32_t v;std::memcpy(&v,copy.data()+at,4);return v;};
        auto u64=[&](size_t at){uint64_t v;std::memcpy(&v,copy.data()+at,8);return v;};
        auto wall=u64(80),now=nowMs();
        if(std::memcmp(copy.data(),"OWPOSE01",8)||u32(8)!=1||u32(16)!=request.pid||u64(24)!=request.hostGeneration||u32(32)!=1||u32(88)!=1||wall>now||now-wall>100)return false;
        std::memcpy(&result,copy.data()+152,12);result=result*-1.f;
        return finite(result)&&dot(result,result)>.99f&&dot(result,result)<1.01f;
    }return false;
}
// Must hold bindingMutex. Resolve each native time interval at most once,
// including the final short interval captured directly by the original End.
void beamPulse(){
    if(!beamPhase.active)return;
    uint64_t clock=0;
    if(!identity()||request.hero!=0x02e0000000000009ULL||!beamClock(clock)){beamPhase.reset();return;}
    double seconds=beamPhase.advance(clock);if(seconds<=0)return;
    NativeEmission e;e.kind=2;e.volley=beamPhase.begin;e.tick=uint32_t(clock);e.wallMs=nowMs();e.owner=request.modelId;e.resource=request.resource;e.lifetime=float(seconds);e.range=8;
    if(!guest(e.guest)||e.guest.worldId!=beamWorld.worldId||e.guest.generation!=beamWorld.generation||e.guest.sourcePid!=beamWorld.sourcePid
       ||!beamDirection(e.direction)||!read(component(request.model,1)+0x60,e.nativeFeet)||!finite(e.nativeFeet)||!damage(request,e.damage)){++beamRejected;return;}
    e.position=e.nativeFeet+Vec3{0,1,0};e.velocity=e.direction;e.flags=217;
    auto result=journal.append(e);
    if(result==EmissionJournal<512>::Result::Accepted){++accepted;++beamIntervals;}
    else if(result==EmissionJournal<512>::Result::Full){++failures;active=false;}
}
uintptr_t WINAPI beamBegin(void* object){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    auto result=beamOriginal[0](object);
    if(active)try{
        std::lock_guard<std::mutex> held(bindingMutex);uint64_t clock=0;float ammo=0,amount=0;
        if(beamState(reinterpret_cast<uintptr_t>(object))&&damage(request,amount)&&beamClock(clock)&&numeric(request.ammoValue,ammo)&&guest(beamWorld)){
            if(beamPhase.active&&beamPhase.begin==clock)return result;
            if(beamPhase.start(clock,ammo,20))++beamBegins;
        }
    }catch(...){++failures;active=false;}
    return result;
}
uintptr_t WINAPI beamEnd(void* object){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    if(active)try{
        std::lock_guard<std::mutex> held(bindingMutex);
        if(beamState(reinterpret_cast<uintptr_t>(object))){beamPulse();beamPhase.reset();++beamEnds;}
    }catch(...){++failures;active=false;}
    return beamOriginal[1](object);
}
const std::array<BeamCallback,2> beamHooks{beamBegin,beamEnd};
// 0x118 is state re-entry, not finish. 0x158 is dispatched for both
// native DoFinishState and DoAbortState, including release and ammo exhaustion.
constexpr std::array<size_t,2> beamSlots{0x110/8,0x158/8};
bool beamExchange(unsigned i,BeamCallback from,BeamCallback to){
    auto address=beamTable+beamSlots[i];DWORD prior=0;
    if(!VirtualProtect(address,sizeof(void*),PAGE_READWRITE,&prior))return false;
    auto previous=InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(address),reinterpret_cast<void*>(to),reinterpret_cast<void*>(from));
    DWORD ignored=0;bool protectedAgain=VirtualProtect(address,sizeof(void*),prior,&ignored)!=FALSE;
    return protectedAgain&&(previous==reinterpret_cast<void*>(from)||previous==reinterpret_cast<void*>(to));
}
bool installBeam(){
    if(fixture)return true;
    beamTable=reinterpret_cast<void**>(base+0x15c8e30);
    for(unsigned i=0;i<2;i++){
        beamOriginal[i]=reinterpret_cast<BeamCallback>(beamTable[beamSlots[i]]);
        if(reinterpret_cast<uintptr_t>(beamOriginal[i])!=base+(i?0xf53270:0xf531f0))return false;
    }
    for(unsigned i=0;i<2;i++)if(!beamExchange(i,beamOriginal[i],beamHooks[i]))return false;
    return true;
}
void capture(uintptr_t context,uintptr_t result){
    std::lock_guard<std::mutex> lock(bindingMutex);
    combatReady=identity();
    if(!combatReady||request.hero!=0x02e0000000000029ULL){++filtered;return;}
    uintptr_t source=ptr(context+8);uint64_t resource=0;unsigned ownerId=0;
    if(source!=request.model||!read(source+0x94,ownerId)||ownerId!=request.modelId||!read(context+0x28,resource)||resource!=request.resource){++filtered;return;}
    if(!result){++filtered;return;}
    NativeEmission e;e.wallMs=nowMs();e.owner=ownerId;e.resource=resource;
    auto projectile=component(result,0x27),scene=component(result,1),nativeScene=component(source,1);
    if(!projectile||!read(result+0x94,e.entity)||!e.entity||ptr(result+0x28)!=request.admin
       ||!read(context,e.context)||!read(context+0x60,e.position)||!read(context+0x70,e.direction)
       ||!finite(e.position)||!finite(e.direction)||dot(e.direction,e.direction)<.25f||dot(e.direction,e.direction)>4.f){++refused;return;}
    read(context,e.tick);read(context+0x44,e.shot);read(context+0x48,e.pellet);read(projectile+0x18,e.componentOwner);
    // The original initializer copies context position to +40 and calculates
    // direction*native speed plus inherited velocity into +50. Capture its
    // completed result, rather than the uninitialized factory's scene object.
    Vec3 initial{};
    if(e.componentOwner!=e.owner||!read(projectile+0x40,initial)||!finite(initial)||!read(projectile+0x50,e.velocity)||!finite(e.velocity)
       ||dot(initial-e.position,initial-e.position)>.01f||dot(e.velocity,e.velocity)<.01f||dot(e.velocity,e.velocity)>1000000.f){++refused;return;}
    read(projectile,e.projectile);e.position=initial;e.flags|=2;
    if(guest(e.guest))e.flags|=1;
    if(!read(scene+0x60,e.scenePosition)||!finite(e.scenePosition))e.scenePosition={0,0,0};
    if(e.componentOwner==e.owner)e.flags|=4;
    if(read(nativeScene+0x60,e.nativeFeet)&&finite(e.nativeFeet))e.flags|=8;else e.nativeFeet={0,0,0};
    if(!damage(request,e.damage)||(!fixture&&!read(ptr(context+0x18)+0x4c,e.lifetime))){++refused;return;}
    if(fixture)e.lifetime=5;
    if(!std::isfinite(e.lifetime)||e.lifetime<=0||e.lifetime>120){++refused;return;}e.flags|=16;
    auto appended=journal.append(e);
    if(appended==EmissionJournal<512>::Result::Duplicate){++filtered;return;}
    if(appended==EmissionJournal<512>::Result::Full){++failures;active=false;return;}++accepted;
}
uintptr_t WINAPI hook(uintptr_t a,uintptr_t b,uintptr_t c,uintptr_t d){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    auto result=original(a,b,c,d);++calls;
    if(active)try{capture(c,b);}catch(...){++failures;active=false;}
    return result;
}
// Observe the original pellet factory after its native scatter calculation.
// The calibrated offline status-8 route retains native scatter and timing;
// Minecraft supplies the missing collision/damage world. Other failures are refused.
bool evaluateDamage(const ArmorySpec& spec,float& amount){
    uintptr_t getter=0;
    if((spec.amountKind&255)==6){
        if(ptr(spec.amountValue)!=base+0x16067a8||spec.damageRid!=base+0x16067a8||ptr(spec.damageRid+0xd0)!=base+0xf5c120)return false;
        constexpr std::array<uint8_t,24> expected{0x48,0x83,0xec,0x28,0x4d,0x8b,0xd0,0x48,0x85,0xd2,0x75,0x07,0x32,0xc0,0x48,0x83,0xc4,0x28,0xc3,0x48,0x8b,0x8a,0x98,0};
        std::array<uint8_t,24> actual{};if(!read(base+0xf5c120,actual)||actual!=expected)return false;getter=base+0xf5c120;
    }else{
        if(ptr(spec.amountValue)!=base+0x160ae38||spec.damageRid!=base+0x160ae38||ptr(spec.damageRid+0xd0)!=base+0xf6adc0)return false;
        constexpr std::array<uint8_t,18> expected{0x40,0x55,0x41,0x55,0x41,0x57,0x48,0x8d,0x6c,0x24,0xc0,0x48,0x81,0xec,0x40,0x01,0,0};
        std::array<uint8_t,18> actual{};if(!read(base+0xf6adc0,actual)||actual!=expected)return false;getter=base+0xf6adc0;
    }
    struct Primitive{uint64_t raw;uint32_t reserved,type;} value{};
    using Getter=char(WINAPI*)(uintptr_t,uintptr_t,uintptr_t,Primitive*);
    if(!reinterpret_cast<Getter>(getter)(spec.amountValue,spec.script,spec.amountObject,&value))return false;
    if(value.type==2)amount=float(int32_t(value.raw));
    else if(value.type==3){uint32_t bits=uint32_t(value.raw);std::memcpy(&amount,&bits,4);}else return false;
    ++nativeDamageEvaluations;return std::isfinite(amount)&&amount>0&&amount<=10000;
}
unsigned barrageOracleChecks=0,barrageOracleFailures=0;float barrageOracleMaxError=0;
BarrageScope barrageScope;unsigned barrageScopeRefused=0;
bool barrageOracle(uintptr_t config,uintptr_t argument,const std::array<BarrageWave,2>& waves){
    constexpr std::array<uint8_t,24> prefix{0x48,0x8b,0xc4,0xf3,0x0f,0x11,0x58,0x20,0x48,0x89,0x48,0x08,0x53,0x48,0x81,0xec,0xf0,0,0,0,0x83,0xba,0xf8,0};
    std::array<uint8_t,24> code{};if(!read(base+0x1037b60,code)||code!=prefix)return false;
    Vec3 f{};uint16_t seed=0;uintptr_t holder=ptr(config+0x68),items=ptr(holder);
    if(!read(argument+0x70,f)||!read(argument+0x40,seed))return false;
    using Motion=void(WINAPI*)(uintptr_t,void*,float,float,uintptr_t);
    for(unsigned i=0;i<2;i++)for(float age:std::array<float,3>{.1f,.6f,1.2f}){
        alignas(16) std::array<uint8_t,256> localFlight{};
        std::memcpy(localFlight.data()+0x50,&f,sizeof f);std::memcpy(localFlight.data()+0x64,&seed,sizeof seed);
        // Pure native wave arithmetic on owned stack data, only on the original
        // factory thread in explicitly scoped calibration. No script/timer call.
        reinterpret_cast<Motion>(base+0x1037b60)(0,localFlight.data(),0,age,ptr(items+i*8));
        std::array<float,3> actual{};std::memcpy(actual.data(),localFlight.data()+0xb0,sizeof actual);
        auto expected=barrageWaveOffset(waves[i],{f.x,f.y,f.z},age);
        for(unsigned j=0;j<3;j++){float delta=std::abs(actual[j]-expected[j]);barrageOracleMaxError=std::max(barrageOracleMaxError,delta);if(!std::isfinite(delta)||delta>.0001f){++barrageOracleFailures;return false;}}
        ++barrageOracleChecks;
    }
    return true;
}
uintptr_t WINAPI factoryHook(uintptr_t a,uintptr_t b,uintptr_t c,uintptr_t d){
    ++inFlight;struct Leave{~Leave(){--inFlight;}}leave;
    FactoryConfigSnapshot entrySnapshot{};bool capturedEntry=false;
    std::array<BarrageWave,2> launchWaves{};bool launchWavesValid=false;
    // Resolved motion storage belongs to this call. Copy before the original
    // factory returns its temporary pooled configuration to its owner.
    if(active){
        std::lock_guard<std::mutex> lock(bindingMutex);
        if(refreshHero()&&local.hero==0x02e0000000000008ULL&&ptr(b+8)==local.model&&ptr(b+0x28)==0x0400000000000052ULL)
            {launchWavesValid=barrageResolved(base,ptr(b+0x18),b,[](uintptr_t at,auto& v){return read(at,v);},launchWaves);
             if(launchWavesValid&&captureFactoryConfig&&barrageOracleChecks<96)launchWavesValid=barrageOracle(ptr(b+0x18),b,launchWaves);}
    }
    if(active&&captureFactoryConfig){
        std::lock_guard<std::mutex> lock(bindingMutex);
        if(refreshHero()&&ptr(b+8)==local.model){
            auto config=ptr(b+0x18);capturedEntry=read(config,entrySnapshot.config);
            // These are provisional resolved-config fields, not proven data-flow
            // semantics. Copy while the original caller still owns its inputs.
            auto flow=ptr(config+0x68);struct FlowList{uintptr_t items;int count,capacity;} list{};
            if(capturedEntry&&read(flow,list)&&read(flow,entrySnapshot.flowHeader)&&list.count>0&&list.count<=8&&list.count<=list.capacity&&list.capacity<=64){
                std::array<uint8_t,192> values{};SIZE_T copied=0;size_t length=size_t(list.count)*24;
                if(list.items>=0x10000&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(list.items),values.data(),length,&copied)&&copied==length)
                    entrySnapshot.flowValues.assign(values.begin(),values.begin()+length);
            }
            if(capturedEntry&&local.hero==0x02e0000000000005ULL){
                for(auto [offset,length]:std::array<std::pair<unsigned,unsigned>,7>{{{0x10,272},{0x58,48},{0x60,56},{0x88,96},{0x90,80},{0xc0,56},{0xd8,272}}}){
                    std::array<uint8_t,272> bytes{};SIZE_T copied=0;auto object=ptr(config+offset);
                    if(object>=0x10000&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(object),bytes.data(),length,&copied)&&copied==length)
                        entrySnapshot.nested[offset]=std::vector<uint8_t>(bytes.begin(),bytes.begin()+length);
                }
            }
        }
    }
    auto result=factoryOriginal(a,b,c,d);++factoryCalls;
    if(active){
        std::lock_guard<std::mutex> lock(bindingMutex);
        FactoryRow row{};
        if(refreshHero()&&ptr(b+8)==local.model
           &&read(b+0x28,row.resource)&&(row.resource>>48)==0x0400
           &&read(b,row.tick)&&read(b+0x20,row.volley)&&read(b+0x44,row.shot)&&read(b+0x48,row.pellet)
           &&read(c,row.status)&&read(ptr(b+0x18)+0x104,row.type)
           &&read(b+0x60,row.position)&&read(b+0x70,row.direction)&&finite(row.position)&&finite(row.direction)){
            row.wall=nowMs();row.owner=local.modelId;row.result=result;row.hero=local.hero;
            auto observedConfig=ptr(b+0x18);
            if(captureFactoryConfig&&capturedEntry&&(factoryConfigs.count(row.resource)||factoryConfigs.size()<32))factoryConfigs[row.resource]=std::move(entrySnapshot);
            read(observedConfig+0x48,row.speed);read(observedConfig+0x4c,row.lifetime);read(observedConfig+0x50,row.range);
            if(!std::isfinite(row.speed))row.speed=0;
            if(!std::isfinite(row.lifetime))row.lifetime=0;
            if(!std::isfinite(row.range))row.range=0;
            if(matches(request)&&request.hero==0x02e0000000000042ULL&&row.resource==request.resource&&(row.status==8||row.status==0)&&row.type==1){
                NativeEmission e;e.kind=1;e.wallMs=row.wall;e.owner=row.owner;e.resource=row.resource;e.tick=row.tick;e.shot=row.shot;e.pellet=row.pellet;e.volley=row.volley;e.result=row.status;
                e.position=row.position;e.direction=row.direction;e.velocity=row.direction;
                float speed=-1,lifetime=-1;auto config=ptr(b+0x18),scene=component(local.model,1);
                bool valid=read(config+0x48,speed)&&read(config+0x4c,lifetime)&&read(config+0x50,e.range)&&speed==0&&lifetime==0&&e.range==100
                    &&dot(e.direction,e.direction)>.99f&&dot(e.direction,e.direction)<1.01f&&damage(request,e.damage)
                    &&read(scene+0x60,e.nativeFeet)&&finite(e.nativeFeet)&&guest(e.guest);
                if(valid){e.flags=57;auto added=journal.append(e);if(added==EmissionJournal<512>::Result::Accepted)++accepted;else if(added==EmissionJournal<512>::Result::Duplicate)++filtered;else{++failures;active=false;}}
                else ++refused;
            }
            // Pharah's actual offline factory returns status8 without an entity.
            // Carry its confirmed native firing identity and measured flight,
            // never synthesize rockets from buttons or ammo observations.
            if(matches(request)&&request.hero==0x02e0000000000008ULL&&row.resource==request.resource&&row.status==8&&row.type==1){
                NativeEmission e;e.kind=3;e.wallMs=row.wall;e.owner=row.owner;e.resource=row.resource;e.tick=row.tick;e.shot=row.shot;e.pellet=row.pellet;e.volley=row.volley;e.result=row.status;
                e.position=row.position;e.direction=row.direction;e.velocity=row.direction*row.speed;e.lifetime=row.lifetime;e.range=row.range;
                bool valid=row.result==0&&row.speed==35&&row.lifetime==5&&row.range==100&&row.volley&&row.tick
                    &&dot(e.direction,e.direction)>.99f&&dot(e.direction,e.direction)<1.01f&&damage(request,e.damage)
                    &&read(component(local.model,1)+0x60,e.nativeFeet)&&finite(e.nativeFeet)&&guest(e.guest);
                if(valid){e.flags=57;e.splashDamage=80;e.innerRadius=.5f;e.outerRadius=2.5f;e.outerScale=.125f;
                    auto added=journal.append(e);if(added==EmissionJournal<512>::Result::Accepted)++accepted;else if(added==EmissionJournal<512>::Result::Duplicate)++filtered;else{++failures;active=false;}}
                else ++refused;
            }
            bool established=emissionResourceMatches(local.hero,row.resource);
            if(!established&&armoryMatches()){
                for(const auto& spec:armorySpecs)if(spec.resource==row.resource&&(row.volley&0xffffff00ULL)==spec.volleyKey){
                    NativeEmission e;e.kind=4;e.flags=313;e.wallMs=row.wall;e.owner=row.owner;e.resource=row.resource;e.tick=row.tick;e.shot=row.shot;e.pellet=row.pellet;e.volley=row.volley;e.result=row.status;
                    e.hero=local.hero;e.factoryType=row.type;e.flight=row.speed>0&&row.lifetime>0;e.position=row.position;e.direction=row.direction;
                    e.velocity=row.direction*(e.flight?row.speed:1.f);e.lifetime=e.flight?row.lifetime:0;e.range=row.range;
                    e.effect=spec.effect;e.bounces=spec.bounces;e.eyeHeight=spec.eyeHeight;e.gravity=spec.gravity;e.fuse=spec.fuse;e.terrain=spec.terrain;
                    e.splashDamage=spec.splash;e.outerRadius=spec.radius;e.outerScale=.125f;
                    ArmoryBlast blast{};bool blastValid=spec.splash==0||armoryBlast(spec,[](uintptr_t at,auto& value){return read(at,value);},blast);
                    if(spec.splash>0&&blastValid){e.splashDamage=blast.splash;e.innerRadius=blast.inner;e.outerRadius=blast.outer;e.outerScale=blast.scale;}
                    bool barrage=local.hero==0x02e0000000000008ULL&&row.resource==0x0400000000000052ULL;
                    if(barrage&&launchWavesValid){e.waveCount=2;e.waves=launchWaves;}
                    bool valid=(spec.effect!=2||(row.speed==30&&row.lifetime==5&&row.range==7&&armoryFlash(armory,spec,[](uintptr_t at,auto& value){return read(at,value);})))
                        &&(spec.effect!=3||(row.speed==60&&row.lifetime==5&&row.range==100&&armoryFlash(armory,spec,[](uintptr_t at,auto& value){return read(at,value);})))
                        &&(!barrage||(launchWavesValid&&row.speed==45&&row.lifetime==5&&row.range==100&&barrageDefinition(spec,[](uintptr_t at,auto& v){return read(at,v);})))
                        &&(row.status==0||(row.status==8&&row.result==0))&&row.type>=1&&row.type<=3&&row.volley&&row.tick
                        &&row.speed>=0&&row.speed<=1000&&row.lifetime>=0&&row.lifetime<=120&&row.range>0&&row.range<=512
                        &&((e.flight&&row.speed>0&&row.lifetime>0)||(!e.flight&&row.speed==0&&row.lifetime==0))
                        &&dot(e.direction,e.direction)>.99f&&dot(e.direction,e.direction)<1.01f
                        &&blastValid&&armoryGravity(spec,[](uintptr_t at,auto& value){return read(at,value);})&&armoryAmount(armory,spec,[](uintptr_t at,auto& value){return read(at,value);},e.damage,evaluateDamage)&&e.damage>0
                        &&armoryBastionTank(armory,spec,[](uintptr_t at,auto& value){return read(at,value);})
                        &&armoryBastionTankFlight(local.hero,row.resource,row.status,row.result,row.type,row.speed,row.lifetime,row.range)
                        &&read(component(local.model,1)+0x60,e.nativeFeet)&&finite(e.nativeFeet)&&guest(e.guest);
                    row.evaluatedDamage=e.damage;
                    if(valid&&barrage&&!barrageScope.admit(row.owner,row.volley,row.tick,row.shot,e.guest.worldId,e.guest.hostGeneration,e.guest.generation)){
                        valid=false;++barrageScopeRefused;
                    }
                    // A weak normal arrow must not accidentally receive the
                    // full-charge base amount while its scaling is calibrated.
                    if(local.hero==0x02e0000000000005ULL&&row.resource==0x040000000000020bULL&&e.damage>=125)valid=false;
                    if(valid){auto added=journal.append(e);if(added==EmissionJournal<512>::Result::Accepted){++accepted;++armoryAccepted;}else if(added==EmissionJournal<512>::Result::Duplicate)++filtered;else{++failures;active=false;}}
                    else ++refused;
                    break;
                }
            }
            if(captureFactoryConfig){if(factoryRows.size()==256){factoryRows.pop_front();++factoryDropped;}factoryRows.push_back(row);}
        }
    }
    return result;
}
template<class Fn> Fn function(HMODULE dll,const char* name){union{FARPROC raw;Fn value;} cast{GetProcAddress(dll,name)};return cast.value;}
bool install(HMODULE library,bool initialize){
    auto create=function<Create>(library,"MH_CreateHook");auto enable=function<Toggle>(library,"MH_EnableHook");disable=function<Toggle>(library,"MH_DisableHook");
    if(!create||!enable||!disable||!read(target,before))return false;
    if(initialize){using Init=int(WINAPI*)();auto init=function<Init>(library,"MH_Initialize");if(!init)return false;int status=init();if(status!=0&&status!=1)return false;}
    void* trampoline=nullptr;
    if(create(reinterpret_cast<void*>(target),reinterpret_cast<void*>(hook),&trampoline)!=0||!trampoline)return false;
    original=reinterpret_cast<Factory>(trampoline);active=true;
    if(enable(reinterpret_cast<void*>(target))!=0){active=false;return false;}installed=true;
    if(factoryTarget){
        if(!read(factoryTarget,factoryBefore))return false;
        trampoline=nullptr;
        if(create(reinterpret_cast<void*>(factoryTarget),reinterpret_cast<void*>(factoryHook),&trampoline)!=0||!trampoline)return false;
        factoryOriginal=reinterpret_cast<Factory>(trampoline);
        if(enable(reinterpret_cast<void*>(factoryTarget))!=0)return false;
        factoryInstalled=true;
    }
    return installBeam();
}
void stop(){
    active=false;
    bool beamRestored=true;
    if(beamTable)for(unsigned i=0;i<2;i++)if(beamOriginal[i])beamRestored=beamExchange(i,beamHooks[i],beamOriginal[i])&&beamRestored;
    if(factoryInstalled&&disable(reinterpret_cast<void*>(factoryTarget))!=0){++failures;return;}
    if(installed&&disable(reinterpret_cast<void*>(target))!=0){++failures;return;}
    for(unsigned i=0;i<200&&inFlight;i++)Sleep(10);
    std::array<unsigned char,24> actual{};restored=beamRestored&&!inFlight&&read(target,actual)&&actual==before;
    if(factoryInstalled)restored=restored&&read(factoryTarget,actual)&&actual==factoryBefore;
    // Keep the disabled trampoline and this module resident for a callback
    // which had already fetched the old entry before MinHook froze threads.
}
void report(const std::filesystem::path& directory){
    uint64_t hero=0;uint32_t modelId=0;{std::lock_guard<std::mutex> lock(bindingMutex);hero=local.hero;modelId=local.modelId;}
    auto rows=journal.snapshot();auto path=directory/(L"native-emissions-"+std::to_wstring(GetCurrentProcessId())+L".json"),temp=path;temp+=L".tmp";
    auto acknowledged=journal.acknowledged(),last=rows.empty()?acknowledged:rows.back().id;
    std::ofstream o(temp);o<<"{\"pid\":"<<GetCurrentProcessId()<<",\"probeVersion\":16,\"protocol\":3,\"epoch\":"<<epoch<<",\"heartbeat\":"<<nowMs()<<",\"baseId\":"<<(rows.empty()?last+1:rows.front().id)<<",\"lastId\":"<<last<<",\"acknowledged\":"<<acknowledged<<",\"enabled\":"<<(active?"true":"false")<<",\"restored\":"<<(restored?"true":"false")<<",\"creation\":"<<request.creation<<",\"hostGeneration\":"<<request.hostGeneration
      <<",\"hero\":"<<hero<<",\"modelId\":"<<modelId<<",\"combatReady\":"<<(combatReady?"true":"false")<<",\"rebindings\":"<<rebindings
      <<",\"calls\":"<<calls<<",\"accepted\":"<<accepted<<",\"filtered\":"<<filtered<<",\"refused\":"<<refused<<",\"failures\":"<<failures<<",\"failureStage\":\""<<failureStage<<"\",\"overflow\":"<<(journal.overflowed()?"true":"false")<<",\"mcDamageSent\":false,\"events\":[";
    for(size_t i=0;i<rows.size();i++){
        if(i)o<<',';
        auto& e=rows[i];o<<std::setprecision(10)<<"{\"id\":"<<e.id<<",\"wallMs\":"<<e.wallMs<<",\"entity\":"<<e.entity<<",\"owner\":"<<e.owner<<",\"resource\":\""<<std::hex<<e.resource<<std::dec<<"\",\"tick\":"<<e.tick<<",\"shot\":"<<e.shot<<",\"pellet\":"<<e.pellet<<",\"status\":"<<e.result<<",\"componentOwner\":"<<e.componentOwner<<",\"flags\":"<<e.flags<<",\"kind\":"<<e.kind<<",\"volley\":"<<e.volley<<",\"range\":"<<e.range;
        auto vector=[&](const char* name,Vec3 v){o<<",\""<<name<<"\":["<<v.x<<','<<v.y<<','<<v.z<<']';};
        vector("position",e.position);vector("direction",e.direction);vector("velocity",e.velocity);vector("nativeFeet",e.nativeFeet);vector("mcFeet",e.guest.foot);
        o<<",\"mcPid\":"<<e.guest.sourcePid<<",\"mcGeneration\":"<<e.guest.generation<<",\"worldId\":"<<e.guest.worldId<<",\"hostGeneration\":"<<e.guest.hostGeneration<<",\"damage\":"<<e.damage<<",\"lifetime\":"<<e.lifetime;
        if(e.kind==3||e.kind==4)o<<",\"splashDamage\":"<<e.splashDamage<<",\"innerRadius\":"<<e.innerRadius<<",\"outerRadius\":"<<e.outerRadius<<",\"outerScale\":"<<e.outerScale;
        if(e.kind==4)o<<",\"hero\":"<<e.hero<<",\"effect\":"<<e.effect<<",\"flight\":"<<e.flight<<",\"factoryType\":"<<e.factoryType<<",\"eyeHeight\":"<<e.eyeHeight<<",\"gravity\":"<<e.gravity<<",\"bounces\":"<<e.bounces<<",\"fuse\":"<<e.fuse<<",\"terrain\":"<<e.terrain;
        if(e.waveCount){o<<",\"waves\":[";for(unsigned w=0;w<e.waveCount;w++){if(w)o<<',';const auto& v=e.waves[w];o<<"{\"start\":"<<v.start<<",\"fade\":"<<v.fade<<",\"phase\":"<<v.phase<<",\"frequency\":"<<v.frequency<<",\"magnitude\":"<<v.magnitude<<",\"rotation\":"<<v.rotation<<",\"spiral\":"<<(v.spiral?"true":"false")<<'}';}o<<']';}
        o<<'}';
    }o<<"],\"armoryRebindings\":"<<armoryRebindings<<",\"armoryAccepted\":"<<armoryAccepted<<",\"armoryVariants\":"<<armorySpecs.size()<<",\"nativeDamageEvaluations\":"<<nativeDamageEvaluations<<",\"beamBegins\":"<<beamBegins<<",\"beamEnds\":"<<beamEnds<<",\"beamIntervals\":"<<beamIntervals<<",\"beamRejected\":"<<beamRejected<<",\"factoryCalls\":"<<factoryCalls<<",\"factoryDropped\":"<<factoryDropped<<",\"factoryObservations\":[";
    {std::lock_guard<std::mutex> lock(bindingMutex);for(size_t i=0;i<factoryRows.size();i++){
        if(i)o<<',';
        const auto& r=factoryRows[i];
        o<<"{\"wallMs\":"<<r.wall<<",\"owner\":"<<r.owner<<",\"volley\":"<<r.volley<<",\"resource\":"<<r.resource
         <<",\"hero\":"<<r.hero<<",\"speed\":"<<r.speed<<",\"lifetime\":"<<r.lifetime<<",\"range\":"<<r.range
         <<",\"result\":"<<r.result<<",\"status\":"<<r.status<<",\"type\":"<<r.type<<",\"tick\":"<<r.tick<<",\"shot\":"<<r.shot<<",\"pellet\":"<<r.pellet<<",\"evaluatedDamage\":"<<r.evaluatedDamage
         <<",\"position\":["<<r.position.x<<','<<r.position.y<<','<<r.position.z<<"],\"direction\":["<<r.direction.x<<','<<r.direction.y<<','<<r.direction.z<<"]}";
    }
    o<<"],\"barrageScopeRefused\":"<<barrageScopeRefused<<",\"barrageOracleChecks\":"<<barrageOracleChecks<<",\"barrageOracleFailures\":"<<barrageOracleFailures<<",\"barrageOracleMaxError\":"<<barrageOracleMaxError<<",\"factoryCalibration\":"<<(captureFactoryConfig?"true":"false")<<",\"factoryConfigs\":[";bool first=true;
    for(const auto& entry:factoryConfigs){
        if(!first){o<<',';}
        first=false;o<<"{\"resource\":"<<entry.first<<",\"bytes\":\"";
        constexpr char hex[]="0123456789abcdef";
        for(auto value:entry.second.config){o<<hex[value>>4]<<hex[value&15];}
        o<<"\",\"dataFlowHeader\":\"";for(auto value:entry.second.flowHeader){o<<hex[value>>4]<<hex[value&15];}
        o<<"\",\"dataFlowValues\":\"";for(auto value:entry.second.flowValues){o<<hex[value>>4]<<hex[value&15];}
        o<<"\",\"provisionalPreCallFields\":true,\"nested\":[";bool firstNested=true;
        for(auto& [offset,bytes]:entry.second.nested){if(!firstNested)o<<',';firstNested=false;o<<"{\"offset\":"<<offset<<",\"bytes\":\"";for(auto value:bytes)o<<hex[value>>4]<<hex[value&15];o<<"\"}";}
        o<<"]}";
    }}o<<"]}";o.close();MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING);
}
void acknowledge(const std::filesystem::path& directory){
    struct Ack{char magic[8];uint64_t epoch,id;uint32_t pid,reserved;} ack{};static_assert(sizeof(Ack)==32);
    std::ifstream input(directory/(L"native-emissions-"+std::to_wstring(GetCurrentProcessId())+L".ack"),std::ios::binary);input.read(reinterpret_cast<char*>(&ack),sizeof ack);
    if(!input||input.peek()!=std::char_traits<char>::eof()||std::memcmp(ack.magic,"OWACK001",8)||ack.epoch!=epoch||ack.reserved)return;
    GuestBody current;if(!guest(current)||ack.pid!=current.sourcePid)return;
    if(!journal.acknowledge(ack.id)){++failures;active=false;}
}
DWORD WINAPI worker(void*){
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(module,dll)){failureStage="exe";return 0;}
    auto directory=dll.parent_path();
    bool haveRequest=loadRequest(directory,request);
    FILETIME creation,exit,kernel,user;ULARGE_INTEGER when{};
    if(!haveRequest||std::memcmp(request.magic,"OWEMIT01",8)||request.version!=4||request.size!=168||request.pid!=GetCurrentProcessId()||request.reserved||request.reserved2||!emissionResourceMatches(request.hero,request.resource)||!request.hostGeneration||!GetProcessTimes(GetCurrentProcess(),&creation,&exit,&kernel,&user)){failureStage="request";++failures;restored=true;report(directory);return 0;}
    when.LowPart=creation.dwLowDateTime;when.HighPart=creation.dwHighDateTime;if(request.creation!=when.QuadPart){failureStage="creation";return 0;}
    base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));target=base+0xd35c20;factoryTarget=base+0xd354b0;
    const unsigned char factoryPrefix[]={0x40,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x48,0x8d,0xac,0x24,0xf0,0xcf,0xff,0xff};
    std::array<unsigned char,sizeof factoryPrefix> factoryActual{};
    if(!read(factoryTarget,factoryActual)||std::memcmp(factoryActual.data(),factoryPrefix,sizeof factoryPrefix)){failureStage="factory-prefix";return 0;}
    const char prefix[]="\x48\x89\x5c\x24\x08\x48\x89\x54\x24\x10\x55\x56\x57\x41\x54\x41\x55\x41\x56\x41\x57\x48\x83\xec";
    std::array<unsigned char,24> actual{};if(!identity()){failureStage="identity";return 0;}if(!read(target,actual)||std::memcmp(actual.data(),prefix,24)){failureStage="target-prefix";return 0;}
    auto library=GetModuleHandleW(L"minhook.x64.dll");if(!owmc::loadedClientCompanion(library,exe,L"minhook.x64.dll")){failureStage="minhook";return 0;}
    bodyMapping=OpenFileMappingW(FILE_MAP_READ,FALSE,L"Local\\OWMCPassthroughFrame");if(bodyMapping){auto view=static_cast<const unsigned char*>(MapViewOfFile(bodyMapping,FILE_MAP_READ,0,0,4096));if(view)body=view+1536;}
    poseMapping=OpenFileMappingW(FILE_MAP_READ,FALSE,L"Local\\OWMCHostPose");if(poseMapping)poseBytes=static_cast<const unsigned char*>(MapViewOfFile(poseMapping,FILE_MAP_READ,0,0,4096));
    HANDLE halt=CreateEventW(nullptr,TRUE,FALSE,(L"Local\\OWMCEmissionStop_"+std::to_wstring(GetCurrentProcessId())).c_str());if(!halt){failureStage="stop-event";return 0;}
    LARGE_INTEGER clock;QueryPerformanceCounter(&clock);epoch=uint64_t(clock.QuadPart);
    float amount=0;if(!damage(request,amount)){failureStage="damage";++failures;report(directory);CloseHandle(halt);return 0;}combatReady=true;if(!install(library,false)){failureStage="install";++failures;stop();report(directory);CloseHandle(halt);return 0;}
    for(unsigned i=0;i<1440000&&active;i++){if(WaitForSingleObject(halt,20)!=WAIT_TIMEOUT)break;synchronize(directory);{std::lock_guard<std::mutex> held(bindingMutex);beamPulse();}acknowledge(directory);report(directory);}
    stop();report(directory);CloseHandle(halt);return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_EmissionTestAttach(uintptr_t factory,uintptr_t model,HMODULE library,uintptr_t pelletFactory){
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-emission-lifecycle-test.exe"||original)return FALSE;
    // This fixture explicitly verifies detailed observation rows in addition
    // to the unchanged event journal. Normal game startup leaves them disabled.
    fixture=true;captureFactoryConfig=true;request.hero=0x02e0000000000029ULL;request.model=model;request.admin=ptr(model+0x28);unsigned id=0;if(!read(model+0x94,id)||!refreshHero())return FALSE;request.modelId=id;request.localId=local.localId;request.resource=0x04000000000007ca;target=factory;factoryTarget=pelletFactory;return identity()&&install(library,true);
}
extern "C" __declspec(dllexport) BOOL OWMC_EmissionTestRebind(){if(!fixture)return FALSE;std::lock_guard<std::mutex> lock(bindingMutex);if(!refreshHero())return FALSE;auto candidate=request;candidate.localId=local.localId;candidate.modelId=local.modelId;candidate.model=local.model;candidate.hero=local.hero;candidate.resource=local.hero==0x02e0000000000042ULL?0x04000000000002a7ULL:local.hero==0x02e0000000000008ULL?0x0400000000000033ULL:0x04000000000007caULL;return adopt(candidate);}
extern "C" __declspec(dllexport) BOOL OWMC_EmissionTestBody(const unsigned char* bytes){if(!fixture)return FALSE;body=bytes;request.hostGeneration=77;return TRUE;}
extern "C" __declspec(dllexport) BOOL OWMC_EmissionTestBeamTable(void** value){if(!fixture||beamTable||!value)return FALSE;beamTable=value;for(unsigned i=0;i<2;i++){beamOriginal[i]=reinterpret_cast<BeamCallback>(beamTable[beamSlots[i]]);if(!beamExchange(i,beamOriginal[i],beamHooks[i]))return FALSE;}return TRUE;}
extern "C" __declspec(dllexport) BOOL OWMC_EmissionTestStop(){if(!fixture)return FALSE;stop();auto rows=journal.snapshot();return restored&&factoryRows.size()==10&&factoryRows[0].status==8&&factoryRows[0].owner==5&&factoryRows[0].direction.z==1&&factoryCalls==10&&rows.size()==6&&rows[0].entity==9&&rows[0].owner==3&&rows[5].entity==10&&rows[5].owner==7&&rows[0].position.x==42&&rows[0].direction.z==1&&rows[0].flags==30&&rows[0].damage==35&&rows[1].kind==1&&rows[1].entity==0&&rows[1].owner==5&&rows[1].tick==42&&rows[1].range==100&&rows[1].flags==57&&rows[1].damage==70&&rows[1].guest.worldId==88&&rows[2].tick==43&&rows[3].kind==3&&rows[3].damage==40&&rows[3].splashDamage==80&&rows[3].velocity.z==35&&rows[3].outerRadius==2.5f&&rows[4].tick==102&&rebindings==3&&filtered>=5&&refused==3&&!failures;}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void*){if(reason==DLL_PROCESS_ATTACH){module=instance;DisableThreadLibraryCalls(instance);HANDLE thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread)CloseHandle(thread);}return TRUE;}
