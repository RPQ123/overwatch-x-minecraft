package lab.owmcguest;

import java.lang.reflect.Method;
import java.util.*;
import net.minecraft.server.world.ServerWorld;
import org.objectweb.asm.*;

/** Bind the actual game dependency's packet-producing override, without a UI. */
public final class RocketExplosionTransportCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static NativeShotProtocol.Shot shot(NativeShotProtocol.Effect effect,boolean rocket,boolean barrage){
        return new NativeShotProtocol.Shot(1,0,1000,new NativeShotProtocol.Vec(0,1,0),new NativeShotProtocol.Vec(0,0,60),50,5,false,100,"terrain-policy-fixture",false,rocket,effect,
            barrage?List.of(new PharahBarrageMotion.Wave(0,.2,.5,.5,1,20,true)):List.of());
    }
    private static void terrainPolicy(){
        var tankEffect=new NativeShotProtocol.Effect(0x02e0000000000015L,0x04000000000003ceL,1,0,140,4,0,0,0,1,.30000001192092896);
        var helixEffect=new NativeShotProtocol.Effect(0x02e000000000006eL,0x040000000000072cL,1,0,80,3,0,0,0,1,.5);
        var barrageEffect=new NativeShotProtocol.Effect(0x02e0000000000008L,0x0400000000000052L,1,0,30,1.5,0,0,0,.5,.3);
        var primary=shot(null,true,false);var tank=shot(tankEffect,false,false);var helix=shot(helixEffect,false,false);var barrage=shot(barrageEffect,false,true);
        check(NativeExplosionTerrain.strength(primary)==2.5&&NativeExplosionTerrain.strength(tank)==2&&NativeExplosionTerrain.strength(helix)==1.5&&NativeExplosionTerrain.strength(barrage)==.6,"User terrain strengths distinguish primary/Tank/Helix/Barrage");
        for(var s:List.of(primary,tank,helix,barrage))check(NativeExplosionTerrain.strength(s)>0&&Double.isFinite(NativeExplosionTerrain.strength(s)),"Every real shot explosion has bounded positive terrain work");
        check(tank.effect().equals(tankEffect)&&tank.effect().terrain()==0&&tank.nativeDamage()==50&&tank.effect().splash()==140&&tank.effect().innerRadius()==1&&tank.effect().radius()==4,"User terrain does not rewrite original native Tank damage/rings/zero metadata");
        for(double configured:new double[]{0,-1,Double.NaN,Double.POSITIVE_INFINITY,.0001,1.75,20}){
            var generic=new NativeShotProtocol.Effect(0x02e0000000000065L,0x0400000000000123L,1,0,25,2,0,0,configured,0,.3);
            double value=NativeExplosionTerrain.strength(shot(generic,false,false));
            check(Double.isFinite(value)&&value>=.25&&value<=4,"Unknown effect1 still gets safe positive terrain fallback");
            if(configured==1.75)check(value==configured,"Existing explicit MC preference remains available to generic adapters");
        }
        check(NativeExplosionTerrain.breakable(0)&&NativeExplosionTerrain.breakable(1.5)&&!NativeExplosionTerrain.breakable(-1)&&!NativeExplosionTerrain.breakable(Double.NaN)&&!NativeExplosionTerrain.breakable(Double.POSITIVE_INFINITY),"Air/ordinary hardness eligible; bedrock/unbreakable/nonfinite refused");
    }
    private static void nativeBlastSafety()throws Exception{
        var damageCode=new ArrayList<Integer>();var knockbackCode=new ArrayList<Integer>();boolean[] vanillaResistance={false},vanillaBreak={false},userBreak={false},loadedResistance={false},loadedBreak={false};
        try(var input=NativeRocketExplosion.class.getResourceAsStream("NativeRocketExplosion$1.class")){
            check(input!=null,"Actual terrain-only explosion behavior exists");
            new ClassReader(input).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitInsn(int opcode){if(name.equals("shouldDamage"))damageCode.add(opcode);if(name.equals("getKnockbackModifier"))knockbackCode.add(opcode);}
                        @Override public void visitMethodInsn(int opcode,String owner,String method,String desc,boolean itf){
                            if(name.equals("getBlastResistance")&&owner.equals("net/minecraft/world/explosion/ExplosionBehavior")&&method.equals("getBlastResistance"))vanillaResistance[0]=true;
                            if(name.equals("canDestroyBlock")&&owner.equals("net/minecraft/world/explosion/ExplosionBehavior")&&method.equals("canDestroyBlock"))vanillaBreak[0]=true;
                            if(name.equals("canDestroyBlock")&&owner.equals("lab/owmcguest/NativeExplosionTerrain")&&method.equals("breakable"))userBreak[0]=true;
                            if(method.equals("isChunkLoaded")){if(name.equals("getBlastResistance"))loadedResistance[0]=true;if(name.equals("canDestroyBlock"))loadedBreak[0]=true;}
                        }
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        check(damageCode.equals(List.of(Opcodes.ICONST_0,Opcodes.IRETURN)),"Vanilla terrain explosion cannot apply second entity damage");
        check(knockbackCode.equals(List.of(Opcodes.FCONST_0,Opcodes.FRETURN)),"No guessed vanilla/self knockback is added");
        check(vanillaResistance[0]&&vanillaBreak[0]&&userBreak[0],"Real vanilla resistance/destruction decision plus unbreakable guard remain in actual blast behavior");
        check(loadedResistance[0]&&loadedBreak[0],"Actual resistance and block destruction behavior each guard loaded chunks");
    }
    public static void main(String[] args)throws Exception{
        var overrides=new HashSet<String>();
        for(Method m:ServerWorld.class.getDeclaredMethods())if(m.getName().equals("createExplosion"))overrides.add(Type.getMethodDescriptor(m));
        check(!overrides.isEmpty(),"actual ServerWorld declares a synced explosion override");
        var packetMethods=new HashSet<String>();
        try(var input=ServerWorld.class.getResourceAsStream("ServerWorld.class")){
            new ClassReader(input).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitTypeInsn(int opcode,String type){
                            if(name.equals("createExplosion")&&opcode==Opcodes.NEW&&type.equals("net/minecraft/network/packet/s2c/play/ExplosionS2CPacket"))packetMethods.add(descriptor);
                        }
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        overrides.retainAll(packetMethods);check(!overrides.isEmpty(),"actual override creates the client explosion packet");
        int[] networkCalls={0},localCalls={0},policyCalls={0},terrainMode={0};
        try(var input=NativeRocketExplosion.class.getResourceAsStream("NativeRocketExplosion.class")){
            new ClassReader(input).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitMethodInsn(int opcode,String owner,String method,String desc,boolean itf){
                            if(name.equals("explode")&&method.equals("createExplosion")){
                                if(overrides.contains(desc))networkCalls[0]++;else localCalls[0]++;
                            }
                            if(name.equals("explode")&&owner.equals("lab/owmcguest/NativeExplosionTerrain")&&method.equals("strength"))policyCalls[0]++;
                        }
                        @Override public void visitFieldInsn(int opcode,String owner,String field,String descriptor){if(name.equals("explode")&&owner.equals("net/minecraft/world/World$ExplosionSourceType")&&field.equals("TNT"))terrainMode[0]++;}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        check(networkCalls[0]==1&&localCalls[0]==0,"All shot explosions share exactly one packet-producing ServerWorld overload, no inherited local-only route");
        check(policyCalls[0]==1&&terrainMode[0]==1,"Actual synced shot explosion always uses the separate MC terrain policy and destruction mode");
        terrainPolicy();nativeBlastSafety();NativeTerrainBurstCheck.verify();
        System.out.println("PASS: synced all-shot terrain explosions, distinct user strengths, unchanged native metadata, vanilla resistance/unbreakable safety and no duplicate entity damage/knockback");
    }
}
