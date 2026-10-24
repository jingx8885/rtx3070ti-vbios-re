import struct
d=open(r'E:\rea-nvidia-bios\msi_3070ti.rom','rb').read()
csize=struct.unpack_from('<I',d,0x19050)[0]; dsize=struct.unpack_from('<I',d,0x19054)[0]
blob=d[0x19058:0x19058+csize]
# Generic LZSS (EFI/Tiano variant): 1 byte bitmask, then literals(1B) or backrefs(2B)
# try flag bit order MSB/LSB, fill char 0x00/0x20, ring size 4096/8192, len offset 2/3
def lzss(src, out, nbits=12, lbits=4, fill=0x20, msb=False, lenoff=3):
    N=1<<nbits; F=(1<<lbits)+ (18 if lbits==4 else lenoff)
    ring=bytearray([fill]*N); r=N-F
    flags=0; i=0; o=0
    try:
        while o<out and i<len(src):
            if msb: flags=((flags<<1)&0xffff)|( (flags&0x100)>>8 )
            else: flags=(flags>>1)&0xffff
            if flags & 0x100 == 0:
                if i>=len(src): break
                flags=src[i]|0xff00; i+=1
            islit = (flags&1)!=0
            if islit:
                c=src[i]; i+=1
                ring[r]=c; r=(r+1)&(N-1); o+=1
                yield c
            else:
                if i+1>=len(src): break
                c1=src[i]; c2=src[i+1]; i+=2
                pos=c1|((c2&0xf0)<<4) if lbits==4 else c1|((c2&0xe0)<<3)
                ln=(c2&0x0f)+lenoff if lbits==4 else (c2&0x1f)+lenoff
                for k in range(ln):
                    b=ring[(pos+k)&(N-1)]; ring[r]=b; r=(r+1)&(N-1); yield b; o+=1
    except IndexError: return
def try_all():
    for nbits in (12,13):
      for fill in (0x20,0x00):
       for msb in (False,True):
        for off in range(0,0x200):
            g=lzss(d[0x19058+off:0x19058+csize],dsize,nbits,4,fill,msb,3)
            out=bytes(bytearray(g))
            if len(out)>0x800 and (out[:2]==b'MZ' or out.count(b'NVIDIA')+out.count(b'GOP')>0):
                print('HIT nbits%d fill%02x msb%s off+%x -> %d %s'%(nbits,fill,msb,off,len(out),out[:8]))
                open(r'E:\rea-nvidia-bios\extracted\efi_gop_msi.bin','wb').write(out); return True
            if len(out)>0x8000:
                print('partial nbits%d fill%02x msb%s off+%x -> %d head %s'%(nbits,fill,msb,off,len(out),out[:8].hex()))
    return False
try_all()
print('done')
