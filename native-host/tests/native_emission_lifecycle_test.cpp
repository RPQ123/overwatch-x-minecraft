#include <windows.h>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iostream>
namespace {
alignas(16) std::array<unsigned char,0x400> model{},entity{},scene{},modelScene{},projectile{},context{};
std::array<unsigned char,0x400> adminData{},controller{},reference{},heroInfo{},otherModel{},newModel{},newScene{};
struct Slot{uintptr_t entry;int used,pad;};std::array<Slot,4096> slots{};
struct Entry{uint32_t id,pad;uintptr_t owner;};std::array<Entry,2> entries{};
std::array<uintptr_t,3> controllerComponents{};std::array<uintptr_t,2> newComponents{};
std::array<uintptr_t,3> projectileComponents{};std::array<uintptr_t,2> modelComponents{};
std::array<uintptr_t,2> otherComponents{};std::array<unsigned char,0x400> otherScene{},config{};
std::array<unsigned char,256> guestBody{};
template<class Array,class T>void put(Array& array,size_t at,T value){std::memcpy(array.data()+at,&value,sizeof value);}
unsigned originalCalls=0;
unsigned beamOriginalCalls=0;
using BeamCall=uintptr_t(WINAPI*)(void*);
std::array<void*,0x160/8> beamTable{};
using Factory=uintptr_t(WINAPI*)(uintptr_t,uintptr_t,uintptr_t,uintptr_t);
void select(uint32_t localId,uint32_t modelId,uintptr_t modelPtr,uint64_t hero){
    put(adminData,0x220,localId);put(controller,0x94,localId);put(reference,0x94,modelId);put(heroInfo,0x98,hero);
    entries={Entry{localId,0,reinterpret_cast<uintptr_t>(controller.data())},Entry{modelId,0,modelPtr}};
}
}
extern "C" __declspec(noinline) uintptr_t WINAPI fixtureFactory(uintptr_t a,uintptr_t b,uintptr_t c,uintptr_t d){
    assert(a==0x1234&&b==reinterpret_cast<uintptr_t>(entity.data())&&c==reinterpret_cast<uintptr_t>(context.data())&&d==0xabcdef1234567801ULL);++originalCalls;
    uintptr_t owner=0;uint32_t ownerId=0;std::memcpy(&owner,context.data()+8,8);std::memcpy(&ownerId,reinterpret_cast<void*>(owner+0x94),4);
    put(projectile,0x18,ownerId);put(projectile,0x40,42.f);put(projectile,0x44,43.f);put(projectile,0x48,44.f);put(projectile,0x58,60.f);
    return 0xabcdef654321ULL;
}
extern "C" __declspec(noinline) uintptr_t WINAPI fixturePelletFactory(uintptr_t a,uintptr_t b,uintptr_t c,uintptr_t d){
    assert(a==0x1234&&b==reinterpret_cast<uintptr_t>(context.data())&&d==0xabcdef1234567801ULL);
    *reinterpret_cast<uint32_t*>(c)=8;return 0;
}
uintptr_t WINAPI fixtureBeamBegin(void* object){assert(object==context.data());++beamOriginalCalls;return 0x123456789abcdef0ULL;}
uintptr_t WINAPI fixtureBeamEnd(void* object){assert(object==context.data());++beamOriginalCalls;return 0xfedcba9876543210ULL;}
int main(int argc,char** argv){
    uintptr_t admin=reinterpret_cast<uintptr_t>(adminData.data()),modelPtr=reinterpret_cast<uintptr_t>(model.data()),entityPtr=reinterpret_cast<uintptr_t>(entity.data());
    uintptr_t controllerPtr=reinterpret_cast<uintptr_t>(controller.data()),newPtr=reinterpret_cast<uintptr_t>(newModel.data());
    put(adminData,0x10,reinterpret_cast<uintptr_t>(slots.data()));for(int i=0;i<2;i++)slots[i]={reinterpret_cast<uintptr_t>(&entries[i]),1,0};
    controllerComponents={reinterpret_cast<uintptr_t>(reference.data()),reinterpret_cast<uintptr_t>(heroInfo.data()),0};
    put(controller,0x28,admin);put(controller,0x50,reinterpret_cast<uintptr_t>(controllerComponents.data()));put(controller,0x58,3);put(controller,0x5c,3);
    put(reference,8,controllerPtr);put(reference,0x10,uint8_t(0x20));put(heroInfo,8,controllerPtr);put(heroInfo,0x10,uint8_t(0x3f));
    select(2,3,modelPtr,0x02e0000000000029ULL);
    put(model,0x28,admin);put(model,0x94,3u);put(entity,0x28,admin);put(entity,0x94,9u);
    projectileComponents={reinterpret_cast<uintptr_t>(scene.data()),reinterpret_cast<uintptr_t>(projectile.data()),0};
    modelComponents={reinterpret_cast<uintptr_t>(modelScene.data()),0};
    put(entity,0x50,reinterpret_cast<uintptr_t>(projectileComponents.data()));put(entity,0x58,3);put(entity,0x5c,3);
    put(model,0x50,reinterpret_cast<uintptr_t>(modelComponents.data()));put(model,0x58,2);put(model,0x5c,2);
    put(scene,8,entityPtr);put(scene,0x10,uint8_t(1));put(projectile,8,entityPtr);put(projectile,0x10,uint8_t(0x27));put(projectile,0x18,3u);
    put(modelScene,8,modelPtr);put(modelScene,0x10,uint8_t(1));
    put(context,8,modelPtr);put(context,0x28,uint64_t(0x04000000000007ca));put(context,0x60,42.f);put(context,0x64,43.f);put(context,0x68,44.f);put(context,0x78,1.f);
    auto library=LoadLibraryW(L"overwatch-2015/Overwatch Beta 0.8.0.24919/minhook.x64.dll");assert(library);
    auto dll=LoadLibraryA(argc==2?argv[1]:"native-host/build/owmc-native-emission-v16.dll");assert(dll);
    union{FARPROC raw;BOOL(*value)(uintptr_t,uintptr_t,HMODULE,uintptr_t);} attach{GetProcAddress(dll,"OWMC_EmissionTestAttach")};
    union{FARPROC raw;BOOL(*value)();} stop{GetProcAddress(dll,"OWMC_EmissionTestStop")};assert(attach.raw&&stop.raw);
    union{FARPROC raw;BOOL(*value)();} rebind{GetProcAddress(dll,"OWMC_EmissionTestRebind")};assert(rebind.raw);
    union{FARPROC raw;BOOL(*value)(const unsigned char*);} setBody{GetProcAddress(dll,"OWMC_EmissionTestBody")};assert(setBody.raw);
    union{FARPROC raw;BOOL(*value)(void**);} setBeam{GetProcAddress(dll,"OWMC_EmissionTestBeamTable")};assert(setBeam.raw);
    auto target=reinterpret_cast<uintptr_t>(fixtureFactory);std::array<unsigned char,24> before{},after{};std::memcpy(before.data(),reinterpret_cast<void*>(target),24);
    auto pelletTarget=reinterpret_cast<uintptr_t>(fixturePelletFactory);std::array<unsigned char,24> pelletBefore{},pelletAfter{};std::memcpy(pelletBefore.data(),reinterpret_cast<void*>(pelletTarget),24);
    assert(attach.value(target,modelPtr,library,pelletTarget));Factory volatile call=fixtureFactory;
    beamTable[0x110/8]=reinterpret_cast<void*>(fixtureBeamBegin);beamTable[0x158/8]=reinterpret_cast<void*>(fixtureBeamEnd);
    assert(setBeam.value(beamTable.data()));
    assert(reinterpret_cast<BeamCall>(beamTable[0x110/8])(context.data())==0x123456789abcdef0ULL);
    assert(reinterpret_cast<BeamCall>(beamTable[0x158/8])(context.data())==0xfedcba9876543210ULL&&beamOriginalCalls==2);
    assert(call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL)==0xabcdef654321ULL&&originalCalls==1);
    // Duplicate callbacks and departed/non-Genji models never enter the journal.
    call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL);
    auto otherPtr=reinterpret_cast<uintptr_t>(otherModel.data());put(otherModel,0x28,admin);put(otherModel,0x94,5u);
    select(4,5,otherPtr,0x02e0000000000042ULL);
    call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL);
    model.fill(0);put(context,8,otherPtr);
    put(context,0x28,uint64_t(0x04000000000002a7));put(context,0x18,reinterpret_cast<uintptr_t>(config.data()));put(config,0x104,1u);
    uint32_t status=0;Factory volatile pelletCall=fixturePelletFactory;
    assert(pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL)==0&&status==8);
    // Actual native hook path: calibrated rays require current binding, fresh
    // world identity and measured config. Duplicate callbacks do not re-emit.
    otherComponents={reinterpret_cast<uintptr_t>(otherScene.data()),0};
    put(otherModel,0x50,reinterpret_cast<uintptr_t>(otherComponents.data()));put(otherModel,0x58,2);put(otherModel,0x5c,2);
    put(otherScene,8,otherPtr);put(otherScene,0x10,uint8_t(1));put(config,0x50,100.f);
    std::memcpy(guestBody.data(),"OWBODY01",8);put(guestBody,8,1u);put(guestBody,12,256u);put(guestBody,16,GetCurrentProcessId());put(guestBody,20,123u);
    put(guestBody,24,uint64_t(66));put(guestBody,32,uint64_t(77));put(guestBody,64,uint64_t(2));put(guestBody,136,uint64_t(88));
    FILETIME time{};GetSystemTimeAsFileTime(&time);ULARGE_INTEGER clock{};clock.LowPart=time.dwLowDateTime;clock.HighPart=time.dwHighDateTime;
    put(guestBody,72,(clock.QuadPart-116444736000000000ULL)/10000);
    assert(setBody.value(guestBody.data())&&rebind.value());put(context,0,42u);put(context,0x20,0x8000000000000001ULL);
    for(int i=0;i<2;i++)assert(pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL)==0&&status==8);
    put(context,0,43u);put(config,0x50,99.f);pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL);
    put(config,0x50,100.f);put(guestBody,32,uint64_t(78));pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL);
    put(guestBody,32,uint64_t(77));pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL);
    // A confirmed Pharah factory failure becomes a measured MC-owned flight.
    select(4,5,otherPtr,0x02e0000000000008ULL);assert(rebind.value());
    put(context,0x28,uint64_t(0x0400000000000033));put(config,0x48,35.f);put(config,0x4c,5.f);put(context,0,100u);
    for(int i=0;i<2;i++)pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL);
    put(context,0,101u);put(config,0x48,34.f);pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL);
    put(context,0,102u);put(config,0x48,35.f);pelletCall(0x1234,reinterpret_cast<uintptr_t>(context.data()),reinterpret_cast<uintptr_t>(&status),0xabcdef1234567801ULL);
    assert(setBody.value(nullptr));
    put(context,0x28,uint64_t(0x04000000000007ca));
    call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL);
    put(newModel,0x28,admin);put(newModel,0x94,7u);newComponents={reinterpret_cast<uintptr_t>(newScene.data()),0};
    put(newModel,0x50,reinterpret_cast<uintptr_t>(newComponents.data()));put(newModel,0x58,2);put(newModel,0x5c,2);
    put(newScene,8,newPtr);put(newScene,0x10,uint8_t(1));select(6,7,newPtr,0x02e0000000000029ULL);
    put(context,8,newPtr);put(entity,0x94,10u);
    call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL);
    assert(rebind.value());call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL);
    assert(stop.value());std::memcpy(after.data(),reinterpret_cast<void*>(target),24);assert(before==after);std::memcpy(pelletAfter.data(),reinterpret_cast<void*>(pelletTarget),24);assert(pelletBefore==pelletAfter);
    assert(beamTable[0x110/8]==reinterpret_cast<void*>(fixtureBeamBegin)&&beamTable[0x158/8]==reinterpret_cast<void*>(fixtureBeamEnd));
    assert(call(0x1234,entityPtr,reinterpret_cast<uintptr_t>(context.data()),0xabcdef1234567801ULL)==0xabcdef654321ULL&&originalCalls==7);
    std::cout<<"Real MinHook fixture: Genji/McCree/Pharah rebind, rays/rockets, duplicate/config/world rejection and original callback restoration passed.\n";
}
