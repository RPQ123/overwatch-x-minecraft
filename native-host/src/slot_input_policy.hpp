#pragma once
#include <windows.h>
namespace passthrough {
inline bool weaponSlotKey(unsigned key){return (key>='0'&&key<='9')||(key>=VK_NUMPAD0&&key<=VK_NUMPAD9);}
inline bool weaponSlotMouse(unsigned message){return message==WM_MOUSEWHEEL||message==WM_MOUSEHWHEEL||message==WM_MBUTTONDOWN||message==WM_MBUTTONUP;}
inline bool deadeyeMotionKey(unsigned key,unsigned flightKey=VK_F6){return key=='W'||key=='S'||key=='A'||key=='D'||key==VK_SPACE||key==VK_CONTROL||key==VK_LCONTROL||key==VK_RCONTROL||key==flightKey||key==VK_SHIFT||key==VK_LSHIFT||key==VK_RSHIFT;}
inline bool deadeyeMotionMessage(unsigned message,unsigned key,unsigned flightKey=VK_F6){
    // Always allow releases to drain a key pressed before the lock. Menus,
    // cancellation, hero selection, primary fire and RMB remain untouched.
    return message==WM_MOUSEMOVE||((message==WM_KEYDOWN||message==WM_SYSKEYDOWN)&&deadeyeMotionKey(key,flightKey));
}
inline bool weaponSlotRaw(const RAWINPUT& raw){
    if(raw.header.dwType==RIM_TYPEKEYBOARD)return weaponSlotKey(raw.data.keyboard.VKey);
    return raw.header.dwType==RIM_TYPEMOUSE&&(raw.data.mouse.usButtonFlags&(RI_MOUSE_WHEEL|RI_MOUSE_HWHEEL|RI_MOUSE_MIDDLE_BUTTON_DOWN|RI_MOUSE_MIDDLE_BUTTON_UP));
}
}
