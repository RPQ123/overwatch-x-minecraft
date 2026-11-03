package lab.owmcguest;

import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.management.ObjectName;
import net.fabricmc.loader.api.entrypoint.PreLaunchEntrypoint;

/** Own one optional C2 directive during cold loading, then restore normal JIT. */
public final class StartupCompilerBudget implements PreLaunchEntrypoint {
    private static final boolean ENABLED=Boolean.getBoolean("owmc.startupCompilerBudget");
    private static String initial="",error="";
    private static boolean captured,restored=!ENABLED;
    private static int initialCount,finalCount;
    private static long restoredAtMs;
    private static final String DIRECTIVE="[{\"match\":\"*::*\",\"c2\":{\"Exclude\":true}}]";
    private static ObjectName bean() throws Exception {return new ObjectName("com.sun.management:type=DiagnosticCommand");}
    private static String print() throws Exception {return (String)ManagementFactory.getPlatformMBeanServer().invoke(bean(),"compilerDirectivesPrint",new Object[0],new String[0]);}
    private static int count(String value){return (int)value.lines().filter(line->line.trim().startsWith("Directive:")).count();}

    @Override public synchronized void onPreLaunch(){
        if(!ENABLED||captured)return;
        try{
            String file=System.getProperty("owmc.startupCompilerBudgetFile","");
            if(file.isEmpty()||!Files.readString(Path.of(file)).trim().equals(DIRECTIVE))throw new IllegalStateException("Compiler budget file differs");
            var arguments=ManagementFactory.getRuntimeMXBean().getInputArguments();
            if(arguments.stream().filter(a->a.startsWith("-XX:CompilerDirectivesFile=")).count()!=1
                ||!arguments.contains("-XX:CompilerDirectivesFile="+file))throw new IllegalStateException("Compiler budget ownership differs");
            initial=print();initialCount=count(initial);
            if(initialCount!=2||!initial.contains("Exclude:true"))throw new IllegalStateException("Unexpected initial compiler directives: count="+initialCount+" excluded="+initial.contains("Exclude:true"));
            captured=true;
        }catch(Exception failure){error=failure.toString();throw new IllegalStateException(error,failure);}
    }

    public static synchronized boolean restored(){return restored;}
    public static synchronized void restore(){
        if(restored)return;
        try{
            if(!captured||!print().equals(initial))throw new IllegalStateException("Compiler directives changed externally; preserved");
            ManagementFactory.getPlatformMBeanServer().invoke(bean(),"compilerDirectivesRemove",new Object[0],new String[0]);
            String after=print();finalCount=count(after);
            if(finalCount!=1||after.contains("Exclude:true"))throw new IllegalStateException("Normal C2 compiler was not restored");
            restored=true;restoredAtMs=System.currentTimeMillis();
            System.out.println("[OWMCStartup] compiler_budget_restored");
        }catch(Exception failure){error=failure.toString();throw new IllegalStateException(error,failure);}
    }
    public static synchronized String status(){
        return "{\"enabled\":"+ENABLED+",\"captured\":"+captured+",\"restored\":"+restored+
            ",\"initialDirectives\":"+initialCount+",\"finalDirectives\":"+finalCount+
            ",\"restoredAtMs\":"+restoredAtMs+",\"compilationMs\":"+ManagementFactory.getCompilationMXBean().getTotalCompilationTime()+
            ",\"error\":"+new com.google.gson.Gson().toJson(error)+"}";
    }
}
