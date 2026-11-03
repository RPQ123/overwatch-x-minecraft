#pragma once
#include "scene_projection.hpp"
#include "world_frame.hpp"
#include <string>

namespace passthrough {
struct HostPose {
    uint64_t frame=0,generation=0,wallMs=0;
    uint32_t pid=0,width=0,height=0,flags=1;
    uint32_t movementBits=0,inputActive=0; // W/S/A/D/jump/sneak/flight/melee/portals.
    uint32_t inputCapabilities=0; // Optional DEY1: existing owner supports confirmed-fire motion filtering.
    float fov=0,fx=0,fy=0;
    std::array<float,9> basis{}; // Camera-to-MC-world columns: right, up, backward.
    std::array<float,3> eye{};
    NativeProjection native{};
};
inline bool poseFromScene(const std::array<float,136>& values,UINT width,UINT height,uint64_t frame,HostPose& out) {
    NativeProjection p{};if(!decodeSceneProjection(values,float(width),float(height),p)) return false;
    HostPose candidate;candidate.frame=frame;candidate.width=width;candidate.height=height;candidate.native=p;
    candidate.fx=-p.viewToClip[0];candidate.fy=p.viewToClip[5];candidate.fov=2*std::atan(1/candidate.fy)*180/3.141592653589793f;
    for(int i=0;i<3;i++) {candidate.basis[i]=-p.worldToView[i*4];candidate.basis[3+i]=p.worldToView[i*4+1];candidate.basis[6+i]=-p.worldToView[i*4+2];candidate.eye[i]=values[44+i];}
    for(int column=0;column<3;column++) {
        float length=0;for(int i=0;i<3;i++) length+=candidate.basis[column*3+i]*candidate.basis[column*3+i];
        if(std::abs(length-1)>.01f) return false;
        for(int other=0;other<column;other++) {float dot=0;for(int i=0;i<3;i++) dot+=candidate.basis[column*3+i]*candidate.basis[other*3+i];if(std::abs(dot)>.01f) return false;}
    }
    if(candidate.fov<20||candidate.fov>140||!frame) return false;
    out=candidate;return true;
}
class PosePublisher {
    HANDLE handle=nullptr;unsigned char* memory=nullptr;uint64_t generation=0,publications=0;
public:
    explicit PosePublisher(const wchar_t* name=L"Local\\OWMCHostPose") {
        if(std::wstring(name)!=L"Local\\OWMCHostPose"&&std::wstring(name)!=L"Local\\OWMCHostPoseTest") throw std::runtime_error("Pose mapping name");
        handle=CreateFileMappingW(INVALID_HANDLE_VALUE,nullptr,PAGE_READWRITE,0,4096,name);if(!handle) throw std::runtime_error("Pose mapping creation");
        memory=static_cast<unsigned char*>(MapViewOfFile(handle,FILE_MAP_ALL_ACCESS,0,0,4096));if(!memory) {CloseHandle(handle);handle=nullptr;throw std::runtime_error("Pose mapping view");}
        if(std::memcmp(memory,"OWPOSE01",8)==0&&field<uint32_t>(memory,32)) {
            DWORD prior=field<uint32_t>(memory,16);HANDLE process=OpenProcess(SYNCHRONIZE|PROCESS_QUERY_LIMITED_INFORMATION,FALSE,prior);
            bool occupied=process?WaitForSingleObject(process,0)!=WAIT_OBJECT_0:GetLastError()!=ERROR_INVALID_PARAMETER;
            if(process) CloseHandle(process);
            if(occupied) {UnmapViewOfFile(memory);CloseHandle(handle);memory=nullptr;handle=nullptr;throw std::runtime_error("A live/unknown host pose producer exists");}
        } else if(std::memcmp(memory,"OWPOSE01",8)!=0&&field<uint64_t>(memory,0)) {UnmapViewOfFile(memory);CloseHandle(handle);memory=nullptr;handle=nullptr;throw std::runtime_error("Pose identity conflict");}
        LARGE_INTEGER counter{};QueryPerformanceCounter(&counter);generation=(uint64_t(counter.QuadPart)^(uint64_t(GetCurrentProcessId())<<32)^unixMillis())|1;
        std::memset(memory,0,4096);std::memcpy(memory,"OWPOSE01",8);put(8,uint32_t(1));put(12,uint32_t(4096));put(16,uint32_t(GetCurrentProcessId()));put(24,generation);put(32,uint32_t(1));put(36,int32_t(-1));put(40,uint32_t(64));
    }
    ~PosePublisher() {if(memory) {InterlockedExchange(reinterpret_cast<volatile LONG*>(memory+32),0);InterlockedExchange64(reinterpret_cast<volatile LONG64*>(memory+64),0);UnmapViewOfFile(memory);}if(handle) CloseHandle(handle);}
    PosePublisher(const PosePublisher&)=delete;PosePublisher& operator=(const PosePublisher&)=delete;
    template<class T> void put(size_t offset,T value) {std::memcpy(memory+offset,&value,sizeof value);}
    uint64_t session() const {return generation;}
    void publish(const HostPose& pose) {
        if(!pose.frame||!pose.width||!pose.height) throw std::runtime_error("Empty pose");
        InterlockedExchange64(reinterpret_cast<volatile LONG64*>(memory+64),LONG64((publications+1)*2-1));
        auto wall=pose.wallMs?pose.wallMs:unixMillis();
        put(72,pose.frame);put(80,wall);put(88,pose.flags);put(92,pose.width);put(96,pose.height);put(104,pose.fov);put(108,pose.fx);put(112,pose.fy);
        std::memcpy(memory+128,pose.basis.data(),36);std::memcpy(memory+168,pose.eye.data(),12);std::memcpy(memory+192,pose.native.worldToView,64);std::memcpy(memory+256,pose.native.viewToClip,64);
        put(320,uint32_t(2));put(324,pose.movementBits);put(328,pose.inputActive);
        put(332,pose.inputCapabilities);
        size_t slot=publications%64,offset=512+slot*56;put(offset,pose.frame);put(offset+8,wall);std::memcpy(memory+offset+16,pose.basis.data(),36);put(offset+52,pose.flags);put(36,int32_t(slot));
        InterlockedExchange64(reinterpret_cast<volatile LONG64*>(memory+64),LONG64(++publications*2));
    }
};
}
