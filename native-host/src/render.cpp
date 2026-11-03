#include "render.hpp"

namespace {
constexpr char shaderSource[]=R"(
Texture2D image : register(t0);
SamplerState pixelSampler : register(s0);
struct Input { float4 position:POSITION; float2 uv:TEXCOORD; float3 tint:COLOR; };
struct Output { float4 position:SV_POSITION; float2 uv:TEXCOORD; float3 tint:COLOR; };
Output vs_main(Input input) {
    Output result;result.position=input.position;result.uv=input.uv;result.tint=input.tint;return result;
}
float4 ps_main(Output input):SV_TARGET {
    float4 color=image.Sample(pixelSampler,input.uv);
    clip(color.a-.1);
    return float4(color.rgb*input.tint,1);
})";
ComPtr<ID3DBlob> compileShader(const char* entry,const char* profile) {
    ComPtr<ID3DBlob> code,error;
    HRESULT result=D3DCompile(shaderSource,sizeof(shaderSource)-1,nullptr,nullptr,nullptr,entry,profile,
                             D3DCOMPILE_OPTIMIZATION_LEVEL3,0,code.GetAddressOf(),error.GetAddressOf());
    if(FAILED(result)) throw std::runtime_error(error ? static_cast<char*>(error->GetBufferPointer()) : "Shader compilation failed");
    return code;
}
struct ContextGuard {
    ID3D11DeviceContext1* context;
    ComPtr<ID3DDeviceContextState> previous;
    ContextGuard(ID3D11DeviceContext1* context,ID3DDeviceContextState* state):context(context) {
        context->SwapDeviceContextState(state,previous.GetAddressOf());
    }
    ~ContextGuard() {
        // Don't retain the host backbuffer in the probe state across ResizeBuffers.
        context->OMSetRenderTargets(0,nullptr,nullptr);
        context->SwapDeviceContextState(previous.Get(),nullptr);
    }
};
struct ScreenVertex { Vec4 clip;float u,v,r,g,b; };
static_assert(sizeof(ScreenVertex)==36);
}

Renderer::Renderer(ID3D11Device* input,Mesh data):device(input) {
    device->GetImmediateContext(context.GetAddressOf());
    ComPtr<ID3D11Device1> device1;
    check(device.As(&device1),"D3D11.1 device");
    check(context.As(&context1),"D3D11.1 context");
    D3D_FEATURE_LEVEL level=device->GetFeatureLevel();
    UINT flags=(device->GetCreationFlags()&D3D11_CREATE_DEVICE_SINGLETHREADED)
        ? D3D11_1_CREATE_DEVICE_CONTEXT_STATE_SINGLETHREADED:0;
    check(device1->CreateDeviceContextState(flags,&level,1,D3D11_SDK_VERSION,__uuidof(ID3D11Device),
                                          nullptr,privateState.GetAddressOf()),"isolated context state");
    auto vs=compileShader("vs_main","vs_5_0"),ps=compileShader("ps_main","ps_5_0");
    check(device->CreateVertexShader(vs->GetBufferPointer(),vs->GetBufferSize(),nullptr,vertexShader.GetAddressOf()),"vertex shader");
    check(device->CreatePixelShader(ps->GetBufferPointer(),ps->GetBufferSize(),nullptr,pixelShader.GetAddressOf()),"pixel shader");
    D3D11_INPUT_ELEMENT_DESC elements[]={
        {"POSITION",0,DXGI_FORMAT_R32G32B32A32_FLOAT,0,0,D3D11_INPUT_PER_VERTEX_DATA,0},
        {"TEXCOORD",0,DXGI_FORMAT_R32G32_FLOAT,0,16,D3D11_INPUT_PER_VERTEX_DATA,0},
        {"COLOR",0,DXGI_FORMAT_R32G32B32_FLOAT,0,24,D3D11_INPUT_PER_VERTEX_DATA,0}};
    check(device->CreateInputLayout(elements,3,vs->GetBufferPointer(),vs->GetBufferSize(),layout.GetAddressOf()),"input layout");
    D3D11_SAMPLER_DESC sampling{};sampling.Filter=D3D11_FILTER_MIN_MAG_MIP_POINT;
    sampling.AddressU=sampling.AddressV=sampling.AddressW=D3D11_TEXTURE_ADDRESS_CLAMP;sampling.MaxLOD=D3D11_FLOAT32_MAX;
    check(device->CreateSamplerState(&sampling,sampler.GetAddressOf()),"sampler");
    D3D11_RASTERIZER_DESC raster{};raster.FillMode=D3D11_FILL_SOLID;raster.CullMode=D3D11_CULL_NONE;raster.DepthClipEnable=TRUE;
    check(device->CreateRasterizerState(&raster,rasterizer.GetAddressOf()),"rasterizer");
    D3D11_DEPTH_STENCIL_DESC depth{};depth.DepthEnable=TRUE;depth.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL;depth.DepthFunc=D3D11_COMPARISON_LESS_EQUAL;
    check(device->CreateDepthStencilState(&depth,depthState.GetAddressOf()),"probe depth state");
    update(std::move(data));
}

