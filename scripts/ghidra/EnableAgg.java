import ghidra.app.script.GhidraScript;
public class EnableAgg extends GhidraScript {
  public void run() throws Exception {
    setAnalysisOption(currentProgram, "Aggressive Instruction Finder", "true");
    setAnalysisOption(currentProgram, "Shared Return Calls", "true");
    println("AGGRESSIVE ON");
  }
}
