#include "../src/local_hero_spawn.hpp"
#include <windows.h>
#include <d3d11.h>
#include <wrl/client.h>
#include <cassert>
#include <iostream>
using namespace passthrough;using Microsoft::WRL::ComPtr;
unsigned calls=0;DWORD owner=0;
SpawnPairAbi* originalFixture(SpawnerAbi* self,SpawnPairAbi* pair) {
    assert(GetCurrentThreadId()==owner&&++calls==1&&self->controller.movement==2&&self->model.weapon==1);
    self->controllerEntity=0x10000;self->modelEntity=0x20000;*pair={0x10000,0x20000};return pair;
}
int main() {
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"OWMCLocalHeroTest";RegisterClassW(&wc);
    HWND window=CreateWindowW(wc.lpszClassName,L"Hidden native-call lifecycle fixture",WS_OVERLAPPEDWINDOW,0,0,160,120,nullptr,nullptr,wc.hInstance,nullptr);assert(window);
    DXGI_SWAP_CHAIN_DESC sd{};sd.BufferDesc.Width=128;sd.BufferDesc.Height=72;sd.BufferDesc.Format=DXGI_FORMAT_R8G8B8A8_UNORM;sd.SampleDesc.Count=1;sd.BufferUsage=DXGI_USAGE_RENDER_TARGET_OUTPUT;sd.BufferCount=1;sd.OutputWindow=window;sd.Windowed=TRUE;
    ComPtr<ID3D11Device> device;ComPtr<ID3D11DeviceContext> context;ComPtr<IDXGISwapChain> swap;
    assert(SUCCEEDED(D3D11CreateDeviceAndSwapChain(nullptr,D3D_DRIVER_TYPE_WARP,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&sd,swap.GetAddressOf(),device.GetAddressOf(),nullptr,context.GetAddressOf())));
    auto original=*reinterpret_cast<void***>(swap.Get());auto oldContext=*reinterpret_cast<void***>(context.Get());
    HMODULE module=LoadLibraryW(L"native-host/build/owmc-local-hero-spawn-v1.dll");assert(module);
    BOOL(*attach)(IDXGISwapChain*,OriginalSpawnFn)=nullptr;BOOL(*verify)()=nullptr;
    auto a=GetProcAddress(module,"OWMC_LocalHeroTestAttach"),v=GetProcAddress(module,"OWMC_LocalHeroTestVerify");memcpy(&attach,&a,sizeof attach);memcpy(&verify,&v,sizeof verify);
    assert(attach&&verify&&attach(swap.Get(),originalFixture));owner=GetCurrentThreadId();
    assert(SUCCEEDED(swap->Present(0,DXGI_PRESENT_TEST))&&calls==0);
    for(int i=0;i<3;i++)assert(SUCCEEDED(swap->Present(0,0)));
    assert(verify()&&calls==1&&*reinterpret_cast<void***>(swap.Get())==original&&*reinterpret_cast<void***>(context.Get())==oldContext);
    assert(SUCCEEDED(swap->Present(0,0))&&calls==1);assert(SUCCEEDED(swap->ResizeBuffers(1,160,90,DXGI_FORMAT_R8G8B8A8_UNORM,0)));
    DestroyWindow(window);std::cout<<"PASS: original member called once on Present thread, test presents ignored, three-frame pointer restoration, no context hook, no retained backbuffer.\n";
}
