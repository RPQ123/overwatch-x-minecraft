"""Compile the real NativeSessionGuard against inert MC/controller fixtures.

This checks picker/focus/gap boundaries and once-per-pawn healing without
building a JAR, launching MC or modifying another thread's Gradle registrations.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JDK = ROOT / 'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin'


class SessionGuardTests(unittest.TestCase):
    def test_real_guard_resets_input_boundaries_without_healing_same_pawn(self):
        source = (ROOT/'guest/src/client/java/lab/owmcguest/NativeSessionGuard.java').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            package = folder/'lab/owmcguest'
            package.mkdir(parents=True)
            (package/'NativeSessionGuard.java').write_text(source, encoding='utf-8')
            (package/'NativeSpawnHealthGate.java').write_text((ROOT/'guest/src/main/java/lab/owmcguest/NativeSpawnHealthGate.java').read_text(encoding='utf-8'), encoding='utf-8')
            owners = set(re.findall(r'\b(\w+)\.(?:INSTANCE\.)?(?:resetSession|reset|configure)\(', source))
            stubs = '\n'.join('class '+owner+' { static final '+owner+' INSTANCE=new '+owner+'(); static int resets; static void resetSession(){resets++;} static void reset(){resets++;} static void configure(Object...args){} }' for owner in sorted(owners))
            (package/'Controllers.java').write_text('package lab.owmcguest;\n'+stubs+'\nclass NativeWorldIdentity { static long of(Object server,Object key){return 1;} }\n', encoding='utf-8')
            mc = folder/'net/minecraft/client'
            mc.mkdir(parents=True)
            (mc/'MinecraftClient.java').write_text('''package net.minecraft.client;
public class MinecraftClient {
    static final MinecraftClient INSTANCE=new MinecraftClient();
    public Player player=new Player(); final Server server=new Server();
    public static MinecraftClient getInstance(){return INSTANCE;}
    public Server getServer(){return server;}
    public class Server { public Server getPlayerManager(){return this;} public Player getPlayer(java.util.UUID id){return player;} }
    public static class World { public Object getRegistryKey(){return "fixture";} }
    public static class Player {
        final java.util.UUID id=new java.util.UUID(1,2); public int heals;
        public java.util.UUID getUuid(){return id;} public boolean isAlive(){return true;}
        public boolean isCreative(){return true;} public World getWorld(){return new World();}
        public float getMaxHealth(){return 20;} public void setHealth(float health){heals++;}
    }
}
''', encoding='utf-8')
            (package/'GuardCheck.java').write_text('''package lab.owmcguest;
import net.minecraft.client.MinecraftClient;
public class GuardCheck {
    static void check(boolean condition,String message){if(!condition)throw new AssertionError(message);}
    public static void main(String[] args){
        var c=MinecraftClient.getInstance(); NativeSessionGuard.resetForTests();
        check(NativeSessionGuard.observe(c,1,7,10,100,true),"initial admission");
        NativeSessionGuard.resetServerState(); check(c.player.heals==1,"initial creative health");
        check(!NativeSessionGuard.observe(c,1,7,10,100,true),"steady state must not reset");
        check(NativeSessionGuard.observe(c,1,7,10,100,false),"picker/focus departure revokes same-pawn leases");
        NativeSessionGuard.resetServerState();
        check(!NativeSessionGuard.observe(c,1,7,10,100,false),"inactive state resets once");
        check(NativeSessionGuard.observe(c,1,7,10,100,true),"input return rebuilds baselines");
        NativeSessionGuard.resetServerState(); check(c.player.heals==1,"same pawn cannot heal on return");
        check(NativeLocomotionController.resets==3,"one reset per actual boundary");
        check(NativeSessionGuard.observe(c,1,0,0,0,false),"reader gap revokes old scope");
        NativeSessionGuard.resetServerState();
        check(!NativeSessionGuard.observe(c,1,0,0,0,false),"stable gap does not churn");
        check(NativeSessionGuard.observe(c,1,7,10,100,true),"same-pawn gap recovery");
        NativeSessionGuard.resetServerState(); check(c.player.heals==1,"gap cannot heal");
        check(NativeSessionGuard.observe(c,1,0x42,11,100,true),"Reinhardt to McCree new model");
        NativeSessionGuard.resetServerState(); check(c.player.heals==2,"new pawn initializes once");
        check(NativeSessionGuard.observe(c,2,0x42,11,100,true),"dimension resets transport");
        NativeSessionGuard.resetServerState(); check(c.player.heals==2,"dimension does not heal same pawn");
        NativeSessionGuard.disconnected();
        check(NativeSessionGuard.observe(c,1,0x42,11,101,true),"new host source is a new session");
        NativeSessionGuard.resetServerState(); check(c.player.heals==3,"new host initializes");
        System.out.println("guard boundaries passed");
    }
}
''', encoding='utf-8')
            compiled = subprocess.run([str(JDK/'javac.exe'), '-d', str(folder/'classes'), *map(str, folder.rglob('*.java'))], capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stderr[-3000:])
            result = subprocess.run([str(JDK/'java.exe'), '-cp', str(folder/'classes'), 'lab.owmcguest.GuardCheck'], capture_output=True, text=True, encoding='utf-8', timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr[-3000:])
            self.assertIn('guard boundaries passed', result.stdout)


if __name__ == '__main__':
    unittest.main()
