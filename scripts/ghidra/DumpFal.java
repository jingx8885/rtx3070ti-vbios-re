import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
public class DumpFal extends GhidraScript {
    public void run() throws Exception {
        String outDir = "/mnt/e/rea-nvidia-bios/out/ghidra";
        Listing l = currentProgram.getListing();
        FileWriter w = new FileWriter(outDir + "/falcon_firmware.asm");
        int ins=0, fn=0;
        // functions
        for (FunctionIterator it=currentProgram.getFunctionManager().getFunctions(true); it.hasNext();) { it.next(); fn++; }
        w.write("; Falcon v5 firmware disasm  functions="+fn+"\n");
        for (InstructionIterator it=l.getInstructions(true); it.hasNext();) {
            Instruction i=it.next();
            w.write(i.getAddress()+"  "+i+"\n"); ins++;
        }
        w.close();
        println("FAL_DUMP ins="+ins+" funcs="+fn);
    }
}