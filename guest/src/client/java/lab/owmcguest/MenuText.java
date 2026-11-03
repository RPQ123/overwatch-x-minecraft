package lab.owmcguest;

import net.minecraft.text.Text;

/** Menu strings live in assets/owmcguest/lang, including native-window overlays. */
final class MenuText {
    private MenuText(){}
    static String get(String key,Object... args){return Text.translatable("menu.owmcguest."+key,args).getString();}
}
