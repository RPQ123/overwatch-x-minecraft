#include "../src/render.hpp"
#include <cassert>
#include <iostream>

int main(int argc,char** argv) {
    assert(argc==2);
    ComPtr<ID3D11Device> device; ComPtr<ID3D11DeviceContext> context;
    check(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,
                           device.GetAddressOf(),nullptr,context.GetAddressOf()),"WARP device");
    D3D11_TEXTURE2D_DESC desc{};desc.Width=128;desc.Height=72;desc.MipLevels=1;desc.ArraySize=1;
    desc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;desc.SampleDesc.Count=1;desc.BindFlags=D3D11_BIND_RENDER_TARGET;
    ComPtr<ID3D11Texture2D> target;check(device->CreateTexture2D(&desc,nullptr,target.GetAddressOf()),"target");
    ComPtr<ID3D11RenderTargetView> originalView;check(device->CreateRenderTargetView(target.Get(),nullptr,originalView.GetAddressOf()),"view");
    ID3D11RenderTargetView* targetView=originalView.Get();context->OMSetRenderTargets(1,&targetView,nullptr);
    const float background[]={.02f,.1f,.3f,1};context->ClearRenderTargetView(targetView,background);
    D3D11_VIEWPORT sentinel{3,5,109,57,.2f,.9f};context->RSSetViewports(1,&sentinel);
    context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_LINESTRIP);
    Renderer renderer(device.Get(),loadMesh(std::filesystem::path(argv[1]).wstring()));
    renderer.draw(target.Get(),Camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f},{-.5f,-.5f,4.f});
    UINT count=1;D3D11_VIEWPORT restored{};context->RSGetViewports(&count,&restored);
    assert(count==1 && restored.TopLeftX==3 && restored.TopLeftY==5 && restored.Width==109 && restored.MinDepth==.2f);
    D3D11_PRIMITIVE_TOPOLOGY topology;context->IAGetPrimitiveTopology(&topology);
    assert(topology==D3D11_PRIMITIVE_TOPOLOGY_LINESTRIP);
    ComPtr<ID3D11RenderTargetView> restoredView;context->OMGetRenderTargets(1,restoredView.GetAddressOf(),nullptr);
    assert(restoredView.Get()==originalView.Get());
    ComPtr<ID3D11VertexShader> shader;context->VSGetShader(shader.GetAddressOf(),nullptr,nullptr);assert(!shader);
    desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;desc.Usage=D3D11_USAGE_STAGING;
    ComPtr<ID3D11Texture2D> staging;check(device->CreateTexture2D(&desc,nullptr,staging.GetAddressOf()),"staging");
    context->CopyResource(staging.Get(),target.Get());
    D3D11_MAPPED_SUBRESOURCE pixels{};check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"read pixels");
    auto* center=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+64*4;
    assert(center[0]>30 && std::abs(static_cast<int>(center[0])-center[1])<=1 && std::abs(static_cast<int>(center[1])-center[2])<=1);
    context->Unmap(staging.Get(),0);
    // Signed host projection must put a marker on the opposite side from the
    // earlier guessed basis; this checks actual pixels through the native path.
    context->ClearRenderTargetView(targetView,background);
    NativeProjection native{{1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1},
                            {-1,0,0,0, 0,2,0,0, 0,0,1,1, 0,0,-.1f,0},0,0,128,72};
    renderer.draw(target.Get(),Camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f},{-2.f,-.5f,4.f},&native);
    count=1;context->RSGetViewports(&count,&restored);assert(restored.TopLeftX==3&&restored.Width==109);
    context->CopyResource(staging.Get(),target.Get());
    check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"native matrix pixels");
    auto* expected=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+85*4;
    auto* mirrored=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+43*4;
    assert(expected[0]>30 && std::abs(static_cast<int>(expected[0])-expected[1])<=1);
    assert(mirrored[2]>mirrored[0]+40);
    context->Unmap(staging.Get(),0);
    D3D11_TEXTURE2D_DESC sceneDepthDesc{};sceneDepthDesc.Width=128;sceneDepthDesc.Height=72;sceneDepthDesc.MipLevels=1;sceneDepthDesc.ArraySize=1;
    sceneDepthDesc.Format=DXGI_FORMAT_D32_FLOAT;sceneDepthDesc.SampleDesc.Count=1;sceneDepthDesc.BindFlags=D3D11_BIND_DEPTH_STENCIL;
    ComPtr<ID3D11Texture2D> sceneDepth;ComPtr<ID3D11DepthStencilView> sceneView;
    check(device->CreateTexture2D(&sceneDepthDesc,nullptr,sceneDepth.GetAddressOf()),"shared test depth");
    check(device->CreateDepthStencilView(sceneDepth.Get(),nullptr,sceneView.GetAddressOf()),"shared test dsv");
    context->ClearRenderTargetView(targetView,background);context->ClearDepthStencilView(sceneView.Get(),D3D11_CLEAR_DEPTH,.9f,0);
    renderer.drawScene(targetView,sceneView.Get(),Camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f},{-2.f,-.5f,4.f},native);
    context->CopyResource(staging.Get(),target.Get());check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"occlusion pixels");
    expected=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+85*4;
    assert(expected[2]>expected[0]+40); // Existing foreground depth hides the cube; it wasn't cleared.
    context->Unmap(staging.Get(),0);
    context->ClearDepthStencilView(sceneView.Get(),D3D11_CLEAR_DEPTH,1.f,0);
    renderer.drawScene(targetView,sceneView.Get(),Camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f},{-2.f,-.5f,4.f},native);
    context->CopyResource(staging.Get(),target.Get());check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"visible scene pixels");
    expected=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+85*4;
    assert(expected[0]>30&&std::abs(static_cast<int>(expected[0])-expected[1])<=1);
    context->Unmap(staging.Get(),0);
    auto colored=loadMesh(std::filesystem::path(argv[1]).wstring());for(auto& vertex:colored.vertices) vertex.tint=0xff00ff00;
    renderer.update(colored);context->ClearRenderTargetView(targetView,background);context->ClearDepthStencilView(sceneView.Get(),D3D11_CLEAR_DEPTH,1.f,0);
    renderer.drawScene(targetView,sceneView.Get(),Camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f},{-2.f,-.5f,4.f},native);
    context->CopyResource(staging.Get(),target.Get());check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"tint update pixels");
    expected=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+85*4;assert(expected[1]>30&&expected[0]==0&&expected[2]==0);context->Unmap(staging.Get(),0);
    colored.vertices.clear();renderer.update(colored);context->ClearRenderTargetView(targetView,background);
    renderer.drawScene(targetView,sceneView.Get(),Camera{{0,0,0},{0,0,1},{0,1,0},1.2217305f},{-2.f,-.5f,4.f},native);
    context->CopyResource(staging.Get(),target.Get());check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"empty update pixels");
    expected=static_cast<unsigned char*>(pixels.pData)+36*pixels.RowPitch+85*4;assert(expected[2]>expected[0]+40);context->Unmap(staging.Get(),0);
    Mesh panel;panel.width=256;panel.height=64;panel.rgba.assign(256*64*4,255);
    for(auto xy:std::array<std::array<float,2>,6>{{{0,0},{1,0},{1,1},{0,0},{1,1},{0,1}}}) panel.vertices.push_back({xy[0],xy[1],0,xy[0],xy[1],1,0xffffffff});
    Renderer hud(device.Get(),panel);context->ClearRenderTargetView(targetView,background);hud.drawOverlay(target.Get());
    context->CopyResource(staging.Get(),target.Get());check(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&pixels),"HUD pixels");
    auto* panelPixel=static_cast<unsigned char*>(pixels.pData)+55*pixels.RowPitch+30*4;
    auto* outside=static_cast<unsigned char*>(pixels.pData)+10*pixels.RowPitch+10*4;
    assert(panelPixel[0]==255&&panelPixel[1]==255&&outside[2]>outside[0]+40);context->Unmap(staging.Get(),0);
    count=1;context->RSGetViewports(&count,&restored);assert(restored.TopLeftX==3&&restored.Width==109);
    context->OMGetRenderTargets(1,restoredView.ReleaseAndGetAddressOf(),nullptr);assert(restoredView.Get()==originalView.Get());
    std::cout<<"WARP pixels, native matrices, shared-depth occlusion, tint/empty updates, creative panel and host state restoration passed.\n";
}
