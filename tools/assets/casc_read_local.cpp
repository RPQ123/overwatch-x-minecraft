// Bounded read-only extraction from the user's local 24919 archive.
#include "CascLib.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
int main(int argc,char** argv) {
    if(argc!=5&&argc!=6)return 2;
    const bool prefix=argc==6&&std::string(argv[5])=="--prefix";
    if(argc==6&&!prefix)return 2;
    CASC_OPEN_STORAGE_ARGS args{};args.Size=sizeof(args);args.dwLocaleMask=CASC_LOCALE_ENUS;
    HANDLE storage=nullptr,file=nullptr;
    if(!CascOpenStorageEx(argv[1],&args,false,&storage))return 3;
    DWORD features=0;CASC_STORAGE_PRODUCT product{};size_t needed=0;
    if(!CascGetStorageInfo(storage,CascStorageFeatures,&features,sizeof(features),&needed)
       ||(features&CASC_FEATURE_ONLINE)||!CascGetStorageInfo(storage,CascStorageProduct,&product,sizeof(product),&needed)
       ||product.BuildNumber!=24919){CascCloseStorage(storage);return 4;}
    if(!CascOpenFile(storage,argv[2],CASC_LOCALE_ENUS,CASC_OPEN_BY_NAME,&file)){CascCloseStorage(storage);return 5;}
    DWORD high=0,size=CascGetFileSize(file,&high),count=0;
    unsigned long limit=std::stoul(argv[4]);
    if(high||size==INVALID_FILE_SIZE||(!prefix&&size>limit)||size>256*1024*1024||!limit||limit>16*1024*1024){CascCloseFile(file);CascCloseStorage(storage);return 6;}
    // Optional bounded prefix inspection of large maps. The archive remains
    // read-only; never allocate or extract the unrequested remainder.
    if(prefix&&size>limit)size=static_cast<DWORD>(limit);
    std::vector<char> bytes(size);
    bool ok=CascReadFile(file,bytes.data(),size,&count)&&count==size;
    CascCloseFile(file);CascCloseStorage(storage);
    if(!ok)return 7;
    std::filesystem::path output(argv[3]);
    if(std::filesystem::exists(output))return 8;
    std::ofstream out(output,std::ios::binary);out.write(bytes.data(),size);
    if(!out)return 9;
    std::cout<<size<<" local bytes read\n";
}
