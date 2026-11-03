#include "../src/native_slot_filter.hpp"
#include <cassert>
#include <iostream>
bool admit=false,motion=false;bool gate(){return admit;}bool motionGate(){return motion;}
int main(){
    using namespace passthrough;NativeSlotFilter filter;
    RAWINPUT input{};input.header.dwType=RIM_TYPEKEYBOARD;input.data.keyboard.VKey='2';input.data.keyboard.MakeCode=3;assert(filter.filter(input)&&input.data.keyboard.VKey==255&&input.data.keyboard.MakeCode==0);
    input={};input.header.dwType=RIM_TYPEMOUSE;input.data.mouse.usButtonFlags=RI_MOUSE_WHEEL|RI_MOUSE_LEFT_BUTTON_DOWN;input.data.mouse.lLastX=19;assert(filter.filter(input));assert(input.data.mouse.lLastX==19&&input.data.mouse.usButtonFlags==RI_MOUSE_LEFT_BUTTON_DOWN);
    input={};input.header.dwType=RIM_TYPEKEYBOARD;input.data.keyboard.VKey='W';assert(!filter.filter(input));
    assert(filter.filter(input,true)&&input.data.keyboard.VKey==255);
    input={};input.header.dwType=RIM_TYPEKEYBOARD;input.data.keyboard.VKey='W';input.data.keyboard.Flags=RI_KEY_BREAK;assert(!filter.filter(input,true));
    input={};input.header.dwType=RIM_TYPEMOUSE;input.data.mouse.lLastX=25;input.data.mouse.lLastY=-10;input.data.mouse.usButtonFlags=RI_MOUSE_LEFT_BUTTON_DOWN|RI_MOUSE_RIGHT_BUTTON_UP;
    assert(filter.filter(input,true)&&!input.data.mouse.lLastX&&!input.data.mouse.lLastY&&input.data.mouse.usButtonFlags==(RI_MOUSE_LEFT_BUTTON_DOWN|RI_MOUSE_RIGHT_BUTTON_UP));
    input.data.mouse.usFlags=MOUSE_MOVE_ABSOLUTE|MOUSE_VIRTUAL_DESKTOP;assert(filter.filter(input,true)&&!(input.data.mouse.usFlags&MOUSE_MOVE_ABSOLUTE));
    input={};input.header.dwType=RIM_TYPEMOUSE;input.data.mouse.usFlags=MOUSE_MOVE_ABSOLUTE|MOUSE_VIRTUAL_DESKTOP;input.data.mouse.usButtonFlags=RI_MOUSE_RIGHT_BUTTON_DOWN;input.data.mouse.lLastX=40000;input.data.mouse.lLastY=30000;
    assert(filter.filter(input,true)&&!input.data.mouse.lLastX&&!input.data.mouse.lLastY&&!(input.data.mouse.usFlags&MOUSE_MOVE_ABSOLUTE)&&input.data.mouse.usButtonFlags==RI_MOUSE_RIGHT_BUTTON_DOWN);
    assert(!filter.filter(input,false)&&!input.data.mouse.lLastX&&!input.data.mouse.lLastY&&input.data.mouse.usButtonFlags==RI_MOUSE_RIGHT_BUTTON_DOWN);
    constexpr unsigned releases[]{'W',VK_CONTROL,VK_LCONTROL,VK_RCONTROL,VK_SHIFT,VK_LSHIFT,VK_RSHIFT,VK_F6};
    for(unsigned key:releases){input={};input.header.dwType=RIM_TYPEKEYBOARD;input.data.keyboard.VKey=static_cast<USHORT>(key);input.data.keyboard.Flags=RI_KEY_BREAK;assert(!filter.filter(input,true)&&input.data.keyboard.VKey==key);}
    auto library=LoadLibraryW(L"overwatch-2015/Overwatch Beta 0.8.0.24919/minhook.x64.dll");assert(library&&filter.start(gate,library,motionGate));
    GetAsyncKeyState('2');assert(filter.keyQueries==0);admit=true;
    assert(GetAsyncKeyState('2')==0&&filter.keyQueries==1);GetAsyncKeyState('Q');assert(filter.keyQueries==1);
    MSG msg{};PeekMessageW(&msg,nullptr,0,0,PM_NOREMOVE);PostThreadMessageW(GetCurrentThreadId(),WM_KEYDOWN,'2',0);assert(PeekMessageW(&msg,nullptr,WM_KEYDOWN,WM_KEYDOWN,PM_REMOVE)&&msg.message==WM_NULL);
    PostThreadMessageW(GetCurrentThreadId(),WM_KEYDOWN,'W',0);assert(PeekMessageW(&msg,nullptr,WM_KEYDOWN,WM_KEYDOWN,PM_REMOVE)&&msg.message==WM_KEYDOWN&&msg.wParam=='W');
    motion=true;assert(GetAsyncKeyState('W')==0);
    const auto priorMotionQueries=filter.keyQueries.load();assert(GetAsyncKeyState(VK_LCONTROL)==0&&GetAsyncKeyState(VK_RCONTROL)==0&&filter.keyQueries==priorMotionQueries+2);
    PostThreadMessageW(GetCurrentThreadId(),WM_KEYDOWN,'W',0);assert(PeekMessageW(&msg,nullptr,WM_KEYDOWN,WM_KEYDOWN,PM_REMOVE)&&msg.message==WM_NULL);
    PostThreadMessageW(GetCurrentThreadId(),WM_KEYUP,'W',0);assert(PeekMessageW(&msg,nullptr,WM_KEYUP,WM_KEYUP,PM_REMOVE)&&msg.message==WM_KEYUP);
    for(unsigned key:releases){PostThreadMessageW(GetCurrentThreadId(),WM_KEYUP,key,0);assert(PeekMessageW(&msg,nullptr,WM_KEYUP,WM_KEYUP,PM_REMOVE)&&msg.message==WM_KEYUP&&msg.wParam==key);}
    PostThreadMessageW(GetCurrentThreadId(),WM_MOUSEMOVE,0,123);assert(PeekMessageW(&msg,nullptr,WM_MOUSEMOVE,WM_MOUSEMOVE,PM_REMOVE)&&msg.message==WM_NULL);
    PostThreadMessageW(GetCurrentThreadId(),WM_KEYDOWN,'H',0);assert(PeekMessageW(&msg,nullptr,WM_KEYDOWN,WM_KEYDOWN,PM_REMOVE)&&msg.message==WM_KEYDOWN&&msg.wParam=='H');
    PostThreadMessageW(GetCurrentThreadId(),WM_KEYDOWN,VK_ESCAPE,0);assert(PeekMessageW(&msg,nullptr,WM_KEYDOWN,WM_KEYDOWN,PM_REMOVE)&&msg.message==WM_KEYDOWN&&msg.wParam==VK_ESCAPE);
    PostThreadMessageW(GetCurrentThreadId(),WM_RBUTTONDOWN,MK_RBUTTON,123);assert(PeekMessageW(&msg,nullptr,WM_RBUTTONDOWN,WM_RBUTTONDOWN,PM_REMOVE)&&msg.message==WM_RBUTTONDOWN&&msg.wParam==MK_RBUTTON);
    admit=false;PostThreadMessageW(GetCurrentThreadId(),WM_MOUSEMOVE,0,123);assert(PeekMessageW(&msg,nullptr,WM_MOUSEMOVE,WM_MOUSEMOVE,PM_REMOVE)&&msg.message==WM_MOUSEMOVE);
    assert(filter.stop()&&filter.restored&&!filter.enabled);
    std::cout<<"PASS: real MinHook input start/stop, message-pump filtering and byte restoration, scope exclusion, raw filtering preserves movement/fire\n";
}
