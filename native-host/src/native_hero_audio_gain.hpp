#pragma once
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <algorithm>

namespace passthrough {
/** Same measured24919 INI registry as native_runtime_settings.py. Never uses a
 * historical PID/address. Only typed Sound.MasterVolume float percent is owned;
 * the original mixer and its one native SFX instance remain authoritative. */
class NativeHeroAudioGain {
    uintptr_t entry_=0,value_=0,base_=0;float before_=0,ours_=0;
    bool owned_=false,rollback_=false,stopped_=false,suppressed_=false;
    uint64_t tick_=0,retry_=0;
    template<class R,class T> static bool get(R& read,uintptr_t p,T& value){return p&&read(p,&value,sizeof(value));}
    template<class R> static bool name(R& read,uintptr_t entry){
        std::array<unsigned char,32> text{};int32_t length=0,capacity=0;uintptr_t pointer=0;
        if(!get(read,entry+8,text))return false;
        std::memcpy(&length,text.data()+16,4);std::memcpy(&capacity,text.data()+20,4);
        constexpr char wanted[]="Sound.MasterVolume";
        if(length!=int32_t(sizeof(wanted)-1)||capacity<length||capacity>8192)return false;
        std::array<char,sizeof(wanted)-1> bytes{};
        if(capacity>16){std::memcpy(&pointer,text.data(),8);if(!read(pointer,bytes.data(),bytes.size()))return false;}
        else std::memcpy(bytes.data(),text.data(),bytes.size());
        return std::memcmp(bytes.data(),wanted,bytes.size())==0;
    }
    template<class R> bool valid(R& read)const{
        int kind=0;uintptr_t value=0;
        return get(read,entry_+104,kind)&&kind==5&&get(read,entry_+144,value)&&value==value_&&name(read,entry_);
    }
    template<class R> bool locate(uintptr_t base,R& read){
        uintptr_t items=0;int count=0,capacity=0;
        if(!get(read,base+0x1859ed0,items)||!get(read,base+0x1859ed8,count)||!get(read,base+0x1859edc,capacity)
            ||count<=0||count>capacity||capacity>10000)return false;
        uintptr_t found=0,value=0;
        for(int i=0;i<count;i++){
            uintptr_t at=0;int type=0;
            if(!get(read,items+i*8,at)||!at||!get(read,at+104,type))return false;
            if(type!=5||!name(read,at))continue;
            if(found||!get(read,at+144,value)||!value)return false;
            found=at;
        }
        if(!found)return false;
        entry_=found;value_=value;base_=base;return true;
    }
    template<class R,class W> bool restore(R& read,W& write){
        if(!owned_){boosted=false;return true;}
        float current=0;
        if(!valid(read)||!get(read,value_,current)||!std::isfinite(current)){++refused;return false;}
        if(current==before_){owned_=rollback_=false;boosted=false;effective=current;return true;}
        if(!rollback_&&current!=ours_){++externalChanges;owned_=false;boosted=false;effective=current;suppressed_=true;return true;}
        if(!write(value_,&before_,4)||!get(read,value_,current)||current!=before_){++refused;return false;}
        ++restorations;owned_=rollback_=false;boosted=false;effective=current;return true;
    }
public:
    std::atomic<uint64_t> applications{0},restorations{0},refused{0},externalChanges{0};
    std::atomic<float> baseline{0},effective{0};std::atomic<bool> boosted{false},capped{false};
    static float level(float current){return current<=0?0.f:std::min(100.f,current*1.25f);}
    bool begin(){if(owned_)return false;stopped_=false;return true;}
    // Resolve the registry on the startup worker, before installing the tick.
    // The hot path subsequently validates just the cached typed entry.
    template<class R> bool prepare(uintptr_t base,R read){return !owned_&&locate(base,read);}
    template<class R,class W> bool update(uintptr_t base,bool roadhog,R read,W write){
        ++tick_;
        if(stopped_)return true;
        if(!roadhog){bool ok=restore(read,write);if(ok){suppressed_=false;capped=false;}return ok;}
        if(suppressed_)return true;
        if(owned_){
            float value=0;if(!valid(read)||!get(read,value_,value)||!std::isfinite(value)){++refused;return false;}
            if(value!=ours_){owned_=false;boosted=false;suppressed_=true;effective=value;++externalChanges;}
            return true;
        }
        if(base_!=base||!entry_||!valid(read)){
            if(tick_<retry_)return false;
            if(!locate(base,read)){retry_=tick_+120;++refused;return false;}
        }
        float current=0;if(!get(read,value_,current)||!std::isfinite(current)||current<0||current>100){++refused;return false;}
        baseline=current;effective=current;before_=current;ours_=level(current);capped=current>=100;
        if(current==ours_)return true; // mute and the user's100% ceiling are retained.
        owned_=true;float check=0;
        if(!write(value_,&ours_,4)||!get(read,value_,check)||check!=ours_){rollback_=true;++refused;restore(read,write);return false;}
        ++applications;effective=check;boosted=true;return true;
    }
    template<class R,class W> bool stop(R read,W write){stopped_=true;return restore(read,write);}
};
}
