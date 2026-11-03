package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.world.BackupPromptScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

/** Accept the selected lab world's initial experimental prompt, with vanilla backup. */
final class TwilightTrialStartup {
    private static BackupPromptScreen acceptedScreen;
    private static boolean selectedAccepted;
    static void tick(MinecraftClient client,boolean initialWorldLoading){
        // Entering vanilla startIntegratedServer from the backup button while
        // a resource reload overlay is active nests render(false) inside tick.
        // That loop cannot finish the tick-owned reload and even delays Stop.
        if(client.getOverlay()!=null)return;
        String world=System.getProperty("owmc.worldName","");
        boolean trial=Boolean.getBoolean("owmc.twilightTrial")&&world.startsWith("Overwatch Twilight ");
        boolean selected=initialWorldLoading&&!selectedAccepted&&!world.isBlank()
            &&world.equals(System.getProperty("owmc.startupBackupWorldName",""));
        if(!(trial||selected)||!(client.currentScreen instanceof BackupPromptScreen screen)
            ||screen==acceptedScreen
            ||!screen.getTitle().getString().equals(Text.translatable("selectWorld.backupQuestion.experimental").getString()))return;
        String label=Text.translatable("selectWorld.backupJoinConfirmButton").getString();
        for(var child:screen.children())if(child instanceof ButtonWidget button&&button.active&&button.getMessage().getString().equals(label)){
            acceptedScreen=screen;if(selected)selectedAccepted=true;
            System.out.println("[OWMCStartup] vanilla create-backup-and-load selected world");button.onPress();break;
        }
    }
}
