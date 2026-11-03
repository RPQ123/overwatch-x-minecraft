#pragma once
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <memory>

namespace passthrough {
// OPTIONAL diagnostic only, not yet wired into the compositor. Numeric CPU
// evidence stays on its existing render owner; no draws, GPU readbacks, hooks,
// image history or rendering policy are introduced by this class.
class HandMaskTrace {
public:
    static constexpr unsigned Capacity=128;
    struct Frame {
        uint64_t frame=0,wall=0;
        unsigned viewMode=0,stageCandidates=0,lensRejected=0,handDraws=0;
        unsigned starts=0,resumed=0,depthChanges=0;
        float minLens=0,maxLens=0;
        bool before=false,after=false,invalid=false,preserved=false;
    };
    struct Snapshot {std::array<Frame,Capacity> rows{};unsigned count=0;};
private:
    bool enabled_=false;
    Frame current_{};
    std::array<Frame,Capacity> ring_{};
    unsigned count_=0,cursor_=0;
    std::shared_ptr<const Snapshot> published_;
public:
    explicit HandMaskTrace(bool enabled=false):enabled_(enabled){}
    bool enabled()const{return enabled_;}
    // Call only AFTER viewport, six RTs and depth format have been validated.
    // This lets a rejected FOV be distinguished from a missing native hand draw.
    void candidate(float lens,bool accepted){
        if(!enabled_)return;
        ++current_.stageCandidates;
        if(std::isfinite(lens)){
            if(current_.stageCandidates==1)current_.minLens=current_.maxLens=lens;
            else {if(lens<current_.minLens)current_.minLens=lens;if(lens>current_.maxLens)current_.maxLens=lens;}
        }
        if(accepted)++current_.handDraws;else ++current_.lensRejected;
    }
    void start(){if(enabled_)++current_.starts;}
    void resumed(){if(enabled_)++current_.resumed;}
    void depthChanged(){if(enabled_)++current_.depthChanges;}
    void decision(bool before,bool after,bool invalid,bool preserved){
        if(!enabled_)return;
        current_.before=before;current_.after=after;current_.invalid=invalid;current_.preserved=preserved;
    }
    // Exactly once, immediately before the existing per-frame flags are reset.
    void finish(uint64_t frame,uint64_t wall,unsigned viewMode){
        if(!enabled_)return;
        current_.frame=frame;current_.wall=wall;current_.viewMode=viewMode;
        ring_[cursor_]=current_;cursor_=(cursor_+1)%Capacity;if(count_<Capacity)++count_;
        auto copy=std::make_shared<Snapshot>();copy->count=count_;
        unsigned begin=(cursor_+Capacity-count_)%Capacity;
        for(unsigned i=0;i<count_;++i)copy->rows[i]=ring_[(begin+i)%Capacity];
        std::atomic_store(&published_,std::shared_ptr<const Snapshot>(copy));
        current_={};
    }
    // Worker/report thread may only read this immutable published snapshot.
    std::shared_ptr<const Snapshot> snapshot()const{return std::atomic_load(&published_);}
};
}
