"""Read-only pose observer for the exact supplied 2015 offline research build."""
from pathlib import Path
from modpack.config import paths
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import http.client
import json
import math
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
PATCHED_SHA256 = "f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f"
ALLOWED_PATHS = paths().native_allowed_paths()


class ResearchProcess:
    def __init__(self, pid):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                         wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                                 ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.kernel.K32EnumProcessModulesEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                                       wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
        # QUERY_INFORMATION | VM_READ only. No write, operation, thread creation or debugging rights.
        self.handle = self.kernel.OpenProcess(0x400 | 0x10, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            name, length = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            if not self.kernel.QueryFullProcessImageNameW(self.handle, 0, name, ctypes.byref(length)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.path = Path(name.value).resolve()
            if self.path not in {path.resolve() for path in ALLOWED_PATHS}:
                raise ValueError("Only the workspace's known research executable is supported")
            if hashlib.sha256(self.path.read_bytes()).hexdigest() != PATCHED_SHA256:
                raise ValueError("Executable hash differs from the verified research build")
            modules, needed = (ctypes.c_void_p * 512)(), wintypes.DWORD()
            if not self.kernel.K32EnumProcessModulesEx(self.handle, modules, ctypes.sizeof(modules), ctypes.byref(needed), 2):
                raise ctypes.WinError(ctypes.get_last_error())
            if not modules[0] or needed.value > ctypes.sizeof(modules):
                raise ValueError("Unsupported module enumeration")
            self.base = modules[0]
        except BaseException:
            self.close()
            raise

    def read(self, address, size):
        if not 0x10000 <= address < 0x7fff_ffff_ffff or not 1 <= size <= 65536:
            raise ValueError("Invalid bounded research read")
        buffer, received = ctypes.create_string_buffer(size), ctypes.c_size_t()
        if not self.kernel.ReadProcessMemory(self.handle, address, buffer, size, ctypes.byref(received)) or received.value != size:
            raise OSError("Research state is unavailable or changed during read")
        return buffer.raw

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


class PoseReader:
    """Offsets from Prometheus game.h/entity_admin.h/MovementState.h, no game calls."""
    def __init__(self, memory):
        self.memory = memory

    def unpack(self, fmt, address):
        return struct.unpack(fmt, self.memory.read(address, struct.calcsize(fmt)))

    def pointer(self, address):
        result, = self.unpack("<Q", address)
        if not 0x10000 <= result < 0x7fff_ffff_ffff:
            raise ValueError("Research pointer is absent or outside user address space")
        return result

    def entity(self, table, identifier):
        # Native buckets contain a contiguous list, not one entity. Once IDs
        # wrap their low12bits (projectiles/summons and repeated hero swaps),
        # the current controller may be the second or later entry in a bucket.
        preferred=identifier&4095
        for slot in [preferred,*(i for i in range(4096) if i!=preferred)]:
            intermediate, occupied, _ = struct.unpack_from("<Qii", table, slot * 16)
            if not 0<=occupied<=4096:raise ValueError("Research entity bucket count bounds")
            if occupied and intermediate:
                for entity_id,_,entity in struct.iter_unpack('<IIQ',self.memory.read(intermediate,occupied*16)):
                    if entity_id == identifier:
                        if not 0x10000 <= entity < 0x7fff_ffff_ffff:
                            raise ValueError("Invalid entity pointer")
                        return entity
        raise ValueError("Research entity is not present in this snapshot")

    def component(self, entity, identifier):
        pointers, count, capacity = self.unpack("<Qii", entity + 0x50)
        if not 1 <= count <= 256 or not count <= capacity <= 256:
            raise ValueError("Invalid research component list")
        components = self.memory.read(pointers, 8 * (count - 1)) if count > 1 else b""
        for pointer, in struct.iter_unpack("<Q", components):
            component_id, = self.unpack("<B", pointer + 0x10)
            if component_id == identifier:
                owner = self.pointer(pointer + 8)
                if owner != entity:
                    raise ValueError("Component owner changed during read")
                return pointer
        raise ValueError(f"Research component {identifier:#x} is absent")

    def sample(self):
        admin = self.pointer(self.memory.base + 0x17b7f90)
        local_id, = self.unpack("<I", admin + 0x220)
        table = self.memory.read(self.pointer(admin + 0x10), 4096 * 16)
        controller = self.entity(table, local_id)
        reference = self.component(controller, 0x20)
        model_id, = self.unpack("<I", reference + 0x94)
        model = self.entity(table, model_id)
        movement = self.component(model, 0x15) + 0xA50
        state = self.memory.read(movement, 0x270)
        tick, = struct.unpack_from("<i", state, 0x1A0)
        position = struct.unpack_from("<ffff", state, 0x220)[:3]
        if tick < 0 or any(not math.isfinite(value) or abs(value) > 10_000_000 for value in position):
            raise ValueError("Invalid or uninitialized original movement state")
        # Detect common map/hero changes rather than emitting a mixed identity snapshot.
        if self.pointer(self.memory.base + 0x17b7f90) != admin or self.unpack("<I", admin + 0x220)[0] != local_id:
            raise ValueError("Research world changed during read")
        return {"transport": "read-only-process-memory", "upstreamTick": tick,
                "position": dict(zip(("x", "y", "z"), position))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--samples", type=int, default=1, help="Sample count; 0 continues until Ctrl+C")
    parser.add_argument("--forward", action="store_true", help="Submit raw Prometheus-layout poses to the MC diagnostic receiver")
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    if args.pid <= 0 or not 0 <= args.samples <= 10000:
        parser.error("A valid PID and 0..10000 samples are required")
    process = None
    connection = http.client.HTTPConnection("127.0.0.1", 32131, timeout=2)
    captures = []
    try:
        process = ResearchProcess(args.pid)
        reader = PoseReader(process)
        sequence = 0
        while args.samples == 0 or sequence < args.samples:
            sample = reader.sample()
            record = {"schemaVersion": 1, "source": "prometheus", "sequence": sequence, **sample}
            if args.forward:
                connection.request("POST", "/v1/pose", json.dumps(record, allow_nan=False),
                                   {"Content-Type": "application/json"})
                response = connection.getresponse()
                response.read()
                if response.status != 200:
                    raise ValueError(f"Minecraft rejected diagnostic pose (HTTP {response.status})")
            if len(captures) < 200:
                captures.append(record)
            if sequence == 0 or (sequence + 1) % 100 == 0:
                print(json.dumps(record), flush=True)
            sequence += 1
            if args.samples == 0 or sequence < args.samples:
                time.sleep(1 / 30)
        if args.capture:
            args.capture.write_text(json.dumps({"pid": args.pid, "executable": str(process.path),
                "sha256": PATCHED_SHA256, "transport": "read-only-process-memory",
                "totalSamples": sequence, "forwardedToMinecraft": args.forward, "samples": captures}, indent=2), encoding="utf-8")
    except KeyboardInterrupt:
        print("Pose observer stopped.")
    except (OSError, ValueError, http.client.HTTPException) as error:
        parser.exit(1, f"Observer unavailable: {error}\n")
    finally:
        connection.close()
        if process is not None:
            process.close()
