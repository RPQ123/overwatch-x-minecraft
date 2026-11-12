#include "../src/frame_compositor.hpp"
#include <d3d11_1.h>
#include <cassert>
#include <iostream>
using namespace passthrough;
#ifndef OWMC_LIVE_VERSION
#define OWMC_LIVE_VERSION 31
#endif
#define OWMC_STRING_IMPL(x) #x
#define OWMC_STRING(x) OWMC_STRING_IMPL(x)
int main() {
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"OWMCHandDepthHiddenTest";RegisterClassW(&wc);
    HWND window=CreateWindowW(wc.lpszClassName,L"Hidden depth test",WS_OVERLAPPEDWINDOW,0,0,160,120,nullptr,nullptr,wc.hInstance,nullptr);assert(window);
    DXGI_SWAP_CHAIN_DESC sd{};sd.BufferDesc.Width=128;sd.BufferDesc.Height=72;sd.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sd.SampleDesc.Count=1;sd.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sd.BufferCount=1;sd.OutputWindow=window;sd.Windowed=TRUE;
#ifdef OWMC_OFFSCREEN_FIXTURE
    sd.BufferDesc.Width=192;sd.BufferDesc.Height=108;
#endif
    ComPtr<ID3D11Device> dev;ComPtr<ID3D11DeviceContext> ctx;ComPtr<IDXGISwapChain> swap;gpuCheck(D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&sd,swap.GetAddressOf(),dev.GetAddressOf(),nullptr,ctx.GetAddressOf()),"hand test device");
    ComPtr<ID3D11Texture2D> color,z;gpuCheck(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(color.GetAddressOf())),"color");
    ComPtr<ID3D11Texture2D> presentColor=color;
#ifdef OWMC_OFFSCREEN_FIXTURE
    D3D11_TEXTURE2D_DESC scene{};color->GetDesc(&scene);scene.Width=128;scene.Height=72;
    color.Reset();gpuCheck(dev->CreateTexture2D(&scene,nullptr,color.GetAddressOf()),"original offscreen scene");
#endif
    ComPtr<ID3D11RenderTargetView> rtv;gpuCheck(dev->CreateRenderTargetView(color.Get(),nullptr,rtv.GetAddressOf()),"rtv");
    D3D11_TEXTURE2D_DESC td{};td.Width=128;td.Height=72;td.MipLevels=1;td.ArraySize=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.SampleDesc.Count=1;td.BindFlags=D3D11_BIND_RENDER_TARGET;
    std::array<ComPtr<ID3D11Texture2D>,6> colors;std::array<ComPtr<ID3D11RenderTargetView>,6> views;
    for(int i=0;i<6;i++) {gpuCheck(dev->CreateTexture2D(&td,nullptr,colors[i].GetAddressOf()),"G buffer");gpuCheck(dev->CreateRenderTargetView(colors[i].Get(),nullptr,views[i].GetAddressOf()),"G view");}
    td.Format=DXGI_FORMAT_R24G8_TYPELESS;td.BindFlags=D3D11_BIND_DEPTH_STENCIL;gpuCheck(dev->CreateTexture2D(&td,nullptr,z.GetAddressOf()),"z");
    D3D11_DEPTH_STENCIL_VIEW_DESC vd{};vd.Format=DXGI_FORMAT_D24_UNORM_S8_UINT;vd.ViewDimension=D3D11_DSV_DIMENSION_TEXTURE2D;ComPtr<ID3D11DepthStencilView> dsv;gpuCheck(dev->CreateDepthStencilView(z.Get(),&vd,dsv.GetAddressOf()),"dsv");
    D3D11_DEPTH_STENCIL_DESC dd{};dd.DepthEnable=TRUE;dd.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL;dd.DepthFunc=D3D11_COMPARISON_GREATER_EQUAL;
#ifdef OWMC_SELECTION_FIXTURE
    dd.DepthFunc=D3D11_COMPARISON_LESS_EQUAL;
