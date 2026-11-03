#include "../src/slot_input_policy.hpp"
#include <cassert>
int main(){
    using namespace passthrough;
    for(unsigned key='0';key<='9';key++)assert(weaponSlotKey(key));
    constexpr unsigned keys[]{'Q','E','H','W',VK_SPACE,VK_F1,VK_F9,VK_F11};
    for(unsigned key:keys)assert(!weaponSlotKey(key));
    RAWINPUT raw{};raw.header.dwType=RIM_TYPEKEYBOARD;raw.data.keyboard.VKey='2';assert(weaponSlotRaw(raw));raw.data.keyboard.VKey='Q';assert(!weaponSlotRaw(raw));
    raw={};raw.header.dwType=RIM_TYPEMOUSE;raw.data.mouse.usButtonFlags=RI_MOUSE_WHEEL;assert(weaponSlotRaw(raw));
    raw.data.mouse.usButtonFlags=RI_MOUSE_LEFT_BUTTON_DOWN;assert(!weaponSlotRaw(raw));raw.data.mouse.usButtonFlags=0;raw.data.mouse.lLastX=15;assert(!weaponSlotRaw(raw));
    constexpr unsigned movementKeys[]{'W','A','S','D',VK_SPACE,VK_CONTROL,VK_LCONTROL,VK_RCONTROL,VK_F6,VK_SHIFT,VK_LSHIFT,VK_RSHIFT};for(unsigned key:movementKeys){assert(deadeyeMotionKey(key));assert(deadeyeMotionMessage(WM_KEYDOWN,key));assert(!deadeyeMotionMessage(WM_KEYUP,key));}
    constexpr unsigned allowedKeys[]{'Q','E','H','V',VK_ESCAPE,VK_F1,VK_RBUTTON,VK_LBUTTON};for(unsigned key:allowedKeys)assert(!deadeyeMotionKey(key));
    assert(deadeyeMotionMessage(WM_MOUSEMOVE,0));assert(deadeyeMotionMessage(WM_KEYDOWN,'W'));
    assert(!deadeyeMotionMessage(WM_KEYUP,'W')&&!deadeyeMotionMessage(WM_LBUTTONDOWN,0)&&!deadeyeMotionMessage(WM_RBUTTONDOWN,0));
}
