import struct, os, re, json, math, sys
ROM = sys.argv[1] if len(sys.argv) > 1 else 'msi_3070ti.rom'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'extracted'
os.makedirs(OUT, exist_ok=True)
d = open(ROM,'rb').read(); N=len(d)
def u16(o): return struct.unpack_from('<H',d,o)[0]
def u32(o): return struct.unpack_from('<I',d,o)[0]
def hx(n): return '0x%06x'%n
def ent(b):
    import collections
    c=collections.Counter(b); n=len(b)
    return -sum(v/n*math.log2(v/n) for v in c.values())
report=[]
def pr(*a):
    l=' '.join(str(x) for x in a); report.append(l); print(l)

# ---- BIT @0x93b2 : header 12B, entries 6B: size u16, off u16, id u8, ver u8 ----
pr('=== BIT @0x93b2 ===')
b=0x93b2; base=0x9200
hdrsz=d[b+6]; esz=d[b+7]; nent=d[b+8]
pr('ver=%04x hdrsz=%d esz=%d n=%d cksum=%02x'%(u16(b+4),hdrsz,esz,nent,d[b+9]))
KNOWN={'B':'BIT/Board','C':'Clocks','D':'Display/DP info','E':'?','F':'Falcon/init?','I':'InitScripts','L':'LowPower?','M':'Memory','N':'Null','P':'Perf','S':'Strings','T':'?','U':'?','V':'Voltage?','2':'?'}
bits=[]
for i in range(nent):
    e=b+hdrsz+i*esz
    sz=u16(e); off=u16(e+2); tid=chr(d[e+4]); ver=d[e+5]
    ab=base+off
    ctx=' '.join('%02x'%x for x in d[ab:ab+12])
    asc=''.join(chr(x) if 32<=x<127 else '.' for x in d[ab:ab+16])
    pr('  %s ver%d sz=%4d @%s->%s | %s | %s'%(tid,ver,sz,'0x%04x'%off,hx(ab),ctx,asc))
    bits.append({'id':tid,'ver':ver,'size':sz,'off':off,'abs':ab})
    if sz and sz<0x2000:
        open(os.path.join(OUT,'bit_%s_%04x.bin'%(tid,off)),'wb').write(d[ab:ab+sz])
# ---- NPDE detail ----
pr('\n=== NPDE detail ===')
for o in [0x9390,0x19040,0x2d960,0x32e40,0xc0e40]:
    ver=u16(o+4); hlen=u16(o+6); s512=u32(o+8)&0xffff; flags=u32(o+8)>>16; f2=u32(o+0xc)
    pay=o+hlen
    # look inside payload for BIT/NPDE/PCIR/55aa
    marks=[]
    for m in re.finditer(b'BIT\x00|NPDE|PCIR|\x55\xaa', d[pay:pay+min(0x400,N-pay)]):
        marks.append('%s@+%x'%(m.group().decode('latin1').replace('\x00','.'),m.start()))
    pr('NPDE@%s ver=%04x hlen=%d size512=%d flags=%04x u32@c=%08x pay@%s e=%.2f %s'%(
        hx(o),ver,hlen,s512,flags,f2,hx(pay),ent(d[pay:pay+512]),' '.join(marks)))
# look for sub-magic inside NPDE payloads deeper (up to size512*512)
for o in [0x9390,0x19040,0x2d960,0x32e40,0xc0e40]:
    hlen=u16(o+6); s512=u32(o+8)&0xffff
    end=o+hlen+ (s512*512 if 0<s512<0x200 else 0x1000)
    end=min(end,N)
    seg=d[o+hlen:end]
    for m in re.finditer(b'BIT\x00|NPDE|PCIR|\x55\xaa|PMRT|ITST|INFO|INIT|COND|FRQS|FREQ|VPST|VPS|TABL|DATA',seg):
        pr('   in %s: %s @%s'%(hx(o),m.group().decode('latin1').replace('\0','.'),hx(o+hlen+m.start())))
# ---- JFFS @0xc1000 ----
pr('\n=== JFFS @0xc1000 region 0xc1000..0xc2000 ===')
o=0xc1000
pr('JFFS ver=%d u32@8=%x'%(u16(o+4),u32(o+8)))
# scan for 3-4 ascii tags
p=0xc0f80
while p<0xc2000:
    t=d[p:p+4]
    if all(32<=c<127 for c in t) and t.strip(b' \x00'):
        ln=u32(p+4)
        ctx=d[p:p+24]
        asc=''.join(chr(c) if 32<=c<127 else '.' for c in ctx)
        pr('  tag@%s %r len=%x : %s'%(hx(p),t,ln,asc))
        if 0<ln<0x2000: p=p+8+ln
        else: p+=4
        continue
    p+=4
open(os.path.join(OUT,'parse2_report.txt'),'w').write('\n'.join(report))
