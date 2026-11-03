#include "../src/native_frame_limit.hpp"
#include <cassert>
#include <iostream>
int main(){
    using passthrough::NativeFrameLimit;
    alignas(4) LONG value=0x42c80000;
    NativeFrameLimit first,second;
    assert(first.acquire(&value)&&value==0x43700000&&first.owned&&!first.restored);
    assert(!first.acquire(&value)&&!second.acquire(&value));
    assert(first.release()&&value==0x42c80000&&first.restored&&!first.owned);
    assert(first.release());
    assert(second.acquire(&value));value=0x42f00000;
    assert(!second.release()&&value==0x42f00000&&!second.restored);
    value=0x43700000;assert(second.release()&&value==0x42c80000);
    NativeFrameLimit invalid;assert(!invalid.bindVerifiedBeta(0));
    std::cout<<"Native frame limit: exclusive ownership, original data restoration, external changes and wrong code refusal passed.\n";
}
