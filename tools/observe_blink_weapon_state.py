"""Bounded read-only Blink/weapon/mask observations; sends zero game input.

Uses only the existing original logger and existing owner's JSON reports. Their
lossy snapshots and cumulative mask counters are NOT frame-exact proof of why a
weapon vanished. Pair with original-native and composed recordings before fixing
animation, FOV or hand-stage grouping. No hook/evaluator/write/focus is installed.
"""
import argparse
import ctypes
import json
import struct
import time
from ctypes import wintypes

from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates


class MappedFrames:
    """Read existing mappings only; never create/claim a publisher or copy pixels."""
    def __init__(self, pid):
        self.pid = pid
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel.OpenFileMappingW.restype = wintypes.HANDLE
        self.kernel.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
        self.kernel.MapViewOfFile.restype = ctypes.c_void_p
        self.kernel.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.maps = {}
        for name in ('Local\\OWMCHostPose', 'Local\\OWMCPassthroughFrame'):
            handle = self.kernel.OpenFileMappingW(4, False, name)
            if not handle:
                continue
            address = self.kernel.MapViewOfFile(handle, 4, 0, 0, 4096)
            if not address:
                self.kernel.CloseHandle(handle)
                continue
            self.maps[name] = (handle, address)

    def read(self):
        result = {}
        now = int(time.time() * 1000)
        for name, (_, address) in self.maps.items():
            raw = ctypes.string_at(address, 4096)
            if name.endswith('HostPose'):
                seq = struct.unpack_from('<Q', raw, 64)[0]
                if raw[:8] != b'OWPOSE01' or struct.unpack_from('<I', raw, 8)[0] != 1 or struct.unpack_from('<I', raw, 32)[0] != 1 \
                        or not seq or seq & 1 or ctypes.string_at(address + 64, 8) != raw[64:72]:
                    continue
                pid = struct.unpack_from('<I', raw, 16)[0]
                wall = struct.unpack_from('<Q', raw, 80)[0]
                if pid != self.pid or not -100 <= now-wall <= 250:
                    continue
                result['host'] = dict(pid=pid, generation=struct.unpack_from('<Q', raw, 24)[0],
                                      frame=struct.unpack_from('<Q', raw, 72)[0],
                                      wall=wall,
                                      inputBits=struct.unpack_from('<I', raw, 324)[0],
                                      inputActive=struct.unpack_from('<I', raw, 328)[0])
            else:
                if raw[:8] != b'OWMCFR01' or struct.unpack_from('<I', raw, 8)[0] != 2:
                    continue
                slot = struct.unpack_from('<i', raw, 48)[0]
                if not 0 <= slot < 3:
                    continue
                offset = 256 + slot * 256
                descriptor = raw[offset:offset + 256]
                seq, mc_frame, host_frame = struct.unpack_from('<QQQ', descriptor)
                if not seq or seq & 1 or ctypes.string_at(address + offset, 8) != descriptor[:8] or ctypes.string_at(address + 56, 8) != raw[56:64]:
                    continue
                wall = struct.unpack_from('<Q', descriptor, 104)[0]
                host_generation = struct.unpack_from('<Q', descriptor, 176)[0]
                if not -100 <= now-wall <= 1000 or bool(host_frame) != bool(host_generation):
                    continue
                result['mc'] = dict(sourcePid=struct.unpack_from('<I', raw, 52)[0],
                                    generation=struct.unpack_from('<Q', raw, 56)[0],
                                    mcFrame=mc_frame, hostFrame=host_frame,
                                    hostGeneration=host_generation, wall=wall)
        return result

    def close(self):
        for handle, address in self.maps.values():
            self.kernel.UnmapViewOfFile(address)
            self.kernel.CloseHandle(handle)
        self.maps.clear()


def creation_time(process):
    times = [ctypes.create_string_buffer(8) for _ in range(4)]
    process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
    if not process.kernel.GetProcessTimes(process.handle, *times):
        raise ctypes.WinError(ctypes.get_last_error())
    return struct.unpack('<Q', times[0].raw)[0]


def report(name, pid):
    try:
        data = json.loads((ROOT / f'native-host/build/{name}-{pid}.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if data.get('pid') != pid:
        return None
    fields = ('pid', 'probeVersion', 'enabled', 'failures', 'frames', 'generation',
              'sampleWallMs', 'viewMode', 'unmaskedFrames', 'unblendedPoses',
              'heldFrames', 'blended', 'blinkCaptures', 'blinkBound', 'lastMcFrame',
              'viewLightHero', 'viewLightModelId', 'viewLightWorldId',
              'handMaskTraceEnabled', 'handMaskTrace')
    return {key: data[key] for key in fields if key in data}


def run(pid, seconds, path):
    process = ResearchProcess(pid)
    created = creation_time(process)
    rows = []
    started = time.monotonic()
    mappings = MappedFrames(pid)
    try:
        reader = WeaponStates(process)
        while time.monotonic() - started < seconds:
            if creation_time(process) != created:
                raise ValueError('Native process creation identity changed')
            row = dict(elapsed=time.monotonic() - started, wallMs=int(time.time() * 1000),
                       qpcNs=time.perf_counter_ns(), mappedBefore=mappings.read())
            try:
                sample = reader.sample_weapon(False, True)
                row.update(localId=sample['localId'], modelId=sample['modelId'])
                row['states'] = [v for v in sample['records'].values()
                                 if v['script'] in ('0580000000000024', '0580000000000016')]
                row['variables'] = {key: value for key, value in sample['observedVariables'].items()
                                    if key in ('0580000000000024', '0580000000000016')}
                row['blinkGraphPresent'] = any(key[2] == 0x0580000000000024 for key in reader.graph_cache)
            except (OSError, ValueError) as error:
                row['readError'] = str(error)
            row['sampleEndWallMs'] = int(time.time() * 1000)
            row['mappedAfter'] = mappings.read()
            row['compositor'] = report('world-live', pid)
            row['body'] = report('body-sync', pid)
            rows.append(row)
            time.sleep(.05)
    finally:
        mappings.close()
        process.close()
    result = dict(pid=pid, creation=created, readOnly=True, inputSent=False,
                  nativeCalls=False, newHooks=False, actualDuration=time.monotonic() - started,
                  rows=rows, completed=True,
                  limits='Existing logger is lossy; report freshness/counters are not individual draw evidence. '
                         'No original/composed pixel comparison is performed by this tool.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(pid=pid, creation=created, samples=len(rows), inputSent=False,
                          blinkSamples=sum(row.get('blinkGraphPresent', False) for row in rows))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not 1 <= args.seconds <= 30 or ROOT / 'research' not in output.parents or output.suffix != '.json':
        parser.error('Use1..30 seconds and a private research JSON output')
    run(args.pid, args.seconds, output)
