#pragma once
#include <windows.h>
#include <chrono>
#include <stdexcept>

namespace passthrough {
// Per-thread timer; no process/global timer-resolution side effects, busy spin,
// or accumulated catch-up frames after a long GPU stall.
class PreciseWait {
    HANDLE timer=CreateWaitableTimerExW(nullptr,nullptr,0x00000002,TIMER_ALL_ACCESS);
public:
    PreciseWait() {if(!timer)throw std::runtime_error("High-resolution frame timer unavailable");}
    ~PreciseWait() {if(timer)CloseHandle(timer);}
    PreciseWait(const PreciseWait&)=delete;
    PreciseWait& operator=(const PreciseWait&)=delete;
    bool wait(std::chrono::nanoseconds duration,HANDLE stop=nullptr) {
        if(duration.count()<=0)return stop&&WaitForSingleObject(stop,0)==WAIT_OBJECT_0;
        LARGE_INTEGER due{};due.QuadPart=-((duration.count()+99)/100);
        if(!SetWaitableTimerEx(timer,&due,0,nullptr,nullptr,nullptr,0))throw std::runtime_error("Frame timer arm failed");
        HANDLE objects[]{stop,timer};
        DWORD result=stop?WaitForMultipleObjects(2,objects,FALSE,1000):WaitForSingleObject(timer,1000);
        if(result==WAIT_FAILED||result==WAIT_TIMEOUT)throw std::runtime_error("Frame timer wait failed");
        return stop&&result==WAIT_OBJECT_0;
    }
};
}
