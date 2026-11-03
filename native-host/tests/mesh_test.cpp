#include "../src/mesh.hpp"
#include <cassert>
#include <iostream>
#include <limits>

namespace {
std::vector<char> fixture() {
    std::vector<char> bytes(24+3*24+4);
    std::memcpy(bytes.data(),"OWMCB001",8);
    uint32_t fields[]{1,3,1,1};std::memcpy(bytes.data()+8,fields,sizeof(fields));
    MeshVertex vertices[]{{0,0,0,0,0,1},{1,0,0,1,0,1},{0,1,0,0,1,1}};
    for(unsigned i=0;i<3;i++) std::memcpy(bytes.data()+24+i*24,&vertices[i],24);
    return bytes;
}
void write(const std::filesystem::path& path,const std::vector<char>& bytes) {
    std::ofstream file(path,std::ios::binary);file.write(bytes.data(),bytes.size());
}
void rejects(const std::filesystem::path& path,const std::vector<char>& bytes) {
    write(path,bytes);bool rejected=false;
    try { loadMesh(path.wstring()); } catch(const std::runtime_error&) { rejected=true; }
    assert(rejected);
}
}
int main() {
    const auto path=std::filesystem::temp_directory_path()/L"owmc-mesh-parser-test.bin";
    auto bytes=fixture();write(path,bytes);auto mesh=loadMesh(path.wstring());
    assert(mesh.vertices.size()==3 && mesh.rgba.size()==4 && mesh.width==1);
    bytes[0]='X';rejects(path,bytes);
    bytes=fixture();bytes.resize(bytes.size()-1);rejects(path,bytes);
    bytes=fixture();bytes.push_back(0);rejects(path,bytes);
    bytes=fixture();uint32_t huge=0xffffffff;std::memcpy(bytes.data()+12,&huge,4);rejects(path,bytes);
    bytes=fixture();uint32_t hugeWidth=257;std::memcpy(bytes.data()+16,&hugeWidth,4);rejects(path,bytes);
    bytes=fixture();float nan=std::numeric_limits<float>::quiet_NaN();std::memcpy(bytes.data()+24,&nan,4);rejects(path,bytes);
    bytes=fixture();float invalid=3;std::memcpy(bytes.data()+24,&invalid,4);rejects(path,bytes);
    bytes=fixture();float uv=2;std::memcpy(bytes.data()+24+12,&uv,4);rejects(path,bytes);
    std::filesystem::remove(path);
    std::cout<<"Valid mesh plus eight malformed/budget/finite/bounds cases passed.\n";
}
