#pragma once
#include <windows.h>
#include <string>

namespace passthrough {
inline std::wstring startupInputEventName(){
    FILETIME created{},exited{},kernel{},user{};
    if(!GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user))return {};
    ULARGE_INTEGER stamp{};stamp.LowPart=created.dwLowDateTime;stamp.HighPart=created.dwHighDateTime;
    return L"Local\\OWMCStartupInput_"+std::to_wstring(GetCurrentProcessId())+L"_"+std::to_wstring(stamp.QuadPart);
}
inline bool startupInputEventExists(const std::wstring& name){
    if(name.empty())return false;
    auto event=OpenEventW(SYNCHRONIZE,FALSE,name.c_str());
    if(!event)return false;
    // Never hold a reference across samples; the OS drops the gate on owner exit.
    CloseHandle(event);
    return true;
}
}
