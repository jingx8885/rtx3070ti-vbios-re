# tools/falcon-probe

GA10x Falcon DEBUG 口 / secret-IMEM 活性探测。详见 RUNBOOK.md 与 docs/06-mmio-probe.md。

    # 裸机 Linux(live USB)+ root,无依赖
    python3 falcon_probe.py                        # 阶段A:只读扫描+pstraps+fuse
    python3 falcon_probe.py --engine 0xXXXXXX --imem 0x0,0x400,...   # 阶段B:IMEM 读回
    python3 falcon_probe.py --engine 0xXXXXXX --debug-test           # 阶段C:DEBUG 口活性

阶段 A/B 只读;阶段 C 会向 falcon 写 BREAK/CONTINUE 寄存器——裸卡低风险,
有驱动的系统勿跑。