#pragma once
#include <array>
#include <cstdint>
#include <cmath>
#include <cstring>

namespace passthrough {
struct HeroCameraDefinition {float fov=0,eyeHeight=0;};
// Read the actual current model's reflected STUFirstPersonComponent. This does
// not grant combat authority and never executes a metadata/config getter.
template<class Read> bool heroCameraDefinition(uintptr_t model,Read read,HeroCameraDefinition& output){
    auto get=[&](uintptr_t p,auto& v){return read(p,&v,sizeof v);};
    auto ptr=[&](uintptr_t p){uintptr_t v=0;get(p,v);return v;};
    auto metadata=[&](uintptr_t object,uint32_t wanted,int minimum,uintptr_t& info){
        auto getter=ptr(ptr(object)+0x28);std::array<unsigned char,8> bytes{};
        if(!get(getter,bytes)||bytes[0]!=0x48||bytes[1]!=0x8d||bytes[2]!=0x05||bytes[7]!=0xc3)return false;
        int32_t relative=0;std::memcpy(&relative,bytes.data()+3,4);info=getter+7+relative;
        uint32_t type=0;int size=0;return get(info+0x50,type)&&type==wanted&&get(info+0x5c,size)&&size>=minimum&&size<=65536;
    };
    auto definition=ptr(ptr(model+0x30)&~uintptr_t(63));uintptr_t info=0;
    if(!metadata(definition,0xec23fffd,0x38,info))return false;
    uint64_t flag=0;if(!get(definition+0x30,flag)||flag!=2)return false;
    auto header=ptr(definition+0x28);int buckets=0,count=0;
    if(!get(header,buckets)||buckets<1||buckets>256||!get(ptr(header+8)+4*(buckets-1),count)||count<1||count>256)return false;
    auto items=ptr(header+16);uintptr_t firstPerson=0;
    for(int i=0;i<count;i++){uint32_t kind=0;if(!get(items+i*16,kind))return false;if(kind==0xdaf7a654){if(firstPerson)return false;firstPerson=ptr(items+i*16+8);}}
    if(!firstPerson||!metadata(firstPerson,0xdaf7a654,40,info))return false;
    auto arguments=ptr(info+0x28);int fields=0;if(!get(info+0x54,fields)||fields<3||fields>512)return false;
    bool fov=false,height=false;
    for(int i=0;i<fields;i++){
        uint32_t key=0;int offset=0;if(!get(arguments+i*0xa0+8,key)||!get(arguments+i*0xa0+12,offset))return false;
        if(key==0x23b74fe6&&offset==0x18)fov=true;
        if(key==0x9c200bc4&&offset==0x1c)height=true;
    }
    HeroCameraDefinition candidate;
    if(!fov||!height||!get(firstPerson+0x18,candidate.fov)||!get(firstPerson+0x1c,candidate.eyeHeight)
       ||!std::isfinite(candidate.fov)||candidate.fov<40||candidate.fov>67
       ||!std::isfinite(candidate.eyeHeight)||candidate.eyeHeight<.5f||candidate.eyeHeight>2.5f)return false;
    output=candidate;return true;
}
}
