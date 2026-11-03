// Original camera observation and MC composition; optional Kyoto light direction
// is camera-relative. HNZ2 suppresses Hanzo cast input through the existing
// input owner; original camera pointers and gameplay values remain untouched.
#include "native_client_paths.hpp"
#include "host_pose.hpp"
#include <d3d11_4.h>
#include <wrl/client.h>
#include <filesystem>
#include <fstream>
#include <memory>
#include <thread>
#include <iomanip>
#include <unordered_map>
#include "movement_intent.hpp"
#include "precise_wait.hpp"
#include "hero_viewmodel_lens.hpp"
#include "tracer_viewmodel_lens.hpp"
#include "native_local_hero.hpp"
#include "native_slot_filter.hpp"
#ifndef OWMC_LIVE_VERSION
#define OWMC_LIVE_VERSION 31
#endif
#ifdef OWMC_LIVE_BLEND
#include "live_world_blend.hpp"
#include "pose_warp.hpp"
#include "hud_hint_region.hpp"
#include "provided_debug_ui.hpp"
#include "native_frame_limit.hpp"
#include "native_view_light.hpp"
#include "view_light_scope.hpp"
#include "guest_body.hpp"
#include "native_deadeye_input.hpp"
#include "hanzo_control.hpp"
#include "hand_mask_trace.hpp"
#include "boss_health_overlay.hpp"
#endif
using Microsoft::WRL::ComPtr;
using namespace passthrough;
extern "C" size_t traceContextCount(unsigned);
extern "C" size_t traceSwapCount();
namespace {
HMODULE moduleHandle;IDXGISwapChain* swap=nullptr;ID3D11DeviceContext* context=nullptr;
void **oldSwap=nullptr,**newSwap=nullptr,**oldContext=nullptr,**newContext=nullptr;
std::atomic<bool> active{false},finished{false},restored{false},stopRequested{false};
std::atomic<unsigned> frames{0},poses{0},failures{0};
std::shared_ptr<const std::string> failureMessage;
void fail(const char* where,const std::exception& error) {
    auto message=std::make_shared<const std::string>(std::string(where)+": "+error.what());
    std::atomic_store(&failureMessage,message);failures++;stopRequested=true;
}
std::atomic<unsigned> presentationFps{60};
std::chrono::steady_clock::time_point nextPresentation{};
std::unique_ptr<PreciseWait> presentationWait;
std::atomic<unsigned> requestedInterval{0};
std::atomic<uint64_t> presentCpuNs{0},pacingNs{0};
std::atomic<uint64_t> drawObserveCpuNs{0},bufferObserveCpuNs{0},hudBlendCpuNs{0},presentCopyCpuNs{0},drawObservations{0};
struct CpuScope {
    std::atomic<uint64_t>& total;
    std::chrono::steady_clock::time_point start=std::chrono::steady_clock::now();
    ~CpuScope(){total+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();}
};
std::atomic<unsigned> viewMode{0}; // 1 first person, 2 native hero selection.
NativeLocalHero presentationHero;
#ifdef OWMC_LIVE_BLEND
NativeLocalHero viewmodelLensHero; // Render-owner read only, refreshed at most once per frame.
uint64_t viewmodelLensFrame=UINT64_MAX;
bool tracerViewmodelScope=false;
#endif
bool captured=false,fixture=false;UINT width=0,height=0;std::thread::id renderOwner;std::atomic<DWORD> renderThread{0};
HWND inputWindow=nullptr;WNDPROC originalWindowProc=nullptr;MovementIntent movementIntent;std::atomic<unsigned> flightKey{VK_F6};
NativeSlotFilter nativeSlotFilter;
bool deadeyeMotionScope();
bool hanzoMotionScope();
bool controlMotionScope();
bool slotFilterScope();
void revokeHanzoControls();
bool torbWeaponSelectionScope();
unsigned nativeViewMode();
bool slotInputScope(){CURSORINFO cursor{sizeof(CURSORINFO),0,nullptr,{0,0}};return active&&viewMode==1&&GetForegroundWindow()==inputWindow&&GetCursorInfo(&cursor)&&!(cursor.flags&CURSOR_SHOWING);}
LRESULT CALLBACK movementMessages(HWND w,UINT message,WPARAM key,LPARAM data) {
    if(active) {
        if(slotFilterScope()){
            if((message==WM_KEYDOWN||message==WM_KEYUP||message==WM_SYSKEYDOWN||message==WM_SYSKEYUP)&&nativeSlotFilter.blocksSlotKey(unsigned(key))){nativeSlotFilter.filteredKeys++;return 0;}
            if(weaponSlotMouse(message)){nativeSlotFilter.filteredMouse++;return 0;}
            if(controlMotionScope()&&deadeyeMotionMessage(message,unsigned(key))){
                if(message==WM_MOUSEMOVE)nativeSlotFilter.motionMouse++;else nativeSlotFilter.motionKeys++;return 0;
            }
        }
        if(message==WM_KILLFOCUS){movementIntent.release();revokeHanzoControls();}
        if(message==WM_KEYDOWN||message==WM_KEYUP||message==WM_SYSKEYDOWN||message==WM_SYSKEYUP) {
            const WPARAM keys[]{'W','S','A','D',VK_SPACE,VK_CONTROL,flightKey.load(),'V',VK_F7,VK_F8};
            for(unsigned i=0;i<10;i++)if(key==keys[i])movementIntent.key(i,message==WM_KEYDOWN||message==WM_SYSKEYDOWN,GetTickCount64());
        }
    }
    return CallWindowProcW(originalWindowProc,w,message,key,data);
}
std::unique_ptr<PosePublisher> publisher;std::shared_ptr<const HostPose> latestPose;
struct Upload {uintptr_t id=0;ComPtr<ID3D11Buffer> buffer;void* data=nullptr;std::array<float,136> values{};bool valid=false;};
std::array<Upload,64> uploads{};size_t nextUpload=0;
struct IgnoredUpload {uintptr_t id=0;ComPtr<ID3D11Buffer> buffer;};
// Retain identities to prevent address reuse. A hashed cache avoids repeated
// COM descriptor queries when the engine cycles through hundreds of buffers.
// At most 1024 * 64 KiB remains retained, with FIFO eviction.
std::array<IgnoredUpload,1024> ignoredUploads{};size_t nextIgnoredUpload=0;
std::unordered_map<uintptr_t,size_t> ignoredUploadIndex;
std::atomic<uint64_t> uploadDescriptorReads{0},ignoredUploadHits{0};
#ifdef OWMC_LIVE_BLEND
std::unique_ptr<LiveWorldBlend> blender;
std::unique_ptr<BossHealthOverlay> bossOverlay;
NativeFrameLimit nativeFrameLimit;
#ifdef OWMC_CAMERA_KEY_LIGHT
NativeViewLight nativeViewLight{NativeViewLight::Rig::CameraKey};
#else
NativeViewLight nativeViewLight;
#endif
bool fixedViewLight=false;
uint64_t viewLightMapId=0;
std::atomic<uint64_t> viewLightPending{0};
struct LightCandidate{uintptr_t address;uint64_t epoch,wallMs;};
std::shared_ptr<const LightCandidate> viewLightCandidate;
std::shared_ptr<const GuestBody> viewLightBody;
std::shared_ptr<const HanzoControlRequest> latestHanzoControl;
std::shared_ptr<const HanzoControlRequest> revokedHanzoControl;
std::atomic<uint64_t> hanzoMotionFrames{0};
struct DeadeyeInputSnapshot{uint64_t wall,observed,generation,hostGeneration,world,begin;uint32_t sourcePid,model;};
std::shared_ptr<const DeadeyeInputSnapshot> deadeyeInputSnapshot;
NativeLocalHero deadeyeInputHero; // Used only by the existing render owner.
ViewLightScope lightScope;
std::atomic<uint64_t> lightEpoch{0},lightHero{0},lightModel{0},lightWorld{0},lightBindings{0};
std::atomic<uintptr_t> lightAddress{0};
uintptr_t lastVerifiedSun=0;
std::atomic<uint64_t> lightVerifiedEpoch{0},lightPacketEpoch{0},lightSamples{0},lightLocated{0};
HudHintRegion debugBanner{true};
ProvidedDebugUi providedDebugUi;
void hideProvidedDebugUi() {
    auto plugin=GetModuleHandleW(L"inject.dll");wchar_t exe[32768]{},path[32768]{};
    if(!plugin||!GetModuleFileNameW(nullptr,exe,32768)||!GetModuleFileNameW(plugin,path,32768)
        ||_wcsicmp(path,(std::filesystem::path(exe).parent_path()/L"inject.dll").c_str())) {
        providedDebugUi.attempted=true;return;
    }
    auto bytes=[](uintptr_t at,void* out,size_t size){SIZE_T n=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),out,size,&n)&&n==size;};
    providedDebugUi.acquire(reinterpret_cast<uintptr_t>(plugin),bytes,ProvidedDebugUi::exchangeByte);
}
ComPtr<ID3D11Texture2D> handDepth;
ComPtr<ID3D11Texture2D> lastPresented;
bool handBefore=false,handAfter=false,handInvalid=false,frameBlended=false;
HandMaskTrace handMaskTrace; // Opt-in at cold attach; no extra stage queries in ordinary play.
std::shared_ptr<const WorldFrame> latestWorld;
std::array<HostPose,256> poseHistory{};
std::atomic<unsigned> blended{0},sourceRejected{0},coverageRejected{0},incompleteHands{0},sourceFrames{0},textureAllocations{0},colorUploads{0};
std::atomic<uint64_t> sourceReadCpuNs{0},sourcePolls{0},sourcePoolBusy{0};
std::atomic<unsigned> unmaskedFrames{0},heldFrames{0};
std::atomic<uint64_t> maxPoseAge{0},lastMcFrame{0},lastMcGeneration{0};
#endif
template<class T> bool read(uintptr_t a,T& v) {SIZE_T n=0;return a>=0x10000&&a<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(a),&v,sizeof v,&n)&&n==sizeof v;}
uintptr_t pointer(uintptr_t a) {uintptr_t p=0;return read(a,p)?p:0;}
// integrator/builders: the WndProc and existing filter need the same narrow gate.
bool torbWeaponSelectionScope(){
    if(fixture||!slotInputScope()||deadeyeMotionScope()||nativeViewMode()!=1)return false;
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointer(base+0x17b7f90);
    thread_local NativeLocalHero hero;
    auto readBytes=[](uintptr_t at,void* out,size_t size){SIZE_T n=0;return at>=0x10000&&at<0x7fffffffffffULL
        &&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),out,size,&n)&&n==size;};
    return hero.refresh(admin,readBytes)&&hero.hero==0x02e0000000000006ULL
        &&admin==pointer(base+0x17b7f90)&&nativeViewMode()==1&&slotInputScope()&&!deadeyeMotionScope();
}
bool deadeyeMotionScope(){
#ifdef OWMC_LIVE_BLEND
    auto s=std::atomic_load(&deadeyeInputSnapshot);auto b=std::atomic_load(&viewLightBody);auto p=std::atomic_load(&latestPose);auto now=unixMillis();
    return active&&s&&b&&p&&p->inputActive&&p->generation==s->hostGeneration&&b->deadeyeFiring
        &&b->sourcePid==s->sourcePid&&b->generation==s->generation&&b->hostGeneration==s->hostGeneration
        &&b->worldId==s->world&&b->deadeyeWorld==s->world&&b->deadeyeModel==s->model&&b->deadeyeBegin==s->begin
        &&now>=s->wall&&now-s->wall<=150&&now>=b->wallMs&&now-b->wallMs<=150&&now>=s->observed&&now-s->observed<=150;
#else
    return false;
#endif
}
#ifdef OWMC_LIVE_BLEND
bool lightRead(uintptr_t at,void* out,size_t size){SIZE_T n=0;return at>=0x10000&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),out,size,&n)&&n==size;}
bool lightWrite(uintptr_t at,const void* data,size_t size){SIZE_T n=0;return at>=0x10000&&WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),data,size,&n)&&n==size;}
void updateDeadeyeInput(const HostPose& pose){
    auto body=std::atomic_load(&viewLightBody);auto image=std::atomic_load(&latestWorld);
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),plugin=reinterpret_cast<uintptr_t>(GetModuleHandleW(L"inject.dll"));
    auto clear=[](){std::atomic_store(&deadeyeInputSnapshot,std::shared_ptr<const DeadeyeInputSnapshot>{});};
    if(fixture||!pose.inputActive||!body||!body->deadeyeFiring||!image||image->sourcePid!=body->sourcePid||image->generation!=body->generation
        ||image->hostGeneration!=pose.generation||!plugin){clear();return;}
    IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};
    if(!read(plugin,dos)||dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<0||dos.e_lfanew>0x100000
        ||!read(plugin+uintptr_t(dos.e_lfanew),nt)||nt.Signature!=IMAGE_NT_SIGNATURE||nt.OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR64_MAGIC
        ||nt.OptionalHeader.SizeOfImage<16||nt.OptionalHeader.SizeOfImage>0x20000000
        ||!deadeyeInputHero.refresh(pointer(base+0x17b7f90),lightRead)){clear();return;}
    auto now=unixMillis();DeadeyeInputContext c{GetCurrentProcessId(),image->sourcePid,image->generation,pose.generation,body->worldId,now,plugin,plugin+nt.OptionalHeader.SizeOfImage};
    if(!nativeDeadeyeInputActive(*body,c,deadeyeInputHero,lightRead)){clear();return;}
    auto state=std::make_shared<const DeadeyeInputSnapshot>(DeadeyeInputSnapshot{now,body->deadeyeObserved,body->generation,body->hostGeneration,body->worldId,body->deadeyeBegin,body->sourcePid,body->deadeyeModel});
    std::atomic_store(&deadeyeInputSnapshot,state);
}
uint64_t lightBackingScene(){
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointer(base+0x17b7f90);
    struct List{uintptr_t items;int count,capacity;} list{};
    if(!read(admin+0xd8,list)||list.count<1||list.count>list.capacity||list.capacity>128)return 0;
    for(int i=0;i<list.count;i++){
        auto system=pointer(list.items+i*8);unsigned char state=0;uint64_t map=0;
        if(pointer(system)==base+0x15c3118&&pointer(system+8)==admin&&read(system+0x10,state)&&read(system+0x20,map))return state==8&&(map==0x0800000000000664ULL||map==0x08000000000002afULL)?map:0;
    }
    return 0;
}
void updateViewLight(){
    if(!fixedViewLight)return;
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    auto pose=std::atomic_load(&latestPose);auto body=std::atomic_load(&viewLightBody);
    ViewLightIdentity identity{};
    auto now=unixMillis();
    if(viewMode==1&&pose&&body&&body->wallMs<=now&&now-body->wallMs<=250&&body->hostGeneration==pose->generation
       &&presentationHero.refresh(pointer(base+0x17b7f90),lightRead))
        identity={presentationHero.hero,presentationHero.modelId,body->sourcePid,body->generation,body->worldId};
    if(lightScope.transition(identity,pose?pose->frame:0)){
        if(!nativeViewLight.release(base,lightRead,lightWrite))throw std::runtime_error("native view light scope restoration");
        lightAddress=0;lightHero=identity.hero;lightModel=identity.model;lightWorld=identity.world;
        lightEpoch=lightScope.epoch;
        std::atomic_store(&viewLightCandidate,std::shared_ptr<const LightCandidate>{});
    }
    if(!identity.valid()||!pose)return;
    if(lightBackingScene()!=viewLightMapId){
        if(!nativeViewLight.release(base,lightRead,lightWrite))throw std::runtime_error("native view light map restoration");
        viewLightPending++;return;
    }
    // A transient camera/picker packet must not stop otherwise healthy fusion.
    // No lighting write occurs until a unique current binding is available.
    auto candidate=std::atomic_load(&viewLightCandidate);
    bool fresh=candidate&&lightScope.accepts(candidate->epoch,candidate->wallMs,now,pose->frame);
    if(fresh&&nativeViewLight.bound()&&nativeViewLight.boundAddress()!=candidate->address){
        if(!nativeViewLight.release(base,lightRead,lightWrite))throw std::runtime_error("native view light packet restoration");
        lightAddress=0;
    }
    if(!nativeViewLight.bound()){
        // Sun belongs to the unchanged OW scene, not to a hero or MC dimension.
        // A restored, previously CPU-verified scene object can bridge a short
        // missing packet, but must pass every original class/color/direction
        // guard again, then validate the current pose and last-owned bytes.
        // A different current CPU packet restores/replaces it. Packet evidence
        // is reported separately from successful scoped ownership validation.
        auto address=fresh?candidate->address:lastVerifiedSun;
        if(pose->frame<=lightScope.poseBarrier||!nativeViewLight.acquireCandidate(base,address,lightRead,viewLightMapId)){viewLightPending++;return;}
        lightAddress=nativeViewLight.boundAddress();lightBindings++;
    }
    if(fresh&&nativeViewLight.boundAddress()==candidate->address){lastVerifiedSun=candidate->address;lightPacketEpoch=lightScope.epoch;}
    if(!nativeViewLight.update(base,pose->basis,lightRead,lightWrite)){
        if(!nativeViewLight.release(base,lightRead,lightWrite))throw std::runtime_error("native view light ownership/restoration");
        lightAddress=0;
        viewLightPending++;
    }else lightVerifiedEpoch=lightScope.epoch;
}
#endif
// Reuses the existing input-filter owner. HNZ2 never changes camera pointers.
void revokeHanzoControls(){
#ifdef OWMC_LIVE_BLEND
    auto r=std::atomic_load(&latestHanzoControl);
    if(r)std::atomic_store(&revokedHanzoControl,r);
    std::atomic_store(&latestHanzoControl,std::shared_ptr<const HanzoControlRequest>{});
#endif
}
bool hanzoMotionScope(){
#ifdef OWMC_LIVE_BLEND
    if(fixture||!active)return false;
    auto r=std::atomic_load(&latestHanzoControl);auto revoked=std::atomic_load(&revokedHanzoControl);
    auto p=std::atomic_load(&latestPose);auto image=std::atomic_load(&latestWorld);auto body=std::atomic_load(&viewLightBody);
    if(!r||!p||!image||!body||(revoked&&sameHanzoCast(*r,*revoked)))return false;
    CURSORINFO cursor{sizeof(CURSORINFO),0,nullptr,{0,0}};
    bool foreground=GetForegroundWindow()==inputWindow,hidden=GetCursorInfo(&cursor)&&!(cursor.flags&CURSOR_SHOWING);
    if(!foreground||!hidden){std::atomic_store(&revokedHanzoControl,r);return false;}
    auto now=unixMillis();
    if(p->wallMs>now||now-p->wallMs>150||image->publishMs>now||now-image->publishMs>300
        ||body->wallMs>now||now-body->wallMs>150||r->guestPid!=image->sourcePid||r->generation!=image->generation
        ||r->hostGeneration!=p->generation||r->guestPid!=body->sourcePid||r->generation!=body->generation
        ||r->hostGeneration!=body->hostGeneration||r->world!=body->worldId)return false;
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));NativeLocalHero hero;
    if(!hero.refresh(pointer(base+0x17b7f90),lightRead))return false;
    HanzoControlContext c{GetCurrentProcessId(),image->sourcePid,hero.modelId,image->generation,p->generation,
        body->worldId,now,hero.hero,foreground,hidden};
    return hanzoMotionActive(*r,c);
