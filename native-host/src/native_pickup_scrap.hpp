#pragma once
#include "native_deadeye_presentation.hpp"
#include "native_weapon_slots.hpp"
#include <algorithm>
namespace passthrough {
struct ScrapCreditRequest {
    char magic[8];uint32_t version,pid;
    uint64_t creation,sequence,wall,generation,world,model,modelId;
    uint32_t quantity,reserved;
};
static_assert(sizeof(ScrapCreditRequest)==80);
struct ScrapCreditAck {
    char magic[8]={'O','W','S','C','R','A','0','1'};uint32_t version=1,pid=0;
    uint64_t creation=0,sequence=0,wall=0,generation=0,world=0,modelId=0;
    uint32_t phase=0,before=0,after=0,credited=0;
};
static_assert(sizeof(ScrapCreditAck)==80);
/** Physical MC scrap is a sequenced receipt, not a test grant. Reuse the
 * already validated Set&Notify on the existing body logic owner. No second
 * callback, remote code call, or raw resource payload write. */
struct NativePickupScrap {
    ScrapCreditAck ack{};uint64_t highWater=0,rejectedSequence=0;
    std::atomic<uint64_t> credits{0},refused{0};
    template<class Read,class Notify> bool update(const ScrapCreditRequest* packet,const DeadeyePresentationContext& c,const NativeLocalHero& h,Read read,Notify notify){
        if(!packet)return false;
        auto& p=*packet;
        auto reject=[&](){if(rejectedSequence!=p.sequence){rejectedSequence=p.sequence;++refused;}return false;};
        if(std::memcmp(p.magic,"OWSCRP01",8)||p.version!=1||p.pid!=c.pid||p.creation!=c.creation||!p.sequence
           ||p.wall>c.now+50||c.now>p.wall+250||p.generation!=c.generation||!p.world||p.world!=c.world
           ||h.hero!=0x02e0000000000006ULL||p.model!=h.model||p.modelId!=h.modelId||p.quantity!=25||p.reserved)return reject();
        WeaponSlotReader<Read> r{c.base,read};auto admin=r.ptr(c.base+0x17b7f90);
        if(!r.owner(admin,h))return reject();
        if(p.sequence==ack.sequence&&p.generation==ack.generation&&p.world==ack.world&&p.modelId==ack.modelId){if(c.now<ack.wall+50)return false;ack.wall=c.now;return true;}
        if(p.sequence<=highWater)return reject();
        auto comp=r.scriptComponent(h.model),sync=comp?comp+0xc0:0,bag=sync?r.ptr(sync+0x2e0):0;
        if(!bag||r.ptr(bag)!=c.base+0x1607a90||r.ptr(bag+0x3c0)!=sync||r.ptr(sync+0x450)!=comp)return reject();
        constexpr uint64_t rid=0x0d80000000000409ULL;uintptr_t primitive=0;
        for(unsigned bucket=0;bucket<16;bucket++){
            typename WeaponSlotReader<Read>::List list;if(!r.vector(bag+0xa0+bucket*0x30,list,512))return reject();
            for(int i=0;i<list.count;i++){std::array<uint64_t,2> pair{};if(!r.get(list.items+i*16,pair))return reject();
                if(pair[0]==rid){if(primitive)return reject();primitive=pair[1];}}
        }
        std::array<unsigned char,16> value{},again{},code{};uint32_t flags=0,kind=0;double current=0;
        if(!primitive||r.ptr(primitive)!=c.base+0x1608248||r.ptr(primitive+0x80)!=bag||r.ptr(primitive+0x98)!=rid
           ||!r.get(primitive+0x94,flags)||(flags!=6&&flags!=14)||!r.get(primitive+0xa0,value))return reject();
        std::memcpy(&kind,value.data()+12,4);
        if(kind==2){int v=0;std::memcpy(&v,value.data(),4);current=v;}
        else if(kind==3){float v=0;std::memcpy(&v,value.data(),4);current=v;}else return reject();
        if(!std::isfinite(current)||current<0||current>200||std::floor(current)!=current)return reject();
        const std::array<unsigned char,16> prefix{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};
        if(r.ptr(c.base+0x1608248+0x288)!=c.base+0xf5f740||!r.get(c.base+0xf5f740,code)||code!=prefix
           ||!r.get(primitive+0xa0,again)||again!=value||!r.owner(admin,h))return reject();
        // Consume each validated request identity before invocation. A failed
        // or interrupted original call is never retried as another grant.
        highWater=p.sequence;ack={};ack.pid=c.pid;ack.creation=c.creation;ack.sequence=p.sequence;ack.wall=c.now;
        ack.generation=p.generation;ack.world=p.world;ack.modelId=p.modelId;ack.before=ack.after=uint32_t(current);
        if(current==200){ack.phase=2;return true;}
        unsigned wanted=std::min(200u,unsigned(current)+25u);auto next=value;
        if(kind==2){int v=int(wanted);std::memcpy(next.data(),&v,4);}else{float v=float(wanted);std::memcpy(next.data(),&v,4);}
        ack.phase=3;
        if(!notify(c.base+0xf5f740,primitive,sync,r.ptr(bag+0x3b8),next.data(),primitive+0x88)){++refused;return true;}
        if(!r.get(primitive+0xa0,again)||again!=next){++refused;return true;}
        ack.phase=1;ack.after=wanted;ack.credited=wanted-ack.before;++credits;return true;
    }
};
}
