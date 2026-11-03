#include "../src/native_client_paths.hpp"
#include <cassert>
#include <fstream>
#include <iostream>

std::filesystem::path environmentPath(const wchar_t* name) {
    std::array<wchar_t,32768> value{};DWORD length=GetEnvironmentVariableW(name,value.data(),DWORD(value.size()));
    assert(length&&length<value.size());return std::filesystem::path(value.data());
}
int main() {
    const auto root=environmentPath(L"OWMC_TEST_PATH_ROOT");
    const auto client=environmentPath(L"OWMC_TEST_CLIENT_EXE");
    assert(root.is_absolute()&&client.is_absolute());
    assert(!std::filesystem::exists(root));std::filesystem::create_directories(root);
    const auto abc=root/L"abc.bin";
    {std::ofstream output(abc,std::ios::binary);output<<"abc";assert(output);}
    const std::array<unsigned char,32> abcSha{0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,
        0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
    std::array<unsigned char,32> digest{};assert(owmc::sha256File(abc,digest)&&digest==abcSha);
    const auto before=digest;assert(!owmc::sha256File(root/L"missing.exe",digest)&&digest==before);
    auto lock=CreateFileW(abc.c_str(),GENERIC_READ|GENERIC_WRITE,0,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    assert(lock!=INVALID_HANDLE_VALUE&&!owmc::sha256File(abc,digest)&&digest==before);CloseHandle(lock);
    assert(owmc::sha256File(client,digest)&&digest==owmc::researchClientSha256&&owmc::researchClientFile(client));
    // A valid filename and directory are insufficient: reject wrong bytes and
    // the current fixture process before any native engine pointer is read.
    auto wrong=root/L"GameClientApp.patched.exe";
    {std::ofstream output(wrong,std::ios::binary);output<<"inert fixture, not a game";assert(output);}
    assert(!owmc::researchClientFile(wrong)&&!owmc::researchClientFile(abc));
    assert(!owmc::researchClientFile(L"relative/GameClientApp.patched.exe"));
    std::filesystem::path actual;
    assert(owmc::moduleFilePath(nullptr,actual)&&actual.is_absolute());
    assert(owmc::sha256File(actual,digest)); // Read an actually running image with the production sharing flags.
    std::filesystem::path unchanged=L"unchanged";
    assert(!owmc::runningResearchClient(unchanged)&&unchanged==L"unchanged");
    assert(owmc::loadedClientCompanion(GetModuleHandleW(nullptr),actual,actual.filename().c_str()));
    assert(!owmc::loadedClientCompanion(nullptr,actual,L"inject.dll"));
    assert(!owmc::loadedClientCompanion(GetModuleHandleW(L"kernel32.dll"),actual,L"kernel32.dll"));
    unsigned accepted=0,refused=0;
    for(const auto& folder:{root/L"dev layout"/L"overwatch-2015"/L"Overwatch Beta 0.8.0.24919",
            root/L"\u4e2d\u6587 \u6574\u5408\u5305"/L"game"/L"Overwatch Beta 0.8.0.24919",
            root/L"another arbitrary root"/L"client with spaces"}) {
        std::filesystem::create_directories(folder);
        const auto link=folder/L"GameClientApp.patched.exe";
        // Same-volume hardlinks only: no duplicate game payload, no writes to
        // the binary, and no real process is launched from these paths.
        assert(CreateHardLinkW(link.c_str(),client.c_str(),nullptr));
        assert(owmc::researchClientFile(link));accepted++;
        assert(owmc::clientCompanionPath(folder/L"inject.dll",link,L"inject.dll"));
        assert(owmc::clientCompanionPath(folder/L"MINHOOK.X64.DLL",link,L"minhook.x64.dll"));
        assert(!owmc::clientCompanionPath(root/L"inject.dll",link,L"inject.dll"));refused++;
        assert(!owmc::clientCompanionPath(folder/L"other"/L"inject.dll",link,L"inject.dll"));refused++;
        assert(!owmc::clientCompanionPath(folder/L"inject.dll",link,L"../inject.dll"));refused++;
        assert(!owmc::clientCompanionPath(folder/L"minhook.x64.dll",link,L"inject.dll"));refused++;
    }
    std::cout<<"PASS: CNG SHA256 known vector and exact offline EXE; "<<accepted
        <<" relocated/Unicode/space roots; "<<refused
        <<" foreign companion refusals; wrong hash/name/process, read failure, locked file, and loaded-module guards. No game launched.\n";
}
