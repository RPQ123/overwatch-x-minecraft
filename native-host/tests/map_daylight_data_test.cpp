#include "../src/map_daylight_data.hpp"
#include <cassert>
#include <cmath>
#include <fstream>
int main(int argc,char** argv){
    assert(argc==3);
    std::array<unsigned char,0x320> source{},lobby{};
    std::ifstream in(argv[1],std::ios::binary),other(argv[2],std::ios::binary);
    in.read(reinterpret_cast<char*>(source.data()),source.size());assert(in);
    other.read(reinterpret_cast<char*>(lobby.data()),lobby.size());assert(other);
    for(size_t i=0;i<source.size();++i){
        auto bad=source;bad[i]^=1;auto before=bad;
        assert(!owmc::daylightHollywoodHeader(bad)&&bad==before);
    }
    auto daylight=source,quiet=source;
    assert(owmc::quietHollywoodHeader(quiet)&&owmc::daylightHollywoodHeader(daylight));
    for(size_t i=0;i<source.size();++i)
        if(i<0x158||i>=0x164)assert(daylight[i]==quiet[i]);
    float rgb[3]{},old[3]{};
    std::memcpy(rgb,daylight.data()+0x158,12);std::memcpy(old,source.data()+0x158,12);
    assert(rgb[0]==rgb[1]&&rgb[1]==rgb[2]&&std::isfinite(rgb[0]));
    assert(std::abs(rgb[0]-(.2126*old[0]+.7152*old[1]+.0722*old[2]))<1e-6);
    assert(rgb[0]>3&&rgb[0]<4);
    auto before=daylight;assert(!owmc::daylightHollywoodHeader(daylight)&&daylight==before);
    before=lobby;assert(!owmc::daylightHollywoodHeader(lobby)&&lobby==before);
}
