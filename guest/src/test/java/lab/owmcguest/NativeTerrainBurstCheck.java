package lab.owmcguest;

import java.util.*;
import net.minecraft.world.World;
import net.minecraft.world.explosion.Explosion;
import net.minecraft.block.AbstractBlock;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.server.world.ServerChunkManager;
import net.minecraft.server.world.ChunkHolder;
import org.objectweb.asm.*;

/** Verify actual vanilla silent destruction still reaches normal block packets. */
public final class NativeTerrainBurstCheck {
    private record Call(String owner,String name,String descriptor){}
    private static final class MethodFact {
        final String name,descriptor;final List<Call> calls=new ArrayList<>();final List<String> ops=new ArrayList<>();final Set<String> created=new HashSet<>();
        MethodFact(String name,String descriptor){this.name=name;this.descriptor=descriptor;}
        boolean calls(String method){return calls.stream().anyMatch(c->c.name().equals(method));}
    }
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static List<MethodFact> inspect(Class<?> type)throws Exception{return inspect(type,type.getSimpleName()+".class");}
    private static List<MethodFact> inspect(Class<?> type,String resource)throws Exception{
        var all=new ArrayList<MethodFact>();
        try(var input=type.getResourceAsStream(resource)){
            check(input!=null,"actual class resource: "+resource);
            new ClassReader(input).accept(new ClassVisitor(Opcodes.ASM9){
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
                    var fact=new MethodFact(name,descriptor);all.add(fact);
                    return new MethodVisitor(Opcodes.ASM9){
                        @Override public void visitInsn(int opcode){fact.ops.add("I:"+opcode);}
                        @Override public void visitFieldInsn(int opcode,String owner,String field,String desc){fact.ops.add("F:"+owner+"."+field);}
                        @Override public void visitMethodInsn(int opcode,String owner,String method,String desc,boolean itf){fact.calls.add(new Call(owner,method,desc));fact.ops.add("C:"+owner+"."+method);}
                        @Override public void visitTypeInsn(int opcode,String owner){if(opcode==Opcodes.NEW)fact.created.add(owner);}
                    };
                }
            },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
        }
        return all;
    }
    static void verify()throws Exception{
        check(NativeExplosionTerrain.FLASHBANG==0&&NativeExplosionTerrain.CONCUSSIVE==0&&NativeExplosionTerrain.PULSE==3,"Explicit Flashbang/Concussive exemptions leave Pulse terrain strength intact");
        for(double strength=.01;strength<=4;strength+=.01)check(NativeTerrainBurst.reach(strength)>1.734*strength+.3,"Loaded preflight encloses vanilla maximum empty-air ray distance");
        for(double invalid:new double[]{0,-1,4.01,Double.NaN,Double.POSITIVE_INFINITY}){
            check(!NativeTerrainBurst.validStrength(invalid),"Invalid/unbounded helper strength refused");
            try{NativeTerrainBurst.reach(invalid);throw new AssertionError("invalid reach accepted");}catch(IllegalArgumentException expected){}
        }
        check(!NativeTerrainBurst.explode(null,null,null,.6).applied(),"Missing actual world/player cannot create terrain work");
        // A new hole cannot retroactively change this same blast's cover,
        // status or impulse decision, nor can a cosmetic replay own terrain.
        for(var handler:List.of(NativeFlashbangRuntime.class,NativeConcussiveRuntime.class)){
            var methods=inspect(handler);
            check(methods.stream().noneMatch(m->m.calls.stream().anyMatch(c->c.owner().equals("lab/owmcguest/NativeTerrainBurst")&&c.name().equals("explode")||c.name().equals("createExplosion"))),"Explicitly exempt control grenade has no added explosion call anywhere: "+handler.getSimpleName());
            var effect=methods.stream().filter(m->m.name.equals("detonate")).findFirst().orElseThrow();
            check(effect.calls("explosionDamage"),"Exemption preserves existing real control grenade damage");
        }
        for(var handler:List.of(NativePulseRuntime.class)){
            var method=inspect(handler).stream().filter(m->m.name.equals("detonate")).findFirst().orElseThrow();
            int terrain=method.ops.indexOf("C:lab/owmcguest/NativeTerrainBurst.explode");
            int damage=-1,status=-1,impulse=-1;
            for(int j=0;j<method.ops.size();j++){
                var op=method.ops.get(j);
                if(op.equals("C:lab/owmcguest/NativeDamageTargets.explosionDamage"))damage=j;
                if(op.endsWith(".addStatusEffect"))status=j;
                if(op.endsWith(".setVelocity"))impulse=j;
            }
            check(terrain>damage&&damage>=0,"Actual skill damage and cover decisions precede terrain: "+handler.getSimpleName());
        }
        var local=inspect(World.class).stream().filter(m->m.name.equals("createExplosion")&&m.descriptor.contains("Lnet/minecraft/world/World$ExplosionSourceType;Z")&&m.calls("collectBlocksAndDamageEntities")&&m.calls("affectWorld")).findFirst().orElseThrow();
        check(!local.created.contains("net/minecraft/network/packet/s2c/play/ExplosionS2CPacket"),"Silent World explosion does not create a duplicate presentation packet");
        var helper=inspect(NativeTerrainBurst.class).stream().filter(m->m.name.equals("explode")).findFirst().orElseThrow();
        var helperCalls=helper.calls.stream().filter(c->c.name().equals("createExplosion")).toList();
        check(helperCalls.size()==1&&helperCalls.getFirst().descriptor().equals(local.descriptor),"Terrain helper chooses exactly the actual World local-only overload");
        int mode=helper.ops.indexOf("F:net/minecraft/world/World$ExplosionSourceType.TNT");
        check(mode>=0&&helper.ops.get(mode+1).equals("I:"+Opcodes.ICONST_0),"Particles=false follows actual TNT destruction mode in helper bytecode");
        var behavior=inspect(NativeTerrainBurst.class,"NativeTerrainBurst$1.class");
        var damage=behavior.stream().filter(m->m.name.equals("shouldDamage")).findFirst().orElseThrow();
        var knockback=behavior.stream().filter(m->m.name.equals("getKnockbackModifier")).findFirst().orElseThrow();
        check(damage.ops.equals(List.of("I:"+Opcodes.ICONST_0,"I:"+Opcodes.IRETURN))&&knockback.ops.equals(List.of("I:"+Opcodes.FCONST_0,"I:"+Opcodes.FRETURN)),"Helper adds neither duplicate entity damage nor guessed impulse");
        var resistance=behavior.stream().filter(m->m.name.equals("getBlastResistance")).findFirst().orElseThrow();
        var breakable=behavior.stream().filter(m->m.name.equals("canDestroyBlock")).findFirst().orElseThrow();
        check(resistance.calls("isChunkLoaded")&&resistance.calls("getBlastResistance")&&breakable.calls("isChunkLoaded")&&breakable.calls("breakable")&&breakable.calls("canDestroyBlock"),"Real helper preserves loaded/unbreakable guards and vanilla resistance/block eligibility");
        var affect=inspect(Explosion.class).stream().filter(m->m.name.equals("affectWorld")).findFirst().orElseThrow();
        check(affect.calls("onExploded")&&affect.calls("dropStack"),"Actual vanilla destruction callback and drops remain in silent affectWorld");
        var block=inspect(AbstractBlock.class).stream().filter(m->m.name.equals("onExploded")&&m.calls("setBlockState")).findFirst().orElseThrow();
        int set=block.ops.indexOf("C:net/minecraft/world/World.setBlockState");
        check(set>0&&block.ops.get(set-1).equals("I:"+Opcodes.ICONST_3)&&block.calls("getDroppedStacks"),"Actual block explosion uses NOTIFY_ALL=3 and vanilla loot");
        check(inspect(World.class).stream().anyMatch(m->m.name.equals("setBlockState")&&m.calls("updateListeners")),"World block-state changes notify listeners");
        check(inspect(ServerWorld.class).stream().anyMatch(m->m.name.equals("updateListeners")&&m.calls("markForUpdate")),"Actual ServerWorld listener schedules network block update");
        check(inspect(ServerChunkManager.class).stream().anyMatch(m->m.name.equals("markForUpdate")&&m.calls("markForBlockUpdate")),"Chunk manager records affected block");
        check(inspect(ChunkHolder.class).stream().anyMatch(m->m.created.contains("net/minecraft/network/packet/s2c/play/BlockUpdateS2CPacket")&&m.created.contains("net/minecraft/network/packet/s2c/play/ChunkDeltaUpdateS2CPacket")&&m.calls("sendPacketToPlayers")),"Actual ChunkHolder sends single/delta block packets without needing ExplosionS2CPacket");
    }
    public static void main(String[] args)throws Exception{verify();System.out.println("PASS: silent terrain-only vanilla blast, radius bounds, no duplicate damage/impulse and actual NOTIFY_ALL block packet chain");}
}
