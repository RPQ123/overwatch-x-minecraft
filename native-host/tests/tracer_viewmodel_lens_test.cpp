#include "../src/tracer_viewmodel_lens.hpp"
#include "../src/hero_viewmodel_lens.hpp"
#include <cassert>
#include <iostream>
#include <limits>
using passthrough::isTracerBlinkViewmodelLens;
int main(){
    constexpr uint64_t tracer=0x02e0000000000003ULL;
    std::array<float,136> values{};values[3]=1;values[10]=1.00005f;values[11]=1;values[14]=-.100005f;
    auto lens=[&](float y){values[5]=y;values[0]=-y*9.f/16;};
    for(float y:{1.979f,1.9273f,1.87768f,1.83004f,1.78422f,1.74013f,1.79876f,1.8864f,1.98089f}){
        lens(y);assert(!isSupportedViewmodelLens(values));assert(isTracerBlinkViewmodelLens(values,tracer,1));
        assert(!isTracerBlinkViewmodelLens(values,0x02e0000000000029ULL,1));
        assert(!isTracerBlinkViewmodelLens(values,tracer,2));assert(!isTracerBlinkViewmodelLens(values,0,1));
    }
    for(unsigned i=0;i<=1000;++i){lens(1.738f+(2.005f-1.738f)*i/1000);assert(isTracerBlinkViewmodelLens(values,tracer,1));}
    for(float y:{1.428148f,1.38181f,1.38125f,1.36575f,1.35047f,1.33542f,1.32058f,1.30595f,1.32533f,1.35319f}){
        lens(y);assert(!isTracerBlinkViewmodelLens(values,tracer,1));
    }
    lens(1.7379f);assert(!isTracerBlinkViewmodelLens(values,tracer,1));
    lens(2.0051f);assert(!isTracerBlinkViewmodelLens(values,tracer,1));
    lens(2.004f);assert(isSupportedViewmodelLens(values)&&isTracerBlinkViewmodelLens(values,tracer,1));
    lens(1.87768f);auto correct=values;
    values[14]=-.200005f;assert(!isTracerBlinkViewmodelLens(values,tracer,1));values=correct;
    values[10]=1.005f;assert(!isTracerBlinkViewmodelLens(values,tracer,1));values=correct;
    values[0]+=.01f;assert(!isTracerBlinkViewmodelLens(values,tracer,1));values=correct;
    values[1]=.01f;assert(!isTracerBlinkViewmodelLens(values,tracer,1));values=correct;
    values[11]=0;values[15]=1;assert(!isTracerBlinkViewmodelLens(values,tracer,1));values=correct;
    values[6]=std::numeric_limits<float>::quiet_NaN();assert(!isTracerBlinkViewmodelLens(values,tracer,1));
    std::cout<<"tracer_viewmodel_lens_test passed: measured Blink interval/current Tracer/FP only, world and malformed rejection\n";
}
