#pragma once
#include "native_armory.hpp"

namespace passthrough {
// Beta 24919: traced Wave resolver 104633b and motion update 1037b60.
// These are per-factory sampled parameters, not a second attack source.
struct BarrageWave {float start=0,fade=0,phase=0,frequency=0,magnitude=0,rotation=0;uint32_t spiral=0;};
// One original Volley numbers its factories0..89. A fresh world packet is not
// permission to move an already channeling ultimate into that world.
struct BarrageScope {
    uint64_t owner=0,volley=0,world=0,host=0,mc=0;uint32_t firstTick=0;
    bool cancelled=false;
    bool admit(uint64_t nextOwner,uint64_t nextVolley,uint32_t tick,uint32_t shot,uint64_t nextWorld,uint64_t nextHost,uint64_t nextMc){
        if(shot>=90)return false;
        bool sameBegin=owner==nextOwner&&volley==nextVolley&&firstTick==tick;
        if(shot==0&&!sameBegin){owner=nextOwner;volley=nextVolley;firstTick=tick;world=nextWorld;host=nextHost;mc=nextMc;cancelled=false;}
        bool same=owner==nextOwner&&volley==nextVolley&&firstTick!=0&&world==nextWorld&&host==nextHost&&mc==nextMc;
        if(!same)cancelled=true;
        return same&&!cancelled;
    }
};
inline std::array<float,3> barrageWaveOffset(const BarrageWave& w,std::array<float,3> forward,float age){
    float t=age-w.start;if(t<=0)return {};
    float size=std::sqrt(forward[0]*forward[0]+forward[2]*forward[2]);
    std::array<float,3> side=size>1e-8f?std::array<float,3>{-forward[2]/size,0,forward[0]/size}:std::array<float,3>{1,0,0};
    std::array<float,3> up{side[1]*forward[2]-side[2]*forward[1],side[2]*forward[0]-side[0]*forward[2],side[0]*forward[1]-side[1]*forward[0]};
    float mag=w.magnitude*(w.fade>0?std::min(1.f,t/w.fade):1.f),angle=(t*w.frequency+w.phase)*6.2831854820251465f;
    if(!w.spiral){mag*=std::sin(angle);angle=w.rotation*.01745329238474369f;}
    float x=std::sin(angle)*mag,y=std::cos(angle)*mag;
    return {side[0]*x+up[0]*y,side[1]*x+up[1]*y,side[2]*x+up[2]*y};
}
template<class Read> bool barrageDefinition(const ArmorySpec& s,Read read){
    uint64_t script=0;uintptr_t items=0;uint64_t count=0;
    if(s.resource!=0x0400000000000052ULL||s.node!=2||s.effect!=1||s.gravity!=0
       ||!read(s.script+0x150,script)||script!=0x058000000000002bULL
       ||!armoryArray(s.definition+0x100,read,items,count)||count!=2)return false;
    for(unsigned i=0;i<2;i++){
        uintptr_t object=0;if(!read(items+i*8,object)||!armoryType(object,read,0x855ce717))return false;
        const std::array<float,12> expected{0,.2f,i==0?1.f:0.f,.5f,0,1,.1f,1,.2f,1.5f,10,360};
        for(unsigned j=0;j<12;j++){
            uintptr_t literal=0;float value=0;if(!read(object+8+j*8,literal))return false;
            if(!literal){if(expected[j]!=0)return false;}
            else if(!armoryLiteral(literal,read,value)||value!=expected[j])return false;
        }
    }
    return true;
}
template<class Read> bool barrageResolved(uintptr_t base,uintptr_t config,uintptr_t argument,Read read,std::array<BarrageWave,2>& waves){
    uintptr_t holder=0,items=0;uint64_t flag=0;std::array<int,2> sizes{};uint16_t seed=0;
    if(!read(config+0x68,holder)||!read(config+0x70,flag)||flag!=1||!read(holder,items)
       ||!read(holder+8,sizes)||sizes[0]!=2||sizes[1]<2||sizes[1]>64||!read(argument+0x40,seed))return false;
    std::array<float,7> random{};
    for(unsigned j=2;j<=6;j++){uint32_t raw=0;if(!read(base+0x18449f0+((seed+j)&0x3fff)*4,raw))return false;random[j]=float(raw)*0x1p-32f;}
    for(unsigned i=0;i<2;i++){
        uintptr_t object=0,vt=0;std::array<float,12> f{};
        if(!read(items+i*8,object)||!read(object,vt)||vt!=base+0x16142c0||!read(object+0x20,f))return false;
        const std::array<float,12> expected{0,.2f,i==0?1.f:0.f,.5f,0,1,.1f,1,.2f,1.5f,10,360};
        if(f!=expected)return false;
        auto& w=waves[i];w.start=f[0];w.fade=f[1];w.spiral=random[2]<=f[2];
        w.phase=f[4]+random[4]*(f[5]-f[4]);w.frequency=f[6]+random[5]*(f[7]-f[6]);
        if(random[3]<=f[3])w.frequency=-w.frequency;
        w.magnitude=f[8]+random[6]*(f[9]-f[8]);w.rotation=f[10]+random[5]*(f[11]-f[10]);
    }
    return true;
}
}