#else
    return false;
#endif
}
bool controlMotionScope(){return deadeyeMotionScope()||hanzoMotionScope();}
bool slotFilterScope(){return slotInputScope()||hanzoMotionScope();}
unsigned nativeViewMode() {
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    auto admin=pointer(base+0x17b7f90),iterators=pointer(admin+0xb0);
    auto component=pointer(pointer(iterators+0x4f*24));
    auto view=pointer(pointer(component+0x40)+0x260),vt=pointer(view);
    if(vt==base+0x15c7000&&view==pointer(component+0x50))return 1;
    if(vt==base+0x15f2cf8)return 2;
    return 0;
}
bool isCurrentViewmodelLens(const std::array<float,136>& values){
    if(isSupportedViewmodelLens(values))return true;
#ifdef OWMC_LIVE_BLEND
    if(fixture)return false;
    const uint64_t currentFrame=uint64_t(frames.load())+1;
    if(viewmodelLensFrame!=currentFrame){
        viewmodelLensFrame=currentFrame;tracerViewmodelScope=false;
        const auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
        if(nativeViewMode()==1&&viewmodelLensHero.refresh(pointer(base+0x17b7f90),lightRead))
            tracerViewmodelScope=viewmodelLensHero.hero==0x02e0000000000003ULL&&viewmodelLensHero.modelId!=0;
        else viewmodelLensHero={};
    }
    return isTracerBlinkViewmodelLens(values,tracerViewmodelScope?viewmodelLensHero.hero:0,tracerViewmodelScope?1u:0u);
#else
    return false;
#endif
}
Upload* upload(ID3D11Resource* r) {
    auto id=reinterpret_cast<uintptr_t>(r);for(auto& u:uploads) if(u.id==id&&u.buffer) return &u;
    if(ignoredUploadIndex.find(id)!=ignoredUploadIndex.end()){ignoredUploadHits++;return nullptr;}
    ComPtr<ID3D11Buffer> buffer;if(!r||FAILED(r->QueryInterface(__uuidof(ID3D11Buffer),reinterpret_cast<void**>(buffer.GetAddressOf())))) return nullptr;
    D3D11_BUFFER_DESC d{};buffer->GetDesc(&d);uploadDescriptorReads++;
    if(d.ByteWidth!=544||!(d.BindFlags&D3D11_BIND_CONSTANT_BUFFER)) {
        if(d.ByteWidth<=64*1024){
            auto slot=nextIgnoredUpload++%ignoredUploads.size();auto& prior=ignoredUploads[slot];
            if(prior.buffer)ignoredUploadIndex.erase(prior.id);
            prior={id,std::move(buffer)};ignoredUploadIndex.emplace(id,slot);
        }
        return nullptr;
    }
    auto& u=uploads[nextUpload++%uploads.size()];u={};u.id=id;u.buffer=buffer;return &u;
}
HRESULT WINAPI map(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub,D3D11_MAP type,UINT flags,D3D11_MAPPED_SUBRESOURCE* out) {
    auto result=reinterpret_cast<decltype(&map)>(oldContext[14])(c,r,sub,type,flags,out);
    CpuScope timer{bufferObserveCpuNs};
    if(active&&SUCCEEDED(result)&&!sub&&out&&type!=D3D11_MAP_READ) if(auto* u=upload(r)) {u->data=out->pData;u->valid=false;}
    return result;
}
void WINAPI unmap(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub) {
    {CpuScope timer{bufferObserveCpuNs};
    // Successful Map guarantees these 544 bytes until the original Unmap.
    // This is an ordinary CPU copy, never a GPU readback or self-process syscall.
    if(active&&!sub) for(auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(r)&&u.data) {std::memcpy(u.values.data(),u.data,sizeof u.values);u.valid=true;u.data=nullptr;break;}
    }
    reinterpret_cast<decltype(&unmap)>(oldContext[15])(c,r,sub);
}
void WINAPI update(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub,const D3D11_BOX* box,const void* data,UINT row,UINT depth) {
    {CpuScope timer{bufferObserveCpuNs};
    if(active&&!sub&&!box&&data) if(auto* u=upload(r)) {std::memcpy(u->values.data(),data,sizeof u->values);u->valid=true;}
    }
    reinterpret_cast<decltype(&update)>(oldContext[48])(c,r,sub,box,data,row,depth);
}
void observe() {
    if(!active||captured) return;
    ComPtr<ID3D11Buffer> cb;context->VSGetConstantBuffers(9,1,cb.GetAddressOf());if(!cb) return;
    Upload* u=nullptr;for(auto& candidate:uploads) if(candidate.id==reinterpret_cast<uintptr_t>(cb.Get())&&candidate.valid) u=&candidate;
    if(!u||isCurrentViewmodelLens(u->values)) return;
    UINT count=1;D3D11_VIEWPORT vp{};context->RSGetViewports(&count,&vp);if(count!=1||vp.TopLeftX||vp.TopLeftY||vp.Width!=width||vp.Height!=height) return;
    ComPtr<ID3D11DepthStencilView> dsv;context->OMGetRenderTargets(0,nullptr,dsv.GetAddressOf());if(!dsv) return;
    ComPtr<ID3D11Resource> resource;dsv->GetResource(resource.GetAddressOf());ComPtr<ID3D11Texture2D> depth;if(FAILED(resource.As(&depth))) return;
    D3D11_TEXTURE2D_DESC d{};depth->GetDesc(&d);if(d.Width!=width||d.Height!=height) return;
    HostPose pose;if(!poseFromScene(u->values,width,height,frames.load()+1,pose)) return;
    if(renderOwner==std::thread::id{}) {renderOwner=std::this_thread::get_id();renderThread=GetCurrentThreadId();}
    if(renderOwner!=std::this_thread::get_id()) {fail("camera",std::runtime_error("Original render thread changed"));return;}
    pose.flags=fixture?2:1;pose.generation=publisher->session();pose.pid=GetCurrentProcessId();pose.wallMs=unixMillis();
    if(!fixture) {
        // Match the already-existing input owner: native menus/pause with a
        // visible cursor are not first-person movement input.
        pose.inputActive=slotInputScope()?1:0;
        pose.movementBits=movementIntent.snapshot(GetTickCount64(),pose.inputActive!=0);
        if(pose.inputActive) {const int keys[]{'W','S','A','D',VK_SPACE,VK_CONTROL,int(flightKey.load()),'V',VK_F7,VK_F8};for(unsigned i=0;i<10;i++)if(GetAsyncKeyState(keys[i])&0x8000)pose.movementBits|=1u<<i;}
#ifdef OWMC_LIVE_BLEND
        pose.inputCapabilities=nativeSlotFilter.enabled&&!nativeSlotFilter.restored?0x31594544u:0u;updateDeadeyeInput(pose);
        if(controlMotionScope())pose.movementBits&=~0x7fu;
        if(hanzoMotionScope())++hanzoMotionFrames;
#endif
    }
    publisher->publish(pose);std::shared_ptr<const HostPose> snapshot=std::make_shared<HostPose>(pose);std::atomic_store(&latestPose,snapshot);poses++;captured=true;
#ifdef OWMC_LIVE_BLEND
    if(!fixture)updateViewLight();
#endif
#ifdef OWMC_LIVE_BLEND
    poseHistory[pose.frame%poseHistory.size()]=pose;
#endif
}
#ifdef OWMC_LIVE_BLEND
bool isHand(ComPtr<ID3D11Texture2D>& depth) {
    ComPtr<ID3D11Buffer> cb;context->VSGetConstantBuffers(9,1,cb.GetAddressOf());const Upload* current=nullptr;
    for(const auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(cb.Get())&&u.valid) current=&u;
    if(!current)return false;
    bool supportedLens=isCurrentViewmodelLens(current->values);
    if(!supportedLens&&!handMaskTrace.enabled())return false;
    UINT n=1;D3D11_VIEWPORT vp{};context->RSGetViewports(&n,&vp);if(n!=1||vp.TopLeftX||vp.TopLeftY||vp.Width!=width||vp.Height!=height) return false;
    ID3D11RenderTargetView* targets[8]{};ComPtr<ID3D11DepthStencilView> dsv;context->OMGetRenderTargets(8,targets,dsv.GetAddressOf());unsigned count=0;for(auto* t:targets) if(t) {count++;t->Release();}if(count!=6||!dsv) return false;
    ComPtr<ID3D11Resource> resource;dsv->GetResource(resource.GetAddressOf());if(FAILED(resource.As(&depth))) return false;
    D3D11_TEXTURE2D_DESC d{};depth->GetDesc(&d);bool stage=d.Width==width&&d.Height==height&&d.Format==DXGI_FORMAT_R24G8_TYPELESS;
    if(stage)handMaskTrace.candidate(current->values[5],supportedLens);
    return stage&&supportedLens;
}
void observeHands() {
    // An empty native stage can draw the viewmodel before any world-camera
    // draw. Depth capture does not depend on a published world pose; blending
    // still requires that pose at the later HUD boundary.
    if(!active||handInvalid||frameBlended||viewMode==2) return;
    ComPtr<ID3D11Texture2D> depth;
    if(isHand(depth)) {
        if(handAfter) {handMaskTrace.resumed();handInvalid=true;return;} // Never merge separated first-person groups.
        if(!blender) {ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());blender=std::make_unique<LiveWorldBlend>(device.Get());}
        if(!handBefore) {handMaskTrace.start();handDepth=depth;blender->captureBefore(depth.Get());handBefore=true;}
        else if(handDepth.Get()!=depth.Get()) {handMaskTrace.depthChanged();handInvalid=true;}
    } else if(handBefore&&!handAfter) {blender->captureAfter(handDepth.Get());handAfter=true;handDepth.Reset();}
}
void blendAtHud(ID3D11DeviceContext* c,ID3D11DepthStencilView* dsv,UINT flags) {
    if(!active||!dsv||flags!=D3D11_CLEAR_STENCIL||frameBlended||!captured) return;
    ComPtr<ID3D11RenderTargetView> color;c->OMGetRenderTargets(1,color.GetAddressOf(),nullptr);if(!color) return;
    ComPtr<ID3D11Resource> resource;color->GetResource(resource.GetAddressOf());ComPtr<ID3D11Texture2D> target;
    gpuCheck(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())),"live target");if(resource.Get()!=target.Get()) return;
    if(!blender) {ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());blender=std::make_unique<LiveWorldBlend>(device.Get());}
    bool selection=viewMode==2;
    if(selection) {
        // Actual fixed selection camera: observed hero depth 0.904..0.936,
        // original background >=0.993. Copy current depth before HUD clears it;
        // no color key, static cutout, draw replay or CPU pixel readback.
        ComPtr<ID3D11Resource> depthResource;dsv->GetResource(depthResource.GetAddressOf());ComPtr<ID3D11Texture2D> depth;
        gpuCheck(depthResource.As(&depth),"selection scene depth");blender->captureSelection(depth.Get());
    }
    bool preserveHand=blender->ready()&&(selection||(!handInvalid&&handBefore&&handAfter));if(!preserveHand)unmaskedFrames++;
    handMaskTrace.decision(handBefore,handAfter,handInvalid,preserveHand);
    auto current=std::atomic_load(&latestPose);auto image=std::atomic_load(&latestWorld);
    WorldFrame testImage;
    if(fixture) {
        testImage.width=32;testImage.height=18;testImage.generation=17;testImage.mcFrame=frames.load()+1;testImage.rgba.assign(32*18*4,255);for(size_t i=0;i<testImage.rgba.size();i+=4) {testImage.rgba[i]=0;testImage.rgba[i+1]=0;}
        blender->draw(target.Get(),testImage,Matrix::identity(),preserveHand,1.f,selection?.98f:0.f);
    } else {
        auto now=unixMillis();
        // Stale/unmatched images are held without relabeling their pose. Until
        // the first MC image arrives use a neutral private scene, never old map.
        Matrix warp=image&&current?heldImageWarp(*image,*current):Matrix::identity();
        // A selection -> first-person lens jump can briefly outrun MC. The old
        // narrow image cannot cover the new view. Hold the last complete frame
        // in Present until a matching wider image arrives; this is not a fatal
        // renderer error and must not restore the original map mid-transition.
        if(!warpCoversView(warp)){coverageRejected++;return;}
        bool paired=current&&current->frame==frames.load()+1&&image&&image->hostGeneration==current->generation&&image->hostFrame&&now>=image->publishMs&&now-image->publishMs<=300;
        const HostPose* old=nullptr;
        if(paired) {old=&poseHistory[image->hostFrame%poseHistory.size()];paired=old->frame==image->hostFrame&&old->generation==image->hostGeneration&&now>=old->wallMs&&now-old->wallMs<=300;}
        if(paired) {auto desired=poseWarp(*image,*old,*current);if(!warpCoversView(desired)) coverageRejected++;warp=coverageLimitedWarp(warp,desired);auto age=now-old->wallMs;if(age>maxPoseAge) maxPoseAge=age;}
        else sourceRejected++;
        // Keep the deployed31 profile while a separate32 candidate tests the
        // suspected lifted-shadow veil. Do not change a live module in place.
        auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
        auto heroRead=[](uintptr_t at,void* data,size_t size){SIZE_T n=0;return at>=0x10000&&at<0x7fffffffffffULL&&size<=65536&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(at),data,size,&n)&&n==size;};
        bool pharah=!selection&&presentationHero.refresh(pointer(base+0x17b7f90),heroRead)&&presentationHero.hero==0x02e0000000000008ULL;
        float firstPersonExposure=pharah?1.f:1.15f;
