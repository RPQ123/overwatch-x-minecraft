#include "native_client_paths.hpp"
#include <d3d11_4.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <windows.h>
#include <array>
#include <cstring>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <vector>
#include "math.hpp"
using Microsoft::WRL::ComPtr;
extern "C" size_t traceContextCount(unsigned);
extern "C" size_t traceSwapCount();
namespace {
HMODULE moduleHandle;IDXGISwapChain* swap=nullptr;ID3D11DeviceContext* context=nullptr;
void **oldSwap=nullptr,**newSwap=nullptr,**oldContext=nullptr,**newContext=nullptr;
std::atomic<bool> active{false},finished{false};unsigned frame=0;UINT width=0,height=0;
std::mutex mutex;
struct Capture {unsigned frame,slot;uintptr_t identity;NativeProjection cpu;std::vector<float> values;};
std::vector<Capture> captures;unsigned failures=0;
template<class T> bool read(uintptr_t address,T& value) {SIZE_T count=0;return address>=0x10000&&address<0x7fffffffffffULL&&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&count)&&count==sizeof(value);}
uintptr_t pointer(uintptr_t address) {uintptr_t value=0;return read(address,value)?value:0;}
NativeProjection projection() {
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointer(base+0x17b7f90);
    auto component=pointer(pointer(pointer(admin+0xb0)+0x4f*0x18)),crosshair=pointer(component+0x48);
    NativeProjection result{};read(crosshair+0x50,result.worldToView);read(crosshair+0x90,result.viewToClip);
    struct Viewport {float l,t,r,b;} vp{};read(crosshair+0x1f0,vp);result.left=vp.l;result.top=vp.t;result.right=vp.r;result.bottom=vp.b;return result;
}
void observe(ID3D11DeviceContext* c) {
    if(!active) return;
    ComPtr<ID3D11DepthStencilView> depth;c->OMGetRenderTargets(0,nullptr,depth.GetAddressOf());if(!depth) return;
    ComPtr<ID3D11Resource> resource;depth->GetResource(resource.GetAddressOf());ComPtr<ID3D11Texture2D> texture;
    if(FAILED(resource.As(&texture))) return;D3D11_TEXTURE2D_DESC td{};texture->GetDesc(&td);
    UINT count=1;D3D11_VIEWPORT vp{};c->RSGetViewports(&count,&vp);
    if(td.Width!=width||td.Height!=height||vp.Width!=width||vp.Height!=height||vp.TopLeftX||vp.TopLeftY) return;
    std::lock_guard<std::mutex> lock(mutex);
    std::array<ID3D11Buffer*,14> buffers{};c->VSGetConstantBuffers(0,buffers.size(),buffers.data());
    ComPtr<ID3D11Device> device;c->GetDevice(device.GetAddressOf());
    for(unsigned slot=0;slot<buffers.size();slot++) {
        ComPtr<ID3D11Buffer> buffer;buffer.Attach(buffers[slot]);if(!buffer) continue;
#ifdef OWMC_SELECTION_TRACE
        if(slot!=9)continue;
#endif
        auto id=reinterpret_cast<uintptr_t>(buffer.Get());bool seen=false;
#ifndef OWMC_SELECTION_TRACE
        for(const auto& prior:captures) if(prior.frame==frame&&prior.identity==id) seen=true;
#endif
        if(seen||captures.size()>=48) continue;
        D3D11_BUFFER_DESC bd{};buffer->GetDesc(&bd);if(bd.ByteWidth<64||bd.ByteWidth>65536||bd.ByteWidth%4) continue;
        bd.Usage=D3D11_USAGE_STAGING;bd.CPUAccessFlags=D3D11_CPU_ACCESS_READ;bd.BindFlags=0;bd.MiscFlags=0;bd.StructureByteStride=0;
        ComPtr<ID3D11Buffer> staging;if(FAILED(device->CreateBuffer(&bd,nullptr,staging.GetAddressOf()))) {++failures;continue;}
        c->CopyResource(staging.Get(),buffer.Get());D3D11_MAPPED_SUBRESOURCE mapped{};
        if(FAILED(c->Map(staging.Get(),0,D3D11_MAP_READ,0,&mapped))) {++failures;continue;}
        Capture capture{frame,slot,id,projection(),std::vector<float>(bd.ByteWidth/4)};
        std::memcpy(capture.values.data(),mapped.pData,bd.ByteWidth);c->Unmap(staging.Get(),0);
#ifdef OWMC_SELECTION_TRACE
        for(const auto& prior:captures) if(prior.frame==frame&&prior.values==capture.values)seen=true;
#endif
        if(!seen)captures.push_back(std::move(capture));
    }
}
void WINAPI draw(ID3D11DeviceContext* c,UINT count,UINT start) {observe(c);reinterpret_cast<decltype(&draw)>(oldContext[13])(c,count,start);}
void WINAPI indexed(ID3D11DeviceContext* c,UINT count,UINT start,INT base) {observe(c);reinterpret_cast<decltype(&indexed)>(oldContext[12])(c,count,start,base);}
void WINAPI indexedInstances(ID3D11DeviceContext* c,UINT count,UINT instances,UINT start,INT base,UINT first) {observe(c);reinterpret_cast<decltype(&indexedInstances)>(oldContext[20])(c,count,instances,start,base,first);}
void WINAPI instances(ID3D11DeviceContext* c,UINT count,UINT n,UINT start,UINT first) {observe(c);reinterpret_cast<decltype(&instances)>(oldContext[21])(c,count,n,start,first);}
void stop() {
    active=false;if(context) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),oldContext,newContext);
    if(swap) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),oldSwap,newSwap);finished=true;
}
HRESULT WINAPI present(IDXGISwapChain* s,UINT interval,UINT flags) {
    auto result=reinterpret_cast<decltype(&present)>(oldSwap[8])(s,interval,flags);
    if(active&&!(flags&DXGI_PRESENT_TEST)&&++frame>=3) stop();return result;
}
bool attach(IDXGISwapChain* s) {
    if(swap) return false;ComPtr<ID3D11Device> device;if(FAILED(s->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())))) return false;
    ComPtr<ID3D11DeviceContext> c;device->GetImmediateContext(c.GetAddressOf());ComPtr<ID3D11DeviceContext4> c4;ComPtr<ID3D11DeviceContext3> c3;ComPtr<ID3D11DeviceContext2> c2;ComPtr<ID3D11DeviceContext1> c1;
    unsigned version=0;
    if(SUCCEEDED(c.As(&c4))&&static_cast<void*>(c4.Get())==c.Get()) version=4;
    else if(SUCCEEDED(c.As(&c3))&&static_cast<void*>(c3.Get())==c.Get()) version=3;
    else if(SUCCEEDED(c.As(&c2))&&static_cast<void*>(c2.Get())==c.Get()) version=2;
    else if(SUCCEEDED(c.As(&c1))&&static_cast<void*>(c1.Get())==c.Get()) version=1;
    if(!version) return false;
    ComPtr<ID3D11Texture2D> target;if(FAILED(s->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())))) return false;
    D3D11_TEXTURE2D_DESC td{};target->GetDesc(&td);width=td.Width;height=td.Height;
    oldContext=*reinterpret_cast<void***>(c.Get());oldSwap=*reinterpret_cast<void***>(s);newContext=new void*[traceContextCount(version)];newSwap=new void*[traceSwapCount()];
    SIZE_T got=0;if(!ReadProcessMemory(GetCurrentProcess(),oldContext,newContext,traceContextCount(version)*sizeof(void*),&got)||got!=traceContextCount(version)*sizeof(void*)) return false;
    if(!ReadProcessMemory(GetCurrentProcess(),oldSwap,newSwap,traceSwapCount()*sizeof(void*),&got)||got!=traceSwapCount()*sizeof(void*)) return false;
    newContext[12]=reinterpret_cast<void*>(indexed);newContext[13]=reinterpret_cast<void*>(draw);newContext[20]=reinterpret_cast<void*>(indexedInstances);newContext[21]=reinterpret_cast<void*>(instances);newSwap[8]=reinterpret_cast<void*>(present);
    context=c.Get();swap=s;c->AddRef();s->AddRef();
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(context),newContext,oldContext)!=oldContext) return false;
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(swap),newSwap,oldSwap)!=oldSwap) {stop();return false;}
    active=true;return true;
}
void report(const std::filesystem::path& path) {
    std::lock_guard<std::mutex> guard(mutex);std::ofstream out(path);out<<std::setprecision(9);
    auto values=[&](const auto& v){out<<'[';bool first=true;for(float f:v) {if(!first) out<<',';first=false;if(std::isfinite(f)) out<<f;else out<<"null";}out<<']';};
    out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"restored\":"<<(finished?"true":"false")<<",\"frames\":"<<frame<<",\"failures\":"<<failures<<",\"captures\":[";
    bool first=true;for(const auto& capture:captures) {if(!first) out<<',';first=false;
        out<<"{\"frame\":"<<capture.frame<<",\"slot\":"<<capture.slot<<",\"identity\":"<<capture.identity<<",\"cpuWorldToView\":";values(capture.cpu.worldToView);
        out<<",\"cpuViewToClip\":";values(capture.cpu.viewToClip);out<<",\"values\":";values(capture.values);out<<'}';
    }out<<"]}";
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dll))return 0;
    auto dir=dll.parent_path();
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),engine=pointer(base+0x181e3e0),p=pointer(engine+0x900),q=pointer(p+0x2e0),r=pointer(q);
    if(!attach(reinterpret_cast<IDXGISwapChain*>(pointer(r+8)))) return 0;
    for(unsigned i=0;i<100&&!finished;i++) Sleep(100);if(!finished) stop();report(dir/(
#ifdef OWMC_SELECTION_TRACE
    L"selection-trace-"
#else
    L"camera-trace-"
#endif
    +std::to_wstring(GetCurrentProcessId())+L".json"));return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_CameraTestAttach(IDXGISwapChain* s) {wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);return std::filesystem::path(exe).filename()==L"owmc-camera-test.exe"&&attach(s);}
extern "C" __declspec(dllexport) BOOL OWMC_CameraTestVerify() {std::lock_guard<std::mutex> lock(mutex);
#ifdef OWMC_SELECTION_TRACE
return finished&&frame==3&&captures.size()==6&&captures[0].slot==9&&captures[0].values[0]==17.f&&captures[1].values[0]==20.f&&captures[5].values[0]==22.f&&!failures;
#else
return finished&&frame==3&&captures.size()==3&&captures[0].slot==2&&captures[0].values[0]==17.f&&captures[2].values[15]==31.f&&!failures;
#endif
}
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID) {if(reason==DLL_PROCESS_ATTACH) {moduleHandle=module;DisableThreadLibraryCalls(module);auto thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread) CloseHandle(thread);}return TRUE;}
