#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
#include <stdexcept>

namespace passthrough {
// Layout measured against the supplied plugin's matching PDB and disassembly.
// Empty vector storage only: no allocation crosses C++ runtimes.
struct SpawnInfoAbi {
    uint64_t resource=0,skin=0,hero=0;
    uint8_t loadLocal=0,loadPlayerInfo=0;
    std::array<uint8_t,6> padding{};
    std::array<uintptr_t,3> emptyComponents{};
    int32_t camera=0,aim=0,movement=0,backref=0,team=-1;
    uint8_t health=0,movable=0,local=0,filter=0,weapon=0,fixScript=0;
    std::array<uint8_t,6> tail{};
};
struct SpawnerAbi {
    SpawnInfoAbi controller,model;
    uintptr_t controllerEntity=0,modelEntity=0;
};
struct SpawnPairAbi {uintptr_t controller=0,model=0;};
static_assert(sizeof(SpawnInfoAbi)==0x58);
static_assert(offsetof(SpawnInfoAbi,emptyComponents)==0x20);
static_assert(offsetof(SpawnInfoAbi,camera)==0x38);
static_assert(offsetof(SpawnInfoAbi,weapon)==0x50);
static_assert(offsetof(SpawnerAbi,model)==0x58);
static_assert(offsetof(SpawnerAbi,controllerEntity)==0xb0);
static_assert(sizeof(SpawnerAbi)==0xc0);

inline SpawnerAbi localHeroSpawner(uint64_t hero,uint64_t model) {
    if(hero!=0x02e0000000000029ULL||model!=0x0400000000000225ULL) throw std::runtime_error("Only the observed Genji resource pair is calibrated");
    SpawnerAbi result;
    result.controller.resource=0x040000000000000eULL;
    result.controller.hero=hero;result.controller.loadLocal=1;result.controller.loadPlayerInfo=1;
    result.controller.camera=2;result.controller.aim=2;result.controller.movement=2;
    result.controller.local=1;result.controller.movable=1;
    result.model.resource=model;result.model.hero=hero;result.model.backref=1;
    result.model.health=1;result.model.weapon=1;result.model.fixScript=1;
    return result;
}
// The measured MSVC member function uses RCX=self, RDX=hidden pair result.
using OriginalSpawnFn=SpawnPairAbi*(*)(SpawnerAbi*,SpawnPairAbi*);
inline SpawnPairAbi invokeOriginalSpawn(OriginalSpawnFn function,SpawnerAbi& owner) {
    if(!function) throw std::runtime_error("No original spawner");
    SpawnPairAbi result;
    if(function(&owner,&result)!=&result||!result.controller||!result.model||result.controller!=owner.controllerEntity||result.model!=owner.modelEntity) throw std::runtime_error("Original spawner returned incomplete entities");
    return result;
}
}