#ifdef OWMC_NATIVE_FOREGROUND_CANDIDATE
        // The native PBR image is already tone mapped. Preserve its actual
        // black/midtone relationship instead of applying a second gamma lift.
        // Pharah's existing separate tint policy is deliberately unchanged.
        firstPersonExposure=1.f;
#endif
        if(image) {blender->draw(target.Get(),*image,warp,preserveHand,selection?1.f:firstPersonExposure,selection?.98f:0.f,pharah);lastMcFrame=image->mcFrame;lastMcGeneration=image->generation;}
        else {testImage.width=1;testImage.height=1;testImage.generation=1;testImage.mcFrame=1;testImage.rgba={24,28,32,255};blender->draw(target.Get(),testImage,warp,preserveHand,firstPersonExposure,0.f,pharah);}
    }
    if(!fixture) {
        // Preserve the actual composed terrain/hands under the native debug
        // banner, including the hero-selection view, then restore it after
        // the native HUD has drawn.
        debugBanner.capture(context,target.Get());
    }
    textureAllocations=blender->textureAllocations();colorUploads=blender->colorUploads();frameBlended=true;blended++;
}
void WINAPI clear(ID3D11DeviceContext* c,ID3D11DepthStencilView* dsv,UINT flags,FLOAT value,UINT8 stencil) {
    try {
        CpuScope timer{hudBlendCpuNs};
        // A group can end at a clear before the next draw (selection -> HUD).
        observeHands();blendAtHud(c,dsv,flags);
    }catch(const std::exception& e) {fail("render",e);}
    reinterpret_cast<decltype(&clear)>(oldContext[53])(c,dsv,flags,value,stencil);
}
#endif
void safeObserve() {CpuScope timer{drawObserveCpuNs};drawObservations++;try {observe();
#ifdef OWMC_LIVE_BLEND
    observeHands();
#endif
}catch(const std::exception& e) {fail("observe",e);}}
void WINAPI draw(ID3D11DeviceContext* c,UINT n,UINT first) {safeObserve();reinterpret_cast<decltype(&draw)>(oldContext[13])(c,n,first);}
void WINAPI indexed(ID3D11DeviceContext* c,UINT n,UINT first,INT base) {safeObserve();reinterpret_cast<decltype(&indexed)>(oldContext[12])(c,n,first,base);}
void WINAPI instances(ID3D11DeviceContext* c,UINT n,UINT instancesCount,UINT first,UINT start) {safeObserve();reinterpret_cast<decltype(&instances)>(oldContext[21])(c,n,instancesCount,first,start);}
void WINAPI indexedInstances(ID3D11DeviceContext* c,UINT n,UINT instancesCount,UINT first,INT base,UINT start) {safeObserve();reinterpret_cast<decltype(&indexedInstances)>(oldContext[20])(c,n,instancesCount,first,base,start);}
void stop() {
#ifdef OWMC_LIVE_BLEND
    std::atomic_store(&latestHanzoControl,std::shared_ptr<const HanzoControlRequest>{});
    std::atomic_store(&revokedHanzoControl,std::shared_ptr<const HanzoControlRequest>{});
#endif
    active=false;InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),oldContext,newContext);InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),oldSwap,newSwap);
    restored=*reinterpret_cast<void***>(context)==oldContext&&*reinterpret_cast<void***>(swap)==oldSwap;
    restored=nativeSlotFilter.stop()&&restored;
    if(inputWindow) {
        if(reinterpret_cast<WNDPROC>(GetWindowLongPtrW(inputWindow,GWLP_WNDPROC))==movementMessages)SetWindowLongPtrW(inputWindow,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(originalWindowProc));
        restored=restored&&reinterpret_cast<WNDPROC>(GetWindowLongPtrW(inputWindow,GWLP_WNDPROC))==originalWindowProc;movementIntent.release();
    }
