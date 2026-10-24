import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.io.*;
public class DumpGop extends GhidraScript {
    public void run() throws Exception {
        String outDir = getScriptArgs().length>0 ? getScriptArgs()[0] : "/mnt/e/rea-nvidia-bios/out/ghidra";
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FileWriter c   = new FileWriter(outDir + "/gop_functions.c");
        FileWriter idx = new FileWriter(outDir + "/gop_index.txt");
        int n=0;
        for (FunctionIterator it = fm.getFunctions(true); it.hasNext();) {
            Function f = it.next();
            idx.write(f.getEntryPoint() + "  " + f.getName() + "\n");
            c.write("\n//=== " + f.getName() + " @ " + f.getEntryPoint() + " ===\n");
            try {
                DecompileResults r = di.decompileFunction(f, 60, monitor);
                DecompiledFunction df = r.getDecompiledFunction();
                c.write(df != null ? df.getC() : "// decompile failed\n");
            } catch (Throwable t) { c.write("// " + t + "\n"); }
            n++;
        }
        idx.close(); c.close();
        println("GOP dumped " + n + " functions");
    }
}
