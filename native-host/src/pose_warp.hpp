#pragma once
#include "host_pose.hpp"
#include "frame_compositor.hpp"

namespace passthrough {
inline Matrix poseView(const HostPose& pose) {
    auto view=Matrix::identity();
    for(int r=0;r<3;r++) for(int c=0;c<3;c++) view.m[r*4+c]=pose.basis[r*3+c];
    return view;
}
inline Matrix hostProjection(const WorldFrame& image,const HostPose& target) {
    if(!std::isfinite(target.fx)||!std::isfinite(target.fy)||target.fx<=0||target.fy<=0||image.nearPlane<=0||image.farPlane<=image.nearPlane)throw std::runtime_error("Invalid held image lens");
    Matrix projection;projection.m[0]=target.fx;projection.m[5]=target.fy;
    projection.m[10]=(image.farPlane+image.nearPlane)/(image.nearPlane-image.farPlane);
    projection.m[11]=2*image.farPlane*image.nearPlane/(image.nearPlane-image.farPlane);projection.m[14]=-1;
    return projection;
}
// Hold the old image's orientation while preserving the native lens crop.
// Identity exposes the guest's wider overscan and changes the block scale.
inline Matrix heldImageWarp(const WorldFrame& image,const HostPose& target) {
    return Matrix::fromColumnMajor(image.projection)*hostProjection(image,target).inverse();
}
inline Matrix poseWarp(const WorldFrame& image,const HostPose& source,const HostPose& target) {
    if(image.hostFrame!=source.frame||image.hostGeneration!=source.generation||source.generation!=target.generation||!source.generation||
       source.flags!=target.flags||source.width!=target.width||source.height!=target.height||target.fx<=0||target.fy<=0) throw std::runtime_error("Unpaired live warp poses");
    // Position is owned by MC. Rotation uses the actual source image's paired pose.
    auto targetProjection=hostProjection(image,target);
    return Matrix::fromColumnMajor(image.projection)*poseView(source)*poseView(target).inverse()*targetProjection.inverse();
}
inline bool warpCoversView(const Matrix& warp) {
    for(float x:{-1.f,1.f}) for(float y:{-1.f,1.f}) {auto p=warp.apply({x,y,-1,1});
        if(p[3]<=0||std::abs(p[0])>p[3]||std::abs(p[1])>p[3]) return false;}
    return true;
}
// Every coverage constraint is linear in the blend fraction. Limit the entire
// homography once; per-pixel identity fallbacks mix two camera orientations.
inline Matrix coverageLimitedWarp(const Matrix& base,const Matrix& desired,float* applied=nullptr) {
    for(float v:desired.m)if(!std::isfinite(v))throw std::runtime_error("Nonfinite requested warp");
    if(!warpCoversView(base))throw std::runtime_error("Uncovered hold lens");
    if(warpCoversView(desired)){if(applied)*applied=1;return desired;}
    double fraction=1;
    for(float x:{-1.f,1.f})for(float y:{-1.f,1.f}) {
        auto a=base.apply({x,y,-1,1}),b=desired.apply({x,y,-1,1});
        std::array<double,5> qa={a[3]-1e-5,a[3]-a[0],a[3]+a[0],a[3]-a[1],a[3]+a[1]};
        std::array<double,5> qb={b[3]-1e-5,b[3]-b[0],b[3]+b[0],b[3]-b[1],b[3]+b[1]};
        for(size_t i=0;i<qa.size();i++)if(qb[i]<0)fraction=std::min(fraction,std::max(0.0,qa[i]/(qa[i]-qb[i])));
    }
    float t=float(fraction*.9999);Matrix result;
    for(int i=0;i<16;i++)result.m[i]=base.m[i]+t*(desired.m[i]-base.m[i]);
    if(!warpCoversView(result)){result=base;t=0;} // Guard float cancellation near a horizon.
    if(applied)*applied=t;
    return result;
}
}
