# tools/gop-decompress

破解 "NVIDIA 私有 GOP 压缩" 的三件套。原理见 docs/04-gop-eficompress.md。

| 工具 | 用途 | 用法 |
|---|---|---|
| nvdec  | 穷举扫描器(偏移 x 位变换 x efi/tiano 网格)| nvdec stream csize dsize e|t|b out [s0 s1] |
| nvdump | 直读解码器内部,参数化 PBIT,跳过文件头 | nvdump in.bin outcap [pbit] [skip] |
| efic   | 压缩器(重打包/验证用)| efic in.bin out.comp [e|t] |
| lzss_bruteforce.py | 历史:裸 LZSS 变体穷举(全灭,留档)| — |

依赖:EDK2 BaseCompressionLib(EfiCompress.c / TianoCompress.c / Decompress.c /
Compress.h / Decompress.h + BaseTypes.h / ProcessorBind.h),未随仓库分发;
可用 chipsec 里的 EfiCompressor(Python)替代,见 docs/08。