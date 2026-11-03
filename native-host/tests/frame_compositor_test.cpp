#include "../src/frame_compositor.hpp"
#include <cassert>
#include <iostream>
#include <limits>
#include <algorithm>

using namespace passthrough;
template<class T> void put(unsigned char* b,size_t n,T v) {std::memcpy(b+n,&v,sizeof v);}
template<class F> void rejected(F fn) {bool failed=false;try {fn();} catch(const std::exception&) {failed=true;}assert(failed);}
Matrix perspective() {Matrix p;p.m={1,0,0,0,0,1,0,0,0,0,-101.f/99,-200.f/99,0,0,-1,0};return p;}
WorldFrame marker(uint32_t w,uint32_t h) {
    WorldFrame f;f.width=w;f.height=h;f.rgba.resize(size_t(w)*h*4);f.depth.resize(size_t(w)*h);
    for(uint32_t y=0;y<h;y++) for(uint32_t x=0;x<w;x++) {size_t i=size_t(y)*w+x;f.rgba[i*4]=x;f.rgba[i*4+1]=y;f.rgba[i*4+2]=x^y;f.rgba[i*4+3]=255;f.depth[i]=(x%5)*.25f;}
    return f;
}
void verifyCpuWarp(const WorldFrame& f,const Matrix& warp,const CompositePixels& output) {
    Matrix reverse=warp.inverse();size_t visible=0,missing=0;
    for(uint32_t y=0;y<f.height;y++) for(uint32_t x=0;x<f.width;x++) {
        size_t i=size_t(y)*f.width+x;auto ray=warp.apply({(x+.5f)*2/f.width-1,1-(y+.5f)*2/f.height,-1,1});
        float u=ray[0]/ray[3]*.5f+.5f,v=.5f-ray[1]/ray[3]*.5f;
        if(ray[3]<=0||u<0||v<0||u>=1||v>=1) {assert(output.rgba[i*4+3]==0&&output.depth[i]==1);missing++;continue;}
        int sx=int(u*f.width),sy=int(v*f.height);size_t s=size_t(sy)*f.width+sx;
        if(f.depth[s]==1) {assert(std::memcmp(output.rgba.data()+i*4,f.rgba.data()+s*4,4)==0&&output.depth[i]==1);visible++;continue;}
        auto clip=reverse.apply({u*2-1,1-v*2,f.depth[s]*2-1,1});float z=clip[2]/clip[3]*.5f+.5f;
        if(clip[3]<=0||z<0||z>1.000001f) {assert(output.rgba[i*4+3]==0);missing++;continue;}
        assert(std::memcmp(output.rgba.data()+i*4,f.rgba.data()+s*4,4)==0);
        assert(std::abs(output.depth[i]-std::clamp(z,0.f,1.f))<2e-6f);visible++;
    }
    assert(visible>f.width*f.height/3&&missing>0);
}
int main() {
    std::array<unsigned char,headerBytes> h{};std::array<unsigned char,256> d{};uint64_t now=unixMillis();
    std::memcpy(h.data(),"OWMCFR01",8);put(h.data(),8,uint32_t(2));put(h.data(),12,uint32_t(headerBytes));put(h.data(),16,uint32_t(3));
    put(h.data(),20,uint32_t(2560));put(h.data(),24,uint32_t(1440));put(h.data(),32,uint64_t(slotStride));put(h.data(),40,uint64_t(1));put(h.data(),48,int32_t(0));put(h.data(),52,uint32_t(GetCurrentProcessId()));put(h.data(),56,uint64_t(99));
    put(d.data(),0,uint64_t(2));put(d.data(),8,uint64_t(1));put(d.data(),24,uint32_t(2));put(d.data(),28,uint32_t(2));put(d.data(),32,1.f);put(d.data(),36,100.f);put(d.data(),40,90.f);put(d.data(),44,uint32_t(2));put(d.data(),84,uint32_t(1));put(d.data(),88,uint64_t(1));put(d.data(),96,uint64_t(2));put(d.data(),104,now);
    auto p=perspective();for(int r=0;r<4;r++) for(int c=0;c<4;c++) put(d.data(),112+(c*4+r)*4,p.m[r*4+c]);
    unsigned char payload[32]={11,12,13,255,21,22,23,255,31,32,33,255,41,42,43,255};
    for(int i=0;i<4;i++) put(payload,16+i*4,float(i)/3);
    auto f=decodeFrame(h.data(),d.data(),payload,sizeof payload,now);assert(f.rgba[0]==31&&f.rgba[8]==11&&f.depth[0]==2.f/3);
    auto colorDescriptor=d;put(colorDescriptor.data(),44,uint32_t(1));
    auto color=decodeFrame(h.data(),colorDescriptor.data(),payload,16,now);assert(color.depth.empty()&&color.rgba==f.rgba);
    auto bossDescriptor=colorDescriptor;put(bossDescriptor.data(),184,uint32_t(0x31485342));put(bossDescriptor.data(),188,125.f);put(bossDescriptor.data(),192,200.f);put(bossDescriptor.data(),196,uint32_t(1));
    auto boss=decodeFrame(h.data(),bossDescriptor.data(),payload,16,now);assert(boss.bossHealth==125&&boss.bossMaximum==200);
    put(bossDescriptor.data(),188,201.f);rejected([&]{decodeFrame(h.data(),bossDescriptor.data(),payload,16,now);});
    put(bossDescriptor.data(),188,std::numeric_limits<float>::quiet_NaN());rejected([&]{decodeFrame(h.data(),bossDescriptor.data(),payload,16,now);});
    // Reusing a color slot keeps its allocation; changing formats clears stale depth.
    auto allocation=f.rgba.data();
    decodeFrameInto(f,h.data(),colorDescriptor.data(),payload,16,now);
    assert(f.rgba.data()==allocation&&f.depth.empty()&&f.rgba==color.rgba);
    decodeFrameInto(f,h.data(),d.data(),payload,32,now);
    assert(f.rgba.data()==allocation&&f.depth.size()==4&&f.depth[0]==2.f/3);
    WorldFramePool pool;
    auto first=pool.acquire();first->rgba.assign(16,91);auto firstAddress=first.get();
    std::shared_ptr<const WorldFrame> outstanding=first;first.reset();
    auto second=pool.acquire(),third=pool.acquire();
    assert(second&&third&&second.get()!=firstAddress&&third.get()!=firstAddress);
    assert(!pool.acquire());second->rgba.assign(16,23);
    assert(outstanding->rgba==std::vector<unsigned char>(16,91));
    outstanding.reset();auto reused=pool.acquire();
    assert(reused.get()==firstAddress&&reused->rgba==std::vector<unsigned char>(16,91));
    rejected([&]{decodeFrame(h.data(),colorDescriptor.data(),payload,32,now);});
    auto hd=colorDescriptor;put(hd.data(),24,uint32_t(1920));put(hd.data(),28,uint32_t(1080));
    std::vector<unsigned char> hdPixels(1920*1080*4,79);auto full=decodeFrame(h.data(),hd.data(),hdPixels.data(),hdPixels.size(),now);
    assert(full.rgba==hdPixels&&full.depth.empty());
    put(hd.data(),44,uint32_t(3));rejected([&]{decodeFrame(h.data(),hd.data(),hdPixels.data(),hdPixels.size(),now);});
    rejected([&]{decodeFrame(h.data(),d.data(),payload,31,now);});rejected([&]{decodeFrame(h.data(),d.data(),payload,32,now+1001);});
    rejected([&]{decodeFrame(h.data(),d.data(),payload,32,now-251);});
    auto bad=d;put(bad.data(),0,uint64_t(3));rejected([&]{decodeFrame(h.data(),bad.data(),payload,32,now);});
    bad=d;put(bad.data(),24,uint32_t(1281));rejected([&]{decodeFrame(h.data(),bad.data(),payload,32,now);});
    bad=d;put(bad.data(),112,std::numeric_limits<float>::quiet_NaN());rejected([&]{decodeFrame(h.data(),bad.data(),payload,32,now);});
    auto badHeader=h;put(badHeader.data(),56,uint64_t(0));rejected([&]{decodeFrame(badHeader.data(),d.data(),payload,32,now);});
    put(payload,16,1.1f);rejected([&]{decodeFrame(h.data(),d.data(),payload,32,now);});put(payload,16,0.f);
    // Win64 lifecycle fixture has a separate identity; it never creates the production mapping.
    const wchar_t* name=L"Local\\OWMCPassthroughFrameNativeTest";
    HANDLE map=CreateFileMappingW(INVALID_HANDLE_VALUE,nullptr,PAGE_READWRITE,0,DWORD(mappingBytes),name);assert(map);
    auto* view=static_cast<unsigned char*>(MapViewOfFile(map,FILE_MAP_WRITE,0,0,mappingBytes));assert(view);
    std::memcpy(view,h.data(),h.size());std::memcpy(view+256,d.data(),d.size());std::memcpy(view+headerBytes,payload,32);
    {WorldFrames reader(name);WorldFrame received;assert(reader.latest(received)&&received.generation==99);
        put(view,256,uint64_t(3));assert(!reader.latest(received));put(view,256,uint64_t(4));put(view,56,uint64_t(100));assert(reader.latest(received)&&received.generation==100);
        put(view,256+104,unixMillis()-2000);rejected([&]{reader.latest(received);});}
    // Race a real mapped producer against direct decoding. Every admitted frame
    // must be owned, wholly one publication, and carry that publication's ID.
    auto racing=colorDescriptor;put(racing.data(),24,uint32_t(1280));put(racing.data(),28,uint32_t(720));
    put(racing.data(),104,unixMillis());std::memcpy(view+256,racing.data(),racing.size());
    std::memset(view+headerBytes,1,1280*720*4);
    std::atomic<bool> done{false};unsigned admitted=0;
    std::thread producer([&]{for(uint64_t frame=2;frame<=80;frame++){
        InterlockedExchange64(reinterpret_cast<volatile LONG64*>(view+256),LONG64(frame*2-1));
        put(view,256+8,frame);put(view,256+104,unixMillis());std::memset(view+headerBytes,int(frame),1280*720*4);
        InterlockedExchange64(reinterpret_cast<volatile LONG64*>(view+256),LONG64(frame*2));Sleep(2);
    }done=true;});
    {WorldFrames reader(name);WorldFrame received;uint64_t sequence=0;
        while(!done){if(reader.latest(received,100,sequence)){
            sequence=received.sequence;auto expected=static_cast<unsigned char>(received.mcFrame);
            assert(std::all_of(received.rgba.begin(),received.rgba.end(),[&](unsigned char byte){return byte==expected;}));admitted++;
        }}
        producer.join();assert(admitted>0);auto retained=received.rgba;std::memset(view+headerBytes,0,1280*720*4);assert(received.rgba==retained);
    }
    UnmapViewOfFile(view);CloseHandle(map);rejected([&]{WorldFrames gone(name);});
    FrameCompositor renderer;auto pixels=renderer.render(f);assert(pixels.rgba==f.rgba);
    rejected([&]{renderer.render(color);}); // Depth compositor must never invent depth for color-only frames.
    for(size_t i=0;i<f.depth.size();i++) assert(std::abs(pixels.depth[i]-f.depth[i])<1e-7f);
    // Asymmetric markers catch vertical flip, mirror, half-pixel shift and channel swapping.
    for(auto size:std::array<std::array<uint32_t,2>,4>{{{97,61},{16,8},{127,71},{97,61}}}) {
        auto m=marker(size[0],size[1]);auto out=renderer.render(m);assert(out.rgba==m.rgba&&out.depth==m.depth);
        verifyCpuWarp(m,p*cameraYaw(.20f)*p.inverse(),renderer.render(m,p*cameraYaw(.20f)*p.inverse()));
        verifyCpuWarp(m,p*cameraYaw(-.20f)*p.inverse(),renderer.render(m,p*cameraYaw(-.20f)*p.inverse()));
    }
    // Perspective endpoints must produce conventional D3D depth, not reversed-Z or GL clip z.
    auto nearClip=p.apply({0,0,-1,1}),farClip=p.apply({0,0,-100,1});assert(std::abs(nearClip[2]/nearClip[3]*.5f+.5f)<1e-6f);assert(std::abs(farClip[2]/farClip[3]*.5f+.5f-1)<1e-6f);
    auto checkMatrix=Matrix::fromColumnMajor(f.projection);for(int i=0;i<16;i++) assert(checkMatrix.m[i]==p.m[i]);
    auto sky=marker(97,61);std::fill(sky.depth.begin(),sky.depth.end(),1.f);
    auto skyWarp=p*cameraYaw(.20f)*p.inverse();auto skyOut=renderer.render(sky,skyWarp);verifyCpuWarp(sky,skyWarp,skyOut);
    // A source ray inside the sky frame must remain sky even when its finite
    // far-plane position would project past the rotated target far plane.
    auto skyPixel=(30*97+30)*4;assert(skyOut.rgba[skyPixel+3]==255);
    rejected([&]{renderer.render(f,Matrix{});});
    bool wrongThreadRejected=false;std::thread worker([&]{try {renderer.render(f);}catch(const std::exception&) {wrongThreadRejected=true;}});worker.join();assert(wrongThreadRejected);
    std::cout<<"PASS: strict native wire, row orientation, mapping restart/odd/stale/close, WARP RGBA/depth, +/- yaw CPU oracle, resize, singular matrix and context thread guard.\n";
}
