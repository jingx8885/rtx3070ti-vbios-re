$ErrorActionPreference = 'Stop'
$cs = @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class NvApi {
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern IntPtr LoadLibrary(string path);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern IntPtr GetProcAddress(IntPtr mod, string name);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate IntPtr QueryInterfaceDelegate(uint id);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate int InitializeDelegate();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate int EnumPhysicalGPUsDelegate(IntPtr handles, out int count);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate int GetStringDelegate(IntPtr gpu, IntPtr buf);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate int GetVbiosImageDelegate(IntPtr gpu, ref uint size, IntPtr buffer);

    static T Get<T>(QueryInterfaceDelegate qif, uint id) {
        return Marshal.GetDelegateForFunctionPointer<T>(qif(id));
    }

    public static int Dump(string outFile, StringBuilder log) {
        IntPtr lib = LoadLibrary("nvapi64.dll");
        if (lib == IntPtr.Zero) lib = LoadLibrary("C:/Windows/System32/nvapi64.dll");
        if (lib == IntPtr.Zero) { log.AppendLine("nvapi64.dll NOT FOUND"); return -1; }
        IntPtr qi = GetProcAddress(lib, "nvapi_QueryInterface");
        if (qi == IntPtr.Zero) { log.AppendLine("no nvapi_QueryInterface"); return -2; }
        var qif = Marshal.GetDelegateForFunctionPointer<QueryInterfaceDelegate>(qi);

        int st = Get<InitializeDelegate>(qif, 0x0150E828u)();
        log.AppendLine("NvAPI_Initialize -> " + st);
        if (st != 0) return st;

        IntPtr handles = Marshal.AllocHGlobal(64 * IntPtr.Size);
        IntPtr strBuf = Marshal.AllocHGlobal(512);
        try {
            int count;
            st = Get<EnumPhysicalGPUsDelegate>(qif, 0xE5AC921Fu)(handles, out count);
            log.AppendLine("EnumPhysicalGPUs -> " + st + " count=" + count);
            if (st != 0) return st;
            for (int i = 0; i < count; i++) {
                IntPtr gpu = Marshal.ReadIntPtr(handles, i * IntPtr.Size);
                Get<GetStringDelegate>(qif, 0xCEEE8E9Fu)(gpu, strBuf);
                string name = Marshal.PtrToStringAnsi(strBuf);
                Get<GetStringDelegate>(qif, 0xA561FD7Du)(gpu, strBuf);
                string ver = Marshal.PtrToStringAnsi(strBuf);
                log.AppendLine("gpu[" + i + "] name='" + name + "' vbios='" + ver + "'");
                if (!name.Contains("3070")) continue;

                // attempt 1: size query with NULL
                uint sz = 0;
                st = Get<GetVbiosImageDelegate>(qif, 0xFC13EE11u)(gpu, ref sz, IntPtr.Zero);
                log.AppendLine("NULL-query st=" + st + " size=" + sz);
                if (st != 0 || sz == 0) {
                    // attempt 2: big buffer with capacity in/out
                    sz = 16u * 1024u * 1024u;
                }
                IntPtr buf = Marshal.AllocHGlobal((int)sz);
                try {
                    uint cap = sz;
                    st = Get<GetVbiosImageDelegate>(qif, 0xFC13EE11u)(gpu, ref cap, buf);
                    log.AppendLine("read st=" + st + " returned=" + cap);
                    if (st == 0 && cap > 0 && cap <= sz) {
                        byte[] data = new byte[cap];
                        Marshal.Copy(buf, data, 0, (int)cap);
                        System.IO.File.WriteAllBytes(outFile, data);
                        log.AppendLine("WROTE " + outFile + " " + cap + " bytes");
                    }
                } finally { Marshal.FreeHGlobal(buf); }
                return st;
            }
            log.AppendLine("no 3070 handle matched");
            return -3;
        } finally {
            Marshal.FreeHGlobal(handles);
            Marshal.FreeHGlobal(strBuf);
        }
    }
}
"@
Add-Type -TypeDefinition $cs
$log = New-Object System.Text.StringBuilder
$rc = [NvApi]::Dump('E:/rea-nvidia-bios/vbios_3070ti.rom', $log)
Write-Output $log.ToString()
Write-Output ('rc=' + $rc)
$f = 'E:/rea-nvidia-bios/vbios_3070ti.rom'
if (Test-Path $f) {
  $b = [IO.File]::ReadAllBytes($f)
  Write-Output ('file: ' + $f + ' ' + $b.Length + ' bytes')
  Write-Output ((($b[0..63] | ForEach-Object { $_.ToString('x2') }) -join ' '))
}
