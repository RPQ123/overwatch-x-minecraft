#pragma once
#include <array>
#include <atomic>
#include <cstdint>

namespace passthrough {
// WM key messages preserve short taps between two rendering/MC ticks. Intent
// expires after focus loss; a released tap lasts at most 100 ms, not forever.
class MovementIntent {
    std::atomic<uint32_t> held{0};
    std::array<std::atomic<uint64_t>,10> until{};
public:
    void key(unsigned index,bool down,uint64_t now) {
        if(index>=until.size())return;
        if(down) {held.fetch_or(1u<<index);until[index]=now+100;}
        else held.fetch_and(~(1u<<index));
    }
    void release() {held=0;for(auto& time:until)time=0;}
    uint32_t snapshot(uint64_t now,bool focused) {
        if(!focused) {release();return 0;}
        uint32_t bits=held.load();for(unsigned i=0;i<until.size();i++)if(until[i].load()>now)bits|=1u<<i;return bits;
    }
};
}
