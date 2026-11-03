#include "live_world_blend.hpp"

namespace passthrough {
namespace {
constexpr const char* shader=R"(
Texture2D<float4> nativeColor:register(t0);
Texture2D<float4> worldColor:register(t1);
Texture2D<float> beforeDepth:register(t2);
Texture2D<float> afterDepth:register(t3);
cbuffer Transform:register(b0) {row_major float4x4 targetToSource;uint preserveHand;float handExposure;float selectionDepthCutoff;uint neutralMetal;};
struct V {float4 pos:SV_Position;float2 uv:TEXCOORD;};
V VS(uint id:SV_VertexID) {V o;o.uv=float2((id<<1)&2,id&2);o.pos=float4(o.uv.x*2-1,1-o.uv.y*2,0,1);return o;}
float4 PS(V i):SV_Target {
    int2 xy=int2(i.pos.xy);float4 native=nativeColor.Load(int3(xy,0));
    // R24 SRVs exclude stencil. Compare this frame's exact depth pair on GPU.
    bool foreground=selectionDepthCutoff>0 ? afterDepth.Load(int3(xy,0))<selectionDepthCutoff : beforeDepth.Load(int3(xy,0))!=afterDepth.Load(int3(xy,0));
    if(preserveHand&&foreground) {
        // A unit setting must be a true RGB pass-through, including deep
        // metallic shadows. Avoid even a redundant pow/log round trip there.
        if(handExposure!=1.0)native.rgb=pow(saturate(native.rgb),1.0/handExposure);
        if(neutralMetal) {
            // Counter the retained warm Hollywood reflection tint, preserving
            // linear luminance. Original geometry/alpha/HUD are untouched.
            float3 linearColor=pow(native.rgb,2.2),balanced=linearColor*float3(.93,1.0,1.23);
            float3 weights=float3(.2126,.7152,.0722);
            balanced*=dot(linearColor,weights)/max(dot(balanced,weights),.000001);
            native.rgb=pow(saturate(balanced),1.0/2.2);
        }
        return native;
    }
    float4 ray=mul(targetToSource,float4(i.uv.x*2-1,1-i.uv.y*2,-1,1));
    // Production uses a whole-frame coverage-limited warp. Clamp only numerical
    // edge roundoff; never select a second camera orientation for edge pixels.
    float2 uv=i.uv;
    if(ray.w>0) {
        float2 projected=float2(ray.x/ray.w*.5+.5,.5-ray.y/ray.w*.5);
        uv=saturate(projected);
    }
    uint w,h;worldColor.GetDimensions(w,h);
    float4 result=worldColor.Load(int3(min(int2(uv*float2(w,h)),int2(w,h)-1),0));
    result.a=native.a;return result;
})";
}
void LiveWorldBlend::assertOwner() const {if(owner!=std::this_thread::get_id()) throw std::runtime_error("Live blend outside render owner");}
LiveWorldBlend::LiveWorldBlend(ID3D11Device* input):device(input) {
    if(!input) throw std::runtime_error("No live blend device");
    device->GetImmediateContext(context.GetAddressOf());gpuCheck(device->CreateDeferredContext(0,commands.GetAddressOf()),"live owned context");
    auto compile=[&](const char* entry,const char* profile) {ComPtr<ID3DBlob> code,error;auto hr=D3DCompile(shader,strlen(shader),nullptr,nullptr,nullptr,entry,profile,D3DCOMPILE_ENABLE_STRICTNESS,0,code.GetAddressOf(),error.GetAddressOf());
        if(FAILED(hr)&&error) throw std::runtime_error(std::string(static_cast<char*>(error->GetBufferPointer()),error->GetBufferSize()));
        gpuCheck(hr,"live shader");return code;};
    auto v=compile("VS","vs_5_0"),p=compile("PS","ps_5_0");gpuCheck(device->CreateVertexShader(v->GetBufferPointer(),v->GetBufferSize(),nullptr,vs.GetAddressOf()),"live VS");gpuCheck(device->CreatePixelShader(p->GetBufferPointer(),p->GetBufferSize(),nullptr,ps.GetAddressOf()),"live PS");
    D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;gpuCheck(device->CreateRasterizerState(&rd,raster.GetAddressOf()),"live raster");
    D3D11_BUFFER_DESC bd{};bd.ByteWidth=80;bd.Usage=D3D11_USAGE_DEFAULT;bd.BindFlags=D3D11_BIND_CONSTANT_BUFFER;gpuCheck(device->CreateBuffer(&bd,nullptr,constants.GetAddressOf()),"live warp constants");
}
void LiveWorldBlend::beginFrame() {assertOwner();before=false;after=false;}
void LiveWorldBlend::depthSize(ID3D11Texture2D* source) {
    assertOwner();D3D11_TEXTURE2D_DESC d{};source->GetDesc(&d);
    if(!d.Width||!d.Height||d.Width>4096||d.Height>2160||d.MipLevels!=1||d.ArraySize!=1||d.SampleDesc.Count!=1||d.Format!=DXGI_FORMAT_R24G8_TYPELESS) throw std::runtime_error("Uncalibrated live depth");
    if(width==d.Width&&height==d.Height&&beforeDepth&&afterDepth) return;
    beforeView.Reset();afterView.Reset();beforeDepth.Reset();afterDepth.Reset();nativeColor.Reset();nativeView.Reset();colorFormat=DXGI_FORMAT_UNKNOWN;
    width=d.Width;height=d.Height;d.Usage=D3D11_USAGE_DEFAULT;d.CPUAccessFlags=0;d.MiscFlags=0;d.BindFlags=D3D11_BIND_SHADER_RESOURCE;
    gpuCheck(device->CreateTexture2D(&d,nullptr,beforeDepth.GetAddressOf()),"live before depth");gpuCheck(device->CreateTexture2D(&d,nullptr,afterDepth.GetAddressOf()),"live after depth");allocations+=2;
    D3D11_SHADER_RESOURCE_VIEW_DESC srv{};srv.Format=DXGI_FORMAT_R24_UNORM_X8_TYPELESS;srv.ViewDimension=D3D11_SRV_DIMENSION_TEXTURE2D;srv.Texture2D.MipLevels=1;
    gpuCheck(device->CreateShaderResourceView(beforeDepth.Get(),&srv,beforeView.GetAddressOf()),"live before depth view");gpuCheck(device->CreateShaderResourceView(afterDepth.Get(),&srv,afterView.GetAddressOf()),"live after depth view");
}
void LiveWorldBlend::captureBefore(ID3D11Texture2D* depth) {
    if(before) throw std::runtime_error("Duplicate live before-depth");
    depthSize(depth);context->CopyResource(beforeDepth.Get(),depth);before=true;
}
void LiveWorldBlend::captureAfter(ID3D11Texture2D* depth) {
    assertOwner();D3D11_TEXTURE2D_DESC d{};depth->GetDesc(&d);
    if(!before||after||d.Width!=width||d.Height!=height||d.Format!=DXGI_FORMAT_R24G8_TYPELESS||d.SampleDesc.Count!=1) throw std::runtime_error("Unpaired live after-depth");
    context->CopyResource(afterDepth.Get(),depth);after=true;
}
void LiveWorldBlend::captureSelection(ID3D11Texture2D* depth) {
    depthSize(depth);context->CopyResource(afterDepth.Get(),depth);before=true;after=true;
}
void LiveWorldBlend::draw(ID3D11Texture2D* target,const WorldFrame& f,const Matrix& warp,bool preserveHand,float handExposure,float selectionDepthCutoff,bool neutralMetal) {
    assertOwner();D3D11_TEXTURE2D_DESC td{};target->GetDesc(&td);
    if(!preserveHand&&(width!=td.Width||height!=td.Height)) {
        beforeView.Reset();afterView.Reset();beforeDepth.Reset();afterDepth.Reset();nativeColor.Reset();nativeView.Reset();colorFormat=DXGI_FORMAT_UNKNOWN;
        width=td.Width;height=td.Height;before=false;after=false;
    }
    if((preserveHand&&!ready())||!td.Width||!td.Height||td.Width>4096||td.Height>2160||td.Width!=width||td.Height!=height||td.MipLevels!=1||td.ArraySize!=1||td.SampleDesc.Count!=1||
       (td.Format!=DXGI_FORMAT_R8G8B8A8_UNORM&&td.Format!=DXGI_FORMAT_B8G8R8A8_UNORM)||!f.width||!f.height||f.width>2560||f.height>1440||f.rgba.size()!=size_t(f.width)*f.height*4) throw std::runtime_error("Live blend bounds/pair");
    for(float v:warp.m) if(!std::isfinite(v)) throw std::runtime_error("Nonfinite live warp");
    if(!std::isfinite(handExposure)||handExposure<1||handExposure>2) throw std::runtime_error("Hand exposure bounds");
    if(!std::isfinite(selectionDepthCutoff)||(selectionDepthCutoff!=0&&selectionDepthCutoff!=.98f))throw std::runtime_error("Uncalibrated selection depth cutoff");
    if(!nativeColor||colorFormat!=td.Format) {
        nativeView.Reset();nativeColor.Reset();auto d=td;d.Usage=D3D11_USAGE_DEFAULT;d.BindFlags=D3D11_BIND_SHADER_RESOURCE;d.CPUAccessFlags=0;d.MiscFlags=0;
        gpuCheck(device->CreateTexture2D(&d,nullptr,nativeColor.GetAddressOf()),"live native copy");gpuCheck(device->CreateShaderResourceView(nativeColor.Get(),nullptr,nativeView.GetAddressOf()),"live native view");colorFormat=td.Format;allocations++;
    }
    if(guestWidth!=f.width||guestHeight!=f.height) {
        guestView.Reset();guestColor.Reset();D3D11_TEXTURE2D_DESC d{};d.Width=f.width;d.Height=f.height;d.MipLevels=1;d.ArraySize=1;d.SampleDesc.Count=1;d.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.BindFlags=D3D11_BIND_SHADER_RESOURCE;
        gpuCheck(device->CreateTexture2D(&d,nullptr,guestColor.GetAddressOf()),"live guest texture");gpuCheck(device->CreateShaderResourceView(guestColor.Get(),nullptr,guestView.GetAddressOf()),"live guest view");guestWidth=f.width;guestHeight=f.height;sourceGeneration=0;sourceFrame=0;allocations++;
    }
    if(!sourceGeneration||sourceGeneration!=f.generation||sourceFrame!=f.mcFrame) {context->UpdateSubresource(guestColor.Get(),0,nullptr,f.rgba.data(),f.width*4,0);sourceGeneration=f.generation;sourceFrame=f.mcFrame;uploads++;}
    struct Constants {std::array<float,16> matrix;uint32_t mask;float exposure;float cutoff;uint32_t padding;};
    Constants parameters{warp.m,preserveHand?1u:0u,handExposure,selectionDepthCutoff,neutralMetal?1u:0u};
    context->CopyResource(nativeColor.Get(),target);context->UpdateSubresource(constants.Get(),0,nullptr,&parameters,0,0);
    ComPtr<ID3D11RenderTargetView> output;gpuCheck(device->CreateRenderTargetView(target,nullptr,output.GetAddressOf()),"live output view");
    commands->ClearState();auto* rtv=output.Get();commands->OMSetRenderTargets(1,&rtv,nullptr);D3D11_VIEWPORT vp{0,0,float(width),float(height),0,1};commands->RSSetViewports(1,&vp);commands->RSSetState(raster.Get());
    commands->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);commands->VSSetShader(vs.Get(),nullptr,0);commands->PSSetShader(ps.Get(),nullptr,0);
    ID3D11ShaderResourceView* views[]={nativeView.Get(),guestView.Get(),beforeView.Get(),afterView.Get()};commands->PSSetShaderResources(0,4,views);auto* cb=constants.Get();commands->PSSetConstantBuffers(0,1,&cb);commands->Draw(3,0);
    ComPtr<ID3D11CommandList> list;gpuCheck(commands->FinishCommandList(FALSE,list.GetAddressOf()),"live command list");context->ExecuteCommandList(list.Get(),TRUE);gpuCheck(device->GetDeviceRemovedReason(),"live device health");
    // FALSE resets the deferred state; list/output die here, retaining no target.
}
}