#ifdef OWMC_LIVE_BLEND
    restored=nativeViewLight.release(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),lightRead,lightWrite)&&restored;
    restored=nativeFrameLimit.release()&&restored;
    restored=providedDebugUi.release(lightRead,ProvidedDebugUi::exchangeByte)&&restored;
    handDepth.Reset();lastPresented.Reset();blender.reset();bossOverlay.reset();
#endif
    for(auto& u:uploads)u={}; // Release retained buffer identities on the render owner.
    for(auto& u:ignoredUploads)u={};
    ignoredUploadIndex.clear();
    presentationWait.reset();publisher.reset();context->Release();swap->Release();context=nullptr;swap=nullptr;finished=true;
}
HRESULT WINAPI present(IDXGISwapChain* s,UINT interval,UINT flags) {
#ifdef OWMC_LIVE_BLEND
    // The provided plugin draws its configuration UI inside the downstream
    // PresentHook, after our composition. Hide its own UI flag before that call.
    // Keep its hotkey usable; do not re-force the flag every frame.
    if(active&&!fixture&&!(flags&DXGI_PRESENT_TEST)&&!providedDebugUi.attempted)hideProvidedDebugUi();
    // A missed boundary must not present one raw original-map frame. Holding
    // the last complete composed frame also holds its HUD/hand for this frame;
    // it is diagnosed separately and never relabelled as a new MC frame.
    if(active&&!(flags&DXGI_PRESENT_TEST))try {
        CpuScope timer{presentCopyCpuNs};
        ComPtr<ID3D11Texture2D> target;gpuCheck(s->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())),"present target");D3D11_TEXTURE2D_DESC d{};target->GetDesc(&d);
        if(lastPresented) {D3D11_TEXTURE2D_DESC old{};lastPresented->GetDesc(&old);if(old.Width!=d.Width||old.Height!=d.Height||old.Format!=d.Format)lastPresented.Reset();}
        if(frameBlended) {
            if(!fixture) {
                debugBanner.restore(context,target.Get());
                auto image=std::atomic_load(&latestWorld);auto now=unixMillis();
                if(viewMode==1&&image&&!image->hudRgba.empty()&&now>=image->publishMs&&now-image->publishMs<=300){
                    if(!bossOverlay){ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());bossOverlay=std::make_unique<BossHealthOverlay>(device.Get());}
                    bossOverlay->draw(target.Get(),*image);
                }
            }
            if(!lastPresented) {ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());d.BindFlags=0;d.MiscFlags=0;d.Usage=D3D11_USAGE_DEFAULT;d.CPUAccessFlags=0;gpuCheck(device->CreateTexture2D(&d,nullptr,lastPresented.GetAddressOf()),"last composed frame");}
            context->CopyResource(lastPresented.Get(),target.Get());
        } else {
            heldFrames++;
            if(lastPresented)context->CopyResource(target.Get(),lastPresented.Get());
            else {ComPtr<ID3D11RenderTargetView> view;ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());gpuCheck(device->CreateRenderTargetView(target.Get(),nullptr,view.GetAddressOf()),"neutral startup target");const FLOAT neutral[]{.094f,.110f,.125f,1};context->ClearRenderTargetView(view.Get(),neutral);}
        }
    }catch(const std::exception& e) {fail("present",e);}
