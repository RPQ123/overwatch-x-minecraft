package lab.owmcguest;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.util.ArrayList;
import java.util.List;

/** Versioned original-emission journal; no input buttons can create a shot. */
public final class NativeShotProtocol {
    /** Retry transport; never acknowledge a new pawn's journal as old-pawn rejects. */
    public static final class OwnerPending extends IllegalArgumentException {
        OwnerPending(){super("waiting for matching current native journal owner");}
    }
    public record Vec(double x,double y,double z) {
        public Vec add(Vec v){return new Vec(x+v.x,y+v.y,z+v.z);}
        public Vec subtract(Vec v){return new Vec(x-v.x,y-v.y,z-v.z);}
        public Vec multiply(double k){return new Vec(x*k,y*k,z*k);}
        public double lengthSquared(){return x*x+y*y+z*z;}
    }
    public record Expected(int nativePid,int mcPid,long hostGeneration,long mcGeneration,long worldId,double eyeHeight,long modelId,long hero) {
        public Expected(int nativePid,int mcPid,long hostGeneration,long mcGeneration,long worldId,double eyeHeight){this(nativePid,mcPid,hostGeneration,mcGeneration,worldId,eyeHeight,0,0);}
    }
    public record Source(int pid,long creation,long epoch,long hostGeneration) {}
    public record Effect(long hero,long resource,int kind,double gravity,double splash,double radius,int bounces,double fuse,double terrain,double innerRadius,double outerScale){
        public Effect(long hero,long resource,int kind,double gravity,double splash,double radius,int bounces,double fuse,double terrain){this(hero,resource,kind,gravity,splash,radius,bounces,fuse,terrain,0,.125);}
    }
    public record Shot(long id,long nativeEntity,long wallMs,Vec start,Vec velocity,double nativeDamage,double lifetime,boolean hitscan,double range,String identity,boolean beam,boolean rocket,Effect effect,List<PharahBarrageMotion.Wave> waves) {
        public Shot(long id,long nativeEntity,long wallMs,Vec start,Vec velocity,double nativeDamage,double lifetime,boolean hitscan,double range,String identity,boolean beam,boolean rocket,Effect effect){this(id,nativeEntity,wallMs,start,velocity,nativeDamage,lifetime,hitscan,range,identity,beam,rocket,effect,List.of());}
        public boolean barrage(){return effect!=null&&effect.hero()==0x02e0000000000008L&&effect.resource()==0x0400000000000052L&&!waves.isEmpty();}
        public boolean helix(){return !hitscan&&effect!=null&&effect.hero()==0x02e000000000006eL&&effect.resource()==0x040000000000072cL;}
        /** Original beta Tank factory; presentation remains an explicit MC rebuild. */
        public boolean tankShell(){return !hitscan&&effect!=null&&effect.hero()==0x02e0000000000015L&&effect.resource()==0x04000000000003ceL;}
        public Shot(long id,long nativeEntity,long wallMs,Vec start,Vec velocity,double nativeDamage,double lifetime,boolean hitscan,double range,String identity,boolean beam,boolean rocket){this(id,nativeEntity,wallMs,start,velocity,nativeDamage,lifetime,hitscan,range,identity,beam,rocket,null);}
        public Shot(long id,long nativeEntity,long wallMs,Vec start,Vec velocity,double nativeDamage,double lifetime,boolean hitscan,double range,String identity,boolean beam){this(id,nativeEntity,wallMs,start,velocity,nativeDamage,lifetime,hitscan,range,identity,beam,false);}
        public Shot(long id,long nativeEntity,long wallMs,Vec start,Vec velocity,double nativeDamage,double lifetime,boolean hitscan,double range,String identity){this(id,nativeEntity,wallMs,start,velocity,nativeDamage,lifetime,hitscan,range,identity,false);}
        public Shot(long id,long nativeEntity,long wallMs,Vec start,Vec velocity,double nativeDamage,double lifetime){this(id,nativeEntity,wallMs,start,velocity,nativeDamage,lifetime,false,0,"projectile:"+nativeEntity,false);}
    }
    public record Entry(long id,Shot shot,String rejection) {}
    public record Batch(Source source,long acknowledged,long lastId,List<Entry> entries) {}
    private static long number(JsonObject o,String name){return Long.parseUnsignedLong(o.get(name).getAsString());}
    private static double scalar(JsonObject o,String name){double n=o.get(name).getAsDouble();if(!Double.isFinite(n))throw new IllegalArgumentException("nonfinite "+name);return n;}
    private static Vec vector(JsonObject o,String name){
        var a=o.getAsJsonArray(name);if(a.size()!=3)throw new IllegalArgumentException("vector size");
        double[] v=new double[3];for(int i=0;i<3;i++){v[i]=a.get(i).getAsDouble();if(!Double.isFinite(v[i])||Math.abs(v[i])>30000000)throw new IllegalArgumentException("vector bounds");}
        return new Vec(v[0],v[1],v[2]);
    }
    public static Batch decode(String json,Expected expected,long now){
        if(json.length()>524288)throw new IllegalArgumentException("journal size");
        var root=JsonParser.parseString(json).getAsJsonObject();
        int probeVersion=root.get("probeVersion").getAsInt();
        if(root.get("protocol").getAsInt()!=3||(probeVersion!=11&&probeVersion!=12&&probeVersion!=13&&probeVersion!=14&&probeVersion!=15&&probeVersion!=16&&probeVersion!=17)||number(root,"pid")!=Integer.toUnsignedLong(expected.nativePid)
           ||number(root,"hostGeneration")!=expected.hostGeneration||!root.get("enabled").getAsBoolean()||root.get("failures").getAsInt()!=0||root.get("overflow").getAsBoolean())throw new IllegalArgumentException("source identity/status");
        long heartbeat=number(root,"heartbeat"),creation=number(root,"creation"),epoch=number(root,"epoch");
        if(creation<=0||epoch<=0||now-heartbeat>500||heartbeat-now>100)throw new IllegalArgumentException("source freshness");
        // The producer knows its current pawn before MC's reflected locomotion
        // binding catches up. Defer the WHOLE prefix rather than retiring that
        // new pawn's real shots under a departed Expected. Freshness is unchanged;
        // once scopes match, old entries still retire as ordinary rejections.
        if(expected.modelId()!=0&&root.has("modelId")&&number(root,"modelId")!=expected.modelId()
                ||expected.hero()!=0&&root.has("hero")&&number(root,"hero")!=expected.hero())throw new OwnerPending();
        long ack=number(root,"acknowledged"),base=number(root,"baseId"),last=number(root,"lastId");
        var array=root.getAsJsonArray("events");
        if(ack<0||last<ack||array.size()>512||base!=ack+1||last-ack!=array.size())throw new IllegalArgumentException("journal prefix");
        var entries=new ArrayList<Entry>();long cursor=ack;
        for(var value:array){
            var e=value.getAsJsonObject();long id=number(e,"id");if(id!=++cursor)throw new IllegalArgumentException("journal ordering");
            try {
                long wall=number(e,"wallMs"),entity=number(e,"entity"),owner=number(e,"owner");
                if(now-wall>500||wall-now>100)throw new IllegalArgumentException("shot stale/future");
                if(number(e,"mcPid")!=Integer.toUnsignedLong(expected.mcPid)||number(e,"mcGeneration")!=expected.mcGeneration||number(e,"worldId")!=expected.worldId||number(e,"hostGeneration")!=expected.hostGeneration)throw new IllegalArgumentException("shot world/session");
                int kind=e.get("kind").getAsInt();boolean generic=kind==4,hitscan=kind==1||(generic&&e.get("flight").getAsInt()==0),beam=kind==2,rocket=kind==3;
                long resource=Long.parseUnsignedLong(e.get("resource").getAsString(),16);
                if(owner<=0||owner>0xffffffffL||kind<0||kind>4)throw new IllegalArgumentException("native owner/kind");
                if(expected.modelId()!=0&&owner!=expected.modelId())throw new IllegalArgumentException("shot departed native model");
                String identity;Effect effect=null;var waves=new ArrayList<PharahBarrageMotion.Wave>();double nativeEye=beam?1.5:hitscan?1.55:rocket?1.35:1.2;
                if(generic){
                    long hero=number(e,"hero"),volley=number(e,"volley"),tick=number(e,"tick"),shot=number(e,"shot"),pellet=number(e,"pellet");
                    if(expected.hero()!=0&&hero!=expected.hero())throw new IllegalArgumentException("shot departed native hero");
                    if(!java.util.Set.of(2L,3L,5L,6L,8L,10L,0x15L,0x29L,0x42L,0x65L,0x6eL,0xddL,0x40L).contains(hero&0xffffL)||(hero&~0xffffL)!=0x02e0000000000000L
                       ||e.get("flags").getAsInt()!=313||entity!=0||(resource>>>48)!=0x0400||volley==0||tick<=0||tick>0xffffffffL||shot>65535||pellet>255
                       ||(e.get("status").getAsInt()!=0&&e.get("status").getAsInt()!=8)||e.get("factoryType").getAsInt()<1||e.get("factoryType").getAsInt()>3||e.get("flight").getAsInt()<0||e.get("flight").getAsInt()>1)throw new IllegalArgumentException("native armory proof");
                    nativeEye=scalar(e,"eyeHeight");double gravity=scalar(e,"gravity"),splash=scalar(e,"splashDamage"),radius=scalar(e,"outerRadius"),fuse=scalar(e,"fuse"),terrain=scalar(e,"terrain");int code=e.get("effect").getAsInt(),bounces=e.get("bounces").getAsInt();
                    if(nativeEye<.5||nativeEye>2.5||gravity<0||gravity>30||splash<0||splash>1000||radius<0||radius>10||fuse<0||fuse>10||terrain<0||terrain>4||code<0||code>16||bounces<0||bounces>8)throw new IllegalArgumentException("armory effect bounds");
                    double inner=scalar(e,"innerRadius"),scale=scalar(e,"outerScale");
                    if(inner<0||scale<0||scale>1||(splash>0&&(inner>=radius||code!=1)))throw new IllegalArgumentException("armory blast bounds");
                    effect=new Effect(hero,resource,code,gravity,splash,radius,bounces,fuse,terrain,inner,scale);
                    identity="factory:"+hero+":"+owner+":"+Long.toUnsignedString(volley)+":"+tick+":"+shot+":"+pellet;
                }else if(beam){
                    long begin=number(e,"volley"),tick=number(e,"tick");
                    if(e.get("flags").getAsInt()!=217||entity!=0||resource!=0x05800000000000feL||begin<=0||tick<=begin||tick>0xffffffffL)throw new IllegalArgumentException("native beam proof");
                    identity="beam:"+owner+":"+begin+":"+tick;
                }else if(hitscan||rocket){
                    long volley=number(e,"volley"),tick=number(e,"tick"),shot=number(e,"shot"),pellet=number(e,"pellet"),status=number(e,"status");
                    if(e.get("flags").getAsInt()!=57||entity!=0||resource!=(rocket?0x0400000000000033L:0x04000000000002a7L)||volley==0||tick<=0||tick>0xffffffffL||shot>65535||pellet>255||(rocket?status!=8:(status!=0&&status!=8)))throw new IllegalArgumentException("native factory proof");
                    identity=(rocket?"rocket:":"hitscan:")+owner+":"+Long.toUnsignedString(volley)+":"+tick+":"+shot+":"+pellet;
                }else{
                    if(e.get("flags").getAsInt()!=31||entity<=0||entity>0xffffffffL||number(e,"componentOwner")!=owner||resource!=0x04000000000007caL)throw new IllegalArgumentException("native projectile proof");
                    identity="projectile:"+entity;
                }
                var offset=vector(e,"position").subtract(vector(e,"nativeFeet"));var velocity=vector(e,"velocity");
                double damage=scalar(e,"damage"),lifetime=scalar(e,"lifetime"),range=(hitscan||beam||rocket||generic)?scalar(e,"range"):0;
                if(offset.lengthSquared()>64||damage<=0||damage>10000||expected.eyeHeight<.1||expected.eyeHeight>3)throw new IllegalArgumentException("shot numeric bounds");
                if(generic){
                    if(range<=0||range>512||(hitscan?(lifetime!=0||velocity.lengthSquared()<.99||velocity.lengthSquared()>1.01):(lifetime<=0||lifetime>120||velocity.lengthSquared()<.01||velocity.lengthSquared()>1000000)))throw new IllegalArgumentException("armory flight bounds");
                    if(effect.kind()==2&&((probeVersion!=12&&probeVersion!=13&&probeVersion!=14&&probeVersion!=15&&probeVersion!=16&&probeVersion!=17)||effect.hero()!=0x02e0000000000042L||resource!=0x040000000000037dL||hitscan||Math.abs(velocity.lengthSquared()-900)>.1||lifetime!=5||range!=7||damage!=25||effect.gravity()!=20||effect.radius()!=3||effect.splash()!=0||effect.bounces()!=0||effect.fuse()!=0||effect.terrain()!=0))throw new IllegalArgumentException("uncalibrated native Flashbang");
                    if(effect.kind()==3&&((probeVersion!=13&&probeVersion!=14&&probeVersion!=15&&probeVersion!=16&&probeVersion!=17)||effect.hero()!=0x02e0000000000008L||resource!=0x040000000000010fL||hitscan||Math.abs(velocity.lengthSquared()-3600)>.1||lifetime!=5||range!=100||damage!=1||effect.gravity()!=0||effect.radius()!=8||effect.splash()!=0||effect.bounces()!=0||effect.fuse()!=0||effect.terrain()!=0))throw new IllegalArgumentException("uncalibrated native Concussive Blast");
                    if(effect.hero()==RoadhogRules.HERO){
                        if(probeVersion!=17||effect.kind()!=0||effect.gravity()!=0||effect.splash()!=0||effect.radius()!=0
                           ||effect.bounces()!=0||effect.fuse()!=0||effect.terrain()!=0
                           ||!RoadhogRules.factory(resource,e.get("factoryType").getAsInt(),e.get("status").getAsInt(),hitscan,velocity.lengthSquared(),lifetime,range,damage))
                            throw new IllegalArgumentException("uncalibrated native Roadhog factory");
                    }else if(resource==RoadhogRules.SCRAP||resource==RoadhogRules.SECONDARY||resource==RoadhogRules.WHOLE_HOG)
                        throw new IllegalArgumentException("Roadhog resource/hero mismatch");
                    // Resource-specific calibration prevents another armory or
                    // older producer from borrowing Tank blast presentation.
                    if(resource==0x04000000000003ceL&&((probeVersion!=16&&probeVersion!=17)||effect.hero()!=0x02e0000000000015L||hitscan||effect.kind()!=1
                        ||e.get("status").getAsInt()!=8||e.get("factoryType").getAsInt()!=1||Math.abs(velocity.lengthSquared()-3600)>.1
                        ||lifetime!=5||range!=100||damage!=50||effect.gravity()!=0||effect.splash()!=140||effect.innerRadius()!=1||effect.radius()!=4
                        ||Math.abs(effect.outerScale()-.30000001192092896)>1e-6||effect.terrain()!=0||effect.bounces()!=0||effect.fuse()!=0))throw new IllegalArgumentException("uncalibrated native Tank shell");
                    if((resource==0x0400000000000149L||resource==0x040000000000020dL)
                        &&((probeVersion!=16&&probeVersion!=17)||effect.hero()!=HanzoSonicArrowState.HERO||hitscan||effect.kind()!=0
                        ||e.get("status").getAsInt()!=8||e.get("factoryType").getAsInt()!=1
                        ||lifetime!=5||range!=100||damage<25||damage>125
                        ||velocity.lengthSquared()<625-.1||velocity.lengthSquared()>8100+.1
                        ||Math.abs(effect.gravity()-9.800000190734863)>1e-6||effect.splash()!=0||effect.radius()!=0
                        ||effect.terrain()!=0||effect.bounces()!=0||effect.fuse()!=0))throw new IllegalArgumentException("uncalibrated native Sonic arrow");
                }else if(beam){
                    if(velocity.lengthSquared()<.99||velocity.lengthSquared()>1.01||range!=8||damage!=60||lifetime<=0||lifetime>.25)throw new IllegalArgumentException("uncalibrated native beam");
                }else if(rocket){
                    if(Math.abs(velocity.lengthSquared()-1225)>.1||range!=100||damage!=40||lifetime!=5
                       ||scalar(e,"splashDamage")!=80||scalar(e,"innerRadius")!=.5||scalar(e,"outerRadius")!=2.5||scalar(e,"outerScale")!=.125)throw new IllegalArgumentException("uncalibrated native rocket");
                }else if(hitscan){
                    if(velocity.lengthSquared()<.99||velocity.lengthSquared()>1.01||range!=100||damage!=70||lifetime!=0)throw new IllegalArgumentException("uncalibrated native hitscan");
                }else if(velocity.lengthSquared()<.01||velocity.lengthSquared()>1000000||lifetime<=0||lifetime>120)throw new IllegalArgumentException("projectile numeric bounds");
                if(e.has("waves")){
                    if(!generic||(probeVersion!=14&&probeVersion!=15&&probeVersion!=16&&probeVersion!=17)||effect.hero()!=0x02e0000000000008L||resource!=0x0400000000000052L||hitscan||effect.kind()!=1||damage!=10||lifetime!=5||range!=100||Math.abs(velocity.lengthSquared()-2025)>.1||effect.gravity()!=0||effect.splash()!=30||effect.innerRadius()!=.5||effect.radius()!=1.5||Math.abs(effect.outerScale()-.3)>1e-6||effect.terrain()!=0||effect.bounces()!=0||effect.fuse()!=0)throw new IllegalArgumentException("uncalibrated native Barrage");
                    var a=e.getAsJsonArray("waves");if(a.size()!=2)throw new IllegalArgumentException("Barrage wave count");
                    for(int i=0;i<2;i++){
                        var w=a.get(i).getAsJsonObject();double start=scalar(w,"start"),fade=scalar(w,"fade"),phase=scalar(w,"phase"),freq=scalar(w,"frequency"),mag=scalar(w,"magnitude"),rot=scalar(w,"rotation");boolean spiral=w.get("spiral").getAsBoolean();
                        if(start!=0||Math.abs(fade-.2)>1e-6||phase<0||phase>1||Math.abs(freq)<.09999||Math.abs(freq)>1.00001||mag<.19999||mag>1.50001||rot<9.999||rot>360.001||(i==0&&!spiral))throw new IllegalArgumentException("Barrage wave bounds");
                        waves.add(new PharahBarrageMotion.Wave(start,fade,phase,freq,mag,rot,spiral));
                    }
                }else if(generic&&effect.hero()==0x02e0000000000008L&&resource==0x0400000000000052L)throw new IllegalArgumentException("Barrage missing original motion");
                var start=vector(e,"mcFeet").add(offset).add(new Vec(0,expected.eyeHeight-nativeEye,0));
                entries.add(new Entry(id,new Shot(id,entity,wall,start,velocity,damage,lifetime,hitscan,range,identity,beam,rocket,effect,List.copyOf(waves)),""));
            } catch(RuntimeException invalid){entries.add(new Entry(id,null,invalid.getMessage()));}
        }
        return new Batch(new Source(expected.nativePid,creation,epoch,expected.hostGeneration),ack,last,List.copyOf(entries));
    }
}
