#include "frame_compositor.hpp"
#include <algorithm>

namespace passthrough {
Matrix Matrix::identity() {Matrix a;for(int i=0;i<4;i++) a.m[i*4+i]=1;return a;}
Matrix Matrix::fromColumnMajor(const std::array<float,16>& source) {Matrix a;for(int r=0;r<4;r++) for(int c=0;c<4;c++) a.m[r*4+c]=source[c*4+r];return a;}
Matrix Matrix::operator*(const Matrix& b) const {Matrix a;for(int r=0;r<4;r++) for(int c=0;c<4;c++) for(int k=0;k<4;k++) a.m[r*4+c]+=m[r*4+k]*b.m[k*4+c];return a;}
std::array<float,4> Matrix::apply(std::array<float,4> v) const {std::array<float,4> result{};for(int r=0;r<4;r++) for(int c=0;c<4;c++) result[r]+=m[r*4+c]*v[c];return result;}
Matrix Matrix::inverse() const {
    double a[4][8]{};for(int r=0;r<4;r++) for(int c=0;c<4;c++) {if(!std::isfinite(m[r*4+c])) throw std::runtime_error("Nonfinite warp matrix");a[r][c]=m[r*4+c];a[r][c+4]=(r==c);}
    for(int c=0;c<4;c++) {int pivot=c;for(int r=c+1;r<4;r++) if(std::abs(a[r][c])>std::abs(a[pivot][c])) pivot=r;
        if(std::abs(a[pivot][c])<1e-12) throw std::runtime_error("Singular warp matrix");
        for(int k=0;k<8;k++) std::swap(a[c][k],a[pivot][k]);
        double divisor=a[c][c];for(double& v:a[c]) v/=divisor;
        for(int r=0;r<4;r++) if(r!=c) {double factor=a[r][c];for(int k=0;k<8;k++) a[r][k]-=factor*a[c][k];}}
    Matrix result;for(int r=0;r<4;r++) for(int c=0;c<4;c++) result.m[r*4+c]=float(a[r][c+4]);return result;
}
Matrix cameraYaw(float angle) {Matrix r=Matrix::identity();r.m[0]=r.m[10]=std::cos(angle);r.m[2]=std::sin(angle);r.m[8]=-std::sin(angle);return r;}
static const char* shader=R"(
Texture2D<float4> colorImage : register(t0);
Texture2D<float> depthImage : register(t1);
cbuffer Transform : register(b0) {row_major float4x4 targetToSource;row_major float4x4 sourceToTarget;float2 imageSize;float2 padding;};
struct Varying {float4 pos:SV_Position;float2 uv:TEXCOORD;};
Varying VS(uint id:SV_VertexID) {Varying o;o.uv=float2((id<<1)&2,id&2);o.pos=float4(o.uv.x*2-1,1-o.uv.y*2,0,1);return o;}
struct Pixel {float4 color:SV_Target0;float depth:SV_Target1;};
Pixel PS(Varying i) {
    Pixel o;o.color=float4(0,0,0,0);o.depth=1;
    float4 ray=mul(targetToSource,float4(i.uv.x*2-1,1-i.uv.y*2,-1,1));
    if(ray.w<=0) return o;
    float2 uv=float2(ray.x/ray.w*.5+.5,.5-ray.y/ray.w*.5);
    if(any(uv<0)||any(uv>=1)) return o;
    int2 xy=min(int2(uv*imageSize),int2(imageSize)-1);
    float z=depthImage.Load(int3(xy,0));
    // The untouched far-depth background is a direction, not a finite far-plane
    // surface. Reproject its color without clipping sky to the rotated far plane.
    if(z>=1) {o.color=colorImage.Load(int3(xy,0));return o;}
    // GL window depth -> GL clip z, reproject, then D3D [0,1] window depth.
    float4 target=mul(sourceToTarget,float4(uv.x*2-1,1-uv.y*2,z*2-1,1));
    float depth=target.z/target.w*.5+.5;
    if(target.w<=0||depth<0||depth>1.000001) return o;
    o.color=colorImage.Load(int3(xy,0));o.depth=saturate(depth);return o;
})";
void FrameCompositor::assertOwner() const {if(std::this_thread::get_id()!=owner) throw std::runtime_error("D3D context called from non-owner thread");}
FrameCompositor::FrameCompositor(bool warp) {
    gpuCheck(D3D11CreateDevice(nullptr,warp?D3D_DRIVER_TYPE_WARP:D3D_DRIVER_TYPE_HARDWARE,nullptr,0,nullptr,0,D3D11_SDK_VERSION,device.GetAddressOf(),nullptr,context.GetAddressOf()),"D3D11 lab device");
    auto compile=[&](const char* entry,const char* profile) {ComPtr<ID3DBlob> blob,errors;HRESULT hr=D3DCompile(shader,std::strlen(shader),nullptr,nullptr,nullptr,entry,profile,D3DCOMPILE_ENABLE_STRICTNESS,0,blob.GetAddressOf(),errors.GetAddressOf());
        if(FAILED(hr)&&errors) throw std::runtime_error(std::string(static_cast<char*>(errors->GetBufferPointer()),errors->GetBufferSize()));
        gpuCheck(hr,"compile compositor");return blob;};
    auto v=compile("VS","vs_5_0"),p=compile("PS","ps_5_0");
    gpuCheck(device->CreateVertexShader(v->GetBufferPointer(),v->GetBufferSize(),nullptr,vs.GetAddressOf()),"vertex shader");
    gpuCheck(device->CreatePixelShader(p->GetBufferPointer(),p->GetBufferSize(),nullptr,ps.GetAddressOf()),"pixel shader");
    D3D11_BUFFER_DESC cb{};cb.ByteWidth=144;cb.Usage=D3D11_USAGE_DEFAULT;cb.BindFlags=D3D11_BIND_CONSTANT_BUFFER;gpuCheck(device->CreateBuffer(&cb,nullptr,constants.GetAddressOf()),"warp constants");
    D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;gpuCheck(device->CreateRasterizerState(&rd,raster.GetAddressOf()),"compositor rasterizer");
}
void FrameCompositor::resize(uint32_t w,uint32_t h) {
    assertOwner();if(w==width&&h==height) return;
    context->ClearState();colorSrv.Reset();depthSrv.Reset();colorRtv.Reset();depthRtv.Reset();
    auto texture=[&](DXGI_FORMAT format,UINT bind,bool staging) {D3D11_TEXTURE2D_DESC d{};d.Width=w;d.Height=h;d.MipLevels=1;d.ArraySize=1;d.Format=format;d.SampleDesc.Count=1;d.BindFlags=bind;
        d.Usage=staging?D3D11_USAGE_STAGING:D3D11_USAGE_DEFAULT;d.CPUAccessFlags=staging?D3D11_CPU_ACCESS_READ:0;
        ComPtr<ID3D11Texture2D> t;gpuCheck(device->CreateTexture2D(&d,nullptr,t.GetAddressOf()),"frame texture");return t;};
    inputColor=texture(DXGI_FORMAT_R8G8B8A8_UNORM,D3D11_BIND_SHADER_RESOURCE,false);inputDepth=texture(DXGI_FORMAT_R32_FLOAT,D3D11_BIND_SHADER_RESOURCE,false);
    outputColor=texture(DXGI_FORMAT_R8G8B8A8_UNORM,D3D11_BIND_RENDER_TARGET,false);outputDepth=texture(DXGI_FORMAT_R32_FLOAT,D3D11_BIND_RENDER_TARGET,false);
    readColor=texture(DXGI_FORMAT_R8G8B8A8_UNORM,0,true);readDepth=texture(DXGI_FORMAT_R32_FLOAT,0,true);
    gpuCheck(device->CreateShaderResourceView(inputColor.Get(),nullptr,colorSrv.GetAddressOf()),"color input");gpuCheck(device->CreateShaderResourceView(inputDepth.Get(),nullptr,depthSrv.GetAddressOf()),"depth input");
    gpuCheck(device->CreateRenderTargetView(outputColor.Get(),nullptr,colorRtv.GetAddressOf()),"color output");gpuCheck(device->CreateRenderTargetView(outputDepth.Get(),nullptr,depthRtv.GetAddressOf()),"depth output");width=w;height=h;
}
CompositePixels FrameCompositor::render(const WorldFrame& f,const Matrix& warp) {
    assertOwner();if(!f.width||!f.height||f.width>2560||f.height>1440||f.rgba.size()!=size_t(f.width)*f.height*4||f.depth.size()!=size_t(f.width)*f.height) throw std::runtime_error("Invalid compositor input");
    Matrix reverse=warp.inverse();resize(f.width,f.height);
    context->UpdateSubresource(inputColor.Get(),0,nullptr,f.rgba.data(),width*4,0);context->UpdateSubresource(inputDepth.Get(),0,nullptr,f.depth.data(),width*4,0);
    struct Constants {Matrix warp,reverse;float width,height,pad[2];} cb{warp,reverse,float(width),float(height),{0,0}};static_assert(sizeof cb==144);
    context->UpdateSubresource(constants.Get(),0,nullptr,&cb,0,0);
    ID3D11RenderTargetView* targets[]={colorRtv.Get(),depthRtv.Get()};context->OMSetRenderTargets(2,targets,nullptr);
    D3D11_VIEWPORT vp{0,0,float(width),float(height),0,1};context->RSSetViewports(1,&vp);context->RSSetState(raster.Get());
    context->IASetInputLayout(nullptr);context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);context->VSSetShader(vs.Get(),nullptr,0);context->PSSetShader(ps.Get(),nullptr,0);
    ID3D11ShaderResourceView* inputs[]={colorSrv.Get(),depthSrv.Get()};context->PSSetShaderResources(0,2,inputs);ID3D11Buffer* buffer=constants.Get();context->PSSetConstantBuffers(0,1,&buffer);context->Draw(3,0);
    ID3D11ShaderResourceView* none[]={nullptr,nullptr};context->PSSetShaderResources(0,2,none);context->OMSetRenderTargets(0,nullptr,nullptr);
    context->CopyResource(readColor.Get(),outputColor.Get());context->CopyResource(readDepth.Get(),outputDepth.Get());
    CompositePixels result{width,height,std::vector<unsigned char>(size_t(width)*height*4),std::vector<float>(size_t(width)*height)};
    auto read=[&](ID3D11Texture2D* texture,void* dest) {D3D11_MAPPED_SUBRESOURCE map{};gpuCheck(context->Map(texture,0,D3D11_MAP_READ,0,&map),"lab readback");for(uint32_t y=0;y<height;y++) std::memcpy(static_cast<unsigned char*>(dest)+size_t(y)*width*4,static_cast<unsigned char*>(map.pData)+size_t(y)*map.RowPitch,width*4);context->Unmap(texture,0);};
    read(readColor.Get(),result.rgba.data());read(readDepth.Get(),result.depth.data());gpuCheck(device->GetDeviceRemovedReason(),"lab device health");return result;
}
}
