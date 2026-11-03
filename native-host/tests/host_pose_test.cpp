#include "../src/host_pose.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
std::array<float,136> scene() {
    std::array<float,136> f{};f[0]=-.8033332f;f[5]=1.4281478f;f[3]=1;f[10]=1.00005f;f[11]=1;f[14]=-.100005f;
    for(int i=0;i<4;i++) {f[16+i*5]=1;f[32+i*5]=1;}f[112]=1.f/1920;f[113]=1.f/1080;return f;
}
int main() {
    auto values=scene();HostPose pose;assert(poseFromScene(values,1920,1080,7,pose));
    assert(std::abs(pose.fov-70)<.001f&&pose.basis[0]==-1&&pose.basis[4]==1&&pose.basis[8]==-1);
    // Native identity view looks toward +Z; MC yaw 0 has right -X/up +Y/back -Z.
    assert(pose.basis[6]==0&&pose.basis[7]==0&&pose.basis[8]==-1);
    values[16]=2;assert(!poseFromScene(values,1920,1080,7,pose));values=scene();values[3]=0;assert(!poseFromScene(values,1920,1080,7,pose));
    {PosePublisher publisher(L"Local\\OWMCHostPoseTest");pose.flags=2;pose.movementBits=17;pose.inputActive=1;publisher.publish(pose);
        HANDLE h=OpenFileMappingW(FILE_MAP_READ,FALSE,L"Local\\OWMCHostPoseTest");assert(h);auto* p=static_cast<const unsigned char*>(MapViewOfFile(h,FILE_MAP_READ,0,0,4096));assert(p);
        assert(std::memcmp(p,"OWPOSE01",8)==0&&field<uint64_t>(p,64)==2&&field<uint64_t>(p,72)==7&&field<uint32_t>(p,88)==2&&field<float>(p,128)==-1);
        assert(field<uint32_t>(p,320)==2&&field<uint32_t>(p,324)==17&&field<uint32_t>(p,328)==1&&field<uint32_t>(p,332)==0);
        pose.inputCapabilities=0x31594544;publisher.publish(pose);assert(field<uint32_t>(p,332)==0x31594544);
        bool refused=false;try {PosePublisher duplicate(L"Local\\OWMCHostPoseTest");}catch(const std::exception&) {refused=true;}assert(refused);
        UnmapViewOfFile(p);CloseHandle(h);}
    assert(!OpenFileMappingW(FILE_MAP_READ,FALSE,L"Local\\OWMCHostPoseTest"));
    std::cout<<"PASS: observed camera basis/sign/FOV, invalid paired matrices, Win64 pose seqlock/layout/duplicate/close.\n";
}
