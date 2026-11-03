#include "../src/hero_viewmodel_lens.hpp"
#include <cassert>
#include <iostream>
#include <limits>
int main(){
    std::array<float,136> values{};values[3]=1;values[10]=1.00005f;values[11]=1;values[14]=-.100005f;
    for(auto lens:std::array<std::array<float,2>,7>{{{-0.974278569f,1.73205078f},{-1.08055246f,1.920982f},{-1.12820041f,2.00568986f},{-1.247613f,2.217979f},{-1.289428f,2.292317f},{-1.325167f,2.355852f},{-1.224745f,2.177325f}}}){
        values[0]=lens[0];values[5]=lens[1];assert(isSupportedViewmodelLens(values));
    }
    values[0]=-.803333f;values[5]=1.428148f;assert(!isSupportedViewmodelLens(values));
    for(float fov:{45.f,50.f,55.f,60.f,65.f}){
        values[5]=1.f/std::tan(fov*3.14159265358979323846f/360);values[0]=-values[5]*9.f/16;
        assert(isSupportedViewmodelLens(values));
    }
    values[0]=-.5625f;values[5]=1;values[11]=0;values[15]=1;assert(!isSupportedViewmodelLens(values));
    values[0]=-1.325167f;values[5]=2.355852f;assert(!isSupportedViewmodelLens(values));
    values[11]=1;values[15]=0;values[0]=-1.1f;assert(!isSupportedViewmodelLens(values));
    values[0]=-1.325167f;values[5]=std::numeric_limits<float>::quiet_NaN();assert(!isSupportedViewmodelLens(values));
    std::cout<<"PASS: actual idle/Dragonblade viewmodel lenses, world/orthographic exclusion and malformed projection rejection\n";
}
