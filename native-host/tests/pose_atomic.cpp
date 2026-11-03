#include <windows.h>
#include <cstdint>
// Loaded only in the synthetic Python fixture process, never in a game.
// InterlockedExchange64 is a compiler intrinsic rather than a kernel32 export.
extern "C" __declspec(dllexport) LONG64 WINAPI OWMCPoseExchange64(volatile LONG64* address,LONG64 value) {
    if(!address||(reinterpret_cast<uintptr_t>(address)&7)) return -1;
    return InterlockedExchange64(address,value);
}
