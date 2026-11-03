#include "../src/native_view_light.hpp"
#include "../src/view_light_scope.hpp"
#include <unordered_map>
#include <cassert>
#include <iostream>
using passthrough::NativeViewLight;
struct Fixture{
    uintptr_t base=0x10000000,engine=0x200000,frame=0x300000,light=0x400000;
    std::unordered_map<uintptr_t,unsigned char> bytes;
    std::array<float,3> original{-.15205436945f,-.68199837208f,-.71537232399f};
    template<class T> void put(uintptr_t at,const T& v){auto p=reinterpret_cast<const unsigned char*>(&v);for(size_t i=0;i<sizeof v;i++)bytes[at+i]=p[i];}
    bool read(uintptr_t at,void* data,size_t size){auto p=static_cast<unsigned char*>(data);for(size_t i=0;i<size;i++){auto it=bytes.find(at+i);if(it==bytes.end())return false;p[i]=it->second;}return true;}
    bool write(uintptr_t at,const void* data,size_t size){if(at!=light+0x40||size!=12)return false;auto p=static_cast<const unsigned char*>(data);for(size_t i=0;i<size;i++)bytes[at+i]=p[i];return true;}
    Fixture(){
        put(base+0x181e3e0,engine);put(engine,base+0x1589e58);put(engine+0x78,frame+0x41540);
        for(size_t i=0;i<0x800;i++)bytes[frame+0x41540-0x13f00+i]=0;
        put(frame+0x2da10,original);put(frame+0x2da40,light);put(light,base+0x158adb8);
        put(light+0x40,original);put(light+0x28,std::array<float,3>{3.83501410484f,3.09922385216f,2.01314473152f});
        put(light+0x34,std::array<float,3>{3.44524264336f,2.41263008118f,1.15125095844f});
    }
};
int main(){
    passthrough::ViewLightScope scope;
    passthrough::ViewLightIdentity first{41,100,200,300,400};
    assert(scope.transition(first,10));auto epoch=scope.epoch;
    assert(!scope.accepts(epoch,1000,1000,10));
    assert(scope.accepts(epoch,1000,1001,11));
    assert(!scope.transition(first,12));
    auto next=first;next.model++;
    assert(scope.transition(next,12));assert(!scope.accepts(epoch,1000,1001,13));
    assert(!scope.accepts(scope.epoch,1000,1251,13));
    assert(!scope.accepts(scope.epoch,1001,1000,13));
    next.world++;assert(scope.transition(next,13));assert(!scope.accepts(scope.epoch,1000,1001,13));
    next.source++;assert(scope.transition(next,14));
    assert(scope.transition({},15));assert(!scope.accepts(scope.epoch,1000,1000,16));
    Fixture f;auto r=[&](uintptr_t at,void* p,size_t n){return f.read(at,p,n);};auto w=[&](uintptr_t at,const void* p,size_t n){return f.write(at,p,n);};
    NativeViewLight light;assert(light.acquire(f.base,r));auto original=f.bytes;
    // A full yaw/pitch sweep has a constant light direction in camera space.
    for(float yaw:{0.f,1.57f,3.14f,-1.57f})for(float pitch:{-.9f,0.f,.9f}){
        const float s=std::sin(yaw),c=std::cos(yaw),sp=std::sin(pitch),cp=std::cos(pitch);
        std::array<float,9> basis{c,0,s,-s*sp,cp,c*sp,-s*cp,-sp,c*cp};
        assert(light.update(f.base,basis,r,w));std::array<float,3> direction{};assert(r(f.light+0x40,direction.data(),12));
        for(int axis=0;axis<3;axis++){float d=0;for(int j=0;j<3;j++)d+=basis[axis*3+j]*direction[j];assert(std::abs(d-(axis==1?-1.f:0.f))<.00001f);}
    }
    assert(light.owned&&!light.restored&&light.updates==12);assert(light.release(f.base,r,w));assert(f.bytes==original&&light.restored&&!light.owned);
    assert(light.acquire(f.base,r));f.put(f.engine+0x78,uintptr_t(0));
    assert(light.update(f.base,{1,0,0,0,1,0,0,0,1},r,w));assert(light.release(f.base,r,w));f.put(f.engine+0x78,f.frame+0x41540);
    auto sampled=NativeViewLight::locate(f.base,r);assert(sampled==f.light);f.put(f.engine+0x78,uintptr_t(0));
    assert(light.acquireCandidate(f.base,sampled,r));assert(light.release(f.base,r,w));f.put(f.engine+0x78,f.frame+0x41540);
    assert(!light.acquireCandidate(f.base,f.light+16,r));
    assert(light.acquire(f.base,r));auto changed=std::array<float,3>{1,0,0};f.put(f.light+0x40,changed);
    assert(!light.update(f.base,{1,0,0,0,1,0,0,0,1},r,w));assert(!light.release(f.base,r,w));
    f.put(f.light+0x40,f.original);assert(light.release(f.base,r,w));
    f.put(f.frame+0x2da40,uintptr_t(0));assert(!light.acquire(f.base,r));f.put(f.frame+0x2da40,f.light);
    // Real cold starts moved this arena binding by32bytes. Both are located
    // from the active packet; an unverified second light refuses ambiguity.
    f.put(f.frame+0x2da40,uintptr_t(0));f.put(f.frame+0x2da30,f.original);f.put(f.frame+0x2da60,f.light);
    assert(light.acquire(f.base,r));assert(light.release(f.base,r,w));
    f.put(f.engine,f.base+0x1589e59);assert(!light.acquire(f.base,r));f.put(f.engine,f.base+0x1589e58);
    assert(light.acquire(f.base,r));assert(!light.update(f.base,{1,0,0,0,2,0,0,0,1},r,w));assert(light.release(f.base,r,w));
    // Hollywood uses its separately measured neutral-daylight environment;
    // neither map profile may claim the other scene's similarly typed object.
    f.put(f.light+0x40,std::array<float,3>{.131760418415f,-.838670432568f,-.528461098671f});
    f.put(f.light+0x28,std::array<float,3>{3.277166604996f,3.277166604996f,3.277166604996f});
    f.put(f.light+0x34,std::array<float,3>{3.003441095352f,2.672940969467f,2.079642295837f});
    assert(!light.acquireCandidate(f.base,f.light,r));
    assert(!light.acquireCandidate(f.base,f.light,r,0x0800000000000223ULL));
    assert(light.acquireCandidate(f.base,f.light,r,0x08000000000002afULL));
    auto hollywood=f.bytes;
    for(float yaw:{0.f,.7854f,1.57f,2.356f,3.14f,-2.356f,-1.57f,-.7854f})for(float pitch:{-1.4835f,-.7854f,0.f,.7854f,1.4835f}){
        const float s=std::sin(yaw),c=std::cos(yaw),sp=std::sin(pitch),cp=std::cos(pitch);
        std::array<float,9> basis{c,0,s,-s*sp,cp,c*sp,-s*cp,-sp,c*cp};
        assert(light.update(f.base,basis,r,w));std::array<float,3> direction{};assert(r(f.light+0x40,direction.data(),12));
        for(int axis=0;axis<3;axis++){float dot=0;for(int j=0;j<3;j++)dot+=basis[axis*3+j]*direction[j];assert(std::abs(dot-(axis==1?-1.f:0.f))<.00001f);}
    }
    assert(light.release(f.base,r,w));assert(f.bytes==hollywood);
    NativeViewLight key(NativeViewLight::Rig::CameraKey);
    assert(key.acquireCandidate(f.base,f.light,r,0x08000000000002afULL));
    for(float yaw:{0.f,.7854f,1.57f,2.356f,3.14f,-2.356f,-1.57f,-.7854f})for(float pitch:{-1.4835f,-.7854f,0.f,.7854f,1.4835f}){
        const float s=std::sin(yaw),c=std::cos(yaw),sp=std::sin(pitch),cp=std::cos(pitch);
        std::array<float,9> basis{c,0,s,-s*sp,cp,c*sp,-s*cp,-sp,c*cp};
        assert(key.update(f.base,basis,r,w));std::array<float,3> direction{};assert(r(f.light+0x40,direction.data(),12));
        const auto expected=NativeViewLight::coefficients(NativeViewLight::Rig::CameraKey);
        for(int axis=0;axis<3;axis++){float dot=0;for(int j=0;j<3;j++)dot+=basis[axis*3+j]*direction[j];assert(std::abs(dot-expected[axis])<.00001f);}
    }
    assert(!key.update(f.base,{1,0,0,0,1,0,1,0,0},r,w));
    assert(key.release(f.base,r,w));assert(f.bytes==hollywood);
    std::cout<<"Native camera-relative light: yaw/pitch invariance, exact12-byte writes, restoration and binding guards passed\n";
}
