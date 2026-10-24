# 05 — Falcon/PMU 固件(0x31000,~360KB)

## 结论先行

- envydis -i 07_fw_31000.bin -m falcon -V fuc5 **直接解出明文 fuc5 微码**。
  "签名加密、静态不可解"的早期判断是错的——blob 是明文代码与 HS 密文块交织。
- 明文区已 100% 解出;HS 区经论证在软件层无解(密钥在硅熔丝,见文末)。
- envydis 的 fuc5 ISA 表有覆盖缺口,本项目补了一块补丁(patches/falcon_envydis_gap.patch)。

## 反汇编产物

    envydis -m falcon -V fuc5   ->  124374 行(mov/ld/st/shl/extr/cmp/mod ...)
    ??? [unknown instruction] 初始 20626 行

交叉验证:Ghidra + marysaka/ghidra_falcon 扩展(falcon:LE:32:v5)对同一 blob
只解出 21 函数/663 指令——佐证大片高熵区不是代码。

## 熵分区(0x100 粒度)

blob 是单个 ucode image,代码与 HS 块交织(新布局,非旧 ucode_desc 格式):

    0x00000-0x01c00   7KB  HS #0(签名/描述符头区)
    0x01c00-0x0a600  34KB  plain code/data
    0x0a600-0x18a00  57KB  HS #1(最大加密固件块)
    0x19000-0x19600 ~1KB   plain
    0x19600-0x27a00  57KB  HS #2
    0x27e00-0x37e00  64KB  plain code
    0x37e00-0x3cc00  19KB  HS #3
    0x3d200-0x41c00  18KB  HS #4
    0x41c00-0x58000  89KB  plain code+数据尾

## "???" 指令的分类账

对 20626 行 unknown 做熵相关分析:

| 类别 | 数量 | 占比 | 说明 |
|---|---|---|---|
| HS 密文误报 | 18330 | 89% | 熵>7.8 区(0xc000-0x27000、0x38000 等),线性扫描把密文当指令 |
| 代码区内嵌数据 | ~1520 | 7% | 常量表/数据被误当指令 |
| envydis ISA 缺口(真指令)| ~530 | 2.6% | 两边都是已知指令,疑似未建模的 fuc5 指令 |
| 混合/边缘 | 246 | 1.2% | — |

## 补丁:envydis fuc5 缺口补齐

patches/falcon_envydis_gap.patch(envydis/falcon.c,+17 行,已编译验证):

- R-R ALU 组 0x1x:补 16/19/1a/1b/1e/1f → 占位名 unkaluXX
- R-R cmp/st 组 0x2x:补 22/23/27-2f → unkcmpXX
- crypto xfer f4/f5+0x3x:按 Ghidra crypt_inst.sinc 映射命名:
  cnop cmov cxsin cxsout crnd cs0begin cs0exec cs1begin cs1exec cchmod
  cxor cadd cand crev cgfmul csecret ckeyreg ckexp ckrexp cenc cdec
  csigcmp csigenc csigclr

效果:??? 从 20626 → 9128(代码区仅剩 ~380 杂项 + 密文边缘)。
说明:unkalu/unkcmp 是占位名,操作数/编码已定,语义待对照真卡确认。

## 标注修正

f5 3c LL HH 的高字节最初被错标成寄存器;正确解法是 HH=tabcocmd 操作码。
重标后统计:csecret x32, cxor x34, ckeyreg x2, cenc x2, crnd x4, cxset x3。

## HS 明文为什么拿不到(机制实锤)

依据:envytools vm.rst/xfer.rst + nouveau ga102.c + 明文反汇编读出的 crypto 序列。

1. host 上传:sysmem 密文 → XFER_CTRL(mode=code_load, secret=bit2)→
   crypto 单元边传边 AES 解密 → 直接落 IMEM secret 页。
   **明文从不经过 host 内存**;nvagetpub/nvidia-smi 只能拿到 sysmem 密文副本。
2. host 读 secret 页:IMEMD 返回 0xdead5ec1;上传期 secret_lockdown 全锁;
   secret 页只有先被非 secret 数据整页覆盖才能清除标志——无读回通路。
3. 解密钥:明文微码 0x9ca9/0x4fc15 处的 crypto 序列 = 读熔丝密钥 x8 + cxor 派生
   + 绑定 + cenc。**密钥源是硅片熔丝,不是镜像数据 → 静态复现解密不可能。**
4. 引擎能力:CAPS2 VERSION=v4/v5, CRYPT=HEAVY(rnndb falcon.xml)。

## 唯一理论截口:falcon v4+ DEBUG 口(MMIO 0x200-0x20c)

rnndb:BREAK / CONTINUE_FROM_ADDR / SINGLE_STEP / REG_RD / REG_WR / DATA_RD /
DATA_WR / IO_RD / IO_WR / STATUS_RD + BREAKPOINT regs(0x098x2)+ data-ld/st 断点位。

- 零售卡大概率被 debug-disable 熔丝关掉(公开资料无成功案例)。
- 若可用:SINGLE_STEP+REG_READ 可对 secret 区逐条行为追踪;DATA_RD 抓 ucode
  主动 st/xdst 出的中间结果;CONTINUE_FROM_ADDR 跳进 secret 页内 gadget 理论上可外泄。
- 其他全部堵死:JTAG 无、IMEM DMA 读回无、faucon 模拟无熔丝钥、
  csigcmp 漏洞 Ampere 已修、故障注入成本极高。

探测脚本见 tools/falcon-probe/ 与 docs/06。

## 附:strap vs fuse(4090 48G 改装的启示)

4090→48G 改装三件套:定制 PCB 双面 24x2GB GDDR6X(clamshell)+ 改 strap 电阻
+ 刷官方 L40S/4090D-48G 真签名 VBIOS(签名绕不过,用真身)。

pstraps.rst:复位后数周期采样显存总线引脚电平=strap;primary/secondary+select;
secondary 从 BIOS ROM 0x58-0x64 加载;PSTRAPS MMIO @0x101000 可运行时覆写(bit31=en);
GF119+ 有第三组。

**假设**:GA102 falcon debug-disable 若由 strap 位而非 fuse 控制,改电阻或 MMIO 覆写
PSTRAPS 即可打开 DEBUG 口——所以探针顺带 dump PSTRAPS + fuse 块(见 docs/06)。