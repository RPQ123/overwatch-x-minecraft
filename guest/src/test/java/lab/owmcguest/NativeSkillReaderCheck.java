package lab.owmcguest;
import com.google.gson.*;
import com.sun.jna.*;
import java.nio.file.Files;

/** Actual bounded Win64 reads of owned fixture memory, including graph and model replacement. */
public final class NativeSkillReaderCheck {
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-skill-reader-");String previous=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();var file=dir.resolve("native-skills-request-"+pid+".json");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);var handle=kernel.OpenProcess(0x400,false,pid);
        try(var admin=new Memory(0x230);var adminAddress=new Memory(8);var reference=new Memory(0x98);
            var model=new Memory(0x98);var heroInfo=new Memory(0xa0);var script=new Memory(0x168);
            var inner=new Memory(0x458);var component=new Memory(16);var graph=new Memory(0x60);var bag=new Memory(0x3a0);
            var storage=new Memory(16);var nodes=new Memory(1024);var recon=new Memory(0x110);var sentry=new Memory(0x148);var tank=new Memory(0x110);var vtable=new Memory(8);
            var damage=new Memory(0xb0);var health=new Memory(0x40);var config=new Memory(8);var radius=new Memory(24);var offset=new Memory(32);var pairs=new Memory(16);
            var boxStorage=new Memory(16);var boxItems=new Memory(48);var vectors=new Memory(192);
            var logger=new Memory(16);var sentinel=new Memory(40);var outerNode=new Memory(64);
            var stateHead=new Memory(40);var reconNode=new Memory(64);var sentryNode=new Memory(64);var tankNode=new Memory(64);
            var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);
            var reader=new NativeSkillReader()){
            for(var m:new Memory[]{admin,adminAddress,reference,model,heroInfo,script,inner,component,graph,bag,storage,nodes,recon,sentry,tank,vtable,logger,sentinel,outerNode,stateHead,reconNode,sentryNode,tankNode,damage,health,config,radius,offset,pairs})m.clear();
            require(kernel.GetProcessTimes(handle,creation,exit,system,user),"Fixture creation identity");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);
            reference.setInt(0x94,19);model.setInt(0x94,19);model.setLong(0x28,Pointer.nativeValue(admin));
            heroInfo.setLong(0x98,0x02e0000000000015L);script.setLong(0x150,0x058000000000012fL);
            script.setLong(0x98,Pointer.nativeValue(bag));script.setLong(0x160,Pointer.nativeValue(graph));
            script.setLong(0x10,Pointer.nativeValue(inner));inner.setLong(0x450,Pointer.nativeValue(component));component.setLong(8,Pointer.nativeValue(model));
            graph.setLong(0x50,Pointer.nativeValue(storage));graph.setLong(0x58,1);storage.setLong(0,Pointer.nativeValue(nodes));storage.setLong(8,106);
            nodes.setLong(64,Pointer.nativeValue(recon));nodes.setLong(72,Pointer.nativeValue(sentry));nodes.setLong(840,Pointer.nativeValue(tank));recon.setLong(0,Pointer.nativeValue(vtable));sentry.setLong(0,Pointer.nativeValue(vtable));tank.setLong(0,Pointer.nativeValue(vtable));
            logger.setLong(0,Pointer.nativeValue(sentinel));sentinel.setLong(8,Pointer.nativeValue(sentinel));sentinel.setByte(25,(byte)1);
            var b=new JsonObject();b.addProperty("version",1);b.addProperty("pid",pid);b.addProperty("creation",creation.getLong(0));
            b.addProperty("resource",0x058000000000012fL);b.addProperty("hero",0x02e0000000000015L);b.addProperty("localId",17);b.addProperty("modelId",19);
            String[] names={"admin","adminAddress","reference","model","heroInfo","script","graph","bag","logger"};
            Memory[] values={admin,adminAddress,reference,model,heroInfo,script,graph,bag,logger};
            for(int j=0;j<names.length;j++)b.addProperty(names[j],Pointer.nativeValue(values[j]));
            var states=new JsonObject();
            for(int j=0;j<3;j++){var n=new JsonObject();n.addProperty("index",j==2?105:8+j);n.addProperty("address",Pointer.nativeValue(j==0?recon:j==1?sentry:tank));n.addProperty("vtable",Pointer.nativeValue(vtable));states.add(j==0?"recon":j==1?"sentry":"tank",n);}b.add("states",states);
            Files.writeString(file,b.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            var idle=reader.poll(pose,19,0x02e0000000000015L);require(idle!=null&&!idle.active("recon")&&!idle.active("sentry")&&!idle.active("tank"),"Absent logger records are inactive, not inferred from keys");
            logger.setLong(8,1);sentinel.setLong(8,Pointer.nativeValue(outerNode));
            outerNode.setLong(0,Pointer.nativeValue(sentinel));outerNode.setLong(8,Pointer.nativeValue(sentinel));outerNode.setLong(16,Pointer.nativeValue(sentinel));outerNode.setLong(32,Pointer.nativeValue(script));
            outerNode.setLong(40,Pointer.nativeValue(stateHead));outerNode.setLong(48,3);stateHead.setByte(25,(byte)1);stateHead.setLong(8,Pointer.nativeValue(reconNode));
            reconNode.setLong(0,Pointer.nativeValue(stateHead));reconNode.setLong(8,Pointer.nativeValue(stateHead));reconNode.setLong(16,Pointer.nativeValue(sentryNode));reconNode.setInt(32,8);reconNode.setLong(40,100);
            sentryNode.setLong(0,Pointer.nativeValue(stateHead));sentryNode.setLong(8,Pointer.nativeValue(reconNode));sentryNode.setLong(16,Pointer.nativeValue(tankNode));sentryNode.setInt(32,9);sentryNode.setLong(40,100);sentryNode.setByte(48,(byte)1);
            tankNode.setLong(0,Pointer.nativeValue(stateHead));tankNode.setLong(8,Pointer.nativeValue(sentryNode));tankNode.setLong(16,Pointer.nativeValue(stateHead));tankNode.setInt(32,105);tankNode.setLong(40,100);tankNode.setByte(48,(byte)1);
            require(reader.poll(pose,19,0x02e0000000000015L).active("recon"),"Actual native Recon Begin");
            reconNode.setByte(48,(byte)1);sentryNode.setByte(48,(byte)0);sentryNode.setLong(40,150);
            var active=reader.poll(pose,19,0x02e0000000000015L);require(active!=null&&!active.active("recon")&&active.active("sentry")&&active.entries().get("sentry").tick()==150,"Actual independent End/Begin switch");
            sentryNode.setByte(48,(byte)1);tankNode.setByte(48,(byte)0);tankNode.setLong(40,200);
            active=reader.poll(pose,19,0x02e0000000000015L);require(active!=null&&active.active("tank")&&!active.active("recon")&&!active.active("sentry"),"Tank Begin is independent of Recon/Sentry");
            tankNode.setByte(48,(byte)1);require(!reader.poll(pose,19,0x02e0000000000015L).active("tank"),"Tank End cannot authorize movement");
            nodes.setLong(840,Pointer.nativeValue(recon));require(reader.poll(pose,19,0x02e0000000000015L)==null,"Changed Tank definition refuses all form state");nodes.setLong(840,Pointer.nativeValue(tank));
            reference.setInt(0x94,20);require(reader.poll(pose,19,0x02e0000000000015L)==null,"Replaced model invalidates stale states");reference.setInt(0x94,19);
            nodes.setLong(72,Pointer.nativeValue(recon));require(reader.poll(pose,19,0x02e0000000000015L)==null,"Changed graph membership refused");nodes.setLong(72,Pointer.nativeValue(sentry));
            sentryNode.setByte(48,(byte)2);require(reader.poll(pose,19,0x02e0000000000015L)==null,"Invalid native finished byte refused");sentryNode.setByte(48,(byte)0);
            storage.setLong(8,5000);require(reader.poll(pose,19,0x02e0000000000015L)==null,"Unbounded graph refused");storage.setLong(8,106);
            require(reader.poll(pose,19,0x02e0000000000015L)!=null,"Valid owner reconnects");reader.close();
            b.addProperty("creation",creation.getLong(0)-1);Files.writeString(file,b.toString());require(reader.poll(pose,19,0x02e0000000000015L)==null,"Reused PID refused");
            try(var visorReader=new NativeSkillReader();var angle=new Memory(0x68);var codeStorage=new Memory(16);var code=new Memory(3);var constStorage=new Memory(16);var constant=new Memory(4)){
                angle.clear();codeStorage.clear();constStorage.clear();
                b.addProperty("creation",creation.getLong(0));b.addProperty("hero",NativeVisorAim.HERO);b.addProperty("resource",0x0580000000000259L);
                heroInfo.setLong(0x98,NativeVisorAim.HERO);script.setLong(0x150,0x0580000000000259L);storage.setLong(8,16);
                nodes.setLong(96,Pointer.nativeValue(sentry));nodes.setLong(120,Pointer.nativeValue(recon));reconNode.setInt(32,12);sentryNode.setInt(32,15);reconNode.setByte(48,(byte)0);
                states=new JsonObject();for(int j=0;j<2;j++){var n=new JsonObject();n.addProperty("index",j==0?12:15);n.addProperty("address",Pointer.nativeValue(j==0?sentry:recon));n.addProperty("vtable",Pointer.nativeValue(vtable));states.add(j==0?"visor":"ultimate",n);}b.add("states",states);
                radius.setLong(0,Pointer.nativeValue(vtable));radius.setInt(16,45);angle.setLong(0,Pointer.nativeValue(vtable));sentry.setLong(0x140,Pointer.nativeValue(radius));sentry.setLong(0x108,Pointer.nativeValue(angle));
                angle.setLong(0x20,Pointer.nativeValue(codeStorage));angle.setLong(0x28,1);codeStorage.setLong(0,Pointer.nativeValue(code));codeStorage.setLong(8,3);code.write(0,new byte[]{70,0,0},0,3);
                angle.setLong(0x40,Pointer.nativeValue(constStorage));angle.setLong(0x48,1);constStorage.setLong(0,Pointer.nativeValue(constant));constStorage.setLong(8,1);constant.setFloat(0,45);
                var geometry=new JsonObject();for(int j=0;j<2;j++){var g=new JsonObject();g.addProperty("field",Pointer.nativeValue(sentry)+(j==0?0x140:0x108));g.addProperty("object",Pointer.nativeValue(j==0?radius:angle));g.addProperty("vtable",Pointer.nativeValue(vtable));g.addProperty("valueAddress",j==0?Pointer.nativeValue(radius)+16:Pointer.nativeValue(constant));g.addProperty("value",45);g.addProperty("integer",j==0);geometry.add(j==0?"radius":"angle",g);}b.add("visorGeometry",geometry);Files.writeString(file,b.toString());
                require(visorReader.poll(pose,19,NativeVisorAim.HERO).active("visor"),"Measured Visor TrackTargets Begin");require(java.util.Arrays.equals(visorReader.visorGeometry(),new double[]{45,45}),"Original integer radius and compiled literal cone");
                constant.setFloat(0,90);require(visorReader.visorGeometry()==null,"Changed Visor cone refused");constant.setFloat(0,45);require(visorReader.poll(pose,19,NativeVisorAim.HERO)!=null,"Visor reconnect");
                code.setByte(0,(byte)31);require(visorReader.visorGeometry()==null,"Dynamic Visor expression is not treated as a literal");code.setByte(0,(byte)70);require(visorReader.poll(pose,19,NativeVisorAim.HERO)!=null,"Restored literal reconnects");
                constStorage.setLong(8,2);require(visorReader.visorGeometry()==null,"Replaced constant storage refused");constStorage.setLong(8,1);
            }
            var meleeFile=dir.resolve("native-melee-request-"+pid+".json");
            try(var meleeReader=new NativeSkillReader(true)){
                b.addProperty("creation",creation.getLong(0));b.addProperty("hero",0x02e0000000000008L);heroInfo.setLong(0x98,0x02e0000000000008L);
                b.addProperty("resource",0x0580000000000043L);script.setLong(0x150,0x0580000000000043L);storage.setLong(8,14);
                nodes.setLong(96,Pointer.nativeValue(recon));nodes.setLong(104,Pointer.nativeValue(sentry));
                reconNode.setInt(32,12);sentryNode.setInt(32,13);states=new JsonObject();
                for(int j=0;j<2;j++){var n=new JsonObject();n.addProperty("index",12+j);n.addProperty("address",Pointer.nativeValue(j==0?recon:sentry));n.addProperty("vtable",Pointer.nativeValue(vtable));states.add(j==0?"modify":"strike",n);}b.add("states",states);
                String[] fields={"damage","health","damageConfig","radius","radiusVtable","offset","offsetVtable","numericVtable"};Memory[] addresses={damage,health,config,radius,vtable,offset,vtable,vtable};
                for(int j=0;j<fields.length;j++)b.addProperty(fields[j],Pointer.nativeValue(addresses[j]));b.addProperty("damageBucket",0);b.addProperty("eye",1.35);
                damage.setLong(0,Pointer.nativeValue(vtable));damage.setInt(0xa0,50);damage.setInt(0xac,2);
                radius.setLong(0,Pointer.nativeValue(vtable));radius.setInt(16,1);offset.setLong(0,Pointer.nativeValue(vtable));offset.setFloat(16,0);offset.setFloat(20,1.5f);offset.setFloat(24,1.5f);
                bag.setLong(0xa0,Pointer.nativeValue(pairs));bag.setInt(0xa8,1);bag.setInt(0xac,1);pairs.setLong(0,0x0d800000000001dcL);pairs.setLong(8,Pointer.nativeValue(damage));
                recon.setLong(0x108,Pointer.nativeValue(health));health.setLong(0x38,Pointer.nativeValue(config));sentry.setLong(0x130,Pointer.nativeValue(offset));sentry.setLong(0x140,Pointer.nativeValue(radius));
                Files.writeString(meleeFile,b.toString());var strike=meleeReader.poll(pose,19,0x02e0000000000008L);
                require(strike!=null&&strike.active("strike")&&strike.geometry().damage()==50&&strike.geometry().radius()==1,"Native quick-melee execution and original damage/geometry");
                damage.setInt(0xa0,35);require(meleeReader.poll(pose,19,0x02e0000000000008L).geometry().damage()==35,"Read current native damage, not a guessed constant");
                pairs.setLong(0,123);require(meleeReader.poll(pose,19,0x02e0000000000008L)==null,"Replaced melee damage membership refused");pairs.setLong(0,0x0d800000000001dcL);
                offset.setFloat(24,15);require(meleeReader.poll(pose,19,0x02e0000000000008L)==null,"Changed native melee geometry refused");offset.setFloat(24,1.5f);
                health.setLong(0x38,0);require(meleeReader.poll(pose,19,0x02e0000000000008L)==null,"Changed native damage configuration refused");
            }finally{Files.deleteIfExists(meleeFile);}
            var sustainFile=dir.resolve("native-sustain-request-"+pid+".json");
            try(var healReader=new NativeSkillReader("sustain")){
                heroInfo.setLong(0x98,0x02e0000000000015L);script.setLong(0x150,0x0580000000000153L);b.addProperty("hero",0x02e0000000000015L);b.addProperty("resource",0x0580000000000153L);
                nodes.setLong(16,Pointer.nativeValue(sentry));storage.setLong(8,3);sentryNode.setInt(32,2);reconNode.setInt(32,1);
                var node=new JsonObject();node.addProperty("index",2);node.addProperty("address",Pointer.nativeValue(sentry));node.addProperty("vtable",Pointer.nativeValue(vtable));states=new JsonObject();states.add("heal",node);b.add("states",states);
                var healing=new JsonObject();String[] fields={"health","amount","amountVtable","interval","intervalVtable","target","targetVtable"};Memory[] addresses={health,damage,vtable,radius,vtable,offset,vtable};
                for(int j=0;j<fields.length;j++)healing.addProperty(fields[j],Pointer.nativeValue(addresses[j]));b.add("healing",healing);
                sentry.setLong(0x100,Pointer.nativeValue(radius));sentry.setLong(0x108,Pointer.nativeValue(health));sentry.setLong(0x110,Pointer.nativeValue(offset));health.setLong(0x38,Pointer.nativeValue(damage));damage.setInt(16,50);radius.setInt(16,1);Files.writeString(sustainFile,b.toString());
                require(healReader.poll(pose,19,0x02e0000000000015L)!=null&&healReader.healing().amount()==50&&healReader.healing().interval()==1,"Original repair phase and typed self-heal parameters");
                damage.setInt(16,-50);require(healReader.healing()==null,"Damage is never treated as healing");damage.setInt(16,50);
                require(healReader.poll(pose,19,0x02e0000000000015L)!=null,"Healing owner reconnects");sentry.setLong(0x110,0);require(healReader.healing()==null,"Changed self target refuses healing");
            }finally{Files.deleteIfExists(sustainFile);}
            try(var deflectReader=new NativeSkillReader()){
                boxStorage.clear();boxItems.clear();vectors.clear();heroInfo.setLong(0x98,0x02e0000000000029L);script.setLong(0x150,0x05800000000003a3L);
                b.addProperty("hero",0x02e0000000000029L);b.addProperty("resource",0x05800000000003a3L);storage.setLong(8,31);nodes.setLong(240,Pointer.nativeValue(sentry));
                var node=new JsonObject();node.addProperty("index",30);node.addProperty("address",Pointer.nativeValue(sentry));node.addProperty("vtable",Pointer.nativeValue(vtable));states=new JsonObject();states.add("deflect",node);b.add("states",states);
                sentry.setLong(0x100,Pointer.nativeValue(boxStorage));sentry.setLong(0x108,1);boxStorage.setLong(0,Pointer.nativeValue(boxItems));boxStorage.setLong(8,3);
                var definition=new JsonObject();definition.addProperty("field",Pointer.nativeValue(sentry)+0x100);definition.addProperty("items",Pointer.nativeValue(boxItems));definition.addProperty("count",3);var configs=new com.google.gson.JsonArray();
                float[][] corners={{-1,-2,0},{1,.75f,2},{.5f,-2,0},{1,.75f,-1},{-.5f,-2,0},{-1,.75f,-1}};
                for(int j=0;j<6;j++){long at=Pointer.nativeValue(vectors)+j*32;boxItems.setLong(j*8,at);vectors.setLong(j*32,Pointer.nativeValue(vtable));for(int k=0;k<3;k++)vectors.setFloat(j*32+16+k*4,corners[j][k]);}
                for(int j=0;j<3;j++){var c=new JsonObject();c.addProperty("first",Pointer.nativeValue(vectors)+j*64);c.addProperty("second",Pointer.nativeValue(vectors)+j*64+32);c.addProperty("firstVtable",Pointer.nativeValue(vtable));c.addProperty("secondVtable",Pointer.nativeValue(vtable));configs.add(c);}definition.add("boxes",configs);b.add("deflectBoxes",definition);Files.writeString(file,b.toString());
                require(deflectReader.poll(pose,19,0x02e0000000000029L)!=null,"Original Deflect owner");var boxes=deflectReader.deflectBoxes();
                require(boxes!=null&&boxes.size()==3&&boxes.get(0)[5]==2&&boxes.get(1)[2]==-1&&boxes.get(2)[0]==-1,"Actual beta16-byte inline corner pairs, normalized for MC sweep");
                boxStorage.setLong(8,4);require(deflectReader.deflectBoxes()==null,"Changed native box count refused");boxStorage.setLong(8,3);
                require(deflectReader.poll(pose,19,0x02e0000000000029L)!=null,"Deflect reader reconnects");vectors.setFloat(16,Float.NaN);require(deflectReader.deflectBoxes()==null,"Nonfinite native corner refused");vectors.setFloat(16,-1);
                require(deflectReader.poll(pose,19,0x02e0000000000029L)!=null,"Restored corner owner");boxItems.setLong(0,Pointer.nativeValue(vectors)+32);require(deflectReader.deflectBoxes()==null,"Replaced corner config refused");
            }
            try(var fieldReader=new NativeSkillReader("biotic");var fieldGraph=new Memory(0x60);var fieldStorage=new Memory(16);var fieldNodes=new Memory(112);var assignments=new Memory(3*0xb0);var constants=new Memory(72)){
                for(var memory:new Memory[]{fieldGraph,fieldStorage,fieldNodes,assignments,constants})memory.clear();
                b.addProperty("hero",NativeBioticRuntime.HERO);b.addProperty("resource",0x0580000000000257L);
                heroInfo.setLong(0x98,NativeBioticRuntime.HERO);script.setLong(0x150,0x0580000000000257L);storage.setLong(8,26);
                states=new JsonObject();String[] phaseNames={"deploy","cast","windup"};int[] indexes={6,20,11};Memory[] phaseNodes={recon,tank,sentry};
                for(int j=0;j<3;j++){nodes.setLong(indexes[j]*8L,Pointer.nativeValue(phaseNodes[j]));var node=new JsonObject();node.addProperty("index",indexes[j]);node.addProperty("address",Pointer.nativeValue(phaseNodes[j]));node.addProperty("vtable",Pointer.nativeValue(vtable));states.add(phaseNames[j],node);}b.add("states",states);
                fieldGraph.setLong(0,Pointer.nativeValue(vtable));fieldGraph.setLong(0x50,Pointer.nativeValue(fieldStorage));fieldGraph.setLong(0x58,1);fieldStorage.setLong(0,Pointer.nativeValue(fieldNodes));fieldStorage.setLong(8,14);
                b.addProperty("fieldGraph",Pointer.nativeValue(fieldGraph));b.addProperty("fieldGraphVtable",Pointer.nativeValue(vtable));var parameters=new JsonObject();String[] parameterNames={"duration","radius","amount"};
                for(int j=0;j<3;j++){
                    long node=Pointer.nativeValue(assignments)+j*0xb0,value=Pointer.nativeValue(constants)+j*24;
                    fieldNodes.setLong((j+2)*8L,node);assignments.setLong(j*0xb0,Pointer.nativeValue(vtable));assignments.setLong(j*0xb0+0xa0,value);constants.setLong(j*24,Pointer.nativeValue(vtable));constants.setInt(j*24+16,j==2?40:5);
                    var d=new JsonObject();d.addProperty("index",j+2);d.addProperty("node",node);d.addProperty("nodeVtable",Pointer.nativeValue(vtable));d.addProperty("field",node+0xa0);d.addProperty("valueObject",value);d.addProperty("valueVtable",Pointer.nativeValue(vtable));d.addProperty("value",j==2?40:5);parameters.add(parameterNames[j],d);
                }b.add("fieldParameters",parameters);var fieldFile=dir.resolve("native-biotic-request-"+pid+".json");
                try{
                    Files.writeString(fieldFile,b.toString());require(fieldReader.poll(pose,19,NativeBioticRuntime.HERO)!=null,"Actual owned Soldier E profile");
                    require(java.util.Arrays.equals(fieldReader.bioticParameters(),new double[]{5,5,40}),"Actual beta ActionSetVar constant field is at0xa0, not State prefix0x100");
                    constants.setInt(16,6);require(fieldReader.bioticParameters()==null,"Changed actual duration refused");constants.setInt(16,5);
                    require(fieldReader.poll(pose,19,NativeBioticRuntime.HERO)!=null,"Field reconnects after a valid source returns");fieldNodes.setLong(16,fieldNodes.getLong(24));require(fieldReader.bioticParameters()==null,"Replaced child assignment membership refused");
                }finally{Files.deleteIfExists(fieldFile);}
            }
            var pulseFile=dir.resolve("native-pulse-request-"+pid+".json");
            try(var pulseReader=new NativeSkillReader("pulse")){
                heroInfo.setLong(0x98,NativePulseRuntime.HERO);script.setLong(0x150,0x0580000000000034L);b.addProperty("hero",NativePulseRuntime.HERO);b.addProperty("resource",0x0580000000000034L);storage.setLong(8,4);
                nodes.setLong(8,Pointer.nativeValue(recon));nodes.setLong(24,Pointer.nativeValue(sentry));states=new JsonObject();
                for(String name:new String[]{"deploy","cast"}){int index=name.equals("deploy")?1:3;var node=new JsonObject();node.addProperty("index",index);node.addProperty("address",Pointer.nativeValue(index==1?recon:sentry));node.addProperty("vtable",Pointer.nativeValue(vtable));states.add(name,node);}b.add("states",states);Files.writeString(pulseFile,b.toString());
                require(pulseReader.poll(pose,19,NativePulseRuntime.HERO)!=null,"Pulse reads only the exact original throw/Volley owner");
                nodes.setLong(24,Pointer.nativeValue(recon));require(pulseReader.poll(pose,19,NativePulseRuntime.HERO)==null,"Replaced Pulse cast definition refuses deployment");nodes.setLong(24,Pointer.nativeValue(sentry));
                b.addProperty("resource",0x058000000000001aL);Files.writeString(pulseFile,b.toString());require(pulseReader.poll(pose,19,NativePulseRuntime.HERO)==null,"Recall cannot impersonate Pulse Bomb");
            }finally{Files.deleteIfExists(pulseFile);}
            var recallFile=dir.resolve("native-recall-request-"+pid+".json");
            try(var recallReader=new NativeSkillReader("recall")){
                b.addProperty("resource",0x058000000000001aL);script.setLong(0x150,0x058000000000001aL);storage.setLong(8,48);nodes.setLong(31*8,Pointer.nativeValue(recon));nodes.setLong(9*8,Pointer.nativeValue(sentry));states=new JsonObject();
                for(String name:new String[]{"cast","animation"}){int index=name.equals("cast")?31:9;var node=new JsonObject();node.addProperty("index",index);node.addProperty("address",Pointer.nativeValue(index==31?recon:sentry));node.addProperty("vtable",Pointer.nativeValue(vtable));states.add(name,node);}b.add("states",states);Files.writeString(recallFile,b.toString());
                require(recallReader.poll(pose,19,NativeRecallRuntime.HERO)!=null,"Recall reads the original root31 and animation9");
                recallReader.close();states.getAsJsonObject("cast").addProperty("index",27);Files.writeString(recallFile,b.toString());require(recallReader.poll(pose,19,NativeRecallRuntime.HERO)==null,"Stack27 leaf cannot impersonate the Recall lifecycle root");
            }finally{Files.deleteIfExists(recallFile);}
            try(var root=new Memory(0x110);var volley=new Memory(0x1b0);var anim=new Memory(0x170);var rangeValue=new Memory(24);var timeValue=new Memory(24);var blossomReader=new NativeSkillReader()){
                for(var v:new Memory[]{root,volley,anim,rangeValue,timeValue})v.clear();
                heroInfo.setLong(0x98,NativeReaperRuntime.HERO);script.setLong(0x150,0x0580000000000044L);b.addProperty("hero",NativeReaperRuntime.HERO);b.addProperty("resource",0x0580000000000044L);storage.setLong(8,54);states=new JsonObject();
                String[] labels={"ultimate","firing","animation"};int[] indices={49,48,9};Memory[] objects={root,volley,anim};
                for(int j=0;j<3;j++){nodes.setLong(indices[j]*8L,Pointer.nativeValue(objects[j]));objects[j].setLong(0,Pointer.nativeValue(vtable));var d=new JsonObject();d.addProperty("index",indices[j]);d.addProperty("address",Pointer.nativeValue(objects[j]));d.addProperty("vtable",Pointer.nativeValue(vtable));states.add(labels[j],d);}b.add("states",states);
                rangeValue.setLong(0,Pointer.nativeValue(vtable));rangeValue.setInt(16,8);timeValue.setLong(0,Pointer.nativeValue(vtable));timeValue.setInt(16,3);volley.setLong(0x130,Pointer.nativeValue(rangeValue));anim.setLong(0x120,Pointer.nativeValue(timeValue));var parameters=new JsonObject();
                for(String name:new String[]{"range","duration"}){boolean range=name.equals("range");var d=new JsonObject();long definition=Pointer.nativeValue(range?volley:anim);d.addProperty("node",range?48:9);d.addProperty("definition",definition);d.addProperty("field",definition+(range?0x130:0x120));d.addProperty("object",Pointer.nativeValue(range?rangeValue:timeValue));d.addProperty("vtable",Pointer.nativeValue(vtable));d.addProperty("value",range?8:3);parameters.add(name,d);}b.add("reaperParameters",parameters);Files.writeString(file,b.toString());
                require(blossomReader.poll(pose,19,NativeReaperRuntime.HERO)!=null&&java.util.Arrays.equals(blossomReader.reaperParameters(),new double[]{8,3}),"Exact original Death Blossom phase/range/duration");rangeValue.setInt(16,9);require(blossomReader.reaperParameters()==null,"Changed native Blossom radius is not silently accepted");
            }
        }finally{
            kernel.CloseHandle(handle);if(previous==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",previous);
            Files.deleteIfExists(file);Files.deleteIfExists(dir);
        }
        System.out.println("PASS: actual Win64 original skill reads, Begin/End, graph/model/creation/payload guards");
    }
}