#endif
    ComPtr<ID3D11DepthStencilState> depthState;gpuCheck(dev->CreateDepthStencilState(&dd,depthState.GetAddressOf()),"state");
    const char* shader=R"(float4 VS(uint i:SV_VertexID):SV_Position {float2 p=float2((i<<1)&2,i&2);return float4(p.x*2-1,1-p.y*2,.75,1);} float4 PS(float4 p:SV_Position):SV_Target {clip(64-p.x);return float4(1,0,0,1);})";
    ComPtr<ID3DBlob> vb,pb;gpuCheck(D3DCompile(shader,strlen(shader),nullptr,nullptr,nullptr,"VS","vs_5_0",0,0,vb.GetAddressOf(),nullptr),"test VS");gpuCheck(D3DCompile(shader,strlen(shader),nullptr,nullptr,nullptr,"PS","ps_5_0",0,0,pb.GetAddressOf(),nullptr),"test PS");
    ComPtr<ID3D11VertexShader> vs;ComPtr<ID3D11PixelShader> ps;gpuCheck(dev->CreateVertexShader(vb->GetBufferPointer(),vb->GetBufferSize(),nullptr,vs.GetAddressOf()),"VS");gpuCheck(dev->CreatePixelShader(pb->GetBufferPointer(),pb->GetBufferSize(),nullptr,ps.GetAddressOf()),"PS");
    D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;ComPtr<ID3D11RasterizerState> raster;gpuCheck(dev->CreateRasterizerState(&rd,raster.GetAddressOf()),"raster");
    D3D11_BUFFER_DESC bd{};bd.ByteWidth=544;bd.Usage=D3D11_USAGE_DYNAMIC;bd.CPUAccessFlags=D3D11_CPU_ACCESS_WRITE;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;ComPtr<ID3D11Buffer> cb;gpuCheck(dev->CreateBuffer(&bd,nullptr,cb.GetAddressOf()),"cb");
    auto lens=[&](float x,float y) {
        D3D11_MAPPED_SUBRESOURCE mapped{};gpuCheck(ctx->Map(cb.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"map");
        std::array<float,136> values{};values[0]=x;values[5]=y;values[3]=1;values[10]=1.00005f;values[11]=1;values[14]=-.100005f;
        for(int k=0;k<4;k++) {values[16+k*5]=1;values[32+k*5]=1;}values[112]=1.f/128;values[113]=1.f/72;
        memcpy(mapped.pData,values.data(),544);ctx->Unmap(cb.Get(),0);auto* b=cb.Get();ctx->VSSetConstantBuffers(9,1,&b);
    };
    void** originalSwap=*reinterpret_cast<void***>(swap.Get());void** originalContext=*reinterpret_cast<void***>(ctx.Get());
#if defined(OWMC_LIVE_BLEND)
    HMODULE module=LoadLibraryA("native-host/build/owmc-live-passthrough-v" OWMC_STRING(OWMC_LIVE_VERSION) ".dll");
#elif defined(OWMC_POSE_OBSERVER)
    HMODULE module=LoadLibraryW(L"native-host/build/owmc-pose-observer-v1.dll");
#elif defined(OWMC_WORLD_BLEND)
    HMODULE module=LoadLibraryW(L"native-host/build/owmc-world-blend-probe.dll");
#else
    HMODULE module=LoadLibraryW(L"native-host/build/owmc-hand-depth-probe.dll");
#endif
    assert(module);
    BOOL(*attach)(IDXGISwapChain*)=nullptr;BOOL(*verify)()=nullptr;
    auto attachAddress=GetProcAddress(module,
#ifdef OWMC_SELECTION_FIXTURE
    "OWMC_SelectionTestAttach"
#else
    "OWMC_HandDepthTestAttach"
#endif
    ),verifyAddress=GetProcAddress(module,"OWMC_HandDepthTestVerify");
    static_assert(sizeof attach==sizeof attachAddress);memcpy(&attach,&attachAddress,sizeof attach);memcpy(&verify,&verifyAddress,sizeof verify);
    assert(attach&&verify&&attach(swap.Get()));
#if defined(OWMC_LIVE_BLEND) && OWMC_LIVE_VERSION >= 51
    // A missing first host camera must preserve the original pixels while
    // MC frame publication and the native compositor catch up.
    FLOAT nativeColor[]{1,0,0,1};ctx->ClearRenderTargetView(rtv.Get(),nativeColor);
    gpuCheck(swap->Present(0,0),"present without first camera");
    D3D11_TEXTURE2D_DESC firstDesc{};presentColor->GetDesc(&firstDesc);
    firstDesc.Usage=D3D11_USAGE_STAGING;firstDesc.BindFlags=0;firstDesc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
    ComPtr<ID3D11Texture2D> firstReadback;
    gpuCheck(dev->CreateTexture2D(&firstDesc,nullptr,firstReadback.GetAddressOf()),"original frame readback");
    ctx->CopyResource(firstReadback.Get(),presentColor.Get());D3D11_MAPPED_SUBRESOURCE firstPixels{};
    gpuCheck(ctx->Map(firstReadback.Get(),0,D3D11_MAP_READ,0,&firstPixels),"original pixels");
    auto* firstPixel=static_cast<const unsigned char*>(firstPixels.pData);
    assert(firstPixel[0]==255&&firstPixel[1]==0&&firstPixel[2]==0&&firstPixel[3]==255);
    ctx->Unmap(firstReadback.Get(),0);
#endif
#ifdef OWMC_LIVE_BLEND
    // Non-camera uploads must remain usable while their identities are cached.
    auto otherDesc=bd;otherDesc.ByteWidth=64;ComPtr<ID3D11Buffer> other;
    gpuCheck(dev->CreateBuffer(&otherDesc,nullptr,other.GetAddressOf()),"non-camera buffer");
#endif
    for(int i=0;i<3;i++) {
#ifdef OWMC_LIVE_BLEND
        for(int n=0;n<8;n++) {
            D3D11_MAPPED_SUBRESOURCE mapped{};
            gpuCheck(ctx->Map(other.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"non-camera upload");
            memset(mapped.pData,17+i,64);ctx->Unmap(other.Get(),0);
        }
#endif
        ctx->RSSetState(raster.Get());ctx->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);ctx->VSSetShader(vs.Get(),nullptr,0);ctx->PSSetShader(ps.Get(),nullptr,0);
        D3D11_VIEWPORT vp{0,0,128,72,0,1};ctx->RSSetViewports(1,&vp);ID3D11RenderTargetView* targets[6];for(int k=0;k<6;k++) targets[k]=views[k].Get();ctx->OMSetRenderTargets(6,targets,dsv.Get());ctx->OMSetDepthStencilState(depthState.Get(),96);
        ctx->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_DEPTH|D3D11_CLEAR_STENCIL,
#ifdef OWMC_SELECTION_FIXTURE
        1.f,
#else
        .25f,
#endif
        0);lens(-.803333f,1.428147f);ctx->Draw(0,0);
#ifdef OWMC_LIVE_BLEND
        if(i!=1) {
#ifdef OWMC_SELECTION_FIXTURE
        ctx->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_STENCIL,1,0);
#endif
        lens(-1.325167f,2.355852f);ctx->Draw(3,0);lens(-.803333f,1.428147f);ctx->Draw(0,0);}
