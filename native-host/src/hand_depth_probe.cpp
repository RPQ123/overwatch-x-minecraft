// Three-frame observation only: copy original depth around the native first-person
// draw group. No native draw replay, shaders, output bindings or game state writes.
#include "native_client_paths.hpp"
#include "frame_compositor.hpp"
#include <d3d11_4.h>
#include <filesystem>
#include <fstream>
#include <memory>
#ifdef OWMC_WORLD_BLEND
#include "world_blend.hpp"
#endif

extern "C" size_t traceContextCount(unsigned);
extern "C" size_t traceSwapCount();
using namespace passthrough;
namespace {
HMODULE moduleHandle;
IDXGISwapChain* swap=nullptr;ID3D11DeviceContext* context=nullptr;
void **oldSwap=nullptr,**newSwap=nullptr,**oldContext=nullptr,**newContext=nullptr;
std::atomic<bool> active{false},finished{false},restored{false};std::atomic<unsigned> frame{0},failures{0};
UINT width=0,height=0;unsigned handDraws=0;
ComPtr<ID3D11Texture2D> backbuffer,handDepth;
struct Upload {uintptr_t id=0;void* data=nullptr;std::array<float,136> values{};bool valid=false;};
std::array<Upload,64> uploads{};
struct Image {std::string name;UINT width,height,format;std::vector<unsigned char> bytes;};
std::vector<Image> images;
bool before=false,after=false,boundary=false,finalImage=false;
bool worldBlended=false;uint64_t guestGeneration=0,guestFrame=0;UINT guestPid=0;
std::thread::id renderThread;
template<class T> bool read(uintptr_t address,T& value) {SIZE_T n=0;return address>=0x10000&&address<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&n)&&n==sizeof(value);}
uintptr_t pointer(uintptr_t a) {uintptr_t v=0;return read(a,v)?v:0;}
Upload* upload(ID3D11Resource* r) {
    ComPtr<ID3D11Buffer> b;if(!r||FAILED(r->QueryInterface(__uuidof(ID3D11Buffer),reinterpret_cast<void**>(b.GetAddressOf())))) return nullptr;
    D3D11_BUFFER_DESC d{};b->GetDesc(&d);if(d.ByteWidth!=544||!(d.BindFlags&D3D11_BIND_CONSTANT_BUFFER)) return nullptr;
    auto id=reinterpret_cast<uintptr_t>(r);for(auto& u:uploads) if(u.id==id) return &u;
    for(auto& u:uploads) if(!u.id) {u.id=id;return &u;}
    return nullptr;
}
HRESULT WINAPI map(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub,D3D11_MAP type,UINT flags,D3D11_MAPPED_SUBRESOURCE* out) {
    auto hr=reinterpret_cast<decltype(&map)>(oldContext[14])(c,r,sub,type,flags,out);
    if(active&&SUCCEEDED(hr)&&sub==0&&out&&type!=D3D11_MAP_READ) if(auto* u=upload(r)) {u->data=out->pData;u->valid=false;}
    return hr;
}
void WINAPI unmap(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub) {
    if(active&&sub==0) for(auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(r)&&u.data) {u.valid=read(reinterpret_cast<uintptr_t>(u.data),u.values);u.data=nullptr;break;}
    reinterpret_cast<decltype(&unmap)>(oldContext[15])(c,r,sub);
}
void WINAPI update(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub,const D3D11_BOX* box,const void* data,UINT row,UINT depth) {
    if(active&&sub==0&&!box&&data) if(auto* u=upload(r)) u->valid=read(reinterpret_cast<uintptr_t>(data),u->values);
    reinterpret_cast<decltype(&update)>(oldContext[48])(c,r,sub,box,data,row,depth);
}
void capture(ID3D11Texture2D* source,const char* name) {
    if(renderThread==std::thread::id{}) renderThread=std::this_thread::get_id();
    if(renderThread!=std::this_thread::get_id()) throw std::runtime_error("Multiple render context threads");
    D3D11_TEXTURE2D_DESC d{};source->GetDesc(&d);
    if(d.Width!=width||d.Height!=height||d.SampleDesc.Count!=1||d.ArraySize!=1||d.MipLevels!=1||width>4096||height>2160) throw std::runtime_error("Unsupported observation surface");
    if(d.Format!=DXGI_FORMAT_R24G8_TYPELESS&&d.Format!=DXGI_FORMAT_R8G8B8A8_UNORM&&d.Format!=DXGI_FORMAT_R8G8B8A8_UNORM_SRGB&&d.Format!=DXGI_FORMAT_B8G8R8A8_UNORM) throw std::runtime_error("Unsupported observation format");
    ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());d.Usage=D3D11_USAGE_STAGING;d.BindFlags=0;d.CPUAccessFlags=D3D11_CPU_ACCESS_READ;d.MiscFlags=0;
    ComPtr<ID3D11Texture2D> staging;gpuCheck(device->CreateTexture2D(&d,nullptr,staging.GetAddressOf()),"depth observation staging");
    context->CopyResource(staging.Get(),source);D3D11_MAPPED_SUBRESOURCE m{};gpuCheck(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&m),"depth observation readback");
    Image image{name,width,height,UINT(d.Format),std::vector<unsigned char>(size_t(width)*height*4)};
    for(UINT y=0;y<height;y++) std::memcpy(image.bytes.data()+size_t(y)*width*4,static_cast<unsigned char*>(m.pData)+size_t(y)*m.RowPitch,width*4);
    context->Unmap(staging.Get(),0);images.push_back(std::move(image));
}
bool isHand(ComPtr<ID3D11Texture2D>& depth) {
    ComPtr<ID3D11Buffer> cb;context->VSGetConstantBuffers(9,1,cb.GetAddressOf());Upload* current=nullptr;
    for(auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(cb.Get())&&u.valid) current=&u;
    if(!current||std::abs(current->values[0]+1.12820041f)>.002f||std::abs(current->values[5]-2.00568986f)>.002f) return false;
    UINT n=1;D3D11_VIEWPORT vp{};context->RSGetViewports(&n,&vp);
    if(n!=1||vp.TopLeftX||vp.TopLeftY||vp.Width!=width||vp.Height!=height) return false;
    ID3D11RenderTargetView* targets[8]{};ComPtr<ID3D11DepthStencilView> dsv;context->OMGetRenderTargets(8,targets,dsv.GetAddressOf());unsigned count=0;
    for(auto* t:targets) if(t) {count++;t->Release();}
    if(count!=6||!dsv) return false;
    ComPtr<ID3D11Resource> resource;dsv->GetResource(resource.GetAddressOf());if(FAILED(resource.As(&depth))) return false;
    D3D11_TEXTURE2D_DESC d{};depth->GetDesc(&d);return d.Width==width&&d.Height==height&&d.Format==DXGI_FORMAT_R24G8_TYPELESS;
}
#ifdef OWMC_WORLD_BLEND
void blendWorld() {
    if(!before||!after||images.size()!=3||images[0].name!="before-hand-depth"||images[1].name!="after-hand-depth") throw std::runtime_error("Incomplete same-frame hand mask");
    std::vector<unsigned char> mask(size_t(width)*height);size_t changed=0;
    for(size_t i=0;i<mask.size();i++) {bool hit=(field<uint32_t>(images[0].bytes.data(),i*4)&0xffffff)!=(field<uint32_t>(images[1].bytes.data(),i*4)&0xffffff);mask[i]=hit?255:0;changed+=hit;}
    if(!changed||changed>mask.size()/2) throw std::runtime_error("Unverified hand-mask coverage");
    WorldFrame source;
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);
    if(std::filesystem::path(exe).filename()==L"owmc-hand-depth-test.exe") {
        source.width=32;source.height=18;source.rgba.assign(32*18*4,255);
        for(size_t i=0;i<source.rgba.size();i+=4) {source.rgba[i]=0;source.rgba[i+1]=0;}
    } else {
        WorldFrames reader;if(!reader.latest(source)) throw std::runtime_error("No fresh completed guest frame");
        guestGeneration=source.generation;guestFrame=source.mcFrame;guestPid=source.sourcePid;
    }
    ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());
    {WorldBlend compositor(device.Get());compositor.draw(backbuffer.Get(),source,mask);}
    capture(backbuffer.Get(),"world-blended");worldBlended=true;
}
#endif
void observeBeforeDraw() {
    if(!active||frame!=1||after) return;
    try {ComPtr<ID3D11Texture2D> depth;
        if(isHand(depth)) {
            if(!before) {handDepth=depth;capture(depth.Get(),"before-hand-depth");before=true;}
            if(depth.Get()!=handDepth.Get()) throw std::runtime_error("First-person depth identity changed");
            handDraws++;
        } else if(before) {capture(handDepth.Get(),"after-hand-depth");after=true;}
    } catch(const std::exception&) {failures++;active=false;}
}
void WINAPI indexed(ID3D11DeviceContext* c,UINT n,UINT first,INT base) {observeBeforeDraw();reinterpret_cast<decltype(&indexed)>(oldContext[12])(c,n,first,base);}
void WINAPI draw(ID3D11DeviceContext* c,UINT n,UINT first) {observeBeforeDraw();reinterpret_cast<decltype(&draw)>(oldContext[13])(c,n,first);}
void WINAPI indexedInstances(ID3D11DeviceContext* c,UINT n,UINT instances,UINT first,INT base,UINT start) {observeBeforeDraw();reinterpret_cast<decltype(&indexedInstances)>(oldContext[20])(c,n,instances,first,base,start);}
void WINAPI instances(ID3D11DeviceContext* c,UINT n,UINT instancesCount,UINT first,UINT start) {observeBeforeDraw();reinterpret_cast<decltype(&instances)>(oldContext[21])(c,n,instancesCount,first,start);}
void WINAPI clear(ID3D11DeviceContext* c,ID3D11DepthStencilView* dsv,UINT flags,FLOAT value,UINT8 stencil) {
    if(active&&frame==1&&dsv&&flags==D3D11_CLEAR_STENCIL&&!boundary) {
        ComPtr<ID3D11RenderTargetView> color;c->OMGetRenderTargets(1,color.GetAddressOf(),nullptr);ComPtr<ID3D11Resource> r;if(color) color->GetResource(r.GetAddressOf());
        if(r.Get()==backbuffer.Get()) try {
#ifdef OWMC_SELECTION_DEPTH
            ComPtr<ID3D11Resource> depthResource;dsv->GetResource(depthResource.GetAddressOf());ComPtr<ID3D11Texture2D> depth;
            gpuCheck(depthResource.As(&depth),"selection final depth");capture(depth.Get(),"scene-depth");
#endif
            capture(backbuffer.Get(),"before-hud");boundary=true;
#ifdef OWMC_WORLD_BLEND
            blendWorld();
#endif
        }catch(const std::exception&) {failures++;active=false;}
    }
    reinterpret_cast<decltype(&clear)>(oldContext[53])(c,dsv,flags,value,stencil);
}
void stop() {
    active=false;
    if(context) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),oldContext,newContext);
    if(swap) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),oldSwap,newSwap);
    restored=context&&swap&&*reinterpret_cast<void***>(context)==oldContext&&*reinterpret_cast<void***>(swap)==oldSwap;
    // Original resources must not remain referenced by the lab after restoration:
    // retaining the swapchain buffer would prevent a later native ResizeBuffers.
    handDepth.Reset();backbuffer.Reset();
    if(context) context->Release();
    if(swap) swap->Release();
    context=nullptr;swap=nullptr;
    finished=true;
}
HRESULT WINAPI present(IDXGISwapChain* s,UINT interval,UINT flags) {
    if(active&&frame==1&&!(flags&DXGI_PRESENT_TEST)) try {
        if(before&&!after) {capture(handDepth.Get(),"after-hand-depth");after=true;}
        capture(backbuffer.Get(),"final");finalImage=true;
    } catch(const std::exception&) {failures++;active=false;}
    HRESULT hr=reinterpret_cast<decltype(&present)>(oldSwap[8])(s,interval,flags);
    if(!(flags&DXGI_PRESENT_TEST)&&++frame>=3) stop();
    return hr;
}
bool attach(IDXGISwapChain* s) {
    if(swap||finished||!s) return false;
    ComPtr<ID3D11Device> device;if(FAILED(s->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())))) return false;
    ComPtr<ID3D11DeviceContext> c;device->GetImmediateContext(c.GetAddressOf());unsigned version=0;
    ComPtr<ID3D11DeviceContext4> c4;ComPtr<ID3D11DeviceContext3> c3;ComPtr<ID3D11DeviceContext2> c2;ComPtr<ID3D11DeviceContext1> c1;
    if(SUCCEEDED(c.As(&c4))&&static_cast<void*>(c4.Get())==c.Get()) version=4;
    else if(SUCCEEDED(c.As(&c3))&&static_cast<void*>(c3.Get())==c.Get()) version=3;
    else if(SUCCEEDED(c.As(&c2))&&static_cast<void*>(c2.Get())==c.Get()) version=2;
    else if(SUCCEEDED(c.As(&c1))&&static_cast<void*>(c1.Get())==c.Get()) version=1;
    if(!version||FAILED(s->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(backbuffer.GetAddressOf())))) return false;
    D3D11_TEXTURE2D_DESC d{};backbuffer->GetDesc(&d);width=d.Width;height=d.Height;
    oldContext=*reinterpret_cast<void***>(c.Get());oldSwap=*reinterpret_cast<void***>(s);
    newContext=new void*[traceContextCount(version)];newSwap=new void*[traceSwapCount()];SIZE_T bytes=0;
    if(!ReadProcessMemory(GetCurrentProcess(),oldContext,newContext,traceContextCount(version)*sizeof(void*),&bytes)||bytes!=traceContextCount(version)*sizeof(void*)) return false;
    if(!ReadProcessMemory(GetCurrentProcess(),oldSwap,newSwap,traceSwapCount()*sizeof(void*),&bytes)||bytes!=traceSwapCount()*sizeof(void*)) return false;
    newContext[12]=reinterpret_cast<void*>(indexed);newContext[13]=reinterpret_cast<void*>(draw);newContext[20]=reinterpret_cast<void*>(indexedInstances);newContext[21]=reinterpret_cast<void*>(instances);
    newContext[14]=reinterpret_cast<void*>(map);newContext[15]=reinterpret_cast<void*>(unmap);newContext[48]=reinterpret_cast<void*>(update);newContext[53]=reinterpret_cast<void*>(clear);newSwap[8]=reinterpret_cast<void*>(present);
    context=c.Get();swap=s;c->AddRef();s->AddRef();images.reserve(4);
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),newContext,oldContext)!=oldContext) return false;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),newSwap,oldSwap)!=oldSwap) {stop();return false;}active=true;return true;
}
void report(const std::filesystem::path& dir) {
    for(const auto& i:images) {std::ofstream out(dir/("hand-depth-"+std::to_string(GetCurrentProcessId())+"-"+i.name+".raw"),std::ios::binary);out.write("OWRAW001",8);std::array<UINT,4> meta{i.width,i.height,i.format,4};out.write(reinterpret_cast<const char*>(meta.data()),16);out.write(reinterpret_cast<const char*>(i.bytes.data()),i.bytes.size());}
    std::ofstream out(dir/("hand-depth-"+std::to_string(GetCurrentProcessId())+".json"));out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"frames\":"<<frame<<",\"failures\":"<<failures<<",\"restored\":"<<(restored?"true":"false")<<",\"beforeHand\":"<<(before?"true":"false")<<",\"afterHand\":"<<(after?"true":"false")<<",\"beforeHud\":"<<(boundary?"true":"false")<<",\"final\":"<<(finalImage?"true":"false")<<",\"handDraws\":"<<handDraws<<",\"nativeReplay\":false,\"depthMaskVerified\":false,\"worldBlended\":"<<(worldBlended?"true":"false")<<",\"mcSourcePid\":"<<guestPid<<",\"mcGeneration\":"<<guestGeneration<<",\"mcFrame\":"<<guestFrame<<",\"hostPoseConnected\":false}";
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dll))return 0;
    auto dir=dll.parent_path();
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),engine=pointer(base+0x181e3e0),p=pointer(engine+0x900),q=pointer(p+0x2e0),r=pointer(q);
    if(!attach(reinterpret_cast<IDXGISwapChain*>(pointer(r+8)))) return 0;
    // No GPU work on this worker; wait for the render callbacks' three-frame stop.
    while(!finished) Sleep(20);
    report(dir);return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_HandDepthTestAttach(IDXGISwapChain* s) {wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);return std::filesystem::path(exe).filename()==L"owmc-hand-depth-test.exe"&&attach(s);}