#endif
    // Reserve GPU submission time for the real guest. Test presents and the
    // deterministic three-frame restoration fixture must never be paced.
    if(!fixture&&!(flags&DXGI_PRESENT_TEST)) try {
        unsigned cap=presentationFps.load();
        if(cap) {
            auto now=std::chrono::steady_clock::now();
            if(nextPresentation>now)presentationWait->wait(nextPresentation-now);
            auto woke=std::chrono::steady_clock::now();
            pacingNs+=std::chrono::duration_cast<std::chrono::nanoseconds>(woke-now).count();
            auto period=std::chrono::nanoseconds(1000000000/cap);
            nextPresentation=nextPresentation+period;
            if(nextPresentation<=woke||nextPresentation>woke+period)nextPresentation=woke+period;
        } else nextPresentation={};
    }catch(const std::exception& e) {fail("pacing",e);}
    requestedInterval=interval;
    auto beforePresent=std::chrono::steady_clock::now();
    // The composed play window has its own explicit frame pacing. Do not also
    // serialize it to the legacy engine's swap interval. Preserve test calls.
    auto result=reinterpret_cast<decltype(&present)>(oldSwap[8])(s,fixture||(flags&DXGI_PRESENT_TEST)?interval:0,flags);
#ifdef OWMC_LIVE_BLEND
    if(!fixture&&!(flags&DXGI_PRESENT_TEST))providedDebugUi.sample(lightRead);
