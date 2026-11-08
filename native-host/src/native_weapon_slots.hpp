#pragma once
#include "native_local_hero.hpp"
#include <array>
#include <atomic>
#include <cstring>

namespace passthrough {
// The offline spawner starts all weapon scripts with schema default slot0.
// The original graphs compare entity.1f against script.1c. Initialize those
// parameters from STUWeaponComponent's actual array; original graphs still own
// equip/holster, animations, input, ammo and every attack. No hero ID table.
struct NativeWeaponSlot {
    unsigned index=0;uint64_t resource=0;uintptr_t script=0,graph=0,bag=0,primitive=0;
};
struct NativeWeaponSlotLayout {
    uintptr_t definition=0,component=0,items=0,sync=0,bag=0,requested=0,selected=0;
    std::array<NativeWeaponSlot,9> weapons{};unsigned count=0,mask=0;
};
template<class Read> struct WeaponSlotReader {
    uintptr_t base;Read read;
    template<class T> bool get(uintptr_t at,T& v)const{return at>=0x10000&&read(at,&v,sizeof v);}
    uintptr_t ptr(uintptr_t at)const{uintptr_t v=0;return get(at,v)?v:0;}
    bool metadata(uintptr_t obj,uint32_t kind,int size,uintptr_t& info)const{
        auto fn=ptr(ptr(obj)+0x28);std::array<unsigned char,8> code{};int32_t displacement=0;
        if(!get(fn,code)||code[0]!=0x48||code[1]!=0x8d||code[2]!=5||code[7]!=0xc3)return false;
        std::memcpy(&displacement,code.data()+3,4);info=fn+7+displacement;uint32_t actual=0;int bytes=0;
        return get(info+0x50,actual)&&actual==kind&&get(info+0x5c,bytes)&&bytes==size;
    }
    bool field(uintptr_t info,uint32_t wanted,int offset,uintptr_t* constraint=nullptr)const{
        int count=0;if(!get(info+0x54,count)||count<0||count>512)return false;auto args=ptr(info+0x28);bool found=false;
        for(int i=0;i<count;i++){uint32_t key=0;int at=0;
            if(!get(args+i*0xa0+8,key)||!get(args+i*0xa0+12,at))return false;
            if(key==wanted){if(found||at!=offset)return false;found=true;if(constraint)*constraint=ptr(args+i*0xa0+16);}}
        return found;
    }
    bool array(uintptr_t at,uintptr_t& items,uint64_t& count,unsigned limit)const{
        std::array<uint64_t,2> storage{},values{};
        if(!get(at,storage)||(storage[1]!=1&&storage[1]!=2)||!get(storage[0],values))return false;
        items=values[storage[1]==1?0:1];count=values[storage[1]==1?1:0];return count<=limit&&(!count||items>=0x10000);
    }
    struct List{uintptr_t items=0;int count=0,capacity=0;};
    bool vector(uintptr_t at,List& l,int limit)const{
        return get(at,l)&&l.count>=0&&l.count<=l.capacity&&l.capacity<=limit&&(!l.count||l.items>=0x10000);
    }
    uintptr_t scriptComponent(uintptr_t owner)const{
        List l;if(!vector(owner+0x50,l,256))return 0;uintptr_t result=0;
        for(int i=0;i<l.count-1;i++){auto comp=ptr(l.items+i*8);unsigned char kind=0;
            if(!get(comp+0x10,kind))return 0;
            if(kind==0x23&&ptr(comp+8)==owner){if(result)return 0;result=comp;}}
        return result;
    }
    bool primitiveValid(uintptr_t object,uintptr_t bag,uint64_t rid,int& value)const{
        std::array<unsigned char,16> payload{};uint32_t type=0,flags=0;
        if(ptr(object)!=base+0x1608248||ptr(object+0x80)!=bag||ptr(object+0x98)!=rid
           ||!get(object+0x94,flags)||(flags!=6&&flags!=14)||!get(object+0xa0,payload))return false;
        std::memcpy(&type,payload.data()+12,4);std::memcpy(&value,payload.data(),4);
        return type==2&&value>=0&&value<=9;
    }
    uintptr_t primitive(uintptr_t bag,uint64_t rid)const{
        if(ptr(bag)!=base+0x1607a90)return 0;
        uintptr_t result=0;
        for(unsigned bucket=0;bucket<16;bucket++){List l;if(!vector(bag+0xa0+bucket*0x30,l,512))return 0;
            for(int i=0;i<l.count;i++){std::array<uint64_t,2> pair{};if(!get(l.items+i*16,pair))return 0;
                if(pair[0]==rid){if(result)return 0;result=pair[1];}}}
        int value=0;return result&&primitiveValid(result,bag,rid,value)?result:0;
    }
    bool owner(uintptr_t admin,const NativeLocalHero& h)const{
        uint32_t local=0,model=0;
        return ptr(base+0x17b7f90)==admin&&get(admin+0x220,local)&&local==h.localId
            &&get(h.reference+0x94,model)&&model==h.modelId&&ptr(h.reference+8)==h.controller
            &&ptr(h.model+0x28)==admin&&ptr(h.heroInfo+0x98)==h.hero;
    }
    bool definitions(uintptr_t model,NativeWeaponSlotLayout& out)const{
        auto definition=ptr(ptr(model+0x30)&~uintptr_t(63));uintptr_t info=0;
        // Entity definitions have inherited fields and a larger size; the
        // existing first-person metadata reader already validates that owner.
        auto fn=ptr(ptr(definition)+0x28);std::array<unsigned char,8> code{};int32_t d=0;uint32_t kind=0;
        if(!get(fn,code)||code[0]!=0x48||code[1]!=0x8d||code[2]!=5||code[7]!=0xc3)return false;
        std::memcpy(&d,code.data()+3,4);if(!get(fn+7+d+0x50,kind)||kind!=0xec23fffd)return false;
        uint64_t flag=0;if(!get(definition+0x30,flag)||flag!=2)return false;
        auto header=ptr(definition+0x28);int buckets=0,count=0;
        if(!get(header,buckets)||buckets<1||buckets>256||!get(ptr(header+8)+4*(buckets-1),count)||count<1||count>256)return false;
        auto entries=ptr(header+16);uintptr_t component=0;
        for(int i=0;i<count;i++){uint32_t key=0;if(!get(entries+i*16,key))return false;
            if(key==0x378f54cd){if(component)return false;component=ptr(entries+i*16+8);}}
        uintptr_t constraint=0;
        if(!component||!metadata(component,0x378f54cd,40,info)||!field(info,0xa86ea67d,8)
           ||!field(info,0x0841f7a8,24,&constraint)||ptr(component+16)!=0x0580000000000015ULL)return false;
        // Reflected INLINE WeaponDefinition, not a guessed pointer array.
        auto inlineInfo=ptr(constraint+0x28);int stride=0;
        if(!get(inlineInfo+0x50,kind)||kind!=0x78942477||!get(inlineInfo+0x5c,stride)||stride!=48
           ||!field(inlineInfo,0x45b2bab8,0)||!field(inlineInfo,0x5612d5c4,32))return false;
        uintptr_t items=0;uint64_t n=0;if(!array(component+24,items,n,10)||n<2)return false;
        NativeWeaponSlotLayout next;next.definition=definition;next.component=component;next.items=items;
        for(unsigned i=0;i<n;i++){
            uint64_t graph=0,script=0;if(!get(items+i*48+8,graph)||!get(items+i*48+40,script))return false;
            if(!graph&&!script)continue;
            if((graph&&graph>>48!=0x0580)||(script&&script>>48!=0x0580)||(graph&&script&&graph!=script)||!i||i>9)return false;
            auto resource=script?script:graph;
            for(unsigned j=0;j<next.count;j++)if(next.weapons[j].resource==resource)return false;
            next.weapons[next.count++]={i,resource,0,0,0,0};next.mask|=1u<<i;
        }
        out=next;return true;
    }
    bool layout(uintptr_t admin,const NativeLocalHero& hero,NativeWeaponSlotLayout& out)const{
        NativeWeaponSlotLayout next;if(!owner(admin,hero)||!definitions(hero.model,next)||next.count<2)return false;
        auto comp=scriptComponent(hero.model);next.sync=comp?comp+0xc0:0;next.bag=ptr(next.sync+0x2e0);
        if(!comp||ptr(next.sync+0x450)!=comp||ptr(next.bag+0x3c0)!=next.sync||ptr(next.bag+0x3b8))return false;
        next.requested=primitive(next.bag,0x0d8000000000001eULL);next.selected=primitive(next.bag,0x0d8000000000001fULL);
        if(!next.requested||!next.selected)return false;
        List scripts;if(!vector(next.sync+0xf0,scripts,512))return false;
        for(unsigned i=0;i<next.count;i++){
            auto& w=next.weapons[i];for(int j=0;j<scripts.count;j++){
                auto script=ptr(scripts.items+j*8);uint64_t resource=0;if(!script||!get(script+0x150,resource))return false;
                if(resource==w.resource){if(w.script)return false;w.script=script;}}
            if(!w.script||ptr(w.script+0x10)!=next.sync)return false;
            w.graph=ptr(w.script+0x160);w.bag=ptr(w.script+0x98);
            if(!w.graph||ptr(w.bag+0x3b8)!=w.script||ptr(w.bag+0x3c0)!=next.sync)return false;
            w.primitive=primitive(w.bag,0x0d8000000000001cULL);if(!w.primitive)return false;
        }
        if(!owner(admin,hero))return false;
        out=next;return true;
    }
};
template<class Read> bool nativeWeaponSelectionReady(uintptr_t base,uintptr_t admin,const NativeLocalHero& hero,Read read){
    WeaponSlotReader<Read> r{base,read};NativeWeaponSlotLayout layout;
    if(!r.layout(admin,hero,layout)||(layout.mask&6u)!=6u)return false;
    for(unsigned i=0;i<layout.count;i++){int value=0;auto& w=layout.weapons[i];
        if(!r.primitiveValid(w.primitive,w.bag,0x0d8000000000001cULL,value)||value!=int(w.index))return false;}
    int selected=0;return r.primitiveValid(layout.selected,layout.bag,0x0d8000000000001fULL,selected)
        &&selected>0&&(layout.mask&(1u<<selected));
}
struct NativeWeaponSlots {
    std::atomic<uint64_t> initializations{0},parameterWrites{0},notices{0},refused{0};
    std::atomic<unsigned> count{0},selected{0};std::atomic<uint32_t> modelId{0};
    NativeWeaponSlotLayout cached;uintptr_t model=0;bool ready=false,failed=false;unsigned retry=0;
    template<class Read,class Write,class Invoke> void update(uintptr_t base,uintptr_t admin,const NativeLocalHero& hero,Read read,Write write,Invoke invoke){
        WeaponSlotReader<Read> r{base,read};
        if(model!=hero.model||modelId!=hero.modelId){model=hero.model;modelId=hero.modelId;ready=failed=false;retry=0;count=selected=0;cached={};}
        if(failed)return;
        if(ready){int value=0;
            if(r.owner(admin,hero)&&r.ptr(cached.sync+0x2e0)==cached.bag&&r.primitiveValid(cached.selected,cached.bag,0x0d8000000000001fULL,value)){
                selected=unsigned(value);return;}
            ready=false;count=selected=0;
        }
        if(retry&&++retry<30)return;
        retry=1;
        NativeWeaponSlotLayout layout;if(!r.layout(admin,hero,layout))return;
        auto valid=[&](int v){return v==0||(v>0&&v<=9&&(layout.mask&(1u<<v)));};
        int current=0,requested=0;
        if(!r.primitiveValid(layout.selected,layout.bag,0x0d8000000000001fULL,current)
           ||!r.primitiveValid(layout.requested,layout.bag,0x0d8000000000001eULL,requested)||!valid(current)||!valid(requested))return;
        unsigned first=layout.weapons[0].index;int desired=current?current:int(first);
        struct Change{uintptr_t primitive,bag;uint64_t rid;int next;std::array<unsigned char,16> before;uint32_t flags;};
        std::array<Change,11> changes{};unsigned n=0;
        auto add=[&](uintptr_t primitive,uintptr_t bag,uint64_t rid,int next){int old=0;
            if(!r.primitiveValid(primitive,bag,rid,old)||(old!=0&&old!=next))return false;
            if(old!=next){auto& c=changes[n++];c.primitive=primitive;c.bag=bag;c.rid=rid;c.next=next;
                if(!r.get(primitive+0xa0,c.before)||!r.get(primitive+0x94,c.flags))return false;}
            return true;};
        for(unsigned i=0;i<layout.count;i++){auto& w=layout.weapons[i];if(!add(w.primitive,w.bag,0x0d8000000000001cULL,int(w.index)))return;}
        if(!current&&!add(layout.selected,layout.bag,0x0d8000000000001fULL,desired))return;
        if(!requested&&!add(layout.requested,layout.bag,0x0d8000000000001eULL,desired))return;
        const std::array<unsigned char,16> prefix{0x48,0x89,0x5c,0x24,8,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48};
        std::array<unsigned char,16> code{};
        if(r.ptr(base+0x1608248+0x288)!=base+0xf5f740||!r.get(base+0xf5f740,code)||code!=prefix||!r.owner(admin,hero))return;
        // Install all parameters before notifying any original subscription.
        unsigned applied=0;for(;applied<n;applied++){
            auto& c=changes[applied];if(!write(c.primitive+0xa0,&c.next,4))break;parameterWrites++;
        }
        if(applied!=n){for(unsigned i=0;i<applied;i++)write(changes[i].primitive+0xa0,changes[i].before.data(),4);refused++;failed=true;return;}
        for(unsigned i=0;i<n;i++){
            auto& c=changes[i];uint32_t dirty=c.flags|8u;
            if(!write(c.primitive+0x94,&dirty,4)||!invoke(base+0xf5f740,c.primitive,layout.sync,r.ptr(c.bag+0x3b8),c.primitive+0x88)){
                uint32_t now=0;if(r.get(c.primitive+0x94,now)&&now==dirty)write(c.primitive+0x94,&c.flags,4);
                refused++;failed=true;return;}
            notices++;
        }
        cached=layout;ready=true;count=layout.count;selected=unsigned(desired);initializations++;
    }
};
}
