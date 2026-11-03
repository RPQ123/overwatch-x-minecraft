#include "../src/voxel_collision.hpp"
#include <cassert>
#include <iostream>

int main() {
    CollisionBody prototype{.3f,1.8f};std::vector<BlockRecord> blocks{{0,-1,0,1},{3,0,0,1},{3,1,0,1}};
    auto landed=clipVoxels({.5f,2,.5f},{.5f,-2,.5f},{0,0,0},blocks,prototype);
    assert(landed.floor&&landed.position.y==0);
    auto wall=clipVoxels({.5f,0,.5f},{8,0,.5f},{0,0,0},blocks,prototype);
    assert(wall.wall&&std::abs(wall.position.x-2.7f)<.0001f);
    auto diagonal=clipVoxels({2,0,.5f},{4,0,2.5f},{0,0,0},blocks,prototype);
    assert(diagonal.wall&&diagonal.position.z==2.5f);
    auto jump=clipVoxels({.5f,0,.5f},{.5f,2,.5f},{0,0,0},blocks,prototype);
    assert(!jump.floor&&jump.position.y==2);
    auto removed=clipVoxels({.5f,0,.5f},{8,0,.5f},{0,0,0},{},prototype);
    assert(!removed.wall&&removed.position.x==8);
    auto shifted=clipVoxels({10.5f,12,10.5f},{10.5f,8,10.5f},{10,10,10},blocks,prototype);
    assert(shifted.floor&&shifted.position.y==10);
    std::vector<BlockRecord> platform{{1,-1,0,1}};
    auto step=walkVoxels({.5f,-.15f,.5f},{1.2f,-.15f,.5f},{0,0,0},platform,prototype,.4f);
    assert(step.floor&&step.position.x==1.2f&&std::abs(step.position.y)<.0001f);
    auto highWall=walkVoxels({.5f,0,.5f},{8,0,.5f},{0,0,0},blocks,prototype,.4f);
    assert(highWall.wall&&std::abs(highWall.position.x-2.7f)<.0001f);
    assert(overlapsVoxels({1.2f,-.15f,.5f},{0,0,0},platform,prototype));
    bool rejected=false;try {clipVoxels({NAN,0,0},{0,0,0},{0,0,0},blocks,prototype);} catch(const std::runtime_error&) {rejected=true;}assert(rejected);
    std::cout<<"Candidate cube collision: landing, high-speed wall, sliding, jump, removed block, origin and invalid pose passed. Native coupling is not implied.\n";
}
