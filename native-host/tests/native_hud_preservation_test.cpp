#include "../src/live_world_blend.hpp"
#include "../src/hud_hint_region.hpp"
#include <d3d11_1.h>
#include <cassert>
#include <iostream>
using namespace passthrough;

// Exercise the production debug-banner API around real GPU world composition,
// later native F1/scope HUD pixels and finally DEV text. No game/input required.
int main() {
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;
    gpuCheck(D3D11CreateDevice(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,
        device.GetAddressOf(),nullptr,context.GetAddressOf()),"HUD fixture device");
    ComPtr<ID3D11DeviceContext1> context1;gpuCheck(context.As(&context1),"HUD fixture context1");
    LiveWorldBlend blend(device.Get());HudHintRegion debugBanner{true};
    WorldFrame world;world.width=2;world.height=2;world.generation=1;world.mcFrame=1;
    world.rgba={32,96,160,255,48,112,176,255,64,128,192,255,80,144,208,255};
    uint64_t checked=0;
    for(auto size:std::array<std::pair<UINT,UINT>,3>{{{1920,1080},{2560,1440},{1280,720}}}) {
        const auto [width,height]=size;
        D3D11_TEXTURE2D_DESC desc{};desc.Width=width;desc.Height=height;desc.MipLevels=1;
        desc.ArraySize=1;desc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;desc.SampleDesc.Count=1;
        desc.BindFlags=D3D11_BIND_RENDER_TARGET;
        ComPtr<ID3D11Texture2D> target;gpuCheck(device->CreateTexture2D(&desc,nullptr,target.GetAddressOf()),"HUD fixture target");
        ComPtr<ID3D11RenderTargetView> view;gpuCheck(device->CreateRenderTargetView(target.Get(),nullptr,view.GetAddressOf()),"HUD fixture RTV");
        desc.Usage=D3D11_USAGE_STAGING;desc.BindFlags=0;desc.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
        ComPtr<ID3D11Texture2D> expected,actual;
        gpuCheck(device->CreateTexture2D(&desc,nullptr,expected.GetAddressOf()),"HUD fixture expected");
        gpuCheck(device->CreateTexture2D(&desc,nullptr,actual.GetAddressOf()),"HUD fixture actual");
        // Ordinary HUD -> F1 help -> scope -> F1 while scoped -> close both.
        for(unsigned state:std::array<unsigned,5>{0,1,2,3,0}) {
            const FLOAT clear[]{1,0,0,1};context->ClearRenderTargetView(view.Get(),clear);
            blend.beginFrame();blend.draw(target.Get(),world,Matrix::identity(),false);
            debugBanner.capture(context.Get(),target.Get());
            // Each late overlay crosses all four edges of the old debug box.
            D3D11_RECT corner{LONG(width*.88),0,LONG(width),LONG(height*.10)};
            if(state&2) {
                const FLOAT scope[]{.0627451f,.0156863f,.0941176f,1};
                context1->ClearView(view.Get(),scope,&corner,1);
            }
            if(state&1) {
                const FLOAT help[]{.1254902f,.1882353f,.2509804f,1};
                context1->ClearView(view.Get(),help,&corner,1);
            }
            context->CopyResource(expected.Get(),target.Get());
            // Model DEV ENABLED being drawn last. The fill must remove its RGB
            // without exposing the pre-HUD world through F1/scope darkening.
            const LONG left=LONG(width)-LONG(std::ceil(200.0*height/1440));
            const LONG right=LONG(width)-LONG(std::floor(38.0*height/1440));
            D3D11_RECT label{left,LONG(std::floor(29.0*height/1440)),right,LONG(std::ceil(65.0*height/1440))};
            const FLOAT devText[]{1,0,1,1};
            context1->ClearView(view.Get(),devText,&label,1);
            debugBanner.restore(context.Get(),target.Get());
            context->CopyResource(actual.Get(),target.Get());
            D3D11_MAPPED_SUBRESOURCE a{},b{};
            gpuCheck(context->Map(expected.Get(),0,D3D11_MAP_READ,0,&a),"HUD fixture expected pixels");
            gpuCheck(context->Map(actual.Get(),0,D3D11_MAP_READ,0,&b),"HUD fixture actual pixels");
            for(UINT y=0;y<height;y++) {
                const auto* before=static_cast<const unsigned char*>(a.pData)+y*a.RowPitch;
                const auto* after=static_cast<const unsigned char*>(b.pData)+y*b.RowPitch;
                if(memcmp(before,after,size_t(width)*4)!=0) {
                    std::cerr<<"FAIL: DEV label remains or native HUD overwritten at "<<width<<'x'<<height<<", state="<<state<<", y="<<y<<'\n';
                    return 1;
                }
                // With no overlay, the former hole must contain actual MC RGB.
                if(!state)for(UINT x=0;x<width;x++)assert(after[x*4+2]>=160&&after[x*4+3]==255);
            }
            checked+=uint64_t(width)*height;
            context->Unmap(expected.Get(),0);context->Unmap(actual.Get(),0);
        }
    }
    for(auto format:{DXGI_FORMAT_R8G8B8A8_UNORM,DXGI_FORMAT_B8G8R8A8_UNORM}) {
        // Affine shaded background with a vertical terrain edge through the
        // label: row reconstruction must retain its gradient/edge and alpha.
        constexpr UINT width=320,height=180;auto box=HudHintRegion::debugRegion(width,height);
        std::vector<unsigned char> clean(width*height*4),marked;
        for(UINT y=0;y<height;y++)for(UINT x=0;x<width;x++) {
            size_t i=(size_t(y)*width+x)*4;
            clean[i]=x<305?48:96;clean[i+1]=16+(y%100)*2;clean[i+2]=224-y;
            clean[i+3]=(x+3*y)%256;
        }
        marked=clean;
        for(UINT y=box.top;y<box.bottom;y++)for(UINT x=box.left;x<box.right;x++) {
            size_t i=(size_t(y)*width+x)*4;marked[i]=255;marked[i+1]=0;marked[i+2]=255;
        }
        D3D11_TEXTURE2D_DESC d{};d.Width=width;d.Height=height;d.MipLevels=1;d.ArraySize=1;
        d.Format=format;d.SampleDesc.Count=1;d.BindFlags=D3D11_BIND_RENDER_TARGET;
        ComPtr<ID3D11Texture2D> target,readback;
        gpuCheck(device->CreateTexture2D(&d,nullptr,target.GetAddressOf()),"gradient target");
        context->UpdateSubresource(target.Get(),0,nullptr,marked.data(),width*4,0);
        d.BindFlags=0;d.Usage=D3D11_USAGE_STAGING;d.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
        gpuCheck(device->CreateTexture2D(&d,nullptr,readback.GetAddressOf()),"gradient readback");
        D3D11_VIEWPORT viewport{5,7,111,99,.1f,.9f};context->RSSetViewports(1,&viewport);
        D3D11_RECT scissor{3,4,75,76};context->RSSetScissorRects(1,&scissor);
        debugBanner.restore(context.Get(),target.Get());
        UINT count=1;D3D11_VIEWPORT actualViewport{};context->RSGetViewports(&count,&actualViewport);
        assert(count==1&&!memcmp(&viewport,&actualViewport,sizeof viewport));
        D3D11_RECT actualScissor{};count=1;context->RSGetScissorRects(&count,&actualScissor);
        assert(count==1&&!memcmp(&scissor,&actualScissor,sizeof scissor));
        ComPtr<ID3D11PixelShader> ps;context->PSGetShader(ps.GetAddressOf(),nullptr,nullptr);assert(!ps);
        context->CopyResource(readback.Get(),target.Get());D3D11_MAPPED_SUBRESOURCE pixels{};
        gpuCheck(context->Map(readback.Get(),0,D3D11_MAP_READ,0,&pixels),"gradient pixels");
        for(UINT y=0;y<height;y++)for(UINT x=0;x<width;x++) {
            auto* p=static_cast<unsigned char*>(pixels.pData)+y*pixels.RowPitch+x*4;
            size_t i=(size_t(y)*width+x)*4;
            bool inside=x>=box.left&&x<box.right&&y>=box.top&&y<box.bottom;
            for(unsigned c=0;c<4;c++)assert(std::abs(int(p[c])-int(clean[i+c]))<=(inside&&c<3?1:0));
        }
        context->Unmap(readback.Get(),0);checked+=width*height;
    }
    std::cout<<"PASS: DEV hidden; F1/scope/world preserved across 15 frames (33408000 exact pixels), 2 gradient/alpha/RGBA-BGRA/state fixtures; "<<checked<<" total pixels.\n";
}
