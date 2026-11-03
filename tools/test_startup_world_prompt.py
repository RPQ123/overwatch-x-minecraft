"""Compile the real prompt adapter against inert UI stubs; never open a game."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
JDK=ROOT/'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin'

SOURCES={
    'net/minecraft/text/Text.java': '''package net.minecraft.text;
public record Text(String key) {
    public static Text translatable(String key){return new Text(key);}
    public String getString(){return key;}
}''',
    'net/minecraft/client/MinecraftClient.java': '''package net.minecraft.client;
import net.minecraft.client.gui.screen.Screen;
public class MinecraftClient {public Screen currentScreen;}''',
    'net/minecraft/client/gui/widget/ButtonWidget.java': '''package net.minecraft.client.gui.widget;
import net.minecraft.text.Text;
public class ButtonWidget {
    public boolean active=true;public int presses;private final Text label;
    public ButtonWidget(String key){label=Text.translatable(key);}
    public Text getMessage(){return label;}
    public void onPress(){presses++;}
}''',
    'net/minecraft/client/gui/screen/Screen.java': '''package net.minecraft.client.gui.screen;
import java.util.List;
import net.minecraft.text.Text;
import net.minecraft.client.gui.widget.ButtonWidget;
public class Screen {
    private final Text title;
    public final ButtonWidget backup=new ButtonWidget("selectWorld.backupJoinConfirmButton");
    public final ButtonWidget skip=new ButtonWidget("selectWorld.backupJoinSkipButton");
    public Screen(String key){title=Text.translatable(key);}
    public Text getTitle(){return title;}
    public List<Object> children(){return List.of(skip,backup);}
}''',
    'net/minecraft/client/gui/screen/world/BackupPromptScreen.java': '''package net.minecraft.client.gui.screen.world;
public class BackupPromptScreen extends net.minecraft.client.gui.screen.Screen {
    public BackupPromptScreen(String key){super(key);}
}''',
    'lab/owmcguest/StartupPromptCheck.java': '''package lab.owmcguest;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.world.BackupPromptScreen;
public class StartupPromptCheck {
    static final String EXP="selectWorld.backupQuestion.experimental";
    static void check(boolean yes){if(!yes)throw new AssertionError();}
    public static void main(String[] args){
        var client=new MinecraftClient();client.currentScreen=new BackupPromptScreen(EXP);
        System.setProperty("owmc.worldName","selected");
        TwilightTrialStartup.tick(client,true);check(client.currentScreen.backup.presses==0);
        System.setProperty("owmc.startupBackupWorldName","other");
        TwilightTrialStartup.tick(client,true);check(client.currentScreen.backup.presses==0);
        System.setProperty("owmc.startupBackupWorldName","selected");
        TwilightTrialStartup.tick(client,false);check(client.currentScreen.backup.presses==0);
        client.currentScreen=new BackupPromptScreen("selectWorld.backupQuestion.downgrade");
        TwilightTrialStartup.tick(client,true);check(client.currentScreen.backup.presses==0);
        client.currentScreen=new BackupPromptScreen(EXP);client.currentScreen.backup.active=false;
        TwilightTrialStartup.tick(client,true);check(client.currentScreen.backup.presses==0);
        client.currentScreen.backup.active=true;
        TwilightTrialStartup.tick(client,true);TwilightTrialStartup.tick(client,true);
        check(client.currentScreen.backup.presses==1&&client.currentScreen.skip.presses==0);
        client.currentScreen=new BackupPromptScreen(EXP);
        TwilightTrialStartup.tick(client,false);check(client.currentScreen.backup.presses==0);
        TwilightTrialStartup.tick(client,true);check(client.currentScreen.backup.presses==0);
        System.setProperty("owmc.twilightTrial","true");System.setProperty("owmc.worldName","Overwatch Twilight fixture");
        TwilightTrialStartup.tick(client,false);check(client.currentScreen.backup.presses==1);
        System.out.println("PASS: exact world/initial phase/experimental-only/backup-first/once/trial compatibility");
    }
}''',
}


class PromptTests(unittest.TestCase):
    def test_real_adapter_uses_backup_only_inside_the_selected_startup_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            temporary=Path(folder)
            files=[]
            for relative,source in SOURCES.items():
                path=temporary/relative;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(source,encoding='utf-8');files.append(str(path))
            files.append(str(ROOT/'guest/src/client/java/lab/owmcguest/TwilightTrialStartup.java'))
            built=subprocess.run([str(JDK/'javac.exe'),'-d',str(temporary),*files],capture_output=True,timeout=30)
            self.assertEqual(built.returncode,0,built.stderr.decode(errors='replace'))
            result=subprocess.run([str(JDK/'java.exe'),'-cp',str(temporary),'lab.owmcguest.StartupPromptCheck'],capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
            self.assertIn(b'PASS:',result.stdout)


if __name__=='__main__':
    unittest.main()
