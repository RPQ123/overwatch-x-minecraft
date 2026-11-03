#include "../src/hand_mask_trace.hpp"
#include <cassert>
#include <iostream>
using passthrough::HandMaskTrace;
int main(){
    HandMaskTrace disabled;
    disabled.candidate(1.9f,true);disabled.finish(1,1,1);
    assert(!disabled.snapshot());
    HandMaskTrace trace(true);
    trace.candidate(1.920982f,true);trace.start();trace.decision(true,true,false,true);trace.finish(1,100,1);
    auto first=trace.snapshot();assert(first&&first->count==1&&first->rows[0].preserved);
    trace.candidate(1.6f,false);trace.decision(false,false,false,false);trace.finish(2,110,1);
    auto second=trace.snapshot();assert(second->count==2&&second->rows[1].lensRejected==1&&second->rows[1].handDraws==0);
    assert(first->count==1&&first->rows[0].frame==1); // immutable across report/render threads
    trace.candidate(1.920982f,true);trace.start();trace.resumed();trace.depthChanged();
    trace.decision(true,true,true,false);trace.finish(3,120,1);
    auto third=trace.snapshot();assert(third->rows[2].resumed==1&&third->rows[2].depthChanges==1&&third->rows[2].invalid);
    for(unsigned i=4;i<200;++i)trace.finish(i,100+i,1);
    auto bounded=trace.snapshot();assert(bounded->count==HandMaskTrace::Capacity);
    assert(bounded->rows[0].frame==72&&bounded->rows[127].frame==199);
    assert(bounded->rows[127].lensRejected==0&&!bounded->rows[127].preserved); // no prior-frame carry
    std::cout<<"hand_mask_trace_test passed (diagnostic fixture only)\n";
}
