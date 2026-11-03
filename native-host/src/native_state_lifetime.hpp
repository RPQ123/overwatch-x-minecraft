#pragma once
#include <array>
#include <cstdint>
#include <cstring>

namespace passthrough {
// Private, single-node research command. Ordinary startup never writes it.
struct NativeLifetimeRequest {
    char magic[8];uint32_t version,pid;
    uint64_t creation,sequence,wall,hostGeneration,world,admin,modelId,hero,script,graph,definition,state,logger,nativeTick;
    uint32_t node,stateIndex,callbackThread,reserved;
};
static_assert(sizeof(NativeLifetimeRequest)==144);
struct NativeLifetimeContext {uint32_t pid,thread;uint64_t creation,admin,modelId,model,hero,generation,world,now,base,logger;};
template<class Read> bool lifetimeActive(uintptr_t logger,uintptr_t script,uint64_t expectedTick,Read read){
    auto find=[&](uintptr_t map,uint64_t wanted,bool wide,uintptr_t& value){
        std::array<uint64_t,2> h{},again{};std::array<unsigned char,40> raw{};
        if(!read(map,h)||h[1]>4096||!read(h[0],raw)||raw[25]!=1)return false;
        uintptr_t at=0,parent=h[0];std::memcpy(&at,raw.data()+8,8);value=0;
        for(unsigned depth=0;at!=h[0];depth++){
            uintptr_t owner=0;uint64_t key=0;
            if(depth>=64||!read(at,raw)||raw[25])return false;
            std::memcpy(&owner,raw.data()+8,8);if(owner!=parent)return false;
            std::memcpy(&key,raw.data()+32,wide?8:4);
            if(key==wanted){value=at+40;break;}
            parent=at;std::memcpy(&at,raw.data()+(wanted<key?0:16),8);
        }
        return read(map,again)&&h==again;
    };
    uintptr_t inner=0,row=0;std::array<unsigned char,9> a{},b{};uint64_t tick=0;
    if(!find(logger,script,true,inner)||!inner||!find(inner,2,false,row)||!row||!read(row,a)||!read(row,b)||a!=b||a[8]!=0)return false;
    std::memcpy(&tick,a.data(),8);return tick>0&&tick==expectedTick;
}
template<class Read> bool nativeLifetimeOwner(const NativeLifetimeRequest& r,const NativeLifetimeContext& c,Read read){
    auto q=[&](uintptr_t at){uint64_t value=0;read(at,value);return value;};
    auto array=[&](uintptr_t at,uintptr_t& items,uint64_t& count){
        std::array<uint64_t,2> storage{},v{};
        if(!read(at,storage)||(storage[1]!=1&&storage[1]!=2)||!read(storage[0],v))return false;
        items=v[storage[1]==1?0:1];count=v[storage[1]==1?1:0];return items>=0x10000&&count<=4096;
    };
    uint64_t resource=0;uint32_t index=0,flags=0;uintptr_t items=0;uint64_t count=0;
    if(std::memcmp(r.magic,"OWLIFE01",8)||r.version!=1||r.pid!=c.pid||r.creation!=c.creation||!r.sequence||!r.nativeTick||r.node!=2
       ||!r.callbackThread||r.callbackThread!=c.thread||r.reserved
       ||r.wall>c.now+50||c.now>r.wall+1500||r.hostGeneration!=c.generation||r.world!=c.world||r.admin!=c.admin||r.modelId!=c.modelId
       ||r.hero!=c.hero||c.hero!=0x02e0000000000002ULL||r.logger!=c.logger||!c.logger
       ||q(c.model+0x28)!=c.admin||q(q(q(r.script+0x10)+0x450)+8)!=c.model
       ||!read(r.script+0x150,resource)||resource!=0x0580000000000020ULL||q(r.script+0x160)!=r.graph
       ||q(r.state+0x78)!=r.script||!read(r.state+0x70,index)||index!=r.stateIndex||!read(r.state+0x40,flags)||!(flags&1)
       ||q(q(r.state)+0x110)!=c.base+0xd67920)return false;
    if(!array(r.graph+0x50,items,count)||count<=2||q(items+2*8)!=r.definition
       ||!array(r.graph+0x60,items,count)||r.stateIndex>=count||q(items+r.stateIndex*8)!=r.definition)return false;
    // Definitions and current runtime are both members of this exact script.
    struct List{uintptr_t items;int count,capacity;} states{};
    if(!read(r.script+0xa0,states)||states.count<1||states.count>states.capacity||states.capacity>4096)return false;
    bool found=false;for(int n=0;n<states.count;n++)if(q(states.items+n*8)==r.state)found=true;
    return found&&lifetimeActive(r.logger,r.script,r.nativeTick,read);
}
}
