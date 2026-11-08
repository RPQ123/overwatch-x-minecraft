package lab.owmcguest;

import java.lang.reflect.*;
import java.util.*;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.entity.model.*;
import net.minecraft.client.util.math.MatrixStack;

/** Copies the engine's actual cuboid faces and UVs, without modifying shared
 * model transforms/visibility, ticking entities, touching GL or generating PNGs. */
public final class SoulHeadGeometry {
    public static final int MAX_VERTICES=8192,MAX_CUBOIDS=2048;
    public enum Mode { FULL,NAMED_HEAD,ROOT_CUBOIDS }
    public record Selection(List<ModelPart> roots,Mode mode,String via){public Selection{roots=List.copyOf(roots);}}
    public record Vertex(float x,float y,float z,float u,float v,float nx,float ny,float nz){}
    public record Mesh(List<Vertex> vertices){public Mesh{vertices=List.copyOf(vertices);}}
    public static boolean headName(String name){
        String n=name.replaceAll("([a-z0-9])([A-Z])","$1_$2").toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+","_");
        return n.matches("(?:.*_)?(?:heads?|skulls?|cranium)(?:[0-9]+)?(?:_.*)?")
            ||Set.of("beak","wattle","red_thing").contains(n);
    }
    private static boolean headPath(String path){for(String s:path.split("[/.]"))if(headName(s))return true;return false;}
    private static List<ModelPart> unique(Iterable<ModelPart> parts){
        var set=Collections.newSetFromMap(new IdentityHashMap<ModelPart,Boolean>());var out=new ArrayList<ModelPart>();
        for(var p:parts)if(p!=null&&set.add(p)){out.add(p);if(out.size()>64)throw new IllegalArgumentException("head part limit");}
        // A separately exposed descendant must not duplicate a parent's faces.
        var remove=Collections.newSetFromMap(new IdentityHashMap<ModelPart,Boolean>());
        for(var p:out)p.traverse().filter(c->c!=p&&set.contains(c)).forEach(remove::add);
        out.removeIf(remove::contains);return out;
    }
    public static Selection select(Object model,String type)throws ReflectiveOperationException{
        if(model==null)throw new IllegalArgumentException("renderer has no model");
        if(model instanceof SoulAnimalHeadParts animal){var parts=unique(animal.owmc$soulHeadParts());if(!parts.isEmpty())return new Selection(parts,Mode.FULL,"AnimalModel mapped head parts");}
        if(model instanceof ModelWithHead headed)return new Selection(List.of(headed.getHead()),Mode.FULL,"ModelWithHead");
        var roots=new ArrayList<ModelPart>();var named=new ArrayList<ModelPart>();int fields=0;
        if(model instanceof SinglePartEntityModel<?> single)roots.add(single.getPart());
        for(Class<?> c=model.getClass();c!=null&&c!=Object.class;c=c.getSuperclass())for(var f:c.getDeclaredFields()){
            if(++fields>256)throw new IllegalArgumentException("model field limit");
            if(Modifier.isStatic(f.getModifiers()))continue;
            if(f.getType()==ModelPart[].class&&headName(f.getName())&&f.trySetAccessible()){
                var array=(ModelPart[])f.get(model);if(array!=null){if(array.length>64)throw new IllegalArgumentException("head array limit");named.addAll(Arrays.asList(array));}continue;
            }
            if(!ModelPart.class.isAssignableFrom(f.getType()))continue;
            if(!f.trySetAccessible())continue;var p=(ModelPart)f.get(model);if(p==null)continue;roots.add(p);if(headName(f.getName()))named.add(p);
        }
        if(!named.isEmpty())return new Selection(unique(named),Mode.FULL,"head model fields");
        roots=new ArrayList<>(unique(roots));
        for(var root:roots){final boolean[] found={false};final int[] visited={0};root.forEachCuboid(new MatrixStack(),(entry,path,index,box)->{if(++visited[0]>MAX_CUBOIDS)throw new IllegalArgumentException("model cuboid limit");if(headPath(path))found[0]=true;});
            if(found[0])return new Selection(List.of(root),Mode.NAMED_HEAD,"named head bone path");}
        // These creatures' face lives in their main cube, not a separate head.
        if(model instanceof SinglePartEntityModel<?> single){
            if(model instanceof SlimeEntityModel<?>||type.equals("minecraft:magma_cube"))return new Selection(List.of(single.getPart()),Mode.FULL,"face-bearing cube model");
            if(Set.of("minecraft:ghast","minecraft:bee","minecraft:squid","minecraft:glow_squid","minecraft:cod","minecraft:salmon","minecraft:pufferfish","minecraft:tropical_fish").contains(type)){
                for(String body:List.of("body","body_front","front_body","body1")){var part=single.getChild(body);if(part.isPresent())return new Selection(List.of(part.get()),Mode.ROOT_CUBOIDS,"integrated face/body cuboid");}
            }
        }
        // A lone torso cuboid is not evidence of a head/face UV layout.
        throw new IllegalArgumentException("no identifiable head ModelPart/bone");
    }
    public static Mesh capture(Selection selected){
        var collector=new Collector();var matrix=new MatrixStack();matrix.scale(1,-1,-1);final int[] count={0};
        for(var root:selected.roots())root.forEachCuboid(matrix,(entry,path,index,box)->{
            if(++count[0]>MAX_CUBOIDS)throw new IllegalArgumentException("model cuboid limit");
            if(selected.mode()==Mode.NAMED_HEAD&&!headPath(path)||selected.mode()==Mode.ROOT_CUBOIDS&&!path.isEmpty())return;
            box.renderCuboid(entry,collector,0x00f000f0,0,0xffffffff);
        });
        if(collector.vertices.isEmpty()||collector.vertices.size()%4!=0)throw new IllegalArgumentException("empty/incomplete head geometry");
        return new Mesh(collector.vertices);
    }
    public static List<Mesh> normalize(List<Mesh> meshes,float extent){
        if(!Float.isFinite(extent)||extent<=0||extent>1)throw new IllegalArgumentException("head extent");
        float[] lo={Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY},hi={Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY};
        for(var m:meshes)for(var v:m.vertices()){lo[0]=Math.min(lo[0],v.x());lo[1]=Math.min(lo[1],v.y());lo[2]=Math.min(lo[2],v.z());hi[0]=Math.max(hi[0],v.x());hi[1]=Math.max(hi[1],v.y());hi[2]=Math.max(hi[2],v.z());}
        float size=Math.max(hi[0]-lo[0],Math.max(hi[1]-lo[1],hi[2]-lo[2]));if(!Float.isFinite(size)||size<1e-5)throw new IllegalArgumentException("invalid head bounds");float s=extent/size;
        return meshes.stream().map(m->new Mesh(m.vertices().stream().map(v->new Vertex((v.x()-(lo[0]+hi[0])/2)*s,(v.y()-(lo[1]+hi[1])/2)*s,(v.z()-(lo[2]+hi[2])/2)*s,v.u(),v.v(),v.nx(),v.ny(),v.nz())).toList())).toList();
    }
    private static final class Collector implements VertexConsumer {
        final List<Vertex> vertices=new ArrayList<>();float x,y,z,u,v;
        public VertexConsumer vertex(float x,float y,float z){this.x=x;this.y=y;this.z=z;return this;}
        public VertexConsumer color(int r,int g,int b,int a){return this;}
        public VertexConsumer texture(float u,float v){this.u=u;this.v=v;return this;}
        public VertexConsumer overlay(int u,int v){return this;}
        public VertexConsumer light(int u,int v){return this;}
        public VertexConsumer normal(float nx,float ny,float nz){add(x,y,z,u,v,nx,ny,nz);return this;}
        @Override public void vertex(float x,float y,float z,int color,float u,float v,int overlay,int light,float nx,float ny,float nz){add(x,y,z,u,v,nx,ny,nz);}
        private void add(float x,float y,float z,float u,float v,float nx,float ny,float nz){
            if(vertices.size()>=MAX_VERTICES)throw new IllegalArgumentException("head vertex limit");
            for(float f:new float[]{x,y,z,u,v,nx,ny,nz})if(!Float.isFinite(f))throw new IllegalArgumentException("nonfinite head vertex");
            vertices.add(new Vertex(x,y,z,u,v,nx,ny,nz));
        }
    }
    private SoulHeadGeometry(){}
}
