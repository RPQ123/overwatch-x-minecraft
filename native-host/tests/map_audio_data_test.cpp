#include "../src/map_audio_data.hpp"
#include "../src/empty_stage_data.hpp"
#include <cassert>
#include <fstream>
int main(int argc,char** argv){
    assert(argc==3);
    std::array<unsigned char,0x320> source{},lobby{};
    std::ifstream in(argv[1],std::ios::binary),other(argv[2],std::ios::binary);
    in.read(reinterpret_cast<char*>(source.data()),source.size());assert(in);
    other.read(reinterpret_cast<char*>(lobby.data()),lobby.size());assert(other);
    // Any changed byte must reject before changing the supplied header.
    for(size_t i=0;i<source.size();++i){
        auto bad=source;bad[i]^=1;auto before=bad;
        assert(!owmc::quietHollywoodHeader(bad)&&bad==before);
    }
    auto quiet=source;assert(owmc::quietHollywoodHeader(quiet));
    for(size_t i=0;i<source.size();++i){
        bool removed=(i>=0x120&&i<0x128)||(i>=0x240&&i<0x244)
            ||(i>=0x280&&i<0x284)||(i>=0x2c0&&i<0x2c4);
        assert(quiet[i]==(removed?0:source[i]));
    }
    auto before=quiet;assert(!owmc::quietHollywoodHeader(quiet)&&quiet==before);
    before=lobby;assert(!owmc::quietHollywoodHeader(lobby)&&lobby==before);
    before=source;assert(!owmc::emptyStageHeader(source)&&source==before);
}
