
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Decompress.h"
static unsigned char rev8(unsigned char b){
  b=(b>>4)|(b<<4); b=((b&0xCC)>>2)|((b&0x33)<<2); b=((b&0xAA)>>1)|((b&0x55)<<1); return b;
}
static void xform(unsigned char*b,long n,int mode){
  long i;
  switch(mode){
   case 1: for(i=0;i<n;i++)b[i]=rev8(b[i]);break;
   case 2: for(i=0;i+1<n;i+=2){unsigned char t=b[i];b[i]=b[i+1];b[i+1]=t;}break;
   case 3: for(i=0;i+3<n;i+=4){unsigned char t0=b[i],t1=b[i+1];b[i]=b[i+3];b[i+1]=b[i+2];b[i+2]=t1;b[i+3]=t0;}break;
   case 4: for(i=0;i+1<n;i+=2){unsigned char t=rev8(b[i]);b[i]=rev8(b[i+1]);b[i+1]=t;}break;
   case 5: for(i=0;i+3<n;i+=4){unsigned char t0=rev8(b[i]),t1=rev8(b[i+1]);b[i]=rev8(b[i+3]);b[i+1]=rev8(b[i+2]);b[i+2]=t1;b[i+3]=t0;}break;
   case 6: for(i=0;i+1<n;i+=2){unsigned char t=b[i];b[i]=b[i+1];b[i+1]=t;} for(i=0;i<n;i++)b[i]=rev8(b[i]);break;
   default:break;
  }
}
int main(int argc,char**argv){
  if(argc<6)return 1;
  FILE*f=fopen(argv[1],"rb");if(!f){perror("open");return 1;}
  fseek(f,0,SEEK_END);long n=ftell(f);fseek(f,0,SEEK_SET);
  unsigned char*raw=malloc(n);if(fread(raw,1,n,f)!=(size_t)n)return 2;fclose(f);
  unsigned csize=strtoul(argv[2],0,0), dsize=strtoul(argv[3],0,0);
  char algo=argv[4][0];
  long s0=argc>6?strtol(argv[6],0,0):0, s1=argc>7?strtol(argv[7],0,0):s0;
  unsigned char*hdr=malloc(n+8);
  char algs[3]; int na=0;
  if(algo=='b'){algs[na++]='t';algs[na++]='e';} else algs[na++]=algo;
  for(long off=s0;off<=s1;off++)
   for(int ai=0;ai<na;ai++)
    for(int mode=0;mode<=6;mode++){
      hdr[0]=csize&0xff;hdr[1]=(csize>>8)&0xff;hdr[2]=(csize>>16)&0xff;hdr[3]=(csize>>24)&0xff;
      hdr[4]=dsize&0xff;hdr[5]=(dsize>>8)&0xff;hdr[6]=(dsize>>16)&0xff;hdr[7]=(dsize>>24)&0xff;
      memcpy(hdr+8,raw+off,n-off);
      xform(hdr+8,n-off,mode);
      size_t ds=dsize, scr=0;
      EFI_STATUS gi=TianoGetInfo(hdr,n-off+8,&ds,&scr);
      if(gi!=0){printf("off=%ld alg=%c mode=%d getinfo st=%d\n",off,algs[ai],mode,(int)gi);continue;}
      unsigned char*out=calloc(1,ds); void*sc=calloc(1,scr);
      EFI_STATUS st = (algs[ai]=='e') ? EfiDecompress(hdr,n-off+8,out,ds,sc,scr)
                                    : TianoDecompress(hdr,n-off+8,out,ds,sc,scr);
      long nz=0; for(long i=0;i<ds;i++) if(out[i])nz=i+1;
      printf("off=%ld alg=%c mode=%d st=%d nz=%ld head=%02x%02x%02x%02x\n",off,algs[ai],mode,(int)st,nz,out[0],out[1],out[2],out[3]);
      if(st==0 || nz>64){
        char path[512];sprintf(path,"%s_%c_off%lx_m%d.bin",argv[5],algs[ai],off,mode);
        FILE*o=fopen(path,"wb");fwrite(out,1,ds,o);fclose(o);
        printf("WROTE %s\n",path);
      }
      free(out);free(sc);
    }
  return 0;
}
