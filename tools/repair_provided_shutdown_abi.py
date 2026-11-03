"""Cold, two-byte correction of one verified supplied-plugin interface slot.

No runtime writes, new hooks, arbitrary PE patching or allocator bypasses.
The original noop deallocate leaves RAX unspecified; its native caller expects
a nullable allocation pointer. Reuse the same type's verified zero-return
implementation while retaining the original DIR64 relocation and all code.
"""
from modpack.config import paths
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import struct
import time

import psutil
from observe_overwatch import ROOT, PATCHED_SHA256
from provided_plugin_symbols import PeImage, PdbSymbols

GAME = paths().get('owExecutable').parent
TARGET = GAME / "inject.dll"
ORIGINAL = "12a0cf4a105f3e60b36aa9f0186cf82abcd0ab2e6e4354047004ec17a94e2e17"
CORRECTED = "c82f8cea31aca0da8e1cd0b2b4d1a6a1c671a86fa4f1a52120985cbeec2ff2d6"
PDB_SHA = "6947622a4a38a1b5f75961e65de9ff89a05d9a461e7a7293a837a73cf306159b"
GUID = bytes.fromhex("6243b67bb4c67244b35323c1dfc3a1a6")
VTABLE, SLOT, NOOP, ZERO = 0x271820, 0x271840, 0x38a00, 0x3ef20
IMAGE_BASE = 0x180000000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dir64_relocations(image):
    data = image.data
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    rva, size = struct.unpack_from("<II", data, pe + 24 + 112 + 5 * 8)
    if not 0 < size <= 2 * 1024 * 1024:
        raise ValueError("Relocation directory bounds")
    start = image.file_offset(rva)
    end = start + size
    if end > len(data):
        raise ValueError("Truncated relocations")
    result = set()
    at = start
    while at < end:
        if at + 8 > end:
            raise ValueError("Truncated relocation block")
        page, length = struct.unpack_from("<II", data, at)
        if length < 8 or length % 2 or at + length > end:
            raise ValueError("Invalid relocation block")
        for entry, in struct.iter_unpack("<H", data[at + 8:at + length]):
            if entry >> 12 == 10:
                result.add(page + (entry & 4095))
        at += length
    return result


def validate(data, pdb_data):
    sha = digest(data)
    if sha not in (ORIGINAL, CORRECTED) or digest(pdb_data) != PDB_SHA:
        raise ValueError("Unrecognized supplied DLL/PDB: no changes allowed")
    image = PeImage(TARGET, data)
    pdb = PdbSymbols(GAME / "prometheus.pdb", pdb_data)
    if image.identity != pdb.identity or image.identity != (GUID, 1):
        raise ValueError("PE/PDB identity mismatch")
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    if (struct.unpack_from("<Q", data, pe + 24 + 24)[0] != IMAGE_BASE
            or image.timestamp != 1767466924 or image.image_size != 0x2e8000):
        raise ValueError("Unexpected supplied image layout")
    if image.symbol_rva(pdb.exact("??_7PrometheusSystem@@6B@")) != VTABLE:
        raise ValueError("Exact system interface missing")
    rva, code = image.function_prefix(pdb.exact("?deallocate@PrometheusSystem@@EEAAXXZ"))
    if rva != NOOP or code[:16] != bytes.fromhex("c20000" + "cc" * 13):
        raise ValueError("Original noop semantics differ")
    rva, code = image.function_prefix(pdb.exact("?get_inheritance@PrometheusSystem@@EEAA_JXZ"))
    if rva != ZERO or code[:16] != bytes.fromhex("33c0c3" + "cc" * 13):
        raise ValueError("Zero-return semantics differ")
    if SLOT not in dir64_relocations(image):
        raise ValueError("System slot has no DIR64 relocation")
    expected = IMAGE_BASE + (NOOP if sha == ORIGINAL else ZERO)
    if struct.unpack_from("<Q", data, image.file_offset(SLOT))[0] != expected:
        raise ValueError("Unexpected interface slot")
    return image, sha


def corrected_payload(data, pdb_data):
    image, sha = validate(data, pdb_data)
    if sha == CORRECTED:
        return data
    result = bytearray(data)
    offset = image.file_offset(SLOT)
    struct.pack_into("<Q", result, offset, IMAGE_BASE + ZERO)
    if digest(result) != CORRECTED:
        raise ValueError("Candidate digest differs")
    # This also proves that the known code and relocation directory survived.
    validate(bytes(result), pdb_data)
    return bytes(result)


def require_cold():
    exe = (GAME / "GameClientApp.patched.exe").resolve()
    if digest(exe.read_bytes()) != PATCHED_SHA256:
        raise ValueError("Offline executable identity differs")
    for process in psutil.process_iter(["name", "exe"]):
        name = (process.info.get("name") or "").casefold()
        if name != exe.name.casefold():
            continue
        # Refuse even an uncertain same-name process; never inspect/write it.
        path = process.info.get("exe")
        if not path or Path(path).resolve() == exe:
            raise RuntimeError("Target is running; strict restoration and exit required")


