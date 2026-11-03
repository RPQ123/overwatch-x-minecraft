#pragma once
#include "math.hpp"
#include "mesh.hpp"
#include <algorithm>

// Candidate full-cube consumer. Native hero shape dimensions are a separate
// calibration gate; this solver alone is not an installed OW collider.
struct CollisionBody { float radius,height; };
struct CollisionResult { Vec3 position;bool floor=false,wall=false,ceiling=false; };
inline bool overlapsVoxels(Vec3 feet,Vec3 origin,const std::vector<BlockRecord>& blocks,CollisionBody shape) {
    for(const auto& b:blocks) {
        Vec3 low=origin+Vec3{float(b.x),float(b.y),float(b.z)};
        if(feet.x+shape.radius>low.x+.0001f&&feet.x-shape.radius<low.x+1-.0001f
           &&feet.y+shape.height>low.y+.0001f&&feet.y<low.y+1-.0001f
           &&feet.z+shape.radius>low.z+.0001f&&feet.z-shape.radius<low.z+1-.0001f) return true;
    }return false;
}
inline CollisionResult clipVoxels(Vec3 start,Vec3 desired,Vec3 origin,const std::vector<BlockRecord>& blocks,CollisionBody shape) {
    auto finite=[](Vec3 p){return std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z);};
    if(!finite(start)||!finite(desired)||!finite(origin)||!std::isfinite(shape.radius)||!std::isfinite(shape.height)
       ||shape.radius<=0||shape.radius>2||shape.height<=0||shape.height>4||blocks.size()>12288)
        throw std::runtime_error("Invalid collision candidate");
    Vec3 p=start,delta=desired-start;CollisionResult result{};
    for(int axis:{1,0,2}) {
        float movement=axis==0?delta.x:axis==1?delta.y:delta.z;
        float low[3]{p.x-shape.radius,p.y,p.z-shape.radius},high[3]{p.x+shape.radius,p.y+shape.height,p.z+shape.radius};
        float clipped=movement;
        for(const auto& b:blocks) {
            float lower[3]{origin.x+b.x,origin.y+b.y,origin.z+b.z},upper[3]{lower[0]+1,lower[1]+1,lower[2]+1};
            bool overlap=true;
            for(int other=0;other<3;other++) if(other!=axis && (high[other]<=lower[other]+.00001f||low[other]>=upper[other]-.00001f)) overlap=false;
            if(!overlap) continue;
            if(movement>0&&high[axis]<=lower[axis]+.00001f) clipped=std::min(clipped,std::max(0.f,lower[axis]-high[axis]));
            if(movement<0&&low[axis]>=upper[axis]-.00001f) clipped=std::max(clipped,std::min(0.f,upper[axis]-low[axis]));
        }
        if(std::abs(clipped-movement)>.00001f) {
            if(axis==1) { result.floor=movement<0;result.ceiling=movement>0; } else result.wall=true;
        }
        if(axis==0) p.x+=clipped;else if(axis==1) p.y+=clipped;else p.z+=clipped;
    }
    result.position=p;return result;
}
inline CollisionResult walkVoxels(Vec3 start,Vec3 desired,Vec3 origin,const std::vector<BlockRecord>& blocks,CollisionBody shape,float stepHeight) {
    auto normal=clipVoxels(start,desired,origin,blocks,shape);
    if(!normal.wall||stepHeight<=0||stepHeight>.5f||desired.y-start.y>.05f) return normal;
    auto raised=clipVoxels(start,start+Vec3{0,stepHeight,0},origin,blocks,shape);
    auto across=clipVoxels(raised.position,{desired.x,raised.position.y,desired.z},origin,blocks,shape);
    auto down=clipVoxels(across.position,{across.position.x,desired.y,across.position.z},origin,blocks,shape);
    auto progress=[&](Vec3 p){return (p.x-start.x)*(p.x-start.x)+(p.z-start.z)*(p.z-start.z);};
    if(down.floor&&!overlapsVoxels(down.position,origin,blocks,shape)&&progress(down.position)>progress(normal.position)+.000001f) {
        down.wall=across.wall;return down;
    }return normal;
}
