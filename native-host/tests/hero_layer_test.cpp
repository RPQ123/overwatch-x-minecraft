#include "../src/render.hpp"
#include <cassert>
#include <iostream>
#include <windows.h>
int main() {
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"OWMCLayerHiddenTest";RegisterClassW(&wc);
    HWND window=CreateWindowW(wc.lpszClassName,L"Hidden layer test",WS_OVERLAPPEDWINDOW,0,0,160,120,nullptr,nullptr,wc.hInstance,nullptr);assert(window);
    DXGI_SWAP_CHAIN_DESC sd{};sd.BufferDesc.Width=128;sd.BufferDesc.Height=72;sd.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sd.SampleDesc.Count=1;sd.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sd.BufferCount=1;sd.OutputWindow=window;sd.Windowed=TRUE;
    ComPtr<ID3D11Device> dev;ComPtr<ID3D11DeviceContext> ctx;ComPtr<IDXGISwapChain> swap;check(D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&sd,swap.GetAddressOf(),dev.GetAddressOf(),nullptr,ctx.GetAddressOf()),"layer test device");
    ComPtr<ID3D11Texture2D> color,z;check(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(color.GetAddressOf())),"color");
    ComPtr<ID3D11RenderTargetView> rtv;check(dev->CreateRenderTargetView(color.Get(),nullptr,rtv.GetAddressOf()),"rtv");
    D3D11_TEXTURE2D_DESC zd{};zd.Width=128;zd.Height=72;zd.MipLevels=1;zd.ArraySize=1;zd.Format=DXGI_FORMAT_R24G8_TYPELESS;zd.SampleDesc.Count=1;zd.BindFlags=D3D11_BIND_DEPTH_STENCIL;check(dev->CreateTexture2D(&zd,nullptr,z.GetAddressOf()),"z");
    D3D11_DEPTH_STENCIL_VIEW_DESC vd{};vd.Format=DXGI_FORMAT_D24_UNORM_S8_UINT;vd.ViewDimension=D3D11_DSV_DIMENSION_TEXTURE2D;
    ComPtr<ID3D11DepthStencilView> dsv;check(dev->CreateDepthStencilView(z.Get(),&vd,dsv.GetAddressOf()),"dsv");
    D3D11_BUFFER_DESC bd{};bd.ByteWidth=544;bd.Usage=D3D11_USAGE_DYNAMIC;bd.CPUAccessFlags=D3D11_CPU_ACCESS_WRITE;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
    ComPtr<ID3D11Buffer> cb;check(dev->CreateBuffer(&bd,nullptr,cb.GetAddressOf()),"cb");
    void** originalSwap=*reinterpret_cast<void***>(swap.Get());void** originalContext=*reinterpret_cast<void***>(ctx.Get());
    HMODULE module=LoadLibraryW(L"native-host/build/owhero-layer-probe-v1.dll");assert(module);
    auto attach=reinterpret_cast<BOOL(*)(IDXGISwapChain*)>(GetProcAddress(module,"OWMC_LayerTestAttach"));auto verify=reinterpret_cast<BOOL(*)()>(GetProcAddress(module,"OWMC_LayerTestVerify"));assert(attach&&verify&&attach(swap.Get()));
    for(int i=0;i<3;i++) {
        auto* target=rtv.Get();ctx->OMSetRenderTargets(1,&target,dsv.Get());D3D11_VIEWPORT vp{0,0,128,72,0,1};ctx->RSSetViewports(1,&vp);
        FLOAT red[]{1,0,0,1};ctx->ClearRenderTargetView(rtv.Get(),red);ctx->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_DEPTH|D3D11_CLEAR_STENCIL,1,3);
        D3D11_MAPPED_SUBRESOURCE mapped{};check(ctx->Map(cb.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"map");std::array<float,136> values{};values[0]=-.8f;std::memcpy(mapped.pData,values.data(),544);ctx->Unmap(cb.Get(),0);
        auto* buffer=cb.Get();ctx->VSSetConstantBuffers(9,1,&buffer);ctx->Draw(0,0);
        ctx->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_STENCIL,1,0);FLOAT green[]{0,1,0,1};ctx->ClearRenderTargetView(rtv.Get(),green);check(swap->Present(0,0),"present");
    }
    assert(verify());assert(*reinterpret_cast<void***>(swap.Get())==originalSwap);assert(*reinterpret_cast<void***>(ctx.Get())==originalContext);
    DestroyWindow(window);std::cout<<"Actual WARP color/depth capture, upload observation and automatic restoration passed.\n";
}
