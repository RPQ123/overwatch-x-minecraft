#pragma once
#include "guest_body.hpp"
#include <algorithm>

namespace passthrough {
struct NativeBlinkBinding {
    char magic[8];uint32_t version,pid;
    uint64_t creation,admin,localId,modelId,model,script,bag,graph,logger,first,second,definitionVtable;
};
static_assert(sizeof(NativeBlinkBinding)==112);

template<class Read> bool blinkStateTick(uintptr_t logger,uintptr_t script,Read read,uint64_t& tick){
    auto find=[&](uintptr_t map,uint64_t wanted,bool wide,uintptr_t& value){
        std::array<uint64_t,2> header{},again{};std::array<unsigned char,40> node{};
        if(!read(map,header)||header[1]>4096||!read(header[0],node)||node[25]!=1)return false;
        uintptr_t at=0;std::memcpy(&at,node.data()+8,8);uintptr_t parent=header[0];value=0;
        for(unsigned depth=0;at!=header[0];depth++){
            if(depth>=64||!read(at,node)||node[25])return false;
            uintptr_t owner=0;std::memcpy(&owner,node.data()+8,8);if(owner!=parent)return false;
            uint64_t key=0;std::memcpy(&key,node.data()+32,wide?8:4);
            if(key==wanted){value=at+40;break;}
            parent=at;std::memcpy(&at,node.data()+(wanted<key?0:16),8);
        }
        return read(map,again)&&header==again;
    };
    uintptr_t inner=0;if(!find(logger,script,true,inner))return false;
    tick=0;if(!inner)return true;
    for(unsigned index:{5u,10u}){
        uintptr_t row=0;if(!find(inner,index,false,row))return false;if(!row)continue;
        std::array<unsigned char,9> a{},b{};uint64_t value=0;
        if(!read(row,a)||!read(row,b)||a!=b||a[8]>1)return false;
        std::memcpy(&value,a.data(),8);if(value>INT64_MAX)return false;tick=std::max(tick,value);
    }
    return true;
}

template<class Read> bool blinkOwner(const NativeBlinkBinding& b,uintptr_t admin,uint32_t localId,uint32_t modelId,uintptr_t model,Read read){
    auto ptr=[&](uintptr_t at){uintptr_t value=0;read(at,value);return value;};
    uint64_t resource=0;uint32_t owner=0;
    if(std::memcmp(b.magic,"OWBLK001",8)||b.version!=1||b.admin!=admin||b.localId!=localId||b.modelId!=modelId||b.model!=model
       ||!read(admin+0x220,owner)||owner!=localId||ptr(model+0x28)!=admin||!read(model+0x94,owner)||owner!=modelId
       ||!read(b.script+0x150,resource)||resource!=0x0580000000000024ULL||ptr(b.script+0x98)!=b.bag||ptr(b.script+0x160)!=b.graph
       ||ptr(ptr(ptr(b.script+0x10)+0x450)+8)!=model||ptr(b.first)!=b.definitionVtable||ptr(b.second)!=b.definitionVtable)return false;
    uint64_t flag=0,count=0;auto storage=ptr(b.graph+0x50);
    if(!read(b.graph+0x58,flag)||(flag!=1&&flag!=2)||!read(storage+(flag==1?8:0),count)||count<11||count>4096)return false;
    auto items=ptr(storage+(flag==1?0:8));return ptr(items+5*8)==b.first&&ptr(items+10*8)==b.second;
}

struct NativeBlinkAccumulator {
    bool ready=false;uint64_t model=0,world=0,generation=0,lastTick=0,pending=0,pendingWall=0,consumed=0,captures=0;
    Vec3 previous{};std::array<double,3> total{};
    bool capture(const GuestBody& guest,uint32_t currentModel,uint64_t actionTick,uint64_t now,Vec3 position){
        if(!ready||model!=currentModel||world!=guest.worldId||generation!=guest.generation){
            ready=false;model=currentModel;world=guest.worldId;generation=guest.generation;lastTick=actionTick;pending=consumed=captures=0;total={};return false;
        }
        if(actionTick!=lastTick){lastTick=actionTick;pending=actionTick;pendingWall=now;}
        auto delta=position-previous;auto horizontal=delta.x*delta.x+delta.z*delta.z;
        // Original teleport measured7.48m. Admit only its fresh actual action,
        // not ordinary motion, a recall, an owner transition or an old logger row.
        if(!pending||pending==consumed||now<pendingWall||now-pendingWall>100||!std::isfinite(dot(delta,delta))
           ||horizontal<4||horizontal>64||std::abs(delta.y)>1)return false;
        total[0]+=delta.x;total[2]+=delta.z;consumed=pending;++captures;return true;
    }
    void applied(Vec3 position){previous=position;ready=true;}
};
}