void Renderer::update(Mesh data) {
    if(data.vertices.size()>(data.creative?65536u:16384u)||data.rgba.size()!=data.width*data.height*4u) throw std::runtime_error("Invalid GPU mesh budget");
    ComPtr<ID3D11Buffer> nextBuffer=vertexBuffer;ComPtr<ID3D11ShaderResourceView> nextTexture=texture;
    UINT required=static_cast<UINT>(std::max<size_t>(1,data.vertices.size())*sizeof(ScreenVertex));
    if(required>vertexCapacity) {
        D3D11_BUFFER_DESC desc{};desc.ByteWidth=required;desc.Usage=D3D11_USAGE_DYNAMIC;desc.BindFlags=D3D11_BIND_VERTEX_BUFFER;desc.CPUAccessFlags=D3D11_CPU_ACCESS_WRITE;
        nextBuffer.Reset();check(device->CreateBuffer(&desc,nullptr,nextBuffer.GetAddressOf()),"updated vertex buffer");
    }
    if(data.width!=mesh.width||data.height!=mesh.height||data.rgba!=mesh.rgba) {
        D3D11_TEXTURE2D_DESC desc{};desc.Width=data.width;desc.Height=data.height;desc.MipLevels=1;desc.ArraySize=1;
        desc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;desc.SampleDesc.Count=1;desc.Usage=D3D11_USAGE_IMMUTABLE;desc.BindFlags=D3D11_BIND_SHADER_RESOURCE;
        D3D11_SUBRESOURCE_DATA pixels{data.rgba.data(),data.width*4,0};ComPtr<ID3D11Texture2D> image;
        check(device->CreateTexture2D(&desc,&pixels,image.GetAddressOf()),"updated MC atlas");nextTexture.Reset();
        check(device->CreateShaderResourceView(image.Get(),nullptr,nextTexture.GetAddressOf()),"updated atlas view");
    }
    mesh=std::move(data);vertexBuffer=nextBuffer;texture=nextTexture;vertexCapacity=std::max(vertexCapacity,required);
}

