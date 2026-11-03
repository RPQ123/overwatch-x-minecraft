#pragma once
#include "frame_compositor.hpp"
#include <d3d11_1.h>

namespace passthrough {
// Only a bounded first-frame proof. Original HUD is drawn by OW after this call.
// The caller supplies an observed original hand mask from this same native frame.
class WorldBlend {
    std::thread::id owner=std::this_thread::get_id();
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context,commands;
    ComPtr<ID3D11VertexShader> vs;
    ComPtr<ID3D11PixelShader> ps;
    ComPtr<ID3D11RasterizerState> raster;
public:
    explicit WorldBlend(ID3D11Device* input);
    void draw(ID3D11Texture2D* target,const WorldFrame& source,const std::vector<unsigned char>& handMask);
};
}