def stage(directory):
    directory = Path(directory).resolve()
    private = paths().get('backups')
    if not directory.is_relative_to(private) or directory == private:
        raise ValueError("Stage must be a dedicated private backup directory")
    original = TARGET.read_bytes()
    pdb = (GAME / "prometheus.pdb").read_bytes()
    _, sha = validate(original, pdb)
    if sha != ORIGINAL:
        raise ValueError("Already corrected; use the existing recorded backup")
    candidate = corrected_payload(original, pdb)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "inject.original.dll").write_bytes(original)
    (directory / "inject.corrected.dll").write_bytes(candidate)
    metadata = {
        "created": time.time(), "target": str(TARGET.resolve()),
        "originalSha256": ORIGINAL, "correctedSha256": CORRECTED,
        "pdbSha256": PDB_SHA, "slotRva": SLOT,
        "oldTargetRva": NOOP, "newTargetRva": ZERO,
        "changedByteCount": sum(a != b for a, b in zip(original, candidate)),
        "codeChanged": False, "relocationsChanged": False,
        "scope": "PrometheusSystem deallocate return ABI only; TIMER is unresolved",
    }
    (directory / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def flush_file(stream):
    stream.flush()
    os.fsync(stream.fileno())


def replace_slot(stream, expected, wanted, offset, flush=flush_file):
    """Verify under the exclusive handle; roll back any partial write in-place."""
    stream.seek(0)
    locked = stream.read()
    if locked != expected:
        raise ValueError("Target changed before exclusive open; nothing written")
    if len(wanted) != len(locked) or wanted[:offset] != locked[:offset] or wanted[offset + 8:] != locked[offset + 8:]:
        raise ValueError("Only one existing eight-byte slot may change")
    old = locked[offset:offset + 8]
    if len(old) != 8:
        raise ValueError("Truncated interface slot")
    try:
        stream.seek(offset)
        if stream.write(wanted[offset:offset + 8]) != 8:
            raise OSError("Short interface-slot write")
        flush(stream)
        stream.seek(0)
        if stream.read() != wanted:
            raise OSError("Locked readback differs")
    except BaseException as failure:
        try:
            stream.seek(offset)
            if stream.write(old) != 8:
                raise OSError("Short rollback write")
            flush(stream)
            stream.seek(0)
            if stream.read() != locked:
                raise OSError("Rollback readback differs")
        except BaseException as rollback:
            raise RuntimeError("Slot rollback failed; do not launch, restore the pinned private backup") from rollback
        raise RuntimeError("Slot update failed; original contents restored and verified") from failure


def install(directory, restore=False):
    directory = Path(directory).resolve()
    private = paths().get('backups')
    if not directory.is_relative_to(private) or directory == private:
        raise ValueError("Unrecognized private staging location")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("target") != str(TARGET.resolve())
            or manifest.get("originalSha256") != ORIGINAL
            or manifest.get("correctedSha256") != CORRECTED):
        raise ValueError("Staging identity differs")
    original = (directory / "inject.original.dll").read_bytes()
    candidate = (directory / "inject.corrected.dll").read_bytes()
    pdb = (GAME / "prometheus.pdb").read_bytes()
    if digest(original) != ORIGINAL or corrected_payload(original, pdb) != candidate:
        raise ValueError("Staged content is not the verified two-byte correction")
    require_cold()
    current = TARGET.read_bytes()
    _, before = validate(current, pdb)
    wanted = original if restore else candidate
    if current != wanted:
        # Open the actual DLL exclusively. A mapped DLL or concurrent loader
        # must fail rather than rename/overwrite a loaded image.
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                      ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.CreateFileW(str(TARGET.resolve()), 0xc0000000, 0, None, 3, 0x80, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            require_cold()
            import msvcrt
            descriptor = msvcrt.open_osfhandle(handle, os.O_BINARY | os.O_RDWR)
            handle = None  # The file descriptor now owns this exclusive handle.
            offset = PeImage(TARGET, current).file_offset(SLOT)
            with os.fdopen(descriptor, "r+b", buffering=0) as locked:
                replace_slot(locked, current, wanted, offset)
        finally:
            if handle is not None:
                kernel.CloseHandle(handle)
    after = digest(TARGET.read_bytes())
    if after != digest(wanted):
        raise ValueError("Installed content hash differs; do not launch")
    receipt = {"at": time.time(), "restore": restore, "before": before, "after": after,
               "cold": True, "runtimeWrites": False, "target": str(TARGET.resolve())}
    (directory / ("restore.json" if restore else "installed.json")).write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--audit", action="store_true")
    action.add_argument("--stage", type=Path)
    action.add_argument("--install", type=Path)
    action.add_argument("--restore", type=Path)
    args = parser.parse_args()
    if args.audit:
        _, sha = validate(TARGET.read_bytes(), (GAME / "prometheus.pdb").read_bytes())
        result = {"sha256": sha, "corrected": sha == CORRECTED, "slotRva": SLOT}
    elif args.stage:
        result = stage(args.stage)
    else:
        result = install(args.restore or args.install, bool(args.restore))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
