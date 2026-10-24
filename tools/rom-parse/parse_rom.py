import struct, os, sys, json
ROM = sys.argv[1] if len(sys.argv) > 1 else 'msi_3070ti.rom'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'extracted'
os.makedirs(OUT, exist_ok=True)
d = open(ROM,'rb').read()
N = len(d)
def u16(o): return struct.unpack_from('<H',d,o)[0]
def u32(o): return struct.unpack_from('<I',d,o)[0]
def hx(n,w=6): return ('0x%0'+str(w)+'x')%n
def dump(o,n=16):
    return ' '.join('%02x'%b for b in d[o:o+n])
report=[]
def pr(*a):
    line=' '.join(str(x) for x in a); report.append(line); print(line)

pr('# MSI RTX 3070 Ti VBIOS full map  size=%d'%N)
# ---------- PCI ROM images ----------
pr('\n## 55AA PCI ROM images')
imgs=[]
import re
for m in re.finditer(b'\x55\xaa', d):
    o=m.start()
    if o+0x20>=N: continue
    size512=d[o+2]
    imgsize=size512*512
    # find PCIR within first 0x200
    pcir=None
    for j in range(o+4, min(o+0x400, o+imgsize, N-4)):
        if d[j:j+4]==b'PCIR': pcir=j; break
    info={'off':o,'size512':size512,'bytes':imgsize}
    if pcir:
        vend=u16(pcir+4); dev=u16(pcir+6); pcilen=u16(pcir+0x0a); typ=d[pcir+0x14]; ind=d[pcir+0x15]
        codetype = {0:'x86 PC/AT',1:'OpenFirmware',2:'HP-PA',3:'EFI'}.get(typ,'?%d'%typ)
        info.update(pcir=pcir, vend='%04x'%vend, dev='%04x'%dev, type=typ, typename=codetype,
                    last=bool(ind&0x80), imagenum=ind&0x7f, pcilen=pcilen)
        pr('%s  size512=%d (%d B)  PCIR@%s dev=%s type=%s %s%s'%(
            hx(o), size512, imgsize, hx(pcir-o), '%04x'%dev, codetype,
            'LAST ' if ind&0x80 else '', 'efi' if typ==3 else ''))
        if typ==3:
            # EFI image header per PCI FW spec
            imgver=u16(pcir+0x10); init=u16(pcir+0x12)
            ehdr=o+0x40
            sig=u32(ehdr)
            pr('   EFI: ImgVersion=%d EfiSubsystem? pcir+0x12=%04x  sig@%s=%08x'%(imgver,init,hx(ehdr),sig))
            # compression header (NVIDIA): @+0x50: csize u32, dsize u32, then data
            csize=u32(o+0x50); dsize=u32(o+0x54)
            pr('   NVIDIA comp hdr @+0x50: csize=%x dsize=%x data@%s'%(csize,dsize,hx(o+0x58)))
            info.update(csize=csize,dsize=dsize)
    else:
        # no PCIR -> maybe Falcon/data image with 55aa prefix
        pr('%s  size512=%d  NO-PCIR (data/embedded?) head: %s'%(hx(o),size512,dump(o+4,12)))
    imgs.append(info)

# ---------- RFRD ----------
pr('\n## RFRD directory @0x5000')
o=0x5000
ver=u16(o+4); hsz=u16(o+6)
pr('RFRD ver=%d hdrsize=%d'%(ver,hsz))
entries=[]
for i in range(8):
    e=o+8+i*4
    v=u32(e)
    entries.append(v)
    pr('  entry[%d] @%s = %08x'%(i,hx(e),v))

# ---------- BIT ----------
pr('\n## BIT table @0x93b2 (relative to x86 image base 0x9200)')
b=0x93b2; base=0x9200
assert d[b:b+4]==b'BIT\x00'
bitver=u16(b+4); hsize=d[b+6]; token_sz=d[b+7]; ntok=d[b+8]; cksum=d[b+9]; sig16=u16(b+10)
pr('BIT ver=%04x hdrsize=%d entrysize=%d entries=%d cksum=%02x u16@+10=%04x'%(bitver,hsize,token_sz,ntok,cksum,sig16))
ids={'B':'BIOS info','C':'?(mode/clock?)','D':'Display','F':'Falcon?','I':'Init scripts','M':'Memory','N':'NULL/term','P':'Perf/Power','S':'Strings','T':'?','U':'?','V':'?','2':'?'}
bitentries=[]
for i in range(ntok):
    e=b+hsize+i*token_sz
    tid=chr(d[e]) if 32<=d[e]<127 else '%02x'%d[e]
    ver=d[e+1]; sz=u16(e+2); off=u16(e+4)
    abs_off=base+off
    bitentries.append((tid,ver,sz,off,abs_off))
    pr('  [%2d] id=%s ver=%d size=%-4d off=%s -> %s  %s'%(i,tid,ver,sz,hx(off),hx(abs_off),ids.get(tid,'')))
open(os.path.join(OUT,'bit_entries.json'),'w').write(json.dumps(
   [{'id':t,'ver':v,'size':s,'rel':o,'abs':a} for t,v,s,o,a in bitentries],indent=1))

# ---------- NPDE blocks ----------
pr('\n## NPDE blocks')
npdes=[0x9390,0x185b4,0x19040,0x2d960,0x32e40,0x3a682,0xc0e40]
for o in npdes:
    ver=u16(o+4); hlen=u16(o+6); f8=u32(o+8); fc=u32(o+0xc)
    pr('NPDE@%s ver=%04x hdrlen=%d u32@8=%08x u32@c=%08x'%(hx(o),ver,hlen,f8,fc))
    pl=d[o+hlen:o+hlen+32]
    pr('   payload@%s: %s | %s'%(hx(o+hlen), ' '.join('%02x'%x for x in pl),
       ''.join(chr(x) if 32<=x<127 else '.' for x in pl)))

# ---------- JFFS ----------
pr('\n## JFFS @0xc1000')
o=0xc1000
ver=u16(o+4); f1=u32(o+8)
pr('JFFS ver=%d u32@8=%08x'% (ver,f1))
# scan for tag records 0xc1000..0xc2000: 4 ascii + plausible len
import string
p=o+0x80
found=[]
while p < 0xc8000:
    tag=d[p:p+4]
    if all(32<=c<127 for c in tag) and tag.strip(b'\x00 '):
        l=u32(p+4)
        if l and l<0x40000 and p+8+l<=N:
            s=d[p+8:p+8+min(l,40)]
            asc=''.join(chr(c) if 32<=c<127 else '.' for c in s)
            pr('  tag %s @%s len=%d : %s'%(tag.decode(),hx(p),l,asc))
            found.append((p,tag.decode(),l))
            p=p+8+l
            while p%4: p+=1
            continue
    p+=4
# ---------- version strings ----------
pr('\n## strings of interest')
for m in re.finditer(rb'[\x20-\x7e]{6,}', d[0x9200:0x19000]):
    t=m.group().decode()
    if any(k in t for k in ['Version','MSI','VGA','BIOS','Build','Copyright','NVIDIA']):
        pr('  x86@%s: %s'%(hx(0x9200+m.start()), t))
open(os.path.join(OUT,'rom_map_report.txt'),'w').write('\n'.join(report))
