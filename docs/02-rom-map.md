# 02 — ROM 顶层布局

工具:tools/rom-parse/parse_rom.py、parse2_full.py(输入任意 ROM,输出本表 + extracted/ 切块)。

## MSI 镜像(94.04.65.00.2A,999424 B)

| 偏移 | 大小 | 内容 | 状态 |
|---|---|---|---|
| 0x000000 | 0x2000 | NVGI 签名/证书块 #1 | 已提取 |
| 0x002000 | 0x2000 | NVGI 签名/证书块 #2 | 已提取 |
| 0x004000 | 0x1000 | 0xff 填充 | — |
| 0x005000 | 0x200 | RFRD v3 文件目录(8 项)| 已解析 |
| 0x005200 | 0x200 | 板级信息表("113467msi"、"P67217R1")| 已提取 |
| 0x005400–0x9200 | — | 0 填充 | — |
| 0x009200 | 65024 | **x86 16 位实模式 BIOS 镜像**(55AA;PCIR dev=2482 type=0)| **310 函数已反编译** |
| 0x01855b | ~2.6K | 镜像尾部:NVIDIA 结构解析器(遍历 PCIR/NPDS/SGIS/NPDE)| 已反汇编 |
| 0x019000 | 83968 | **UEFI GOP 镜像**(55AA;PCIR dev=2482 type=3 LAST;NPDE 载荷=压缩流)| 已解压+反编译 |
| 0x02d800–0x31000 | ~14K | NPDE 数据块(devinit 字节码)| 已解析 |
| 0x031000–0x89000 | ~360K | **Falcon/PMU 签名固件**(高熵)| 已反汇编(docs/05)|
| 0x088000–0x8a000 | — | RFRD 空槽 + 测试模式填充 aa 33 cc f0 | — |
| 0x0c0000–0xc2000 | ~8K | JFFS 记录区(ROM/IMG/BRD/OBD/OEM/BBO/RPRP)| 已解析 |
| 0x0c2000–0xf4000 | — | 0xff/0x00 填充 | — |

## ASUS 镜像(94.04.5A.00.56)对照

| 偏移 | 内容 |
|---|---|
| 0x000000 / 0x002000 | NVGI 签名块 x2 |
| 0x005000 | RFRD → 条目 0x9200 / 0x8a000 / 0xc1000 / 0x31000 |
| 0x009200 | x86 BIOS(55AA,0x7f*512=0xfe00;PCIR@0x9370,BIT@0x93b2)|
| 0x019000 | EFI 镜像(PCI FW 压缩;8B 头 @0x19050:csize=0x168ac dsize=0x2c690;PCIR@0x1901c)|
| 0x031000 | JFFS 表 → 签名 blob 0x31000..0x89000(~360KB)|
| 0x08a000 | RFRD[1] 空槽 |
| 0x0c1000 | JFFS:IMG=G001.0000.03.03,OEM=PPIDROG-STRIX-RTX3070TI-O8G-GAMING;RIBILU/ISBN @0xc0fe8 |
| 0x0e0000+ | 0xff 填充至 0xf4000 |

## x86 镜像内部(0x9200 起)

- 55AA + eb 4b 短跳转;PCIR @ +0x170(VID 10DE DID 2482 class 030000)
- 字符串:"Version 94.04.65.00.2A"、"MSINV505MH.161"、"PG141 SKU 10 VGA BIOS"、
  "IBM VGA Compatible"、"PLEASE POWER DOWN AND CONNECT THE PCIe POWER CABLE(S)"
  (未接外供电的蜂鸣提示)— 见 samples/x86-image-strings.txt
- Ghidra x86:LE:16:Real Mode,入口 0x10100
- 尾部 @0x1855b:NPDE/PCIR/SGIS 结构遍历器(BIOS 自我解析签名块)

## 函数计数(为什么 81 → 310)

- 默认分析:81 procedures(REA doctor 证据见 samples/procedures.json)
- 开启 **Aggressive Instruction Finder** + Shared Return Calls(scripts/ghidra/EnableAgg.java):
  **310 函数,0 失败**。实模式代码里大量"落在代码中间"的函数头只有 AIF 能找回。

## 各 blob 可解性一览

| Blob | 类型 | 工具 | 状态 |
|---|---|---|---|
| x86 镜像 | x86-16 BIOS | Ghidra/REA、ndisasm | 已解 |
| UEFI GOP | PE32+ x64 EFI 驱动(5 节区)| Ghidra x64 | 已解(需先解压)|
| Falcon/PMU 固件 | NVIDIA 签名 fuc5 微码 | envytools envydis(+补丁)、Ghidra Falcon 扩展 | 明文区已解;HS 区为密文 |
| BIT init 脚本 | devinit 字节码 | envytools nvbios / nouveau iinit | 可逐条解 |

## 一个常被问的问题

VBIOS 里**没有 CUDA/SASS(cubin)代码**。GPU 侧代码是 NVIDIA 签名的 Falcon/devinit 固件;
"反编译 VBIOS 里的 CUDA"这个需求本身不成立。cubin/PTX 属于驱动栈,不在 PCI ROM 里。