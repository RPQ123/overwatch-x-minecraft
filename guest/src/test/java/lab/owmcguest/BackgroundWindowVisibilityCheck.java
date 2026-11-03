package lab.owmcguest;

import java.util.ArrayList;
import java.util.List;
import org.lwjgl.glfw.GLFW;

/** Pure fake-window contract: never initializes GLFW or starts Minecraft. */
public final class BackgroundWindowVisibilityCheck {
    private static void require(boolean value,String message) {
        if(!value)throw new AssertionError(message);
    }
    private static final class Windows implements BackgroundWindowVisibility.Windows {
        final List<String> events=new ArrayList<>();
        boolean visible=true,ignoreHide;
        long monitor,share,result=64;
        int width,height,hides,shows;
        public void hint(int name,int value) {
            events.add("hint:"+name+":"+value);
            if(name==GLFW.GLFW_VISIBLE)visible=value!=GLFW.GLFW_FALSE;
        }
        public long create(int width,int height,CharSequence title,long monitor,long share) {
            events.add("create");this.width=width;this.height=height;this.monitor=monitor;this.share=share;
            return result;
        }
        public boolean visible(long handle) {return visible;}
        public void hide(long handle) {hides++;if(!ignoreHide)visible=false;}
        public void showWithoutFocus(long handle) {shows++;visible=true;}
    }

    public static void main(String[] args) {
        var windows=new Windows();
        var hidden=new BackgroundWindowVisibility.Controller(true,false,windows);
        hidden.prepareCreation();long handle=windows.create(2560,1440,"loading",hidden.fullscreen(true)?88:0,123);hidden.created(handle);
        require(handle==64&&hidden.hidden()&&!windows.visible,"must be invisible at CreateWindow, before world load");
        require(windows.events.equals(List.of("hint:"+GLFW.GLFW_VISIBLE+":0","hint:"+GLFW.GLFW_FOCUSED+":0",
                "hint:"+GLFW.GLFW_FOCUS_ON_SHOW+":0","create")),"creation hints must precede window creation");
        require(windows.monitor==0&&windows.share==123,"hidden windows cannot be exclusive fullscreen");
        require(windows.width==2560&&windows.height==1440,"real export framebuffer dimensions must be retained");
        for(int frame=0;frame<120;frame++)hidden.enforce(handle);
        require(hidden.concealed()&&windows.hides==0,"loading/frames cannot reveal or repeatedly hide an invisible window");
        require(!hidden.show(handle)&&windows.shows==0,"showMinecraft=false cannot be overridden by /window/show");
        windows.visible=true;hidden.enforce(handle);
        require(!windows.visible&&hidden.corrections()==1,"a title/reconfigure visibility change must be corrected without a world gate");

        windows=new Windows();
        var deferred=new BackgroundWindowVisibility.Controller(true,true,windows);
        deferred.prepareCreation();handle=windows.create(1920,1080,"world",deferred.fullscreen(true)?88:0,0);deferred.created(handle);
        deferred.enforce(handle);require(windows.shows==0&&deferred.concealed(),"allowShow is not automatic reveal");
        require(deferred.show(handle)&&!deferred.concealed()&&!deferred.hidden(),"only explicit session release reveals the window");
        deferred.enforce(handle);require(windows.visible&&windows.hides==0,"released comparison window must remain switchable");

        windows=new Windows();
        var ordinary=new BackgroundWindowVisibility.Controller(false,true,windows);
        ordinary.prepareCreation();windows.create(960,540,"standalone",ordinary.fullscreen(true)?88:0,123);ordinary.created(64);
        require(windows.events.equals(List.of("create"))&&windows.monitor==88&&windows.visible,"ordinary visible MC is unchanged");

        windows=new Windows();windows.result=0;
        var failed=new BackgroundWindowVisibility.Controller(true,true,windows);
        failed.prepareCreation();handle=windows.create(960,540,"failed",0,0);failed.created(handle);
        require(handle==0&&!failed.hidden()&&!failed.show(0),"failed creation must not claim a hidden live window");

        windows=new Windows();windows.ignoreHide=true;
        var refused=new BackgroundWindowVisibility.Controller(true,false,windows);
        refused.prepareCreation();windows.create(960,540,"refused",0,0);refused.created(64);windows.visible=true;
        try {refused.enforce(64);throw new AssertionError("failed hide readback was accepted");}
        catch(IllegalStateException expected) {require(!refused.hidden(),"failed hide cannot claim invisibility");}
        System.out.println("Background window creation/deferred reveal/ownership contracts passed (no native GLFW calls)");
    }
}
