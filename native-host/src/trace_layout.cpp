#define CINTERFACE
#include <d3d11_4.h>
#include <dxgi1_6.h>
#include <cstddef>

extern "C" size_t traceContextCount(unsigned version) {
    switch(version) {
    case 4:return sizeof(ID3D11DeviceContext4Vtbl)/sizeof(void*);
    case 3:return sizeof(ID3D11DeviceContext3Vtbl)/sizeof(void*);
    case 2:return sizeof(ID3D11DeviceContext2Vtbl)/sizeof(void*);
    case 1:return sizeof(ID3D11DeviceContext1Vtbl)/sizeof(void*);
    default:return sizeof(ID3D11DeviceContextVtbl)/sizeof(void*);
    }
}
extern "C" size_t traceSwapCount() { return sizeof(IDXGISwapChain4Vtbl)/sizeof(void*); }
static_assert(offsetof(ID3D11DeviceContextVtbl,OMSetRenderTargets)/sizeof(void*)==33);
static_assert(offsetof(ID3D11DeviceContextVtbl,OMSetRenderTargetsAndUnorderedAccessViews)/sizeof(void*)==34);
static_assert(offsetof(ID3D11DeviceContextVtbl,ClearDepthStencilView)/sizeof(void*)==53);
static_assert(offsetof(ID3D11DeviceContextVtbl,ExecuteCommandList)/sizeof(void*)==58);
static_assert(offsetof(ID3D11DeviceContextVtbl,DrawIndexed)/sizeof(void*)==12);
static_assert(offsetof(ID3D11DeviceContextVtbl,Draw)/sizeof(void*)==13);
static_assert(offsetof(ID3D11DeviceContextVtbl,DrawIndexedInstanced)/sizeof(void*)==20);
static_assert(offsetof(ID3D11DeviceContextVtbl,DrawInstanced)/sizeof(void*)==21);
static_assert(offsetof(ID3D11DeviceContextVtbl,Map)/sizeof(void*)==14);
static_assert(offsetof(ID3D11DeviceContextVtbl,Unmap)/sizeof(void*)==15);
static_assert(offsetof(ID3D11DeviceContextVtbl,UpdateSubresource)/sizeof(void*)==48);
