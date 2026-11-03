#include "../src/world_blend.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main() {
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;gpuCheck(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,device.GetAddressOf(),nullptr,context.GetAddressOf()),"blend test device");
    D3D11_TEXTURE2D_DESC d{};d.Width=128;d.Height=72;d.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.MipLevels=1;d.ArraySize=1;d.SampleDesc.Count=1;d.BindFlags=D3D11_BIND_RENDER_TARGET;
    ComPtr<ID3D11Texture2D> target;gpuCheck(device->CreateTexture2D(&d,nullptr,target.GetAddressOf()),"blend target");ComPtr<ID3D11RenderTargetView> rtv;gpuCheck(device->CreateRenderTargetView(target.Get(),nullptr,rtv.GetAddressOf()),"blend rtv");
    float red[]={1,0,0,.5f};context->ClearRenderTargetView(rtv.Get(),red);auto* bound=rtv.Get();context->OMSetRenderTargets(1,&bound,nullptr);
    D3D11_VIEWPORT sentinel{3,5,100,60,.2f,.9f};context->RSSetViewports(1,&sentinel);context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_LINESTRIP);
    D3D11_BUFFER_DESC bd{};bd.ByteWidth=64;bd.Usage=D3D11_USAGE_DEFAULT;bd.BindFlags=D3D11_BIND_UNORDERED_ACCESS;bd.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;bd.StructureByteStride=4;
    ComPtr<ID3D11Buffer> buffer;gpuCheck(device->CreateBuffer(&bd,nullptr,buffer.GetAddressOf()),"sentinel UAV buffer");D3D11_UNORDERED_ACCESS_VIEW_DESC ud{};ud.Format=DXGI_FORMAT_UNKNOWN;ud.ViewDimension=D3D11_UAV_DIMENSION_BUFFER;ud.Buffer.NumElements=16;ComPtr<ID3D11UnorderedAccessView> uav;gpuCheck(device->CreateUnorderedAccessView(buffer.Get(),&ud,uav.GetAddressOf()),"sentinel UAV");auto* unordered=uav.Get();UINT keep=UINT(-1);context->CSSetUnorderedAccessViews(3,1,&unordered,&keep);
    WorldFrame frame;frame.width=32;frame.height=18;frame.rgba.assign(32*18*4,255);for(size_t i=0;i<frame.rgba.size();i+=4) {frame.rgba[i]=0;frame.rgba[i+1]=0;}
    std::vector<unsigned char> mask(128*72);for(int y=0;y<72;y++) for(int x=0;x<64;x++) mask[y*128+x]=255;
    {WorldBlend blend(device.Get());blend.draw(target.Get(),frame,mask);}
    UINT count=1;D3D11_VIEWPORT restored{};context->RSGetViewports(&count,&restored);assert(count==1&&restored.TopLeftX==3&&restored.MinDepth==.2f);
    D3D11_PRIMITIVE_TOPOLOGY topology;context->IAGetPrimitiveTopology(&topology);assert(topology==D3D11_PRIMITIVE_TOPOLOGY_LINESTRIP);
    ComPtr<ID3D11RenderTargetView> current;context->OMGetRenderTargets(1,current.GetAddressOf(),nullptr);assert(current.Get()==rtv.Get());ComPtr<ID3D11UnorderedAccessView> currentUav;context->CSGetUnorderedAccessViews(3,1,currentUav.GetAddressOf());assert(currentUav.Get()==uav.Get());
    d.Usage=D3D11_USAGE_STAGING;d.BindFlags=0;d.CPUAccessFlags=D3D11_CPU_ACCESS_READ;ComPtr<ID3D11Texture2D> readback;gpuCheck(device->CreateTexture2D(&d,nullptr,readback.GetAddressOf()),"blend test readback");context->CopyResource(readback.Get(),target.Get());D3D11_MAPPED_SUBRESOURCE m{};gpuCheck(context->Map(readback.Get(),0,D3D11_MAP_READ,0,&m),"blend test pixels");
    for(int y=0;y<72;y++) for(int x=0;x<128;x++) {auto* pixel=static_cast<unsigned char*>(m.pData)+y*m.RowPitch+x*4;assert(pixel[0]==(x<64?255:0)&&pixel[1]==0&&pixel[2]==(x<64?0:255)&&pixel[3]==128);}
    context->Unmap(readback.Get(),0);
    std::cout<<"PASS: native hand pixels, full guest background, native alpha, viewport/topology/RTV/CS-UAV restoration.\n";
}
