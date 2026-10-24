# RTX 3070 Ti VBIOS Reverse Engineering

> English: this repository documents a complete static-analysis pipeline for a
> Turing+/Ampere-era NVIDIA VBIOS (PCI ROM): NVGI/RFRD/NPDE container parsing,
> 16-bit x86 real-mode BIOS decompilation with Ghidra, UEFI GOP decompression
> (standard EfiCompress minus its 8-byte header), Falcon fuc5 microcode
> disassembly with envytools, and a bare-metal MMIO probe for the Falcon debug
> port. All documents are written in Chinese. No NVIDIA firmware blobs or ROM
> dumps are included for copyright reasons.

## 这是什么

对 **MSI GeForce RTX 3070 Ti (GA104)** 真卡 dump 出的 VBIOS(999424 字节、版本 94.04.65.00.2A)
做的完整逆向工程记录与可复现工具链。对照镜像:ASUS RTX 3070 Ti(94.04.5A.00.56,
来自 TechPowerUp 公开库)。

## 主要结论(TL;DR)

| 区块 | 结果 |
|---|---|
| x86 16 位实模式 BIOS @0x9200 | Ghidra `x86:LE:16:Real Mode` + Aggressive Instruction Finder:81 → 310 函数全反编译 |
| UEFI GOP @0x19000(MSI/ASUS)| "NVIDIA 私有压缩"实为**标准 UEFI EfiCompress**,只是 NPDE 把 8 字节 {csize,dsize} 头拆走、流裸存;补头后一次解出 PE32+ |
| Falcon/PMU 固件 @0x31000(~360KB)| envydis `-m falcon -V fuc5` 直接解出明文 fuc5 微码;高熵区经熵切分定位为 HS 密文块 |
| envydis fuc5 ISA 覆盖缺口 | 自写补丁补齐缺失 ALU/cmp 指令 + 全部 crypto 指令命名(`patches/`)|
| HS 密文静态解密 | **不可能**(设计使然):密钥在硅熔丝、明文不经 host 内存;唯一理论截口是 falcon v4+ DEBUG 口 |
| 全 ROM 顶层结构 | NVGI x2 / RFRD / 板级信息 / x86 BIOS / UEFI GOP / NPDE x4 / JFFS 记录区,全部解析(见 `docs/02-rom-map.md`)|

## 仓库结构

    docs/         完整文档(环境、布局、格式、GOP 解压、Falcon、探针、过程总结、工具清单)
    scripts/      Ghidra headless 脚本 + REA/WSL 流水线脚本
    tools/        ROM 解析器、GOP 解压器(nvdec/nvdump/efic)、Falcon MMIO 探针
    patches/      envytools envydis fuc5 ISA 补丁
    samples/      小型分析输出样例(函数清单、字符串、BIT 表清单)

## 文档索引(过程与结论的全文都在这)

- [docs/01-environment-and-rea.md](docs/01-environment-and-rea.md) — 环境搭建 + REA 平台边界
- [docs/02-rom-map.md](docs/02-rom-map.md) — ROM 顶层布局逐段图
- [docs/03-npde-bit-jffs.md](docs/03-npde-bit-jffs.md) — NPDE / BIT / JFFS 格式细节
- [docs/04-gop-eficompress.md](docs/04-gop-eficompress.md) — GOP "私有压缩"真相与 nvdec 用法
- [docs/05-falcon-firmware.md](docs/05-falcon-firmware.md) — Falcon fuc5 微码、熵分区、补丁、HS 结论
- [docs/06-mmio-probe.md](docs/06-mmio-probe.md) — DEBUG 口活性探测 runbook(裸机 Linux)
- [docs/07-process-timeline.md](docs/07-process-timeline.md) — **过程总结**:时间线、弯路、方法论
- [docs/08-prior-art.md](docs/08-prior-art.md) — GitHub 相关项目与出处

## 复现速览

    # 1. dump 自己的 VBIOS(只读;切勿 --flash,会变砖)
    nvflashk --save my_vbios.rom          # github.com/notfromstatefarm/nvflashk

    # 2. 顶层结构 + 切块
    python tools/rom-parse/parse_rom.py  my_vbios.rom extracted
    python tools/rom-parse/parse2_full.py my_vbios.rom extracted

    # 3. x86 实模式段交给 REA+Ghidra(WSL)
    source scripts/rea/env.sh            # 见 docs/01
    rea search vbios_entry.com "" --kind procedures --target-format dos-com --provider ghidra --json

    # 4. GOP: EDK2 EfiDecompress + 补头(nvdec)
    # 5. Falcon: envydis -m falcon -V fuc5 + 本仓补丁

## 版权与安全说明

- 本仓库**不含**任何 NVIDIA ROM/固件二进制、反编译产物;所有文档基于自有分析撰写。
- VBIOS 属 NVIDIA 版权;dump 自己卡的 BIOS 用于研究请自行评估当地法律。
- **只读操作**:全部脚本默认只读;`nvflashk` 仅用 `--save`。**切勿** `--flash` 修改过的 VBIOS(签名校验会变砖)。
- `tools/falcon-probe/` 的 `--debug-test` 会向 falcon 寄存器写 BREAK/CONTINUE;请在无驱动的裸卡环境运行,风险自担。

## License

MIT(见 [LICENSE](LICENSE))。文档中的第三方项目(envytools、EDK2、Ghidra 等)各自保留原许可证。