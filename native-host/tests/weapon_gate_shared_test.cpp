#include "../src/native_local_hero.hpp"
#include <windows.h>
#include <array>
#include <cassert>
#include <cstring>
#include <iostream>
#include <memory>
#include <thread>
#include <utility>
using namespace passthrough;
namespace {
template<size_t N> using Bytes=std::array<unsigned char,N>;
Bytes<0x300> admin{};Bytes<65536> entities{};
std::array<void*,0x298/8> table{};
using Callback=uintptr_t(WINAPI*)(void*);bool expectGate=true;
using Entry=void(WINAPI*)(void*,void*,void*);bool expectSkillGate=false,mutateSkillFlags=false;unsigned skillCalls=0;
using Tick=intptr_t(WINAPI*)(void*,void*);
template<class T> void put(void* p,size_t offset,T value){std::memcpy(static_cast<unsigned char*>(p)+offset,&value,sizeof value);}
template<class T> T get(void* p,size_t offset){T value{};std::memcpy(&value,static_cast<unsigned char*>(p)+offset,sizeof value);return value;}
struct Hero {
    Bytes<0x300> controller{},model{},reference{},info{},component{};
    Bytes<0x500> container{},script{},state{};
    std::array<uintptr_t,3> components{};
    std::array<uint64_t,2> controllerEntry{},modelEntry{};
    Bytes<0x80> tankGraph{},tankDefinition{};
    std::array<uint64_t,2> tankStateList{},tankNodeList{};
    std::array<uintptr_t,22> tankStates{};
    std::array<uintptr_t,29> tankNodes{};
    uint32_t id,modelId;
    Hero(unsigned n){
        id=101+n*2;modelId=id+1;auto p=heroWeapons[n];
        put(controller.data(),0x28,reinterpret_cast<uintptr_t>(admin.data()));put(controller.data(),0x94,id);
        put(model.data(),0x28,reinterpret_cast<uintptr_t>(admin.data()));put(model.data(),0x94,modelId);
        components={reinterpret_cast<uintptr_t>(reference.data()),reinterpret_cast<uintptr_t>(info.data()),0};
        put(controller.data(),0x50,reinterpret_cast<uintptr_t>(components.data()));put(controller.data(),0x58,int(3));put(controller.data(),0x5c,int(3));
        put(reference.data(),8,reinterpret_cast<uintptr_t>(controller.data()));put(reference.data(),0x10,uint8_t(0x20));put(reference.data(),0x94,modelId);
        put(info.data(),8,reinterpret_cast<uintptr_t>(controller.data()));put(info.data(),0x10,uint8_t(0x3f));put(info.data(),0x98,p.hero);
        controllerEntry={id,reinterpret_cast<uintptr_t>(controller.data())};modelEntry={modelId,reinterpret_cast<uintptr_t>(model.data())};
        put(entities.data(),n*32,reinterpret_cast<uintptr_t>(controllerEntry.data()));put(entities.data(),n*32+8,int(1));
        put(entities.data(),n*32+16,reinterpret_cast<uintptr_t>(modelEntry.data()));put(entities.data(),n*32+24,int(1));
        put(component.data(),8,reinterpret_cast<uintptr_t>(model.data()));put(container.data(),0x450,reinterpret_cast<uintptr_t>(component.data()));
        put(script.data(),0x10,reinterpret_cast<uintptr_t>(container.data()));put(script.data(),0x150,p.script);put(script.data(),0x258,uint32_t(0x408001|p.extraFlags));
        put(state.data(),0,reinterpret_cast<uintptr_t>(table.data()));put(state.data(),0x78,reinterpret_cast<uintptr_t>(script.data()));put(state.data(),0x70,int(4));
    }
    void select(){put(admin.data(),0x220,id);}
    uint32_t flags(){return get<uint32_t>(script.data(),0x258);}
    void tank(){
        put(info.data(),0x98,uint64_t(0x02e0000000000015));
        put(script.data(),0x150,uint64_t(0x058000000000024f));put(script.data(),0x258,uint32_t(0x408003));
        put(script.data(),0x160,reinterpret_cast<uintptr_t>(tankGraph.data()));
        tankStates[19]=reinterpret_cast<uintptr_t>(tankDefinition.data());tankNodes[25]=tankStates[19];
        tankStateList={reinterpret_cast<uintptr_t>(tankStates.data()),tankStates.size()};
        tankNodeList={reinterpret_cast<uintptr_t>(tankNodes.data()),tankNodes.size()};
        put(tankGraph.data(),0x60,reinterpret_cast<uintptr_t>(tankStateList.data()));put(tankGraph.data(),0x68,uint64_t(1));
        put(tankGraph.data(),0x50,reinterpret_cast<uintptr_t>(tankNodeList.data()));put(tankGraph.data(),0x58,uint64_t(1));
        put(tankDefinition.data(),0x68,int(25));put(tankDefinition.data(),0x6c,int(11));
        put(state.data(),0x70,int(19));
    }
};
uintptr_t WINAPI update(void* state){auto script=get<uintptr_t>(state,0x78);assert(bool(get<uint32_t>(reinterpret_cast<void*>(script),0x258)&8)==expectGate);return 33;}
uintptr_t WINAPI shot(void* state){auto script=get<uintptr_t>(state,0x78);assert(bool(get<uint32_t>(reinterpret_cast<void*>(script),0x258)&8)==expectGate);return 44;}
uintptr_t WINAPI begin(void* state){
    auto t=reinterpret_cast<void**>(get<uintptr_t>(state,0));assert(reinterpret_cast<Callback>(t[0x120/8])(state)==33);assert(reinterpret_cast<Callback>(t[0x270/8])(state)==44);return 0xabcdef0123456789ULL;
}
void fire(Hero& hero){assert(reinterpret_cast<Callback>(table[0x110/8])(hero.state.data())==0xabcdef0123456789ULL);assert(!(hero.flags()&8));}
void WINAPI entry(void*,void* script,void*){assert(bool(get<uint32_t>(script,0x258)&8)==expectSkillGate);if(mutateSkillFlags)put(script,0x258,get<uint32_t>(script,0x258)|0x20u);++skillCalls;}
intptr_t WINAPI tick(void* script,void* event){assert(event==reinterpret_cast<void*>(0x12345678));entry(nullptr,script,nullptr);return intptr_t(0x123456789abcdefLL);}
}
int main(){
    table.fill(reinterpret_cast<void*>(update));table[0x110/8]=reinterpret_cast<void*>(begin);table[0x270/8]=reinterpret_cast<void*>(shot);
    put(admin.data(),0x10,reinterpret_cast<uintptr_t>(entities.data()));
    auto genji=std::make_unique<Hero>(0);Hero mccree(1),winston(2);genji->select();
    auto dll=LoadLibraryW(L"native-host/build/owmc-weapon-gate-v11.dll");assert(dll);
    union {FARPROC raw;BOOL(*fn)(uintptr_t,void**);} attach{GetProcAddress(dll,"OWMC_SharedGateTestAttach")};
    union {FARPROC raw;BOOL(*fn)();} stop{GetProcAddress(dll,"OWMC_SharedGateTestStop")};assert(attach.raw&&stop.raw);
    assert(attach.fn(reinterpret_cast<uintptr_t>(admin.data()),table.data()));
    expectGate=false;std::thread other([&]{fire(mccree);});other.join();
    expectGate=true;fire(*genji);
    expectGate=false;fire(mccree); // Other entity's same supported weapon is untouched.
    mccree.select();expectGate=true;fire(mccree);
    auto primaryResource=get<uint64_t>(mccree.script.data(),0x150);
    put(mccree.script.data(),0x150,uint64_t(0x05800000000001e9));put(mccree.script.data(),0x258,uint32_t(0x408003));fire(mccree);
    assert(mccree.flags()==0x408003);
    put(mccree.script.data(),0x150,uint64_t(0x058000000000007b));expectGate=false;fire(mccree);
    put(mccree.script.data(),0x150,primaryResource);put(mccree.script.data(),0x258,uint32_t(0x408001));
    expectGate=false;fire(*genji);genji.reset(); // No dangling state vtable survives destruction.
    winston.select();expectGate=true;fire(winston);assert(winston.flags()==0xc08001);
    // Entity IDs wrap into the same 4096-entry hash bucket after enough native
    // projectiles/spawns. The current controller/model need not be its first row.
    std::array<uint64_t,4> controllers{0x80000069,0,winston.id,reinterpret_cast<uintptr_t>(winston.controller.data())};
    std::array<uint64_t,6> models{0x8000006a,0,0x8000106a,0,winston.modelId,reinterpret_cast<uintptr_t>(winston.model.data())};
    entities.fill(0);
    put(entities.data(),(winston.id&4095u)*16,reinterpret_cast<uintptr_t>(controllers.data()));
    put(entities.data(),(winston.id&4095u)*16+8,int(2));
    put(entities.data(),(winston.modelId&4095u)*16,reinterpret_cast<uintptr_t>(models.data()));
    put(entities.data(),(winston.modelId&4095u)*16+8,int(3));
    NativeLocalHero collision;
    auto read=[](uintptr_t address,void* out,size_t size){SIZE_T done=0;return ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void*>(address),out,size,&done)&&done==size;};
    assert(collision.refresh(reinterpret_cast<uintptr_t>(admin.data()),read));
    assert(collision.controller==reinterpret_cast<uintptr_t>(winston.controller.data())&&collision.model==reinterpret_cast<uintptr_t>(winston.model.data()));
    fire(winston);
    // A real local Volley from another native script is now admitted by class
    // and current-owner proof, rather than only three hard-coded resource IDs.
    auto otherScript=get<uint64_t>(winston.script.data(),0x150);put(winston.script.data(),0x150,uint64_t(0x058000000000002b));fire(winston);put(winston.script.data(),0x150,otherScript);
    auto original=get<uint64_t>(winston.script.data(),0x150);put(winston.script.data(),0x150,uint64_t(0x123));expectGate=false;fire(winston);put(winston.script.data(),0x150,original);
    // Tank's extra bit2 is confined to the actual local shared Volley class
    // and graph024f node25. Its runtime m_states index is19, not25 or the
    // unrelated definition+6c value11. Each fire
    // exercises original Begin plus its nested Update and Shot callbacks.
    winston.tank();expectGate=true;fire(winston);assert(winston.flags()==0x408003);
    put(winston.script.data(),0x258,uint32_t(0x400083));fire(winston);assert(winston.flags()==0x400083);
    put(winston.script.data(),0x258,uint32_t(0x408003));
    expectGate=false;std::thread tankOther([&]{fire(winston);});tankOther.join();
    mccree.select();fire(winston);winston.select();
    put(winston.info.data(),0x98,uint64_t(0x02e0000000000009));fire(winston);
    put(winston.info.data(),0x98,uint64_t(0x02e0000000000015));
    put(winston.script.data(),0x150,uint64_t(0x058000000000012e));fire(winston);
    put(winston.script.data(),0x150,uint64_t(0x058000000000024f));
    for(uint32_t flags:{0x400003u,0xc00083u,0xc08003u,0x408023u,0xffffffffu}){
        put(winston.script.data(),0x258,flags&~8u);fire(winston);
    }
    put(winston.script.data(),0x258,uint32_t(0x408003));
    put(winston.state.data(),0x70,int(25));fire(winston); // Wrong list index, even though node25 exists.
    put(winston.state.data(),0x70,int(11));fire(winston); // Definition+6c is not a runtime index.
    put(winston.state.data(),0x70,int(19));
    put(winston.tankDefinition.data(),0x68,int(24));fire(winston);put(winston.tankDefinition.data(),0x68,int(25));
    auto tankNode=winston.tankNodes[25];winston.tankNodes[25]=tankNode+8;fire(winston);winston.tankNodes[25]=tankNode;
    put(winston.tankGraph.data(),0x68,uint64_t(3));fire(winston);put(winston.tankGraph.data(),0x68,uint64_t(1));
    auto count=winston.tankStateList[1];winston.tankStateList[1]=4097;fire(winston);winston.tankStateList[1]=count;
    put(winston.script.data(),0x160,uintptr_t(0));fire(winston);put(winston.script.data(),0x160,reinterpret_cast<uintptr_t>(winston.tankGraph.data()));
    auto foreignTable=table;put(winston.state.data(),0,reinterpret_cast<uintptr_t>(foreignTable.data()));fire(winston);
    put(winston.state.data(),0,reinterpret_cast<uintptr_t>(table.data()));
    put(winston.component.data(),8,reinterpret_cast<uintptr_t>(mccree.model.data()));fire(winston);
    put(winston.component.data(),8,reinterpret_cast<uintptr_t>(winston.model.data()));
    // Both declared STU list layouts are supported without guessing offsets.
    std::swap(winston.tankStateList[0],winston.tankStateList[1]);put(winston.tankGraph.data(),0x68,uint64_t(2));
    std::swap(winston.tankNodeList[0],winston.tankNodeList[1]);put(winston.tankGraph.data(),0x58,uint64_t(2));
    expectGate=true;fire(winston);assert(winston.flags()==0x408003);
    // Reuse this actual local entity as the guarded Reaper fixture. Another
    // entity's graph and another callback thread must remain untouched.
    put(winston.info.data(),0x98,uint64_t(0x02e0000000000002));put(winston.script.data(),0x150,uint64_t(0x0580000000000020));put(winston.script.data(),0x258,uint32_t(0x408003));
    void* entrySlot=reinterpret_cast<void*>(entry);void* finishSlot=reinterpret_cast<void*>(entry);
    union {FARPROC raw;BOOL(*fn)(void**,void**);} entries{GetProcAddress(dll,"OWMC_SharedGateTestEntries")};
    union {FARPROC raw;BOOL(*fn)(uint64_t);} mask{GetProcAddress(dll,"OWMC_SharedGateTestSkillMask")};assert(entries.raw&&mask.raw&&entries.fn(&entrySlot,&finishSlot));
    expectSkillGate=true;mutateSkillFlags=true;reinterpret_cast<Entry>(entrySlot)(nullptr,winston.script.data(),winston.state.data());assert(winston.flags()==0x408023); // native mutation survives, authority does not.
    put(winston.script.data(),0x258,uint32_t(0x408003));mutateSkillFlags=false;reinterpret_cast<Entry>(finishSlot)(nullptr,winston.script.data(),winston.state.data());assert(winston.flags()==0x408003);
    expectSkillGate=false;reinterpret_cast<Entry>(entrySlot)(nullptr,mccree.script.data(),mccree.state.data());
    std::thread otherSkill([&]{reinterpret_cast<Entry>(entrySlot)(nullptr,winston.script.data(),winston.state.data());});otherSkill.join();
    assert(mask.fn(0));reinterpret_cast<Entry>(entrySlot)(nullptr,winston.script.data(),winston.state.data());assert(skillCalls==5);
    void* tickSlot=reinterpret_cast<void*>(tick);
    union {FARPROC raw;BOOL(*fn)(void**);} ticks{GetProcAddress(dll,"OWMC_SharedGateTestTick")};assert(ticks.raw&&ticks.fn(&tickSlot));
    assert(mask.fn(2));expectSkillGate=true;auto event=reinterpret_cast<void*>(0x12345678);
    assert(reinterpret_cast<Tick>(tickSlot)(winston.script.data(),event)==intptr_t(0x123456789abcdefLL));assert(winston.flags()==0x408003);
    expectSkillGate=false;assert(reinterpret_cast<Tick>(tickSlot)(mccree.script.data(),event)==intptr_t(0x123456789abcdefLL));
    std::thread otherTick([&]{reinterpret_cast<Tick>(tickSlot)(winston.script.data(),event);});otherTick.join();
    assert(mask.fn(0));reinterpret_cast<Tick>(tickSlot)(winston.script.data(),event);assert(skillCalls==9);
    assert(stop.fn());assert(table[0x110/8]==reinterpret_cast<void*>(begin)&&table[0x120/8]==reinterpret_cast<void*>(update)&&table[0x270/8]==reinterpret_cast<void*>(shot));
    assert(entrySlot==reinterpret_cast<void*>(entry)&&finishSlot==reinterpret_cast<void*>(entry)&&tickSlot==reinterpret_cast<void*>(tick));
    expectGate=false;fire(winston);
    std::cout<<"PASS: shared Volley and opt-in Wraith entry/finish/tick gates, owner/thread/mask guards, native flag mutation and complete callback restoration.\n";
}
