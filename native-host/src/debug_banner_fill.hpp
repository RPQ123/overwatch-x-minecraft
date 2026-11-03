#pragma once
#include "frame_compositor.hpp"

namespace passthrough {
// Remove only the calibrated DEV ENABLED line from the *finished* native HUD.
// Interpolate its immediate upper/lower rows from this same frame. In scope/F1
// those rows already contain the native vignette/panel, unlike a pre-HUD copy.
// This intentionally reconstructs a tiny strip, not the original hidden detail.
class DebugBannerFill {
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> commands;
    ComPtr<ID3D11Texture2D> input;
    ComPtr<ID3D11ShaderResourceView> inputView;
    ComPtr<ID3D11VertexShader> vertex;
    ComPtr<ID3D11PixelShader> pixel;
    ComPtr<ID3D11RasterizerState> raster;
    ComPtr<ID3D11Buffer> constants;
    UINT inputWidth=0,inputHeight=0;
    DXGI_FORMAT format=DXGI_FORMAT_UNKNOWN;
    std::thread::id owner=std::this_thread::get_id();
public:
    static D3D11_BOX region(UINT width,UINT height) {
        // Actual paired pre-/post-HUD QHD evidence: glyph+outline is
        // [2361,30,2521,63). Keep only a 1..2 px margin, and anchor to the
        // right edge using height scale, avoiding horizontal stretching.
        const UINT left=UINT(std::ceil(200.0*height/1440));
        const UINT right=UINT(std::floor(38.0*height/1440));
        if(width<=left||height<72)return {};
        return {width-left,UINT(std::floor(29.0*height/1440)),0,
            width-right,UINT(std::ceil(65.0*height/1440)),1};
    }
    explicit DebugBannerFill(ID3D11Device* source):device(source) {
        gpuCheck(device->CreateDeferredContext(0,commands.GetAddressOf()),"debug fill deferred context");
        const char* shader=R"(
Texture2D<float4> scene:register(t0);
cbuffer Bounds:register(b0) {uint left;uint top;uint height;uint unused;};
float4 VS(uint i:SV_VertexID):SV_Position {
    float2 uv=float2((i<<1)&2,i&2);return float4(uv.x*2-1,1-uv.y*2,0,1);
}
float4 PS(float4 position:SV_Position):SV_Target {
    int x=int(position.x)-int(left),y=int(position.y)-int(top);
    float4 upper=scene.Load(int3(x,0,0)),lower=scene.Load(int3(x,int(height)+1,0));
    float3 rgb=lerp(upper.rgb,lower.rgb,float(y+1)/float(height+1));
    // Keep this exact native pixel's alpha for later native blending.
    return float4(rgb,scene.Load(int3(x,y+1,0)).a);
})";
        auto compile=[&](const char* entry,const char* profile) {
            ComPtr<ID3DBlob> code,error;
            HRESULT hr=D3DCompile(shader,strlen(shader),nullptr,nullptr,nullptr,entry,profile,
                D3DCOMPILE_ENABLE_STRICTNESS,0,code.GetAddressOf(),error.GetAddressOf());
            if(FAILED(hr)&&error)throw std::runtime_error(std::string(
                static_cast<char*>(error->GetBufferPointer()),error->GetBufferSize()));
            gpuCheck(hr,"debug fill shader");return code;
        };
        auto vs=compile("VS","vs_5_0"),ps=compile("PS","ps_5_0");
        gpuCheck(device->CreateVertexShader(vs->GetBufferPointer(),vs->GetBufferSize(),nullptr,vertex.GetAddressOf()),"debug fill VS");
        gpuCheck(device->CreatePixelShader(ps->GetBufferPointer(),ps->GetBufferSize(),nullptr,pixel.GetAddressOf()),"debug fill PS");
        D3D11_BUFFER_DESC cb{};cb.ByteWidth=16;cb.Usage=D3D11_USAGE_DEFAULT;cb.BindFlags=D3D11_BIND_CONSTANT_BUFFER;
        gpuCheck(device->CreateBuffer(&cb,nullptr,constants.GetAddressOf()),"debug fill constants");
        D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;
        gpuCheck(device->CreateRasterizerState(&rd,raster.GetAddressOf()),"debug fill raster");
    }
    void draw(ID3D11DeviceContext* context,ID3D11Texture2D* target) {
        if(owner!=std::this_thread::get_id())throw std::runtime_error("Debug fill outside render owner");
        D3D11_TEXTURE2D_DESC d{};target->GetDesc(&d);auto box=region(d.Width,d.Height);
        if(box.right<=box.left||box.bottom<=box.top||box.top==0||box.bottom>=d.Height)return;
        if(d.SampleDesc.Count!=1||d.MipLevels!=1||d.ArraySize!=1||
            (d.Format!=DXGI_FORMAT_R8G8B8A8_UNORM&&d.Format!=DXGI_FORMAT_B8G8R8A8_UNORM))
            throw std::runtime_error("Uncalibrated debug fill target");
        UINT w=box.right-box.left,h=box.bottom-box.top;
        if(!input||inputWidth!=w||inputHeight!=h+2||format!=d.Format) {
            inputView.Reset();input.Reset();auto copy=d;copy.Width=w;copy.Height=h+2;
            copy.BindFlags=D3D11_BIND_SHADER_RESOURCE;copy.Usage=D3D11_USAGE_DEFAULT;copy.CPUAccessFlags=0;copy.MiscFlags=0;
            gpuCheck(device->CreateTexture2D(&copy,nullptr,input.GetAddressOf()),"debug fill current scene");
            gpuCheck(device->CreateShaderResourceView(input.Get(),nullptr,inputView.GetAddressOf()),"debug fill scene view");
            inputWidth=w;inputHeight=h+2;format=d.Format;
        }
        D3D11_BOX source=box;source.top--;source.bottom++;
        context->CopySubresourceRegion(input.Get(),0,0,0,0,target,0,&source);
        const UINT bounds[]{box.left,box.top,h,0};context->UpdateSubresource(constants.Get(),0,nullptr,bounds,0,0);
        ComPtr<ID3D11RenderTargetView> output;
        gpuCheck(device->CreateRenderTargetView(target,nullptr,output.GetAddressOf()),"debug fill output");
        commands->ClearState();auto* rtv=output.Get();commands->OMSetRenderTargets(1,&rtv,nullptr);
        D3D11_VIEWPORT vp{float(box.left),float(box.top),float(w),float(h),0,1};
        commands->RSSetViewports(1,&vp);commands->RSSetState(raster.Get());
        commands->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
        commands->VSSetShader(vertex.Get(),nullptr,0);commands->PSSetShader(pixel.Get(),nullptr,0);
        auto* srv=inputView.Get();commands->PSSetShaderResources(0,1,&srv);
        auto* cb=constants.Get();commands->PSSetConstantBuffers(0,1,&cb);commands->Draw(3,0);
        ComPtr<ID3D11CommandList> list;
        gpuCheck(commands->FinishCommandList(FALSE,list.GetAddressOf()),"debug fill command list");
        context->ExecuteCommandList(list.Get(),TRUE);
        // Only the tiny private scene strip persists, never the swapchain RTV.
    }
};
}
