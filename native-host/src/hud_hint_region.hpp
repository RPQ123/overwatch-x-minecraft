#pragma once
#include "frame_compositor.hpp"
#include "debug_banner_fill.hpp"
#include <memory>

namespace passthrough {
// The calibrated Genji change-hero banner only. Save the actual current-frame
// composed terrain/hands before HUD, then restore that region after HUD.
// No static pixels, color key, CPU capture, or suppression of the other HUD.
class HudHintRegion {
    ComPtr<ID3D11Texture2D> saved;
    D3D11_BOX box{};DXGI_FORMAT format=DXGI_FORMAT_UNKNOWN;
    bool debug=false;
    std::unique_ptr<DebugBannerFill> debugFill;
public:
    explicit HudHintRegion(bool debugRegion=false):debug(debugRegion){}
    static D3D11_BOX region(UINT w,UINT h){return {UINT(w*.414),UINT(h*.714),0,UINT(w*.586),UINT(h*.766),1};}
    // Debug mode reconstructs only the text line from the final HUD's bordering
    // rows, retaining F1/scope shading. Never restore a broad pre-HUD rectangle.
    static D3D11_BOX debugRegion(UINT w,UINT h){return DebugBannerFill::region(w,h);}
    void capture(ID3D11DeviceContext* context,ID3D11Texture2D* target){
        if(debug)return;
        D3D11_TEXTURE2D_DESC d{};target->GetDesc(&d);auto next=region(d.Width,d.Height);
        if(!saved||box.right-box.left!=next.right-next.left||box.bottom-box.top!=next.bottom-next.top||d.Format!=format){
            saved.Reset();auto small=d;small.Width=next.right-next.left;small.Height=next.bottom-next.top;small.BindFlags=0;small.CPUAccessFlags=0;small.MiscFlags=0;small.Usage=D3D11_USAGE_DEFAULT;
            ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());gpuCheck(device->CreateTexture2D(&small,nullptr,saved.GetAddressOf()),"current pre-HUD hint region");format=d.Format;
        }
        box=next;context->CopySubresourceRegion(saved.Get(),0,0,0,0,target,0,&box);
    }
    void restore(ID3D11DeviceContext* context,ID3D11Texture2D* target){
        if(debug){
            if(!debugFill){ComPtr<ID3D11Device> device;context->GetDevice(device.GetAddressOf());debugFill=std::make_unique<DebugBannerFill>(device.Get());}
            debugFill->draw(context,target);return;
        }
        if(saved)context->CopySubresourceRegion(target,0,box.left,box.top,0,saved.Get(),0,nullptr);
    }
};
}
