#include "../src/local_hero_spawn.hpp"
#include <cassert>
#include <iostream>
using namespace passthrough;
SpawnPairAbi* nativeFixture(SpawnerAbi* self,SpawnPairAbi* result) {
    assert(self->controller.resource==0x040000000000000eULL);
    assert(self->controller.hero==0x02e0000000000029ULL);
    assert(self->controller.loadLocal==1&&self->controller.loadPlayerInfo==1&&self->controller.movable==1&&self->controller.local==1);
    assert(self->controller.camera==2&&self->controller.aim==2&&self->controller.movement==2&&self->controller.filter==0);
    assert(self->model.resource==0x0400000000000225ULL&&self->model.backref==1);
    assert(self->model.health==1&&self->model.weapon==1&&self->model.fixScript==1);
    for(auto p:self->controller.emptyComponents) assert(!p);
    for(auto p:self->model.emptyComponents) assert(!p);
    self->controllerEntity=0x10000;self->modelEntity=0x20000;*result={self->controllerEntity,self->modelEntity};return result;
}
int main() {
    auto owner=localHeroSpawner(0x02e0000000000029ULL,0x0400000000000225ULL);
    auto pair=invokeOriginalSpawn(nativeFixture,owner);assert(pair.controller==0x10000&&pair.model==0x20000);
    bool refused=false;try {localHeroSpawner(7,9);}catch(const std::exception&) {refused=true;}assert(refused);
    refused=false;try {invokeOriginalSpawn(nullptr,owner);}catch(const std::exception&) {refused=true;}assert(refused);
    std::cout<<"PASS: measured source spawner ABI, empty cross-runtime vectors, native member return convention, original local/model flags and calibrated hero guard.\n";
}
