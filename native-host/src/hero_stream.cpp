#include "hero_stream.hpp"
#include <algorithm>

void HeroStream::texture(DXGI_FORMAT format,ComPtr<ID3D11Texture2D>& t,ComPtr<ID3D11RenderTargetView>& r,ComPtr<ID3D11ShaderResourceView>* v,UINT w,UINT h) {
    D3D11_TEXTURE2D_DESC desc{};desc.Width=w;desc.Height=h;desc.MipLevels=1;desc.ArraySize=1;desc.Format=format;desc.SampleDesc.Count=1;
    desc.BindFlags=D3D11_BIND_RENDER_TARGET|(v?D3D11_BIND_SHADER_RESOURCE:0);
    check(device->CreateTexture2D(&desc,nullptr,t.GetAddressOf()),"hero texture");check(device->CreateRenderTargetView(t.Get(),nullptr,r.GetAddressOf()),"hero rtv");
    if(v) check(device->CreateShaderResourceView(t.Get(),nullptr,v->GetAddressOf()),"hero srv");
}
HeroStream::HeroStream(ID3D11Device* d,UINT w,UINT h,DXGI_FORMAT format):device(d),width(w),height(h) {
    if(w>4096||h>2160||w<320||h<180||(format!=DXGI_FORMAT_R8G8B8A8_UNORM&&format!=DXGI_FORMAT_B8G8R8A8_UNORM)) throw std::runtime_error("unsupported native hero surface");
    d->GetImmediateContext(context.GetAddressOf());check(context.As(&context1),"hero context1");
    D3D_FEATURE_LEVEL level;D3D_FEATURE_LEVEL levels[]{D3D_FEATURE_LEVEL_11_0};
    ComPtr<ID3D11Device1> dev1;check(device.As(&dev1),"hero device1");
    check(dev1->CreateDeviceContextState(0,levels,1,D3D11_SDK_VERSION,__uuidof(ID3D11Device),&level,privateState.GetAddressOf()),"hero private state");
    texture(DXGI_FORMAT_R8_UNORM,handMask,maskTarget,&maskView,w,h);texture(format,hud,hudTarget,&hudView,w,h);
    ComPtr<ID3D11RenderTargetView> unused;texture(format,scene,unused,&sceneView,w,h);
    UINT outWidth=960,outHeight=UINT(std::lround(960.0*h/w));
    texture(DXGI_FORMAT_R8G8B8A8_UNORM,output,outputTarget,nullptr,outWidth,outHeight);
    D3D11_TEXTURE2D_DESC sd{};output->GetDesc(&sd);sd.Usage=D3D11_USAGE_STAGING;sd.BindFlags=0;sd.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
    for(auto& s:slots) check(device->CreateTexture2D(&sd,nullptr,s.staging.GetAddressOf()),"hero staging");
    const char shader[]=R"(
        Texture2D<float4> sceneTex:register(t0);Texture2D<float> maskTex:register(t1);Texture2D<float4> hudTex:register(t2);SamplerState samp:register(s0);
        struct V {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;};
        V vs(uint id:SV_VertexID) {V v;v.uv=float2((id<<1)&2,id&2);v.pos=float4(v.uv*float2(2,-2)+float2(-1,1),0,1);return v;}
        float4 mask():SV_TARGET {return float4(1,1,1,1);}
        float4 compose(V v):SV_TARGET {float a=maskTex.Sample(samp,v.uv);float3 hand=sceneTex.Sample(samp,v.uv).rgb*a;float4 ui=hudTex.Sample(samp,v.uv);return float4(ui.rgb+hand*(1-ui.a),ui.a+a*(1-ui.a));}
    )";
    auto compile=[&](const char* entry,const char* profile){ComPtr<ID3DBlob> b;check(D3DCompile(shader,sizeof(shader),nullptr,nullptr,nullptr,entry,profile,0,0,b.GetAddressOf(),nullptr),"hero shader");return b;};
    auto v=compile("vs","vs_5_0"),p=compile("mask","ps_5_0"),c=compile("compose","ps_5_0");
    check(device->CreateVertexShader(v->GetBufferPointer(),v->GetBufferSize(),nullptr,fullscreen.GetAddressOf()),"hero vs");
    check(device->CreatePixelShader(p->GetBufferPointer(),p->GetBufferSize(),nullptr,white.GetAddressOf()),"hero mask ps");
    check(device->CreatePixelShader(c->GetBufferPointer(),c->GetBufferSize(),nullptr,composite.GetAddressOf()),"hero composite ps");
    D3D11_SAMPLER_DESC ss{};ss.Filter=D3D11_FILTER_MIN_MAG_MIP_LINEAR;ss.AddressU=ss.AddressV=ss.AddressW=D3D11_TEXTURE_ADDRESS_CLAMP;ss.MaxLOD=D3D11_FLOAT32_MAX;
    check(device->CreateSamplerState(&ss,sampler.GetAddressOf()),"hero sampler");
    D3D11_RASTERIZER_DESC rs{};rs.FillMode=D3D11_FILL_SOLID;rs.CullMode=D3D11_CULL_NONE;rs.DepthClipEnable=TRUE;check(device->CreateRasterizerState(&rs,rasterizer.GetAddressOf()),"hero rasterizer");
    D3D11_DEPTH_STENCIL_DESC ds{};check(device->CreateDepthStencilState(&ds,noDepth.GetAddressOf()),"hero no depth");
    D3D11_BLEND_DESC bs{};bs.RenderTarget[0].RenderTargetWriteMask=D3D11_COLOR_WRITE_ENABLE_ALL;check(device->CreateBlendState(&bs,noBlend.GetAddressOf()),"hero no blend");
    FLOAT clear[4]{};context->ClearRenderTargetView(maskTarget.Get(),clear);context->ClearRenderTargetView(hudTarget.Get(),clear);
}
void HeroStream::replay(bool firstPerson,bool originalBackbuffer,const std::function<void()>& draw) {
    bool ui=hudPhase&&originalBackbuffer;if(!firstPerson&&!ui) return;
    // Preserve every binding altered by replay; original draw uses the restored state.
    std::array<ID3D11RenderTargetView*,8> targets{};ComPtr<ID3D11DepthStencilView> depth;context->OMGetRenderTargets(8,targets.data(),depth.GetAddressOf());
    unsigned targetCount=0;for(unsigned i=0;i<targets.size();i++) if(targets[i]) targetCount=i+1;
    std::array<ID3D11UnorderedAccessView*,8> uavs{};context->OMGetRenderTargetsAndUnorderedAccessViews(0,nullptr,nullptr,0,uavs.size(),uavs.data());
    unsigned uavMask=0;for(unsigned i=0;i<uavs.size();i++) if(uavs[i]) uavMask|=1u<<i;observedUavMask.fetch_or(uavMask);
    std::array<ID3D11Buffer*,4> so{};context->SOGetTargets(so.size(),so.data());bool hasStreamOutput=false;for(auto* buffer:so) if(buffer) {hasStreamOutput=true;buffer->Release();}
    if(hasStreamOutput) {++skippedStreamOutput;for(auto* t:targets) if(t) t->Release();for(auto* u:uavs) if(u) u->Release();return;}
    ComPtr<ID3D11BlendState> blend;FLOAT factor[4];UINT sampleMask;context->OMGetBlendState(blend.GetAddressOf(),factor,&sampleMask);
    ComPtr<ID3D11DepthStencilState> dss;UINT stencil;context->OMGetDepthStencilState(dss.GetAddressOf(),&stencil);
    ComPtr<ID3D11PixelShader> ps;std::array<ID3D11ClassInstance*,256> classes{};UINT classCount=classes.size();context->PSGetShader(ps.GetAddressOf(),classes.data(),&classCount);
    D3D11_DEPTH_STENCIL_DESC dd{};if(dss) dss->GetDesc(&dd);else {dd.DepthEnable=TRUE;dd.DepthFunc=D3D11_COMPARISON_LESS;dd.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ALL;}
    dd.DepthWriteMask=D3D11_DEPTH_WRITE_MASK_ZERO;dd.StencilWriteMask=0;
    if(firstPerson) dd.StencilEnable=FALSE;
    auto key=std::make_pair(reinterpret_cast<uintptr_t>(dss.Get()),firstPerson);
    auto found=depthCache.find(key);if(found==depthCache.end()) {
        if(depthCache.size()>=128) throw std::runtime_error("hero depth state limit");
        DepthCache item;item.original=dss;check(device->CreateDepthStencilState(&dd,item.capture.GetAddressOf()),"hero capture depth");found=depthCache.emplace(key,std::move(item)).first;
    }
    ComPtr<ID3D11BlendState> uiBlend;
    if(!firstPerson) {
        auto blendKey=reinterpret_cast<uintptr_t>(blend.Get());auto existing=blendCache.find(blendKey);
        if(existing==blendCache.end()) {
            if(blendCache.size()>=128) throw std::runtime_error("hero blend state limit");
            D3D11_BLEND_DESC bd{};if(blend) blend->GetDesc(&bd);else bd.RenderTarget[0].RenderTargetWriteMask=D3D11_COLOR_WRITE_ENABLE_ALL;
            auto& b=bd.RenderTarget[0];if(!b.BlendEnable) {b.BlendEnable=TRUE;b.SrcBlend=D3D11_BLEND_ONE;b.DestBlend=D3D11_BLEND_ZERO;b.BlendOp=D3D11_BLEND_OP_ADD;}
            b.SrcBlendAlpha=D3D11_BLEND_ONE;b.DestBlendAlpha=D3D11_BLEND_INV_SRC_ALPHA;b.BlendOpAlpha=D3D11_BLEND_OP_ADD;b.RenderTargetWriteMask|=D3D11_COLOR_WRITE_ENABLE_ALPHA;
            BlendCache item;item.original=blend;check(device->CreateBlendState(&bd,item.capture.GetAddressOf()),"hero ui blend");existing=blendCache.emplace(blendKey,std::move(item)).first;
        }uiBlend=existing->second.capture;
    }
    context->OMSetDepthStencilState(found->second.capture.Get(),stencil);
    std::array<ID3D11UnorderedAccessView*,7> emptyUavs{};
    if(firstPerson) {
        auto* target=maskTarget.Get();context->OMSetRenderTargetsAndUnorderedAccessViews(1,&target,depth.Get(),1,7,emptyUavs.data(),nullptr);context->PSSetShader(white.Get(),nullptr,0);context->OMSetBlendState(noBlend.Get(),nullptr,0xffffffff);
        draw();++handDraws;
    } else {
        auto* target=hudTarget.Get();context->OMSetRenderTargetsAndUnorderedAccessViews(1,&target,depth.Get(),1,7,emptyUavs.data(),nullptr);context->OMSetBlendState(uiBlend.Get(),factor,sampleMask);draw();++hudDraws;
    }
    context->OMSetRenderTargetsAndUnorderedAccessViews(targetCount,targets.data(),depth.Get(),targetCount,8-targetCount,uavs.data()+targetCount,nullptr);
    context->OMSetBlendState(blend.Get(),factor,sampleMask);context->OMSetDepthStencilState(dss.Get(),stencil);context->PSSetShader(ps.Get(),classes.data(),classCount);
    for(auto* t:targets) if(t) t->Release();for(auto* u:uavs) if(u) u->Release();for(UINT i=0;i<classCount;i++) if(classes[i]) classes[i]->Release();
}
void HeroStream::boundary(ID3D11Texture2D* color) {
    if(!sceneCopied) {context->CopyResource(scene.Get(),color);sceneCopied=true;hudPhase=true;}
}
std::optional<HeroStream::Frame> HeroStream::present() {
    std::optional<Frame> ready;
    // Read only a completed older slot. A busy GPU drops a transport frame.
    for(auto& s:slots) if(s.pending) {
        D3D11_MAPPED_SUBRESOURCE mapped{};HRESULT result=context->Map(s.staging.Get(),0,D3D11_MAP_READ,D3D11_MAP_FLAG_DO_NOT_WAIT,&mapped);
        if(result==DXGI_ERROR_WAS_STILL_DRAWING) continue;check(result,"hero async readback");
        D3D11_TEXTURE2D_DESC desc{};s.staging->GetDesc(&desc);Frame f{s.sequence,s.time,desc.Width,desc.Height,std::vector<unsigned char>(size_t(desc.Width)*desc.Height*4)};
        for(UINT y=0;y<desc.Height;y++) std::memcpy(f.rgba.data()+size_t(y)*desc.Width*4,static_cast<unsigned char*>(mapped.pData)+size_t(y)*mapped.RowPitch,desc.Width*4);
        context->Unmap(s.staging.Get(),0);s.pending=false;if(!ready||f.sequence>ready->sequence) ready=std::move(f);
    }
    uint64_t now=GetTickCount64();auto& slot=slots[slotIndex];
    if(sceneCopied&&now-lastCopy>=33&&!slot.pending) {
        ComPtr<ID3DDeviceContextState> saved;context1->SwapDeviceContextState(privateState.Get(),saved.GetAddressOf());
        auto* target=outputTarget.Get();context->OMSetRenderTargets(1,&target,nullptr);
        D3D11_TEXTURE2D_DESC desc{};output->GetDesc(&desc);D3D11_VIEWPORT vp{0,0,FLOAT(desc.Width),FLOAT(desc.Height),0,1};context->RSSetViewports(1,&vp);context->RSSetState(rasterizer.Get());
        context->OMSetDepthStencilState(noDepth.Get(),0);context->OMSetBlendState(noBlend.Get(),nullptr,0xffffffff);
        context->IASetInputLayout(nullptr);context->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_TRIANGLELIST);context->VSSetShader(fullscreen.Get(),nullptr,0);context->PSSetShader(composite.Get(),nullptr,0);
        ID3D11ShaderResourceView* textures[]{sceneView.Get(),maskView.Get(),hudView.Get()};context->PSSetShaderResources(0,3,textures);auto* samp=sampler.Get();context->PSSetSamplers(0,1,&samp);context->Draw(3,0);
        context->CopyResource(slot.staging.Get(),output.Get());slot.pending=true;slot.sequence=++sequence;
        slot.time=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        context1->SwapDeviceContextState(saved.Get(),nullptr);slotIndex=(slotIndex+1)%slots.size();lastCopy=now;++frames;
    } else if(sceneCopied&&now-lastCopy>=33) ++dropped;
    FLOAT clear[4]{};context->ClearRenderTargetView(maskTarget.Get(),clear);context->ClearRenderTargetView(hudTarget.Get(),clear);hudPhase=false;sceneCopied=false;return ready;
}
