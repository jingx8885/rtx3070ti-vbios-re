
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "Compress.h"
int main(int argc,char**argv){
  if(argc<3){fprintf(stderr,"use: efic in.bin out.comp [e|t]\n");return 1;}
  FILE*f=fopen(argv[1],"rb");if(!f){perror("open");return 1;}
  fseek(f,0,SEEK_END);long n=ftell(f);fseek(f,0,SEEK_SET);
  unsigned char*in=malloc(n);if(fread(in,1,n,f)!=(size_t)n)return 2;fclose(f);
  size_t cap=n*2+64;
  unsigned char*out=malloc(cap);
  size_t ds=cap;
  EFI_STATUS st;
  if(argc>3 && argv[3][0]=='t') st=TianoCompress(in,n,out,&ds);
  else st=EfiCompress(in,n,out,&ds);
  fprintf(stderr,"st=%d ds=%zu\n",(int)st,ds);
  if(st==0){FILE*o=fopen(argv[2],"wb");fwrite(out,1,ds,o);fclose(o);}
  return st!=0;
}
