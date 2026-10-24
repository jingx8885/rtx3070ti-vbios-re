# tools/rom-parse

VBIOS 顶层结构解析器(纯 stdlib)。

    python parse_rom.py    <rom> [outdir]   # 55AA/PCIR 镜像、RFRD 目录、NPDE、切块
    python parse2_full.py  <rom> [outdir]   # BIT 条目、NPDE 细节、JFFS 记录、熵

输出:控制台报告 + outdir/ 下每段的 .bin + bit_*.bin + bit_entries.json。
对 MSI/ASUS 3070Ti ROM 的输出结论见 docs/02 与 docs/03。