#endif
    presentCpuNs+=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-beforePresent).count();
    if(!(flags&DXGI_PRESENT_TEST)) {
#ifdef OWMC_LIVE_BLEND
        if(captured&&!frameBlended) incompleteHands++;
        if(!frameBlended)handMaskTrace.decision(handBefore,handAfter,handInvalid,false);
        handMaskTrace.finish(frames.load()+1,unixMillis(),viewMode);
        handDepth.Reset();handBefore=false;handAfter=false;handInvalid=false;frameBlended=false;if(blender) blender->beginFrame();
#endif
        frames++;captured=false;
        if(!fixture)viewMode=nativeViewMode();
#ifdef OWMC_LIVE_BLEND
        if(!fixture&&!stopRequested)try{updateViewLight();}catch(const std::exception& e){fail("lighting",e);}
#endif
        if(stopRequested||(fixture&&frames>=3)) stop();
        else {ComPtr<ID3D11Texture2D> buffer;if(SUCCEEDED(s->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(buffer.GetAddressOf())))) {D3D11_TEXTURE2D_DESC d{};buffer->GetDesc(&d);width=d.Width;height=d.Height;}}
    }
    return result;
}
bool labCallback(void* address) {
    HMODULE owner=nullptr;wchar_t path[32768]{};
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(address),&owner)) return true;
    GetModuleFileNameW(owner,path,32768);auto name=std::filesystem::path(path).filename().wstring();
    return name.rfind(L"owmc-",0)==0||name.rfind(L"owhero-",0)==0;
}
bool attach(IDXGISwapChain* s) {
    auto reject=[](const char* why){std::atomic_store(&failureMessage,std::make_shared<const std::string>(std::string("attach: ")+why));return false;};
    if(!s||swap||finished) return reject("invalid swap or already attached");
    if(!fixture)presentationWait=std::make_unique<PreciseWait>();
    if(!fixture)viewMode=nativeViewMode();
    ComPtr<ID3D11Device> device;if(FAILED(s->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())))) return reject("GetDevice");
    ComPtr<ID3D11DeviceContext> c;device->GetImmediateContext(c.GetAddressOf());unsigned version=0;
    ComPtr<ID3D11DeviceContext4> c4;ComPtr<ID3D11DeviceContext3> c3;ComPtr<ID3D11DeviceContext2> c2;ComPtr<ID3D11DeviceContext1> c1;
    if(SUCCEEDED(c.As(&c4))&&static_cast<void*>(c4.Get())==c.Get()) version=4;else if(SUCCEEDED(c.As(&c3))&&static_cast<void*>(c3.Get())==c.Get()) version=3;
    else if(SUCCEEDED(c.As(&c2))&&static_cast<void*>(c2.Get())==c.Get()) version=2;else if(SUCCEEDED(c.As(&c1))&&static_cast<void*>(c1.Get())==c.Get()) version=1;
    if(!version) return reject("unsupported D3D context version");
    oldContext=*reinterpret_cast<void***>(c.Get());oldSwap=*reinterpret_cast<void***>(s);
    for(unsigned slot:{12u,13u,14u,15u,20u,21u,48u}) if(labCallback(oldContext[slot])) return reject("context callback already owned");
#ifdef OWMC_LIVE_BLEND
    if(labCallback(oldContext[53])) return reject("clear callback already owned");
#endif
    if(labCallback(oldSwap[8])) return reject("present callback already owned");
    ComPtr<ID3D11Texture2D> buffer;if(FAILED(s->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(buffer.GetAddressOf())))) return reject("backbuffer");
    D3D11_TEXTURE2D_DESC d{};buffer->GetDesc(&d);width=d.Width;height=d.Height;
    publisher=std::make_unique<PosePublisher>(fixture?L"Local\\OWMCHostPoseTest":L"Local\\OWMCHostPose");
#ifdef OWMC_LIVE_BLEND
    if(!fixture)publisher->put(336,uint32_t(0x325a4e48)); // HNZ2 suppression capability; rejects old free-control Guest.
#endif
    newContext=new void*[traceContextCount(version)];newSwap=new void*[traceSwapCount()];SIZE_T bytes=0;
    if(!ReadProcessMemory(GetCurrentProcess(),oldContext,newContext,traceContextCount(version)*sizeof(void*),&bytes)||bytes!=traceContextCount(version)*sizeof(void*)) return reject("copy context table");
    if(!ReadProcessMemory(GetCurrentProcess(),oldSwap,newSwap,traceSwapCount()*sizeof(void*),&bytes)||bytes!=traceSwapCount()*sizeof(void*)) return reject("copy swap table");
    newContext[12]=reinterpret_cast<void*>(indexed);newContext[13]=reinterpret_cast<void*>(draw);newContext[14]=reinterpret_cast<void*>(map);newContext[15]=reinterpret_cast<void*>(unmap);newContext[20]=reinterpret_cast<void*>(indexedInstances);newContext[21]=reinterpret_cast<void*>(instances);newContext[48]=reinterpret_cast<void*>(update);newSwap[8]=reinterpret_cast<void*>(present);
#ifdef OWMC_LIVE_BLEND
    newContext[53]=reinterpret_cast<void*>(clear);
