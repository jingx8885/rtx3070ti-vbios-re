#!/usr/bin/env python3
# falcon_probe.py -- GA10x Falcon debug-port / secret-IMEM liveness probe
# Run on BARE METAL Linux (live USB is fine) as root.
# No dependencies beyond stdlib. Default mode is READ-ONLY.
import os, sys, glob, struct, argparse, mmap, time

NVIDIA = "0x10de"
# candidate MMIO window scan range inside BAR0 (GA10x BAR0 is 16MB)
SCAN_START, SCAN_END, SCAN_STRIDE = 0x0, 0x400000, 0x1000

# falcon host-MMIO register offsets (per rnndb falcon.xml, GF119+ simple addressing)
REG = {
    "CAPS2":      0x12c,
    "UC_STATUS":  0x128,   # v3 only, may be junk on v4
    "BREAK0":     0x098,
    "BREAK1":     0x09c,
    "IMEMC":      0x180,   # CODE_INDEX candidate (v4)
    "IMEMD":      0x184,   # CODE data window candidate
    "DMEMC":      0x1c0,   # DATA_INDEX[0]
    "DMEMD":      0x1c4,   # DATA[0]
    "DEBUG_CMD":  0x200,
    "DEBUG_ADDR": 0x204,
    "DEBUG_WR":   0x208,
    "DEBUG_RD":   0x20c,
    "SEC_MODE":   0x240,
    "CPUCTL":     0x100,
    "PC_v3":      0xff0,   # v0/v3 only
    "UPLOAD":     0xff4,   # v0/v3 only
}

# DEBUG_CMD.CMD values
DBG = dict(BREAK=0x0, CONT_PC=0x1, CONT_ADDR=0x2, STEP_PC=0x5,
           STEP_ADDR=0x6, SET_BM=0x7, REG_RD=0x8, REG_WR=0x9,
           DATA_RD=0xa, DATA_WR=0xb, IO_RD=0xc, IO_WR=0xd, STATUS=0xe)
SEC = {0: "NS", 1: "LS", 2: "HS"}

def find_gpus():
    devs = []
    for d in glob.glob("/sys/bus/pci/devices/*"):
        try:
            ven = open(d + "/vendor").read().strip()
            cls = open(d + "/class").read().strip()
        except OSError:
            continue
        if ven == NVIDIA and cls.startswith("0x03"):
            devs.append(d)
    return devs

def bar0_map(devdir):
    # resource0 = BAR0. Need root; iomem may need to be relaxed.
    r = os.path.join(devdir, "resource0")
    size = os.path.getsize(r)
    fd = os.open(r, os.O_RDWR | os.O_SYNC)
    mm = mmap.mmap(fd, size, mmap.MAP_SHARED,
                   mmap.PROT_READ | mmap.PROT_WRITE)
    return mm, size

rd = lambda mm, a: struct.unpack_from("<I", mm, a)[0]
wr = lambda mm, a, v: struct.pack_into("<I", mm, a, v)

def caps2_sane(v):
    ver = v & 0xf
    crypt = (v >> 4) & 3
    return ver in (3, 4, 5, 6) and crypt == 3

def scan_engines(mm, bar_sz):
    hits = []
    end = min(SCAN_END, bar_sz - 0x1000)
    for base in range(SCAN_START, end, SCAN_STRIDE):
        try:
            v = rd(mm, base + REG["CAPS2"])
        except Exception:
            continue
        if caps2_sane(v):
            hits.append(base)
    return hits

def dump_engine(mm, base, tag):
    print("\n=== engine @0x%06x (%s) ===" % (base, tag))
    for name in ("CAPS2", "UC_STATUS", "SEC_MODE", "CPUCTL", "IMEMC"):
        try:
            v = rd(mm, base + REG[name])
            extra = ""
            if name == "SEC_MODE":
                extra = "  -> %s" % SEC.get(v & 3, "?")
            print("  %-10s = %08x%s" % (name, v, extra))
        except Exception as e:
            print("  %-10s = <err %s>" % (name, e))

def imem_peek(mm, base, phys_addrs):
    # Try CODE_INDEX/IMEMD style: write index with READ_AUTOINCR (bit25),
    # then read IMEMD. phys addr is a byte address in code space.
    res = []
    for pa in phys_addrs:
        try:
            wr(mm, base + REG["IMEMC"], pa | (1 << 25))
            vals = [rd(mm, base + REG["IMEMD"]) for _ in range(4)]
        except Exception as e:
            vals = ["err:%s" % e]
        res.append((pa, vals))
    return res

