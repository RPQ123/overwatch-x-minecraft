#include "world_blend.hpp"

namespace passthrough {
namespace {
constexpr const char* source=R"(
Texture2D<float4> originalColor:register(t0);
Texture2D<float4> worldColor:register(t1);
Texture2D<uint> handMask:register(t2);
struct V {float4 pos:SV_Position;float2 uv:TEXCOORD;};
V VS(uint id:SV_VertexID) {V o;o.uv=float2((id<<1)&2,id&2);o.pos=float4(o.uv.x*2-1,1-o.uv.y*2,0,1);return o;}
float4 PS(V i):SV_Target {
    uint w,h;worldColor.GetDimensions(w,h);int2 xy=int2(i.pos.xy);
    float4 native=originalColor.Load(int3(xy,0));
    int2 guest=min(int2(i.uv*float2(w,h)),int2(w,h)-1);
    float4 result=handMask.Load(int3(xy,0))!=0?native:worldColor.Load(int3(guest,0));
    // Keep native alpha for the native HUD's subsequent blend operations.
    result.a=native.a;return result;
})";
}
WorldBlend::WorldBlend(ID3D11Device* input):device(input) {
    device->GetImmediateContext(context.GetAddressOf());
    gpuCheck(device->CreateDeferredContext(0,commands.GetAddressOf()),"blend owned command context");
    auto compile=[&](const char* entry,const char* profile) {ComPtr<ID3DBlob> code,error;auto hr=D3DCompile(source,strlen(source),nullptr,nullptr,nullptr,entry,profile,D3DCOMPILE_ENABLE_STRICTNESS,0,code.GetAddressOf(),error.GetAddressOf());
        if(FAILED(hr)&&error) throw std::runtime_error(std::string(static_cast<char*>(error->GetBufferPointer()),error->GetBufferSize()));
        gpuCheck(hr,"compile world blend");return code;};
    auto v=compile("VS","vs_5_0"),p=compile("PS","ps_5_0");gpuCheck(device->CreateVertexShader(v->GetBufferPointer(),v->GetBufferSize(),nullptr,vs.GetAddressOf()),"blend VS");gpuCheck(device->CreatePixelShader(p->GetBufferPointer(),p->GetBufferSize(),nullptr,ps.GetAddressOf()),"blend PS");
    D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;gpuCheck(device->CreateRasterizerState(&rd,raster.GetAddressOf()),"blend raster");
}
void WorldBlend::draw(ID3D11Texture2D* target,const WorldFrame& f,const std::vector<unsigned char>& mask) {
    if(owner!=std::this_thread::get_id()) throw std::runtime_error("Blend called outside render owner");
    D3D11_TEXTURE2D_DESC td{};target->GetDesc(&td);
    if(td.SampleDesc.Count!=1||td.ArraySize!=1||td.MipLevels!=1||!td.Width||!td.Height||td.Width>4096||td.Height>2160||mask.size()!=size_t(td.Width)*td.Height||
       f.rgba.size()!=size_t(f.width)*f.height*4||!f.width||!f.height||f.width>2560||f.height>1440) throw std::runtime_error("Blend bounds");
    if(td.Format!=DXGI_FORMAT_R8G8B8A8_UNORM&&td.Format!=DXGI_FORMAT_B8G8R8A8_UNORM) throw std::runtime_error("Uncalibrated blend target format");
    auto make=[&](UINT w,UINT h,DXGI_FORMAT fmt,const void* data,UINT pitch) {D3D11_TEXTURE2D_DESC d{};d.Width=w;d.Height=h;d.MipLevels=1;d.ArraySize=1;d.Format=fmt;d.SampleDesc.Count=1;d.BindFlags=D3D11_BIND_SHADER_RESOURCE;d.Usage=data?D3D11_USAGE_IMMUTABLE:D3D11_USAGE_DEFAULT;
        D3D11_SUBRESOURCE_DATA init{data,pitch,0};ComPtr<ID3D11Texture2D> image;gpuCheck(device->CreateTexture2D(&d,data?&init:nullptr,image.GetAddressOf()),"blend input texture");return image;};
    auto original=make(td.Width,td.Height,td.Format,nullptr,0);context->CopyResource(original.Get(),target);
    auto world=make(f.width,f.height,DXGI_FORMAT_R8G8B8A8_UNORM,f.rgba.data(),f.width*4);auto hands=make(td.Width,td.Height,DXGI_FORMAT_R8_UINT,mask.data(),td.Width);
    ComPtr<ID3D11ShaderResourceView> originalView,worldView,handView;gpuCheck(device->CreateShaderResourceView(original.Get(),nullptr,originalView.GetAddressOf()),"blend native color");gpuCheck(device->CreateShaderResourceView(world.Get(),nullptr,worldView.GetAddressOf()),"blend world color");gpuCheck(device->CreateShaderResourceView(hands.Get(),nullptr,handView.GetAddressOf()),"blend hand mask");
    ComPtr<ID3D11RenderTargetView> output;gpuCheck(device->CreateRenderTargetView(target,nullptr,output.GetAddressOf()),"blend output");
    // Record only our fullscreen triangle on an unhooked owned context. This
    // avoids re-entering original native draw observers during state switching.
    commands->ClearState();auto* rtv=output.Get();commands->OMSetRenderTargets(1,&rtv,nullptr);D3D11_VIEWPORT vp{0,0,float(td.Width),float(td.Height),0,1};commands->RSSetViewports(1,&vp);commands->RSSetState(raster.Get());
    commands->IASetInputLayout(nullptr);commands->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);commands->VSSetShader(vs.Get(),nullptr,0);commands->PSSetShader(ps.Get(),nullptr,0);
    ID3D11ShaderResourceView* views[]={originalView.Get(),worldView.Get(),handView.Get()};commands->PSSetShaderResources(0,3,views);commands->Draw(3,0);
    ComPtr<ID3D11CommandList> list;gpuCheck(commands->FinishCommandList(FALSE,list.GetAddressOf()),"finish own blend commands");
    context->ExecuteCommandList(list.Get(),TRUE); // Runtime preserves all original context state.
    gpuCheck(device->GetDeviceRemovedReason(),"blend device health");
}
}
