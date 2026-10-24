import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.io.*;
public class DumpAll extends GhidraScript {
    public void run() throws Exception {
        String outDir = getScriptArgs()[0];
        FunctionManager fm = currentProgram.getFunctionManager();
        Listing listing = currentProgram.getListing();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FileWriter asm = new FileWriter(outDir + "/all_functions.asm");
        FileWriter c   = new FileWriter(outDir + "/all_functions.c");
        FileWriter idx = new FileWriter(outDir + "/functions_index.txt");
        int n=0;
        for (FunctionIterator it = fm.getFunctions(true); it.hasNext();) {
            Function f = it.next();
            idx.write(f.getEntryPoint() + "  " + f.getName() + "\n");
            asm.write("\n;==== " + f.getName() + " @ " + f.getEntryPoint() + " ====\n");
            InstructionIterator ins = listing.getInstructions(f.getBody(), true);
            while (ins.hasNext()) { Instruction i = ins.next(); asm.write(i.getAddress() + "  " + i + "\n"); }
            c.write("\n//=== " + f.getName() + " @ " + f.getEntryPoint() + " ===\n");
            try {
                DecompileResults r = di.decompileFunction(f, 60, monitor);
                DecompiledFunction df = r.getDecompiledFunction();
                c.write(df != null ? df.getC() : "// decompile failed\n");
            } catch (Throwable t) { c.write("// " + t + "\n"); }
            n++;
        }
        idx.close(); asm.close(); c.close();
        println("dumped " + n + " functions");
    }
}
