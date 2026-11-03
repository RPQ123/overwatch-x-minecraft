#include "../src/render.hpp"
#include <windows.h>
#include <cassert>
#include <iostream>

int main() {
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"OWMCTraceHidden";RegisterClassW(&wc);
    HWND window=CreateWindowW(wc.lpszClassName,L"Trace test",WS_OVERLAPPEDWINDOW,0,0,160,120,nullptr,nullptr,wc.hInstance,nullptr);assert(window);
    DXGI_SWAP_CHAIN_DESC desc{};desc.BufferDesc.Width=128;desc.BufferDesc.Height=72;desc.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;
    desc.SampleDesc.Count=1;desc.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;desc.BufferCount=1;desc.OutputWindow=window;desc.Windowed=TRUE;
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;ComPtr<IDXGISwapChain> swap;
    check(D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&desc,
        swap.GetAddressOf(),device.GetAddressOf(),nullptr,context.GetAddressOf()),"trace fake host");
    ComPtr<ID3D11Texture2D> target;check(swap->GetBuffer(0,__uuidof(ID3D11Texture2D),reinterpret_cast<void**>(target.GetAddressOf())),"target");
    ComPtr<ID3D11RenderTargetView> rtv;check(device->CreateRenderTargetView(target.Get(),nullptr,rtv.GetAddressOf()),"rtv");
    D3D11_TEXTURE2D_DESC depthDesc{};depthDesc.Width=128;depthDesc.Height=72;depthDesc.MipLevels=1;depthDesc.ArraySize=1;
    depthDesc.Format=DXGI_FORMAT_D32_FLOAT;depthDesc.SampleDesc.Count=1;depthDesc.BindFlags=D3D11_BIND_DEPTH_STENCIL;
    ComPtr<ID3D11Texture2D> depth;ComPtr<ID3D11DepthStencilView> dsv;
    check(device->CreateTexture2D(&depthDesc,nullptr,depth.GetAddressOf()),"depth");check(device->CreateDepthStencilView(depth.Get(),nullptr,dsv.GetAddressOf()),"dsv");
    D3D11_DEPTH_STENCIL_DESC stateDesc{};stateDesc.DepthEnable=TRUE;stateDesc.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL;stateDesc.DepthFunc=D3D11_COMPARISON_GREATER_EQUAL;
    ComPtr<ID3D11DepthStencilState> state;check(device->CreateDepthStencilState(&stateDesc,state.GetAddressOf()),"greater state");
    const char source[]=R"(float4 vs(uint id:SV_VertexID):SV_POSITION { return float4(id==1?.5:-.5,id==2?.5:-.5,.5,1); }
        float4 ps():SV_TARGET { return float4(1,1,1,1); })";
    ComPtr<ID3DBlob> vsCode,psCode;
    check(D3DCompile(source,sizeof(source),nullptr,nullptr,nullptr,"vs","vs_5_0",0,0,vsCode.GetAddressOf(),nullptr),"vs compile");
    check(D3DCompile(source,sizeof(source),nullptr,nullptr,nullptr,"ps","ps_5_0",0,0,psCode.GetAddressOf(),nullptr),"ps compile");
    ComPtr<ID3D11VertexShader> vs;ComPtr<ID3D11PixelShader> ps;
    check(device->CreateVertexShader(vsCode->GetBufferPointer(),vsCode->GetBufferSize(),nullptr,vs.GetAddressOf()),"vs");
    check(device->CreatePixelShader(psCode->GetBufferPointer(),psCode->GetBufferSize(),nullptr,ps.GetAddressOf()),"ps");
    void** contextTable=*reinterpret_cast<void***>(context.Get());void** swapTable=*reinterpret_cast<void***>(swap.Get());
    HMODULE module=LoadLibraryW(L"native-host\\build\\owmc-depth-trace.dll");assert(module);
    auto attach=reinterpret_cast<BOOL(*)(IDXGISwapChain*)>(GetProcAddress(module,"OWMC_TraceTestAttach"));
    auto verify=reinterpret_cast<BOOL(*)()>(GetProcAddress(module,"OWMC_TraceTestVerify"));assert(attach&&verify&&attach(swap.Get()));
    assert(*reinterpret_cast<void***>(context.Get())!=contextTable&&*reinterpret_cast<void***>(swap.Get())!=swapTable);
    for(int frame=0;frame<3;frame++) {
        ID3D11RenderTargetView* view=rtv.Get();context->OMSetRenderTargets(1,&view,dsv.Get());context->ClearDepthStencilView(dsv.Get(),D3D11_CLEAR_DEPTH,0,0);
        context->OMSetDepthStencilState(state.Get(),0);D3D11_VIEWPORT viewport{0,0,128,72,0,1};context->RSSetViewports(1,&viewport);
        context->VSSetShader(vs.Get(),nullptr,0);context->PSSetShader(ps.Get(),nullptr,0);context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        context->Draw(3,0);check(swap->Present(0,0),"trace present");
    }
    assert(verify());assert(*reinterpret_cast<void***>(context.Get())==contextTable&&*reinterpret_cast<void***>(swap.Get())==swapTable);
    ComPtr<ID3D11DepthStencilState> restored;UINT ref=0;context->OMGetDepthStencilState(restored.GetAddressOf(),&ref);assert(restored.Get()==state.Get());
    DestroyWindow(window);std::cout<<"Three-frame depth/viewport observation, original callback chaining and both vtable restorations passed.\n";
}
