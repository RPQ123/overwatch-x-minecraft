#pragma once
#include "voxel_collision.hpp"
#include <memory>
#include <windows.h>

struct CollisionFrame {
    Vec3 origin;std::vector<BlockRecord> blocks;
    ULONGLONG received;uint64_t session,sequence;
    bool creative=false;
    bool streamedWorld=false;
};
using CollisionSource=std::shared_ptr<const CollisionFrame>(*)();
struct HeroFrame {
    Vec3 foot,state1Foot,scene,eye,copiedEye,velocity,gravity;
    unsigned flags=0;uintptr_t mover=0,local=0,sceneAddress=0;
    unsigned buttons=0;
};
struct NativeCollisionStats { bool attached;unsigned ticks,corrections,floors,walls,rejected,writeFailures;bool creativeEntered,flying;unsigned rescues; };
bool attachNativeCollision(CollisionSource source);
void stopNativeCollision();
NativeCollisionStats nativeCollisionStats();
bool nativeHeroFoot(Vec3& foot);
// Only accepted in the owned native-host test executable.
bool attachCollisionTest(void* object,bool(*read)(HeroFrame&),bool(*write)(const HeroFrame&,Vec3,const CollisionResult&),CollisionSource source,void* testSceneSetter=nullptr);
