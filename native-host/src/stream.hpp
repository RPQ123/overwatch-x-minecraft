#pragma once
#include "mesh.hpp"

struct SnapshotOrder {
    uint64_t session=0,sequence=0,produced=0;
    bool accept(const Mesh& mesh,uint64_t now) {
        if(!mesh.session||!mesh.sequence||!mesh.producedEpochMillis) return false;
        uint64_t age=now>=mesh.producedEpochMillis?now-mesh.producedEpochMillis:mesh.producedEpochMillis-now;
        if(age>2000 || (mesh.session==session&&mesh.sequence<=sequence)
            ||(mesh.session!=session&&mesh.producedEpochMillis<produced)) return false;
        session=mesh.session;sequence=mesh.sequence;produced=mesh.producedEpochMillis;return true;
    }
};
