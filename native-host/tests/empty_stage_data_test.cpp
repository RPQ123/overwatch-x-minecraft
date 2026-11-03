#include "../src/empty_stage_data.hpp"
#include <cassert>
#include <fstream>
int main(int argc,char** argv){
    assert(argc==2);
    std::array<unsigned char,0x320> source{};
    std::ifstream in(argv[1],std::ios::binary);in.read(reinterpret_cast<char*>(source.data()),source.size());assert(in);
    auto bad=source;bad[0]^=1;auto before=bad;
    assert(!owmc::emptyStageHeader(bad)&&bad==before);
    auto empty=source;assert(owmc::emptyStageHeader(empty));
    for(size_t i=0;i<source.size();++i){
        bool removed=(i>=0x110&&i<0x128)||i>=0x200;
        assert(empty[i]==(removed?0:source[i]));
    }
    assert(!owmc::emptyStageHeader(empty));
}
