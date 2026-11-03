package lab.owmcguest;

import com.google.gson.JsonObject;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import java.nio.file.Files;

/** Real Win64 self-process reads of owned fixtures; no game, hooks or input. */
public final class NativeAbilityReaderCheck {
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] args) throws Exception {
        var directory = Files.createTempDirectory("owmc-ability-check-");
        var previous = System.getProperty("owmc.nativeEventsDirectory");
        int pid = (int) ProcessHandle.current().pid();
        var file = directory.resolve("native-dash-request-" + pid + ".json");
        var kernel = Native.load("kernel32", NativeAbilityReader.Kernel.class);
        var process = kernel.OpenProcess(0x400, false, pid);
        require(process != null, "Cannot open own fixture process");
        try (var admin = new Memory(0x230); var adminAddress = new Memory(8);
             var model = new Memory(0x98); var script = new Memory(0x168);
             var controller = new Memory(0x98); var reference = new Memory(0x98);var heroInfo = new Memory(0xa0);var graph = new Memory(8);
             var bag = new Memory(8); var speed = new Memory(24);
             var damage = new Memory(0xb0); var vtable = new Memory(8);
             var logger = new Memory(16); var sentinel = new Memory(40);
             var outerNode = new Memory(64); var innerHead = new Memory(40); var innerNode = new Memory(64);
             var creation = new Memory(8); var exit = new Memory(8);
             var system = new Memory(8); var user = new Memory(8);
             var reader = new NativeAbilityReader()) {
            for (var memory : new Memory[]{admin,adminAddress,model,script,bag,speed,damage,vtable,logger,sentinel})
                memory.clear();
            require(kernel.GetProcessTimes(process, creation, exit, system, user), "Creation identity");
            adminAddress.setLong(0, Pointer.nativeValue(admin));
            admin.setInt(0x220, 17);
            controller.clear();reference.clear();heroInfo.clear();
            controller.setLong(0x28,Pointer.nativeValue(admin));controller.setInt(0x94,17);
            reference.setLong(8,Pointer.nativeValue(controller));reference.setInt(0x94,19);
            heroInfo.setLong(8,Pointer.nativeValue(controller));heroInfo.setLong(0x98,0x02e0000000000029L);
            model.setLong(0x28, Pointer.nativeValue(admin)); model.setInt(0x94, 19);
            script.setLong(0x98, Pointer.nativeValue(bag)); script.setLong(0x150, 0x05800000000001dbL);
            script.setLong(0x160,Pointer.nativeValue(graph));
            speed.setLong(0, Pointer.nativeValue(vtable)); speed.setInt(16, 50);
            damage.setLong(0, Pointer.nativeValue(vtable)); damage.setInt(0xa0, 35); damage.setInt(0xac, 2);
            logger.setLong(0, Pointer.nativeValue(sentinel));
            sentinel.setLong(8, Pointer.nativeValue(sentinel)); sentinel.setByte(25, (byte) 1);
            var binding = new JsonObject();
            binding.addProperty("version", 2); binding.addProperty("pid", pid);
            binding.addProperty("controller",Pointer.nativeValue(controller));binding.addProperty("reference",Pointer.nativeValue(reference));binding.addProperty("heroInfo",Pointer.nativeValue(heroInfo));binding.addProperty("graph",Pointer.nativeValue(graph));
            binding.addProperty("creation", creation.getLong(0));
            binding.addProperty("resource", 0x05800000000001dbL); binding.addProperty("node", 6);
            binding.addProperty("adminAddress", Pointer.nativeValue(adminAddress));
            binding.addProperty("admin", Pointer.nativeValue(admin)); binding.addProperty("localId", 17);
            binding.addProperty("model", Pointer.nativeValue(model)); binding.addProperty("modelId", 19);
            binding.addProperty("script", Pointer.nativeValue(script)); binding.addProperty("bag", Pointer.nativeValue(bag));
            binding.addProperty("speed", Pointer.nativeValue(speed)); binding.addProperty("speedVtable", Pointer.nativeValue(vtable));
            binding.addProperty("damage", Pointer.nativeValue(damage)); binding.addProperty("damageVtable", Pointer.nativeValue(vtable));
            binding.addProperty("logger", Pointer.nativeValue(logger));
            System.setProperty("owmc.nativeEventsDirectory", directory.toString());
            var pose = new HostPoseReader.Pose(42, 1, pid, 1, 70,
                    new float[]{1,0,0,0,1,0,0,0,1}, new float[]{0,0,0}, 0, false);
            require(reader.poll(null) == null && reader.error.equals("native camera unavailable"), "Missing camera");
            require(reader.poll(pose) == null && reader.error.equals("waiting for native ability binding"), "Missing binding diagnosis");
            Files.writeString(file, binding.toString());
            var idle=reader.poll(pose);
            require(idle!=null&&!idle.active()&&idle.tick()==0, "Idle supplies a non-executing baseline");
            var phase=new NativeDashPhase();require(!phase.observe(idle.source(),idle.model(),idle.tick(),idle.active(),1000), "Idle cannot manufacture a dash");
            require(phase.observe(idle.source(),idle.model(),1,true,1010), "First original Begin after idle is admitted");
            require(reader.error.isEmpty(), "Idle binding must clear the earlier camera/binding error before first Shift");
            // Real hero replacement can leave every old model/script byte
            // intact. Only the current controller's model reference changes.
            reference.setInt(0x94,21);
            require(reader.poll(pose)==null&&reader.error.contains("native hero/ability changed"),"Retained old model is not the current hero");
            reference.setInt(0x94,19);
            require(reader.poll(pose)!=null,"Current owner reconnects after a retained-object refusal");
            admin.setInt(0x220, 18);
            require(reader.poll(pose) == null && reader.error.contains("native hero/ability changed"), "Changed hero must still fail");
            admin.setInt(0x220, 17);
            require(reader.poll(pose) != null && reader.error.isEmpty(), "Healthy identity recovery");
            // A respawn creates a new native owner within the same host camera generation.
            admin.setInt(0x220, 21); model.setInt(0x94, 23);
            require(reader.poll(pose) == null && reader.error.contains("native hero/ability changed"), "Departed owner closes reader");
            controller.setInt(0x94,21);reference.setInt(0x94,23);
            binding.addProperty("localId", 21); binding.addProperty("modelId", 23); Files.writeString(file, binding.toString());
            require(!reader.poll(pose).active() && reader.error.isEmpty(), "New hero binding reconnects without host restart or manufactured dash");
            // Read the real nested-map layout: original End updates its timestamp
            // too, but must not manufacture a second Dragonblade swing.
            outerNode.clear();innerHead.clear();innerNode.clear();
            logger.setLong(8,1);sentinel.setLong(8,Pointer.nativeValue(outerNode));
            outerNode.setLong(0,Pointer.nativeValue(sentinel));outerNode.setLong(8,Pointer.nativeValue(sentinel));outerNode.setLong(16,Pointer.nativeValue(sentinel));outerNode.setLong(32,Pointer.nativeValue(script));
            outerNode.setLong(40,Pointer.nativeValue(innerHead));outerNode.setLong(48,1);
            innerHead.setLong(8,Pointer.nativeValue(innerNode));innerHead.setByte(25,(byte)1);
            innerNode.setLong(0,Pointer.nativeValue(innerHead));innerNode.setLong(8,Pointer.nativeValue(innerHead));innerNode.setLong(16,Pointer.nativeValue(innerHead));innerNode.setInt(32,57);innerNode.setLong(40,100);
            require(reader.stateTick(Pointer.nativeValue(script),57,true)==100,"Original tracking Begin is a swing");
            innerNode.setLong(40,110);innerNode.setByte(48,(byte)1);
            require(reader.stateTick(Pointer.nativeValue(script),57,false)==110,"End really has a newer native timestamp");
            require(reader.stateTick(Pointer.nativeValue(script),57,true)==0,"Tracking End cannot become a second swing");
            speed.setInt(16, 0);
            require(reader.poll(pose) == null && reader.error.contains("numeric bounds"), "Invalid native speed must still fail");
        } finally {
            kernel.CloseHandle(process);
            if (previous == null) System.clearProperty("owmc.nativeEventsDirectory");
            else System.setProperty("owmc.nativeEventsDirectory", previous);
            Files.deleteIfExists(file); Files.deleteIfExists(directory);
        }
        System.out.println("PASS: idle ability clears stale camera/binding errors without an attack; identity and numeric guards remain active");
    }
}