#endif
    context=c.Get();swap=s;c->AddRef();s->AddRef();
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),newContext,oldContext)!=oldContext) return reject("context table race");
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),newSwap,oldSwap)!=oldSwap) {stop();return reject("swap table race");}
    if(!fixture) {
        DXGI_SWAP_CHAIN_DESC desc{};DWORD pid=0;
        if(FAILED(s->GetDesc(&desc))||!desc.OutputWindow||!GetWindowThreadProcessId(desc.OutputWindow,&pid)||pid!=GetCurrentProcessId()) {stop();return reject("swap output window");}
        inputWindow=desc.OutputWindow;originalWindowProc=reinterpret_cast<WNDPROC>(GetWindowLongPtrW(inputWindow,GWLP_WNDPROC));
        if(!originalWindowProc||labCallback(reinterpret_cast<void*>(originalWindowProc))) {inputWindow=nullptr;stop();return reject("window procedure");}
        SetLastError(0);auto previous=SetWindowLongPtrW(inputWindow,GWLP_WNDPROC,reinterpret_cast<LONG_PTR>(movementMessages));
        if(!previous||reinterpret_cast<WNDPROC>(previous)!=originalWindowProc) {if(previous)SetWindowLongPtrW(inputWindow,GWLP_WNDPROC,previous);inputWindow=nullptr;stop();return reject("window procedure exchange");}
    }
#ifdef OWMC_LIVE_BLEND
    if(!fixture&&!nativeFrameLimit.bindVerifiedBeta(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)))) {stop();return reject("native frame limit binding");}
    if(!fixture){viewLightMapId=lightBackingScene();fixedViewLight=viewLightMapId!=0;}
#endif
    if(!fixture){auto library=GetModuleHandleW(L"minhook.x64.dll");wchar_t location[32768]{},exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);
        if(!library||!GetModuleFileNameW(library,location,32768)||_wcsicmp(location,(std::filesystem::path(exe).parent_path()/L"minhook.x64.dll").c_str())||!nativeSlotFilter.start(slotFilterScope,library,controlMotionScope,torbWeaponSelectionScope)){stop();return reject("native slot input filter");}}
#ifdef OWMC_LIVE_BLEND
    std::error_code traceError;wchar_t tracePath[32768]{};bool traceRequested=false;
    if(!fixture&&GetModuleFileNameW(moduleHandle,tracePath,32768)){
        auto project=std::filesystem::path(tracePath).parent_path().parent_path().parent_path();
        traceRequested=std::filesystem::exists(project/L"research"/L"enable-hand-mask-trace.txt",traceError)&&!traceError;
    }
    handMaskTrace=HandMaskTrace(traceRequested);
#endif
    active=true;return true;
}
void report(const std::filesystem::path& dir) {
    const char* prefix=
#ifdef OWMC_LIVE_BLEND
    "world-live-";
#else
    "host-pose-";
#endif
    auto file=dir/(prefix+std::to_string(GetCurrentProcessId())+".json"),temp=file;temp+=L".tmp";
    std::ofstream out(temp);out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"probeVersion\":"<<OWMC_LIVE_VERSION<<",\"enabled\":"<<(active?"true":"false")<<",\"restored\":"<<(restored?"true":"false")<<",\"frames\":"<<frames<<",\"poses\":"<<poses<<",\"failures\":"<<failures;
    auto error=std::atomic_load(&failureMessage);if(error)out<<",\"failureMessage\":"<<std::quoted(*error);
    auto pose=std::atomic_load(&latestPose);if(pose) {out<<",\"generation\":"<<pose->generation<<",\"lastFrame\":"<<pose->frame<<",\"fov\":"<<pose->fov<<",\"basis\":[";for(int i=0;i<9;i++) {if(i) out<<',';out<<pose->basis[i];}out<<']';}
#ifdef OWMC_LIVE_BLEND
#ifdef OWMC_NATIVE_FOREGROUND_CANDIDATE
    out<<",\"nativeForegroundGammaLift\":false";
#else
    out<<",\"nativeForegroundGammaLift\":true";
#endif
#ifdef OWMC_CAMERA_KEY_LIGHT
    out<<",\"viewLightRig\":\"camera-key\"";
#else
    out<<",\"viewLightRig\":\"overhead\"";
#endif
    out<<",\"nativeFrameLimitRaised\":"<<(nativeFrameLimit.owned?"true":"false")<<",\"nativeFrameLimitRestored\":"<<(nativeFrameLimit.restored?"true":"false");
    out<<",\"providedDebugUiAttempted\":"<<(providedDebugUi.attempted?"true":"false")<<",\"providedDebugUiVerified\":"<<(providedDebugUi.verified?"true":"false")
       <<",\"providedDebugUiHidden\":"<<(providedDebugUi.hidden?"true":"false")<<",\"providedDebugUiOwned\":"<<(providedDebugUi.owned?"true":"false")
       <<",\"providedDebugUiRestored\":"<<(providedDebugUi.restored?"true":"false");
    out<<",\"fixedKyotoLight\":"<<(fixedViewLight&&viewLightMapId==0x0800000000000664ULL?"true":"false")<<",\"fixedViewLight\":"<<(fixedViewLight?"true":"false")<<",\"viewLightMapId\":"<<viewLightMapId<<",\"viewLightOwned\":"<<(nativeViewLight.owned?"true":"false")<<",\"viewLightRestored\":"<<(nativeViewLight.restored?"true":"false")<<",\"viewLightUpdates\":"<<nativeViewLight.updates<<",\"viewLightPending\":"<<viewLightPending;
    out<<",\"sourceReadCpuNs\":"<<sourceReadCpuNs<<",\"sourcePolls\":"<<sourcePolls<<",\"sourcePoolBusy\":"<<sourcePoolBusy;
    out<<",\"viewLightEpoch\":"<<lightEpoch<<",\"viewLightHero\":"<<lightHero<<",\"viewLightModelId\":"<<lightModel<<",\"viewLightWorldId\":"<<lightWorld<<",\"viewLightAddress\":"<<lightAddress<<",\"viewLightBindings\":"<<lightBindings;
    out<<",\"viewLightVerifiedEpoch\":"<<lightVerifiedEpoch<<",\"viewLightPacketEpoch\":"<<lightPacketEpoch<<",\"viewLightSamples\":"<<lightSamples<<",\"viewLightLocated\":"<<lightLocated;
    out<<",\"blended\":"<<blended<<",\"sourceRejected\":"<<sourceRejected<<",\"coverageRejected\":"<<coverageRejected<<",\"unblendedPoses\":"<<incompleteHands<<",\"unmaskedFrames\":"<<unmaskedFrames<<",\"heldFrames\":"<<heldFrames<<",\"sourceFrames\":"<<sourceFrames<<",\"textureAllocations\":"<<textureAllocations<<",\"colorUploads\":"<<colorUploads<<",\"maxPoseAgeMs\":"<<maxPoseAge<<",\"lastMcFrame\":"<<lastMcFrame<<",\"lastMcGeneration\":"<<lastMcGeneration<<",\"nativeDrawingModified\":true,\"gpuReadbacks\":0";
#else
    out<<",\"nativeDrawingModified\":false";
#endif
    out<<",\"uploadDescriptorReads\":"<<uploadDescriptorReads<<",\"ignoredUploadHits\":"<<ignoredUploadHits;
#ifdef OWMC_LIVE_BLEND
    out<<",\"renderThread\":"<<renderThread<<",\"scriptNotificationOwner\":\"body-sync\"";
#endif
    out<<",\"slotInputFilter\":"<<(nativeSlotFilter.enabled?"true":"false")<<",\"slotInputRestored\":"<<(nativeSlotFilter.restored?"true":"false")<<",\"slotFilteredKeys\":"<<nativeSlotFilter.filteredKeys<<",\"slotFilteredMouse\":"<<nativeSlotFilter.filteredMouse<<",\"slotBufferCalls\":"<<nativeSlotFilter.bufferCalls<<",\"slotDataCalls\":"<<nativeSlotFilter.dataCalls<<",\"slotKeyQueries\":"<<nativeSlotFilter.keyQueries<<",\"slotMessageCalls\":"<<nativeSlotFilter.messageCalls;
#ifdef OWMC_LIVE_BLEND
    // HNZ2 diagnostics exist only with the live compositor input owner.
    out<<",\"hanzoControlProtocol\":2,\"hanzoCameraSelections\":0,\"hanzoMotionLocked\":"<<(hanzoMotionScope()?"true":"false")<<",\"hanzoMotionFrames\":"<<hanzoMotionFrames.load();
#endif
    out<<",\"deadeyeInputProtocol\":1,\"deadeyeInputGuardAvailable\":"<<(active&&nativeSlotFilter.enabled&&!nativeSlotFilter.restored?"true":"false")<<",\"deadeyeMotionLocked\":"<<(deadeyeMotionScope()?"true":"false")<<",\"deadeyeMotionKeys\":"<<nativeSlotFilter.motionKeys<<",\"deadeyeMotionMouse\":"<<nativeSlotFilter.motionMouse;
#ifdef OWMC_LIVE_BLEND
    out<<",\"handMaskTraceEnabled\":"<<(handMaskTrace.enabled()?"true":"false")<<",\"handMaskTrace\":[";
    if(auto trace=handMaskTrace.snapshot())for(unsigned i=0;i<trace->count;i++){
        const auto& row=trace->rows[i];if(i)out<<',';
        out<<"{\"frame\":"<<row.frame<<",\"wall\":"<<row.wall<<",\"viewMode\":"<<row.viewMode<<",\"stageCandidates\":"<<row.stageCandidates
           <<",\"lensRejected\":"<<row.lensRejected<<",\"handDraws\":"<<row.handDraws<<",\"minLens\":"<<row.minLens<<",\"maxLens\":"<<row.maxLens
           <<",\"starts\":"<<row.starts<<",\"resumed\":"<<row.resumed<<",\"depthChanges\":"<<row.depthChanges<<",\"before\":"<<(row.before?"true":"false")
           <<",\"after\":"<<(row.after?"true":"false")<<",\"invalid\":"<<(row.invalid?"true":"false")<<",\"preserved\":"<<(row.preserved?"true":"false")<<'}';
    }
    out<<']';
#endif
    out<<",\"viewMode\":"<<viewMode<<",\"presentationFps\":"<<presentationFps<<",\"requestedSyncInterval\":"<<requestedInterval<<",\"presentCpuNs\":"<<presentCpuNs<<",\"pacingNs\":"<<pacingNs;
    out<<",\"drawObserveCpuNs\":"<<drawObserveCpuNs<<",\"bufferObserveCpuNs\":"<<bufferObserveCpuNs<<",\"hudBlendCpuNs\":"<<hudBlendCpuNs<<",\"presentCopyCpuNs\":"<<presentCopyCpuNs<<",\"drawObservations\":"<<drawObservations<<",\"sampleWallMs\":"<<unixMillis()<<",\"movementModified\":false}";out.close();MoveFileExW(temp.c_str(),file.c_str(),MOVEFILE_REPLACE_EXISTING);
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dll))return 0;
    auto dir=dll.parent_path();
    try {auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),engine=pointer(base+0x181e3e0),p=pointer(engine+0x900),q=pointer(p+0x2e0),r=pointer(q);
        if(!attach(reinterpret_cast<IDXGISwapChain*>(pointer(r+8)))) {failures++;report(dir);return 0;}
        HANDLE event=CreateEventW(nullptr,TRUE,FALSE,(
#ifdef OWMC_LIVE_BLEND
        L"Local\\OWMCLiveStop_"
#else
        L"Local\\OWMCPoseStop_"
#endif
        +std::to_wstring(GetCurrentProcessId())).c_str());auto started=GetTickCount64(),last=started;
