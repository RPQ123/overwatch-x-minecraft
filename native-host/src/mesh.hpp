#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <filesystem>
#include <stdexcept>
#include <vector>
#include <set>
#include <tuple>

struct MeshVertex { float x,y,z,u,v,shade; uint32_t tint=0xffffffff; };
static_assert(sizeof(MeshVertex)==28);
struct BlockRecord { int32_t x,y,z;uint32_t state; };
static_assert(sizeof(BlockRecord)==16);
struct Mesh {
    bool creative=false;
    bool streamedWorld=false;
    std::vector<MeshVertex> vertices;
    std::vector<uint8_t> rgba;
    uint32_t width=0,height=0;
    uint64_t session=0,sequence=0,worldTick=0,producedEpochMillis=0;
    std::vector<BlockRecord> blocks;
};
inline Mesh loadMesh(const std::wstring& path) {
    std::ifstream file(std::filesystem::path(path),std::ios::binary|std::ios::ate);
    if(!file) throw std::runtime_error("No exported MC mesh");
    auto size=file.tellg();
    if(size<24 || size>4*1024*1024) throw std::runtime_error("Invalid mesh file budget");
    file.seekg(0); std::vector<char> bytes(static_cast<size_t>(size));
    if(!file.read(bytes.data(),size)) throw std::runtime_error("Incomplete mesh file");
    uint32_t fields[4]; std::memcpy(fields,bytes.data()+8,16);
    bool world=std::memcmp(bytes.data(),"OWMCB004",8)==0;
    bool creative=world||std::memcmp(bytes.data(),"OWMCB003",8)==0;
    bool patch=creative||std::memcmp(bytes.data(),"OWMCB002",8)==0;
    if((!patch&&std::memcmp(bytes.data(),"OWMCB001",8)) || fields[0]!=(world?4u:creative?3u:patch?2u:1u)
       || (!patch&&fields[1]<3) || fields[1]>(creative?65536u:patch?16384u:4096u)
       || fields[1]%3 || fields[2]<1 || fields[2]>256 || fields[3]<1 || fields[3]>256)
        throw std::runtime_error("Unsupported mesh protocol/counts");
    if(!creative&&size>1024*1024) throw std::runtime_error("Legacy mesh file budget");
    Mesh mesh;mesh.creative=creative;mesh.streamedWorld=world; mesh.width=fields[2];mesh.height=fields[3];mesh.vertices.resize(fields[1]);
    size_t header=patch?64:24,blockBytes=0,vertexStride=patch?28:24;
    if(patch) {
        if(bytes.size()<64) throw std::runtime_error("Truncated patch header");
        uint64_t metadata[4];std::memcpy(metadata,bytes.data()+24,32);
        mesh.session=metadata[0];mesh.sequence=metadata[1];mesh.worldTick=metadata[2];mesh.producedEpochMillis=metadata[3];
        uint32_t count,flags;std::memcpy(&count,bytes.data()+56,4);std::memcpy(&flags,bytes.data()+60,4);
        if(!mesh.session||!mesh.sequence||!mesh.producedEpochMillis||count>(creative?12288u:320u)||flags) throw std::runtime_error("Invalid patch metadata");
        blockBytes=count*sizeof(BlockRecord);mesh.blocks.resize(count);
    }
    size_t vertexBytes=fields[1]*vertexStride,textureBytes=fields[2]*fields[3]*4u;
    if(bytes.size()!=header+blockBytes+vertexBytes+textureBytes) throw std::runtime_error("Mesh length mismatch");
    if(patch) {
        std::memcpy(mesh.blocks.data(),bytes.data()+header,blockBytes);std::set<std::tuple<int,int,int>> occupied;
        for(const auto& block:mesh.blocks) {
            int low=world?-1000000:creative?-16:-4,high=world?1000000:creative?15:3,bottom=creative?-4:-1,top=creative?7:3;
            if(block.x<low||block.x>high||block.z<low||block.z>high||block.y<bottom||block.y>top||block.state>1000000)
                throw std::runtime_error("Invalid patch occupancy");
            if(!occupied.emplace(block.x,block.y,block.z).second) throw std::runtime_error("Duplicate patch block");
        }
    }
    for(size_t i=0;i<mesh.vertices.size();i++)
        std::memcpy(&mesh.vertices[i],bytes.data()+header+blockBytes+i*vertexStride,vertexStride);
    for(const auto& vertex:mesh.vertices) {
        std::array<float,6> values{vertex.x,vertex.y,vertex.z,vertex.u,vertex.v,vertex.shade};
        for(float value:values) if(!std::isfinite(value)) throw std::runtime_error("Nonfinite mesh vertex");
        if(std::abs(vertex.x)>(world?1000001:creative?17:patch?8:2) || std::abs(vertex.y)>(patch?8:2) || std::abs(vertex.z)>(world?1000001:creative?17:patch?8:2)
           || vertex.u<-.1f || vertex.u>1.1f || vertex.v<-.1f || vertex.v>1.1f || vertex.shade<0 || vertex.shade>1)
            throw std::runtime_error("Vertex outside proof bounds");
        if((vertex.tint>>24)!=255) throw std::runtime_error("Invalid tint alpha");
    }
    mesh.rgba.assign(bytes.begin()+header+blockBytes+vertexBytes,bytes.end());
    return mesh;
}
