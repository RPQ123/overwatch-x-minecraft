package lab.owmcguest;

import java.util.*;
import org.objectweb.asm.*;

/** 离线检查用户数值、升级边界、拾取身份，以及真实编译字节码的破坏顺序/分支。 */
public final class NativeBuildersTuningCheck {
    private static int checks;
    private static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    private record Jump(int index,Label target){}
    private static final class Method {
        final List<String> ops=new ArrayList<>();final List<Jump> jumps=new ArrayList<>();final Map<Label,Integer> labels=new HashMap<>();
    }
    private static Map<String,Method> inspect(String name)throws Exception{
        var result=new HashMap<String,Method>();
        try(var input=NativeBuildersTuningCheck.class.getClassLoader().getResourceAsStream("lab/owmcguest/"+name+".class")){
            check(input!=null,"compiled class "+name);
            new ClassReader(input).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String method,String descriptor,String signature,String[] exceptions){
                    var facts=new Method();result.put(method,facts);
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitFieldInsn(int op,String owner,String field,String desc){facts.ops.add("F:"+owner+"."+field);}
                        @Override public void visitMethodInsn(int op,String owner,String method,String desc,boolean itf){facts.ops.add("C:"+owner+"."+method);}
                        @Override public void visitJumpInsn(int opcode,Label target){facts.jumps.add(new Jump(facts.ops.size(),target));facts.ops.add("J:"+opcode);}
                        @Override public void visitLabel(Label label){facts.labels.put(label,facts.ops.size());}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        return result;
    }
    private static boolean guarded(Method method,String field,int call){
        int at=method.ops.subList(0,Math.max(0,call)).lastIndexOf("F:"+field);
        return at>=0&&at<call&&method.jumps.stream().anyMatch(j->j.index()>at&&j.index()<call&&method.ops.get(j.index()).equals("J:"+Opcodes.IF_ACMPNE)&&method.labels.getOrDefault(j.target(),-1)>call);
    }
    public static void main(String[] args)throws Exception{
        check(NativeJunkratGrenadeTuning.RENDER_SCALE==2,"grenade visible size2");
        check(NativeJunkratGrenadeTuning.FUSE_TICKS==30,"grenade1.5s");
        for(int age=0;age<=200;age++)check(!NativeJunkratGrenadeTuning.expired(age,-1),"airborne age cannot start fuse");
        int ground=-1;
        ground=NativeJunkratGrenadeTuning.groundContact(ground,40,0);
        ground=NativeJunkratGrenadeTuning.groundContact(ground,45,-1);
        check(ground==-1,"wall/ceiling cannot arm fuse");
        ground=NativeJunkratGrenadeTuning.groundContact(ground,50,1);
        check(ground==50,"first floor collision arms fuse");
        ground=NativeJunkratGrenadeTuning.groundContact(ground,65,1);
        ground=NativeJunkratGrenadeTuning.groundContact(ground,72,0);
        check(ground==50,"subsequent floor/wall bounces cannot postpone fuse");
        check(!NativeJunkratGrenadeTuning.expired(79,ground)&&NativeJunkratGrenadeTuning.expired(80,ground),"exact30 ticks after floor, not cast");
        ground=NativeJunkratGrenadeTuning.groundContact(-1,195,1);
        check(!NativeJunkratGrenadeTuning.expired(224,ground)&&NativeJunkratGrenadeTuning.expired(225,ground),"late landing retains full fuse");
        check(NativeJunkratGrenadeTuning.damage(40)==80&&NativeJunkratGrenadeTuning.damage(80)==160,"direct and splash damage both double");
        check(NativeJunkratGrenadeTuning.terrainStrength(1.5)==3.5,"previous terrain1.75 doubles to3.5");
        check(NativeJunkratGrenadeTuning.terrainStrength(4)==4,"shared helper strength cap");
        for(double invalid:new double[]{0,-1,Double.NaN,Double.POSITIVE_INFINITY,4.1}){
            try{NativeJunkratGrenadeTuning.terrainStrength(invalid);throw new AssertionError("invalid terrain input");}catch(IllegalArgumentException expected){checks++;}
        }
        var turret=NativeTorbjornTuning.hammer(1,0);check(turret.level()==1&&turret.progress()==50,"first hammer progress");
        turret=NativeTorbjornTuning.hammer(turret.level(),turret.progress());check(turret.level()==2&&turret.progress()==0&&turret.upgraded(),"1 to2 resets progress");
        check(NativeTorbjornTuning.MAX_LEVEL==2&&NativeTorbjornTuning.CORE_LEVEL==3,"normal cap2 and temporary Core3");
        for(int i=0;i<20;i++){turret=NativeTorbjornTuning.hammer(turret.level(),turret.progress());check(turret.level()==2&&turret.progress()==0&&!turret.upgraded(),"hammer cannot upgrade past2");}
        check(NativeTorbjornTuning.health(1,false)==150&&NativeTorbjornTuning.health(2,false)==300&&NativeTorbjornTuning.health(2,true)==800,"normal and temporary Core HP");
        check(NativeTorbjornTuning.effectiveLevel(2,true)==3&&NativeTorbjornTuning.effectiveLevel(2,false)==2,"temporary Core level");
        check(NativeTorbjornTuning.effectiveLevel(1,true)==1,"Core does not change stored tier1");
        var duringCore=NativeTorbjornTuning.hammer(1,50);
        check(duringCore.level()==2&&NativeTorbjornTuning.effectiveLevel(duringCore.level(),true)==3,"tier1 upgraded during Core becomes temporary3");
        check(NativeTorbjornTuning.effectiveLevel(duringCore.level(),false)==2&&NativeTorbjornTuning.health(duringCore.level(),false)==300,"Core End restores base2 and300HP cap");
        for(int base=1;base<=2;base++)for(int cycle=0;cycle<10;cycle++){
            int expected=base==2?3:1;
            check(NativeTorbjornTuning.effectiveLevel(base,true)==expected&&NativeTorbjornTuning.effectiveLevel(base,false)==base,"repeated Core does not promote base tier");
        }
        try{NativeTorbjornTuning.hammer(3,0);throw new AssertionError("base3 admitted");}catch(IllegalArgumentException expected){checks++;}
        try{NativeTorbjornTuning.effectiveLevel(3,false);throw new AssertionError("permanent3 admitted");}catch(IllegalArgumentException expected){checks++;}
        var owner=UUID.randomUUID();var other=UUID.randomUUID();
        check(!NativeTorbjornTuning.recipient(owner,owner,true,false),"owner always excluded");
        check(NativeTorbjornTuning.recipient(owner,other,true,false),"other alive recipient");
        check(!NativeTorbjornTuning.recipient(owner,other,false,false)&&!NativeTorbjornTuning.recipient(owner,other,true,true),"dead/spectator excluded");
        check(!NativeTorbjornTuning.recipient(null,other,true,false)&&!NativeTorbjornTuning.recipient(owner,null,true,false),"unknown identity excluded");

        var junk=inspect("NativeJunkratRuntime");var blast=junk.get("explode");
        int terrain=blast.ops.indexOf("C:lab/owmcguest/NativeTerrainBurst.explode");
        int damage=blast.ops.lastIndexOf("C:lab/owmcguest/NativeDamageTargets.explosionDamage");
        check(terrain>damage&&damage>=0,"real damage and cover before terrain");
        check(Collections.frequency(blast.ops,"C:lab/owmcguest/NativeTerrainBurst.explode")==1,"one shared terrain burst per grenade");
        check(guarded(blast,"lab/owmcguest/NativeJunkratRuntime$Kind.GRENADE",terrain),"mines/traps/death bombs cannot enter grenade terrain");
        check(junk.values().stream().noneMatch(m->m.ops.stream().anyMatch(op->op.endsWith(".createExplosion"))),"no duplicated local destruction implementation");
        check(junk.get("tick").ops.contains("C:lab/owmcguest/NativeJunkratGrenadeTuning.expired"),"runtime uses tuned fuse");
        check(junk.get("tick").ops.contains("C:lab/owmcguest/NativeJunkratGrenadeTuning.groundContact"),"actual block collision arms first-ground fuse");
        int direct=junk.get("tick").ops.indexOf("C:lab/owmcguest/NativeDamageTargets.projectileDamage");
        check(direct>=0&&junk.get("tick").ops.subList(0,direct).contains("C:lab/owmcguest/NativeJunkratGrenadeTuning.damage"),"direct hit uses doubled damage immediately");
        int tuned=blast.ops.indexOf("C:lab/owmcguest/NativeJunkratGrenadeTuning.damage");
        check(tuned>=0&&guarded(blast,"lab/owmcguest/NativeJunkratRuntime$Kind.GRENADE",tuned),"mine/passive damage remains native base");
        int mineImpulse=blast.ops.indexOf("C:lab/owmcguest/NativeRocketSelfImpulse.concussiveMine");
        check(mineImpulse>=0&&Collections.frequency(blast.ops,"C:lab/owmcguest/NativeRocketSelfImpulse.concussiveMine")==1,"mine uses one shared impulse");
        check(guarded(blast,"lab/owmcguest/NativeJunkratRuntime$Kind.MINE",mineImpulse),"grenade/passive cannot request mine impulse");
        check(blast.ops.subList(0,mineImpulse).contains("F:lab/owmcguest/NativeJunkratRuntime$Body.nativePid")
            &&blast.ops.subList(0,mineImpulse).contains("F:lab/owmcguest/NativeJunkratRuntime$Body.nativeTick"),"mine passes stored authenticated throw identity");
        check(blast.ops.stream().noneMatch(op->op.endsWith(".addVelocity")||op.endsWith(".velocityModified")||op.endsWith(".isOnGround")),"no duplicate local kick or jump prerequisite");
        check(junk.get("detonateMine").ops.contains("C:lab/owmcguest/NativeJunkratRuntime.current")
            &&junk.get("detonateMine").ops.contains("C:lab/owmcguest/NativeJunkratRuntime$Scope.equals"),"adapted detonation validates full scope");
        check(junk.get("cast").ops.contains("F:lab/owmcguest/NativeJunkratRuntime$Body.nativePid")
            &&junk.get("cast").ops.contains("F:lab/owmcguest/NativeJunkratRuntime$Body.nativeTick"),"cast stores native identity for delayed blast");
        var render=inspect("JunkratRenderer").get("render");int field=render.ops.lastIndexOf("F:lab/owmcguest/NativeJunkratRuntime$Kind.GRENADE");
        int scale=-1;for(int i=field+1;i<render.ops.size();i++)if(render.ops.get(i).equals("C:net/minecraft/client/util/math/MatrixStack.scale")){scale=i;break;}
        check(scale>=0&&guarded(render,"lab/owmcguest/NativeJunkratRuntime$Kind.GRENADE",scale),"scale only admitted left grenade geometry");
        var torb=inspect("NativeTorbjornRuntime");
        check(torb.get("hammer").ops.contains("C:lab/owmcguest/NativeTorbjornTuning.hammer"),"runtime uses full upgrade state machine");
        check(torb.get("endCore").ops.contains("C:lab/owmcguest/NativeTorbjornTuning.health"),"Core End restores stored tier health");
        check(torb.values().stream().anyMatch(m->m.ops.contains("C:lab/owmcguest/NativeTorbjornTuning.recipient")),"actual pickup filter uses owner exclusion");
        System.out.println("NativeBuildersTuningCheck passed: "+checks+" assertions");
    }
}
