#include "native_collision.hpp"
#include <array>
#include <atomic>
#include <filesystem>
#include "creative_motion.hpp"

namespace {
using Tick=uintptr_t(WINAPI*)(void*,UINT);
void* hooked=nullptr;void **original=nullptr,**copy=nullptr;
CollisionSource source=nullptr;
bool(*fixtureRead)(HeroFrame&)=nullptr;
bool(*fixtureWrite)(const HeroFrame&,Vec3,const CollisionResult&)=nullptr;
void* fixtureSceneSetter=nullptr;
std::atomic<bool> active{false};
std::atomic<unsigned> ticks{0},corrections{0},floors{0},walls{0},rejected{0},writeFailures{0};
std::atomic<bool> creativeEntered{false},flying{false};std::atomic<unsigned> rescues{0};
CreativeFlight flight;uint64_t creativeSession=0;
struct CachedHero {uintptr_t admin=0,controller=0,reference=0,model=0,mover=0,local=0,scene=0;unsigned localId=0,modelId=0;} cached;
template<class T> bool readAt(uintptr_t address,T& value) {
    SIZE_T count=0;return address>=0x10000&&address<0x7fffffffffffULL
        &&ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),&value,sizeof(value),&count)&&count==sizeof(value);
}
uintptr_t pointerAt(uintptr_t address) {uintptr_t result=0;return readAt(address,result)?result:0;}
uintptr_t entity(uintptr_t admin,unsigned id) {
    struct Slot {uintptr_t entry;int occupied,pad;};std::array<Slot,4096> table{};
    if(!readAt(pointerAt(admin+0x10),table)) return 0;
    for(const auto& slot:table) if(slot.occupied&&slot.entry) {
        struct Entry {unsigned id,pad;uintptr_t owner;} value{};
        if(readAt(slot.entry,value)&&value.id==id) return value.owner;
    }return 0;
}
uintptr_t component(uintptr_t owner,unsigned char wanted) {
    struct List {uintptr_t items;int count,capacity;} list{};
    if(!readAt(owner+0x50,list)||list.count<1||list.count>256||list.capacity<list.count||list.capacity>256) return 0;
    for(int i=0;i<list.count-1;i++) {
        auto item=pointerAt(list.items+i*8);unsigned char id=0;
        if(readAt(item+0x10,id)&&id==wanted&&pointerAt(item+8)==owner) return item;
    }return 0;
}
bool finite(Vec3 v) {return std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z)&&std::abs(v.x)<1e6&&std::abs(v.y)<1e6&&std::abs(v.z)<1e6;}
bool readHero(HeroFrame& frame) {
    if(fixtureRead) return fixtureRead(frame);
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointerAt(base+0x17b7f90);unsigned localId=0,modelId=0;
    if(!readAt(admin+0x220,localId)) return false;
    bool cachedValid=admin==cached.admin&&localId==cached.localId
        &&pointerAt(cached.reference+8)==cached.controller&&pointerAt(cached.mover+8)==cached.model
        &&pointerAt(cached.local+8)==cached.controller&&pointerAt(cached.scene+8)==cached.model;
    unsigned cachedModel=0;
    cachedValid=cachedValid&&readAt(cached.reference+0x94,cachedModel)&&cachedModel==cached.modelId;
    auto controller=cachedValid?cached.controller:entity(admin,localId),reference=cachedValid?cached.reference:component(controller,0x20);
    if(!readAt(reference+0x94,modelId)) return false;
    auto model=cachedValid?cached.model:entity(admin,modelId);
    frame.mover=cachedValid?cached.mover:component(model,0x15);frame.local=cachedValid?cached.local:component(controller,0x2f);frame.sceneAddress=cachedValid?cached.scene:component(model,1);
    if(frame.mover&&frame.local&&frame.sceneAddress) cached={admin,controller,reference,model,frame.mover,frame.local,frame.sceneAddress,localId,modelId};
    return frame.mover&&frame.local&&frame.sceneAddress
        &&readAt(frame.mover+0xa50+0x220,frame.foot)&&readAt(frame.mover+0x7e0+0x220,frame.state1Foot)
        &&readAt(frame.sceneAddress+0x60,frame.scene)&&readAt(frame.local+0x1500,frame.eye)&&readAt(frame.local+0x1510,frame.copiedEye)
        &&readAt(frame.mover+0xa50+0x230,frame.velocity)&&readAt(frame.mover+0xa50+0x250,frame.gravity)&&readAt(frame.mover+0xa50+0x198,frame.flags)
        &&readAt(frame.local+0x147a,*reinterpret_cast<unsigned short*>(&frame.buttons))
        &&finite(frame.foot)&&finite(frame.state1Foot)&&finite(frame.scene)&&finite(frame.eye)&&finite(frame.copiedEye)&&finite(frame.velocity)&&finite(frame.gravity)
        &&pointerAt(base+0x17b7f90)==admin;
}
bool writeHero(const HeroFrame& expected,Vec3 change,const CollisionResult& hit) {
    if(fixtureWrite) return fixtureWrite(expected,change,hit);
    HeroFrame current{};if(!readHero(current)||current.mover!=expected.mover||current.local!=expected.local||current.sceneAddress!=expected.sceneAddress
        ||dot(current.foot-expected.foot,current.foot-expected.foot)>.000001f) return false;
    struct alignas(16) Vector4 {float x,y,z,w;};Vector4 rotation{},position{};
    if(!readAt(current.sceneAddress+0x40,rotation)||!readAt(current.sceneAddress+0x60,position)) return false;
    // Preflight every field and retain originals; never copy whole movement states or their pointers.
    struct Field {uintptr_t address;std::array<unsigned char,12> before,after;size_t length;};
    std::array<Field,16> fields{};size_t count=0;
    auto add=[&](uintptr_t address,const auto& value) {
        if(count>=fields.size()) return false;auto& f=fields[count++];f.address=address;f.length=sizeof(value);
        if(f.length>f.before.size()||!readAt(address,f.before)) return false;
        std::memcpy(f.after.data(),&value,f.length);return true;
    };
    Vec3 velocity=current.velocity,gravity=current.gravity;
    if(std::abs(change.x)>.00001f) velocity.x=0;
    if(std::abs(change.z)>.00001f) velocity.z=0;
    if(hit.floor||hit.ceiling) {velocity.y=0;gravity.y=0;}
    unsigned flags=current.flags;
    // Actual trace: idle grounded=512, airborne includes bits 0/2/3/7;
    // keep unrelated ability/directional bits. Prototype only, not full native capsule registration.
    if(hit.floor) flags=(flags&~0x8du)|0x200u;
    for(auto offset:{0x7e0,0xa50}) {
        if(!add(current.mover+offset+0x220,(offset==0x7e0?current.state1Foot:current.foot)+change)
           ||!add(current.mover+offset+0x230,velocity)||!add(current.mover+offset+0x250,gravity)
           ||!add(current.mover+offset+0x198,flags)) return false;
        if(hit.floor&&!add(current.mover+offset+0x1a8,0)) return false;
    }
    if(!add(current.local+0x1500,current.eye+change)||!add(current.local+0x1510,current.copiedEye+change)) return false;
    auto write=[](const Field& f,bool restore){SIZE_T written=0;return WriteProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(f.address),
        restore?f.before.data():f.after.data(),f.length,&written)&&written==f.length;};
    size_t done=0;for(;done<count;done++) if(!write(fields[done],false)) {
        // Attempt restoration of even the partially written field before disabling coupling.
        for(size_t undo=done+1;undo>0;undo--) write(fields[undo-1],true);return false;
    }
    position.x+=change.x;position.y+=change.y;position.z+=change.z;
    using SetTransform=void(WINAPI*)(void*,const Vector4*,const Vector4*);
    auto setter=fixtureSceneSetter?fixtureSceneSetter:reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+0xa04000);
    reinterpret_cast<SetTransform>(setter)(reinterpret_cast<void*>(current.sceneAddress),&rotation,&position);
    return true;
}
uintptr_t WINAPI tick(void* object,UINT commandFrame) {
    HeroFrame before{};bool observed=active&&readHero(before);
    auto result=reinterpret_cast<Tick>(original[0])(object,commandFrame);
    if(!active||!observed) return result;
    ++ticks;auto world=source?source():nullptr;
    if(!world||GetTickCount64()-world->received>2000) return result;
    HeroFrame after{};
    if(!readHero(after)||before.mover!=after.mover||before.local!=after.local||before.sceneAddress!=after.sceneAddress) {++rejected;return result;}
    if(world->creative) {
        if(creativeSession!=world->session) {creativeEntered=false;creativeSession=world->session;flight={};flying=false;}
        bool outside=(!world->streamedWorld&&(std::abs(after.foot.x-world->origin.x)>15.6f||std::abs(after.foot.z-world->origin.z)>15.6f))||after.foot.y<world->origin.y-5;
        if(!creativeEntered||outside) {
            Vec3 desired=world->origin+Vec3{.5f,.04f,.5f};CollisionResult reset{desired,true,false,false};
            if(!writeHero(after,desired-after.foot,reset)) {++writeFailures;active=false;return result;}
            if(creativeEntered) ++rescues;creativeEntered=true;return result;
        }
        flight.update(after.buttons,GetTickCount64());flying=flight.enabled;
    }
    // Large native teleports/map changes do not become swept moves or carry an old collision origin.
    if(dot(after.foot-before.foot,after.foot-before.foot)>1.f) {++rejected;return result;}
    const CollisionBody prototype{.3f,1.8f};
    try {
        Vec3 desired=after.foot;
        if(world->creative&&flight.enabled) desired.y=std::min(world->origin.y+12,before.foot.y+flight.vertical(after.buttons));
        std::vector<BlockRecord> nearby;nearby.reserve(64);
        for(const auto& block:world->blocks) {
            Vec3 p=world->origin+Vec3{float(block.x),float(block.y),float(block.z)};
            if(p.x+1>=std::min(before.foot.x,desired.x)-.31f&&p.x<=std::max(before.foot.x,desired.x)+.31f
               &&p.z+1>=std::min(before.foot.z,desired.z)-.31f&&p.z<=std::max(before.foot.z,desired.z)+.31f
               &&p.y+1>=std::min(before.foot.y,desired.y)-.01f&&p.y<=std::max(before.foot.y,desired.y)+2.21f) nearby.push_back(block);
        }
        if(overlapsVoxels(before.foot,world->origin,nearby,prototype)) {++rejected;return result;}
        auto hit=walkVoxels(before.foot,desired,world->origin,nearby,prototype,.4f);
        auto change=hit.position-after.foot;
        if(dot(change,change)<.00000001f&&!(world->creative&&flight.enabled)) return result;
        if(dot(change,change)>1.f||!finite(change)) {++rejected;return result;}
        if(world->creative&&flight.enabled) hit.ceiling=true; // Freeze native vertical velocity/gravity while hovering.
        if(!writeHero(after,change,hit)) {++writeFailures;active=false;return result;}
        ++corrections;if(hit.floor) ++floors;if(hit.wall) ++walls;
    } catch(const std::exception&) {++rejected;active=false;}
    return result;
}
bool install(void* object) {
    if(hooked||!object) return false;hooked=object;original=*reinterpret_cast<void***>(object);
    copy=new void*[3]{reinterpret_cast<void*>(tick),original[1],original[2]};
    if(InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(object),copy,original)!=original) return false;
    active=true;return true;
}
}
bool attachNativeCollision(CollisionSource reader) {
    auto base=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr)),admin=pointerAt(base+0x17b7f90);
    struct List {uintptr_t items;int count,capacity;} list{};
    if(!reader||!readAt(admin+0xf0,list)||list.count<1||list.count>32||list.capacity<list.count||list.capacity>32) return false;
    const std::array<unsigned char,17> signature{0x48,0x8b,0xc4,0x48,0x89,0x58,0x18,0x55,0x56,0x57,0x48,0x81,0xec,0xa0,0,0,0};
    std::array<unsigned char,17> actual{};if(!readAt(base+0xa04000,actual)||actual!=signature) return false;
    for(int i=0;i<list.count;i++) {
        auto object=pointerAt(list.items+i*8);if(pointerAt(object)!=base+0x15c4e28) continue;
        std::array<uintptr_t,3> table{};
        if(!readAt(pointerAt(object),table)||table!=std::array<uintptr_t,3>{base+0xca0960,base+0xca0800,base+0xca09c0}) return false;
        source=reader;return install(reinterpret_cast<void*>(object));
    }return false;
}
void stopNativeCollision() {
    active=false;if(hooked) InterlockedCompareExchangePointer(reinterpret_cast<PVOID volatile*>(hooked),original,copy);
    // Retain the original/copy/code until process exit for any callback already in flight.
}
NativeCollisionStats nativeCollisionStats() {return {active,ticks,corrections,floors,walls,rejected,writeFailures,creativeEntered,flying,rescues};}
bool nativeHeroFoot(Vec3& foot) {HeroFrame hero{};if(!readHero(hero)) return false;foot=hero.foot;return true;}
bool attachCollisionTest(void* object,bool(*reader)(HeroFrame&),bool(*writer)(const HeroFrame&,Vec3,const CollisionResult&),CollisionSource world,void* setter) {
    wchar_t exe[32768]{};GetModuleFileNameW(nullptr,exe,32768);
    if(std::filesystem::path(exe).filename()!=L"owmc-collision-test.exe"||!reader||(!writer&&!setter)||!world) return false;
    fixtureRead=reader;fixtureWrite=writer;fixtureSceneSetter=setter;source=world;return install(object);
}
