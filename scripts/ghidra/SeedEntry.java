import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
public class SeedEntry extends GhidraScript {
    public void run() throws Exception {
        Address a = toAddr(0x10100);
        createEntryPoint(a);
        println("seeded entry at " + a);
    }
}
