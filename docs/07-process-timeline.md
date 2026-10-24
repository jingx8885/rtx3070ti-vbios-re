# 07 — 过程总结(时间线 + 弯路 + 方法论)

这份文档记录"怎么做到的",包括走错的每一步——弯路比结论更有复现价值。

## 时间线

### 1. 拿 ROM
- NvAPI_GPU_GetVbiosImage 返回 -9(NvAPI 路径堵死,记录于 tools/dump-vbios/)
- 改用 nvflashk --save,拿到本机 MSI 卡 999424B 真镜像
- 同时从 TechPowerUp 拿 ASUS 同代镜像做差分对照

### 2. 选对反编译环境
- Windows REA 的 Ghidra provider 只放行 PE/6502;裸 x86 VBIOS 被判"不支持"
- 结论:VBIOS 是 16 位实模式,必须 dos-com lane → 只能在 WSL/Linux 跑
- 装好 WSL Ubuntu-22.04 + node + JDK21 + Ghidra 12.1.4 + rea-agents 6.7.0

### 3. 顶层结构
- 手写 parse_rom.py:扫 55AA/PCIR → 认 RFRD → 认 NPDE → 认 JFFS
- 关键发现:ROM 不是"一个 BIOS 镜像",而是 NVGI 签名头 + RFRD 文件系统
  + NPDE 容器层层包裹的多 blob 结构(Turing+ 新格式)
- 用 010 Editor 模板(night199uk/010-nvidia-vbios)校对 NPDE/BIT 结构定义,
  纠正了自己解析器的字段偏移(BITENTRY 是 {size,off,id,ver},条目自 +hlen 起)

### 4. x86 实模式段
- 切 0x9203 起 64KB 为 .com,COM 入口 0x10100 = 真实 POST 入口
- 默认分析只有 81 函数 → EnableAgg.java 开 Aggressive Instruction Finder
  + Shared Return Calls → **310 函数,0 失败**
- DumpAll.java 出全量伪代码 + 反汇编;尾部 0x1855b 找到 BIOS 自带的
  PCIR/NPDS/SGIS/NPDE 签名链遍历器(自我解析代码,最好的格式旁证)

### 5. GOP 压缩(最大的弯路,也是最大的胜利)
- 第一反应是"私有格式":穷举 LZSS 各变体(flag 位序/窗口/填充/偏移)全灭;
  写了一半 EDK2 Huffman 解码器移植(e 阶段停);bit-reverse/word-swap
  七种字节变换 + Tiano/Efi 双算法网格(nvdec 的 xform)也全灭
- 转折点:重读 EDK2 BaseCompressionLib,意识到 **EfiCompress 流有 8B 头,
  而 NPDE 恰好把 dsize 挪到表首、csize 放自己头里**——流是标准的,只是无头
- 拼回头部 → EfiDecompress 一次解出;ASUS 流解出与已知 GOP 逐字节相同
- 教训:遇到"解不开的压缩",先问"是不是少了个头",再问"是不是私有格式"

### 6. Falcon/PMU 固件
- 早期判断"签名加密静态不可解"——又是错的:WSL 编出 envytools 后
  envydis -m falcon -V fuc5 直接出 124374 行明文
- 但 ??? unknown 高达 20626 行 → 做 0x100 粒度熵切分:89% 是 HS 密文被
  线性扫描误当指令,~2.6% 才是 envydis 没建模的真指令
- 对照 Ghidra crypt_inst.sinc 把 crypto 指令族全部命名,补 R-R ALU/cmp 缺口
  → 补丁 patches/falcon_envydis_gap.patch,??? 降到 9128
- 标注修正:f5 3c 的高字节是 tabcocmd 操作码不是寄存器

### 7. HS 明文的可行性论证(负结果,但值得留下)
- 读 envytools vm.rst/xfer.rst + nouveau ga102.c + 明文里的 crypto 序列:
  上传路径是密文→XFER_CTRL→crypto 单元边传边解密→IMEM secret 页;
  host 读 secret 页只得 0xdead5ec1;密钥来自硅熔丝
- 结论:软件静态层拿不到 HS 明文——这是 NVIDIA 设计目标
- 唯一理论截口:falcon v4+ DEBUG 口(可能被零售卡熔丝关闭)
- 为此写了 falcon_probe.py(只读扫描/IMEM 验证/debug-test 三阶段)

## 方法论沉淀

1. **先画地图再挖地**。55AA/PCIR/RFRD/NPDE 的层叠关系不弄清,
   后面每一步都会把容器头当数据、把数据当代码。
2. **负结果要记档**。"NvAPI 返回 -9"、"LZSS 穷举全灭"、"PBIT=5 BAD_TABLE"
   这些排除项直接指向了正解。
3. **怀疑工具,先怀疑自己**。三次"工具不行"的判断(Windows REA、私有压缩、
   envydis 缺口)里,两次是自己用法错,一次是工具真缺口(补了补丁)。
4. **多工具交叉验证**。envydis vs Ghidra Falcon 插件 vs 熵分析三方互证,
   才把"unknown"分类账做实。
5. **读开源实现的源码,不只读文档**。EDK2 BaseCompressionLib、
   envytools envy_bios_p_falcon_ucode、nouveau iinit——格式细节都在代码里。

## 如果继续做

- 真卡跑 falcon_probe 三阶段,确认 DEBUG 口死活
- devinit 字节码逐条翻译(对照 nouveau iinit)
- 多 SKU 对比 PSTRAPS,验证 strap-vs-fuse 假设