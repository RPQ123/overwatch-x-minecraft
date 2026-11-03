// Read-only, local-only reconnaissance of the user's early beta archive.
// Link against the upstream CascLib 3.0 library built in ignored research storage.
#include "CascLib.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <map>
#include <set>
#include <vector>
#include <sstream>

std::string quoted(const std::string& value) {
    std::ostringstream out;out<<'"';for(unsigned char c:value) {
        if(c=='"'||c=='\\') out<<'\\'<<c;
        else if(c<32||c>126) out<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;
        else out<<c;
    }out<<'"';return out.str();
}
int main(int argc,char** argv) {
    if(argc!=3) {std::cerr<<"Usage: casc-inventory <owned-beta-folder> <private-output-directory>\n";return 2;}
    auto root=std::filesystem::absolute(argv[1]),output=std::filesystem::absolute(argv[2]);
    if(!std::filesystem::is_regular_file(root/".build.info")) {std::cerr<<"Local build info missing\n";return 2;}
    // No online storage, force-download or missing-encryption-key overrides.
    CASC_OPEN_STORAGE_ARGS args{};args.Size=sizeof(args);args.dwLocaleMask=CASC_LOCALE_ENUS;args.dwFlags=0;
    HANDLE storage=nullptr;if(!CascOpenStorageEx(root.string().c_str(),&args,false,&storage)) {std::cerr<<"Local archive open failed: "<<GetLastError()<<'\n';return 1;}
    DWORD features=0;CASC_STORAGE_PRODUCT product{};size_t needed=0;
    if(!CascGetStorageInfo(storage,CascStorageFeatures,&features,sizeof(features),&needed)||(features&CASC_FEATURE_ONLINE)
       ||!CascGetStorageInfo(storage,CascStorageProduct,&product,sizeof(product),&needed)||product.BuildNumber!=24919) {
        std::cerr<<"Archive identity/strict local mode verification failed\n";CascCloseStorage(storage);return 1;
    }
    std::filesystem::create_directories(output);std::ofstream inventory(output/"assets.tsv");
    inventory<<"name\tsize\tavailable\n";
    CASC_FIND_DATA data{};HANDLE search=CascFindFirstFile(storage,"*",&data,nullptr);
    if(search==INVALID_HANDLE_VALUE) {std::cerr<<"Local enumeration failed: "<<GetLastError()<<'\n';CascCloseStorage(storage);return 1;}
    std::map<std::string,uint64_t> counts,sampled;
    std::set<std::string> wanted{".00C",".006",".004",".007",".050",".03F",".05A",".075",".003",".01B"};
    struct Sample {std::string name,type,file,header;uint64_t size;DWORD read,error;};std::vector<Sample> samples;
    uint64_t total=0,available=0;
    do {
        std::string name=data.szFileName,type=std::filesystem::path(name).extension().string();
        for(char& c:type) c=std::toupper(static_cast<unsigned char>(c));
        ++total;available+=data.bFileAvailable;++counts[type];inventory<<name<<'\t'<<data.FileSize<<'\t'<<data.bFileAvailable<<'\n';
        if(wanted.count(type)&&sampled[type]<2&&data.bFileAvailable&&data.FileSize&&data.FileSize<=16*1024*1024) {
            ++sampled[type];Sample s{name,type,"sample-"+std::to_string(samples.size())+type,"",data.FileSize,0,0};HANDLE file=nullptr;
            if(CascOpenFile(storage,name.c_str(),CASC_LOCALE_ENUS,CASC_OPEN_BY_NAME,&file)) {
                std::vector<unsigned char> bytes(static_cast<size_t>(data.FileSize));
                if(CascReadFile(file,bytes.data(),static_cast<DWORD>(bytes.size()),&s.read)&&s.read==bytes.size()) {
                    std::ofstream out(output/s.file,std::ios::binary);out.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());
                    std::ostringstream hex;for(size_t i=0;i<std::min(size_t(32),bytes.size());i++) hex<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(bytes[i]);s.header=hex.str();
                } else s.error=GetLastError();CascCloseFile(file);
            } else s.error=GetLastError();samples.push_back(std::move(s));
        }
        if(total>=500000) {std::cerr<<"Archive enumeration cap reached\n";CascFindClose(search);CascCloseStorage(storage);return 1;}
    } while(CascFindNextFile(search,&data));
    DWORD endError=GetLastError();CascFindClose(search);CascCloseStorage(storage);
    std::ofstream report(output/"inventory.json");report<<"{\"build\":"<<product.BuildNumber<<",\"online\":false,\"features\":"<<features<<",\"files\":"<<total<<",\"available\":"<<available<<",\"enumerationEndError\":"<<endError<<",\"types\":{";
    bool first=true;for(const auto& c:counts) {if(!first) report<<',';first=false;report<<quoted(c.first)<<':'<<c.second;}report<<"},\"samples\":[";
    first=true;for(const auto& s:samples) {if(!first) report<<',';first=false;report<<"{\"name\":"<<quoted(s.name)<<",\"type\":"<<quoted(s.type)<<",\"file\":"<<quoted(s.file)<<",\"size\":"<<s.size<<",\"read\":"<<s.read<<",\"error\":"<<s.error<<",\"header\":"<<quoted(s.header)<<'}';}report<<"]}\n";
    std::cout<<"Read-only local beta "<<product.BuildNumber<<": "<<total<<" files, "<<available<<" locally available; "<<samples.size()<<" bounded sample reads.\n";
}
