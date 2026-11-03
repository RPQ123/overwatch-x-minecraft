#include "native_client_paths.hpp"
#include "render.hpp"
#include <atomic>
#include <cwctype>
#include <memory>
#include <mutex>
#include <thread>
#include <windows.h>
#include <d3d11_4.h>
#include <chrono>
#include "stream.hpp"
#include "native_collision.hpp"
#include "scene_projection.hpp"

extern "C" size_t traceContextCount(unsigned);

namespace {
using PresentFn=HRESULT(WINAPI*)(IDXGISwapChain*,UINT,UINT);
HMODULE moduleHandle;
IDXGISwapChain* attachedSwap=nullptr;
void** originalTable=nullptr;
void** copiedTable=nullptr;
PresentFn originalPresent=nullptr;
Renderer* renderer=nullptr;
Renderer* hudRenderer=nullptr;std::shared_ptr<const Mesh> pendingHud;std::shared_ptr<const Mesh> appliedHud;
std::atomic<bool> enabled{false};
std::atomic<unsigned> draws{0},failures{0};
std::atomic<unsigned> placements{0};
bool patchMode=false;
bool creativeMode=false;
bool streamedWorld=false;
struct PatchSnapshot { Mesh mesh;ULONGLONG received; };
std::shared_ptr<const PatchSnapshot> pendingPatch;
std::shared_ptr<const CollisionFrame> collisionFrame;
std::shared_ptr<const CollisionFrame> collisionSource() {return enabled?std::atomic_load(&collisionFrame):nullptr;}
std::atomic<uint64_t> appliedSession{0},appliedSequence{0},latestReceived{0};
std::atomic<unsigned> patchBlocks{0},snapshotRejects{0};
bool fakeHost=false,anchored=false;
std::atomic<bool> sceneMode{false};
std::atomic<bool> reanchorRequested{false};
bool sceneProjectionMode=false,sceneProjectionValid=false;
NativeProjection sceneProjection{};unsigned sceneProjectionFrame=0;
std::atomic<unsigned> sceneCameraCaptures{0},sceneProjectionMisses{0};
std::atomic<unsigned> presents{0},missingSceneFrames{0},staleSceneFrames{0};
std::atomic<float> sceneScaleX{0},sceneScaleY{0};
struct CameraUpload {uintptr_t identity=0;void* mapped=nullptr;std::array<float,136> values{};bool ready=false;unsigned frame=0;};
std::array<CameraUpload,8> cameraUploads{};
ID3D11DeviceContext* sceneContext=nullptr;
void **originalContextTable=nullptr,**copiedContextTable=nullptr;
ComPtr<ID3D11DepthStencilView> sceneDepth;
unsigned frameId=0,lastSceneFrame=~0u;
Vec3 anchor{};
std::wstring outputDirectory;
std::mutex errorMutex;
std::string lastError;

template<class T> bool readAt(uintptr_t address,T& value) {
    SIZE_T size=0;
    return address>=0x10000 && address<0x7fffffffffffULL
        && ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&size)
        && size==sizeof(value);
}
uintptr_t pointerAt(uintptr_t address) {
    uintptr_t value=0;return readAt(address,value)&&value>=0x10000&&value<0x7fffffffffffULL?value:0;
}
bool hostCamera(Camera& result,NativeProjection& projection) {
    uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t admin=pointerAt(base+0x17b7f90),iterators=pointerAt(admin+0xb0);
    uintptr_t list=pointerAt(iterators+0x4f*0x18),component=pointerAt(list);
    unsigned char id=0;if(!readAt(component+0x10,id)||id!=0x4f) return false;
    uintptr_t camera=pointerAt(component+0x40),view=pointerAt(camera+0x260);
    struct RawView { float data[24]; };RawView data{};
    if(!view || !readAt(view+0x10,data)) return false;
    unsigned char active=0;if(!readAt(view+0x68,active)||!active) return false;
    result={{data.data[0],data.data[1],data.data[2]},
            {data.data[4],data.data[5],data.data[6]},
            {data.data[8],data.data[9],data.data[10]},data.data[16]};
    uintptr_t crosshair=pointerAt(component+0x48);
    struct Matrices { float values[32]; } matrices{};
    int perspective=0;
    if(!crosshair||!readAt(crosshair+0x50,matrices)||!readAt(crosshair+0xd0,perspective)||perspective!=1) return false;
    std::memcpy(projection.worldToView,matrices.values,64);
    std::memcpy(projection.viewToClip,matrices.values+16,64);
    struct Viewport { float left,top,right,bottom; } viewport{};
    if(!readAt(crosshair+0x1f0,viewport)) return false;
    projection.left=viewport.left;projection.top=viewport.top;projection.right=viewport.right;projection.bottom=viewport.bottom;
    return pointerAt(base+0x17b7f90)==admin && pointerAt(camera+0x260)==view
        && pointerAt(component+0x48)==crosshair && validCamera(result)&&validProjection(projection);
}
void error(const std::exception& value) {
    ++failures;std::lock_guard<std::mutex> lock(errorMutex);lastError=value.what();
}
bool currentCamera(Camera& camera,NativeProjection& projection) {
    bool valid=true;
    if(!fakeHost) valid=hostCamera(camera,projection);
    else {
      camera={{0,0,0},{0,0,1},{0,1,0},1.2217305f};
      projection={{1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1},
                {-1,0,0,0, 0,2,0,0, 0,0,1,1, 0,0,-.1f,0},0,0,128,72};
    }
    if(sceneProjectionMode) {
        if(!sceneProjectionValid||sceneProjectionFrame!=frameId) {++sceneProjectionMisses;return false;}
        projection=sceneProjection;
    }return valid;
}
bool prepareRenderer(Camera& camera) {
    auto patch=patchMode?std::atomic_load(&pendingPatch):nullptr;
    if(patchMode&&(!patch||GetTickCount64()-patch->received>2000)) return false;
    if(!renderer) {
        ComPtr<ID3D11Device> device;
        check(attachedSwap->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())),"native device");
        renderer=new Renderer(device.Get(),patchMode?patch->mesh:loadMesh(outputDirectory+L"\\stone-mesh.bin"));
    } else if(patchMode&&(patch->mesh.session!=appliedSession||patch->mesh.sequence!=appliedSequence)) {
        renderer->update(patch->mesh);
    }
    if(patchMode) { appliedSession=patch->mesh.session;appliedSequence=patch->mesh.sequence;patchBlocks=static_cast<unsigned>(patch->mesh.blocks.size()); }
    if(reanchorRequested.exchange(false)) anchored=false;
    if(!anchored) {
        if(patchMode) {
            Vec3 flat{camera.forward.x,0,camera.forward.z};if(dot(flat,flat)<.01f) flat={0,0,1};else flat=normalized(flat);
            anchor=camera.position+flat*6;
            Vec3 foot{};anchor.y=nativeHeroFoot(foot)?foot.y:camera.position.y-1.2f;
            if(creativeMode) {anchor.x=camera.position.x;anchor.z=camera.position.z;anchor.y+=40;}
        } else anchor=camera.position+camera.forward*4.f+camera.up*.35f-Vec3{.5f,.5f,.5f};
        anchored=true;++placements;
    }
    if(patchMode) {
        auto current=std::atomic_load(&collisionFrame);
        if(!current||current->sequence!=patch->mesh.sequence||current->session!=patch->mesh.session
           ||dot(current->origin-anchor,current->origin-anchor)>.000001f) {
            std::shared_ptr<const CollisionFrame> next=std::make_shared<CollisionFrame>(CollisionFrame{
                anchor,patch->mesh.blocks,patch->received,patch->mesh.session,patch->mesh.sequence,creativeMode&&patch->mesh.creative,streamedWorld&&patch->mesh.streamedWorld});
            std::atomic_store(&collisionFrame,next);
        }
    }return true;
}
HRESULT WINAPI nativeMap(ID3D11DeviceContext* c,ID3D11Resource* resource,UINT subresource,D3D11_MAP type,UINT flags,D3D11_MAPPED_SUBRESOURCE* mapped) {
    auto result=reinterpret_cast<decltype(&nativeMap)>(originalContextTable[14])(c,resource,subresource,type,flags,mapped);
    if(enabled&&sceneProjectionMode&&SUCCEEDED(result)&&mapped&&mapped->pData&&subresource==0
       &&(type==D3D11_MAP_WRITE||type==D3D11_MAP_READ_WRITE||type==D3D11_MAP_WRITE_DISCARD||type==D3D11_MAP_WRITE_NO_OVERWRITE)) {
        ComPtr<ID3D11Buffer> buffer;
        if(SUCCEEDED(resource->QueryInterface(__uuidof(ID3D11Buffer),reinterpret_cast<void**>(buffer.GetAddressOf())))) {
            D3D11_BUFFER_DESC desc{};buffer->GetDesc(&desc);
            if(desc.ByteWidth==544&&(desc.BindFlags&D3D11_BIND_CONSTANT_BUFFER)) {
                auto id=reinterpret_cast<uintptr_t>(buffer.Get());CameraUpload* slot=nullptr;
                for(auto& upload:cameraUploads) if(upload.identity==id) slot=&upload;
                if(!slot) for(auto& upload:cameraUploads) if(!upload.identity) {slot=&upload;break;}
                if(!slot) slot=&cameraUploads[frameId%cameraUploads.size()];
                slot->identity=id;slot->mapped=mapped->pData;slot->ready=false;
            }
        }
    }return result;
}
void WINAPI nativeUnmap(ID3D11DeviceContext* c,ID3D11Resource* resource,UINT subresource) {
    if(enabled&&sceneProjectionMode&&subresource==0) {
        auto id=reinterpret_cast<uintptr_t>(resource);
        for(auto& upload:cameraUploads) if(upload.identity==id&&upload.mapped) {
            upload.ready=readAt(reinterpret_cast<uintptr_t>(upload.mapped),upload.values);upload.mapped=nullptr;upload.frame=frameId;
        }
    }
    reinterpret_cast<decltype(&nativeUnmap)>(originalContextTable[15])(c,resource,subresource);
}
void WINAPI nativeUpdate(ID3D11DeviceContext* c,ID3D11Resource* resource,UINT subresource,const D3D11_BOX* box,const void* data,UINT rowPitch,UINT depthPitch) {
    if(enabled&&sceneProjectionMode&&subresource==0&&!box&&data) {
        ComPtr<ID3D11Buffer> buffer;
        if(SUCCEEDED(resource->QueryInterface(__uuidof(ID3D11Buffer),reinterpret_cast<void**>(buffer.GetAddressOf())))) {
            D3D11_BUFFER_DESC desc{};buffer->GetDesc(&desc);
            if(desc.ByteWidth==544&&(desc.BindFlags&D3D11_BIND_CONSTANT_BUFFER)) {
                auto id=reinterpret_cast<uintptr_t>(buffer.Get());CameraUpload* slot=nullptr;
                for(auto& upload:cameraUploads) if(upload.identity==id) slot=&upload;
                if(!slot) for(auto& upload:cameraUploads) if(!upload.identity) {slot=&upload;break;}
                if(!slot) slot=&cameraUploads[frameId%cameraUploads.size()];
                slot->identity=id;slot->mapped=nullptr;slot->ready=readAt(reinterpret_cast<uintptr_t>(data),slot->values);slot->frame=frameId;
            }
        }
    }
    reinterpret_cast<decltype(&nativeUpdate)>(originalContextTable[48])(c,resource,subresource,box,data,rowPitch,depthPitch);
}
void sceneDrawing(ID3D11DeviceContext* c) {
    if(!enabled||!sceneProjectionMode||!sceneDepth) return;
    // Freeze the first verified main-depth camera for this frame. A later
    // first-person/other pass must not replace the world lens before insertion.
    if(sceneProjectionValid&&sceneProjectionFrame==frameId) return;
    ComPtr<ID3D11DepthStencilView> depth;c->OMGetRenderTargets(0,nullptr,depth.GetAddressOf());if(depth.Get()!=sceneDepth.Get()) return;
    ComPtr<ID3D11Resource> resource;depth->GetResource(resource.GetAddressOf());ComPtr<ID3D11Texture2D> texture;
    if(FAILED(resource.As(&texture))) return;D3D11_TEXTURE2D_DESC desc{};texture->GetDesc(&desc);
    UINT count=1;D3D11_VIEWPORT viewport{};c->RSGetViewports(&count,&viewport);
    if(count!=1||viewport.TopLeftX||viewport.TopLeftY||viewport.Width!=desc.Width||viewport.Height!=desc.Height) return;
    ComPtr<ID3D11Buffer> global;c->VSGetConstantBuffers(9,1,global.GetAddressOf());if(!global) return;
    auto id=reinterpret_cast<uintptr_t>(global.Get());
    for(const auto& upload:cameraUploads) if(upload.identity==id&&upload.ready&&upload.frame==frameId) {
        NativeProjection decoded{};
        if(decodeSceneProjection(upload.values,desc.Width,desc.Height,decoded)) {
            sceneProjection=decoded;sceneProjectionFrame=frameId;sceneProjectionValid=true;
            sceneScaleX=decoded.viewToClip[0];sceneScaleY=decoded.viewToClip[5];++sceneCameraCaptures;
        }
        break;
    }
}
void WINAPI nativeDraw(ID3D11DeviceContext* c,UINT n,UINT first) {sceneDrawing(c);reinterpret_cast<decltype(&nativeDraw)>(originalContextTable[13])(c,n,first);}
void WINAPI nativeIndexed(ID3D11DeviceContext* c,UINT n,UINT first,INT base) {sceneDrawing(c);reinterpret_cast<decltype(&nativeIndexed)>(originalContextTable[12])(c,n,first,base);}
void WINAPI nativeInstances(ID3D11DeviceContext* c,UINT n,UINT instances,UINT first,UINT start) {sceneDrawing(c);reinterpret_cast<decltype(&nativeInstances)>(originalContextTable[21])(c,n,instances,first,start);}
void WINAPI nativeIndexedInstances(ID3D11DeviceContext* c,UINT n,UINT instances,UINT first,INT base,UINT start) {sceneDrawing(c);reinterpret_cast<decltype(&nativeIndexedInstances)>(originalContextTable[20])(c,n,instances,first,base,start);}
void WINAPI nativeClear(ID3D11DeviceContext* context,ID3D11DepthStencilView* depth,UINT flags,FLOAT value,UINT8 stencil) {
    if(enabled.load(std::memory_order_acquire)&&sceneMode&&depth) {
        try {
            ComPtr<ID3D11Resource> resource;depth->GetResource(resource.GetAddressOf());
            ComPtr<ID3D11Texture2D> texture;
            if(SUCCEEDED(resource.As(&texture))) {
                D3D11_TEXTURE2D_DESC desc{};texture->GetDesc(&desc);
                ComPtr<ID3D11Texture2D> backbuffer;
                check(attachedSwap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(backbuffer.GetAddressOf())),"scene backbuffer");
                D3D11_TEXTURE2D_DESC bufferDesc{};backbuffer->GetDesc(&bufferDesc);
                if((flags&D3D11_CLEAR_DEPTH)&&desc.Width==bufferDesc.Width&&desc.Height==bufferDesc.Height&&desc.Format==DXGI_FORMAT_R24G8_TYPELESS)
                    sceneDepth=depth;
                if((flags&D3D11_CLEAR_STENCIL)&&!(flags&D3D11_CLEAR_DEPTH)&&depth==sceneDepth.Get()&&lastSceneFrame!=frameId) {
                    ComPtr<ID3D11RenderTargetView> color;ComPtr<ID3D11DepthStencilView> boundDepth;
                    context->OMGetRenderTargets(1,color.GetAddressOf(),boundDepth.GetAddressOf());
                    ComPtr<ID3D11Resource> targetResource;if(color) color->GetResource(targetResource.GetAddressOf());
                    UINT count=1;D3D11_VIEWPORT viewport{};context->RSGetViewports(&count,&viewport);
                    if(targetResource.Get()==backbuffer.Get()&&boundDepth.Get()==depth&&count==1&&viewport.TopLeftX==0&&viewport.TopLeftY==0
                       &&viewport.Width==bufferDesc.Width&&viewport.Height==bufferDesc.Height) {
                        Camera camera;NativeProjection projection{};
                        if(currentCamera(camera,projection)&&prepareRenderer(camera)) {
                            renderer->drawScene(color.Get(),depth,camera,anchor,projection);
                            ++draws;lastSceneFrame=frameId;
                        }
                    }
                }
            }
        } catch(const std::exception& exception) { error(exception);enabled=false; }
    }
    reinterpret_cast<decltype(&nativeClear)>(originalContextTable[53])(context,depth,flags,value,stencil);
}
bool attachSceneContext(IDXGISwapChain* swap) {
    ComPtr<ID3D11Device> device;
    if(FAILED(swap->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())))) return false;
    ComPtr<ID3D11DeviceContext> context;device->GetImmediateContext(context.GetAddressOf());
    ComPtr<ID3D11DeviceContext4> c4;ComPtr<ID3D11DeviceContext3> c3;ComPtr<ID3D11DeviceContext2> c2;ComPtr<ID3D11DeviceContext1> c1;
    unsigned version=0;
    if(SUCCEEDED(context.As(&c4))&&static_cast<void*>(c4.Get())==context.Get()) version=4;
    else if(SUCCEEDED(context.As(&c3))&&static_cast<void*>(c3.Get())==context.Get()) version=3;
    else if(SUCCEEDED(context.As(&c2))&&static_cast<void*>(c2.Get())==context.Get()) version=2;
    else if(SUCCEEDED(context.As(&c1))&&static_cast<void*>(c1.Get())==context.Get()) version=1;
    if(!version) return false;
    size_t bytes=traceContextCount(version)*sizeof(void*),read=0;
    originalContextTable=*reinterpret_cast<void***>(context.Get());copiedContextTable=new void*[traceContextCount(version)];
    if(!ReadProcessMemory(GetCurrentProcess(),originalContextTable,copiedContextTable,bytes,&read)||read!=bytes) return false;
    copiedContextTable[53]=reinterpret_cast<void*>(nativeClear);sceneContext=context.Get();sceneContext->AddRef();
    if(sceneProjectionMode) {
        copiedContextTable[14]=reinterpret_cast<void*>(nativeMap);copiedContextTable[15]=reinterpret_cast<void*>(nativeUnmap);
        copiedContextTable[48]=reinterpret_cast<void*>(nativeUpdate);
        copiedContextTable[12]=reinterpret_cast<void*>(nativeIndexed);copiedContextTable[13]=reinterpret_cast<void*>(nativeDraw);
        copiedContextTable[20]=reinterpret_cast<void*>(nativeIndexedInstances);copiedContextTable[21]=reinterpret_cast<void*>(nativeInstances);
    }
    return InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(sceneContext),copiedContextTable,originalContextTable)==originalContextTable;
}
HRESULT WINAPI present(IDXGISwapChain* swap,UINT interval,UINT flags) {
    if(sceneMode&&swap==attachedSwap&&!(flags&DXGI_PRESENT_TEST)) {
        ++presents;
        if(enabled&&lastSceneFrame!=frameId) {++missingSceneFrames;if(!latestReceived||GetTickCount64()-latestReceived>2000) ++staleSceneFrames;}
        ++frameId;
    }
    if(!sceneMode&&enabled.load(std::memory_order_acquire)&&swap==attachedSwap && !(flags&DXGI_PRESENT_TEST)) {
        try {
            Camera camera;NativeProjection projection{};
            bool valid=fakeHost;
            if(fakeHost) camera={{0,0,0},{0,0,1},{0,1,0},1.2217305f};
            else valid=hostCamera(camera,projection);
            if(valid&&prepareRenderer(camera)) {
                ComPtr<ID3D11Texture2D> target;
                check(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())),"native backbuffer");
                renderer->draw(target.Get(),camera,anchor,fakeHost?nullptr:&projection);++draws;
            }
        } catch(const std::exception& exception) { error(exception);enabled=false; }
    }
    if(creativeMode&&enabled&&swap==attachedSwap&&!(flags&DXGI_PRESENT_TEST)) {
        try {
            auto hud=std::atomic_load(&pendingHud);
            if(hud&&latestReceived&&GetTickCount64()-latestReceived<=2000) {
                if(!hudRenderer) {
                    ComPtr<ID3D11Device> device;check(swap->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())),"HUD device");
                    hudRenderer=new Renderer(device.Get(),*hud);appliedHud=hud;
                } else if(appliedHud!=hud) {hudRenderer->update(*hud);appliedHud=hud;}
                ComPtr<ID3D11Texture2D> target;check(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())),"HUD buffer");hudRenderer->drawOverlay(target.Get());
            }
        } catch(const std::exception&) {std::atomic_store(&pendingHud,std::shared_ptr<const Mesh>{});}
    }
    return originalPresent(swap,interval,flags);
}
bool attach(IDXGISwapChain* swap,bool fake) {
    if(attachedSwap) return false;
    MEMORY_BASIC_INFORMATION memory{};
    if(!VirtualQuery(swap,&memory,sizeof(memory)) || memory.State!=MEM_COMMIT || (memory.Protect&PAGE_GUARD)
       || !(memory.Protect&(PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY))) return false;
    auto* table=*reinterpret_cast<void***>(swap);
    // Retain the complete relevant COM surface; additional unused copied entries aren't invoked by us.
    auto* copy=new void*[64];SIZE_T read=0;
    if(!ReadProcessMemory(GetCurrentProcess(),table,copy,64*sizeof(void*),&read)||read!=64*sizeof(void*)) { delete[] copy;return false; }
    originalTable=table;copiedTable=copy;originalPresent=reinterpret_cast<PresentFn>(table[8]);copy[8]=reinterpret_cast<void*>(present);
    attachedSwap=swap;fakeHost=fake;swap->AddRef();enabled=true;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),copy,table)!=table) {
        enabled=false;attachedSwap=nullptr;swap->Release();return false;
    }
    if(sceneMode&&!attachSceneContext(swap)) {
        enabled=false;InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),originalTable,copiedTable);return false;
    }
    return true;
}
void stop() {
    enabled=false;
    stopNativeCollision();std::atomic_store(&collisionFrame,std::shared_ptr<const CollisionFrame>{});
    if(sceneContext) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(sceneContext),originalContextTable,copiedContextTable);
    if(attachedSwap) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(attachedSwap),originalTable,copiedTable);
    // Keep table, code and resources alive until normal process exit; an in-flight callback remains valid.
}
bool sceneVariant(const std::filesystem::path& path) {
    return path.filename()==L"owmc-render-probe-v3.dll"||path.filename()==L"owmc-render-probe-v4.dll"||path.filename()==L"owmc-render-probe-v5.dll"||path.filename()==L"owmc-render-probe-v6.dll"||path.filename()==L"owmc-render-probe-v7.dll"||path.filename()==L"owmc-render-probe-v8.dll"||path.filename()==L"owmc-render-probe-v9.dll";
}
DWORD WINAPI start(void*) {
    std::filesystem::path exe,dllPath;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dllPath))return 0;
    auto directory=dllPath.parent_path();
    outputDirectory=directory.wstring();sceneMode=sceneVariant(dllPath);
    auto filename=std::filesystem::path(dllPath).filename();
    streamedWorld=filename==L"owmc-render-probe-v9.dll";
    creativeMode=streamedWorld||filename==L"owmc-render-probe-v8.dll";
    patchMode=creativeMode||filename==L"owmc-render-probe-v5.dll"||filename==L"owmc-render-probe-v6.dll"||filename==L"owmc-render-probe-v7.dll";
    sceneProjectionMode=creativeMode||filename==L"owmc-render-probe-v7.dll";
    if(sceneProjectionMode&&!creativeMode) {
        std::array<unsigned char,36> raw{};std::ifstream preserved(directory/L"preserved-anchor.bin",std::ios::binary);
        if(preserved.read(reinterpret_cast<char*>(raw.data()),raw.size())) {
            uint64_t when=0;uint32_t pid=0,reserved=0;Vec3 position{};
            std::memcpy(&when,raw.data()+8,8);std::memcpy(&pid,raw.data()+16,4);std::memcpy(&reserved,raw.data()+20,4);std::memcpy(&position,raw.data()+24,12);
            uint64_t now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
            if(std::memcmp(raw.data(),"OWMCAN01",8)==0&&pid==GetCurrentProcessId()&&!reserved&&now>=when&&now-when<30000
               &&std::isfinite(position.x)&&std::isfinite(position.y)&&std::isfinite(position.z)
               &&std::abs(position.x)<1e6&&std::abs(position.y)<1e6&&std::abs(position.z)<1e6) {anchor=position;anchored=true;placements=1;}
        }
    }
    uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t engine=pointerAt(base+0x181e3e0),a=pointerAt(engine+0x900),b=pointerAt(a+0x2e0),c=pointerAt(b);
    uintptr_t swap=pointerAt(c+8);
    if(!swap || !attach(reinterpret_cast<IDXGISwapChain*>(swap),false)) return 0;
    if((filename==L"owmc-render-probe-v6.dll"||sceneProjectionMode)&&!attachNativeCollision(collisionSource)) {stop();return 0;}
    std::wstring eventName=L"Local\\OWMCProbeStop_"+std::to_wstring(GetCurrentProcessId());
    HANDLE halt=CreateEventW(nullptr,TRUE,FALSE,eventName.c_str());
    if(!halt) { stop();return 0; }
    std::wstring placeName=L"Local\\OWMCProbePlace_"+std::to_wstring(GetCurrentProcessId());
    HANDLE place=CreateEventW(nullptr,TRUE,FALSE,placeName.c_str());
    if(!place) { stop();CloseHandle(halt);return 0; }
    HANDLE events[]{halt,place};
    SnapshotOrder snapshotOrder;
    for(;;) {
        DWORD wait=WaitForMultipleObjects(2,events,FALSE,500);
        if(wait==WAIT_OBJECT_0||wait==WAIT_FAILED) break;
        if(wait==WAIT_OBJECT_0+1) { ResetEvent(place);reanchorRequested=true; }
        if(patchMode) {
            try {
                std::error_code ec;auto path=directory/L"patch-mesh.bin";
                if(std::filesystem::exists(path,ec)) {
                    Mesh candidate=loadMesh(path.wstring());
                    if(creativeMode&&!candidate.creative) throw std::runtime_error("Creative guest snapshot required");
                    if(streamedWorld&&!candidate.streamedWorld) throw std::runtime_error("MC generated world snapshot required");
                    uint64_t now=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
                    if(snapshotOrder.accept(candidate,now)) {
                        auto received=GetTickCount64();
                        std::shared_ptr<const PatchSnapshot> snapshot=std::make_shared<PatchSnapshot>(PatchSnapshot{std::move(candidate),received});
                        std::atomic_store(&pendingPatch,snapshot);latestReceived=received;
                    }
                }
            } catch(const std::exception&) { ++snapshotRejects; }
        }
        auto physics=nativeCollisionStats();auto collision=collisionSource();
        if(creativeMode) {
            try {
                auto hud=std::make_shared<Mesh>(loadMesh(directory/L"creative-hud.bin"));
                if(hud->vertices.size()==6&&hud->width==256&&hud->height==64) {
                    std::shared_ptr<const Mesh> accepted=hud;std::atomic_store(&pendingHud,accepted);
                }
            } catch(const std::exception&) {}
        }
        std::ofstream report(directory/(L"host-"+std::to_wstring(GetCurrentProcessId())+L".json"));
        report<<"{\"pid\":"<<GetCurrentProcessId()<<",\"enabled\":"<<(enabled?"true":"false")
              <<",\"draws\":"<<draws<<",\"failures\":"<<failures
              <<",\"anchorPlacements\":"<<placements
              <<",\"patchMode\":"<<(patchMode?"true":"false")<<",\"appliedSession\":"<<appliedSession<<",\"appliedSequence\":"<<appliedSequence
              <<",\"patchBlocks\":"<<patchBlocks<<",\"snapshotRejects\":"<<snapshotRejects
              <<",\"patchFresh\":"<<(patchMode&&latestReceived&&GetTickCount64()-latestReceived<=2000?"true":"false")
              <<",\"collisionAttached\":"<<(physics.attached?"true":"false")<<",\"collisionTicks\":"<<physics.ticks
              <<",\"collisionCorrections\":"<<physics.corrections<<",\"collisionFloors\":"<<physics.floors<<",\"collisionWalls\":"<<physics.walls
              <<",\"collisionRejected\":"<<physics.rejected<<",\"collisionWriteFailures\":"<<physics.writeFailures
              <<",\"collisionPrototypeRadius\":0.3,\"collisionPrototypeHeight\":1.8"
              <<",\"creativeMode\":"<<(creativeMode?"true":"false")<<",\"creativeEntered\":"<<(physics.creativeEntered?"true":"false")
              <<",\"streamedWorld\":"<<(streamedWorld?"true":"false")<<",\"presents\":"<<presents<<",\"missingSceneFrames\":"<<missingSceneFrames<<",\"staleSceneFrames\":"<<staleSceneFrames
              <<",\"flying\":"<<(physics.flying?"true":"false")<<",\"edgeRescues\":"<<physics.rescues
              <<",\"patchOrigin\":["<<(collision?collision->origin.x:0)<<','<<(collision?collision->origin.y:0)<<','<<(collision?collision->origin.z:0)<<']'
              <<",\"sceneCameraCaptures\":"<<sceneCameraCaptures<<",\"sceneProjectionMisses\":"<<sceneProjectionMisses
              <<",\"sceneProjectionScales\":["<<sceneScaleX<<','<<sceneScaleY<<']'
              <<",\"projectionSource\":\""<<(sceneProjectionMode?"native-scene-upload":"native-crosshair-matrices")<<"\",\"passSource\":\""<<(sceneMode?"native-stencil-boundary":"present")
              <<"\",\"nativeDepthUsed\":"<<(sceneMode&&draws>0?"true":"false")
              <<",\"hostWorldDepthVerified\":false,\"nativeWorldPassVerified\":false}";
    }
    stop();CloseHandle(place);CloseHandle(halt);return 0;
}
}

