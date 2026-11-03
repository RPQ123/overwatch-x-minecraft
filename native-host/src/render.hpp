#pragma once
#include <d3d11_1.h>
#include <d3dcompiler.h>
#include <wrl/client.h>
#include "math.hpp"
#include "mesh.hpp"

using Microsoft::WRL::ComPtr;
inline void check(HRESULT result,const char* operation) {
    if(FAILED(result)) throw std::runtime_error(std::string(operation)+" HRESULT="+std::to_string(result));
}
class Renderer {
    Mesh mesh;
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context;
    ComPtr<ID3D11DeviceContext1> context1;
    ComPtr<ID3DDeviceContextState> privateState;
    ComPtr<ID3D11VertexShader> vertexShader;
    ComPtr<ID3D11PixelShader> pixelShader;
    ComPtr<ID3D11InputLayout> layout;
    ComPtr<ID3D11Buffer> vertexBuffer;
    ComPtr<ID3D11ShaderResourceView> texture;
    ComPtr<ID3D11SamplerState> sampler;
    ComPtr<ID3D11RasterizerState> rasterizer;
    ComPtr<ID3D11DepthStencilState> depthState;
    ComPtr<ID3D11Texture2D> depthTexture;
    ComPtr<ID3D11DepthStencilView> depthView;
    UINT depthWidth=0,depthHeight=0,depthSamples=0;
    UINT vertexCapacity=0;
    void drawBound(ID3D11RenderTargetView* color,ID3D11DepthStencilView* depth,
                   const D3D11_TEXTURE2D_DESC& target,const Camera& camera,Vec3 anchor,const NativeProjection* projection);
public:
    Renderer(ID3D11Device* device,Mesh data);
    void update(Mesh data);
    void draw(ID3D11Texture2D* target,const Camera& camera,Vec3 anchor,const NativeProjection* projection=nullptr);
    void drawScene(ID3D11RenderTargetView* color,ID3D11DepthStencilView* depth,
                   const Camera& camera,Vec3 anchor,const NativeProjection& projection);
    void drawOverlay(ID3D11Texture2D* target);
};
