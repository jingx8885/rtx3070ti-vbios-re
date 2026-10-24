# samples/

小型分析输出样例(全部不含受版权保护的固件代码):

- x86-image-strings.txt — x86 镜像内字符串(版本/板号/提示语)
- procedures.json — REA 列出的函数清单(地址+名字,非代码)
- rea-decompile-sample.json — REA decompile 单函数输出样例
- bit_entries.json — BIT 表条目清单(id/ver/size/offset)

完整产物(反编译 C、反汇编、解压后的 GOP 等)因含 NVIDIA 版权代码,不分发;
用 docs/01-05 的流程在自有 ROM 上可完全复现。