#include "../src/mesh.hpp"
#include "../src/stream.hpp"
#include <cassert>
#include <iostream>
#include <chrono>

int main() {
    const auto path=std::filesystem::temp_directory_path()/L"owmc-patch-test.bin";
    std::vector<char> bytes(64+16+3*28+4);
    std::memcpy(bytes.data(),"OWMCB002",8);uint32_t fields[]{2,3,1,1};std::memcpy(bytes.data()+8,fields,16);
    uint64_t metadata[]{7,1,20,1000};std::memcpy(bytes.data()+24,metadata,32);
    uint32_t counts[]{1,0};std::memcpy(bytes.data()+56,counts,8);
    int32_t block[]{-4,-1,3,123};std::memcpy(bytes.data()+64,block,16);
    float vertices[]{-4,-1,3,0,0,1, -3,-1,3,1,0,1, -4,0,3,0,1,1};
    for(unsigned i=0;i<3;i++) { std::memcpy(bytes.data()+80+i*28,vertices+i*6,24);uint32_t color=0xff55aa33;std::memcpy(bytes.data()+104+i*28,&color,4); }
    auto write=[&]{std::ofstream file(path,std::ios::binary);file.write(bytes.data(),bytes.size());};
    write();auto mesh=loadMesh(path.wstring());
    assert(mesh.session==7&&mesh.sequence==1&&mesh.blocks.size()==1&&mesh.vertices[0].tint==0xff55aa33);
    assert(mesh.vertices[0].x==-4);
    SnapshotOrder order;assert(order.accept(mesh,1000));assert(!order.accept(mesh,1000));
    mesh.sequence=2;assert(!order.accept(mesh,5000));assert(order.accept(mesh,1100));
    mesh.sequence=1;assert(!order.accept(mesh,1100));mesh.session=9;mesh.producedEpochMillis=1100;
    assert(order.accept(mesh,1100));mesh.session=8;mesh.producedEpochMillis=999;assert(!order.accept(mesh,1100));
    auto reject=[&]{write();bool failed=false;try {loadMesh(path.wstring());} catch(const std::runtime_error&) {failed=true;}assert(failed);};
    bytes[24]=0;reject();bytes[24]=7;
    int32_t outside=9;std::memcpy(bytes.data()+64,&outside,4);reject();std::memcpy(bytes.data()+64,block,4);
    // Dedicated version 3 expands the superflat volume without loosening V2.
    std::memcpy(bytes.data(),"OWMCB003",8);uint32_t version=3;std::memcpy(bytes.data()+8,&version,4);
    int32_t edge[]{-16,-4,15,1};std::memcpy(bytes.data()+64,edge,16);write();
    auto flat=loadMesh(path.wstring());assert(flat.creative&&flat.blocks[0].x==-16&&flat.blocks[0].y==-4);
    outside=16;std::memcpy(bytes.data()+64,&outside,4);reject();std::memcpy(bytes.data()+64,edge,4);
    std::memcpy(bytes.data(),"OWMCB004",8);version=4;std::memcpy(bytes.data()+8,&version,4);
    int32_t streamed[]{128,-4,-96,79};std::memcpy(bytes.data()+64,streamed,16);write();
    auto window=loadMesh(path.wstring());assert(window.streamedWorld&&window.blocks[0].x==128);
    outside=1000001;std::memcpy(bytes.data()+64,&outside,4);reject();std::memcpy(bytes.data()+64,streamed,4);
    bytes.pop_back();reject();std::filesystem::remove(path);
    std::cout<<"Patch metadata, signed bounds, tint, session and truncation checks passed.\n";
}
