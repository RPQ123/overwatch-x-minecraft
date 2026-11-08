package lab.owmcguest;

import java.lang.reflect.*;
import java.util.*;
import com.google.gson.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.*;
import net.minecraft.client.render.entity.model.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.*;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.registry.Registries;
import net.minecraft.util.Identifier;

/** Per-victim immutable head meshes. Resolve once on the render thread, using
 * the victim renderer's texture. No copied textures, saves or world entity spawns. */
final class SoulEntityHeads {
    record Layer(Identifier texture,SoulHeadGeometry.Mesh mesh,int color,float alpha,boolean eyes){}
    record Head(List<Layer> layers,String type,String model,String via,String appearance,String error,int vertices,double captureMs){
        boolean fallback(){return !error.isEmpty();}
    }
    private static final Map<UUID,Head> cache=new LinkedHashMap<>();
    private record Case(UUID victim,Head head){}
    private static volatile List<Case> diagnosticSnapshot=List.of();
    private static NativeSoulRuntime.Scope scope;private static int budget;
    private static volatile long captured,fallbacks,frames;private static volatile double maxCaptureMs;
    private static void publish(){diagnosticSnapshot=cache.entrySet().stream().map(e->new Case(e.getKey(),e.getValue())).toList();}
    static void begin(NativeSoulRuntime.View view){
        if(view==null||!view.scope().equals(scope)){reset();scope=view==null?null:view.scope();}
        if(view!=null)cache.keySet().retainAll(view.orbs().stream().map(NativeSoulRuntime.Orb::victim).toList());
        publish();
        budget=2;
    }
    static void reset(){cache.clear();diagnosticSnapshot=List.of();scope=null;}
    static Head prepare(NativeSoulRuntime.Orb orb,MinecraftClient client){
        var old=cache.get(orb.victim());if(old!=null)return old;if(budget--<=0)return null;
        long start=System.nanoTime();String type="unknown",model="",appearance="";
        try{
            var source=orb.head().appearance();if(source==null)throw new IllegalArgumentException("victim appearance missing");
            type=Registries.ENTITY_TYPE.getId(source.type()).toString();
            Entity entity=client.world.getEntityById(source.entityId());
            if(entity==null||!entity.getUuid().equals(source.victim())){
                // A dead/untracked client entity may already be gone. Rebuild
                // a detached visual proxy from copied tracker values only.
                if(!source.error().isEmpty())throw new IllegalArgumentException("appearance capture: "+source.error());
                entity=source.type().create(client.world);if(entity==null)throw new IllegalArgumentException("client visual factory returned null");
                entity.setUuid(source.victim());entity.refreshPositionAndAngles(source.position().x,source.position().y,source.position().z,source.yaw(),source.pitch());entity.age=source.age();
                entity.getDataTracker().writeUpdatedEntries(source.tracked());appearance="detached tracked appearance";
            }else appearance="live client victim";
            if(!(entity instanceof LivingEntity living))throw new IllegalArgumentException("victim is not living");
            @SuppressWarnings("rawtypes") EntityRenderer renderer=client.getEntityRenderDispatcher().getRenderer(entity);
            @SuppressWarnings("unchecked") Identifier texture=renderer.getTexture(entity);
            if(texture==null||texture.getPath().contains("missingno"))throw new IllegalArgumentException("entity skin unavailable");
            // Resource-pack PNGs are validated without reading/copying pixels.
            // Generated mod textures may already be registered by their renderer.
            if(client.getResourceManager().getResource(texture).isEmpty()
                &&client.getTextureManager().getTexture(texture)==net.minecraft.client.texture.MissingSprite.getMissingSpriteTexture())throw new IllegalArgumentException("entity texture missing: "+texture);
            Object meshModel=model(renderer);model=meshModel==null?renderer.getClass().getName():meshModel.getClass().getName();
            var selected=SoulHeadGeometry.select(meshModel,type);var meshes=new ArrayList<SoulHeadGeometry.Mesh>();var textures=new ArrayList<Identifier>();var colors=new ArrayList<Integer>();var alphas=new ArrayList<Float>();var eyeLayers=new ArrayList<Boolean>();
            meshes.add(SoulHeadGeometry.capture(selected));textures.add(texture);colors.add(0xffffffff);alphas.add(1f);eyeLayers.add(false);
            String eyes=switch(type){case "minecraft:spider","minecraft:cave_spider"->"textures/entity/spider_eyes.png";case "minecraft:enderman"->"textures/entity/enderman/enderman_eyes.png";default->"";};
            if(!eyes.isEmpty()&&client.getResourceManager().getResource(Identifier.ofVanilla(eyes)).isPresent()){
                meshes.add(meshes.getFirst());textures.add(Identifier.ofVanilla(eyes));colors.add(0xffffffff);alphas.add(1f);eyeLayers.add(true);
            }
            if(living instanceof SheepEntity sheep&&!sheep.isSheared()){
                var wool=new SheepWoolEntityModel<>(SheepWoolEntityModel.getTexturedModelData().createModel());
                meshes.add(SoulHeadGeometry.capture(SoulHeadGeometry.select(wool,type)));textures.add(Identifier.ofVanilla("textures/entity/sheep/sheep_fur.png"));colors.add(0xff000000|SheepEntity.getRgbColor(sheep.getColor()));alphas.add(1f);eyeLayers.add(false);
            }
            if(type.equals("minecraft:slime")){
                var outer=new SlimeEntityModel<>(SlimeEntityModel.getOuterTexturedModelData().createModel());
                meshes.add(SoulHeadGeometry.capture(SoulHeadGeometry.select(outer,type)));textures.add(texture);colors.add(0xffffffff);alphas.add(.35f);eyeLayers.add(false);
            }
            var normalized=SoulHeadGeometry.normalize(meshes,SoulHeadVisual.MESH_EXTENT);var layers=new ArrayList<Layer>();int count=0;
            for(int i=0;i<normalized.size();i++){var m=normalized.get(i);count+=m.vertices().size();layers.add(new Layer(textures.get(i),m,colors.get(i),alphas.get(i),eyeLayers.get(i)));}
            double ms=(System.nanoTime()-start)/1_000_000.;maxCaptureMs=Math.max(maxCaptureMs,ms);captured++;
            var head=new Head(List.copyOf(layers),type,model,selected.via(),appearance,"",count,ms);cache.put(orb.victim(),head);publish();return head;
        }catch(Exception|LinkageError failure){
            String message=failure.getClass().getSimpleName()+": "+String.valueOf(failure.getMessage());if(message.length()>240)message=message.substring(0,240);
            double ms=(System.nanoTime()-start)/1_000_000.;maxCaptureMs=Math.max(maxCaptureMs,ms);fallbacks++;
            var head=new Head(List.of(),type,model,"skeleton fallback",appearance,message,0,ms);cache.put(orb.victim(),head);publish();return head;
        }
    }
    private static Object model(EntityRenderer<?> renderer)throws ReflectiveOperationException{
        if(renderer instanceof LivingEntityRenderer<?,?> living)return living.getModel();
        // Optional custom renderers: inspect only model/ModelPart data, never
        // invoke arbitrary render/animation/gameplay methods or register a mod.
        for(Class<?> c=renderer.getClass();c!=null&&c!=Object.class;c=c.getSuperclass())for(var field:c.getDeclaredFields()){
            if(Modifier.isStatic(field.getModifiers()))continue;
            if((EntityModel.class.isAssignableFrom(field.getType())||field.getName().equalsIgnoreCase("model")||field.getType().getSimpleName().endsWith("Model"))&&field.trySetAccessible()){
                var value=field.get(renderer);if(value!=null)return value;
            }
        }
        // A renderer can also directly own its ModelPart hierarchy.
        return renderer;
    }
    static void draw(Head head,MatrixStack matrices,VertexConsumerProvider.Immediate buffers){
        var entry=matrices.peek();
        for(var layer:head.layers()){
            var render=layer.eyes()?RenderLayer.getEyes(layer.texture()):RenderLayer.getEntityTranslucent(layer.texture());var out=buffers.getBuffer(render);int color=layer.color();int alpha=Math.round(((color>>>24)&255)*layer.alpha());
            for(var v:layer.mesh().vertices())out.vertex(entry.getPositionMatrix(),v.x(),v.y(),v.z()).color((color>>>16)&255,(color>>>8)&255,color&255,alpha)
                .texture(v.u(),v.v()).overlay(OverlayTexture.DEFAULT_UV).light(LightmapTextureManager.MAX_LIGHT_COORDINATE).normal(entry,v.nx(),v.ny(),v.nz());
            buffers.draw(render);
        }frames++;
    }
    static JsonObject diagnostics(){
        // /combat runs on an HTTP worker; never iterate the render-owned map or
        // make the render thread wait on diagnostic JSON serialization.
        var snapshot=diagnosticSnapshot;var out=new JsonObject();out.addProperty("captured",captured);out.addProperty("fallbacks",fallbacks);out.addProperty("frames",frames);out.addProperty("cached",snapshot.size());out.addProperty("meshExtent",SoulHeadVisual.MESH_EXTENT);out.addProperty("maxCaptureMs",maxCaptureMs);out.addProperty("captureBudgetPerFrame",2);out.addProperty("privateAssetsRequired",false);
        var entries=new JsonArray();snapshot.forEach(item->{var id=item.victim();var head=item.head();var row=new JsonObject();row.addProperty("victim",id.toString());row.addProperty("type",head.type());row.addProperty("model",head.model());row.addProperty("via",head.via());row.addProperty("appearance",head.appearance());row.addProperty("vertices",head.vertices());row.addProperty("fallback",head.fallback());row.addProperty("error",head.error());var textures=new JsonArray();head.layers().forEach(l->textures.add(l.texture().toString()));row.add("textures",textures);entries.add(row);});out.add("victims",entries);return out;
    }
}
