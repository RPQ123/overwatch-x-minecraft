package lab.owmcguest.mixin;
import lab.owmcguest.BossHudTravelScope;
import net.minecraft.client.gui.hud.*;
import net.minecraft.entity.boss.BossBar;
import net.minecraft.network.packet.s2c.play.BossBarS2CPacket;
import net.minecraft.text.Text;
import java.util.*;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
@Mixin(BossBarHud.class)
public class BossBarTravelMixin {
    @Redirect(method="render",at=@At(value="INVOKE",target="Ljava/util/Map;values()Ljava/util/Collection;"))
    private Collection<ClientBossBar> owmc$visible(Map<UUID,ClientBossBar> bars){
        return bars.entrySet().stream().filter(e->BossHudTravelScope.visible(e.getKey())).map(Map.Entry::getValue).toList();
    }
    @Inject(method="handlePacket",at=@At("HEAD"))
    private void owmc$originalPacket(BossBarS2CPacket packet,CallbackInfo ci){
        packet.accept(new BossBarS2CPacket.Consumer(){
            public void add(UUID id,Text name,float percent,BossBar.Color color,BossBar.Style style,boolean sky,boolean music,boolean fog){BossHudTravelScope.added(id);}
            public void remove(UUID id){BossHudTravelScope.removed(id);}
            public void updateProgress(UUID id,float percent){}
            public void updateName(UUID id,Text name){}
            public void updateStyle(UUID id,BossBar.Color color,BossBar.Style style){}
            public void updateProperties(UUID id,boolean sky,boolean music,boolean fog){}
        });
    }
}
