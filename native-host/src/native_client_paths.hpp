#pragma once
#include <windows.h>
#include <bcrypt.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <vector>

namespace owmc {
// Directory placement is not an executable identity. All production workers
// must verify the exact owned offline binary before reading engine pointers.
inline constexpr std::array<unsigned char,32> researchClientSha256{
    0xf7,0x3a,0x74,0x7b,0x7d,0x63,0xa0,0x74,0x02,0x95,0x8b,0x2b,0x2c,0x45,0x87,0x12,
    0x5a,0x46,0xef,0x8e,0x18,0x12,0x81,0x66,0x9d,0xa0,0x09,0xd3,0x52,0x30,0x8e,0x9f};

inline bool moduleFilePath(HMODULE module,std::filesystem::path& result) noexcept {
    try {
        std::array<wchar_t,32768> path{};
        const DWORD length=GetModuleFileNameW(module,path.data(),DWORD(path.size()));
        if(!length||length>=path.size())return false;
        auto found=std::filesystem::path(std::wstring(path.data(),length)).lexically_normal();
        if(!found.is_absolute())return false;
        result=std::move(found);return true;
    }catch(...){return false;}
}

inline bool clientCompanionPath(const std::filesystem::path& loaded,const std::filesystem::path& executable,
                                const std::filesystem::path& filename) {
    if(!loaded.is_absolute()||!executable.is_absolute()||filename.empty()
        ||filename!=filename.filename()||filename==L"."||filename==L"..")return false;
    const auto expected=(executable.parent_path()/filename).lexically_normal();
    return !_wcsicmp(loaded.lexically_normal().c_str(),expected.c_str());
}
inline bool loadedClientCompanion(HMODULE module,const std::filesystem::path& executable,const wchar_t* filename) {
    std::filesystem::path loaded;
    return module&&moduleFilePath(module,loaded)&&clientCompanionPath(loaded,executable,filename);
}

// Resolve CNG from System32 so every existing MinGW build entry keeps working
// without an added import-library dependency or any DLL search in the client.
namespace client_identity_detail {
template<class T> inline T function(HMODULE library,const char* name) {
    const auto address=GetProcAddress(library,name);T result=nullptr;
    static_assert(sizeof result==sizeof address);std::memcpy(&result,&address,sizeof result);return result;
}
struct Sha256 {
    HMODULE library=nullptr;BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    decltype(&BCryptOpenAlgorithmProvider) open=nullptr;
    decltype(&BCryptGetProperty) property=nullptr;
    decltype(&BCryptCreateHash) create=nullptr;
    decltype(&BCryptHashData) update=nullptr;
    decltype(&BCryptFinishHash) finish=nullptr;
    decltype(&BCryptDestroyHash) destroy=nullptr;
    decltype(&BCryptCloseAlgorithmProvider) close=nullptr;
    std::vector<unsigned char> object;
    ~Sha256(){if(hash&&destroy)destroy(hash);if(algorithm&&close)close(algorithm,0);if(library)FreeLibrary(library);}
    bool initialize() {
        library=LoadLibraryExW(L"bcrypt.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!library)return false;
        open=function<decltype(open)>(library,"BCryptOpenAlgorithmProvider");
        property=function<decltype(property)>(library,"BCryptGetProperty");
        create=function<decltype(create)>(library,"BCryptCreateHash");
        update=function<decltype(update)>(library,"BCryptHashData");
        finish=function<decltype(finish)>(library,"BCryptFinishHash");
        destroy=function<decltype(destroy)>(library,"BCryptDestroyHash");
        close=function<decltype(close)>(library,"BCryptCloseAlgorithmProvider");
        if(!open||!property||!create||!update||!finish||!destroy||!close
            ||open(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)return false;
        ULONG length=0,size=0,digest=0;
        if(property(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&length),sizeof length,&size,0)<0
            ||size!=sizeof length||!length||length>1024*1024
            ||property(algorithm,BCRYPT_HASH_LENGTH,reinterpret_cast<PUCHAR>(&digest),sizeof digest,&size,0)<0
            ||size!=sizeof digest||digest!=32)return false;
        object.resize(length);
        return create(algorithm,&hash,object.data(),ULONG(object.size()),nullptr,0,0)>=0;
    }
};
struct File {HANDLE value=INVALID_HANDLE_VALUE;~File(){if(value!=INVALID_HANDLE_VALUE)CloseHandle(value);}};
}

inline bool sha256File(const std::filesystem::path& file,std::array<unsigned char,32>& digest) noexcept {
    try {
        client_identity_detail::File input;
        // No write/delete sharing while reading the executable's immutable bytes.
        input.value=CreateFileW(file.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,nullptr);
        if(input.value==INVALID_HANDLE_VALUE)return false;
        LARGE_INTEGER size{};if(!GetFileSizeEx(input.value,&size)||size.QuadPart<0)return false;
        client_identity_detail::Sha256 sha;if(!sha.initialize())return false;
        std::array<unsigned char,65536> buffer{};uint64_t count=0;
        for(;;) {
            DWORD received=0;if(!ReadFile(input.value,buffer.data(),DWORD(buffer.size()),&received,nullptr))return false;
            if(!received)break;
            count+=received;if(sha.update(sha.hash,buffer.data(),received,0)<0)return false;
        }
        std::array<unsigned char,32> result{};
        if(count!=uint64_t(size.QuadPart)||sha.finish(sha.hash,result.data(),ULONG(result.size()),0)<0)return false;
        digest=result;return true;
    }catch(...){return false;}
}
inline bool researchClientFile(const std::filesystem::path& executable) noexcept {
    if(!executable.is_absolute()||_wcsicmp(executable.filename().c_str(),L"GameClientApp.patched.exe"))return false;
    std::array<unsigned char,32> digest{};
    return sha256File(executable,digest)&&digest==researchClientSha256;
}
inline bool runningResearchClient(std::filesystem::path& executable) noexcept {
    std::filesystem::path current;
    if(!moduleFilePath(nullptr,current)||!researchClientFile(current))return false;
    executable=std::move(current);return true;
}
}