void Renderer::draw(ID3D11Texture2D* target,const Camera& camera,Vec3 anchor,const NativeProjection* projection) {
    D3D11_TEXTURE2D_DESC targetDesc{};target->GetDesc(&targetDesc);
    if(!targetDesc.Width || !targetDesc.Height || targetDesc.Width>16384 || targetDesc.Height>16384)
        throw std::runtime_error("Unsupported target size");
    ComPtr<ID3D11RenderTargetView> renderTarget;
    check(device->CreateRenderTargetView(target,nullptr,renderTarget.GetAddressOf()),"host backbuffer view");
    if(depthWidth!=targetDesc.Width || depthHeight!=targetDesc.Height || depthSamples!=targetDesc.SampleDesc.Count) {
        depthView.Reset();depthTexture.Reset();
        D3D11_TEXTURE2D_DESC depth{};depth.Width=targetDesc.Width;depth.Height=targetDesc.Height;depth.MipLevels=1;depth.ArraySize=1;
        depth.Format=DXGI_FORMAT_D32_FLOAT;depth.SampleDesc=targetDesc.SampleDesc;depth.BindFlags=D3D11_BIND_DEPTH_STENCIL;
        check(device->CreateTexture2D(&depth,nullptr,depthTexture.GetAddressOf()),"private cube depth");
        check(device->CreateDepthStencilView(depthTexture.Get(),nullptr,depthView.GetAddressOf()),"private depth view");
        depthWidth=targetDesc.Width;depthHeight=targetDesc.Height;depthSamples=targetDesc.SampleDesc.Count;
    }
    context->ClearDepthStencilView(depthView.Get(),D3D11_CLEAR_DEPTH,1,0);
    drawBound(renderTarget.Get(),depthView.Get(),targetDesc,camera,anchor,projection);
}

