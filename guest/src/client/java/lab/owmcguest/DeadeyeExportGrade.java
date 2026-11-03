package lab.owmcguest;

import org.lwjgl.opengl.*;
import org.lwjgl.system.MemoryStack;

/** MC export-only sepia adapter for native Deadeye. Not the original OW shader.
 * One GPU pass; original MC framebuffer/depth, native hands and HUD are untouched. */
final class DeadeyeExportGrade implements AutoCloseable {
    private int program,vao,fbo,texture,width,height;private boolean disabled;
    private long frames,restored,activationNs;private float strength;private String error="";
    static volatile String status="{}";
    private static int shader(int type,String source){
        int id=GL20.glCreateShader(type);GL20.glShaderSource(id,source);GL20.glCompileShader(id);
        if(GL20.glGetShaderi(id,GL20.GL_COMPILE_STATUS)==0){String log=GL20.glGetShaderInfoLog(id);GL20.glDeleteShader(id);throw new IllegalStateException(log);}return id;
    }
    private void create(int w,int h){
        if(program==0){
            int vs=shader(GL20.GL_VERTEX_SHADER,"#version 150\nout vec2 uv;void main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);uv=p;gl_Position=vec4(p*2.-1.,0.,1.);}");
            int fs=0;
            try{
                fs=shader(GL20.GL_FRAGMENT_SHADER,"""
                    #version 150
                    uniform sampler2D scene;uniform float amount;in vec2 uv;out vec4 pixel;
                    void main(){vec4 c=texture(scene,uv);vec3 sepia=vec3(dot(c.rgb,vec3(.393,.769,.189)),dot(c.rgb,vec3(.349,.686,.168)),dot(c.rgb,vec3(.272,.534,.131)))*.85;
                    // Saturated red feedback must remain legible over a graded
                    // world: lethal skulls and the requested short blood burst.
                    float alert=smoothstep(.10,.40,c.r-max(c.g,c.b))*smoothstep(.15,.65,c.r);
                    pixel=vec4(mix(c.rgb,clamp(sepia,0.,1.),amount*.85*(1.-alert)),c.a);}
                    """);
                program=GL20.glCreateProgram();GL20.glAttachShader(program,vs);GL20.glAttachShader(program,fs);GL20.glLinkProgram(program);
                if(GL20.glGetProgrami(program,GL20.GL_LINK_STATUS)==0)throw new IllegalStateException(GL20.glGetProgramInfoLog(program));
            }finally{GL20.glDeleteShader(vs);if(fs!=0)GL20.glDeleteShader(fs);}
            vao=GL30.glGenVertexArrays();
        }
        if(w==width&&h==height)return;
        if(fbo!=0)GL30.glDeleteFramebuffers(fbo);if(texture!=0)GL11.glDeleteTextures(texture);
        texture=GL11.glGenTextures();GL11.glBindTexture(GL11.GL_TEXTURE_2D,texture);
        GL11.glTexParameteri(GL11.GL_TEXTURE_2D,GL11.GL_TEXTURE_MIN_FILTER,GL11.GL_NEAREST);GL11.glTexParameteri(GL11.GL_TEXTURE_2D,GL11.GL_TEXTURE_MAG_FILTER,GL11.GL_NEAREST);
        GL11.glTexImage2D(GL11.GL_TEXTURE_2D,0,GL11.GL_RGBA8,w,h,0,GL11.GL_RGBA,GL11.GL_UNSIGNED_BYTE,(java.nio.ByteBuffer)null);
        fbo=GL30.glGenFramebuffers();GL30.glBindFramebuffer(GL30.GL_DRAW_FRAMEBUFFER,fbo);GL30.glFramebufferTexture2D(GL30.GL_DRAW_FRAMEBUFFER,GL30.GL_COLOR_ATTACHMENT0,GL11.GL_TEXTURE_2D,texture,0);
        GL20.glDrawBuffers(GL30.GL_COLOR_ATTACHMENT0);
        if(GL30.glCheckFramebufferStatus(GL30.GL_DRAW_FRAMEBUFFER)!=GL30.GL_FRAMEBUFFER_COMPLETE)throw new IllegalStateException("Deadeye export framebuffer incomplete");
        width=w;height=h;
    }
    private void publish(){var o=new com.google.gson.JsonObject();o.addProperty("strength",strength);o.addProperty("frames",frames);o.addProperty("restored",restored);o.addProperty("disabled",disabled);o.addProperty("error",error);o.addProperty("scope","MC export-only sepia adapter");status=o.toString();}
    int colorFramebuffer(int original,int sourceTexture,int w,int h){
        float target=NativeDeadeyeController.INSTANCE.gradeStrength();
        if(target==0){activationNs=0;strength=0;publish();return original;}
        if(activationNs==0)activationNs=System.nanoTime();
        // Original graph's entrance chase lasts .4s. Scope loss clears at once.
        strength=Math.min(1,(System.nanoTime()-activationNs)/400_000_000f);
        if(disabled){publish();return original;}
        int oldProgram=GL11.glGetInteger(GL20.GL_CURRENT_PROGRAM),oldVao=GL11.glGetInteger(GL30.GL_VERTEX_ARRAY_BINDING),oldDraw=GL11.glGetInteger(GL30.GL_DRAW_FRAMEBUFFER_BINDING),oldActive=GL11.glGetInteger(GL13.GL_ACTIVE_TEXTURE);
        boolean depth=GL11.glIsEnabled(GL11.GL_DEPTH_TEST),blend=GL11.glIsEnabled(GL11.GL_BLEND),cull=GL11.glIsEnabled(GL11.GL_CULL_FACE),scissor=GL11.glIsEnabled(GL11.GL_SCISSOR_TEST),srgb=GL11.glIsEnabled(GL30.GL_FRAMEBUFFER_SRGB);
        int[] viewport=new int[4];GL11.glGetIntegerv(GL11.GL_VIEWPORT,viewport);
        GL13.glActiveTexture(GL13.GL_TEXTURE0);int oldTexture=GL11.glGetInteger(GL11.GL_TEXTURE_BINDING_2D);
        boolean[] mask=new boolean[4];
        try(var stack=MemoryStack.stackPush()){
            var bytes=stack.malloc(4);GL11.glGetBooleanv(GL11.GL_COLOR_WRITEMASK,bytes);for(int i=0;i<4;i++)mask[i]=bytes.get(i)!=0;
        }
        int result=original;
        try{
            create(w,h);GL30.glBindFramebuffer(GL30.GL_DRAW_FRAMEBUFFER,fbo);GL11.glViewport(0,0,w,h);
            GL11.glDisable(GL11.GL_DEPTH_TEST);GL11.glDisable(GL11.GL_BLEND);GL11.glDisable(GL11.GL_CULL_FACE);GL11.glDisable(GL11.GL_SCISSOR_TEST);GL11.glDisable(GL30.GL_FRAMEBUFFER_SRGB);GL11.glColorMask(true,true,true,true);
            GL20.glUseProgram(program);GL20.glUniform1i(GL20.glGetUniformLocation(program,"scene"),0);GL20.glUniform1f(GL20.glGetUniformLocation(program,"amount"),strength);
            GL11.glBindTexture(GL11.GL_TEXTURE_2D,sourceTexture);GL30.glBindVertexArray(vao);GL11.glDrawArrays(GL11.GL_TRIANGLES,0,3);frames++;result=fbo;
        }catch(Exception e){disabled=true;error=e.toString();}
        finally{
            GL20.glUseProgram(oldProgram);GL30.glBindVertexArray(oldVao);GL30.glBindFramebuffer(GL30.GL_DRAW_FRAMEBUFFER,oldDraw);GL11.glBindTexture(GL11.GL_TEXTURE_2D,oldTexture);GL13.glActiveTexture(oldActive);GL11.glViewport(viewport[0],viewport[1],viewport[2],viewport[3]);GL11.glColorMask(mask[0],mask[1],mask[2],mask[3]);
            enable(GL11.GL_DEPTH_TEST,depth);enable(GL11.GL_BLEND,blend);enable(GL11.GL_CULL_FACE,cull);enable(GL11.GL_SCISSOR_TEST,scissor);enable(GL30.GL_FRAMEBUFFER_SRGB,srgb);restored++;publish();
        }
        return result;
    }
    private static void enable(int state,boolean value){if(value)GL11.glEnable(state);else GL11.glDisable(state);}
    @Override public void close(){if(fbo!=0)GL30.glDeleteFramebuffers(fbo);if(texture!=0)GL11.glDeleteTextures(texture);if(vao!=0)GL30.glDeleteVertexArrays(vao);if(program!=0)GL20.glDeleteProgram(program);fbo=texture=vao=program=0;}
}