#ifdef OWMC_LIVE_BLEND
        std::unique_ptr<WorldFrames> reader;WorldFramePool framePool;uint64_t knownGeneration=0,knownSequence=0,retryAt=0;
#endif
        PreciseWait sourceWait;
#ifdef OWMC_LIVE_BLEND
        uint64_t nextLightSample=0;
#endif
        while(!finished) {if(sourceWait.wait(std::chrono::milliseconds(1),event)||GetTickCount64()-started>
#ifdef OWMC_LIVE_BLEND
            28800000
#else
            120000
#endif
            ) stopRequested=true;
#ifdef OWMC_LIVE_BLEND
            // The command packet exists during CPU recording, outside the GPU
            // callbacks on this beta. This already-existing worker only reads
            // a candidate; all validation, writes and restoration stay on the
            // one existing render owner.
            if(fixedViewLight&&viewMode==1&&GetTickCount64()>=nextLightSample){
                nextLightSample=GetTickCount64()+(nativeViewLight.owned.load()?16:2);
                auto epoch=lightEpoch.load();
                lightSamples++;
                if(auto candidate=NativeViewLight::locate(base,lightRead)){
                    lightLocated++;
                    auto sample=std::make_shared<const LightCandidate>(LightCandidate{candidate,epoch,unixMillis()});
                    if(epoch==lightEpoch.load())std::atomic_store(&viewLightCandidate,sample);
                }
            }
            if(GetTickCount64()>=retryAt) try {
                CpuScope readTimer{sourceReadCpuNs};sourcePolls++;
                if(!reader) reader=std::make_unique<WorldFrames>();
                if(!fixture){std::array<unsigned char,256> packet{};if(reader->bodyPacket(packet)){
                    try {auto body=std::make_shared<const GuestBody>(decodeGuestBody(packet.data(),unixMillis(),GetCurrentProcessId()));std::atomic_store(&viewLightBody,body);auto hanzo=decodeHanzoControl(packet.data());std::atomic_store(&latestHanzoControl,hanzo.model?std::make_shared<const HanzoControlRequest>(hanzo):std::shared_ptr<const HanzoControlRequest>{});}catch(const std::exception&){}
                }}
                auto image=framePool.acquire();if(!image)sourcePoolBusy++;if(image&&reader->latestInto(*image,knownGeneration,knownSequence)) {knownGeneration=image->generation;knownSequence=image->sequence;std::shared_ptr<const WorldFrame> snapshot=std::move(image);std::atomic_store(&latestWorld,snapshot);sourceFrames++;}
            }catch(const std::exception&) {reader.reset();retryAt=GetTickCount64()+250;}
#endif
            if(GetTickCount64()-last>500) {
                unsigned cap=60;std::ifstream settings(dir/"presentation-fps.txt");
                if(settings){unsigned requested=0;if(settings>>requested&&(requested==0||(requested>=30&&requested<=240)))cap=requested;}
                unsigned key=VK_F6;std::ifstream keySettings(dir/"flight-key.txt");if(!(keySettings>>key)||key<VK_F6||key>VK_F10)key=VK_F6;
                if(flightKey.exchange(key)!=key)movementIntent.release();
                presentationFps=cap;report(dir);last=GetTickCount64();}}
        report(dir);if(event) CloseHandle(event);
    }catch(const std::exception&) {failures++;report(dir);}
    return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_HandDepthTestAttach(IDXGISwapChain* s) {wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-hand-depth-test.exe") return FALSE;fixture=true;return attach(s);}
extern "C" __declspec(dllexport) BOOL OWMC_SelectionTestAttach(IDXGISwapChain* s) {wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);if(std::filesystem::path(exe).filename()!=L"owmc-hand-depth-test.exe")return FALSE;fixture=true;viewMode=2;return attach(s);}
extern "C" __declspec(dllexport) void OWMC_HandDepthTestDump() {}
extern "C" __declspec(dllexport) BOOL OWMC_HandDepthTestVerify() {auto p=std::atomic_load(&latestPose);return finished&&restored&&frames==3&&poses==3&&!failures&&p&&std::abs(p->fov-70)<.01f&&p->flags==2
#ifdef OWMC_LIVE_BLEND
    &&ignoredUploadHits>=20&&[](){for(const auto& u:ignoredUploads)if(u.buffer)return false;return true;}()
    &&blended==2&&unmaskedFrames==(viewMode==2?0u:1u)&&heldFrames==1
#endif
    ;}
BOOL WINAPI DllMain(HMODULE m,DWORD reason,LPVOID) {if(reason==DLL_PROCESS_ATTACH) {moduleHandle=m;DisableThreadLibraryCalls(m);HANDLE t=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(t) CloseHandle(t);}return TRUE;}
