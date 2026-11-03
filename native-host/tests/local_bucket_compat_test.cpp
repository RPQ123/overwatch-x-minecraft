#include "../src/local_bucket_compat.hpp"
#include <windows.h>
#include <array>
#include <cassert>
#include <iostream>
using namespace passthrough;
int main(){
    std::array<unsigned char,0x300> admin{},controller{},model{};std::array<unsigned char,65536> table{};
    std::array<uint64_t,4> controllers{},models{};
    auto put=[](void* p,size_t at,auto value){std::memcpy(static_cast<unsigned char*>(p)+at,&value,sizeof value);};
    NativeLocalHero h;h.localId=0x8000102a;h.modelId=h.localId+1;h.controller=reinterpret_cast<uintptr_t>(controller.data());h.model=reinterpret_cast<uintptr_t>(model.data());auto owner=reinterpret_cast<uintptr_t>(admin.data());
    put(admin.data(),0x10,reinterpret_cast<uintptr_t>(table.data()));put(admin.data(),0x220,h.localId);
    for(auto pair:{std::pair{controller.data(),h.localId},std::pair{model.data(),h.modelId}}){put(pair.first,0x94,pair.second);put(pair.first,0x28,owner);}
    auto reset=[&]{controllers={0x8000002a,0,h.localId,h.controller};models={0x8000002b,0,h.modelId,h.model};};reset();
    put(table.data(),(h.localId&4095u)*16,reinterpret_cast<uintptr_t>(controllers.data()));put(table.data(),(h.localId&4095u)*16+8,int(2));
    put(table.data(),(h.modelId&4095u)*16,reinterpret_cast<uintptr_t>(models.data()));put(table.data(),(h.modelId&4095u)*16+8,int(2));
    auto read=[](uintptr_t p,void* out,size_t size){SIZE_T done=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),out,size,&done)&&done==size;};
    int calls=0,fail=-1;
    auto write=[&](uintptr_t p,const void* in,size_t size){if(++calls==fail)return false;SIZE_T done=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(p),in,size,&done)&&done==size;};
    unsigned promoted=0;assert(localBucketCompatibility(owner,h,read,write,promoted)&&promoted==2);
    assert(controllers[0]==h.localId&&controllers[1]==h.controller&&controllers[2]==0x8000002a&&models[0]==h.modelId&&models[2]==0x8000002b);
    promoted=0;calls=0;assert(localBucketCompatibility(owner,h,read,write,promoted)&&promoted==0&&calls==0);
    reset();calls=0;fail=2;auto before=controllers;assert(!localBucketCompatibility(owner,h,read,write,promoted)&&controllers==before);
    reset();fail=-1;put(admin.data(),0x220,uint32_t(9));assert(!localBucketCompatibility(owner,h,read,write,promoted)&&controllers==before);
    std::cout<<"PASS: legacy local lookup sees collided IDs; all bucket records/counts retained, repeat is inert, failed write rolls back, stale owner refused.\n";
}
