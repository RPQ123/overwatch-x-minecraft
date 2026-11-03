#include "../src/hero_camera_definition.hpp"
#include <cassert>
#include <iostream>
#include <limits>
using namespace passthrough;
int main(){
    std::array<unsigned char,8192> memory{};constexpr uintptr_t origin=0x10000;
    auto put=[&](uintptr_t at,const auto& v){assert(at>=origin&&at+sizeof v<=origin+memory.size());std::memcpy(memory.data()+at-origin,&v,sizeof v);};
    auto read=[&](uintptr_t at,void* out,size_t count){if(at<origin||at+count>origin+memory.size())return false;std::memcpy(out,memory.data()+at-origin,count);return true;};
    auto meta=[&](uintptr_t obj,uintptr_t vt,uintptr_t getter,uintptr_t info,uint32_t kind,int size){
        put(obj,vt);put(vt+0x28,getter);std::array<unsigned char,8> code{0x48,0x8d,0x05,0,0,0,0,0xc3};
        int32_t rel=int32_t(info-getter-7);std::memcpy(code.data()+3,&rel,4);put(getter,code);put(info+0x50,kind);put(info+0x5c,size);
    };
    uintptr_t model=0x10100,entry=0x10200,def=0x10300,head=0x10400,ends=0x10500,items=0x10600,fp=0x10700;
    put(model+0x30,entry);put(entry,def);meta(def,0x10800,0x10900,0x10a00,0xec23fffd,0x38);
    put(def+0x28,head);put(def+0x30,uint64_t(2));put(head,int(1));put(head+8,ends);put(head+16,items);put(ends,int(1));
    put(items,uint32_t(0xdaf7a654));put(items+8,fp);meta(fp,0x10b00,0x10c00,0x10d00,0xdaf7a654,40);
    put(0x10d28,uintptr_t(0x10e00));put(0x10d54,int(3));put(0x10e08,uint32_t(0x23b74fe6));put(0x10e0c,int(0x18));
    put(0x10ea8,uint32_t(0x9c200bc4));put(0x10eac,int(0x1c));put(fp+0x18,53.f);put(fp+0x1c,1.2f);
    HeroCameraDefinition c;assert(heroCameraDefinition(model,read,c));assert(c.fov==53&&c.eyeHeight==1.2f);
    for(float eye:{1.f,1.25f,1.35f,1.55f,1.82f}){put(fp+0x1c,eye);assert(heroCameraDefinition(model,read,c)&&c.eyeHeight==eye);}
    put(fp+0x18,70.f);assert(!heroCameraDefinition(model,read,c));put(fp+0x18,50.f);
    put(fp+0x1c,std::numeric_limits<float>::quiet_NaN());assert(!heroCameraDefinition(model,read,c));put(fp+0x1c,1.2f);
    put(0x10eac,int(0x20));assert(!heroCameraDefinition(model,read,c));put(0x10eac,int(0x1c));
    put(ends,int(2));put(items+16,uint32_t(0xdaf7a654));put(items+24,fp);assert(!heroCameraDefinition(model,read,c));
    std::cout<<"PASS: reflected hero camera, multiple original heights, wrong lens/type/layout/duplicate/NaN refusal\n";
}
