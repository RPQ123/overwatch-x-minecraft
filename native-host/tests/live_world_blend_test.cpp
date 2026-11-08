#include "../src/live_world_blend.hpp"
#include "../src/pose_warp.hpp"
#include "../src/boss_health_overlay.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main() {
    ComPtr<ID3D11Device> dev;ComPtr<ID3D11DeviceContext> ctx;gpuCheck(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,dev.GetAddressOf(),nullptr,ctx.GetAddressOf()),"live test device");
    LiveWorldBlend blend(dev.Get());
    WorldFrame f;f.width=32;f.height=18;f.generation=17;f.mcFrame=1;f.rgba.assign(32*18*4,255);for(size_t i=0;i<f.rgba.size();i+=4) {f.rgba[i]=0;f.rgba[i+1]=0;}
    auto run=[&](UINT width,UINT height,bool left,Matrix warp=Matrix::identity(),bool preserveHand=true,float exposure=1.f,bool neutralMetal=false,bool nativeSamples=false,bool splitGroups=false) {
        D3D11_TEXTURE2D_DESC d{};d.Width=width;d.Height=height;d.MipLevels=1;d.ArraySize=1;d.SampleDesc.Count=1;d.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.BindFlags=D3D11_BIND_RENDER_TARGET;
        ComPtr<ID3D11Texture2D> color,depth;gpuCheck(dev->CreateTexture2D(&d,nullptr,color.GetAddressOf()),"live test color");ComPtr<ID3D11RenderTargetView> rtv;gpuCheck(dev->CreateRenderTargetView(color.Get(),nullptr,rtv.GetAddressOf()),"live test RTV");
        d.Format=DXGI_FORMAT_R24G8_TYPELESS;d.BindFlags=D3D11_BIND_DEPTH_STENCIL;gpuCheck(dev->CreateTexture2D(&d,nullptr,depth.GetAddressOf()),"live test depth");
        std::vector<uint32_t> z(size_t(width)*height,0x400000);ctx->UpdateSubresource(depth.Get(),0,nullptr,z.data(),width*4,0);
        blend.beginFrame();if(preserveHand)blend.captureBefore(depth.Get());
        for(UINT y=0;y<height;y++) for(UINT x=0;x<width;x++) z[y*width+x]=(splitGroups?x<width/3:(x<width/2)==left)?0xc00000:0xab400000;
        ctx->UpdateSubresource(depth.Get(),0,nullptr,z.data(),width*4,0);if(preserveHand)blend.captureAfter(depth.Get());
        if(splitGroups){
            // A real world draw BETWEEN hand groups writes the middle third.
            // It must never become foreground just because a later hand draws.
            for(UINT y=0;y<height;y++)for(UINT x=width/3;x<width*2/3;x++)z[y*width+x]=0x650000;
            ctx->UpdateSubresource(depth.Get(),0,nullptr,z.data(),width*4,0);blend.captureBefore(depth.Get());
            for(UINT y=0;y<height;y++)for(UINT x=width*2/3;x<width;x++)z[y*width+x]=0xd00000;
            ctx->UpdateSubresource(depth.Get(),0,nullptr,z.data(),width*4,0);blend.captureAfter(depth.Get());
        }
        FLOAT red[]={neutralMetal?.45f:exposure==1?1.f:.25f,neutralMetal?.38f:0,neutralMetal?.24f:0,.5f};ctx->ClearRenderTargetView(rtv.Get(),red);auto* bound=rtv.Get();ctx->OMSetRenderTargets(1,&bound,nullptr);
        std::vector<unsigned char> originalPixels;
        if(nativeSamples) {
            // Real shader/texture readback: black, deep gray, colored midtones,
            // highlights and variable alpha must survive the native-RGB path.
            const std::array<std::array<unsigned char,4>,8> samples{{
                {{0,0,0,0}},{{3,5,7,17}},{{16,16,16,64}},{{34,26,19,95}},
                {{83,112,179,128}},{{144,89,42,191}},{{240,242,244,254}},{{255,255,255,255}}
            }};
            originalPixels.resize(size_t(width)*height*4);
            for(UINT y=0;y<height;y++)for(UINT x=0;x<width;x++)
                std::copy(samples[(x+y)%samples.size()].begin(),samples[(x+y)%samples.size()].end(),originalPixels.begin()+(size_t(y)*width+x)*4);
            ctx->UpdateSubresource(color.Get(),0,nullptr,originalPixels.data(),width*4,0);
        }
        D3D11_VIEWPORT sentinel{3,5,100,60,.2f,.9f};ctx->RSSetViewports(1,&sentinel);ctx->IASetPrimitiveTopology(D3D11_PRIMITIVE_TOPOLOGY_LINESTRIP);
        blend.draw(color.Get(),f,warp,preserveHand,exposure,0.f,neutralMetal);
        UINT count=1;D3D11_VIEWPORT vp{};ctx->RSGetViewports(&count,&vp);assert(count==1&&vp.TopLeftX==3&&vp.MinDepth==.2f);
        D3D11_PRIMITIVE_TOPOLOGY topology;ctx->IAGetPrimitiveTopology(&topology);assert(topology==D3D11_PRIMITIVE_TOPOLOGY_LINESTRIP);ComPtr<ID3D11RenderTargetView> current;ctx->OMGetRenderTargets(1,current.GetAddressOf(),nullptr);assert(current.Get()==rtv.Get());
        d.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.Usage=D3D11_USAGE_STAGING;d.BindFlags=0;d.CPUAccessFlags=D3D11_CPU_ACCESS_READ;ComPtr<ID3D11Texture2D> read;gpuCheck(dev->CreateTexture2D(&d,nullptr,read.GetAddressOf()),"live test readback");ctx->CopyResource(read.Get(),color.Get());D3D11_MAPPED_SUBRESOURCE m{};gpuCheck(ctx->Map(read.Get(),0,D3D11_MAP_READ,0,&m),"live test read");
        for(UINT y=0;y<height;y++) for(UINT x=0;x<width;x++) {auto* pixel=static_cast<unsigned char*>(m.pData)+y*m.RowPitch+x*4;bool hand=preserveHand&&(splitGroups?(x<width/3||x>=width*2/3):(x<width/2)==left);
            if(nativeSamples){
                auto* original=originalPixels.data()+(size_t(y)*width+x)*4;
                for(int channel=0;channel<4;channel++)
                    assert(pixel[channel]==(hand||channel==3?original[channel]:channel==2?255:0));
            }else if(neutralMetal&&hand){
                assert(pixel[0]<115&&pixel[2]>61&&pixel[3]==128);
                float luminance=.2126f*std::pow(pixel[0]/255.f,2.2f)+.7152f*std::pow(pixel[1]/255.f,2.2f)+.0722f*std::pow(pixel[2]/255.f,2.2f);
                float original=.2126f*std::pow(.45f,2.2f)+.7152f*std::pow(.38f,2.2f)+.0722f*std::pow(.24f,2.2f);assert(std::abs(luminance-original)<.004f);
            }else{int expected=hand?(exposure==1?255:int(std::lround(std::pow(64.f/255,1.f/exposure)*255))):0;assert(std::abs(int(pixel[0])-expected)<=1&&pixel[1]==0&&pixel[2]==(hand?0:255)&&pixel[3]==128);}}
        ctx->Unmap(read.Get(),0);ctx->ClearState();
    };
    run(128,72,true);assert(blend.textureAllocations()==5&&blend.colorUploads()==1);
    run(128,72,false);assert(blend.textureAllocations()==5&&blend.colorUploads()==1); // Moving mask, cached source.
    f.mcFrame++;run(128,72,true);assert(blend.colorUploads()==2);
    run(160,90,false);assert(blend.textureAllocations()==9&&blend.colorUploads()==2);
    auto outside=Matrix::identity();outside.m[3]=5;run(160,90,true,outside); // Source rays outside the MC frame never reveal native red background.
    auto behind=Matrix::identity();behind.m[15]=-1;run(160,90,false,behind);
    run(160,90,true,Matrix::identity(),false); // No hand draw: never retain a previous frame's mask.
    run(192,108,true,Matrix::identity(),false); // Resize before a depth pair exists.
    run(192,108,false); // A real pair resumes after world-only fallback at the same size.
    run(192,108,true,Matrix::identity(),true,1.3f); // Lift native hand shadows only, retaining MC color and alpha.
    run(192,108,true,Matrix::identity(),true,1.f,true); // Neutral Pharah metal only; exact background/mask/alpha and luminance preserved.
    run(192,108,true,Matrix::identity(),true,1.f,false,true); // Exact native RGB/alpha through an actual GPU mask.
    run(192,108,false,Matrix::identity(),true,1.f,false,true); // Moving mask must not tint MC or retain prior native pixels.
    run(192,108,true,Matrix::identity(),true,1.f,false,true,true); // Split reload: both native groups, zero intervening-world pixels.
    blend.beginFrame();assert(!blend.ready());bool offThreadRejected=false;std::thread worker([&] {try {blend.beginFrame();}catch(const std::exception&) {offThreadRejected=true;}});worker.join();assert(offThreadRejected);
    HostPose source,target;source.frame=11;source.generation=target.generation=23;source.flags=target.flags=2;source.width=target.width=128;source.height=target.height=72;
    source.basis=target.basis={1,0,0,0,1,0,0,0,1};target.fx=.8f;target.fy=1.4f;source.fx=target.fx;source.fy=target.fy;
    f.hostFrame=11;f.hostGeneration=23;f.nearPlane=.05f;f.farPlane=256;
    Matrix p;p.m[0]=target.fx/1.18f;p.m[5]=target.fy/1.18f;p.m[10]=(f.farPlane+f.nearPlane)/(f.nearPlane-f.farPlane);p.m[11]=2*f.farPlane*f.nearPlane/(f.nearPlane-f.farPlane);p.m[14]=-1;
    for(int r=0;r<4;r++) for(int c=0;c<4;c++) f.projection[c*4+r]=p.m[r*4+c];
    auto warp=poseWarp(f,source,target);auto ray=warp.apply({1,1,-1,1});assert(std::abs(ray[0]/ray[3]-1/1.18f)<1e-5&&warpCoversView(warp));
    // Missing/stale pose history must hold the same lens crop, not zoom out to
    // the guest's overscan FOV. The old identity fallback changed block scale.
    auto hold=heldImageWarp(f,target);
    auto wideTarget=target;wideTarget.fx*=.5f;wideTarget.fy*=.5f;
    assert(!warpCoversView(heldImageWarp(f,wideTarget)));
    auto wideFrame=f;wideFrame.projection[0]*=.5f;wideFrame.projection[5]*=.5f;
    assert(warpCoversView(heldImageWarp(wideFrame,wideTarget)));
    for(float x:{-.8f,0.f,.8f})for(float y:{-.8f,0.f,.8f}) {
        auto a=hold.apply({x,y,-1,1}),b=warp.apply({x,y,-1,1});
        assert(std::abs(a[0]/a[3]-b[0]/b[3])<1e-5&&std::abs(a[1]/a[3]-b[1]/b[3])<1e-5);
    }
    auto rotation=cameraYaw(.03f);for(int r=0;r<3;r++) for(int c=0;c<3;c++) target.basis[c*3+r]=rotation.m[r*4+c];
    warp=poseWarp(f,source,target);auto center=warp.apply({0,0,-1,1});assert(std::abs(center[0]/center[3]+p.m[0]*std::tan(.03f))<1e-5&&warpCoversView(warp));
    // Fast turns may exceed the real overscan. All pixels must use one bounded
    // projective transform, rather than switching orientation per pixel.
    for(int degrees=-180;degrees<=180;degrees++) {
        auto turn=cameraYaw(degrees*3.14159265f/180);for(int r=0;r<3;r++)for(int c=0;c<3;c++)target.basis[c*3+r]=turn.m[r*4+c];
        auto desired=poseWarp(f,source,target);float fraction=-1;
        auto limited=coverageLimitedWarp(heldImageWarp(f,target),desired,&fraction);
        assert(fraction>=0&&fraction<=1&&warpCoversView(limited));
        if(warpCoversView(desired)){assert(fraction==1);for(int i=0;i<16;i++)assert(limited.m[i]==desired.m[i]);}
        for(float x:{-.95f,0.f,.95f})for(float y:{-.95f,0.f,.95f}) {
            auto q=limited.apply({x,y,-1,1});assert(q[3]>0&&std::abs(q[0])<=q[3]&&std::abs(q[1])<=q[3]);
        }
    }
    target.generation++;bool rejected=false;try {poseWarp(f,source,target);}catch(const std::exception&) {rejected=true;}assert(rejected);
    {
        BossHealthOverlay overlay(dev.Get());D3D11_TEXTURE2D_DESC d{};d.Width=1280;d.Height=720;d.MipLevels=1;d.ArraySize=1;d.SampleDesc.Count=1;d.Format=DXGI_FORMAT_R8G8B8A8_UNORM;d.BindFlags=D3D11_BIND_RENDER_TARGET;
        ComPtr<ID3D11Texture2D> target;gpuCheck(dev->CreateTexture2D(&d,nullptr,target.GetAddressOf()),"boss test color");ComPtr<ID3D11RenderTargetView> rtv;gpuCheck(dev->CreateRenderTargetView(target.Get(),nullptr,rtv.GetAddressOf()),"boss test RTV");
        FLOAT bg[]{0,0,0,1};ctx->ClearRenderTargetView(rtv.Get(),bg);D3D11_VIEWPORT sentinel{3,5,100,60,.2f,.9f};ctx->RSSetViewports(1,&sentinel);
        WorldFrame hud;hud.width=1280;hud.height=720;hud.hudWidth=512;hud.hudHeight=64;hud.mcFrame=1;hud.hudRgba.resize(512*64*4);
        for(int y=36;y<52;y++)for(int x=4;x<256;x++){auto i=(y*512+x)*4;hud.hudRgba[i]=176;hud.hudRgba[i+2]=214;hud.hudRgba[i+3]=255;}
        overlay.draw(target.Get(),hud);UINT count=1;D3D11_VIEWPORT vp{};ctx->RSGetViewports(&count,&vp);assert(vp.TopLeftX==3&&vp.TopLeftY==5);
        d.Usage=D3D11_USAGE_STAGING;d.BindFlags=0;d.CPUAccessFlags=D3D11_CPU_ACCESS_READ;ComPtr<ID3D11Texture2D> read;gpuCheck(dev->CreateTexture2D(&d,nullptr,read.GetAddressOf()),"boss test staging");ctx->CopyResource(read.Get(),target.Get());D3D11_MAPPED_SUBRESOURCE mapped{};gpuCheck(ctx->Map(read.Get(),0,D3D11_MAP_READ,0,&mapped),"boss test read");
        auto pixel=[&](int x,int y){return static_cast<unsigned char*>(mapped.pData)+y*mapped.RowPitch+x*4;};
        assert(pixel(537,48)[0]>140&&pixel(742,48)[0]<60&&pixel(10,10)[0]==0);
        ctx->Unmap(read.Get(),0);ctx->ClearState();
    }
    std::cout<<"PASS: GPU depth-pair mask, native state, cached textures/uploads, resize, thread guard, paired rotation warp; screen-space HUD image and untouched surrounding pixels.\n";
}