void Renderer::drawScene(ID3D11RenderTargetView* color,ID3D11DepthStencilView* depth,
                         const Camera& camera,Vec3 anchor,const NativeProjection& projection) {
    if(!color||!depth) throw std::runtime_error("Missing native scene views");
    ComPtr<ID3D11Resource> colorResource,depthResource;color->GetResource(colorResource.GetAddressOf());depth->GetResource(depthResource.GetAddressOf());
    ComPtr<ID3D11Texture2D> colorTexture,depthTexture;
    check(colorResource.As(&colorTexture),"scene color texture");check(depthResource.As(&depthTexture),"scene depth texture");
    D3D11_TEXTURE2D_DESC colorDesc{},depthDesc{};colorTexture->GetDesc(&colorDesc);depthTexture->GetDesc(&depthDesc);
    if(!colorDesc.Width||!colorDesc.Height||colorDesc.Width>16384||colorDesc.Height>16384
       ||colorDesc.Width!=depthDesc.Width||colorDesc.Height!=depthDesc.Height||colorDesc.SampleDesc.Count!=depthDesc.SampleDesc.Count)
        throw std::runtime_error("Mismatched scene color/depth");
    // Existing host depth is neither cleared nor replaced. The new block writes
    // its depth so subsequent host objects can also occlude against it.
    drawBound(color,depth,colorDesc,camera,anchor,&projection);
}
void Renderer::drawOverlay(ID3D11Texture2D* target) {
    // Owned creative status panel only. It never covers the host world or replaces native HUD.
    if(mesh.vertices.size()!=6||mesh.width!=256||mesh.height!=64) throw std::runtime_error("HUD format");
    D3D11_TEXTURE2D_DESC desc{};target->GetDesc(&desc);
    std::array<ScreenVertex,6> vertices{};
    for(unsigned i=0;i<6;i++) {
        const auto& v=mesh.vertices[i];
        vertices[i]={{2*(24+v.x*512)/desc.Width-1,1-2*(50+v.y*128)/desc.Height,0,1},v.u,v.v,1,1,1};
    }
    ComPtr<ID3D11RenderTargetView> color;check(device->CreateRenderTargetView(target,nullptr,color.GetAddressOf()),"creative panel target");
    ContextGuard guard(context1.Get(),privateState.Get());
    D3D11_MAPPED_SUBRESOURCE mapped{};check(context->Map(vertexBuffer.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"creative panel vertices");
    std::memcpy(mapped.pData,vertices.data(),sizeof(vertices));context->Unmap(vertexBuffer.Get(),0);
    auto* rtv=color.Get();context->OMSetRenderTargets(1,&rtv,nullptr);context->OMSetDepthStencilState(nullptr,0);context->OMSetBlendState(nullptr,nullptr,0xffffffff);
    D3D11_VIEWPORT vp{0,0,float(desc.Width),float(desc.Height),0,1};context->RSSetViewports(1,&vp);context->RSSetState(rasterizer.Get());
    auto* buffer=vertexBuffer.Get();UINT stride=sizeof(ScreenVertex),offset=0;context->IASetVertexBuffers(0,1,&buffer,&stride,&offset);
    context->IASetInputLayout(layout.Get());context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    context->VSSetShader(vertexShader.Get(),nullptr,0);context->PSSetShader(pixelShader.Get(),nullptr,0);context->GSSetShader(nullptr,nullptr,0);context->HSSetShader(nullptr,nullptr,0);context->DSSetShader(nullptr,nullptr,0);
    auto* image=texture.Get();auto* pixelSampler=sampler.Get();context->PSSetShaderResources(0,1,&image);context->PSSetSamplers(0,1,&pixelSampler);
    context->SetPredication(nullptr,FALSE);context->Draw(6,0);
}

void Renderer::drawBound(ID3D11RenderTargetView* color,ID3D11DepthStencilView* depth,
                         const D3D11_TEXTURE2D_DESC& targetDesc,const Camera& camera,Vec3 anchor,const NativeProjection* projection) {
    if(mesh.vertices.empty()) return;
    if(projection&&(!validProjection(*projection)||projection->right>targetDesc.Width||projection->bottom>targetDesc.Height)) throw std::runtime_error("Invalid scene projection");
    std::vector<ScreenVertex> vertices;vertices.reserve(mesh.vertices.size());
    for(const auto& vertex:mesh.vertices) {
        Vec3 point=anchor+Vec3{vertex.x,vertex.y,vertex.z};
        Vec4 clip=projection?projectNativeValidated(point,*projection,targetDesc.Width,targetDesc.Height)
            :project(point,camera,static_cast<float>(targetDesc.Width)/targetDesc.Height);
        vertices.push_back({clip,vertex.u,vertex.v,vertex.shade*((vertex.tint>>16)&255)/255.f,
                            vertex.shade*((vertex.tint>>8)&255)/255.f,vertex.shade*(vertex.tint&255)/255.f});
    }
    ContextGuard guard(context1.Get(),privateState.Get());
    D3D11_MAPPED_SUBRESOURCE mapped{};
    check(context->Map(vertexBuffer.Get(),0,D3D11_MAP_WRITE_DISCARD,0,&mapped),"write pose-coherent vertices");
    std::memcpy(mapped.pData,vertices.data(),vertices.size()*sizeof(ScreenVertex));context->Unmap(vertexBuffer.Get(),0);
    context->OMSetRenderTargets(1,&color,depth);
    context->OMSetDepthStencilState(depthState.Get(),0);
    context->OMSetBlendState(nullptr,nullptr,0xffffffff);
    D3D11_VIEWPORT viewport{0,0,static_cast<float>(targetDesc.Width),static_cast<float>(targetDesc.Height),0,1};
    context->RSSetViewports(1,&viewport);context->RSSetState(rasterizer.Get());
    ID3D11Buffer* buffer=vertexBuffer.Get();UINT stride=sizeof(ScreenVertex),offset=0;
    context->IASetVertexBuffers(0,1,&buffer,&stride,&offset);context->IASetInputLayout(layout.Get());
    context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);
    context->VSSetShader(vertexShader.Get(),nullptr,0);context->PSSetShader(pixelShader.Get(),nullptr,0);
    context->GSSetShader(nullptr,nullptr,0);context->HSSetShader(nullptr,nullptr,0);context->DSSetShader(nullptr,nullptr,0);
    ID3D11ShaderResourceView* view=texture.Get();ID3D11SamplerState* sampling=sampler.Get();
    context->PSSetShaderResources(0,1,&view);context->PSSetSamplers(0,1,&sampling);
    context->SetPredication(nullptr,FALSE);
    context->Draw(static_cast<UINT>(vertices.size()),0);
}
