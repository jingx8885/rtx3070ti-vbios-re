# 03 — NPDE / BIT / JFFS 容器格式

结构定义已和 night199uk/010-nvidia-vbios 的 010 Editor 模板(NPDE.bt / BIT.bt /
NVidiaVBios.bt)交叉校对。

## NPDE(Turing+ 引入的签名段容器)

头 12~20 字节:

    u32  magic    "NPDE"
    u16  ver      (本 ROM 出现 1.0 / 1.1)
    u16  hdrLen   (1.0=12/16, 1.1=20)
    u32  size512  (低16位: 总大小/512)
    u32  flags
    ...  可选扩展字 + 表区(每项 4B)+ 数据

规则:载荷首 u32 常常是解压后大小 dsize;若是压缩段,压缩流紧跟其后裸存。
BIOS 尾部解析器按 PCIR→NPDS→SGIS→NPDE 签名链扫描。

| 偏移 | ver | hdrLen | size512 | 载荷内容 |
|---|---|---|---|---|
| 0x9390  | 1.1 | 20 | 127 | BIT 表 + x86 BIOS 头(整个 x86 镜像被 NPDE 包裹)|
| 0x19040 | 1.0 | 16 | 164 | UEFI GOP:表首 4B=dsize(0x27330),后接 EfiCompress 裸流 |
| 0x2d960 | 1.1 | 20 | 43  | devinit/init 字节码段 |
| 0x32e40 | 1.1 | 20 | 754 | 功耗/频率/devinit 表(u32 指针对 + 0xf9xx/0xfe 记录)|
| 0xc0e40 | 1.0 | 12 | 409 | JFFS 区 NPDE 头 |

## BIT(BIOS Information Table)@0x93b2

头:"BIT\0" + ver(u16@4) + hdrSize(u8@6) + entrySize(u8@7) + nEntries(u8@8) + cksum。
条目 6B:{ size u16, off u16, id u8, ver u8 };off 相对 x86 镜像基址(0x9200)。

MSI 镜像实测条目:

| id | ver | size | off | 含义(nouveau 惯例)|
|---|---|---|---|---|
| B | 2 | 37  | 0x23e | Board/BIOS info |
| C | 2 | 44  | 0x263 | Clocks |
| D | 1 | 4   | 0x28f | Display 指针("RP\0\0" 签名)|
| I | 1 | 36  | 0x293 | **Init 脚本指针表**(9 个 u16 段偏移 → 0xd132/0xd136/0xd1a2 devinit 脚本)|
| M | 2 | 41  | 0x2b7 | Memory/strap |
| N | 0 | 41  | 0x2b7 | — |
| P | 2 | 0   | 0     | Perf(此镜像为空)|
| S | 2 | 232 | 0x2e0 | Strings/字符表 |
| T | 1 | 24  | 0x3c8 | — |
| U | 1 | 2   | 0x3e0 | — |
| V | 1 | 5   | 0x3e2 | — |
| d,p,u,i,E,x | — | — | — | 小表若干(见 samples/bit_entries.json)|

envytools nvbios 对同一 ROM 输出 102085 行:BIT 全 17 项 + P 性能表 30+ 子表
(PERFORMANCE / MEMORY TIMINGS / VOLTAGE / THERMAL / POWER / FAN / BOOST / CSTEP /
PSTATE / LOW POWER)。注意:Ampere 上各子表指针是**签名混淆值**,nvbios 对 NPDE 包装代的
支持较老——表名/结构能对上,指针不要按字面解。

## init/devinit 字节码(BIT I 表 + NPDE 数据段)

NVIDIA 私有字节码,语义用 nouveau 文档 hw/nvidia/init/ + envytools nvbios 的
iinit/info 解析器逐条解。常见 opcode:INIT_RESUME=0x5d、INIT_ZM_REG=0x5a、
INIT_NV_REG=0x10、INIT_IO_* 等。

## JFFS 记录区 @0xc1000(板卡标识)

记录块 0x80 对齐,结构 { idx, TAG3, ver, dlen, data };目录项 5B { tag3, off16 }。
本 ROM 含:

    ROM  (dlen 212)   零售 ROM 标识
    IMG  = "G001.0000.03.03"   原厂 IMG 编号
    BRD / OBD="Generic" / OEM / BBO / RPRP   板卡与 OEM 信息
    RIBILU / ISBN 记录 @0xc0fe8

## RFRD(0x5000,ROM 文件系统目录)

v3,8 个条目,每项给出镜像内部各"文件"的偏移:
0x9200(x86 BIOS)/ 0x8a000(空槽)/ 0xc1000(JFFS)/ 0x31000(Falcon 固件)。
这是解析 ROM 时最先读的一张表。