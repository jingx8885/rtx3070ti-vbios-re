import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.Address;
import java.io.*;

public class DumpDecomp extends GhidraScript {
  public void run() throws Exception {
    String outPath = getScriptArgs().length > 0 ? getScriptArgs()[0] : "/tmp/decomp.c";
    String seedHex = getScriptArgs().length > 1 ? getScriptArgs()[1] : null;
    if (seedHex != null) {
      Address entry = toAddr(seedHex);
      if (entry != null) {
        disassemble(entry);
        createFunction(entry, "entry_bios_init");
        analyzeAll(currentProgram);
      }
    }
    DecompInterface ifc = new DecompInterface();
    ifc.openProgram(currentProgram);
    PrintWriter pw = new PrintWriter(new FileWriter(outPath));
    int ok = 0, fail = 0, total = 0;
    for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
      total++;
      pw.println("/* ===== " + f.getName() + " @ " + f.getEntryPoint() + " ===== */");
      DecompileResults res = ifc.decompileFunction(f, 60, monitor);
      if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
        pw.println(res.getDecompiledFunction().getC());
        ok++;
      } else { pw.println("/* DECOMPILE FAILED */"); fail++; }
      pw.println();
    }
    pw.println("/* SUMMARY functions=" + total + " ok=" + ok + " fail=" + fail + " */");
    pw.close();
    println("FUNCS total=" + total + " ok=" + ok + " fail=" + fail);
  }
}
