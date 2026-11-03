#pragma once
#include "render.hpp"
#include <functional>
#include <array>
#include <optional>
#include <chrono>
#include <map>
#include <atomic>

// CPU transport contains only a premultiplied native hero/HUD layer, never world color.
class HeroStream {
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context;
    ComPtr<ID3D11Texture2D> handMask,hud,scene,output;
    ComPtr<ID3D11RenderTargetView> maskTarget,hudTarget,outputTarget;
    ComPtr<ID3D11ShaderResourceView> maskView,hudView,sceneView;
    ComPtr<ID3D11PixelShader> white,composite;
    ComPtr<ID3D11VertexShader> fullscreen;
    ComPtr<ID3D11SamplerState> sampler;
    ComPtr<ID3D11RasterizerState> rasterizer;
    ComPtr<ID3D11DepthStencilState> noDepth;
    ComPtr<ID3D11BlendState> noBlend;
    ComPtr<ID3D11DeviceContext1> context1;
    ComPtr<ID3DDeviceContextState> privateState;
    struct DepthCache {ComPtr<ID3D11DepthStencilState> original,capture;};
    struct BlendCache {ComPtr<ID3D11BlendState> original,capture;};
    std::map<std::pair<uintptr_t,bool>,DepthCache> depthCache;
    std::map<uintptr_t,BlendCache> blendCache;
    struct Slot {ComPtr<ID3D11Texture2D> staging;bool pending=false;uint64_t sequence=0,time=0;};
    std::array<Slot,3> slots;
    unsigned slotIndex=0;
    uint64_t sequence=0,lastCopy=0;
    UINT width,height;
    bool hudPhase=false,sceneCopied=false;
    void texture(DXGI_FORMAT format,ComPtr<ID3D11Texture2D>& t,ComPtr<ID3D11RenderTargetView>& r,ComPtr<ID3D11ShaderResourceView>* v,UINT w,UINT h);
public:
    struct Frame {uint64_t sequence,time;UINT width,height;std::vector<unsigned char> rgba;};
    std::atomic<uint64_t> handDraws{0},hudDraws{0},dropped{0},frames{0};
    std::atomic<unsigned> observedUavMask{0},skippedStreamOutput{0};
    HeroStream(ID3D11Device* d,UINT w,UINT h,DXGI_FORMAT format);
    void replay(bool firstPerson,bool originalBackbuffer,const std::function<void()>& draw);
    void boundary(ID3D11Texture2D* color);
    std::optional<Frame> present();
};
