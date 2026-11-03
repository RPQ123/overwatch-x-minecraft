#pragma once
#include "frame_compositor.hpp"
#include <cwchar>
#include <algorithm>

namespace passthrough {
// Actual vanilla BossBarHud pixels. No generated label or bar. No world-camera
// warp is applied to UI, and deferred execution preserves the native context.
class BossHealthOverlay {
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context,commands;
    ComPtr<ID3D11VertexShader> vs;
    ComPtr<ID3D11PixelShader> ps;
    ComPtr<ID3D11RasterizerState> raster;
    ComPtr<ID3D11BlendState> blend;
    ComPtr<ID3D11Texture2D> image;
    ComPtr<ID3D11ShaderResourceView> view;
    ComPtr<ID3D11SamplerState> sampler;
    UINT width=0,height=0;uint64_t generation=0,frame=0;
    ComPtr<ID3D11Buffer> constants;
public:
    explicit BossHealthOverlay(ID3D11Device* input):device(input){
        device->GetImmediateContext(context.GetAddressOf());gpuCheck(device->CreateDeferredContext(0,commands.GetAddressOf()),"boss context");
        const char* shader=R"(
            Texture2D image:register(t0);SamplerState sampleImage:register(s0);
            cbuffer Bounds:register(b0){float2 size;float2 pad;};
            struct V{float4 pos:SV_Position;float2 uv:TEXCOORD;};
            V VS(uint id:SV_VertexID){V v;v.uv=float2((id<<1)&2,id&2);v.pos=float4(v.uv.x*2-1,1-v.uv.y*2,0,1);return v;}
            float4 PS(V v):SV_Target{float2 uv=(v.uv-float2((1-size.x)*.5,0))/size;clip(uv);clip(1-uv);return image.Sample(sampleImage,uv);}
        )";
        auto compile=[&](const char* entry,const char* profile){ComPtr<ID3DBlob> code,error;gpuCheck(D3DCompile(shader,strlen(shader),nullptr,nullptr,nullptr,entry,profile,0,0,code.GetAddressOf(),error.GetAddressOf()),"boss shader");return code;};
        auto vertex=compile("VS","vs_5_0"),pixel=compile("PS","ps_5_0");
        gpuCheck(device->CreateVertexShader(vertex->GetBufferPointer(),vertex->GetBufferSize(),nullptr,vs.GetAddressOf()),"boss vertex shader");
        gpuCheck(device->CreatePixelShader(pixel->GetBufferPointer(),pixel->GetBufferSize(),nullptr,ps.GetAddressOf()),"boss pixel shader");
        D3D11_BUFFER_DESC cb{};cb.ByteWidth=16;cb.Usage=D3D11_USAGE_DEFAULT;cb.BindFlags=D3D11_BIND_CONSTANT_BUFFER;gpuCheck(device->CreateBuffer(&cb,nullptr,constants.GetAddressOf()),"HUD bounds");
        D3D11_SAMPLER_DESC sd{};sd.Filter=D3D11_FILTER_MIN_MAG_MIP_POINT;sd.AddressU=sd.AddressV=sd.AddressW=D3D11_TEXTURE_ADDRESS_CLAMP;sd.MaxLOD=D3D11_FLOAT32_MAX;
        gpuCheck(device->CreateSamplerState(&sd,sampler.GetAddressOf()),"boss sampler");
        D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;gpuCheck(device->CreateRasterizerState(&rd,raster.GetAddressOf()),"boss rasterizer");
        D3D11_BLEND_DESC bd{};auto& b=bd.RenderTarget[0];b.BlendEnable=TRUE;b.SrcBlend=D3D11_BLEND_ONE;b.DestBlend=D3D11_BLEND_INV_SRC_ALPHA;b.BlendOp=D3D11_BLEND_OP_ADD;b.SrcBlendAlpha=D3D11_BLEND_ONE;b.DestBlendAlpha=D3D11_BLEND_INV_SRC_ALPHA;b.BlendOpAlpha=D3D11_BLEND_OP_ADD;b.RenderTargetWriteMask=D3D11_COLOR_WRITE_ENABLE_ALL;
        gpuCheck(device->CreateBlendState(&bd,blend.GetAddressOf()),"boss blend");
    }
    void draw(ID3D11Texture2D* target,const WorldFrame& f){
        if(!f.hudWidth||!f.hudHeight||f.hudRgba.size()!=size_t(f.hudWidth)*f.hudHeight*4)return;
        if(width!=f.hudWidth||height!=f.hudHeight){
            image.Reset();view.Reset();width=f.hudWidth;height=f.hudHeight;frame=0;
            D3D11_TEXTURE2D_DESC td{};td.Width=width;td.Height=height;td.MipLevels=1;td.ArraySize=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.SampleDesc.Count=1;td.BindFlags=D3D11_BIND_SHADER_RESOURCE;
            gpuCheck(device->CreateTexture2D(&td,nullptr,image.GetAddressOf()),"vanilla HUD texture");gpuCheck(device->CreateShaderResourceView(image.Get(),nullptr,view.GetAddressOf()),"HUD view");
        }
        if(frame!=f.mcFrame||generation!=f.generation){context->UpdateSubresource(image.Get(),0,nullptr,f.hudRgba.data(),width*4,0);frame=f.mcFrame;generation=f.generation;}
        float bounds[]{float(width)/f.width,float(height)/f.height,0,0};context->UpdateSubresource(constants.Get(),0,nullptr,bounds,0,0);
        D3D11_TEXTURE2D_DESC td{};target->GetDesc(&td);ComPtr<ID3D11RenderTargetView> output;gpuCheck(device->CreateRenderTargetView(target,nullptr,output.GetAddressOf()),"boss target");
        commands->ClearState();auto* rtv=output.Get();commands->OMSetRenderTargets(1,&rtv,nullptr);commands->OMSetBlendState(blend.Get(),nullptr,0xffffffff);
        D3D11_VIEWPORT vp{0,0,float(td.Width),float(td.Height),0,1};commands->RSSetViewports(1,&vp);commands->RSSetState(raster.Get());
        commands->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);commands->VSSetShader(vs.Get(),nullptr,0);commands->PSSetShader(ps.Get(),nullptr,0);
        auto* texture=view.Get();auto* filter=sampler.Get();auto* cb=constants.Get();commands->PSSetConstantBuffers(0,1,&cb);commands->PSSetShaderResources(0,1,&texture);commands->PSSetSamplers(0,1,&filter);commands->Draw(3,0);
        ComPtr<ID3D11CommandList> list;gpuCheck(commands->FinishCommandList(FALSE,list.GetAddressOf()),"boss commands");context->ExecuteCommandList(list.Get(),TRUE);
    }
};
}
