package lab.owmcguest;
import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.management.ObjectName;

public final class StartupCompilerBudgetCheck {
    public static void main(String[] args) throws Exception {
        var server=ManagementFactory.getPlatformMBeanServer();var bean=new ObjectName("com.sun.management:type=DiagnosticCommand");
        new StartupCompilerBudget().onPreLaunch();
        if(StartupCompilerBudget.restored())throw new AssertionError("Budget was not active");
        if(args.length>0){
            Path extra=Path.of(System.getProperty("owmc.compilerTestDirectory"),"external.json");
            Files.writeString(extra,"[{\"match\":\"*::external\",\"c2\":{\"Exclude\":false}}]");
            server.invoke(bean,"compilerDirectivesAdd",new Object[]{new String[]{"\""+extra+"\""}},new String[]{"[Ljava.lang.String;"});
            boolean refused=false;try{StartupCompilerBudget.restore();}catch(IllegalStateException expected){refused=true;}
            String current=(String)server.invoke(bean,"compilerDirectivesPrint",new Object[0],new String[0]);
            if(!refused||current.lines().filter(line->line.trim().startsWith("Directive:")).count()!=3)throw new AssertionError("External directive was changed");
            System.out.println("PASS: changed external directive preserved; no unowned pop");return;
        }
        StartupCompilerBudget.restore();StartupCompilerBudget.restore();
        String after=(String)server.invoke(bean,"compilerDirectivesPrint",new Object[0],new String[0]);
        if(!StartupCompilerBudget.restored()||after.contains("Exclude:true")||after.lines().filter(line->line.trim().startsWith("Directive:")).count()!=1)
            throw new AssertionError("Original C2 state not restored exactly once");
        System.out.println("PASS: actual HotSpot C2 budget restored before world frames; duplicate restore is inert");
    }
}
