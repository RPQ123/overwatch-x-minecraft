#include "native_client_paths.hpp"
#include <d3d11_4.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <windows.h>
#include <atomic>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <vector>

using Microsoft::WRL::ComPtr;
extern "C" size_t traceContextCount(unsigned);
extern "C" size_t traceSwapCount();
namespace {
HMODULE moduleHandle;
IDXGISwapChain* attachedSwap=nullptr;
ID3D11DeviceContext* attachedContext=nullptr;
void **oldSwap=nullptr,**newSwap=nullptr,**oldContext=nullptr,**newContext=nullptr;
std::atomic<bool> active{false},finished{false};
std::atomic<unsigned> frame{0},overflow{0},executions{0};
std::mutex lock;
struct Texture { UINT width=0,height=0,format=0,samples=0; uintptr_t id=0; };
struct Event {
    const char* kind;unsigned frame,draws=0;Texture color,depth;
    UINT targets=0,depthFunction=0,depthWrite=0;bool depthEnabled=false;
    float clear=-1;D3D11_VIEWPORT viewport{};
};
std::vector<Event> events;
template<class T> bool read(uintptr_t address,T& result) {
    SIZE_T count=0;return address>=0x10000&&address<0x7fffffffffffULL
        &&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&result,sizeof(result),&count)&&count==sizeof(result);
}
uintptr_t pointer(uintptr_t address) { uintptr_t result=0;return read(address,result)?result:0; }
Texture describe(ID3D11View* view) {
    Texture result;if(!view) return result;
    ComPtr<ID3D11Resource> resource;view->GetResource(resource.GetAddressOf());
    ComPtr<ID3D11Texture2D> texture;
    if(SUCCEEDED(resource.As(&texture))) {
        D3D11_TEXTURE2D_DESC desc{};texture->GetDesc(&desc);
        result={desc.Width,desc.Height,static_cast<UINT>(desc.Format),desc.SampleDesc.Count,reinterpret_cast<uintptr_t>(resource.Get())};
    }
    return result;
}
void binding(const char* kind,UINT count,ID3D11RenderTargetView*const* targets,ID3D11DepthStencilView* depth,float clear=-1) {
    if(!active) return;
    Event event{};event.kind=kind;event.frame=frame;event.targets=count;event.clear=clear;
    event.color=describe(count&&count!=D3D11_KEEP_RENDER_TARGETS_AND_DEPTH_STENCIL&&targets?targets[0]:nullptr);
    event.depth=describe(depth);
    std::lock_guard<std::mutex> guard(lock);
    if(events.size()<512) events.push_back(event);else ++overflow;
}
void drawing(ID3D11DeviceContext* context) {
    if(!active) return;
    std::lock_guard<std::mutex> guard(lock);
    if(events.empty()) return;
    Event& event=events.back();
    if(event.draws++==0) {
        ComPtr<ID3D11DepthStencilState> state;UINT stencil=0;context->OMGetDepthStencilState(state.GetAddressOf(),&stencil);
        D3D11_DEPTH_STENCIL_DESC desc{};
        if(state) state->GetDesc(&desc);else { desc.DepthEnable=TRUE;desc.DepthFunc=D3D11_COMPARISON_LESS;desc.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL; }
        event.depthEnabled=desc.DepthEnable;event.depthFunction=desc.DepthFunc;event.depthWrite=desc.DepthWriteMask;
        UINT count=1;context->RSGetViewports(&count,&event.viewport);
        ComPtr<ID3D11RenderTargetView> color;ComPtr<ID3D11DepthStencilView> depth;
        context->OMGetRenderTargets(1,color.GetAddressOf(),depth.GetAddressOf());
        event.color=describe(color.Get());event.depth=describe(depth.Get());
    }
}
void WINAPI setTargets(ID3D11DeviceContext* c,UINT n,ID3D11RenderTargetView*const* targets,ID3D11DepthStencilView* depth) {
    reinterpret_cast<decltype(&setTargets)>(oldContext[33])(c,n,targets,depth);binding("targets",n,targets,depth);
}
void WINAPI setTargetsUav(ID3D11DeviceContext* c,UINT n,ID3D11RenderTargetView*const* targets,ID3D11DepthStencilView* depth,
                         UINT start,UINT count,ID3D11UnorderedAccessView*const* uavs,const UINT* initial) {
    reinterpret_cast<decltype(&setTargetsUav)>(oldContext[34])(c,n,targets,depth,start,count,uavs,initial);
    binding("targets-uav",n,targets,depth);
}
void WINAPI clearDepth(ID3D11DeviceContext* c,ID3D11DepthStencilView* depth,UINT flags,FLOAT value,UINT8 stencil) {
    reinterpret_cast<decltype(&clearDepth)>(oldContext[53])(c,depth,flags,value,stencil);
    binding("clear-depth",0,nullptr,depth,(flags&D3D11_CLEAR_DEPTH)?value:-1);
}
void WINAPI drawIndexed(ID3D11DeviceContext* c,UINT count,UINT start,INT base) {
    drawing(c);reinterpret_cast<decltype(&drawIndexed)>(oldContext[12])(c,count,start,base);
}
void WINAPI draw(ID3D11DeviceContext* c,UINT count,UINT start) {
    drawing(c);reinterpret_cast<decltype(&draw)>(oldContext[13])(c,count,start);
}
void WINAPI drawIndexedInstanced(ID3D11DeviceContext* c,UINT count,UINT instances,UINT start,INT base,UINT first) {
    drawing(c);reinterpret_cast<decltype(&drawIndexedInstanced)>(oldContext[20])(c,count,instances,start,base,first);
}
void WINAPI drawInstanced(ID3D11DeviceContext* c,UINT count,UINT instances,UINT start,UINT first) {
    drawing(c);reinterpret_cast<decltype(&drawInstanced)>(oldContext[21])(c,count,instances,start,first);
}
void WINAPI execute(ID3D11DeviceContext* c,ID3D11CommandList* commands,BOOL restore) {
    if(active) ++executions;
    reinterpret_cast<decltype(&execute)>(oldContext[58])(c,commands,restore);
}
void stop() {
    active=false;
    if(attachedContext) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(attachedContext),oldContext,newContext);
    if(attachedSwap) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(attachedSwap),oldSwap,newSwap);
    finished=true;
    // Retain callbacks/tables and COM references until exit, including any calls already in flight.
}
HRESULT WINAPI present(IDXGISwapChain* swap,UINT interval,UINT flags) {
    HRESULT result=reinterpret_cast<decltype(&present)>(oldSwap[8])(swap,interval,flags);
    if(active&&!(flags&DXGI_PRESENT_TEST)&&++frame>=3) stop();
    return result;
}
bool attach(IDXGISwapChain* swap) {
    if(attachedSwap) return false;
    ComPtr<ID3D11Device> device;
    if(FAILED(swap->GetDevice(__uuidof(ID3D11Device),reinterpret_cast<void**>(device.GetAddressOf())))) return false;
    ComPtr<ID3D11DeviceContext> context;device->GetImmediateContext(context.GetAddressOf());
    unsigned version=0;ComPtr<ID3D11DeviceContext4> c4;ComPtr<ID3D11DeviceContext3> c3;
    ComPtr<ID3D11DeviceContext2> c2;ComPtr<ID3D11DeviceContext1> c1;
    if(SUCCEEDED(context.As(&c4))&&static_cast<void*>(c4.Get())==context.Get()) version=4;
    else if(SUCCEEDED(context.As(&c3))&&static_cast<void*>(c3.Get())==context.Get()) version=3;
    else if(SUCCEEDED(context.As(&c2))&&static_cast<void*>(c2.Get())==context.Get()) version=2;
    else if(SUCCEEDED(context.As(&c1))&&static_cast<void*>(c1.Get())==context.Get()) version=1;
    if(version==0) return false; // Unknown extended alias surface: don't truncate a table.
    size_t contextCount=traceContextCount(version),swapCount=traceSwapCount(),bytesRead=0;
    oldContext=*reinterpret_cast<void***>(context.Get());oldSwap=*reinterpret_cast<void***>(swap);
    newContext=new void*[contextCount];newSwap=new void*[swapCount];
    if(!ReadProcessMemory(GetCurrentProcess(),oldContext,newContext,contextCount*sizeof(void*),&bytesRead)||bytesRead!=contextCount*sizeof(void*)) return false;
    if(!ReadProcessMemory(GetCurrentProcess(),oldSwap,newSwap,swapCount*sizeof(void*),&bytesRead)||bytesRead!=swapCount*sizeof(void*)) return false;
    newContext[12]=reinterpret_cast<void*>(drawIndexed);newContext[13]=reinterpret_cast<void*>(draw);
    newContext[20]=reinterpret_cast<void*>(drawIndexedInstanced);newContext[21]=reinterpret_cast<void*>(drawInstanced);
    newContext[33]=reinterpret_cast<void*>(setTargets);newContext[34]=reinterpret_cast<void*>(setTargetsUav);
    newContext[53]=reinterpret_cast<void*>(clearDepth);newContext[58]=reinterpret_cast<void*>(execute);
    newSwap[8]=reinterpret_cast<void*>(present);
    attachedContext=context.Get();attachedSwap=swap;context->AddRef();swap->AddRef();
    { std::lock_guard<std::mutex> guard(lock);events.reserve(512); }
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(attachedContext),newContext,oldContext)!=oldContext) { stop();return false; }
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(attachedSwap),newSwap,oldSwap)!=oldSwap) { stop();return false; }
    active=true;return true;
}
void writeReport(const std::filesystem::path& path) {
    std::lock_guard<std::mutex> guard(lock);std::ofstream out(path);
    out<<"{\"pid\":"<<GetCurrentProcessId()<<",\"restored\":"<<(finished?"true":"false")
       <<",\"frames\":"<<frame<<",\"commandListExecutions\":"<<executions<<",\"overflow\":"<<overflow<<",\"events\":[";
    bool first=true;for(const auto& event:events) {
        if(!first) out<<',';first=false;
        out<<"{\"kind\":\""<<event.kind<<"\",\"frame\":"<<event.frame<<",\"draws\":"<<event.draws
           <<",\"targets\":"<<event.targets<<",\"clearDepth\":"<<event.clear<<",\"depthEnabled\":"<<(event.depthEnabled?"true":"false")
           <<",\"depthFunction\":"<<event.depthFunction<<",\"depthWrite\":"<<event.depthWrite;
        auto texture=[&](const char* name,const Texture& value) { out<<",\""<<name<<"\":{\"id\":"<<value.id<<",\"width\":"<<value.width
            <<",\"height\":"<<value.height<<",\"format\":"<<value.format<<",\"samples\":"<<value.samples<<'}'; };
        texture("color",event.color);texture("depth",event.depth);
        out<<",\"viewport\":["<<event.viewport.TopLeftX<<','<<event.viewport.TopLeftY<<','<<event.viewport.Width<<','<<event.viewport.Height<<','
           <<event.viewport.MinDepth<<','<<event.viewport.MaxDepth<<"]}";
    }out<<"]}";
}
DWORD WINAPI worker(void*) {
    std::filesystem::path exe,dll;
    if(!owmc::runningResearchClient(exe)||!owmc::moduleFilePath(moduleHandle,dll))return 0;
    auto directory=dll.parent_path();
    uintptr_t base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t engine=pointer(base+0x181e3e0),a=pointer(engine+0x900),b=pointer(a+0x2e0),c=pointer(b),swap=pointer(c+8);
    if(!swap||!attach(reinterpret_cast<IDXGISwapChain*>(swap))) return 0;
    for(unsigned tick=0;tick<100&&!finished;tick++) Sleep(100);
    if(!finished) stop();
    writeReport(directory/(L"trace-"+std::to_wstring(GetCurrentProcessId())+L".json"));return 0;
}
}
extern "C" __declspec(dllexport) BOOL OWMC_TraceTestAttach(IDXGISwapChain* swap) {
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);
    if(std::filesystem::path(exe).filename()!=L"owmc-trace-test.exe") return FALSE;
    return attach(swap);
}
extern "C" __declspec(dllexport) BOOL OWMC_TraceTestVerify() {
    std::lock_guard<std::mutex> guard(lock);bool zeroClear=false,greater=false;
    for(const auto& event:events) {
        zeroClear|=event.kind==std::string("clear-depth")&&event.clear==0;
        greater|=event.draws>0&&event.depthFunction==D3D11_COMPARISON_GREATER_EQUAL;
    }return finished&&frame==3&&zeroClear&&greater&&!overflow;
}
BOOL WINAPI DllMain(HMODULE module,DWORD reason,LPVOID) {
    if(reason==DLL_PROCESS_ATTACH) { moduleHandle=module;DisableThreadLibraryCalls(module);
        HANDLE thread=CreateThread(nullptr,0,worker,nullptr,0,nullptr);if(thread) CloseHandle(thread); }
    return TRUE;
}
