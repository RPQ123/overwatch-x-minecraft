package lab.owmcguest;

import org.lwjgl.glfw.GLFW;

/** Visibility belongs to the session, independently of world loading and frame export. */
public final class BackgroundWindowVisibility {
    interface Windows {
        void hint(int name, int value);
        boolean visible(long handle);
        void hide(long handle);
        void showWithoutFocus(long handle);
    }

    static final class Controller {
        private final boolean startHidden, allowShow;
        private final Windows windows;
        private volatile boolean released, hidden;
        private volatile long corrections;

        Controller(boolean startHidden, boolean allowShow, Windows windows) {
            this.startHidden=startHidden;this.allowShow=allowShow;this.windows=windows;
        }
        boolean concealed() {return startHidden&&!released;}
        boolean allowShow() {return allowShow;}
        boolean hidden() {return hidden;}
        long corrections() {return corrections;}
        boolean fullscreen(boolean requested) {return !concealed()&&requested;}

        void prepareCreation() {
            if(concealed()) {
                // Hints must precede CreateWindow: hiding on the first world tick is too late.
                windows.hint(GLFW.GLFW_VISIBLE,GLFW.GLFW_FALSE);
                windows.hint(GLFW.GLFW_FOCUSED,GLFW.GLFW_FALSE);
                windows.hint(GLFW.GLFW_FOCUS_ON_SHOW,GLFW.GLFW_FALSE);
            }
        }
        void created(long handle) {enforce(handle);}
        void enforce(long handle) {
            if(!startHidden||handle==0)return;
            if(concealed()&&windows.visible(handle)) {windows.hide(handle);corrections++;}
            hidden=!windows.visible(handle);
            if(concealed()&&!hidden)throw new IllegalStateException("Background Minecraft window could not stay hidden");
        }
        boolean show(long handle) {
            if(!allowShow||handle==0)return false;
            released=true;windows.showWithoutFocus(handle);hidden=!windows.visible(handle);
            return true;
        }
    }

    private static final Controller STATE=new Controller(Boolean.getBoolean("owmc.startHidden"),
            Boolean.parseBoolean(System.getProperty("owmc.allowWindowShow","true")),new Windows() {
        public void hint(int name,int value) {GLFW.glfwWindowHint(name,value);}
        public boolean visible(long handle) {return GLFW.glfwGetWindowAttrib(handle,GLFW.GLFW_VISIBLE)!=GLFW.GLFW_FALSE;}
        public void hide(long handle) {GLFW.glfwHideWindow(handle);}
        public void showWithoutFocus(long handle) {
            GLFW.glfwSetWindowAttrib(handle,GLFW.GLFW_FOCUS_ON_SHOW,GLFW.GLFW_FALSE);
            GLFW.glfwShowWindow(handle);
        }
    });

    private BackgroundWindowVisibility() {}
    public static void prepareCreation() {STATE.prepareCreation();}
    public static void created(long handle) {STATE.created(handle);}
    public static boolean fullscreen(boolean requested) {return STATE.fullscreen(requested);}
    public static boolean concealed() {return STATE.concealed();}
    public static boolean allowShow() {return STATE.allowShow();}
    public static boolean hidden() {return STATE.hidden();}
    public static long corrections() {return STATE.corrections();}
    public static void enforce(long handle) {STATE.enforce(handle);}
    public static boolean show(long handle) {return STATE.show(handle);}
}