extern "C" __declspec(dllexport) void OWMC_HandDepthTestDump() {
    wchar_t exe[32768]{},dll[32768]{};GetModuleFileNameW(nullptr,exe,32768);GetModuleFileNameW(moduleHandle,dll,32768);
    if(std::filesystem::path(exe).filename()==L"owmc-hand-depth-test.exe"&&finished) report(std::filesystem::path(dll).parent_path());
}
extern "C" __declspec(dllexport) BOOL OWMC_HandDepthTestVerify() {
    if(!finished||!restored||frame!=3||failures||!before||!after||!boundary||!finalImage||handDraws!=1) return FALSE;
#ifdef OWMC_WORLD_BLEND
    if(!worldBlended||images.size()!=5) return FALSE;
    const auto& mixed=images[3].bytes;size_t left=(size_t(height/2)*width+width/4)*4,right=(size_t(height/2)*width+width*3/4)*4;
    if(mixed[left]!=255||mixed[left+2]!=0||mixed[right]!=0||mixed[right+2]!=255) return FALSE;
    const auto& final=images[4].bytes;
    if(final[left]!=255||final[right+2]!=255||final[1]!=255||final[0]!=0) return FALSE;
#else
    if(images.size()!=4) return FALSE;
#endif
    unsigned changed=0;for(size_t i=0;i<images[0].bytes.size();i+=4) if((field<uint32_t>(images[0].bytes.data(),i)&0xffffff)!=(field<uint32_t>(images[1].bytes.data(),i)&0xffffff)) changed++;
    return changed==width*height/2;
}
BOOL WINAPI DllMain(HMODULE m,DWORD reason,LPVOID) {if(reason==DLL_PROCESS_ATTACH) {moduleHandle=m;DisableThreadLibraryCalls(m);HANDLE t=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(t) CloseHandle(t);}return TRUE;}
