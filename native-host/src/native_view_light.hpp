#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <cmath>
#include <cstring>

namespace passthrough {
// Only the owned beta's calibrated Kyoto/Hollywood environments. The existing render owner calls this
// once per frame; no camera, hero, movement, shader or callback pointer changes.
class NativeViewLight {
public:
    enum class Rig {Overhead,CameraKey};
    static std::array<float,3> coefficients(Rig rig){return rig==Rig::CameraKey?std::array<float,3>{.5f,-.707106781187f,-.5f}:std::array<float,3>{0,-1,0};}
private:
    uintptr_t environment=0;
    std::array<float,3> original{},expected{};
    std::array<float,6> colors{};
    Rig rig;
    static bool unit(const std::array<float,3>& v){
        float n=0;for(float f:v){if(!std::isfinite(f))return false;n+=f*f;}
        return std::abs(n-1)<.001f;
    }
public:
    explicit NativeViewLight(Rig value=Rig::Overhead):rig(value){}
    std::atomic<bool> owned{false},restored{true};
    std::atomic<uint64_t> updates{0};
    bool bound() const{return environment!=0;}
    uintptr_t boundAddress() const{return environment;}
    template<class Read> static uintptr_t locate(uintptr_t base,Read read){
        auto ptr=[&](uintptr_t at){uintptr_t v=0;read(at,&v,8);return v;};
        auto engine=ptr(base+0x181e3e0);
        if(ptr(engine)!=base+0x1589e58)return 0;
        auto matrices=ptr(engine+0x78);if(matrices<0x23f00)return 0;
        // The frame arena's allocations move between cold starts. Search only
        // the calibrated 2KiB sun-binding neighborhood of the active matrix
        // packet, verifying its unit direction and exact environment class.
        // Never derive an object from the arena's allocation-base offset.
        std::array<unsigned char,0x800> packet{};
        if(!read(matrices-0x13f00,packet.data(),packet.size()))return 0;
        uintptr_t found=0;
        for(size_t i=48;i+8<=packet.size();i+=8){
            std::array<float,3> direction{};uintptr_t light=0;
            std::memcpy(direction.data(),packet.data()+i-48,12);
            if(!unit(direction))continue;
            std::memcpy(&light,packet.data()+i,8);
            if(light<0x10000||light>=0x7fffffffffffULL||(light&15)||ptr(light)!=base+0x158adb8)continue;
            if(found&&found!=light)return 0;
            found=light;
        }
        return found;
    }
    template<class Read> bool acquireCandidate(uintptr_t base,uintptr_t candidate,Read read,uint64_t map=0x0800000000000664ULL){
        if(environment)return false;
        std::array<float,3> direction{},rgb{},derived{};uintptr_t table=0;
        const std::array<float,3> kyotoDirection{-.15205436945f,-.68199837208f,-.71537232399f};
        const std::array<float,3> kyotoRgb{3.83501410484f,3.09922385216f,2.01314473152f};
        const std::array<float,3> kyotoDerived{3.44524264336f,2.41263008118f,1.15125095844f};
        const std::array<float,3> hollywoodDirection{.131760418415f,-.838670432568f,-.528461098671f};
        const std::array<float,3> hollywoodRgb{3.277166604996f,3.277166604996f,3.277166604996f};
        const std::array<float,3> hollywoodDerived{3.003441095352f,2.672940969467f,2.079642295837f};
        if(map!=0x0800000000000664ULL&&map!=0x08000000000002afULL)return false;
        if(candidate<0x10000||candidate>=0x7fffffffffffULL||(candidate&15)
            ||!read(candidate,&table,8)||table!=base+0x158adb8
            ||!read(candidate+0x40,direction.data(),12)||!unit(direction)
            ||!read(candidate+0x28,rgb.data(),12)||!read(candidate+0x34,derived.data(),12)
            ||direction!=(map==0x0800000000000664ULL?kyotoDirection:hollywoodDirection)
            ||rgb!=(map==0x0800000000000664ULL?kyotoRgb:hollywoodRgb)
            ||derived!=(map==0x0800000000000664ULL?kyotoDerived:hollywoodDerived))return false;
        environment=candidate;original=expected=direction;
        std::memcpy(colors.data(),rgb.data(),12);std::memcpy(colors.data()+3,derived.data(),12);return true;
    }
    template<class Read> bool acquire(uintptr_t base,Read read){return acquireCandidate(base,locate(base,read),read);}
    template<class Read,class Write> bool update(uintptr_t base,const std::array<float,9>& basis,Read read,Write write){
        std::array<float,3> up{},current{};const auto key=coefficients(rig);
        for(int axis=0;axis<3;axis++){
            if(!unit({basis[axis*3],basis[axis*3+1],basis[axis*3+2]}))return false;
            for(int other=0;other<axis;other++){
                float dot=0;for(int i=0;i<3;i++)dot+=basis[axis*3+i]*basis[other*3+i];
                if(std::abs(dot)>.001f)return false;
            }
            for(int i=0;i<3;i++)up[i]+=key[axis]*basis[axis*3+i];
        }
        uintptr_t table=0;std::array<float,6> currentColors{};
        // engine+78 is a transient command-packet pointer, often null during
        // Present. Keep the uniquely bound environment for this unchanged
        // native map, checking its exact class/colors/last owned bytes instead.
        if(!unit(up)||!environment||!read(environment,&table,8)||table!=base+0x158adb8
            ||!read(environment+0x28,currentColors.data(),24)||currentColors!=colors
            ||!read(environment+0x40,current.data(),12)||current!=expected)return false;
        float n=std::sqrt(up[0]*up[0]+up[1]*up[1]+up[2]*up[2]);for(auto& f:up)f/=n;
        // Remember our attempted bytes before write so an interrupted write can
        // be audited by the same render owner; never overwrite an external edit.
        expected=up;owned=true;restored=false;
        if(!write(environment+0x40,up.data(),12))return false;
        updates++;return true;
    }
    template<class Read,class Write> bool release(uintptr_t base,Read read,Write write){
        if(!environment)return true;
        std::array<float,3> current{};
        uintptr_t table=0;
        if(!read(environment,&table,8)||table!=base+0x158adb8
            ||!read(environment+0x40,current.data(),12))return false;
        if(current!=original&&(current!=expected||!write(environment+0x40,original.data(),12)))return false;
        restored=true;owned=false;environment=0;return true;
    }
};
}
