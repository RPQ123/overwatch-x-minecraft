#include "../src/frame_compositor.hpp"
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <filesystem>

using namespace passthrough;
void bmp(const std::filesystem::path& path,const CompositePixels& image) {
    BITMAPFILEHEADER file{};file.bfType=0x4d42;file.bfOffBits=sizeof file+sizeof(BITMAPINFOHEADER);file.bfSize=file.bfOffBits+image.width*image.height*4;
    BITMAPINFOHEADER info{};info.biSize=sizeof info;info.biWidth=image.width;info.biHeight=-int(image.height);info.biPlanes=1;info.biBitCount=32;info.biCompression=BI_RGB;
    std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<char*>(&file),sizeof file);out.write(reinterpret_cast<char*>(&info),sizeof info);
    auto bgra=image.rgba;for(size_t i=0;i<bgra.size();i+=4) std::swap(bgra[i],bgra[i+2]);out.write(reinterpret_cast<char*>(bgra.data()),bgra.size());if(!out) throw std::runtime_error("Write evidence bitmap");
}
int main(int argc,char** argv) {try {
    if(argc<3||argc>4) throw std::runtime_error("Usage: frame-compositor-live seconds evidence-directory [warp]");
    int seconds=std::stoi(argv[1]);if(seconds<1||seconds>60) throw std::runtime_error("Seconds must be 1..60");
    std::filesystem::path dir(argv[2]);std::filesystem::create_directories(dir);
    FrameCompositor renderer(argc==4);WorldFrames reader;
    auto started=std::chrono::steady_clock::now();uint64_t generation=0,seq=0;unsigned frames=0,rejected=0;float maxDepthError=0;std::vector<double> times;
    WorldFrame last;CompositePixels output;
    while(std::chrono::steady_clock::now()-started<std::chrono::seconds(seconds)) {
        WorldFrame f;try {if(!reader.latest(f)|| (f.generation==generation&&f.sequence==seq)) {Sleep(5);continue;}}
        catch(const std::exception& e) {rejected++;if(rejected<=3) std::cerr<<e.what()<<"\n";Sleep(10);continue;}
        auto before=std::chrono::steady_clock::now();output=renderer.render(f);
        if(output.rgba!=f.rgba) throw std::runtime_error("Real MC -> D3D RGBA mismatch");
        for(size_t i=0;i<f.depth.size();i++) maxDepthError=std::max(maxDepthError,std::abs(output.depth[i]-f.depth[i]));
        if(maxDepthError>2e-7f) throw std::runtime_error("Real MC -> D3D depth mismatch");
        times.push_back(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-before).count());
        frames++;generation=f.generation;seq=f.sequence;last=std::move(f);
    }
    if(!frames) throw std::runtime_error("No fresh frames composited");
    bmp(dir/"d3d-mc-world.bmp",output);
    // Retain this one actual frame for offline shader regression without
    // repeatedly running two games. These private captures stay in research/.
    auto saveBytes=[&](const char* name,const void* bytes,size_t count) {std::ofstream file(dir/name,std::ios::binary);file.write(static_cast<const char*>(bytes),count);if(!file) throw std::runtime_error("Write actual frame fixture");};
    saveBytes("source.rgba",last.rgba.data(),last.rgba.size());saveBytes("source.depth",last.depth.data(),last.depth.size()*sizeof(float));saveBytes("source.projection",last.projection.data(),last.projection.size()*sizeof(float));
    Matrix projection=Matrix::fromColumnMajor(last.projection);Matrix warp=projection*cameraYaw(.20943951f)*projection.inverse();auto rotated=renderer.render(last,warp);bmp(dir/"d3d-mc-yaw12.bmp",rotated);
    std::sort(times.begin(),times.end());double sum=0;for(double t:times) sum+=t;
    std::ofstream json(dir/"d3d-frame-proof.json");json<<"{\n  \"kind\":\"actual-minecraft-independent-d3d11\",\n  \"owAttached\":false,\n  \"hostPoseConnected\":false,\n  \"driver\":\""<<(argc==4?"WARP":"hardware")<<"\",\n  \"sourcePid\":"<<last.sourcePid<<",\n  \"generation\":"<<generation<<",\n  \"frames\":"<<frames<<",\n  \"rejected\":"<<rejected<<",\n  \"width\":"<<last.width<<",\n  \"height\":"<<last.height<<",\n  \"rgbaExact\":true,\n  \"maxDepthError\":"<<maxDepthError<<",\n  \"meanUploadDrawReadbackVerifyMs\":"<<sum/times.size()<<",\n  \"p95UploadDrawReadbackVerifyMs\":"<<times[size_t((times.size()-1)*.95)]<<",\n  \"maxUploadDrawReadbackVerifyMs\":"<<times.back()<<",\n  \"rotationOnlyDemoDegrees\":12\n}\n";if(!json) throw std::runtime_error("Write evidence report");
    std::cout<<"Actual MC frames through independent D3D11: "<<frames<<", rejected="<<rejected<<", RGBA exact, max depth error="<<maxDepthError<<". Evidence: "<<dir.string()<<"\n";return rejected?2:0;
} catch(const std::exception& e) {std::cerr<<e.what()<<"\n";return 1;}}
