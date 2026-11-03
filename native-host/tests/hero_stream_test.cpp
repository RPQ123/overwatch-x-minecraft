#include "../src/hero_stream.hpp"
#include <cassert>
#include <iostream>

int main() {
    ComPtr<ID3D11Device> dev;ComPtr<ID3D11DeviceContext> ctx;check(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,dev.GetAddressOf(),nullptr,ctx.GetAddressOf()),"stream test device");
    D3D11_TEXTURE2D_DESC td{};td.Width=320;td.Height=180;td.MipLevels=1;td.ArraySize=1;td.Format=DXGI_FORMAT_R8G8B8A8_UNORM;td.SampleDesc.Count=1;td.BindFlags=D3D11_BIND_RENDER_TARGET;
    ComPtr<ID3D11Texture2D> color;ComPtr<ID3D11RenderTargetView> rtv;check(dev->CreateTexture2D(&td,nullptr,color.GetAddressOf()),"color");check(dev->CreateRenderTargetView(color.Get(),nullptr,rtv.GetAddressOf()),"rtv");
    const char shader[]=R"(float4 hand(uint id:SV_VertexID):SV_POSITION {return float4(id==1?0:-1,id==2?1:-1,0,1);}
    float4 quad(uint id:SV_VertexID):SV_POSITION {return float4(id==1?3:-1,id==2?-3:1,0,1);}
    float4 red():SV_TARGET {return float4(1,0,0,1);}float4 blue():SV_TARGET {return float4(0,0,1,.5);})";
    auto compile=[&](const char* entry,const char* profile){ComPtr<ID3DBlob> b;check(D3DCompile(shader,sizeof(shader),nullptr,nullptr,nullptr,entry,profile,0,0,b.GetAddressOf(),nullptr),"test shader");return b;};
    auto h=compile("hand","vs_5_0"),q=compile("quad","vs_5_0"),r=compile("red","ps_5_0"),b=compile("blue","ps_5_0");
    ComPtr<ID3D11VertexShader> hand,quad;ComPtr<ID3D11PixelShader> red,blue;check(dev->CreateVertexShader(h->GetBufferPointer(),h->GetBufferSize(),nullptr,hand.GetAddressOf()),"hand");check(dev->CreateVertexShader(q->GetBufferPointer(),q->GetBufferSize(),nullptr,quad.GetAddressOf()),"quad");check(dev->CreatePixelShader(r->GetBufferPointer(),r->GetBufferSize(),nullptr,red.GetAddressOf()),"red");check(dev->CreatePixelShader(b->GetBufferPointer(),b->GetBufferSize(),nullptr,blue.GetAddressOf()),"blue");
    D3D11_BLEND_DESC bd{};auto& rb=bd.RenderTarget[0];rb.BlendEnable=TRUE;rb.SrcBlend=D3D11_BLEND_SRC_ALPHA;rb.DestBlend=D3D11_BLEND_INV_SRC_ALPHA;rb.BlendOp=D3D11_BLEND_OP_ADD;rb.SrcBlendAlpha=D3D11_BLEND_ONE;rb.DestBlendAlpha=D3D11_BLEND_INV_SRC_ALPHA;rb.BlendOpAlpha=D3D11_BLEND_OP_ADD;rb.RenderTargetWriteMask=D3D11_COLOR_WRITE_ENABLE_ALL;
    ComPtr<ID3D11BlendState> blend;check(dev->CreateBlendState(&bd,blend.GetAddressOf()),"blend");
    D3D11_RASTERIZER_DESC rd{};rd.FillMode=D3D11_FILL_SOLID;rd.CullMode=D3D11_CULL_NONE;rd.DepthClipEnable=TRUE;
    ComPtr<ID3D11RasterizerState> raster;check(dev->CreateRasterizerState(&rd,raster.GetAddressOf()),"test rasterizer");ctx->RSSetState(raster.Get());
    HeroStream stream(dev.Get(),320,180,td.Format);auto* target=rtv.Get();ctx->OMSetRenderTargets(1,&target,nullptr);D3D11_VIEWPORT vp{0,0,320,180,0,1};ctx->RSSetViewports(1,&vp);ctx->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);ctx->VSSetShader(hand.Get(),nullptr,0);ctx->PSSetShader(red.Get(),nullptr,0);FLOAT green[]{0,1,0,1};ctx->ClearRenderTargetView(rtv.Get(),green);ctx->Draw(3,0);
    // A native renderer may retain PS UAVs in slots above its MRTs. Replaying
    // with eight RTV slots must not silently unbind these original resources.
    D3D11_BUFFER_DESC ub{};ub.ByteWidth=16;ub.BindFlags=D3D11_BIND_UNORDERED_ACCESS;ub.MiscFlags=D3D11_RESOURCE_MISC_BUFFER_STRUCTURED;ub.StructureByteStride=4;
    ComPtr<ID3D11Buffer> storage;check(dev->CreateBuffer(&ub,nullptr,storage.GetAddressOf()),"uav buffer");
    D3D11_UNORDERED_ACCESS_VIEW_DESC ud{};ud.ViewDimension=D3D11_UAV_DIMENSION_BUFFER;ud.Buffer.NumElements=4;
    ComPtr<ID3D11UnorderedAccessView> uav;check(dev->CreateUnorderedAccessView(storage.Get(),&ud,uav.GetAddressOf()),"uav");auto* unordered=uav.Get();ctx->OMSetRenderTargetsAndUnorderedAccessViews(1,&target,nullptr,6,1,&unordered,nullptr);
    stream.replay(true,false,[&]{ctx->Draw(3,0);});stream.boundary(color.Get());
    ComPtr<ID3D11UnorderedAccessView> retained;ctx->OMGetRenderTargetsAndUnorderedAccessViews(0,nullptr,nullptr,6,1,retained.GetAddressOf());assert(retained.Get()==uav.Get());
    vp={240,0,80,80,0,1};ctx->RSSetViewports(1,&vp);ctx->VSSetShader(quad.Get(),nullptr,0);ctx->PSSetShader(blue.Get(),nullptr,0);ctx->OMSetBlendState(blend.Get(),nullptr,0xffffffff);ctx->Draw(3,0);stream.replay(false,true,[&]{ctx->Draw(3,0);});
    ComPtr<ID3D11RenderTargetView> bound;ctx->OMGetRenderTargets(1,bound.GetAddressOf(),nullptr);assert(bound.Get()==rtv.Get());ComPtr<ID3D11PixelShader> savedPs;ctx->PSGetShader(savedPs.GetAddressOf(),nullptr,nullptr);assert(savedPs.Get()==blue.Get());
    std::optional<HeroStream::Frame> captured;
    for(int i=0;i<15&&!captured;i++) {captured=stream.present();ctx->Flush();Sleep(40);}
    assert(captured&&captured->width==960&&captured->height==540);
    auto pixel=[&](int x,int y){return captured->rgba.data()+4*(y*960+x);};
    auto handPixel=pixel(60,470);assert(handPixel[0]>250&&handPixel[1]<3&&handPixel[3]>250);
    auto worldPixel=pixel(700,470);assert(worldPixel[0]==0&&worldPixel[1]==0&&worldPixel[2]==0&&worldPixel[3]==0);
    auto hudPixel=pixel(850,70);assert(hudPixel[0]<3&&hudPixel[1]<3&&hudPixel[2]>=127&&hudPixel[2]<=129&&hudPixel[3]>=127&&hudPixel[3]<=129);
    ComPtr<ID3D11BlendState> savedBlend;FLOAT factor[4];UINT mask;ctx->OMGetBlendState(savedBlend.GetAddressOf(),factor,&mask);assert(savedBlend.Get()==blend.Get());
    ctx->PSGetShader(savedPs.ReleaseAndGetAddressOf(),nullptr,nullptr);assert(savedPs.Get()==blue.Get());
    std::cout<<"Native draw replay isolates hands and half-transparent HUD, omits world, preserves state and asynchronously reads pixels.\n";
}
