# GA10x Falcon DEBUG 口活性测试 —— 实测手册

工具: probe/falcon_probe.py (纯 stdlib, 无需安装)

## 环境: Linux live USB (唯一现实路径)

WSL2 看不到 PCIe MMIO, Windows 下 BAR0 被 NVIDIA 驱动独占。
做法: Ubuntu live U盘 -> "Try Ubuntu" -> 拷入 falcon_probe.py。

可选但建议: 启动菜单按 e, 在 linux 行尾加 `iomem=relaxed nouveau.modeset=0`
(前者放开 BAR0 mmap, 后者让 nouveau 不碰卡, 完全裸卡状态最安全)。

## 阶段 A: 只读扫描 (零风险)

    sudo -i
    python3 falcon_probe.py

预期输出: 找到若干 "engine @0xXXXXXX", 每个打印 CAPS2/SEC_MODE/UC_STATUS。
关键看:
- SEC_MODE -> HS 或 LS 的引擎 = 跑过签名微码的 (候选目标)
- SEC_MODE 全 0/NS 的 = 非安全引擎
- 一个都找不到 = scan 范围不够或 GA10x 窗口布局不同, 回报输出

若 BAR0 map failed: 重启 live USB, 内核加 iomem=relaxed。

## 阶段 B: IMEM 读回验证 (仍只读)

    python3 falcon_probe.py --engine 0xXXXXXX --imem 0x0,0x400,0x800,0x1000,0xa600,0x1c00

(0xXXXXXX = 阶段 A 找到的 SEC_MODE=HS 引擎)

判定:
- 低位地址读出真实微码(非 0, 非 ffffffff) = IMEM 窗口活着,
  可和我们的 out/falcon_fuc5_disasm_v2.txt 前几条指令比对确认引擎身份
- 某些物理页返回 dead5ec1 = secret 页确认存在, 硬件锁生效
- 全部 dead5ec1 = ucode 已不驻留 (需重传, 阶段 D)

## 阶段 C: DEBUG 口活性 (核心问题, 毫秒级风险)

    python3 falcon_probe.py --engine 0xXXXXXX --debug-test

做三件事: DEBUG_CMD BREAK -> REG_READ r0..r15 -> CONTINUE_FROM_PC。
- "port ALIVE" + 寄存器值非全 0/dead5ec1 = 中大奖:
  接下来可做 SINGLE_STEP 追踪 + gadget 外泄, 整套 HS 明文可拿
- DONE 永不置位 / 全 dead5ec1 / ERROR 位 = 零售卡熔断关闭, 死路实锤

风险: BREAK 期间 falcon 停 ~几 ms。裸卡(无驱动)下无任何依赖。
装了 nvidia 驱动的系统别跑 --debug-test (PMU 停顿可能触发 RM 恢复)。

## 阶段 D (仅当 B 显示 IMEM 空)

VBIOS ucode 是 POST 时由 x86 BIOS/UEFI 传上去的。若裸卡 IMEM 已空:
- 先确认是否 POST 根本没传 (CSM 关+纯 UEFI 时 devinit 可能走不同路径)
- 备选: 在带 NVIDIA 驱动的系统上, 驱动加载瞬间会重传 ucode;
  或我们后续写个上传器复现 XFER_CTRL secret 路径

## 回报格式
把阶段 A/B/C 完整输出贴回来即可, 我来判定下一步。

## 更新: 阶段A 现在额外输出两组数据

1. [pstraps] 13 个寄存器 @BAR0+0x101000 (pstraps.rst: primary/select/secondary x3组+UNK)
   - 用途: 若 GA102 的 falcon debug-disable 是 strap 位而非 fuse,
     对比其它 SKU/卡的 strap 差可定位该位; PSTRAPS bit31 可 MMIO 覆写
2. [fuse] 64 个 dword @BAR0+0x021100 (nouveau gm107_fuse_read 证实 host 可读;
   RM 在 GSP 卡上主动不读 = 硬件上一直是裸读的)
   - 用途: debug-disable / security fuse 位大概率在这; 全部贴回我来分析
   - 若全 0 / 全 0xbad0acxx = 此代 fuse 窗口被锁 (也是有效信息)

参照: GA107M 实测 (github pipinovi4/ga107m-bar1-bad0ac) 对被拦截的
MMIO 读返回 0xBAD0ACxx 毒化值 + 低字节全局计数器 —— 与 0xdead5ec1 同族。
探针输出里出现这类值 = 访问被硬件拦截的标志, 不是读数错误。
