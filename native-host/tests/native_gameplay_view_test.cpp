#include "../src/native_gameplay_view.hpp"
#include <unordered_map>
#include <cassert>
#include <cstring>
#include <iostream>
using namespace passthrough;
int main(){
    std::unordered_map<uintptr_t,unsigned char> data;
    auto put=[&](uintptr_t at,auto value){auto bytes=reinterpret_cast<unsigned char*>(&value);for(size_t i=0;i<sizeof value;i++)data[at+i]=bytes[i];};
    auto read=[&](uintptr_t at,void* out,size_t size){auto bytes=static_cast<unsigned char*>(out);for(size_t i=0;i<size;i++){auto found=data.find(at+i);if(found==data.end())return false;bytes[i]=found->second;}return true;};
    uintptr_t base=0x10000000,admin=0x20000,iter=0x30000,list=iter+0x4f*24;
    put(admin+0xb0,iter);put(list,uintptr_t(0x40000));put(list+8,int(1));put(list+12,int(1));put(0x40000,uintptr_t(0x50000));
    put(0x50040,uintptr_t(0x60000));put(0x50050,uintptr_t(0x70000));put(0x60260,uintptr_t(0x70000));put(0x70000,base+0x15c7000);
    assert(nativeGameplayView(base,admin,read));
    put(0x60260,uintptr_t(0x80000));assert(!nativeGameplayView(base,admin,read));
    put(0x60260,uintptr_t(0x70000));put(0x70000,base+0x15c7008);assert(!nativeGameplayView(base,admin,read));
    put(list+8,int(257));assert(!nativeGameplayView(base,admin,read));
    std::cout<<"PASS: original gameplay camera, picker/other-state hold, type and list bounds.\n";
}
