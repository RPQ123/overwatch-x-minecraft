#include "../src/native_hero_audio_gain.hpp"
#include <vector>
#include <cassert>
#include <iostream>
#include <limits>
using namespace passthrough;
int main(){
    std::vector<unsigned char> m(0x1b00000);unsigned writes=0;
    auto put=[&](uintptr_t p,auto v){assert(p+sizeof(v)<=m.size());std::memcpy(m.data()+p,&v,sizeof(v));};
    auto read=[&](uintptr_t p,void* v,size_t n){if(!p||p+n>m.size())return false;std::memcpy(v,m.data()+p,n);return true;};
    constexpr uintptr_t base=0x100000,items=0x300000,entry=0x400000,value=0x500000;
    put(base+0x1859ed0,items);put(base+0x1859ed8,1);put(base+0x1859edc,2);put(items,entry);
    put(entry+8,uintptr_t(0x410000));put(entry+24,18);put(entry+28,32);std::memcpy(m.data()+0x410000,"Sound.MasterVolume",18);
    put(entry+104,5);put(entry+144,value);put(value,80.f);put(value+4,0x12345678u);
    auto write=[&](uintptr_t p,const void* v,size_t n){assert(p==value&&n==4);++writes;std::memcpy(m.data()+p,v,n);return true;};
    auto level=[&](){float f=0;read(value,&f,4);return f;};
    NativeHeroAudioGain gain;assert(gain.begin());assert(gain.prepare(base,read)&&writes==0);assert(gain.update(base,true,read,write)&&level()==100&&writes==1);
    assert(gain.baseline==80&&gain.effective==100&&gain.boosted);
    assert(gain.update(base,true,read,write)&&writes==1); // never multiply again each frame
    assert(gain.update(base,false,read,write)&&level()==80&&writes==2&&!gain.boosted);
    uint32_t neighbor=0;read(value+4,&neighbor,4);assert(neighbor==0x12345678); // no default/mirror overwrite
    put(value,50.f);assert(gain.update(base,true,read,write)&&level()==62.5f);
    put(value,42.f);unsigned before=writes;assert(gain.update(base,true,read,write)&&level()==42&&writes==before);
    assert(gain.update(base,true,read,write)&&writes==before); // respect user change until hero transition
    assert(gain.update(base,false,read,write));assert(gain.update(base,true,read,write)&&level()==52.5f);
    assert(gain.stop(read,write)&&level()==42);before=writes;assert(gain.update(base,true,read,write)&&writes==before);
    assert(gain.begin());put(value,100.f);assert(gain.update(base,true,read,write)&&level()==100&&writes==before&&gain.capped);
    put(value,0.f);assert(gain.update(base,true,read,write)&&level()==0&&writes==before); // do not unmute
    put(value,-1.f);assert(!gain.update(base,true,read,write)&&writes==before);
    put(value,std::numeric_limits<float>::quiet_NaN());assert(!gain.update(base,true,read,write)&&writes==before);
    put(value,80.f);put(entry+104,3);NativeHeroAudioGain wrongType;assert(!wrongType.update(base,true,read,write)&&writes==before);
    put(entry+104,5);NativeHeroAudioGain fail;bool once=true;
    auto partial=[&](uintptr_t p,const void* v,size_t n){write(p,v,n);if(once){once=false;return false;}return true;};
    assert(!fail.update(base,true,read,partial)&&level()==80);assert(fail.stop(read,write));
    NativeHeroAudioGain stale;assert(stale.update(base,true,read,write)&&level()==100);
    put(entry+144,uintptr_t(0x510000));before=writes;assert(!stale.stop(read,write)&&writes==before); // refuse stale metadata
    put(entry+144,value);assert(stale.stop(read,write)&&level()==80);
    put(base+0x1859ed8,2);put(items+8,entry);NativeHeroAudioGain duplicate;before=writes;assert(!duplicate.update(base,true,read,write)&&writes==before);
    std::cout<<"PASS: native Roadhog master80->100/+1.94dB,typed registry bounds,no repeat,100/mute cap,hero/stop restore,external edits preserved,partial-write rollback,stale/duplicate refusal\n";
}
