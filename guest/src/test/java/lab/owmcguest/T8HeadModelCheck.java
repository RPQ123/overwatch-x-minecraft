package lab.owmcguest;

import java.nio.file.*;
import java.util.*;
import com.google.gson.*;
import net.minecraft.client.model.*;
import net.minecraft.client.render.entity.model.*;
import net.minecraft.entity.data.*;
import net.minecraft.util.math.Direction;

/** Exercises actual vanilla model builders/cuboid UVs without constructing a
 * MinecraftClient, window, world, renderer, OpenGL context or game process. */
public final class T8HeadModelCheck {
    private static int checks;private static final JsonArray rows=new JsonArray();
    private static void check(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
    private static void near(double a,double b){check(Math.abs(a-b)<1e-6,a+" != "+b);}
    private static SoulHeadGeometry.Mesh exercise(String type,Object model)throws Exception{
        var selected=SoulHeadGeometry.select(model,type);var mesh=SoulHeadGeometry.capture(selected);check(!mesh.vertices().isEmpty()&&mesh.vertices().size()%4==0,type+" complete head quads");
        var normalized=SoulHeadGeometry.normalize(List.of(mesh),SoulHeadVisual.MESH_EXTENT).getFirst();double[] lo={999,999,999},hi={-999,-999,-999};
        var uvs=new HashSet<String>();
        for(int i=0;i<mesh.vertices().size();i++){
            var original=mesh.vertices().get(i);var v=normalized.vertices().get(i);near(original.u(),v.u());near(original.v(),v.v());uvs.add(v.u()+":"+v.v());
            double[] pos={v.x(),v.y(),v.z()};for(int axis=0;axis<3;axis++){lo[axis]=Math.min(lo[axis],pos[axis]);hi[axis]=Math.max(hi[axis],pos[axis]);}
            check(Float.isFinite(v.nx())&&Float.isFinite(v.ny())&&Float.isFinite(v.nz()),type+" finite normals");
        }
        near(Math.max(hi[0]-lo[0],Math.max(hi[1]-lo[1],hi[2]-lo[2])),.30);for(int axis=0;axis<3;axis++)near(lo[axis]+hi[axis],0);
        check(uvs.size()>=4,type+" original skin UV layout retained");
        var row=new JsonObject();row.addProperty("type",type);row.addProperty("model",model.getClass().getSimpleName());row.addProperty("via",selected.via());row.addProperty("vertices",mesh.vertices().size());row.addProperty("uvPairs",uvs.size());row.addProperty("extent",.30);rows.add(row);return mesh;
    }
    /** Simulates an obfuscated model field, but retains real mod bone labels. */
    private record ModRig(ModelPart a){}
    private record HeadFields(ModelPart head,ModelPart realHead){}
    private record MappedAnimal(List<ModelPart> parts)implements SoulAnimalHeadParts{public Iterable<ModelPart> owmc$soulHeadParts(){return parts;}}
    private static ModelPart rig(boolean head){
        var data=new ModelData();var root=data.getRoot();root.addChild("body",ModelPartBuilder.create().uv(0,16).cuboid(-4,0,-4,8,12,8),ModelTransform.NONE);
        if(head){var h=root.addChild("Head_Main",ModelPartBuilder.create().uv(16,0).cuboid(-4,-8,-4,8,8,8),ModelTransform.NONE);h.addChild("horn",ModelPartBuilder.create().uv(0,0).cuboid(3,-10,-1,2,4,2),ModelTransform.NONE);}
        return TexturedModelData.of(data,64,64).createModel();
    }
    private static final class Data implements DataTracked{
        public void onTrackedDataSet(TrackedData<?> data){}
        public void onDataTrackerUpdate(List<DataTracker.SerializedEntry<?>> entries){}
    }
    private static DataTracker standaloneTracker(TrackedData<String> key)throws Exception{
        // Test-only direct entry construction: exercise real tracker copy/dirty
        // behavior without bootstrapping Minecraft registries or a game world.
        var ctor=DataTracker.class.getDeclaredConstructor(DataTracked.class,DataTracker.Entry[].class);ctor.setAccessible(true);
        return ctor.newInstance(new Data(),new DataTracker.Entry<?>[]{new DataTracker.Entry<>(key,"default")});
    }
    public static void main(String[] args)throws Exception{
        exercise("minecraft:pig",new PigEntityModel<>(PigEntityModel.getTexturedModelData(Dilation.NONE).createModel()));
        exercise("minecraft:cow",new CowEntityModel<>(CowEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:sheep",new SheepEntityModel<>(SheepEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:sheep_fleece",new SheepWoolEntityModel<>(SheepWoolEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:chicken",new ChickenEntityModel<>(ChickenEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:wolf",new WolfEntityModel<>(TexturedModelData.of(WolfEntityModel.getTexturedModelData(Dilation.NONE),64,32).createModel()));
        exercise("minecraft:spider",new SpiderEntityModel<>(SpiderEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:enderman",new EndermanEntityModel<>(EndermanEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:blaze",new BlazeEntityModel<>(BlazeEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:villager",new VillagerResemblingModel<>(TexturedModelData.of(VillagerResemblingModel.getModelData(),64,64).createModel()));
        exercise("minecraft:iron_golem",new IronGolemEntityModel<>(IronGolemEntityModel.getTexturedModelData().createModel()));
        exercise("minecraft:slime",new SlimeEntityModel<>(SlimeEntityModel.getInnerTexturedModelData().createModel()));
        exercise("minecraft:slime_outer",new SlimeEntityModel<>(SlimeEntityModel.getOuterTexturedModelData().createModel()));
        var root=rig(true);var mod=new ModRig(root);var mesh=exercise("examplemod:horned_animal",mod);
        check(mesh.vertices().size()==48,"mod head+horn only, body excluded");
        var head=root.getChild("Head_Main");var horn=head.getChild("horn");
        var duplicate=exercise("examplemod:exposed_head_and_child",new HeadFields(head,horn));check(duplicate.vertices().size()==48,"no duplicate descendant faces");
        exercise("examplemod:mapped_animal_provider",new MappedAnimal(List.of(head)));
        var copied=List.copyOf(mesh.vertices());head.pivotY=123;head.yaw=2;check(copied.equals(mesh.vertices()),"captured geometry survives shared model reuse/death");
        boolean refused=false;try{SoulHeadGeometry.select(new ModRig(rig(false)),"examplemod:no_identifiable_head");}catch(IllegalArgumentException expected){refused=true;}check(refused,"fallback only after head lookup fails");
        for(String name:new String[]{"head","Head_Main","mainHead","skull2","real_head","heads"})check(SoulHeadGeometry.headName(name),"mod head label "+name);
        check(!SoulHeadGeometry.headName("body")&&!SoulHeadGeometry.headName("left_leg"),"body/leg not mistaken for head");
        var oversized=new ModelData();var part=ModelPartBuilder.create();for(int i=0;i<400;i++)part.uv(0,0).cuboid(0,0,0,8,8,8);oversized.getRoot().addChild("head",part,ModelTransform.NONE);
        refused=false;try{SoulHeadGeometry.capture(new SoulHeadGeometry.Selection(List.of(TexturedModelData.of(oversized,64,64).createModel().getChild("head")),SoulHeadGeometry.Mode.FULL,"oversized"));}catch(IllegalArgumentException expected){refused=true;}check(refused,"bounded geometry allocation");
        // Appearance copy must not consume packets needed by the real client.
        var handler=new TrackedDataHandler<String>(){
            public net.minecraft.network.codec.PacketCodec<? super net.minecraft.network.RegistryByteBuf,String> codec(){throw new AssertionError("fixture never serializes network packets");}
            public String copy(String value){return value;}
        };
        var key=new TrackedData<String>(0,handler);var tracker=standaloneTracker(key);tracker.set(key,"variant-B");
        var changed=tracker.getChangedEntries();check(changed!=null&&changed.size()==1&&tracker.isDirty(),"snapshot preserves network dirty state");
        check(tracker.getDirtyEntries().size()==1&&!tracker.isDirty(),"normal client packet is still available");
        var other=standaloneTracker(key);other.writeUpdatedEntries(changed);check(other.get(key).equals("variant-B"),"detached proxy preserves tracked skin variant");
        check(SoulHeadVisual.kind("minecraft:cow",false,false)==SoulHeadVisual.Kind.ENTITY&&SoulHeadVisual.kind("examplemod:creature",false,false)==SoulHeadVisual.Kind.ENTITY,"all non-item species attempt own geometry");
        var out=new JsonObject();out.addProperty("passed",true);out.addProperty("fixtureOnly",true);out.addProperty("models",rows.size());out.addProperty("assertions",checks);out.addProperty("gameStarted",false);out.addProperty("gpuRenderingVerified",false);out.add("cases",rows);
        Files.writeString(Path.of(args[0]),out.toString());System.out.println("PASS T8 head models="+rows.size()+" assertions="+checks+"; real vanilla UVs,custom bones/composite heads,immutable snapshots,tracker dirty/variant preservation,geometry caps");
    }
}
