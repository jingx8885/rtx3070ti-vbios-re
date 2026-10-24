# 01 — 环境与 REA 工具链

## 硬件 / 固件对象

- 卡:MSI GeForce RTX 3070 Ti,GA104 核心,PCI dev id = 0x2482
- VBIOS:Version 94.04.65.00.2A,999424 字节,nvflashk --save 真卡 dump
- 对照:ASUS RTX 3070 Ti(94.04.5A.00.56,TechPowerUp VBIOS 库公开镜像)

## REA 是什么

REA(morluto/rea,npm 包 rea-agents)把逆向工具(Ghidra / Hopper / IDA / binwalk / unblob …)
统一接到 coding agent 或 CLI 上。它自己不反编译,而是**驱动 Ghidra 后台分析**并把结果
包成带证据(Evidence)的 JSON。

    npm install -g rea-agents   # 命令 rea,本项目用 6.7.0

## 平台边界(本项目踩过的最重要的坑)

- Windows 上的 REA Ghidra provider 只放行 **PE** 和 **6502 裸镜像**;
  **裸 x86 VBIOS 必须走 Linux**。本项目用 WSL Ubuntu-22.04。
- VBIOS 的 x86 部分是 **16 位实模式**。REA 对应 lane:

| lane | Ghidra 语言 | 适用 |
|---|---|---|
| --target-format dos-com | x86:LE:16:Real Mode | 入口固定 1000:0100(线性 0x10100),文件上限 65280B |
| --target-format raw-binary --architecture x86 | x86:LE:32:default | 32 位;实模式代码会被解错,只能看保护模式片段 |
| Falcon/PMU/GSP 固件 | — | 非 x86,REA 现有 lane 不覆盖,需 envytools/Ghidra Falcon 扩展 |

- COM lane 单次最多 65280B;~976KB 的 ROM 需按 64KB 窗口分块。

## WSL 环境(已验证可复现)

/opt/rea-tools/ 下:

    node v22.23.4(镜像源安装)
    openjdk-21-jdk-headless
    ghidra_12.1.4_PUBLIC
    npm i -g rea-agents   -> rea 6.7.0

一键脚本:scripts/rea/wsl-setup.sh(node+JDK+Ghidra+rea 安装 + rea doctor 自检)。
环境变量:scripts/rea/env.sh(PATH / GHIDRA_INSTALL_DIR / JAVA_HOME / REA_ANALYSIS_PROVIDER)。

## REA 用法(VBIOS)

    source env.sh
    rea doctor --provider ghidra --json                 # 环境自检, healthy:true
    rea inspect     <target.com> --target-format dos-com --provider ghidra --json
    rea inspect-native-load-image  ... 同上参数 --json  # 加载器准入证据
    rea search      <target> "" --kind procedures --target-format dos-com --provider ghidra --json
    rea instructions <target> 0x10100 --target-format dos-com --provider ghidra --json
    rea decompile   <target> 0x10100 --target-format dos-com --provider ghidra --json
    rea decompile   <target> --file-offset 0xNN --target-format dos-com --provider ghidra --json

完整流水线见 scripts/rea/analyze.sh。

## 目标切片

    vbios_entry.com = ROM[0x9203 : 0x9203+65280]

从入口指令 EB(跳转)处开始取 64KB,COM 入口 0x10100 即真实 POST 入口。

## 已知限制

- 静态反编译不跑硬件:POST 的寄存器/显存初始化效果要对照 BIT/init 表读,不模拟。
- GSP/Falcon 安全固件不是 x86;REA 不能反编译,走 envytools(见 docs/05)。
- NvAPI_GPU_GetVbiosImage 在这块卡上返回 -9(dump-vbios.ps1 记录了该路径),所以用 nvflashk。

## nvflashk 安全红线

    nvflashk --save my.rom    # OK,只读
    nvflashk --flash ...      # 切勿。改过的 VBIOS 过不了签名,会变砖