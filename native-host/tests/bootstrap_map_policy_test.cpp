#include "../src/bootstrap_map_policy.hpp"
#include <cassert>
#include <initializer_list>
int main(){
    using namespace owmc;
    static_assert(bootstrapMapAllowed(kyotoLoginMap)&&!bootstrapPatchesMap(kyotoLoginMap));
    assert(bootstrapMapPrepared(kyotoLoginMap,0,0,0));
    assert(!bootstrapMapPrepared(kyotoLoginMap,1,0,0));
    assert(bootstrapMapPrepared(hollywoodMap,0,0,1));
    assert(!bootstrapMapPrepared(hollywoodMap,0,0,0));
    assert(!bootstrapMapPrepared(hollywoodMap,0,0,2));
    assert(bootstrapMapPrepared(emptyLobbyMap,0,1,0));
    assert(!bootstrapMapPrepared(emptyLobbyMap,0,0,1));
    for(uint64_t id:{0ULL,0x08000000000001c2ULL,0x0800000000000665ULL}){
        assert(!bootstrapMapAllowed(id));assert(!bootstrapPatchesMap(id));assert(!bootstrapMapPrepared(id,0,1,1));
    }
}
