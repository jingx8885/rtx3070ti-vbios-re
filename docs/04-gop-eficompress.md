# 04 — UEFI GOP 的"私有压缩"其实是标准 EfiCompress

## 现象

UEFI 镜像 @0x19000 的 NPDE@0x19040 载荷是一段压缩流;
MSI:csize=0x1468d, dsize=0x27330;ASUS:csize=0x168ac, dsize=0x2c690。
直接喂给各种解压器全败,一度判断为"NVIDIA 私有压缩,无公开解压器"。

## 结论(已硬破)

**是标准 UEFI EfiCompress(LZ77 + 动态 Huffman,PBIT=4,THRESHOLD=3,MAXMATCH=256),
只是 NPDE 把 EDK2 流的 8 字节 { csize u32, dsize u32 } 头拆走了:**

    EDK2 EfiCompress 输出 = [csize u32][dsize u32][压缩流]
    NVIDIA NPDE 存储      = [dsize u32 放载荷表首][csize 在 NPDE 头][压缩流裸存]

把 8 字节头拼回去,EfiDecompress **一次解出**。
ASUS 流解出结果与已知明文 GOP 逐字节相同,交叉验证通过。

## 之前失败的两个原因

1. 误用 Tiano 变体(PBIT=5)读位置码表 → BAD_TABLE。EfiCompress 是 PBIT=4。
2. 拿裸流当完整 EDK2 流 → 缺头,GetInfo 直接失败。
   lzss_bruteforce.py(穷举 flag 序/窗口/填充/偏移)全灭,佐证不是裸 LZSS 变体。

## 产物

    MSI GOP  -> 160560B PE32+ x64 EFI 驱动,Ghidra 反编译 296 函数
    ASUS GOP -> 182928B PE32+ x64,反编译 319 函数

识别到的内容:DriverEntry(加载 BIT、注册 GOP/EDID 协议)、sprintf/printf 族、
PCI 配置空间遍历(扫 10de:xxxx)、GOP SetMode/Blt、EDID 解析、FWSEC 安全校验。

## 工具(tools/gop-decompress/)

三件套都依赖 EDK2 BaseCompressionLib 源码,需自行获取(见下):

    nvdec   穷举扫描器:对偏移范围 x 位变换(mode0-6)x {efi,tiano} 网格尝试,
            命中即写出。当初破 GOP 就靠它。
            用法: nvdec stream csize dsize e|t|b out_prefix [s0 s1]

    nvdump  直读内部解码器:参数化 PBIT,跳过头部直接对裸流 Decode()。
            用法: nvdump in.bin outcap [pbit] [skip]

    efic    压缩器(压缩/重打包验证用)。
            用法: efic in.bin out.comp [e|t]

## 构建

    # 需要 EDK2 的四个文件(放在本目录,未随仓库分发,许可证见 edk2):
    #   MdeModulePkg/Library/BaseCompressionLib/{EfiCompress.c,TianoCompress.c,Decompress.c,Compress.h,Decompress.h}
    #   + MdePkg/Include/{BaseTypes.h,ProcessorBind.h}
    gcc -O2 -o nvdec  nvdec.c  Decompress.c EfiCompress.c TianoCompress.c
    gcc -O2 -o nvdump nvdump.c                 # nvdump.c 内部 #include "Decompress.c"
    gcc -O2 -o efic   efic.c   EfiCompress.c TianoCompress.c Compress.c

    # 最小复现(以 MSI GOP 为例,csize/dsize 从 NPDE 头/表首读):
    ./nvdec gop_stream.bin 0x1468d 0x27330 e out
    # 验证:输出应为 MZ 开头的 PE32+

## 备注

- bit-reversal/word-swap 那 7 种 xform 是早期假设"字节序被动过"留下的,
  最后证明流是标准的,mode 0 即命中;保留它们对别的卡仍有排错价值。
- 同代/同架构其它 NVIDIA VBIOS 的 GOP 大概率同构:NPDE 表首 dsize + EfiCompress 裸流。