extern "C" __declspec(dllexport) BOOL OWMC_TestAttach(IDXGISwapChain* swap) {
    wchar_t exe[32768]{},dll[32768]{};GetModuleFileNameW(nullptr,exe,32768);GetModuleFileNameW(moduleHandle,dll,32768);
    if(std::filesystem::path(exe).filename()!=L"owmc-host-test.exe") return FALSE;
    outputDirectory=std::filesystem::path(dll).parent_path().wstring();sceneMode=sceneVariant(dll);
    sceneProjectionMode=std::filesystem::path(dll).filename()==L"owmc-render-probe-v7.dll"||std::filesystem::path(dll).filename()==L"owmc-render-probe-v8.dll"||std::filesystem::path(dll).filename()==L"owmc-render-probe-v9.dll";
    return attach(swap,true);
}
extern "C" __declspec(dllexport) unsigned OWMC_TestDraws() { return draws; }
extern "C" __declspec(dllexport) unsigned OWMC_TestPlacements() { return fakeHost?placements.load():0; }
extern "C" __declspec(dllexport) float OWMC_TestSceneScale() {return fakeHost?sceneProjection.viewToClip[0]:0;}
extern "C" __declspec(dllexport) void OWMC_TestStop() { stop(); }
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH) {
        moduleHandle=module;DisableThreadLibraryCalls(module);
        HANDLE worker=CreateThread(nullptr,0,start,nullptr,0,nullptr);if(worker) CloseHandle(worker);
    }
    return TRUE;
}
