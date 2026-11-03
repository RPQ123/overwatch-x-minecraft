#pragma once
#include <windows.h>
#include <array>
#include <vector>
#include <cstring>
#include <cmath>
#include <cstdint>
#include <stdexcept>
#include <atomic>
#include <memory>

namespace passthrough {
constexpr size_t headerBytes=4096, slotStride=2560*1440*8, mappingBytes=headerBytes+3*slotStride;
template<class T> T field(const unsigned char* bytes,size_t offset) {T v;std::memcpy(&v,bytes+offset,sizeof v);return v;}
inline uint64_t unixMillis() {FILETIME ft;GetSystemTimeAsFileTime(&ft);ULARGE_INTEGER t{};t.LowPart=ft.dwLowDateTime;t.HighPart=ft.dwHighDateTime;return (t.QuadPart-116444736000000000ULL)/10000;}
struct WorldFrame {
    uint64_t sequence{},mcFrame{},hostFrame{},hostGeneration{},generation{},captureNs{},publishNs{},publishMs{};
    uint32_t width{},height{},sourcePid{};
    float nearPlane{},farPlane{},fov{};
    float bossHealth{},bossMaximum{};
    uint32_t hudWidth{},hudHeight{};
    std::vector<unsigned char> hudRgba;
    std::array<double,3> camera{};
    std::array<float,3> rotation{};
    std::array<float,16> projection{}; // Column-major, original MC OpenGL clip matrix.
    std::vector<unsigned char> rgba; // Owned, top-down RGBA8.
    std::vector<float> depth; // Owned, top-down GL window depth [0,1], not clip z.
};
inline void validateHeader(const unsigned char* h) {
    if(std::memcmp(h,"OWMCFR01",8)||field<uint32_t>(h,8)!=2||field<uint32_t>(h,12)!=headerBytes||
       field<uint32_t>(h,16)!=3||field<uint32_t>(h,20)!=2560||field<uint32_t>(h,24)!=1440||
       field<uint32_t>(h,28)!=0||field<uint64_t>(h,32)!=slotStride||!field<uint32_t>(h,52)||!field<uint64_t>(h,56))
        throw std::runtime_error("World frame identity/layout");
}
// Only decode into unpublished storage. A failed validation may modify it.
inline void decodeFrameInto(WorldFrame& f,const unsigned char* h,const unsigned char* d,const unsigned char* pixels,size_t size,uint64_t now) {
    validateHeader(h);
    f.sequence=field<uint64_t>(d,0);f.mcFrame=field<uint64_t>(d,8);f.hostFrame=field<uint64_t>(d,16);
    f.hostGeneration=field<uint64_t>(d,176);
    f.bossHealth=0;f.bossMaximum=0;
    if(field<uint32_t>(d,184)==0x31485342&&field<uint32_t>(d,196)==1){
        f.bossHealth=field<float>(d,188);f.bossMaximum=field<float>(d,192);
        if(!std::isfinite(f.bossHealth)||!std::isfinite(f.bossMaximum)||f.bossHealth<0||f.bossMaximum<=0||f.bossHealth>f.bossMaximum||f.bossMaximum>100000)
            throw std::runtime_error("Invalid boss health");
    }
    if((f.hostFrame==0)!=(f.hostGeneration==0)) throw std::runtime_error("Unpaired host frame/generation");
    f.width=field<uint32_t>(d,24);f.height=field<uint32_t>(d,28);
    f.nearPlane=field<float>(d,32);f.farPlane=field<float>(d,36);f.fov=field<float>(d,40);
    f.sourcePid=field<uint32_t>(h,52);f.generation=field<uint64_t>(h,56);
    f.captureNs=field<uint64_t>(d,88);f.publishNs=field<uint64_t>(d,96);f.publishMs=field<uint64_t>(d,104);
    if(!f.sequence||(f.sequence&1)||!f.mcFrame||!field<uint64_t>(h,40)||field<int32_t>(h,48)<0||field<int32_t>(h,48)>2)
          throw std::runtime_error("Incomplete world frame: seq="+std::to_string(f.sequence)+" frame="+std::to_string(f.mcFrame)+" publication="+std::to_string(field<uint64_t>(h,40))+" slot="+std::to_string(field<int32_t>(h,48)));
    auto format=field<uint32_t>(d,44);if(format!=1&&format!=2)throw std::runtime_error("World frame payload format");
    if(!f.width||!f.height||f.width>2560||f.height>1440||size!=size_t(f.width)*f.height*4*format)
        throw std::runtime_error("World frame dimensions/payload");
    if(field<uint32_t>(d,84)!=1||!std::isfinite(f.nearPlane)||!std::isfinite(f.farPlane)||
       !std::isfinite(f.fov)||f.nearPlane<=0||f.farPlane<=f.nearPlane||f.farPlane>100000||f.fov<=0||f.fov>=179||
       !f.captureNs||f.publishNs<f.captureNs) throw std::runtime_error("World frame planes/conventions");
    if((now>=f.publishMs&&now-f.publishMs>1000)||(f.publishMs>now&&f.publishMs-now>250)) throw std::runtime_error("Stale world frame");
    for(int i=0;i<3;i++) {f.camera[i]=field<double>(d,48+i*8);f.rotation[i]=field<float>(d,72+i*4);
        if(!std::isfinite(f.camera[i])||!std::isfinite(f.rotation[i])) throw std::runtime_error("Nonfinite camera");}
    for(int i=0;i<16;i++) {f.projection[i]=field<float>(d,112+i*4);if(!std::isfinite(f.projection[i])) throw std::runtime_error("Nonfinite projection");}
    size_t n=size_t(f.width)*f.height;f.rgba.resize(n*4);f.depth.resize(format==2?n:0);
    for(size_t y=0;y<f.height;y++) {
        size_t src=(f.height-1-y)*f.width,dst=y*f.width;
        std::memcpy(f.rgba.data()+dst*4,pixels+src*4,f.width*4);
        if(format==2)for(size_t x=0;x<f.width;x++) {float z=field<float>(pixels,n*4+(src+x)*4);
            if(!std::isfinite(z)||z<0||z>1) throw std::runtime_error("Invalid world depth");
            f.depth[dst+x]=z;}
    }
}
inline WorldFrame decodeFrame(const unsigned char* h,const unsigned char* d,const unsigned char* pixels,size_t size,uint64_t now) {
    WorldFrame f;decodeFrameInto(f,h,d,pixels,size,now);return f;
}
// Worker owns this pool. A render-thread snapshot prevents its slot being reused.
class WorldFramePool {
    std::array<std::shared_ptr<WorldFrame>,3> slots{};
public:
    std::shared_ptr<WorldFrame> acquire() {
        for(auto& slot:slots) {
            if(!slot)slot=std::make_shared<WorldFrame>();
            if(slot.use_count()==1)return slot;
        }
        return {}; // Bounded memory; never overwrite an outstanding snapshot.
    }
};
class WorldFrames {
    HANDLE handle=nullptr;
    const unsigned char* view=nullptr;
public:
    bool bodyPacket(std::array<unsigned char,256>& result) const {
        for(int i=0;i<3;i++){
            auto sequence=field<uint64_t>(view,1536+64);
            std::atomic_thread_fence(std::memory_order_seq_cst);
            std::memcpy(result.data(),view+1536,result.size());
            std::atomic_thread_fence(std::memory_order_seq_cst);
            if(sequence&&!(sequence&1)&&sequence==field<uint64_t>(result.data(),64)&&sequence==field<uint64_t>(view,1536+64))return true;
        }
        return false;
    }
    explicit WorldFrames(const wchar_t* name=L"Local\\OWMCPassthroughFrame") {
        handle=OpenFileMappingW(FILE_MAP_READ,FALSE,name);if(!handle) throw std::runtime_error("No MC frame producer");
        view=static_cast<const unsigned char*>(MapViewOfFile(handle,FILE_MAP_READ,0,0,mappingBytes));
        if(!view) {CloseHandle(handle);handle=nullptr;throw std::runtime_error("MC mapping view unavailable");}
    }
    ~WorldFrames() {if(view) UnmapViewOfFile(view);if(handle) CloseHandle(handle);}
    WorldFrames(const WorldFrames&)=delete;WorldFrames& operator=(const WorldFrames&)=delete;
    bool latest(WorldFrame& result,uint64_t knownGeneration=0,uint64_t knownSequence=0) {
        WorldFrame candidate;
        if(!latestInto(candidate,knownGeneration,knownSequence))return false;
        result=std::move(candidate);return true;
    }
    // Caller must own exclusive, unpublished storage; contents are undefined on failure.
    bool latestInto(WorldFrame& result,uint64_t knownGeneration=0,uint64_t knownSequence=0) {
        for(int attempt=0;attempt<4;attempt++) {
            std::array<unsigned char,headerBytes> h{};std::memcpy(h.data(),view,h.size());validateHeader(h.data());
            int slot=field<int32_t>(h.data(),48);if(slot<0||slot>2) return false;
            size_t offset=256+slot*256;std::array<unsigned char,256> d{};std::memcpy(d.data(),view+offset,d.size());
            // Materialize the local descriptor before validation; the producer
            // may change the mapping while the payload is being decoded.
            std::atomic_thread_fence(std::memory_order_seq_cst);
            uint64_t seq=field<uint64_t>(d.data(),0);if(!seq||(seq&1)) continue;
            if(seq==knownSequence&&field<uint64_t>(h.data(),56)==knownGeneration) return false;
            uint32_t w=field<uint32_t>(d.data(),24),ht=field<uint32_t>(d.data(),28);
            if(!w||!ht||w>2560||ht>1440) throw std::runtime_error("Unsafe frame dimensions");
            auto format=field<uint32_t>(d.data(),44);if(format!=1&&format!=2)throw std::runtime_error("Unsafe frame format");
            // Decode into the owned output while the slot is guarded by its
            // seqlock. A second full-size temporary copy adds avoidable latency.
            try {decodeFrameInto(result,h.data(),d.data(),view+headerBytes+slot*slotStride,size_t(w)*ht*4*format,unixMillis());
                result.hudWidth=0;result.hudHeight=0;result.hudRgba.clear();
                if(field<uint32_t>(d.data(),200)==0x31445548){
                    auto hw=field<uint32_t>(d.data(),204),hh=field<uint32_t>(d.data(),208);
                    if(format!=1||!hw||!hh||hw>1024||hh>192||hw>w||hh>ht)throw std::runtime_error("Invalid vanilla HUD dimensions");
                    result.hudWidth=hw;result.hudHeight=hh;result.hudRgba.resize(size_t(hw)*hh*4);
                    auto source=view+headerBytes+slot*slotStride+2560*1440*4;
                    for(size_t y=0;y<hh;y++)std::memcpy(result.hudRgba.data()+y*hw*4,source+(hh-1-y)*hw*4,hw*4);
                }
            }
            catch(const std::exception&) {
                std::atomic_thread_fence(std::memory_order_seq_cst);
                if(field<uint64_t>(view,offset)!=seq||field<uint64_t>(view,56)!=field<uint64_t>(h.data(),56))continue;
                throw;
            }
            std::atomic_thread_fence(std::memory_order_seq_cst);
            if(field<uint64_t>(view,offset)!=seq||field<uint64_t>(view,56)!=field<uint64_t>(h.data(),56)) continue;
            return true;
        }
        return false;
    }
};
}
