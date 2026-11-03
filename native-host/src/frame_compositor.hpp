#pragma once
#include "world_frame.hpp"
#include <d3d11.h>
#include <d3dcompiler.h>
#include <wrl/client.h>
#include <thread>

namespace passthrough {
using Microsoft::WRL::ComPtr;
inline void gpuCheck(HRESULT hr,const char* action) {if(FAILED(hr)) throw std::runtime_error(std::string(action)+" HRESULT="+std::to_string(hr));}
struct Matrix {
    std::array<float,16> m{}; // Row-major, multiplies a column vector.
    static Matrix identity();
    static Matrix fromColumnMajor(const std::array<float,16>& source);
    Matrix inverse() const;
    Matrix operator*(const Matrix& other) const;
    std::array<float,4> apply(std::array<float,4> v) const;
};
// Rotation-only reprojection. Translation/disocclusion need a separate depth-aware path.
Matrix cameraYaw(float radians);
struct CompositePixels {uint32_t width{},height{};std::vector<unsigned char> rgba;std::vector<float> depth;};
// Isolated lab renderer. Owns a dedicated immediate context; NOT a host injection adapter.
// Construction, upload, draw, readback and destruction stay on the owning thread.
class FrameCompositor {
    std::thread::id owner=std::this_thread::get_id();
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context;
    ComPtr<ID3D11VertexShader> vs;
    ComPtr<ID3D11PixelShader> ps;
    ComPtr<ID3D11Buffer> constants;
    ComPtr<ID3D11RasterizerState> raster;
    ComPtr<ID3D11Texture2D> inputColor,inputDepth,outputColor,outputDepth,readColor,readDepth;
    ComPtr<ID3D11ShaderResourceView> colorSrv,depthSrv;
    ComPtr<ID3D11RenderTargetView> colorRtv,depthRtv;
    uint32_t width=0,height=0;
    void assertOwner() const;
    void resize(uint32_t w,uint32_t h);
public:
    explicit FrameCompositor(bool warp=true);
    CompositePixels render(const WorldFrame& frame,const Matrix& targetToSource=Matrix::identity());
};
}
