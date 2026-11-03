#pragma once
#include "guest_body.hpp"
#include <vector>

namespace passthrough {
struct BodyAddresses {uintptr_t mover=0,local=0,scene=0,presentationState=0;};
struct BodyField {uintptr_t address;size_t size;std::array<unsigned char,12> before{},after{};};
// Preflight all fields, preserve vector W/pointers/tick IDs, and roll back on a
// short/failed write. Scene transform is committed by the native owner thread.
template<class Reader,class Writer,class Setter>
bool applyGuestBody(BodyAddresses a,const GuestBody& s,Vec3 target,Reader read,Writer write,Setter setScene,float eyeHeight=1.2f,const Vec3* nativeGravity=nullptr) {
    if(!std::isfinite(eyeHeight)||eyeHeight<.5f||eyeHeight>2.5f)return false;
    std::vector<BodyField> fields;fields.reserve(16);
    auto add=[&](uintptr_t address,const auto& value){
        BodyField f{address,sizeof value,{},{}};
        if(f.size>12||!read(address,f.before.data(),f.size))return false;
        std::memcpy(f.after.data(),&value,f.size);fields.push_back(f);return true;
    };
    Vec4 rotation{},position{};
    if(!read(a.scene+0x40,&rotation,sizeof rotation)||!read(a.scene+0x60,&position,sizeof position))return false;
    for(auto offset:{0x7e0,0xa50}) {
        unsigned flags=0;if(!read(a.mover+offset+0x198,&flags,4))return false;
        Vec3 velocity=s.velocity,gravity{0,s.grounded?0:s.velocity.y,0};if(s.grounded)velocity.y=0;
        if(nativeGravity)gravity=s.grounded?Vec3{}:*nativeGravity;
        if(!add(a.mover+offset+0x220,target)||!add(a.mover+offset+0x230,velocity)||!add(a.mover+offset+0x250,gravity)
           ||!add(a.mover+offset+0x198,bodyFlags(flags,s)))return false;
        // Original TrackMovement (10aaa81..10aab55) requires flag80 AND
        // WallMove mode2..4 before publishing the animation condition04b4.
        if(!add(a.mover+offset+0x8c,static_cast<unsigned char>(s.climbing?2:0)))return false;
        if(s.grounded&&!add(a.mover+offset+0x1a8,0))return false;
    }
    if(a.presentationState){
        unsigned flags=0;if(!read(a.presentationState+0x198,&flags,4))return false;
        // The original script context getter d14af0 reads component12's current
        // presentation state; changing only the mover cannot reach animation.
        // TrackMovement also derives airborne/grounded from bits0x0c. Leaving
        // native falling here permanently prevents grounded skills such as roll.
        flags=bodyFlags(flags,s);
        if(!add(a.presentationState+0x198,flags)
          ||!add(a.presentationState+0x8c,static_cast<unsigned char>(s.climbing?2:0)))return false;
    }
    const Vec3 eye=target+Vec3{0,eyeHeight,0}; // Measured original hero camera height.
    if(!add(a.local+0x1500,eye)||!add(a.local+0x1510,eye))return false;
    for(size_t i=0;i<fields.size();i++)if(!write(fields[i].address,fields[i].after.data(),fields[i].size)) {
        for(size_t j=i+1;j>0;j--)write(fields[j-1].address,fields[j-1].before.data(),fields[j-1].size);
        return false;
    }
    position.x=target.x;position.y=target.y;position.z=target.z;setScene(a.scene,rotation,position);return true;
}
}