def dbg_cmd(mm, base, cmd, addr=None, wdata=None, idx=0, timeout=0.5):
    if addr is not None:
        wr(mm, base + REG["DEBUG_ADDR"], addr)
    if wdata is not None:
        wr(mm, base + REG["DEBUG_WR"], wdata)
    wr(mm, base + REG["DEBUG_CMD"], cmd | (idx << 8))
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = rd(mm, base + REG["DEBUG_CMD"])
        if v & 0x8000:   # DONE
            err = bool(v & 0x4000)
            data = rd(mm, base + REG["DEBUG_RD"])
            return True, err, data
        time.sleep(0.001)
    return False, None, None

def debug_liveness(mm, base):
    print("  [dbg] DEBUG_CMD reset state = %08x" % rd(mm, base + REG["DEBUG_CMD"]))
    ok, err, data = dbg_cmd(mm, base, DBG["BREAK"])
    print("  [dbg] BREAK: done=%s err=%s rd=%s" % (ok, err,
          ("%08x" % data) if data is not None else None))
    if not ok:
        return False
    # read $pc (STATUS_READ idx 0 is a guess; REG_READ idx 0 = r0)
    for idx in range(0x10):
        ok2, err2, d2 = dbg_cmd(mm, base, DBG["REG_RD"], idx=idx)
        if ok2:
            print("  [dbg] REG[%02x] = %08x (err=%s)" % (idx, d2, err2))
    # resume immediately
    ok3, err3, _ = dbg_cmd(mm, base, DBG["CONT_PC"])
    print("  [dbg] CONTINUE_FROM_PC: done=%s err=%s" % (ok3, err3))
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--debug-test", action="store_true",
                    help="issue DEBUG_CMD BREAK/CONTINUE (tiny hang risk)")
    ap.add_argument("--imem", default="",
                    help="comma list of phys code addrs to peek, e.g. 0x0,0xa600")
    ap.add_argument("--engine", default="",
                    help="only probe engine at this BAR0 offset (hex)")
    args = ap.parse_args()

    if os.geteuid() != 0:
        sys.exit("need root")
    gpus = find_gpus()
    if not gpus:
        sys.exit("no NVIDIA VGA/3D device found")
    for devdir in gpus:
        bdf = os.path.basename(devdir)
        try:
            bound = os.path.basename(os.readlink(devdir + "/driver"))
        except OSError:
            bound = "none"
        dev = open(devdir + "/device").read().strip()
        print("\n##### %s device=%s driver=%s #####" % (bdf, dev, bound))
        if bound in ("nvidia", "nouveau"):
            print("  WARNING: driver bound. Prefer running with no GPU driver "
                  "(live USB / blacklist) to avoid disturbing a live RM.")
        try:
            mm, sz = bar0_map(devdir)
        except OSError as e:
            print("  BAR0 map failed: %s (try iomem=relaxed kernel cmdline)" % e)
            continue
        print("  BAR0 size = %#x" % sz)

        # PSTRAPS readout (BAR0+0x101000, per pstraps.rst; GF119+ has 3 sets)
        _ps = [(0x00,"STRAPS0_PRI"),(0x04,"STRAPS0_SEL"),(0x08,"STRAPS0_SEC"),
               (0x0c,"STRAPS1_PRI"),(0x10,"STRAPS1_SEL"),(0x14,"STRAPS1_SEC"),
               (0x34,"STRAPS2_PRI"),(0x38,"STRAPS2_SEL"),(0x3c,"STRAPS2_SEC"),
               (0x28,"UNK28"),(0x2c,"UNK2C"),(0x30,"UNK30"),(0x40,"UNK40")]
        # FUSE block readout (BAR0+0x021100, per nouveau gm107_fuse_read)
        # GSP cards: RM hides it from driver but host MMIO still works on bare card
        print('  [fuse] block @0x021100 (256B):')
        for off in range(0, 0x100, 4):
            try:
                v = rd(mm, 0x021100 + off)
                print('    fuse[%03x] = %08x' % (off, v))
            except Exception as e:
                print('    fuse[%03x] err %s' % (off, e))
        for off, name in _ps:
            try:
                print("  [pstraps] %-12s = %08x" % (name, rd(mm, 0x101000+off)))
            except Exception as e:
                print("  [pstraps] %-12s err %s" % (name, e))
        engines = [int(args.engine, 16)] if args.engine else scan_engines(mm, sz)
        print("  falcon engines found: %s" %
              ([hex(e) for e in engines] or "NONE"))
        for i, base in enumerate(engines):
            dump_engine(mm, base, "eng%d" % i)
            if args.imem:
                addrs = [int(x, 16) for x in args.imem.split(",")]
                for pa, vals in imem_peek(mm, base, addrs):
                    print("  [imem] phys %#06x -> %s" %
                          (pa, " ".join(("%08x" % v) if isinstance(v, int)
                                         else str(v) for v in vals)))
            if args.debug_test:
                alive = debug_liveness(mm, base)
                print("  [dbg] port %s" % ("ALIVE" if alive else "dead/blocked"))

if __name__ == "__main__":
    main()