#else
        lens(-1.12820041f,2.00568986f);ctx->Draw(3,0);lens(-.803333f,1.428147f);ctx->Draw(0,0);
#endif
        auto* target=rtv.Get();ctx->OMSetRenderTargets(1,&target,dsv.Get());FLOAT red[]{1,0,0,1};ctx->ClearRenderTargetView(rtv.Get(),red);
#ifdef OWMC_OFFSCREEN_FIXTURE
        // Current native fullscreen uses a dual-output stencil boundary. Only
        // its first color receives composition; geometry MRTs above stay excluded.
        ID3D11RenderTargetView* dual[]{target,views[1].Get()};ctx->OMSetRenderTargets(2,dual,dsv.Get());
#endif
#ifdef OWMC_LIVE_BLEND
        if(i!=2)
#endif
        ctx->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_STENCIL,1,0);
        FLOAT green[]{0,1,0,1};ComPtr<ID3D11DeviceContext1> ctx1;gpuCheck(ctx.As(&ctx1),"test HUD context");D3D11_RECT hudRect{0,0,128,4};ctx1->ClearView(rtv.Get(),green,&hudRect,1);
#ifdef OWMC_OFFSCREEN_FIXTURE
        ctx->CopySubresourceRegion(presentColor.Get(),0,0,0,0,color.Get(),0,nullptr);
#endif
        gpuCheck(swap->Present(0,0),"present");
#if defined(OWMC_LIVE_BLEND)
        D3D11_TEXTURE2D_DESC readDesc{};presentColor->GetDesc(&readDesc);readDesc.Usage=D3D11_USAGE_STAGING;readDesc.BindFlags=0;readDesc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
        ComPtr<ID3D11Texture2D> readback;gpuCheck(dev->CreateTexture2D(&readDesc,nullptr,readback.GetAddressOf()),"live fixture readback");ctx->CopyResource(readback.Get(),presentColor.Get());D3D11_MAPPED_SUBRESOURCE pixels{};gpuCheck(ctx->Map(readback.Get(),0,D3D11_MAP_READ,0,&pixels),"live fixture pixels");
        for(UINT y=0;y<72;y++) for(UINT x=0;x<128;x++) {auto* p=static_cast<unsigned char*>(pixels.pData)+y*pixels.RowPitch+x*4;bool hand=i==0&&y>=4&&x<64;assert(p[0]==(hand?255:0)&&p[1]==(y<4?255:0)&&p[2]==(y>=4&&!hand?255:0)&&p[3]==255);}
        ctx->Unmap(readback.Get(),0);
#endif
    }
    void(*dump)()=nullptr;auto dumpAddress=GetProcAddress(module,"OWMC_HandDepthTestDump");memcpy(&dump,&dumpAddress,sizeof dump);assert(dump);dump();
    assert(verify());assert(*reinterpret_cast<void***>(swap.Get())==originalSwap);assert(*reinterpret_cast<void***>(ctx.Get())==originalContext);
    ComPtr<ID3D11VertexShader> current;ctx->VSGetShader(current.GetAddressOf(),nullptr,nullptr);assert(current.Get()==vs.Get());
    ComPtr<ID3D11DepthStencilState> currentDepth;UINT stencil=0;ctx->OMGetDepthStencilState(currentDepth.GetAddressOf(),&stencil);assert(currentDepth.Get()==depthState.Get()&&stencil==96);
    // Observation must release original color resources, otherwise the user
    // would be unable to change window size after the three-frame stop.
    ctx->ClearState();rtv.Reset();color.Reset();presentColor.Reset();gpuCheck(swap->ResizeBuffers(1,160,90,DXGI_FORMAT_R8G8B8A8_UNORM,0),"resize after observation");
    DestroyWindow(window);std::cout<<"PASS: same-frame hand-depth capture, optional world blend, subsequent HUD, native shader/depth state, three-frame restoration and resize.\n";
}
