#include "../src/native_collision.hpp"
#include <cassert>
#include <cstring>
#include <iostream>

namespace {
alignas(16) std::array<unsigned char,0xd00> mover{};
alignas(16) std::array<unsigned char,0x1600> local{};
alignas(16) std::array<unsigned char,0x200> scene{};
struct alignas(16) Vector4 {float x,y,z,w;};
Vec3 desired{};unsigned setterCalls=0,buttons=0;
std::shared_ptr<CollisionFrame> patch=std::make_shared<CollisionFrame>();
template<class T> T get(unsigned char* data,size_t offset) {T value;std::memcpy(&value,data+offset,sizeof(value));return value;}
template<class T> void put(unsigned char* data,size_t offset,T value) {std::memcpy(data+offset,&value,sizeof(value));}
bool sample(HeroFrame& pose) {
    pose.foot=get<Vec3>(mover.data(),0xa50+0x220);pose.state1Foot=get<Vec3>(mover.data(),0x7e0+0x220);
    pose.scene=get<Vec3>(scene.data(),0x60);pose.eye=get<Vec3>(local.data(),0x1500);pose.copiedEye=get<Vec3>(local.data(),0x1510);
    pose.velocity=get<Vec3>(mover.data(),0xa50+0x230);pose.gravity=get<Vec3>(mover.data(),0xa50+0x250);pose.flags=get<unsigned>(mover.data(),0xa50+0x198);
    pose.mover=reinterpret_cast<uintptr_t>(mover.data());pose.local=reinterpret_cast<uintptr_t>(local.data());pose.sceneAddress=reinterpret_cast<uintptr_t>(scene.data());pose.buttons=buttons;return true;
}
void place(Vec3 foot) {
    for(auto offset:{0x7e0,0xa50}) {
        put(mover.data(),offset+0x220,Vector4{foot.x,foot.y,foot.z,1234});
        put(mover.data(),offset+0x230,Vector4{1,-5,2,2345});put(mover.data(),offset+0x250,Vector4{0,-5,0,3456});
        put(mover.data(),offset+0x198,553u);put(mover.data(),offset+0x1a8,12);
    }
    put(scene.data(),0x40,Vector4{0,0,0,1});put(scene.data(),0x60,Vector4{foot.x,foot.y,foot.z,1});
    put(local.data(),0x1500,Vector4{foot.x,foot.y+1.2f,foot.z,4567});put(local.data(),0x1510,Vector4{foot.x,foot.y+1.2f,foot.z,5678});
}
uintptr_t WINAPI nativeTick(void*,UINT cf) {place(desired);return 0x12340000+cf;}
void WINAPI other(void*) {}
void WINAPI sceneSetter(void* object,const Vector4* rotation,const Vector4* position) {
    assert(object==scene.data()&&rotation->w==1&&position->w==1);++setterCalls;put(scene.data(),0x60,*position);
}
std::shared_ptr<const CollisionFrame> source() {return patch;}
}
int main() {
    patch->origin={0,0,0};patch->blocks={{0,-1,0,1},{3,0,0,1},{3,1,0,1}};patch->received=GetTickCount64();patch->session=1;patch->sequence=1;
    void* table[]{reinterpret_cast<void*>(nativeTick),reinterpret_cast<void*>(other),reinterpret_cast<void*>(other)};
    struct Object {void** table;} object{table};
    assert(attachCollisionTest(&object,sample,nullptr,source,reinterpret_cast<void*>(sceneSetter)));
    auto tick=reinterpret_cast<uintptr_t(WINAPI*)(void*,UINT)>(object.table[0]);
    place({2.6f,0,.5f});desired={2.76f,0,.5f};assert(tick(&object,7)==0x12340007);
    HeroFrame pose;sample(pose);assert(std::abs(pose.foot.x-2.7f)<.0001f&&pose.state1Foot.x==pose.foot.x&&pose.scene.x==pose.foot.x
        &&pose.eye.x==pose.foot.x&&pose.copiedEye.x==pose.foot.x&&pose.velocity.x==0);
    place({.5f,.04f,.5f});desired={.5f,-.12f,.5f};tick(&object,8);sample(pose);
    assert(std::abs(pose.foot.y)<.0001f&&pose.scene.y==pose.foot.y&&std::abs(pose.eye.y-1.2f)<.0001f
        &&pose.velocity.y==0&&pose.gravity.y==0&&(pose.flags&0x8d)==0);
    assert(get<float>(mover.data(),0x7e0+0x22c)==1234&&get<float>(mover.data(),0xa50+0x23c)==2345
        &&get<float>(mover.data(),0xa50+0x25c)==3456&&get<float>(local.data(),0x150c)==4567&&get<int>(mover.data(),0xa50+0x1a8)==0);
    place({.5f,0,.5f});desired={.5f,.16f,.5f};tick(&object,9);sample(pose);assert(pose.foot.y==.16f);
    patch->blocks.clear();place({2.6f,0,.5f});desired={2.76f,0,.5f};tick(&object,10);sample(pose);assert(pose.foot.x==2.76f);
    patch->blocks={{3,0,0,1}};patch->received=GetTickCount64()-3000;place({2.6f,0,.5f});tick(&object,11);sample(pose);assert(pose.foot.x==2.76f);
    patch->received=GetTickCount64();place({2.6f,0,.5f});desired={20,0,.5f};tick(&object,12);sample(pose);assert(pose.foot.x==20);
    auto stats=nativeCollisionStats();assert(stats.corrections==2&&stats.floors==1&&stats.walls==1&&stats.rejected==1&&stats.writeFailures==0&&setterCalls==2);
    patch->creative=true;patch->origin={0,40,0};patch->blocks={{0,-1,0,1}};
    place({.5f,0,.5f});desired={.5f,0,.5f};tick(&object,13);sample(pose);
    assert(std::abs(pose.foot.y-40.04f)<.0001f&&pose.state1Foot.y==pose.foot.y&&pose.scene.y==pose.foot.y
        &&std::abs(pose.eye.y-pose.foot.y-1.2f)<.0001f&&nativeCollisionStats().creativeEntered);
    // Stepping outside the finite island safely returns to spawn.
    place({20,40,.5f});desired={20,40,.5f};tick(&object,14);sample(pose);
    assert(pose.foot.x==.5f&&nativeCollisionStats().rescues==1&&nativeCollisionStats().writeFailures==0);
    patch->streamedWorld=true;place({128,40,96});desired={128,40,96};tick(&object,15);sample(pose);
    assert(pose.foot.x==128&&pose.foot.z==96&&nativeCollisionStats().rescues==1); // A real MC world has no island boundary.
    stopNativeCollision();assert(object.table==table&&!nativeCollisionStats().attached);
    std::cout<<"Native tick chaining/return, field-only pose correction, model/eyes, velocity/ground flags, W preservation, jump, block removal, stale transport, teleport and stop passed in owned fixture.\n";
}
