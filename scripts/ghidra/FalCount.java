import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import java.io.*;
public class FalCount extends GhidraScript {
    public void run() throws Exception {
        Listing l = currentProgram.getListing();
        int ins=0; for (InstructionIterator it=l.getInstructions(true); it.hasNext(); it.next()) ins++;
        println("FALCON ins="+ins+" lang="+currentProgram.getLanguageID());
        // first 40 instructions
        int n=0; for (InstructionIterator it=l.getInstructions(true); it.hasNext() && n<40; n++){ Instruction i=it.next(); println(i.getAddress()+"  "+i); }
    }
}