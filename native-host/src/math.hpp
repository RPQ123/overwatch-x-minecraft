#pragma once
#include <cmath>
#include <stdexcept>

struct Vec3 { float x,y,z; };
struct Vec4 { float x,y,z,w; };
inline Vec3 operator+(Vec3 a,Vec3 b) { return {a.x+b.x,a.y+b.y,a.z+b.z}; }
inline Vec3 operator-(Vec3 a,Vec3 b) { return {a.x-b.x,a.y-b.y,a.z-b.z}; }
inline Vec3 operator*(Vec3 a,float b) { return {a.x*b,a.y*b,a.z*b}; }
inline float dot(Vec3 a,Vec3 b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
inline Vec3 cross(Vec3 a,Vec3 b) { return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x}; }
inline Vec3 normalized(Vec3 a) { float n=std::sqrt(dot(a,a)); if(n<.001f) throw std::runtime_error("Degenerate basis"); return a*(1/n); }
struct Camera { Vec3 position,forward,up; float verticalFov; };
struct NativeProjection {
    float worldToView[16],viewToClip[16];
    float left,top,right,bottom;
};
inline bool validProjection(const NativeProjection& p) {
    for(float value:p.worldToView) if(!std::isfinite(value)) return false;
    for(float value:p.viewToClip) if(!std::isfinite(value)) return false;
    return std::isfinite(p.left)&&std::isfinite(p.top)&&std::isfinite(p.right)&&std::isfinite(p.bottom)
        &&p.left>=0&&p.top>=0&&p.right>p.left&&p.bottom>p.top&&p.right<=16384&&p.bottom<=16384
        && std::abs(p.worldToView[15]-1)<.001f && std::abs(p.viewToClip[11]-1)<.001f
        && std::abs(p.viewToClip[15])<.001f && std::abs(p.viewToClip[0])>.01f
        && std::abs(p.viewToClip[5])>.01f;
}
inline Vec4 transform(Vec4 v,const float* matrix) {
    return {v.x*matrix[0]+v.y*matrix[4]+v.z*matrix[8]+v.w*matrix[12],
            v.x*matrix[1]+v.y*matrix[5]+v.z*matrix[9]+v.w*matrix[13],
            v.x*matrix[2]+v.y*matrix[6]+v.z*matrix[10]+v.w*matrix[14],
            v.x*matrix[3]+v.y*matrix[7]+v.z*matrix[11]+v.w*matrix[15]};
}
inline Vec4 projectNativeValidated(Vec3 point,const NativeProjection& p,float width,float height) {
    Vec4 clip=transform(transform({point.x,point.y,point.z,1},p.worldToView),p.viewToClip);
    clip.x=clip.x*(p.right-p.left)/width+clip.w*((p.right+p.left)/width-1);
    clip.y=clip.y*(p.bottom-p.top)/height+clip.w*(1-(p.bottom+p.top)/height);
    return clip;
}
inline Vec4 projectNative(Vec3 point,const NativeProjection& p,float width,float height) {
    if(!validProjection(p)||width<=0||height<=0||p.right>width||p.bottom>height)
        throw std::runtime_error("Invalid native projection/viewport");
    return projectNativeValidated(point,p,width,height);
}
inline bool validCamera(const Camera& c) {
    return std::isfinite(c.verticalFov) && c.verticalFov>.1f && c.verticalFov<3.f
        && std::abs(dot(c.forward,c.forward)-1)<.03f && std::abs(dot(c.up,c.up)-1)<.03f
        && std::abs(dot(c.forward,c.up))<.03f
        && std::isfinite(c.position.x) && std::isfinite(c.position.y) && std::isfinite(c.position.z);
}
inline Vec4 project(Vec3 point,const Camera& c,float aspect) {
    if(!validCamera(c) || aspect<=0) throw std::runtime_error("Invalid camera projection candidate");
    Vec3 relative=point-c.position, right=normalized(cross(c.up,c.forward));
    float depth=dot(relative,c.forward), scale=1/std::tan(c.verticalFov/2);
    constexpr float nearPlane=.05f,farPlane=1000.f;
    return {dot(relative,right)*scale/aspect,dot(relative,c.up)*scale,
            depth*farPlane/(farPlane-nearPlane)-nearPlane*farPlane/(farPlane-nearPlane),depth};
}
