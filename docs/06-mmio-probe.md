# 06 — Falcon DEBUG 口 / secret-IMEM 活性探测

工具:tools/falcon-probe/falcon_probe.py(纯 stdlib,无需安装)。
完整 runbook 同目录 RUNBOOK.md,此处为摘要 + 设计依据。

## 环境:Linux live USB(唯一现实路径)

- WSL2 看不到 PCIe MMIO;Windows 下 BAR0 被 NVIDIA 驱动独占。
- Ubuntu live U盘 → "Try Ubuntu" → 拷入 falcon_probe.py。
- 建议启动参数:在 linux 行尾加 iomem=relaxed nouveau.modeset=0
  (前者放开 BAR0 mmap,后者让 nouveau 不碰卡,裸卡状态最安全)。

## 阶段 A:只读扫描(零风险)

    sudo -i
    python3 falcon_probe.py

打印每个 engine 的 CAPS2/SEC_MODE/UC_STATUS + [pstraps] 13 个寄存器
(@0x101000)+ [fuse] 64 dword(@0x021100)。

判定:
- SEC_MODE=HS/LS 的引擎 = 跑过签名微码的候选目标。
- pstraps:若 debug-disable 是 strap 位,多卡对比可定位;bit31 可 MMIO 覆写。
- fuse 全 0 / 全 0xbad0acxx = 该代 fuse 窗口被锁(也是有效信息)。
- 参照:GA107M 实测(pipinovi4/ga107m-bar1-bad0ac)对被拦截 MMIO 读返回
  0xBAD0ACxx 毒化值 + 低字节计数器——出现这类值 = 访问被硬件拦截,不是读错。

## 阶段 B:IMEM 读回验证(仍只读)

    python3 falcon_probe.py --engine 0xXXXXXX --imem 0x0,0x400,0x800,0x1000,0xa600,0x1c00

- 低位地址读出真实微码 = IMEM 窗口活着,可与 envydis 输出比对确认引擎身份。
- 某些页返回 dead5ec1 = secret 页确认存在,硬件锁生效。
- 全部 dead5ec1 = ucode 已不驻留(见阶段 D)。

## 阶段 C:DEBUG 口活性(核心,毫秒级风险)

    python3 falcon_probe.py --engine 0xXXXXXX --debug-test

做三件事:DEBUG_CMD BREAK → REG_READ r0..r15 → CONTINUE_FROM_PC。

| 结果 | 含义 |
|---|---|
| port ALIVE + 寄存器值正常 | DEBUG 口没被熔断:可进入单步追踪/gadget 外泄路线 |
| DONE 不置位 / 全 dead5ec1 / ERROR 位 | 零售卡熔丝已关,死路实锤 |

风险:BREAK 期间 falcon 停几 ms。**裸卡(无驱动)下无依赖,可接受;
装了 nvidia 驱动的系统别跑 --debug-test**(PMU 停顿可能触发 RM 恢复)。

## 阶段 D(仅当 B 显示 IMEM 空)

VBIOS ucode 是 POST 时由 x86 BIOS/UEFI 上传的。裸卡 IMEM 空时:
先确认是否 POST 没传(CSM 关+纯 UEFI 时 devinit 可能走不同路径);
备选是在带驱动的系统上驱动加载瞬间重传,或自写上传器复现 XFER_CTRL secret 路径。

## 寄存器依据

脚本内的偏移表来自 rnndb falcon.xml(GF119+ 简单寻址):
CAPS2@0x12c / IMEMC@0x180 / IMEMD@0x184 / DMEMC@0x1c0 / DEBUG_CMD@0x200 /
DEBUG_ADDR@0x204 / DEBUG_WR@0x208 / DEBUG_RD@0x20c / SEC_MODE@0x240。