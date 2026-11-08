#include "native_client_paths.hpp"
#include "body_fields.hpp"
#include "native_local_hero.hpp"
#include "hero_camera_definition.hpp"
#include "native_flight.hpp"
#include "local_bucket_compat.hpp"
#include "native_gameplay_view.hpp"
#include "native_blink.hpp"
#include "native_state_lifetime.hpp"
#include "native_meter_display.hpp"
#include "native_deadeye_presentation.hpp"
#include "native_recall_completion.hpp"
#include "native_recall_ammo.hpp"
#include "native_wraith_completion.hpp"
#include "native_shadow_completion.hpp"
#include "native_weapon_slots.hpp"
#include "native_pickup_scrap.hpp"
#include "native_placement_actions.hpp"
#include "native_winston_actions.hpp"
#include "native_winston_presentation.hpp"
#include "native_hero_audio_gain.hpp"
#include <windows.h>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <memory>
#include <mutex>

using namespace passthrough;
namespace {
HMODULE module;void* hooked=nullptr;void **original=nullptr,**owned=nullptr;
using Tick=uintptr_t(WINAPI*)(void*,UINT);
std::atomic<bool> active{false},restored{false};
std::atomic<unsigned> ticks{0},writes{0},rejected{0},failures{0},grounded{0},airborne{0};
std::atomic<uint64_t> lastSequence{0};BodyAnchor anchor;
GuestBody lastBody{};bool haveBody=false;
NativeFlightAccumulator flight;HANDLE flightMapping=nullptr;unsigned char* flightMemory=nullptr;uint64_t flightSequence=0;
NativeBlinkAccumulator blink;std::shared_ptr<const NativeBlinkBinding> blinkBinding;
std::atomic<unsigned> blinkCaptures{0};std::atomic<bool> blinkBound{false};
std::atomic<unsigned> flightCaptures{0};
std::atomic<unsigned> motorCaptures{0};
std::atomic<unsigned> bucketPromotions{0};
std::atomic<unsigned> menuHeldTicks{0};
std::atomic<unsigned> heldTicks{0},sessionResumes{0};
std::atomic<unsigned> climbTicks{0};
std::atomic<unsigned> worldTransitions{0},worldStableTicks{0};
std::shared_ptr<const NativeLifetimeRequest> lifetimeBinding;
std::atomic<uint64_t> lifetimeHandled{0};
std::atomic<unsigned> lifetimeCalls{0},lifetimeRefused{0};
std::atomic<DWORD> lifetimeThread{0};
using LifetimeHelper=void(WINAPI*)(void*,int,bool);
LifetimeHelper lifetimeHelper=nullptr;uint64_t lifetimeCreation=0;uintptr_t lifetimeLogger=0;
bool lifetimeLab=false;
BodyStability bodyStability;
HANDLE mapping=nullptr;const unsigned char* body=nullptr;
uintptr_t base=0,admin=0,controller=0,model=0,reference=0;unsigned localId=0,modelId=0;
BodyAddresses addresses{};
NativeLocalHero current;
NativeMeterDisplay nativeMeterDisplay;
NativeWeaponSlots nativeWeaponSlots;
NativePickupScrap nativePickupScrap;
std::shared_ptr<const ScrapCreditRequest> scrapCreditRequest;
std::shared_ptr<const ScrapCreditAck> scrapCreditAck;
NativePlacementActions nativePlacementActions;
std::array<NativeWinstonActions,2> nativeWinstonActions;
NativeWinstonPresentation nativeWinstonPresentation;
NativeHeroAudioGain nativeHeroAudioGain;std::mutex nativeHeroAudioMutex;
bool audioProfile(bool enabled,bool stopping=false){
    std::lock_guard<std::mutex> lock(nativeHeroAudioMutex);
    auto read=[](uintptr_t p,void* out,size_t size){SIZE_T n=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),out,size,&n)&&n==size;};
    auto write=[](uintptr_t p,const void* in,size_t size){SIZE_T n=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),in,size,&n)&&n==size;};
    return stopping?nativeHeroAudioGain.stop(read,write):nativeHeroAudioGain.update(base,enabled,read,write);
}
std::array<std::shared_ptr<const PlacementActionRequest>,5> placementRequests;
std::array<std::shared_ptr<const PlacementActionAck>,5> placementAcks;
NativeDeadeyePresentation nativeDeadeye;
NativeRecallCompletion nativeRecall;
NativeRecallAmmo nativeRecallAmmo;
NativeWraithCompletion nativeWraith;
std::shared_ptr<const NativeWraithBinding> wraithBinding;
NativeShadowCompletion nativeShadow;
std::shared_ptr<const NativeShadowBinding> shadowBinding;
std::shared_ptr<const NativeShadowAck> shadowAck;
std::shared_ptr<const NativeRecallBinding> recallBinding;
std::shared_ptr<const NativeRecallCompletionAck> recallAck;
std::shared_ptr<const DeadeyePresentationRequest> deadeyeRequest;
std::shared_ptr<const DeadeyePresentationAck> deadeyeAck;
uint64_t nativeCreation=0,nextMeterDisplay=0;
std::atomic<DWORD> callbackThread{0};
float eyeHeight=1.2f;
std::atomic<unsigned> heroRebindings{0},waitingForHero{0};
std::atomic<uint64_t> boundHero{0},boundModel{0};
template<class T> bool read(uintptr_t p,T& v){SIZE_T n=0;return p>=0x10000&&p<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),&v,sizeof v,&n)&&n==sizeof v;}
uintptr_t ptr(uintptr_t p){uintptr_t v=0;return read(p,v)?v:0;}
uintptr_t component(uintptr_t owner,unsigned wanted){
    struct List{uintptr_t items;int count,capacity;} l{};
    if(!read(owner+0x50,l)||l.count<1||l.count>l.capacity||l.capacity>256)return 0;
    for(int i=0;i<l.count-1;i++){auto p=ptr(l.items+i*8);unsigned char id=0;if(read(p+0x10,id)&&id==wanted&&ptr(p+8)==owner)return p;}return 0;
}
bool identity(){
    unsigned id=0,refId=0;return ptr(base+0x17b7f90)==admin&&read(admin+0x220,id)&&id==localId
        &&read(reference+0x94,refId)&&refId==modelId&&ptr(reference+8)==controller
        &&ptr(addresses.mover+8)==model&&ptr(addresses.scene+8)==model&&ptr(addresses.local+8)==controller
        &&addresses.presentationState>=0xa060&&ptr(addresses.presentationState-0xa060+8)==model;
}
bool bindHero(){
    if(ptr(base+0x17b7f90)!=admin)return false;
    auto reader=[](uintptr_t address,void* data,size_t size){SIZE_T n=0;return address>=0x10000&&size<=65536&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),data,size,&n)&&n==size;};
    if(!current.refresh(admin,reader))return false;
    HeroCameraDefinition camera;
    if(!heroCameraDefinition(current.model,reader,camera))return false;
    float height=camera.eyeHeight;
    auto movementState=component(current.model,0x12);
    BodyAddresses candidate{component(current.model,0x15),component(current.controller,0x2f),component(current.model,1),movementState?movementState+0xa060:0};
    if(!candidate.mover||!candidate.local||!candidate.scene||!candidate.presentationState)return false;
    if(modelId&&modelId!=current.modelId)++heroRebindings;
    localId=current.localId;modelId=current.modelId;controller=current.controller;reference=current.reference;model=current.model;
    addresses=candidate;eyeHeight=height;boundHero=current.hero;boundModel=modelId;return identity();
}
uint64_t nowMs(){FILETIME ft;GetSystemTimeAsFileTime(&ft);ULARGE_INTEGER t{};t.LowPart=ft.dwLowDateTime;t.HighPart=ft.dwHighDateTime;return (t.QuadPart-116444736000000000ULL)/10000;}
void publishFlight(const GuestBody& s,Vec3 velocity,uint32_t mode){
    if(!flightMemory)return;
    std::array<unsigned char,256> packet{};
    auto put=[&](size_t at,auto value){std::memcpy(packet.data()+at,&value,sizeof value);};
    std::memcpy(packet.data(),"OWFLY001",8);put(8,uint32_t(1));put(12,uint32_t(256));put(16,uint32_t(GetCurrentProcessId()));put(20,uint32_t(modelId));
    put(24,s.hostGeneration);put(32,s.worldId);put(40,s.generation);put(48,s.sourcePid);put(52,mode);
    flightSequence+=2;put(64,flightSequence);put(72,nowMs());
    for(unsigned i=0;i<3;i++)put(80+i*8,mode==2?blink.total[i]:flight.total[i]);
    put(104,velocity);put(116,uint32_t(s.grounded));
    if(mode==2){put(120,blink.consumed);put(128,blink.captures);}
    InterlockedExchange64(reinterpret_cast<volatile LONG64*>(flightMemory+64),flightSequence-1);MemoryBarrier();
    std::memcpy(flightMemory,packet.data(),64);std::memcpy(flightMemory+72,packet.data()+72,184);MemoryBarrier();
    InterlockedExchange64(reinterpret_cast<volatile LONG64*>(flightMemory+64),flightSequence);
}
bool latest(GuestBody& result){
    std::array<unsigned char,256> b{};
    for(int attempt=0;attempt<3;attempt++){
        uint64_t seq=0;std::memcpy(&seq,body+64,8);if(!seq||(seq&1))continue;
        std::atomic_thread_fence(std::memory_order_seq_cst);std::memcpy(b.data(),body,b.size());std::atomic_thread_fence(std::memory_order_seq_cst);
        uint64_t after=0;std::memcpy(&after,body+64,8);if(after!=seq)continue;
        try{result=decodeGuestBody(b.data(),nowMs(),GetCurrentProcessId());return result.sequence==seq;}catch(...){return false;}
    }return false;
}
uintptr_t WINAPI tick(void* object,UINT cf){
    callbackThread=GetCurrentThreadId();
    if(active){
        if(!identity())bindHero();
        if(identity()){
            auto reader=[](uintptr_t p,void* out,size_t size){SIZE_T n=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),out,size,&n)&&n==size;};
            auto writer=[](uintptr_t p,const void* in,size_t size){SIZE_T n=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),in,size,&n)&&n==size;};
            unsigned promoted=0;
            if(!localBucketCompatibility(admin,current,reader,writer,promoted)){++failures;active=false;}
            bucketPromotions+=promoted;
            if(active)nativeWeaponSlots.update(base,admin,current,reader,writer,
                [](uintptr_t fn,uintptr_t primitive,uintptr_t sync,uintptr_t instance,uintptr_t user){
                    using Notify=uintptr_t(WINAPI*)(void*,void*,void*,const void*,void*,bool);
                    return reinterpret_cast<Notify>(fn)(reinterpret_cast<void*>(primitive),reinterpret_cast<void*>(sync),
                        reinterpret_cast<void*>(instance),reinterpret_cast<void*>(primitive+0xa0),reinterpret_cast<void*>(user),false)!=0;
                });
        }
    }
    audioProfile(active&&identity()&&current.hero==0x02e0000000000040ULL);
    auto result=reinterpret_cast<Tick>(original[0])(object,cf);++ticks;
    if(!active)return result;
    // Native selection destroys/recreates both entities. Rebind on the native
    // movement owner thread; do not retain or write a departed hero's fields.
    if(!identity()&&!bindHero()){++waitingForHero;return result;}
    GuestBody s;
    bool freshBody=latest(s);
    if(!freshBody){
        ++rejected;if(!haveBody)return result;
        // A loading screen/restarted MC must not let the original actor fall
        // and die in its old map. Hold only its last verified position, with
        // all guest movement/ability intent cleared until fresh packets return.
        s=lastBody;s.velocity={0,0,0};s.grounded=true;s.climbing=false;s.nativeFlight=false;++heldTicks;
    } else {
        if(anchor.ready&&(s.generation!=anchor.generation||s.sourcePid!=anchor.sourcePid)) {
            if(!anchor.resumeSession(s)){++failures;active=false;return result;}++sessionResumes;
        }
        lastBody=s;haveBody=true;
    }
    if((current.hero!=0x02e0000000000029ULL&&current.hero!=0x02e0000000000005ULL)||s.climbModel!=modelId)s.climbing=false;
    Vec3 target;try{target=anchor.target(s);}catch(...){++failures;active=false;return result;}
    // Dimension changes are asynchronous in both clients.  Rebinding and
    // writing the old native mover on the first End packet can leave the new
    // hero floating with a zeroed health/weapon owner.  Require two
    // consecutive fresh packets from the same world before applying the
    // rebased pose.  The first packet is deliberately held for one native
    // callback; the normal native animation continues to render meanwhile.
    if(anchor.worldChanged)++worldTransitions;
    bool stable=bodyStability.observe(s,freshBody);
    worldStableTicks.store(bodyStability.ticks,std::memory_order_relaxed);
    if(freshBody&&(anchor.worldChanged||!stable))return result;
    auto reader=[](uintptr_t p,void* dst,size_t size){SIZE_T n=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),dst,size,&n)&&n==size;};
    // Script notifications belong to this existing native logic owner. The
    // renderer must not allocate/drain script notifications in parallel.
    if(freshBody&&nativeGameplayView(base,admin,reader)){
        auto command=std::atomic_load(&deadeyeRequest);
        DeadeyePresentationContext c{GetCurrentProcessId(),nativeCreation,nowMs(),s.hostGeneration,s.worldId,base,reinterpret_cast<uintptr_t>(GetModuleHandleW(L"inject.dll"))};
        nativeWinstonPresentation.update(c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool start){
            reinterpret_cast<void(WINAPI*)(void*,int,bool)>(function)(reinterpret_cast<void*>(script),node,start);
        });
        int placementKind=current.hero==0x02e00000000000ddULL?1:current.hero==0x02e0000000000006ULL?2:current.hero==0x02e000000000000aULL?3:0;
        if(current.hero==0x02e0000000000009ULL)for(unsigned role=0;role<2;role++){
            auto command=std::atomic_load(&placementRequests[role+3]);auto& action=nativeWinstonActions[role];
            if(action.update(command.get(),c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool){
                reinterpret_cast<void(WINAPI*)(void*,int)>(function)(reinterpret_cast<void*>(script),node);
            },[](uintptr_t at,const void* data,size_t size){SIZE_T n=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),data,size,&n)&&n==size;}))
                std::atomic_store(&placementAcks[role+3],std::make_shared<const PlacementActionAck>(action.ack));
        }
        if(placementKind){auto placement=std::atomic_load(&placementRequests[placementKind-1]);
            if(nativePlacementActions.update(placement.get(),c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool start){
                if(function==reinterpret_cast<uintptr_t>(GetModuleHandleW(L"inject.dll"))+0x7abc0)
                    reinterpret_cast<void(WINAPI*)(void*,int)>(function)(reinterpret_cast<void*>(script),node);
                else reinterpret_cast<void(WINAPI*)(void*,int,bool)>(function)(reinterpret_cast<void*>(script),node,start);
            },[](uintptr_t at,const void* data,size_t size){SIZE_T n=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),data,size,&n)&&n==size;}))std::atomic_store(&placementAcks[placementKind-1],std::make_shared<const PlacementActionAck>(nativePlacementActions.ack));
        }
        auto scrapCommand=std::atomic_load(&scrapCreditRequest);
        if(nativePickupScrap.update(scrapCommand.get(),c,current,reader,[](uintptr_t fn,uintptr_t primitive,uintptr_t sync,uintptr_t instance,const void* value,uintptr_t user){
            using Notify=uintptr_t(WINAPI*)(void*,void*,void*,const void*,void*,bool);
            return reinterpret_cast<Notify>(fn)(reinterpret_cast<void*>(primitive),reinterpret_cast<void*>(sync),reinterpret_cast<void*>(instance),value,reinterpret_cast<void*>(user),false)!=0;
        }))std::atomic_store(&scrapCreditAck,std::make_shared<const ScrapCreditAck>(nativePickupScrap.ack));
        auto recall=std::atomic_load(&recallBinding);
        auto recallResult=std::atomic_load(&recallAck);
        auto wraith=std::atomic_load(&wraithBinding);
        auto shadow=std::atomic_load(&shadowBinding);auto shadowResult=std::atomic_load(&shadowAck);
        nativeShadow.update(shadow.get(),shadowResult.get(),c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool start){
            if(function==reinterpret_cast<uintptr_t>(GetModuleHandleW(L"inject.dll"))+0x7abc0)
                reinterpret_cast<void(WINAPI*)(void*,int)>(function)(reinterpret_cast<void*>(script),node);
            else reinterpret_cast<void(WINAPI*)(void*,int,bool)>(function)(reinterpret_cast<void*>(script),node,start);
        });
        nativeWraith.update(wraith.get(),c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool start){
            reinterpret_cast<void(WINAPI*)(void*,int,bool)>(function)(reinterpret_cast<void*>(script),node,start);
        });
        nativeRecall.update(recall.get(),recallResult.get(),c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool start){
            reinterpret_cast<void(WINAPI*)(void*,int,bool)>(function)(reinterpret_cast<void*>(script),node,start);
        });
        if(nativeRecall.ammoDue){
            nativeRecall.ammoDue=false;
            if(recall)nativeRecallAmmo.restore(*recall,c,current,reader,[](uintptr_t fn,uintptr_t primitive,uintptr_t sync,uintptr_t instance,const void* value,uintptr_t user){
                using Notify=uintptr_t(WINAPI*)(void*,void*,void*,const void*,void*,bool);
                return reinterpret_cast<Notify>(fn)(reinterpret_cast<void*>(primitive),reinterpret_cast<void*>(sync),reinterpret_cast<void*>(instance),value,reinterpret_cast<void*>(user),false)!=0;
            });
        }
        if(nativeDeadeye.update(command.get(),c,current,reader,[](uintptr_t function,uintptr_t script,int node,bool start){
            reinterpret_cast<void(WINAPI*)(void*,int,bool)>(function)(reinterpret_cast<void*>(script),node,start);
        }))std::atomic_store(&deadeyeAck,std::make_shared<const DeadeyePresentationAck>(nativeDeadeye.ack));
        if(GetTickCount64()>=nextMeterDisplay){
            nextMeterDisplay=GetTickCount64()+50;
            nativeMeterDisplay.update(base,admin,current,reader,
                [](uintptr_t at,const void* data,size_t size){SIZE_T n=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),data,size,&n)&&n==size;},
                [](uintptr_t fn,uintptr_t primitive,uintptr_t sync,uintptr_t instance,const void*,uintptr_t user){
                    using Notify=uintptr_t(WINAPI*)(void*,void*,void*,const void*,void*,bool);
                    return reinterpret_cast<Notify>(fn)(reinterpret_cast<void*>(primitive),reinterpret_cast<void*>(sync),reinterpret_cast<void*>(instance),reinterpret_cast<void*>(primitive+0xa0),reinterpret_cast<void*>(user),false)!=0;
                });
        }
    }
    // Prewarm observers without moving the initial picker actor. After the
    // first gameplay write, retain the existing MC authority in every view:
    // suspending it on later menus lets the native actor fall in the old map.
    if(!writes.load()&&!nativeGameplayView(base,admin,reader)){++menuHeldTicks;flight.ready=false;publishFlight(s,{},false);return result;}
    if(lifetimeLab&&lifetimeHelper&&freshBody&&nativeGameplayView(base,admin,reader)){
        auto command=std::atomic_load(&lifetimeBinding);
        if(command&&command->sequence>lifetimeHandled){
            lifetimeHandled=command->sequence;lifetimeThread=GetCurrentThreadId();uint64_t actualHero=0;read(current.heroInfo+0x98,actualHero);
            NativeLifetimeContext context{GetCurrentProcessId(),GetCurrentThreadId(),lifetimeCreation,admin,modelId,model,actualHero,s.hostGeneration,s.worldId,nowMs(),base,lifetimeLogger};
            if(nativeLifetimeOwner(*command,context,[](uintptr_t at,auto& value){return read(at,value);})){
                // The supplied plugin's exact public helper creates its own
                // original lifetime notification on this native owner thread.
                // No direct Finish callback, state flag or timer write occurs.
                lifetimeHelper(reinterpret_cast<void*>(command->script),2,false);++lifetimeCalls;
                if(!identity())return result;
            }else ++lifetimeRefused;
        }
    }
    auto writer=[](uintptr_t p,const void* src,size_t size){SIZE_T n=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),src,size,&n)&&n==size;};
    auto setter=[](uintptr_t scene,Vec4 rotation,Vec4 position){using Fn=void(WINAPI*)(void*,const Vec4*,const Vec4*);reinterpret_cast<Fn>(base+0xa04000)(reinterpret_cast<void*>(scene),&rotation,&position);};
    GuestBody applied=s;Vec3 nativePosition{},nativeVelocity{},nativeGravity{};
    Vec3 motorVelocity{};
    bool wantsMotor=s.nativeFlight&&s.flightModel==modelId&&nativeMotorHero(current.hero)
        &&read(addresses.mover+0x7e0+0x220,nativePosition)&&read(addresses.mover+0x7e0+0x230,motorVelocity)&&validNativeFlight(nativePosition,motorVelocity,{});
    bool wantsFlight=s.nativeFlight&&s.flightModel==modelId&&current.hero==0x02e0000000000008ULL;
    bool wantsBlink=false;
    if(s.nativeFlight&&s.flightModel==modelId&&current.hero==0x02e0000000000003ULL&&nativeGameplayView(base,admin,reader)){
        auto binding=std::atomic_load(&blinkBinding);uint64_t actionTick=0;
        auto typedReader=[](uintptr_t p,auto& value){return read(p,value);};
        wantsBlink=binding&&blinkOwner(*binding,admin,localId,modelId,model,typedReader)
            &&blinkStateTick(binding->logger,binding->script,typedReader,actionTick)&&read(addresses.mover+0x7e0+0x220,nativePosition);
        if(wantsBlink&&blink.capture(s,modelId,actionTick,nowMs(),nativePosition))++blinkCaptures;
    }
    blinkBound=wantsBlink;if(!wantsBlink)blink.ready=false;
    bool captured=false;
    if(wantsFlight&&read(addresses.mover+0x7e0+0x220,nativePosition)&&read(addresses.mover+0x7e0+0x230,nativeVelocity)&&read(addresses.mover+0x7e0+0x250,nativeGravity)&&validNativeFlight(nativePosition,nativeVelocity,nativeGravity)){
        captured=flight.capture(s,modelId,nativePosition,nativeVelocity);
        if(s.blockedAxes&1)nativeVelocity.x=0;
        if((s.blockedAxes&2)&&nativeVelocity.y<=0){nativeVelocity.y=0;nativeGravity.y=0;}
        if((s.blockedAxes&2)&&!s.grounded&&nativeVelocity.y>0){nativeVelocity.y=0;nativeGravity.y=0;}
        if(s.blockedAxes&4)nativeVelocity.z=0;
        applied.velocity=nativeVelocity;if(nativeVelocity.y>0)applied.grounded=false;
    }else if(wantsMotor){
        captured=flight.capture(s,modelId,nativePosition,motorVelocity);
        if(s.blockedAxes&1)motorVelocity.x=0;
        if(s.blockedAxes&4)motorVelocity.z=0;
        // MC friction is not the native integrator's velocity. Preserve the
        // original horizontal state; import actual displacement rather than
        // feeding MC's damped velocity back into every native physics frame.
        applied.velocity.x=motorVelocity.x;applied.velocity.z=motorVelocity.z;
        wantsFlight=false;
    }else {flight.ready=false;wantsFlight=false;}
    if(!applyGuestBody(addresses,applied,target,reader,writer,setter,eyeHeight,wantsFlight?&nativeGravity:nullptr)){++failures;active=false;return result;}
    if(wantsFlight||wantsMotor){flight.applied(target);if(captured){if(wantsMotor)++motorCaptures;else ++flightCaptures;}}
    if(wantsBlink)blink.applied(target);
    publishFlight(s,wantsFlight?nativeVelocity:wantsMotor?motorVelocity:Vec3{},wantsBlink?2u:wantsMotor?3u:uint32_t(wantsFlight&&captured));
    ++writes;if(s.climbing)++climbTicks;if(s.grounded)++grounded;else ++airborne;lastSequence=s.sequence;return result;
}
void stop(){active=false;bool hookRestored=!hooked;if(hooked){auto previous=InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(hooked),original,owned);hookRestored=previous==owned||previous==original;}restored=audioProfile(false,true)&&hookRestored;}
void report(const std::filesystem::path& directory){
    auto path=directory/(L"body-sync-"+std::to_wstring(GetCurrentProcessId())+L".json"),temp=path;temp+=L".tmp";
    std::ofstream o(temp);o<<"{\"pid\":"<<GetCurrentProcessId()<<",\"probeVersion\":39,\"enabled\":"<<(active?"true":"false")<<",\"restored\":"<<(restored?"true":"false")
      <<",\"roadhogAudioBaseline\":"<<nativeHeroAudioGain.baseline.load()<<",\"roadhogAudioEffective\":"<<nativeHeroAudioGain.effective.load()
      <<",\"roadhogAudioBoosted\":"<<(nativeHeroAudioGain.boosted?"true":"false")<<",\"roadhogAudioCapped\":"<<(nativeHeroAudioGain.capped?"true":"false")
      <<",\"roadhogAudioApplications\":"<<nativeHeroAudioGain.applications.load()<<",\"roadhogAudioRestorations\":"<<nativeHeroAudioGain.restorations.load()<<",\"roadhogAudioRefused\":"<<nativeHeroAudioGain.refused.load()<<",\"roadhogAudioExternalChanges\":"<<nativeHeroAudioGain.externalChanges.load()
      <<",\"winstonJumpCalls\":"<<nativeWinstonActions[0].calls<<",\"winstonJumpCompleted\":"<<nativeWinstonActions[0].completed<<",\"winstonJumpRefused\":"<<nativeWinstonActions[0].refused
      <<",\"winstonBarrierCalls\":"<<nativeWinstonActions[1].calls<<",\"winstonBarrierCompleted\":"<<nativeWinstonActions[1].completed<<",\"winstonBarrierRefused\":"<<nativeWinstonActions[1].refused
      <<",\"winstonClockWrites\":"<<(nativeWinstonActions[0].clockWrites+nativeWinstonActions[1].clockWrites)
      <<",\"winstonPoseEnds\":"<<nativeWinstonPresentation.ends<<",\"winstonPoseCompleted\":"<<nativeWinstonPresentation.completed<<",\"winstonPoseRefused\":"<<nativeWinstonPresentation.refused
      <<",\"placementOriginalCalls\":"<<nativePlacementActions.calls<<",\"placementOriginalCompleted\":"<<nativePlacementActions.completed<<",\"placementOriginalRefused\":"<<nativePlacementActions.refused
      <<",\"placementNativeCounterStarts\":"<<nativePlacementActions.counterStarts
      <<",\"scrapNativeCredits\":"<<nativePickupScrap.credits<<",\"scrapNativeRefused\":"<<nativePickupScrap.refused
      <<",\"weaponSlotModel\":"<<nativeWeaponSlots.modelId<<",\"weaponSlotCount\":"<<nativeWeaponSlots.count
      <<",\"weaponSlotSelected\":"<<nativeWeaponSlots.selected<<",\"weaponSlotInitializations\":"<<nativeWeaponSlots.initializations
      <<",\"weaponSlotParameterWrites\":"<<nativeWeaponSlots.parameterWrites<<",\"weaponSlotNotices\":"<<nativeWeaponSlots.notices
      <<",\"weaponSlotRefused\":"<<nativeWeaponSlots.refused<<",\"weaponSlotWallMs\":"<<nowMs()
      <<",\"recallCompletionCalls\":"<<nativeRecall.calls<<",\"recallCompleted\":"<<nativeRecall.completed<<",\"recallCompletionRefused\":"<<nativeRecall.refused
      <<",\"recallHistoryCalls\":"<<nativeRecall.historyCalls<<",\"recallHistoryCompleted\":"<<nativeRecall.historyCompleted
      <<",\"recallAmmoRestored\":"<<nativeRecallAmmo.restored<<",\"recallAmmoRefused\":"<<nativeRecallAmmo.refused
      <<",\"wraithAdmissionCalls\":"<<nativeWraith.starts<<",\"wraithCompletionCalls\":"<<nativeWraith.calls<<",\"wraithCompleted\":"<<nativeWraith.completed<<",\"wraithCompletionRefused\":"<<nativeWraith.refused
      <<",\"shadowAdmissionCalls\":"<<nativeShadow.admissions<<",\"shadowCompleted\":"<<nativeShadow.completed<<",\"shadowRefused\":"<<nativeShadow.refused<<",\"shadowCancelledAim\":"<<nativeShadow.cancelledAim
      <<",\"callbackThread\":"<<callbackThread<<",\"meterDisplayNotices\":"<<nativeMeterDisplay.notices<<",\"meterDisplayRefused\":"<<nativeMeterDisplay.refused
      <<",\"deadeyeAnimationCalls\":"<<nativeDeadeye.calls<<",\"deadeyeAnimationCompleted\":"<<nativeDeadeye.completed<<",\"deadeyeAnimationRefused\":"<<nativeDeadeye.refused
      <<",\"menuHeldTicks\":"<<menuHeldTicks<<",\"bucketPromotions\":"<<bucketPromotions<<",\"flightCaptures\":"<<flightCaptures<<",\"motorCaptures\":"<<motorCaptures<<",\"blinkCaptures\":"<<blinkCaptures<<",\"blinkBound\":"<<(blinkBound?"true":"false")<<",\"ticks\":"<<ticks<<",\"writes\":"<<writes<<",\"rejected\":"<<rejected<<",\"failures\":"<<failures
      <<",\"grounded\":"<<grounded<<",\"airborne\":"<<airborne<<",\"heldTicks\":"<<heldTicks<<",\"climbTicks\":"<<climbTicks<<",\"sessionResumes\":"<<sessionResumes<<",\"lastSequence\":"<<lastSequence
      <<",\"sourcePid\":"<<lastBody.sourcePid<<",\"guestGeneration\":"<<lastBody.generation<<",\"hostGeneration\":"<<lastBody.hostGeneration<<",\"sourceAgeMs\":"<<(haveBody?nowMs()-lastBody.wallMs:0)<<",\"hero\":"<<boundHero<<",\"modelId\":"<<boundModel<<",\"worldId\":"<<lastBody.worldId<<",\"worldTransitions\":"<<worldTransitions<<",\"worldStableTicks\":"<<worldStableTicks<<",\"worldStable\":"<<(worldStableTicks.load(std::memory_order_relaxed)>=2?"true":"false")<<",\"heroRebindings\":"<<heroRebindings<<",\"waitingForHero\":"<<waitingForHero<<",\"nativeLifetimeLab\":"<<(lifetimeLab?"true":"false")<<",\"nativeLifetimeCalls\":"<<lifetimeCalls<<",\"nativeLifetimeRefused\":"<<lifetimeRefused<<",\"nativeLifetimeThread\":"<<lifetimeThread<<",\"nativeLifetimeSequence\":"<<lifetimeHandled<<",\"mcPositionWrites\":false,\"nativePositionWrites\":true}";o.close();MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*){
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(module,dll))return 0;
    auto dir=dll.parent_path();
    base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));admin=ptr(base+0x17b7f90);
    if(!bindHero())return 0;
    const std::array<unsigned char,17> signature{0x48,0x8b,0xc4,0x48,0x89,0x58,0x18,0x55,0x56,0x57,0x48,0x81,0xec,0xa0,0,0,0};
    std::array<unsigned char,17> actual{};if(!read(base+0xa04000,actual)||actual!=signature)return 0;
    struct List{uintptr_t items;int count,capacity;} l{};
    if(!read(admin+0xf0,l)||l.count<1||l.count>l.capacity||l.capacity>32)return 0;
    for(int i=0;i<l.count;i++){auto p=ptr(l.items+i*8);if(ptr(p)==base+0x15c4e28)hooked=reinterpret_cast<void*>(p);}
    if(!hooked)return 0;
    original=*reinterpret_cast<void***>(hooked);
    if(original[0]!=reinterpret_cast<void*>(base+0xca0960)||original[1]!=reinterpret_cast<void*>(base+0xca0800)||original[2]!=reinterpret_cast<void*>(base+0xca09c0))return 0;
    mapping=OpenFileMappingW(FILE_MAP_READ,FALSE,L"Local\\OWMCPassthroughFrame");if(!mapping)return 0;
    auto view=static_cast<const unsigned char*>(MapViewOfFile(mapping,FILE_MAP_READ,0,0,4096));if(!view)return 0;
    body=view+1536;GuestBody s;if(!latest(s))return 0;
    flightMapping=CreateFileMappingW(INVALID_HANDLE_VALUE,nullptr,PAGE_READWRITE,0,256,(L"Local\\OWMCNativeFlight_"+std::to_wstring(GetCurrentProcessId())).c_str());
    if(!flightMapping||GetLastError()==ERROR_ALREADY_EXISTS)return 0;
    flightMemory=static_cast<unsigned char*>(MapViewOfFile(flightMapping,FILE_MAP_WRITE,0,0,256));if(!flightMemory)return 0;
    std::memset(flightMemory,0,256);
    HANDLE halt=CreateEventW(nullptr,TRUE,FALSE,(L"Local\\OWMCBodyStop_"+std::to_wstring(GetCurrentProcessId())).c_str());if(!halt)return 0;
    FILETIME creation{},exitTime{},kernelTime{},userTime{};ULARGE_INTEGER creationNumber{};
    if(GetProcessTimes(GetCurrentProcess(),&creation,&exitTime,&kernelTime,&userTime)){creationNumber.LowPart=creation.dwLowDateTime;creationNumber.HighPart=creation.dwHighDateTime;}
    wchar_t lab[4]{};lifetimeLab=GetEnvironmentVariableW(L"OWMC_NATIVE_LIFETIME_LAB",lab,4)==1&&lab[0]==L'1';
    if(lifetimeLab){
        auto plugin=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"inject.dll"));
        std::array<unsigned char,32> code{};constexpr std::array<unsigned char,32> signature{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20,0x48,0x8b,0x99,0x60,1,0,0,0x41,0x0f,0xb6,0xe8,0x48};
        if(!owmc::loadedClientCompanion(reinterpret_cast<HMODULE>(plugin),exe,L"inject.dll")||!read(plugin+0x7acd0,code)||code!=signature)lifetimeLab=false;
        else{lifetimeHelper=reinterpret_cast<LifetimeHelper>(plugin+0x7acd0);lifetimeLogger=plugin+0x2d04c0;lifetimeCreation=creationNumber.QuadPart;}
    }
    nativeCreation=creationNumber.QuadPart;
    std::shared_ptr<const DeadeyePresentationAck> savedDeadeye;
    std::shared_ptr<const ScrapCreditAck> savedScrap;
    std::array<std::shared_ptr<const PlacementActionAck>,5> savedPlacement;
    {std::lock_guard<std::mutex> lock(nativeHeroAudioMutex);if(!nativeHeroAudioGain.begin()){++failures;report(dir);CloseHandle(halt);return 0;}
        nativeHeroAudioGain.prepare(base,[](uintptr_t p,void* out,size_t size){SIZE_T n=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),out,size,&n)&&n==size;});}
    owned=new void*[3]{reinterpret_cast<void*>(tick),original[1],original[2]};active=true;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(hooked),owned,original)!=original){active=false;++failures;report(dir);CloseHandle(halt);return 0;}
    for(unsigned i=0;i<2880000&&active;i++){
        if(WaitForSingleObject(halt,10)!=WAIT_TIMEOUT)break;
        for(int k=1;k<=5;k++){
            PlacementActionRequest packet{};
            auto name=L"native-placement-"+std::to_wstring(k<=3?k:k+1);
            std::ifstream input(dir/(name+L"-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
            input.read(reinterpret_cast<char*>(&packet),sizeof packet);
            if(input&&input.peek()==EOF)std::atomic_store(&placementRequests[k-1],std::make_shared<const PlacementActionRequest>(packet));
            else std::atomic_store(&placementRequests[k-1],std::shared_ptr<const PlacementActionRequest>{});
            auto receipt=std::atomic_load(&placementAcks[k-1]);
            if(receipt&&receipt!=savedPlacement[k-1]){
                auto path=dir/(name+L"-ack-"+std::to_wstring(GetCurrentProcessId())+L".bin"),temp=path;temp+=L".tmp";
                std::ofstream output(temp,std::ios::binary);output.write(reinterpret_cast<const char*>(receipt.get()),sizeof *receipt);output.close();
                if(MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING))savedPlacement[k-1]=receipt;
            }
        }
        ScrapCreditRequest scrapPacket{};
        std::ifstream scrapFile(dir/(L"native-scrap-credit-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        scrapFile.read(reinterpret_cast<char*>(&scrapPacket),sizeof scrapPacket);
        if(scrapFile&&scrapFile.peek()==EOF)std::atomic_store(&scrapCreditRequest,std::make_shared<const ScrapCreditRequest>(scrapPacket));
        else std::atomic_store(&scrapCreditRequest,std::shared_ptr<const ScrapCreditRequest>{});
        auto scrapReceipt=std::atomic_load(&scrapCreditAck);
        if(scrapReceipt&&scrapReceipt!=savedScrap){
            auto path=dir/(L"native-scrap-credit-ack-"+std::to_wstring(GetCurrentProcessId())+L".bin"),temp=path;temp+=L".tmp";
            std::ofstream output(temp,std::ios::binary);output.write(reinterpret_cast<const char*>(scrapReceipt.get()),sizeof *scrapReceipt);output.close();
            if(MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING))savedScrap=scrapReceipt;
        }
        NativeShadowBinding shadowPacket{};
        std::ifstream shadowFile(dir/(L"native-shadow-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        shadowFile.read(reinterpret_cast<char*>(&shadowPacket),sizeof shadowPacket);
        if(shadowFile&&shadowFile.peek()==EOF)std::atomic_store(&shadowBinding,std::make_shared<const NativeShadowBinding>(shadowPacket));
        else std::atomic_store(&shadowBinding,std::shared_ptr<const NativeShadowBinding>{});
        NativeShadowAck shadowReceipt{};
        std::ifstream shadowReceiptFile(dir/(L"native-shadow-ack-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        shadowReceiptFile.read(reinterpret_cast<char*>(&shadowReceipt),sizeof shadowReceipt);
        if(shadowReceiptFile&&shadowReceiptFile.peek()==EOF)std::atomic_store(&shadowAck,std::make_shared<const NativeShadowAck>(shadowReceipt));
        else std::atomic_store(&shadowAck,std::shared_ptr<const NativeShadowAck>{});
        NativeWraithBinding wraithPacket{};
        std::ifstream wraithFile(dir/(L"native-wraith-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        wraithFile.read(reinterpret_cast<char*>(&wraithPacket),sizeof wraithPacket);
        if(wraithFile&&wraithFile.peek()==EOF)std::atomic_store(&wraithBinding,std::make_shared<const NativeWraithBinding>(wraithPacket));
        else std::atomic_store(&wraithBinding,std::shared_ptr<const NativeWraithBinding>{});
        NativeRecallBinding recallPacket{};
        std::ifstream recallFile(dir/(L"native-recall-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        recallFile.read(reinterpret_cast<char*>(&recallPacket),sizeof recallPacket);
        if(recallFile&&recallFile.peek()==EOF)std::atomic_store(&recallBinding,std::make_shared<const NativeRecallBinding>(recallPacket));
        else std::atomic_store(&recallBinding,std::shared_ptr<const NativeRecallBinding>{});
        NativeRecallCompletionAck recallReceipt{};
        std::ifstream recallReceiptFile(dir/(L"native-recall-ack-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        recallReceiptFile.read(reinterpret_cast<char*>(&recallReceipt),sizeof recallReceipt);
        if(recallReceiptFile&&recallReceiptFile.peek()==EOF)std::atomic_store(&recallAck,std::make_shared<const NativeRecallCompletionAck>(recallReceipt));
        else std::atomic_store(&recallAck,std::shared_ptr<const NativeRecallCompletionAck>{});
        DeadeyePresentationRequest packet{};
        std::ifstream commandFile(dir/(L"deadeye-presentation-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        commandFile.read(reinterpret_cast<char*>(&packet),sizeof packet);
        if(commandFile&&commandFile.peek()==EOF)std::atomic_store(&deadeyeRequest,std::make_shared<const DeadeyePresentationRequest>(packet));
        else std::atomic_store(&deadeyeRequest,std::shared_ptr<const DeadeyePresentationRequest>{});
        auto receipt=std::atomic_load(&deadeyeAck);
        if(receipt&&receipt!=savedDeadeye){
            auto path=dir/(L"deadeye-presentation-ack-"+std::to_wstring(GetCurrentProcessId())+L".bin"),temp=path;temp+=L".tmp";
            std::ofstream output(temp,std::ios::binary);output.write(reinterpret_cast<const char*>(receipt.get()),sizeof *receipt);output.close();
            if(MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING))savedDeadeye=receipt;
        }
        if(i%50==0){
        NativeBlinkBinding candidate{};
        std::ifstream request(dir/(L"native-blink-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
        if(request.read(reinterpret_cast<char*>(&candidate),sizeof candidate)&&request.peek()==EOF
           &&!std::memcmp(candidate.magic,"OWBLK001",8)&&candidate.version==1&&candidate.pid==GetCurrentProcessId()
           &&candidate.creation==creationNumber.QuadPart&&candidate.admin==admin)
            std::atomic_store(&blinkBinding,std::make_shared<const NativeBlinkBinding>(candidate));
        if(lifetimeLab){
            NativeLifetimeRequest command{};std::ifstream input(dir/(L"native-lifetime-lab-request-"+std::to_wstring(GetCurrentProcessId())+L".bin"),std::ios::binary);
            if(input.read(reinterpret_cast<char*>(&command),sizeof command)&&input.peek()==EOF&&command.pid==GetCurrentProcessId()&&command.creation==lifetimeCreation)
                std::atomic_store(&lifetimeBinding,std::make_shared<const NativeLifetimeRequest>(command));
        }
        }
        if(i%100==0)report(dir);
    }
    stop();report(dir);CloseHandle(halt);
    // Mapping/table/code retained until process exit for an already-entered callback.
    return 0;
}
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,void*){if(reason==DLL_PROCESS_ATTACH){module=instance;DisableThreadLibraryCalls(instance);HANDLE t=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(t)CloseHandle(t);}return TRUE;}
