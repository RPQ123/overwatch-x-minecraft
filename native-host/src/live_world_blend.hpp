#pragma once
#include "frame_compositor.hpp"

namespace passthrough {
// Persistent, render-thread-only compositor. All native surfaces are transient
// arguments; only private copies persist, so ResizeBuffers has no lab references.
class LiveWorldBlend {
    std::thread::id owner=std::this_thread::get_id();
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context,commands;
    ComPtr<ID3D11VertexShader> vs;
    ComPtr<ID3D11PixelShader> ps,maskPs;
    ComPtr<ID3D11BlendState> maskMax;
    ComPtr<ID3D11RasterizerState> raster;
    ComPtr<ID3D11Buffer> constants;
    ComPtr<ID3D11Texture2D> beforeDepth,afterDepth,nativeColor,guestColor,handMask;
    ComPtr<ID3D11ShaderResourceView> beforeView,afterView,nativeView,guestView,maskView;
    ComPtr<ID3D11RenderTargetView> maskTarget;
    UINT width=0,height=0,guestWidth=0,guestHeight=0;
    DXGI_FORMAT colorFormat=DXGI_FORMAT_UNKNOWN;
    uint64_t sourceGeneration=0,sourceFrame=0;
    bool before=false,after=false,maskReady=false;
    unsigned allocations=0,uploads=0;
    void assertOwner() const;
    void depthSize(ID3D11Texture2D* source);
    void accumulateMask();
public:
    explicit LiveWorldBlend(ID3D11Device* input);
    void beginFrame();
    void captureBefore(ID3D11Texture2D* depth);
    void captureAfter(ID3D11Texture2D* depth);
    void captureSelection(ID3D11Texture2D* depth);
    bool ready() const {return before&&after;}
    void draw(ID3D11Texture2D* target,const WorldFrame& frame,const Matrix& targetToSource,bool preserveHand=true,float handExposure=1.f,float selectionDepthCutoff=0.f,bool neutralMetal=false);
    unsigned textureAllocations() const {return allocations;}
    unsigned colorUploads() const {return uploads;}
};
}
