#include "../src/native_weapon_slots.hpp"
#include <vector>
#include <cassert>
#include <iostream>
using namespace passthrough;
struct Fixture {
    std::vector<unsigned char> memory=std::vector<unsigned char>(0x2000000);
    uintptr_t base=0x100000,admin=0x300000,model=0x400000,sync=0x5000c0,bag=0x600000;
    uintptr_t definition=0x420000,weapon=0x430000,items=0x440000,script1=0x700000,script2=0x710000;
    uintptr_t p1=0x810000,p2=0x820000,selected=0x830000,requested=0x840000;
    NativeLocalHero hero;
    template<class T> void put(uintptr_t at,T value){assert(at+sizeof value<=memory.size());std::memcpy(memory.data()+at,&value,sizeof value);}
    bool read(uintptr_t at,void* out,size_t n){if(at+n>memory.size())return false;std::memcpy(out,memory.data()+at,n);return true;}
    bool write(uintptr_t at,const void* in,size_t n){if(at+n>memory.size())return false;std::memcpy(memory.data()+at,in,n);return true;}
    uintptr_t next=0x900000;
    uintptr_t alloc(){auto p=next;next+=0x1000;return p;}
    void meta(uintptr_t obj,uint32_t kind,int size){
        auto vt=alloc(),fn=alloc(),info=alloc();put(obj,vt);put(vt+0x28,fn);
        const unsigned char code[]{0x48,0x8d,5,0,0,0,0,0xc3};std::memcpy(memory.data()+fn,code,8);
        put(fn+3,int32_t(info-fn-7));put(info+0x50,kind);put(info+0x5c,size);
    }
    uintptr_t info(uintptr_t obj){uintptr_t vt=0,fn=0;read(obj,&vt,8);read(vt+0x28,&fn,8);int32_t d=0;read(fn+3,&d,4);return fn+7+d;}
    void fields(uintptr_t type,std::initializer_list<std::pair<uint32_t,int>> list){
        auto args=alloc();put(type+0x28,args);put(type+0x54,int(list.size()));unsigned i=0;
        for(auto f:list){put(args+i*0xa0+8,f.first);put(args+i*0xa0+12,f.second);i++;}
    }
    void array(uintptr_t at,uintptr_t data,uint64_t n){auto storage=alloc();put(at,storage);put(at+8,uint64_t(2));put(storage,n);put(storage+8,data);}
    void vector(uintptr_t at,uintptr_t data,int n){put(at,data);put(at+8,n);put(at+12,n);}
    void primitive(uintptr_t object,uintptr_t owner,uint64_t rid){put(object,base+0x1608248);put(object+0x80,owner);put(object+0x98,rid);put(object+0x94,6u);put(object+0xac,2u);}
    void bucket(uintptr_t owner,std::initializer_list<std::pair<uint64_t,uintptr_t>> list){
        put(owner,base+0x1607a90);auto data=alloc();vector(owner+0xa0,data,int(list.size()));unsigned i=0;
        for(auto pair:list){put(data+i*16,pair.first);put(data+i*16+8,pair.second);i++;}
    }
    Fixture(){
        hero.hero=0x02e0000000000006ULL;hero.model=model;hero.modelId=19;hero.localId=17;
        hero.reference=0x450000;hero.controller=0x460000;hero.heroInfo=0x470000;
        put(base+0x17b7f90,admin);put(admin+0x220,17u);put(hero.reference+0x94,19u);
        put(hero.reference+8,hero.controller);put(model+0x28,admin);put(hero.heroInfo+0x98,hero.hero);
        auto entry=alloc();put(model+0x30,entry);put(entry,definition);meta(definition,0xec23fffd,0x38);
        auto header=alloc(),ends=alloc(),pairs=alloc();put(definition+0x28,header);put(definition+0x30,uint64_t(2));
        put(header,1);put(header+8,ends);put(header+16,pairs);put(ends,1);put(pairs,0x378f54cdu);put(pairs+8,weapon);
        meta(weapon,0x378f54cd,40);auto wi=info(weapon);fields(wi,{{0xa86ea67d,8},{0x0841f7a8,24}});
        uintptr_t args=0;read(wi+0x28,&args,8);auto constraint=alloc(),inlineInfo=alloc();put(args+0xa0+16,constraint);put(constraint+0x28,inlineInfo);
        put(inlineInfo+0x50,0x78942477u);put(inlineInfo+0x5c,48);fields(inlineInfo,{{0x45b2bab8,0},{0x5612d5c4,32}});
        put(weapon+16,0x0580000000000015ULL);array(weapon+24,items,3);
        put(items+48+40,0x0580000000000102ULL);put(items+96+40,0x05800000000000f3ULL);
        auto comps=alloc();vector(model+0x50,comps,2);put(comps,sync-0xc0);put(sync-0xc0+8,model);put(sync-0xc0+0x10,uint8_t(0x23));
        put(sync+0x450,sync-0xc0);put(sync+0x2e0,bag);put(bag+0x3c0,sync);
        auto scripts=alloc();vector(sync+0xf0,scripts,2);put(scripts,script1);put(scripts+8,script2);
        unsigned i=0;for(auto script:std::array<uintptr_t,2>{script1,script2}){
            auto sbag=alloc(),graph=alloc();put(script+0x10,sync);put(script+0x160,graph);put(script+0x98,sbag);
            put(script+0x150,i?0x05800000000000f3ULL:0x0580000000000102ULL);
            put(sbag+0x3b8,script);put(sbag+0x3c0,sync);auto parameter=i?p2:p1;
            bucket(sbag,{{0x0d8000000000001cULL,parameter}});primitive(parameter,sbag,0x0d8000000000001cULL);i++;
        }
        bucket(bag,{{0x0d8000000000001eULL,requested},{0x0d8000000000001fULL,selected}});
        primitive(requested,bag,0x0d8000000000001eULL);primitive(selected,bag,0x0d8000000000001fULL);
        put(base+0x1608248+0x288,base+0xf5f740);
        const unsigned char prefix[]{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};std::memcpy(memory.data()+base+0xf5f740,prefix,16);
    }
    int value(uintptr_t obj){int v=0;read(obj+0xa0,&v,4);return v;}
};
int main(){
    for(auto heroId:std::array<uint64_t,2>{0x02e0000000000006ULL,0x02e0000000000004ULL}){
        Fixture f;f.hero.hero=heroId;f.put(f.hero.heroInfo+0x98,heroId);
        auto read=[&](uintptr_t a,void* b,size_t n){return f.read(a,b,n);};auto write=[&](uintptr_t a,const void* b,size_t n){return f.write(a,b,n);};
        NativeWeaponSlotLayout layout;WeaponSlotReader<decltype(read)> r{f.base,read};assert(r.layout(f.admin,f.hero,layout)&&layout.count==2&&layout.mask==6);
        assert(!nativeWeaponSelectionReady(f.base,f.admin,f.hero,read));unsigned calls=0;
        auto invoke=[&](uintptr_t fn,uintptr_t object,uintptr_t sync,uintptr_t instance,uintptr_t user){
            assert(fn==f.base+0xf5f740&&sync==f.sync&&user==object+0x88);assert(instance==0||instance==f.script1||instance==f.script2);
            assert(f.value(f.p1)==1&&f.value(f.p2)==2&&f.value(f.selected)==1&&f.value(f.requested)==1);
            f.put(object+0x94,6u);calls++;return true;};
        NativeWeaponSlots slots;slots.update(f.base,f.admin,f.hero,read,write,invoke);
        assert(slots.initializations==1&&slots.parameterWrites==4&&slots.notices==4&&calls==4);
        assert(nativeWeaponSelectionReady(f.base,f.admin,f.hero,read));
        for(int i=0;i<12;i++){f.put(f.selected+0xa0,i%2+1);slots.update(f.base,f.admin,f.hero,read,write,invoke);assert(f.value(f.selected)==i%2+1);}
        assert(calls==4&&slots.initializations==1); // Never force the default after a real selection.
        f.put(f.hero.reference+0x94,20u);assert(!nativeWeaponSelectionReady(f.base,f.admin,f.hero,read));
        NativeWeaponSlots stale;stale.update(f.base,f.admin,f.hero,read,write,invoke);assert(stale.parameterWrites==0);
    }
    {Fixture f;auto read=[&](uintptr_t a,void* b,size_t n){return f.read(a,b,n);};
     f.put(f.items+96+40,uint64_t(0));NativeWeaponSlots slots;
     slots.update(f.base,f.admin,f.hero,read,[](auto...){assert(false);return false;},[](auto...){assert(false);return false;});assert(slots.parameterWrites==0);}
    {Fixture f;auto read=[&](uintptr_t a,void* b,size_t n){return f.read(a,b,n);};auto write=[&](uintptr_t a,const void* b,size_t n){return f.write(a,b,n);};
     f.put(f.p2+0x80,uintptr_t(0));NativeWeaponSlots slots;slots.update(f.base,f.admin,f.hero,read,write,[](auto...){assert(false);return false;});assert(slots.parameterWrites==0);}
    {Fixture f;auto read=[&](uintptr_t a,void* b,size_t n){return f.read(a,b,n);};unsigned writes=0;NativeWeaponSlots slots;
     auto write=[&](uintptr_t a,const void* b,size_t n){if(a==f.p2+0xa0)return false;writes++;return f.write(a,b,n);};
     slots.update(f.base,f.admin,f.hero,read,write,[](auto...){assert(false);return false;});
     assert(slots.refused==1&&f.value(f.p1)==0&&f.value(f.selected)==0&&writes==2);}
    {Fixture f;auto read=[&](uintptr_t a,void* b,size_t n){return f.read(a,b,n);};auto write=[&](uintptr_t a,const void* b,size_t n){return f.write(a,b,n);};NativeWeaponSlots slots;
     slots.update(f.base,f.admin,f.hero,read,write,[](auto...){return false;});assert(slots.refused==1);unsigned flags=0;f.read(f.p1+0x94,&flags,4);assert(flags==6);}
    std::cout<<"PASS: actual inline slot definitions, Torbjorn/Mercy without hero special cases, native notification order, repeated selection, stale/single/wrong-owner exclusion and write-failure rollback\n";
}
