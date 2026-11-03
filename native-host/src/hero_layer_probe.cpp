// Bounded, observational capture. Native color, depth and draw calls are unchanged.
#include "native_client_paths.hpp"
#include "render.hpp"
#include <d3d11_4.h>
#include <windows.h>
#include <atomic>
#include <algorithm>
#include <fstream>
#include <mutex>
#include <vector>
#include <memory>
#include "hero_stream.hpp"

extern "C" size_t traceContextCount(unsigned);
extern "C" size_t traceSwapCount();
namespace {
HMODULE moduleHandle;
IDXGISwapChain* swap=nullptr;ID3D11DeviceContext* context=nullptr;
void **oldSwap=nullptr,**newSwap=nullptr,**oldContext=nullptr,**newContext=nullptr;
std::atomic<bool> active{false},finished{false};std::atomic<unsigned> frame{0},failures{0};
UINT width=0,height=0;bool boundaryCaptured=false,finalCaptured=false;
std::filesystem::path directory;
ComPtr<ID3D11Texture2D> backbuffer;
struct Upload {uintptr_t id=0;void* mapped=nullptr;std::array<float,136> values{};bool valid=false;};
std::array<Upload,64> uploads{};
struct Draw {unsigned frame,count,targets;UINT stencil,depthFunction;uintptr_t shader;std::array<float,16> lens;};
std::vector<Draw> draws;
struct Image {std::string name;UINT width,height,format;std::vector<unsigned char> bytes;};
std::vector<Image> images;
std::mutex mutex;
#ifdef OWMC_HERO_STREAM
constexpr bool streaming=true;
#else
constexpr bool streaming=false;
#endif
std::unique_ptr<HeroStream> hero;
std::shared_ptr<const HeroStream::Frame> pendingFrame;
uint64_t published=0;
HANDLE faultFile=INVALID_HANDLE_VALUE;
std::atomic<unsigned> exceptions{0},phase{0};
LONG CALLBACK fault(EXCEPTION_POINTERS* e) {
    if(!active||faultFile==INVALID_HANDLE_VALUE||e->ExceptionRecord->ExceptionCode!=EXCEPTION_ACCESS_VIOLATION||exceptions.fetch_add(1)>=16) return EXCEPTION_CONTINUE_SEARCH;
    struct Fault {DWORD code,phase,frame,reserved;uint64_t ip,sp,ownBase,stack[16];wchar_t module[512];} f{};
    f.code=e->ExceptionRecord->ExceptionCode;f.phase=phase;f.frame=frame;f.ip=e->ContextRecord->Rip;f.sp=e->ContextRecord->Rsp;f.ownBase=reinterpret_cast<uintptr_t>(moduleHandle);
    SIZE_T n=0;ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(f.sp),f.stack,sizeof(f.stack),&n);
    HMODULE owner=nullptr;if(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(f.ip),&owner)) GetModuleFileNameW(owner,f.module,512);
    DWORD wrote=0;WriteFile(faultFile,&f,sizeof(f),&wrote,nullptr);return EXCEPTION_CONTINUE_SEARCH;
}
template<class T> bool read(uintptr_t address,T& value) {SIZE_T n=0;return address>=0x10000&&address<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&n)&&n==sizeof(value);}
uintptr_t pointer(uintptr_t a) {uintptr_t v=0;return read(a,v)?v:0;}
Upload* upload(ID3D11Resource* resource) {
    ComPtr<ID3D11Buffer> buffer;if(!resource||FAILED(resource->QueryInterface(__uuidof(ID3D11Buffer),reinterpret_cast<void**>(buffer.GetAddressOf())))) return nullptr;
    D3D11_BUFFER_DESC desc{};buffer->GetDesc(&desc);if(desc.ByteWidth!=544||!(desc.BindFlags&D3D11_BIND_CONSTANT_BUFFER)) return nullptr;
    uintptr_t id=reinterpret_cast<uintptr_t>(resource);
    for(auto& u:uploads) if(u.id==id) return &u;
    for(auto& u:uploads) if(!u.id) {u.id=id;return &u;}
    return nullptr;
}
HRESULT WINAPI map(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub,D3D11_MAP type,UINT flags,D3D11_MAPPED_SUBRESOURCE* out) {
    HRESULT result=reinterpret_cast<decltype(&map)>(oldContext[14])(c,r,sub,type,flags,out);
    if(active&&SUCCEEDED(result)&&out&&sub==0&&(type==D3D11_MAP_WRITE||type==D3D11_MAP_READ_WRITE||type==D3D11_MAP_WRITE_DISCARD||type==D3D11_MAP_WRITE_NO_OVERWRITE)) {
        if(auto* u=upload(r)) {u->mapped=out->pData;u->valid=false;}
    }return result;
}
void WINAPI unmap(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub) {
    if(active&&sub==0) for(auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(r)&&u.mapped) {
        u.valid=read(reinterpret_cast<uintptr_t>(u.mapped),u.values);u.mapped=nullptr;break;
    }
    reinterpret_cast<decltype(&unmap)>(oldContext[15])(c,r,sub);
}
void WINAPI update(ID3D11DeviceContext* c,ID3D11Resource* r,UINT sub,const D3D11_BOX* box,const void* data,UINT row,UINT depth) {
    if(active&&sub==0&&!box&&data) if(auto* u=upload(r)) u->valid=read(reinterpret_cast<uintptr_t>(data),u->values);
    reinterpret_cast<decltype(&update)>(oldContext[48])(c,r,sub,box,data,row,depth);
}
void capture(ID3D11Texture2D* source,const char* name) {
    D3D11_TEXTURE2D_DESC desc{};source->GetDesc(&desc);
    if(desc.SampleDesc.Count!=1||desc.Width>4096||desc.Height>2160||desc.ArraySize!=1) throw std::runtime_error("unsupported capture surface");
    if(desc.Format!=DXGI_FORMAT_R8G8B8A8_UNORM&&desc.Format!=DXGI_FORMAT_R8G8B8A8_UNORM_SRGB&&desc.Format!=DXGI_FORMAT_B8G8R8A8_UNORM&&desc.Format!=DXGI_FORMAT_R24G8_TYPELESS) throw std::runtime_error("unsupported capture format");
    ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());
    desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;desc.MiscFlags=0;desc.MipLevels=1;
    ComPtr<ID3D11Texture2D> staging;check(device->CreateTexture2D(&desc,nullptr,staging.GetAddressOf()),"layer staging");
    context->CopyResource(staging.Get(),source);D3D11_MAPPED_SUBRESOURCE mapped{};check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&mapped),"layer readback");
    Image result{name,desc.Width,desc.Height,static_cast<UINT>(desc.Format),std::vector<unsigned char>(size_t(desc.Width)*desc.Height*4)};
    for(UINT y=0;y<desc.Height;y++) std::memcpy(result.bytes.data()+size_t(y)*desc.Width*4,static_cast<unsigned char*>(mapped.pData)+size_t(y)*mapped.RowPitch,desc.Width*4);
    context->Unmap(staging.Get(),0);images.push_back(std::move(result));
}
void observe(ID3D11DeviceContext* c,UINT count) {
    if(streaming||!active||frame!=1||draws.size()>=512) return;
    ComPtr<ID3D11Buffer> cb;c->VSGetConstantBuffers(9,1,cb.GetAddressOf());if(!cb) return;
    Upload* current=nullptr;for(auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(cb.Get())&&u.valid) current=&u;
    if(!current) return;
    UINT n=1;D3D11_VIEWPORT vp{};c->RSGetViewports(&n,&vp);if(n!=1||vp.Width!=width||vp.Height!=height||vp.TopLeftX||vp.TopLeftY) return;
    std::array<ID3D11RenderTargetView*,8> targets{};ComPtr<ID3D11DepthStencilView> dsv;c->OMGetRenderTargets(8,targets.data(),dsv.GetAddressOf());unsigned targetCount=0;
    for(auto* t:targets) if(t) {++targetCount;t->Release();}
    UINT stencil=0;ComPtr<ID3D11DepthStencilState> state;c->OMGetDepthStencilState(state.GetAddressOf(),&stencil);
    D3D11_DEPTH_STENCIL_DESC desc{};if(state) state->GetDesc(&desc);
    ComPtr<ID3D11VertexShader> shader;c->VSGetShader(shader.GetAddressOf(),nullptr,nullptr);
    Draw d{frame,count,targetCount,stencil,desc.DepthEnable?static_cast<UINT>(desc.DepthFunc):0,reinterpret_cast<uintptr_t>(shader.Get()),{}};
    std::copy_n(current->values.begin(),16,d.lens.begin());draws.push_back(d);
}
void replay(ID3D11DeviceContext* c,const std::function<void()>& original) {
    if(!streaming||!active||!hero) return;
    phase=1;
    ComPtr<ID3D11RenderTargetView> color;ComPtr<ID3D11DepthStencilView> depth;c->OMGetRenderTargets(1,color.GetAddressOf(),depth.GetAddressOf());
    ComPtr<ID3D11Resource> resource;if(color) color->GetResource(resource.GetAddressOf());
    bool firstPerson=false;
    ComPtr<ID3D11Buffer> cb;c->VSGetConstantBuffers(9,1,cb.GetAddressOf());
    if(cb&&depth) for(auto& u:uploads) if(u.id==reinterpret_cast<uintptr_t>(cb.Get())&&u.valid) {
        UINT count=1;D3D11_VIEWPORT vp{};c->RSGetViewports(&count,&vp);
        std::array<ID3D11RenderTargetView*,8> targets{};c->OMGetRenderTargets(8,targets.data(),nullptr);unsigned n=0;for(auto* t:targets) if(t) {++n;t->Release();}
        firstPerson=n>=4&&count==1&&!vp.TopLeftX&&!vp.TopLeftY&&vp.Width==width&&vp.Height==height
            &&std::abs(u.values[0]+1.12820041f)<.002f&&std::abs(u.values[5]-2.00568986f)<.002f;break;
    }
    try {hero->replay(firstPerson,resource.Get()==backbuffer.Get(),original);phase=0;} catch(const std::exception&) {++failures;active=false;}
}
void WINAPI indexed(ID3D11DeviceContext* c,UINT n,UINT first,INT base) {observe(c,n);auto original=[&]{reinterpret_cast<decltype(&indexed)>(oldContext[12])(c,n,first,base);};original();replay(c,original);}
void WINAPI draw(ID3D11DeviceContext* c,UINT n,UINT first) {observe(c,n);auto original=[&]{reinterpret_cast<decltype(&draw)>(oldContext[13])(c,n,first);};original();replay(c,original);}
void WINAPI indexedInstances(ID3D11DeviceContext* c,UINT n,UINT instances,UINT first,INT base,UINT start) {observe(c,n);auto original=[&]{reinterpret_cast<decltype(&indexedInstances)>(oldContext[20])(c,n,instances,first,base,start);};original();replay(c,original);}
void WINAPI instances(ID3D11DeviceContext* c,UINT n,UINT instanceCount,UINT first,UINT start) {observe(c,n);auto original=[&]{reinterpret_cast<decltype(&instances)>(oldContext[21])(c,n,instanceCount,first,start);};original();replay(c,original);}
void WINAPI clear(ID3D11DeviceContext* c,ID3D11DepthStencilView* depth,UINT flags,FLOAT value,UINT8 stencil) {
    if(active&&(streaming||(frame==1&&!boundaryCaptured))&&depth&&(flags&D3D11_CLEAR_STENCIL)&&!(flags&D3D11_CLEAR_DEPTH)) {
        ComPtr<ID3D11Resource> r;depth->GetResource(r.GetAddressOf());ComPtr<ID3D11Texture2D> z;
        ComPtr<ID3D11RenderTargetView> color;c->OMGetRenderTargets(1,color.GetAddressOf(),nullptr);ComPtr<ID3D11Resource> cr;if(color) color->GetResource(cr.GetAddressOf());
        if(SUCCEEDED(r.As(&z))&&cr.Get()==backbuffer.Get()) {
            D3D11_TEXTURE2D_DESC desc{};z->GetDesc(&desc);
            if(desc.Width==width&&desc.Height==height&&desc.Format==DXGI_FORMAT_R24G8_TYPELESS) {
                try {if(streaming) hero->boundary(backbuffer.Get());else {capture(backbuffer.Get(),"before-hud");capture(z.Get(),"before-hud-depth");}boundaryCaptured=true;} catch(const std::exception&) {++failures;active=false;}
            }
        }
    }
    reinterpret_cast<decltype(&clear)>(oldContext[53])(c,depth,flags,value,stencil);
}
void stop() {
    active=false;if(context) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),oldContext,newContext);
    if(swap) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),oldSwap,newSwap);finished=true;
}
HRESULT WINAPI present(IDXGISwapChain* s,UINT interval,UINT flags) {
    if(active&&!(flags&DXGI_PRESENT_TEST)) try {
        if(streaming) {phase=2;auto ready=hero->present();if(ready) {std::shared_ptr<const HeroStream::Frame> f=std::make_shared<HeroStream::Frame>(std::move(*ready));std::atomic_store(&pendingFrame,f);finalCaptured=true;}phase=0;}
        else if(frame==1) {capture(backbuffer.Get(),"final");finalCaptured=true;}
    } catch(const std::exception&) {++failures;active=false;}
    HRESULT result=reinterpret_cast<decltype(&present)>(oldSwap[8])(s,interval,flags);
    if(active&&!(flags&DXGI_PRESENT_TEST)&&++frame>=3&&!streaming) stop();return result;
}
bool attach(IDXGISwapChain* s) {
    if(swap) return false;ComPtr<ID3D11Device> device;if(FAILED(s->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())))) return false;
    ComPtr<ID3D11DeviceContext> c;device->GetImmediateContext(c.GetAddressOf());unsigned version=0;
    ComPtr<ID3D11DeviceContext4> c4;ComPtr<ID3D11DeviceContext3> c3;ComPtr<ID3D11DeviceContext2> c2;ComPtr<ID3D11DeviceContext1> c1;
    if(SUCCEEDED(c.As(&c4))&&static_cast<void*>(c4.Get())==c.Get()) version=4;
    else if(SUCCEEDED(c.As(&c3))&&static_cast<void*>(c3.Get())==c.Get()) version=3;
    else if(SUCCEEDED(c.As(&c2))&&static_cast<void*>(c2.Get())==c.Get()) version=2;
    else if(SUCCEEDED(c.As(&c1))&&static_cast<void*>(c1.Get())==c.Get()) version=1;
    if(!version||FAILED(s->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(backbuffer.GetAddressOf())))) return false;
    D3D11_TEXTURE2D_DESC desc{};backbuffer->GetDesc(&desc);width=desc.Width;height=desc.Height;
    if(streaming) hero=std::make_unique<HeroStream>(device.Get(),width,height,desc.Format);
    oldContext=*reinterpret_cast<void***>(c.Get());oldSwap=*reinterpret_cast<void***>(s);
    newContext=new void*[traceContextCount(version)];newSwap=new void*[traceSwapCount()];SIZE_T bytes=0;
    if(!ReadProcessMemory(GetCurrentProcess(),oldContext,newContext,traceContextCount(version)*sizeof(void*),&bytes)||bytes!=traceContextCount(version)*sizeof(void*)) return false;
    if(!ReadProcessMemory(GetCurrentProcess(),oldSwap,newSwap,traceSwapCount()*sizeof(void*),&bytes)||bytes!=traceSwapCount()*sizeof(void*)) return false;
    newContext[12]=reinterpret_cast<void*>(indexed);newContext[13]=reinterpret_cast<void*>(draw);newContext[20]=reinterpret_cast<void*>(indexedInstances);newContext[21]=reinterpret_cast<void*>(instances);
    newContext[14]=reinterpret_cast<void*>(map);newContext[15]=reinterpret_cast<void*>(unmap);newContext[48]=reinterpret_cast<void*>(update);newContext[53]=reinterpret_cast<void*>(clear);newSwap[8]=reinterpret_cast<void*>(present);
    context=c.Get();swap=s;c->AddRef();s->AddRef();draws.reserve(512);
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),newContext,oldContext)!=oldContext) return false;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),newSwap,oldSwap)!=oldSwap) {stop();return false;}
    active=true;return true;
}
void report() {
    std::lock_guard<std::mutex> guard(mutex);
    if(streaming) {
        auto path=directory/("hero-stream-"+std::to_string(GetCurrentProcessId())+".json"),temporary=path;temporary+=L".tmp";
        std::ofstream out(temporary);out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"enabled\":"<<(active?"true":"false")<<",\"restored\":"<<(finished?"true":"false")<<",\"frames\":"<<frame<<",\"failures\":"<<failures
            <<",\"handDraws\":"<<(hero?hero->handDraws.load():0)<<",\"hudDraws\":"<<(hero?hero->hudDraws.load():0)<<",\"observedUavMask\":"<<(hero?hero->observedUavMask.load():0)<<",\"published\":"<<published<<",\"cameraSyncVerified\":false,\"nativeAttackVerified\":false}";out.close();MoveFileExW(temporary.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING);return;
    }
    for(const auto& i:images) {
        std::ofstream out(directory/("hero-layer-"+std::to_string(GetCurrentProcessId())+"-"+i.name+".raw"),std::ios::binary);
        out.write("OWRAW001",8);std::array<UINT,4> info{i.width,i.height,i.format,4};out.write(reinterpret_cast<const char*>(info.data()),16);out.write(reinterpret_cast<const char*>(i.bytes.data()),i.bytes.size());
    }
    std::ofstream out(directory/("hero-layer-"+std::to_string(GetCurrentProcessId())+".json"));
    out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"restored\":"<<(finished?"true":"false")<<",\"frames\":"<<frame<<",\"failures\":"<<failures<<",\"boundaryCaptured\":"<<(boundaryCaptured?"true":"false")<<",\"finalCaptured\":"<<(finalCaptured?"true":"false")<<",\"draws\":[";
    bool first=true;for(const auto& d:draws) {if(!first) out<<',';first=false;out<<"{\"count\":"<<d.count<<",\"targets\":"<<d.targets<<",\"stencil\":"<<d.stencil<<",\"depthFunction\":"<<d.depthFunction<<",\"shader\":"<<d.shader<<",\"lens\":[";
        for(unsigned i=0;i<16;i++) {if(i) out<<',';if(std::isfinite(d.lens[i])) out<<d.lens[i];else out<<"null";}out<<"]}";
    }out<<"]}";
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dll))return 0;
    directory=dll.parent_path();
    // Archived failed replay experiment. Standalone GPU fixtures may still
    // exercise the class, but this DLL must never auto-attach to a real game.
    if(streaming) return 0;
    if(streaming) {faultFile=CreateFileW((directory/("hero-fault-"+std::to_string(GetCurrentProcessId())+".bin")).c_str(),GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);AddVectoredExceptionHandler(1,fault);}
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),engine=pointer(base+0x181e3e0),p=pointer(engine+0x900),q=pointer(p+0x2e0),r=pointer(q);
    if(!attach(reinterpret_cast<IDXGISwapChain*>(pointer(r+8)))) return 0;
    if(streaming) {
        auto event=CreateEventW(nullptr,TRUE,FALSE,(L"Local\\OWHeroStreamStop_"+std::to_wstring(GetCurrentProcessId())).c_str());
        uint64_t lastReport=0;
        while(active&&WaitForSingleObject(event,10)==WAIT_TIMEOUT) {
            auto f=std::atomic_load(&pendingFrame);if(f&&f->sequence>published) {
                auto path=directory/L"native-hero-frame.bin",temp=directory/L"native-hero-frame.tmp";
                std::ofstream out(temp,std::ios::binary);out.write("OWHERO01",8);std::array<UINT,6> info{1,f->width,f->height,3,GetCurrentProcessId(),0};out.write(reinterpret_cast<const char*>(info.data()),24);
                out.write(reinterpret_cast<const char*>(&f->sequence),8);out.write(reinterpret_cast<const char*>(&f->time),8);
                std::array<UINT,4> tail{static_cast<UINT>(f->rgba.size()),0,0,0};out.write(reinterpret_cast<const char*>(tail.data()),16);out.write(reinterpret_cast<const char*>(f->rgba.data()),f->rgba.size());out.close();
                if(MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING)) published=f->sequence;
            }
            if(GetTickCount64()-lastReport>1000) {report();lastReport=GetTickCount64();}
        }
        stop();report();if(event) CloseHandle(event);return 0;
    }
    for(unsigned i=0;i<100&&!finished;i++) Sleep(100);if(!finished) stop();report();return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_LayerTestAttach(IDXGISwapChain* s) {wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);return std::filesystem::path(exe).filename()==L"owmc-layer-test.exe"&&attach(s);}
extern "C" __declspec(dllexport) BOOL OWMC_LayerTestVerify() {return finished&&frame==3&&boundaryCaptured&&finalCaptured&&!failures&&images.size()==3&&images[0].bytes[0]==255&&images[2].bytes[1]==255&&draws.size()==1&&draws[0].lens[0]==-.8f;}
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID) {if(reason==DLL_PROCESS_ATTACH) {moduleHandle=module;DisableThreadLibraryCalls(module);HANDLE thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread) CloseHandle(thread);}return TRUE;}
