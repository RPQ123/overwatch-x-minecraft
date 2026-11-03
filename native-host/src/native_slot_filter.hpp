#pragma once
#include <windows.h>
#include <atomic>
#include <array>
#include <vector>
#include <cstring>
#include <type_traits>
#include <cstddef>
#include "slot_input_policy.hpp"
namespace passthrough {
// Per-process input delivery, owned/restored by the existing compositor.
// No system-wide hooks and no second owner of a pre-existing MinHook target.
class NativeSlotFilter {
    using Toggle=int(WINAPI*)(void*);using Create=int(WINAPI*)(void*,void*,void**);
    struct Site{void* target;std::array<unsigned char,16> before;};
    std::vector<Site> sites;Toggle disable=nullptr;bool(*gate)()=nullptr;bool(*motionGate)()=nullptr;bool(*weaponSelectionGate)()=nullptr;
    inline static NativeSlotFilter* owner=nullptr;
    inline static decltype(&GetRawInputBuffer) bufferOriginal=nullptr;
    inline static decltype(&GetRawInputData) dataOriginal=nullptr;
    inline static decltype(&GetAsyncKeyState) asyncOriginal=nullptr;
    inline static decltype(&GetKeyState) keyOriginal=nullptr;
    inline static decltype(&GetKeyboardState) keyboardOriginal=nullptr;
    inline static decltype(&PeekMessageW) peekWOriginal=nullptr;
    inline static decltype(&PeekMessageA) peekAOriginal=nullptr;
    inline static decltype(&GetMessageW) messageWOriginal=nullptr;
    inline static decltype(&GetMessageA) messageAOriginal=nullptr;
    template<class T> static T proc(HMODULE library,const char* name){union {FARPROC raw;T fn;} x{GetProcAddress(library,name)};return x.fn;}
    static bool scoped(){return owner&&owner->enabled&&owner->gate&&owner->gate();}
    static bool motionScoped(){return owner&&owner->motionGate&&owner->motionGate();}
    static UINT WINAPI bufferHook(PRAWINPUT out,PUINT size,UINT header){
        UINT cap=size?*size:0,result=bufferOriginal(out,size,header);if(owner)owner->bufferCalls++;
        if(out&&result!=UINT(-1)&&result<=1024&&cap<=1024*1024&&header==sizeof(RAWINPUTHEADER)&&scoped()){
            size_t at=0;for(UINT i=0;i<result;i++){
                if(at+sizeof(RAWINPUTHEADER)>cap)break;
                auto r=reinterpret_cast<RAWINPUT*>(reinterpret_cast<unsigned char*>(out)+at);
                if(r->header.dwSize<sizeof(RAWINPUTHEADER)||r->header.dwSize>cap-at)break;
                if(r->header.dwSize>=offsetof(RAWINPUT,data)+sizeof(RAWKEYBOARD))owner->filter(*r,motionScoped());
                at+=(r->header.dwSize+sizeof(DWORD)-1)&~size_t(sizeof(DWORD)-1);
            }
        }return result;
    }
    static UINT WINAPI dataHook(HRAWINPUT input,UINT command,LPVOID out,PUINT size,UINT header){
        UINT result=dataOriginal(input,command,out,size,header);if(owner)owner->dataCalls++;
        if(out&&command==RID_INPUT&&result!=UINT(-1)&&result>=sizeof(RAWINPUTHEADER)&&header==sizeof(RAWINPUTHEADER)&&scoped()){
            auto r=static_cast<RAWINPUT*>(out);if(result>=offsetof(RAWINPUT,data)+sizeof(RAWKEYBOARD))owner->filter(*r,motionScoped());
        }return result;
    }
    static SHORT WINAPI asyncHook(int key){if(scoped()&&(owner->blocksSlotKey(unsigned(key))||key==VK_MBUTTON||(motionScoped()&&deadeyeMotionKey(unsigned(key))))){owner->keyQueries++;return 0;}return asyncOriginal(key);}
    static SHORT WINAPI keyHook(int key){if(scoped()&&(owner->blocksSlotKey(unsigned(key))||key==VK_MBUTTON||(motionScoped()&&deadeyeMotionKey(unsigned(key))))){owner->keyQueries++;return 0;}return keyOriginal(key);}
    static BOOL WINAPI keyboardHook(PBYTE keys){auto result=keyboardOriginal(keys);if(result&&keys&&scoped()){bool motion=motionScoped();for(unsigned i=0;i<256;i++)if(owner->blocksSlotKey(i)||i==VK_MBUTTON||(motion&&deadeyeMotionKey(i)))keys[i]=0;}return result;}
    static void messageFilter(MSG* msg,bool removed){
        if(!msg||!scoped())return;
        owner->messageCalls++;bool drop=false;bool motion=motionScoped();
        if(((msg->message==WM_KEYDOWN||msg->message==WM_KEYUP||msg->message==WM_SYSKEYDOWN||msg->message==WM_SYSKEYUP)&&owner->blocksSlotKey(unsigned(msg->wParam)))
           ||((msg->message==WM_CHAR||msg->message==WM_SYSCHAR)&&msg->wParam>='0'&&msg->wParam<='9'&&owner->blocksSlotKey(unsigned(msg->wParam)))){drop=true;owner->filteredKeys++;}
        if(weaponSlotMouse(msg->message)){drop=true;owner->filteredMouse++;}
        if(motion&&deadeyeMotionMessage(msg->message,unsigned(msg->wParam))){drop=true;if(msg->message==WM_MOUSEMOVE)owner->motionMouse++;else owner->motionKeys++;}
        if(msg->message==WM_INPUT&&removed){
            RAWINPUT raw{};UINT size=sizeof raw;
            if(dataOriginal(reinterpret_cast<HRAWINPUT>(msg->lParam),RID_INPUT,&raw,&size,sizeof(RAWINPUTHEADER))!=UINT(-1)&&size<=sizeof raw){
                drop=raw.header.dwType==RIM_TYPEKEYBOARD&&owner->blocksSlotKey(raw.data.keyboard.VKey);
                if(motion&&raw.header.dwType==RIM_TYPEKEYBOARD&&deadeyeMotionKey(raw.data.keyboard.VKey)&&!(raw.data.keyboard.Flags&RI_KEY_BREAK)){drop=true;owner->motionKeys++;}
                if(raw.header.dwType==RIM_TYPEMOUSE&&weaponSlotRaw(raw)&&!raw.data.mouse.lLastX&&!raw.data.mouse.lLastY&&!(raw.data.mouse.usButtonFlags&~(RI_MOUSE_WHEEL|RI_MOUSE_HWHEEL|RI_MOUSE_MIDDLE_BUTTON_DOWN|RI_MOUSE_MIDDLE_BUTTON_UP)))drop=true;
                if(motion&&raw.header.dwType==RIM_TYPEMOUSE&&!raw.data.mouse.usButtonFlags&&(raw.data.mouse.lLastX||raw.data.mouse.lLastY)){drop=true;owner->motionMouse++;}
                if(drop){if(raw.header.dwType==RIM_TYPEKEYBOARD)owner->filteredKeys++;else owner->filteredMouse++;}
            }
            if(drop&&GET_RAWINPUT_CODE_WPARAM(msg->wParam)==RIM_INPUT)DefWindowProcW(msg->hwnd,msg->message,msg->wParam,msg->lParam);
        }
        if(drop){msg->message=WM_NULL;msg->wParam=0;msg->lParam=0;}
    }
    static BOOL WINAPI peekW(MSG* msg,HWND w,UINT lo,UINT hi,UINT flags){auto result=peekWOriginal(msg,w,lo,hi,flags);if(result)messageFilter(msg,(flags&PM_REMOVE)!=0);return result;}
    static BOOL WINAPI peekA(MSG* msg,HWND w,UINT lo,UINT hi,UINT flags){auto result=peekAOriginal(msg,w,lo,hi,flags);if(result)messageFilter(msg,(flags&PM_REMOVE)!=0);return result;}
    static BOOL WINAPI messageW(MSG* msg,HWND w,UINT lo,UINT hi){auto result=messageWOriginal(msg,w,lo,hi);if(result>0)messageFilter(msg,true);return result;}
    static BOOL WINAPI messageA(MSG* msg,HWND w,UINT lo,UINT hi){auto result=messageAOriginal(msg,w,lo,hi);if(result>0)messageFilter(msg,true);return result;}
public:
    // integrator/builders: native top-row 1/2 only, with fresh Torbjorn/FPS proof.
    // Numpad, other heroes, wheel/middle and the Deadeye lock keep the old policy.
    bool blocksSlotKey(unsigned key) const {
        return weaponSlotKey(key)&&!((key=='1'||key=='2')&&scoped()&&!motionScoped()
            &&weaponSelectionGate&&weaponSelectionGate());
    }
    std::atomic<bool> enabled{false},restored{true};std::atomic<uint64_t> filteredKeys{0},filteredMouse{0},bufferCalls{0},dataCalls{0},keyQueries{0},messageCalls{0},motionKeys{0},motionMouse{0};
    bool filter(RAWINPUT& raw,bool motion=false){
        if(raw.header.dwType==RIM_TYPEKEYBOARD&&blocksSlotKey(raw.data.keyboard.VKey)){
            raw.data.keyboard.VKey=255;raw.data.keyboard.MakeCode=0;raw.data.keyboard.Message=WM_NULL;filteredKeys++;return true;
        }
        if(motion&&raw.header.dwType==RIM_TYPEKEYBOARD&&deadeyeMotionKey(raw.data.keyboard.VKey)&&!(raw.data.keyboard.Flags&RI_KEY_BREAK)){
            raw.data.keyboard.VKey=255;raw.data.keyboard.MakeCode=0;raw.data.keyboard.Message=WM_NULL;motionKeys++;return true;
        }
        if(raw.header.dwType==RIM_TYPEMOUSE){
            constexpr USHORT bits=RI_MOUSE_WHEEL|RI_MOUSE_HWHEEL|RI_MOUSE_MIDDLE_BUTTON_DOWN|RI_MOUSE_MIDDLE_BUTTON_UP;
            bool changed=false;
            if(raw.data.mouse.usButtonFlags&bits){raw.data.mouse.usButtonFlags&=~bits;raw.data.mouse.usButtonData=0;filteredMouse++;changed=true;}
            if(motion&&(raw.data.mouse.lLastX||raw.data.mouse.lLastY||(raw.data.mouse.usFlags&MOUSE_MOVE_ABSOLUTE))){
                raw.data.mouse.usFlags&=~(MOUSE_MOVE_ABSOLUTE|MOUSE_VIRTUAL_DESKTOP);raw.data.mouse.lLastX=raw.data.mouse.lLastY=0;motionMouse++;changed=true;
            }
            return changed;
        }return false;
    }
    bool start(bool(*admit)(),HMODULE library,bool(*lockMotion)()=nullptr,bool(*selectWeapon)()=nullptr){
        if(owner||!sites.empty()||!library)return false;
        gate=admit;motionGate=lockMotion;weaponSelectionGate=selectWeapon;
        auto initialize=proc<int(WINAPI*)()>(library,"MH_Initialize");auto create=proc<Create>(library,"MH_CreateHook");auto enable=proc<Toggle>(library,"MH_EnableHook");disable=proc<Toggle>(library,"MH_DisableHook");
        if(!initialize||!create||!enable||!disable)return false;
        int initialized=initialize();if(initialized!=0&&initialized!=1)return false;
        auto user=GetModuleHandleW(L"user32.dll");owner=this;
        auto bind=[&](const char* name,void* replacement,auto& original){
            auto target=reinterpret_cast<void*>(GetProcAddress(user,name));if(!target)return false;
            for(const auto& site:sites)if(site.target==target)return true;
            Site site{target,{}};std::memcpy(site.before.data(),target,site.before.size());void* trampoline=nullptr;
            // ALREADY_CREATED is refused, never adopted or chained.
            if(create(target,replacement,&trampoline)!=0||!trampoline)return false;
            union {void* p;std::remove_reference_t<decltype(original)> fn;} cast{trampoline};original=cast.fn;
            sites.push_back(site);restored=false;return enable(target)==0;
        };
        enabled=true;
        if(!bind("GetRawInputBuffer",reinterpret_cast<void*>(bufferHook),bufferOriginal)||!bind("GetRawInputData",reinterpret_cast<void*>(dataHook),dataOriginal)
           ||!bind("GetAsyncKeyState",reinterpret_cast<void*>(asyncHook),asyncOriginal)||!bind("GetKeyState",reinterpret_cast<void*>(keyHook),keyOriginal)
           ||!bind("GetKeyboardState",reinterpret_cast<void*>(keyboardHook),keyboardOriginal)
           ||!bind("PeekMessageW",reinterpret_cast<void*>(peekW),peekWOriginal)||!bind("PeekMessageA",reinterpret_cast<void*>(peekA),peekAOriginal)
           ||!bind("GetMessageW",reinterpret_cast<void*>(messageW),messageWOriginal)||!bind("GetMessageA",reinterpret_cast<void*>(messageA),messageAOriginal)){stop();return false;}
        return true;
    }
    bool stop(){
        enabled=false;bool ok=true;
        for(auto& site:sites){int result=disable?disable(site.target):-1;ok=(result==0||result==6)&&ok;ok=std::memcmp(site.target,site.before.data(),site.before.size())==0&&ok;}
        // Retain disabled trampolines until process exit for in-flight calls.
        // Never uninitialize the shared library or remove another owner's hook.
        restored=ok;return ok;
    }
};
}
