
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Decompress.h"
#include "Decompress.c"
int main(int argc,char**argv){
  // use: nvdump in.bin outcap [pbit] [skip]
  if(argc<3){fprintf(stderr,"use: nvdump in.bin outcap [pbit] [skip]\n");return 1;}
  FILE*f=fopen(argv[1],"rb");if(!f){perror("open");return 1;}
  fseek(f,0,SEEK_END);long n=ftell(f);fseek(f,0,SEEK_SET);
  unsigned char*raw=malloc(n);if(fread(raw,1,n,f)!=(size_t)n)return 2;fclose(f);
  long outcap=strtol(argv[2],0,0);
  int pbit=argc>3?atoi(argv[3]):4;
  long skip=argc>4?strtol(argv[4],0,0):0;
  SCRATCH_DATA*Sd=calloc(1,sizeof(SCRATCH_DATA));
  unsigned char*out=calloc(1,outcap);
  mPbit=pbit;
  Sd->mSrcBase=raw+skip; Sd->mCompSize=(UINT32)(n-skip);
  Sd->mDstBase=out; Sd->mOrigSize=(UINT32)outcap;
  FillBuf(Sd,BITBUFSIZ);
  Decode(Sd);
  fprintf(stderr,"pbit=%d skip=%ld InBuf=%u OutBuf=%u bad=%d head=%02x%02x%02x%02x\n",
    pbit,skip,Sd->mInBuf,Sd->mOutBuf,Sd->mBadTableFlag,out[0],out[1],out[2],out[3]);
  if(Sd->mOutBuf>0){char p[512];snprintf(p,512,"%s.p%d.s%ld.out",argv[1],pbit,skip);FILE*o=fopen(p,"wb");fwrite(out,1,Sd->mOutBuf<outcap?Sd->mOutBuf:outcap,o);fclose(o);fprintf(stderr,"wrote %s\n",p);}
  return 0;
}
