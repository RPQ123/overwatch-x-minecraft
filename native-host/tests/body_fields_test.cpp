#include "../src/body_fields.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
int main(){
    std::array<unsigned char,0x4000> bytes{};BodyAddresses a{0x10000,0x11000,0x13000,0x13800};
    auto read=[&](uintptr_t p,void* dst,size_t n){if(p<0x10000||p+n>0x14000)return false;std::memcpy(dst,bytes.data()+p-0x10000,n);return true;};
    unsigned writes=0,failAt=0;
    auto write=[&](uintptr_t p,const void* src,size_t n){if(++writes==failAt)return false;std::memcpy(bytes.data()+p-0x10000,src,n);return true;};
    auto put=[&](uintptr_t p,const auto& v){std::memcpy(bytes.data()+p-0x10000,&v,sizeof v);};
    for(auto off:{0x7e0,0xa50}){
        put(a.mover+off+0x220,Vec4{0,-9000,0,123});put(a.mover+off+0x230,Vec4{0,-30,0,456});
        put(a.mover+off+0x250,Vec4{0,-30,0,789});put(a.mover+off+0x198,0x28u);put(a.mover+off+0x1a8,200);
    }
    put(a.local+0x1500,Vec4{0,-8998.8f,0,234});put(a.local+0x1510,Vec4{0,-8998.8f,0,345});
    put(a.scene+0x40,Vec4{0,0,0,1});put(a.scene+0x60,Vec4{0,-9000,0,1});
    put(a.presentationState+0x198,0x10020u);
    auto baseline=bytes;GuestBody s;s.grounded=true;bool sceneCalled=false;
    auto setter=[&](uintptr_t p,Vec4 r,Vec4 v){assert(p==a.scene&&r.w==1&&v.w==1&&v.y==1000);sceneCalled=true;};
    assert(applyGuestBody(a,s,{1000,1000,1000},read,write,setter)&&sceneCalled);
    for(auto off:{0x7e0,0xa50}){Vec4 p{},v{};read(a.mover+off+0x220,&p,16);read(a.mover+off+0x230,&v,16);assert(p.y==1000&&p.w==123&&v.y==0&&v.w==456);}
    for(unsigned fail=1;fail<=16;fail++){
        bytes=baseline;writes=0;failAt=fail;sceneCalled=false;
        assert(!applyGuestBody(a,s,{1000,1000,1000},read,write,setter)&&bytes==baseline&&!sceneCalled);
    }
    failAt=0;
    s.grounded=false;s.climbing=true;
    bytes=baseline;writes=0;sceneCalled=false;
    assert(applyGuestBody(a,s,{1000,1000,1000},read,write,setter));
    for(auto off:{0x7e0,0xa50}){
        unsigned char mode=0;unsigned flags=0;read(a.mover+off+0x8c,&mode,1);read(a.mover+off+0x198,&flags,4);
        assert(mode==2&&(flags&0x80));
        assert(std::memcmp(bytes.data()+off+0x70,baseline.data()+off+0x70,28)==0);
    }
    unsigned presentationFlags=0;unsigned char presentationMode=0;
    read(a.presentationState+0x198,&presentationFlags,4);read(a.presentationState+0x8c,&presentationMode,1);
    assert(presentationFlags==0x100a8u&&presentationMode==2);
    for(size_t i=0;i<0x268;i++)if(i!=0x8c&&(i<0x198||i>=0x19c))
        assert(bytes[a.presentationState-0x10000+i]==baseline[a.presentationState-0x10000+i]);
    s.climbing=false;
    assert(applyGuestBody(a,s,{1000,1000,1000},read,write,setter));
    read(a.presentationState+0x198,&presentationFlags,4);read(a.presentationState+0x8c,&presentationMode,1);
    assert(presentationFlags==0x10028u&&presentationMode==0);
    s.climbing=true;
    for(unsigned fail=1;fail<=14;fail++){
        bytes=baseline;writes=0;failAt=fail;sceneCalled=false;
        assert(!applyGuestBody(a,s,{1000,1000,1000},read,write,setter)&&bytes==baseline&&!sceneCalled);
    }
    failAt=0;s.climbing=false;s.grounded=true;
    for(float height:{1.2f,1.55f,1.5f}){
        bytes=baseline;writes=0;sceneCalled=false;
        assert(applyGuestBody(a,s,{1000,1000,1000},read,write,setter,height));
        Vec4 eye{},previous{};read(a.local+0x1500,&eye,16);read(a.local+0x1510,&previous,16);
        assert(std::abs(eye.y-1000-height)<.0001f&&eye.y==previous.y&&eye.w==234&&previous.w==345);
        read(a.presentationState+0x198,&presentationFlags,4);
        assert(presentationFlags==0x10220u); // Native grounded condition sees no air bits.
    }
    bytes=baseline;writes=0;
    assert(!applyGuestBody(a,s,{1000,1000,1000},read,write,setter,0)&&writes==0&&bytes==baseline);
    std::cout<<"Body writes preserve W, set both histories/eyes, reset ground speed, and roll back every injected field-write failure.\n";
}
