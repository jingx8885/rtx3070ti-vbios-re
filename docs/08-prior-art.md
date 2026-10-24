# 08 — GitHub 相关项目(已核实)

本项目用到的,以及同领域值得看的:

## NVIDIA 逆向全家桶

- **envytools/envytools** — 核心。envydis(Falcon 微码反汇编,fuc/fuc5)、
  nvbios(完整 VBIOS 表解析:bit.c/p.c/info.c/mem.c/power.c/dcb.c/gpio.c)、
  nvagetpub/nvdump(运行时取解密后的固件/寄存器,绕开静态加密)。
  构建:cmake;用法:envydis -i fw.bin -m falcon -V fuc5
- **vbe0201/faucon** — Falcon 套件(模拟器等)
- **marysaka/ghidra_falcon** — Ghidra Falcon 语言模块(falcon:LE:32:v0..v5),
  本项目用它交叉验证 envydis 输出

## VBIOS 结构/补丁

- **night199uk/010-nvidia-vbios** — 010 Editor 模板:NPDE.bt/BIT.bt/NVidiaVBios.bt。
  NPDE 头 12B、BITENTRY {id,ver,len,off16} 的官方结构定义来源
- **Matoking/NVIDIA-vBIOS-VFIO-Patcher** — VBIOS 修补(VFIO 场景)
- **antroids/nv-rom-parser** — ROM 解析器
- **cmdrNumber2/HP-NVS510-UEFI-GOP** — 另一张卡 GOP 的参考实现

## 压缩

- **chipsec/chipsec**(chipsec_tools/compression)— EfiCompressor,
  现成的 EfiCompress/TianoCompress 解压实现,免自己编 EDK2
- tianocore/edk2 — BaseCompressionLib(nvdec/nvdump/efic 依赖的源码出处)

## dump 工具

- **notfromstatefarm/nvflashk** — 本项目取 ROM 用的工具(--save 只读)

## SASS(与 VBIOS 无关但常被一起问)

- **laanwj/decuda** — G80 时代 SASS 反汇编,太老不适用于 GA104
- **redplait/denvdis** — 现代 SASS 反汇编
- **cloudcores/CuAssembler** — SASS 汇编器

## 文档

- nouveau hw/nvidia/init/ 文档 — init/devinit 字节码 opcode 语义
- envytools docs(rst):vm.rst / xfer.rst / pstraps.rst / rnndb falcon.xml —
  XFER_CTRL secret 上传路径、PSTRAPS、falcon DEBUG 寄存器定义的出处
- pipinovi4/ga107m-bar1-bad0ac — GA107M 实测:被拦截 MMIO 读返回
  0xBAD0ACxx 毒化值(判定探针读数是否被硬件拦截的参照)