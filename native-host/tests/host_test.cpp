#include "../src/render.hpp"
#include <cassert>
#include <windows.h>
#include <iostream>

int main(int argc,char** argv) {
    assert(argc==2);
    WNDCLASSW windowClass{};windowClass.lpfnWndProc=DefWindowProcW;windowClass.hInstance=GetModuleHandleW(nullptr);
    windowClass.lpszClassName=L"OWMCHiddenHostTest";RegisterClassW(&windowClass);
    HWND window=CreateWindowW(windowClass.lpszClassName,L"Hidden render test",WS_OVERLAPPEDWINDOW,0,0,160,120,
                              nullptr,nullptr,windowClass.hInstance,nullptr);
    assert(window);
    DXGI_SWAP_CHAIN_DESC desc{};desc.BufferDesc.Width=128;desc.BufferDesc.Height=72;desc.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;
    desc.SampleDesc.Count=1;desc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;desc.BufferCount=1;desc.OutputWindow=window;desc.Windowed=TRUE;
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;ComPtr<IDXGISwapChain> swap;
    check(D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,
        &desc,swap.GetAddressOf(),device.GetAddressOf(),nullptr,context.GetAddressOf()),"fake swapchain");
    void** original=*reinterpret_cast<void***>(swap.Get());
    void** originalContext=*reinterpret_cast<void***>(context.Get());
    bool scene=std::filesystem::path(argv[1]).filename()!=L"owmc-render-probe.dll"&&std::filesystem::path(argv[1]).filename()!=L"owmc-render-probe-v2.dll";
    ComPtr<ID3D11RenderTargetView> rtv;ComPtr<ID3D11DepthStencilView> dsv;
    if(scene) {
        ComPtr<ID3D11Texture2D> target;check(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())),"test target");
        check(device->CreateRenderTargetView(target.Get(),nullptr,rtv.GetAddressOf()),"test scene color");
        D3D11_TEXTURE2D_DESC desc{};desc.Width=128;desc.Height=72;desc.MipLevels=1;desc.ArraySize=1;desc.Format=DXGI_FORMAT_R24G8_TYPELESS;
        desc.SampleDesc.Count=1;desc.BindFlags=D3D11_BIND_DEPTH_STENCIL;
        ComPtr<ID3D11Texture2D> depth;check(device->CreateTexture2D(&desc,nullptr,depth.GetAddressOf()),"test scene depth");
        D3D11_DEPTH_STENCIL_VIEW_DESC view{};view.Format=DXGI_FORMAT_D24_UNORM_S8_UINT;view.ViewDimension=D3D11_DSV_DIMENSION_TEXTURE2D;
        check(device->CreateDepthStencilView(depth.Get(),&view,dsv.GetAddressOf()),"test scene dsv");
    }
    HMODULE plugin=LoadLibraryW(std::filesystem::absolute(argv[1]).wstring().c_str());assert(plugin);
    auto attach=reinterpret_cast<BOOL(*)(IDXGISwapChain*)>(GetProcAddress(plugin,"OWMC_TestAttach"));
    auto draws=reinterpret_cast<unsigned(*)()>(GetProcAddress(plugin,"OWMC_TestDraws"));
    auto stop=reinterpret_cast<void(*)()>(GetProcAddress(plugin,"OWMC_TestStop"));assert(attach&&draws&&stop);
    auto placements=reinterpret_cast<unsigned(*)()>(GetProcAddress(plugin,"OWMC_TestPlacements"));
    assert(attach(swap.Get()));assert(*reinterpret_cast<void***>(swap.Get())!=original);
    bool sceneCamera=std::filesystem::path(argv[1]).filename()==L"owmc-render-probe-v7.dll"||std::filesystem::path(argv[1]).filename()==L"owmc-render-probe-v8.dll"||std::filesystem::path(argv[1]).filename()==L"owmc-render-probe-v9.dll";
    std::array<float,136> camera{};
    camera[0]=-.803333223f;camera[3]=1;camera[5]=1.42814779f;camera[10]=1.00004995f;camera[11]=1;camera[14]=-.100005f;
    for(int i=0;i<4;i++) {camera[16+i*5]=1;camera[32+i*5]=1;}
    camera[112]=1.f/128;camera[113]=1.f/72;
    ComPtr<ID3D11Buffer> cb,updatedCb;
    ComPtr<ID3D11VertexShader> hostVs;ComPtr<ID3D11PixelShader> hostPs;
    if(sceneCamera) {
        D3D11_BUFFER_DESC bd{};bd.ByteWidth=544;bd.Usage=D3D11_USAGE_DYNAMIC;bd.CPUAccessFlags=D3D11_CPU_ACCESS_WRITE;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
        check(device->CreateBuffer(&bd,nullptr,cb.GetAddressOf()),"fake original camera upload");
        bd.Usage=D3D11_USAGE_DEFAULT;bd.CPUAccessFlags=0;
        check(device->CreateBuffer(&bd,nullptr,updatedCb.GetAddressOf()),"fake original camera update");
        const char shader[]=R"(float4 vs(uint id:SV_VertexID):SV_POSITION {return float4(id==1?.5:-.5,id==2?.5:-.5,1,1);}
            float4 ps():SV_TARGET {return float4(1,1,1,1);})";
        ComPtr<ID3DBlob> v,p;
        check(D3DCompile(shader,sizeof(shader),nullptr,nullptr,nullptr,"vs","vs_5_0",0,0,v.GetAddressOf(),nullptr),"host vs");
        check(D3DCompile(shader,sizeof(shader),nullptr,nullptr,nullptr,"ps","ps_5_0",0,0,p.GetAddressOf(),nullptr),"host ps");
        check(device->CreateVertexShader(v->GetBufferPointer(),v->GetBufferSize(),nullptr,hostVs.GetAddressOf()),"host vertex shader");
        check(device->CreatePixelShader(p->GetBufferPointer(),p->GetBufferSize(),nullptr,hostPs.GetAddressOf()),"host pixel shader");
    }
    auto sceneScale=reinterpret_cast<float(*)()>(GetProcAddress(plugin,"OWMC_TestSceneScale"));
    for(int frame=0;frame<3;frame++) {
        float expectedSceneScale=0;
        if(scene) {
            ID3D11RenderTargetView* target=rtv.Get();context->OMSetRenderTargets(1,&target,dsv.Get());
            context->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_DEPTH,1,0);
            D3D11_VIEWPORT viewport{0,0,128,72,0,1};context->RSSetViewports(1,&viewport);
            if(sceneCamera) {
                camera[0]=-(.803333223f+frame*.05f);camera[5]=-camera[0]*128/72;
                expectedSceneScale=camera[0];
                ID3D11Buffer* buffer=nullptr;
                if(frame==1) {context->UpdateSubresource(updatedCb.Get(),0,nullptr,camera.data(),0,0);buffer=updatedCb.Get();}
                else {
                    D3D11_MAPPED_SUBRESOURCE mapped{};check(context->Map(cb.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"original camera map");
                    std::memcpy(mapped.pData,camera.data(),544);context->Unmap(cb.Get(),0);buffer=cb.Get();
                }
                context->VSSetConstantBuffers(9,1,&buffer);context->VSSetShader(hostVs.Get(),nullptr,0);context->PSSetShader(hostPs.Get(),nullptr,0);
                context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);context->Draw(3,0);
                // A later first-person lens uses the same global layout and
                // depth. It must not replace the already selected world lens.
                auto weaponCamera=camera;weaponCamera[0]=-1.12820041f;weaponCamera[5]=2.00568986f;
                context->UpdateSubresource(updatedCb.Get(),0,nullptr,weaponCamera.data(),0,0);
                buffer=updatedCb.Get();context->VSSetConstantBuffers(9,1,&buffer);context->Draw(3,0);
            }
            context->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_STENCIL,1,0);
            assert(draws()==static_cast<unsigned>(frame+1)); // Draw precedes Present; no overlay fallback.
            if(sceneCamera) {assert(sceneScale&&sceneScale()==expectedSceneScale);ComPtr<ID3D11Buffer> bound;context->VSGetConstantBuffers(9,1,bound.GetAddressOf());assert(bound.Get()==updatedCb.Get());}
        }
        check(swap->Present(0,0),"probe present");
    }
    assert(draws()==3);if(placements) assert(placements()==1);stop();assert(*reinterpret_cast<void***>(swap.Get())==original);
    assert(*reinterpret_cast<void***>(context.Get())==originalContext);
    check(swap->Present(0,0),"restored present");assert(draws()==3);
    // The module deliberately remains loaded until exit, matching the real host's safe stop behavior.
    DestroyWindow(window);std::cout<<"Native Present chaining, three draws and reversible vtable stop passed.\n";
}
