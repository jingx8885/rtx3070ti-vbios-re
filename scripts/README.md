# scripts/

- ghidra/ — Ghidra headless 脚本(均为 GhidraScript Java)

| 脚本 | 用途 |
|---|---|
| EnableAgg.java | preScript:开 Aggressive Instruction Finder + Shared Return Calls(81→310 函数的关键)|
| DumpDecomp.java | postScript:把每个函数的反编译 C 写到一个文件 |
| DumpAll.java    | 全量导出:伪代码 + 反汇编 + 函数索引 |
| DumpGop.java    | GOP PE32+ 专用导出 |
| DumpFal.java / FalCount.java | Falcon 固件(配合 ghidra_falcon 扩展)|
| SeedEntry.java  | 手动种入口点 |

    # 典型用法(headless)
    analyzeHeadless <projdir> <projname> -import vbios.com -processor "x86:LE:16:Real Mode" \
      -loader BinaryLoader -preScript EnableAgg.java -postScript DumpDecomp.java /tmp/decomp.c

- rea/ — REA/WSL 流水线

| 脚本 | 用途 |
|---|---|
| wsl-setup.sh | 装 node+JDK21+Ghidra+rea-agents,跑 rea doctor |
| env.sh       | 注入 PATH/GHIDRA_INSTALL_DIR/JAVA_HOME/REA_ANALYSIS_PROVIDER |
| analyze.sh   | 完整 REA 体检+inspect+函数表+反编译,输出 JSON |
| stage2.sh    | wsl-setup 的续段(分步安装时用)|