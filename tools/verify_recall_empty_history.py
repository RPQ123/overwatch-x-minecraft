"""One controlled real Recall with empty MC history, then ordinary recovery.

Run ONLY on the fully modded disposable creative Switch save. The persistent
installed UM WinDrive stdin protocol is warmed/focused before the fixed 500ms
fixture; no new input process is started inside that window. This program never
edits native memory, grants charge, fabricates native Begin/End or stops nodes.
Each invocation requires a fresh private evidence directory and explicit current
native/MC creation times plus the installed guest JAR SHA256.
"""
from modpack.config import paths
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import struct
import subprocess
import sys
import threading
import time
import urllib.request

import psutil

from calibrate_hero_roster import ROSTER, observe, report
from launch_passthrough_session import first_person_ready
from native_binding_scope import GuestBindingScope
from native_map_snapshot import snapshot_map
from native_tracer_ammo import inspect as inspect_ammo
from observe_native_weapon_states import WeaponStates
from observe_overwatch import ROOT, ResearchProcess, PATCHED_SHA256


HERO = 0x02E0000000000003
RECALL = 0x058000000000001A
PROFILE = paths().get('profile')
EXE = paths().get('owExecutable')
JAR = PROFILE / 'mods/owmc-guest-0.1.0.jar'
BODY_KEYS = ('pid', 'probeVersion', 'enabled', 'failures', 'hero', 'modelId',
             'sourcePid', 'hostGeneration', 'guestGeneration', 'worldId',
             'recallCompletionCalls', 'recallCompleted', 'recallHistoryCalls',
             'recallHistoryCompleted', 'recallAmmoRestored', 'recallAmmoRefused')


class InvalidAttempt(RuntimeError):
    """A missed pause/input is not a pre-fix reproduction or post-fix pass."""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u64(value):
    return int(value) & ((1 << 64) - 1)


def request(route, post=False, timeout=2):
    req = urllib.request.Request('http://127.0.0.1:32133/' + route,
                                 method='POST' if post else 'GET')
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def position(player):
    return [player['x'], player['feetY'], player['z']]


class Identity:
    def __init__(self, args):
        self.args = args
        self.native = psutil.Process(args.pid)
        self.mc = psutil.Process(args.mc_pid)
        self.quick()
        require(Path(self.native.exe()).resolve() == EXE.resolve(), 'Native path differs')
        require(digest(EXE) == PATCHED_SHA256, 'Offline executable SHA256 differs')
        require(Path(self.mc.exe()).resolve().is_relative_to((ROOT / 'minecraft-1.21.1/runtime').resolve()),
                'MC Java executable is outside this project runtime')
        command = self.mc.cmdline()
        require('--gameDir' in command and Path(command[command.index('--gameDir') + 1]).resolve() == PROFILE.resolve(),
                'Actual MC --gameDir is not the isolated project profile')
        for option in ('-Dowmc.twilightTrial=true', '-Dowmc.creativeWorld=true',
                       '-Dowmc.worldName=' + args.world):
            require(option in command, 'Actual MC command lacks ' + option)
        require(args.world.startswith('Overwatch Twilight Switch '), 'Disposable Switch world required')
        settings_path = ROOT / 'passthrough-settings.json'
        settings = json.loads(settings_path.read_text(encoding='utf-8'))
        require(settings.get('worldName') == args.world and settings.get('twilightTrial') is True,
                'Current project settings differ from the named isolated profile')
        require(digest(JAR) == args.guest_sha256.lower(), 'Installed guest JAR SHA256 differs')
        require(JAR.stat().st_mtime <= args.mc_created + 1, 'Guest JAR changed after this MC process started')
        from twilight_forest import NAME, validate
        validate(PROFILE / 'mods' / NAME)
        self.files = {path: (path.stat().st_size, path.stat().st_mtime_ns)
                      for path in (EXE, JAR, settings_path)}
        self.proof = dict(pid=args.pid, creation=args.created, executable=str(EXE),
                          executableSha256=PATCHED_SHA256, mcPid=args.mc_pid,
                          mcCreation=args.mc_created, profile=str(PROFILE),
                          world=args.world, guestSha256=args.guest_sha256.lower(),
                          mcCommand=command, settings=settings)

    def quick(self):
        for process, created in ((self.native, self.args.created), (self.mc, self.args.mc_created)):
            require(process.is_running() and process.create_time() == created,
                    'Process exited or PID/creation identity changed')
        for path, signature in getattr(self, 'files', {}).items():
            require((path.stat().st_size, path.stat().st_mtime_ns) == signature,
                    'Pinned executable/JAR/profile configuration changed')

    def input_target(self):
        self.quick()
        matches = [p.pid for p in psutil.process_iter(['name'])
                   if (p.info.get('name') or '').lower() == EXE.name.lower()]
        require(matches == [self.args.pid], 'UM process-name selection is not unique to the verified PID')

    def health(self):
        self.quick()
        health = request('health')
        require(health.get('sourcePid') == self.args.mc_pid and health.get('worldName') == self.args.world,
                'HTTP source PID/world differs from the verified MC process')
        player = health.get('player') or {}
        require(player.get('alive') and not player.get('survival') and player.get('screen') == 'none',
                'MC is not a live creative gameplay world')
        return health


class PersistentDrive:
    """Actual installed UM WinDrive.ps1 one-line/reply protocol, no auto-refocus."""
    def __init__(self, identity, folder, log):
        self.identity, self.log = identity, log
        identity.input_target()
        package = Path(os.environ['APPDATA']) / 'uv/tools/universal-modder/Lib/site-packages'
        require((package / 'um/win.py').is_file(), 'Installed UM protocol implementation missing')
        sys.path.insert(0, str(package))
        from um.win import ps_exe, tool_path, text_utf8
        script = Path(tool_path('WinDrive.ps1'))
        self.proof = dict(script=str(script), sha256=digest(script),
                          implementation=str(package / 'um/win.py'),
                          implementationSha256=digest(package / 'um/win.py'))
        self.errors = open(folder / 'driver-stderr.log', 'w', encoding='utf-8')
        self.process = subprocess.Popen(
            [ps_exe(), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script),
             '-Proc', EXE.name], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.errors, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW, **text_utf8())
        self.lines = queue.Queue()
        def consume():
            for line in self.process.stdout:
                self.lines.put(line.strip())
            self.lines.put(None)
        threading.Thread(target=consume, daemon=True).start()
        try:
            require(self._reply(15) == 'ready window', 'UM did not find the native game window')
        except Exception:
            self.close()
            raise
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.user.GetForegroundWindow.restype = wintypes.HWND
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

    def _reply(self, timeout):
        try:
            reply = self.lines.get(timeout=timeout)
        except queue.Empty as error:
            raise RuntimeError('UM driver response deadline exceeded') from error
        require(reply is not None, 'UM input process exited')
        return reply

    def foreground(self):
        owner = wintypes.DWORD()
        self.user.GetWindowThreadProcessId(self.user.GetForegroundWindow(), ctypes.byref(owner))
        return owner.value == self.identity.args.pid

    def send(self, command):
        self.identity.input_target()
        if command != 'focus' and command.split()[0] not in ('rect', 'fg', 'title', 'idle'):
            require(self.foreground(), 'Foreground/input interference; no refocus or further input')
        require(self.process.poll() is None, 'UM input process is no longer running')
        sent = time.time() * 1000
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()
        answer = self._reply(5)
        self.log.append(dict(wall=sent, returnedWall=time.time() * 1000, command=command, reply=answer))
        require(answer != 'fail' and not answer.startswith('error'), 'Protected UM input refused: ' + answer)
        return answer

    def close(self):
        try:
            self.process.stdin.close()
            self.process.wait(3)
        except (OSError, subprocess.TimeoutExpired):
            # Only this helper is terminated, never a game process.
            self.process.terminate()
            self.process.wait(3)
        self.errors.close()


class Native:
    """Existing logger and typed original ammo reads; no new hook or native call."""
    def __init__(self, pid):
        self.process = ResearchProcess(pid)
        try:
            self._bind()
        except Exception:
            self.process.close()
            raise

    def _bind(self):
        self.reader = WeaponStates(self.process)
        sample = self.reader.sample_weapon(False, True)
        self.model = sample['modelId']
        matches = [key for key in self.reader.graph_cache if key[2] == RECALL]
        require(len(matches) == 1, 'Original Recall graph is not unique')
        self.script, self.graph, _ = matches[0]
        nodes = self.reader.stu_list(self.graph + 0x50)
        require(len(nodes) == 48 and self.reader.bindings.metadata(nodes[1])[1] == 0x7211CF70
                and self.reader.bindings.metadata(nodes[9])[1] == 0x7FB4BF64,
                'Original Recall graph declarations differ')
        admin = self.reader.pointer(self.process.base + 0x17B7F90)
        table = self.process.read(self.reader.pointer(admin + 16), 65536)
        self.controller = self.reader.entity(table, sample['localId'])
        self.reference = self.reader.component(self.controller, 0x20)
        self.hero_info = self.reader.component(self.controller, 0x3F)
        ammo = inspect_ammo(self.process)
        require(ammo['modelId'] == self.model, 'Ammo has another model')
        self.ammo = ammo['numeric']
        self.ammo_bag = self.reader.pointer(self.ammo + 0x80)

    def sample(self):
        r = self.reader
        require(r.unpack('<I', self.reference + 0x94)[0] == self.model
                and r.unpack('<Q', self.hero_info + 0x98)[0] == HERO,
                'Actual native hero/model changed; preserve failed pawn')
        # The provided logger has no row until a node actually executes. This
        # is the same inactive zero baseline used by NativeSkillReader.entry;
        # it can never satisfy the required positive Begin/End observations.
        records = {str(node): dict(tick=0, active=False, observed=False) for node in (1, 9, 31)}
        for instance, inner in snapshot_map(self.process, r.logger, 'Q'):
            if instance != self.script:
                continue
            for node, value in snapshot_map(self.process, inner, 'i', 4096):
                if node in (1, 9, 31):
                    tick, finished = r.unpack('<qB', value)
                    require(tick >= 0 and finished in (0, 1), 'Native Recall logger bounds')
                    records[str(node)] = dict(tick=tick, active=not bool(finished), observed=True)
        require(r.pointer(self.ammo + 0x80) == self.ammo_bag
                and r.unpack('<Q', self.ammo + 0x98)[0] == 0x0D80000000000035,
                'Original ammo owner changed')
        value = self.process.read(self.ammo + 0xA0, 16)
        ammo, kind = struct.unpack_from('<i', value)[0], struct.unpack_from('<i', value, 12)[0]
        require(kind == 2 and 0 <= ammo <= 40, 'Original typed magazine is outside bounds')
        return dict(modelId=self.model, states=records, ammo=ammo)

    def close(self):
        self.process.close()


class Trial:
    def __init__(self, args, folder, result):
        self.args, self.folder, self.result = args, folder, result
        self.identity = Identity(args)
        result['identity'] = self.identity.proof
        self.driver = PersistentDrive(self.identity, folder, result['input'])
        result['driver'] = self.driver.proof
        self.native = None
        self.scope_reader = GuestBindingScope()
        self.scope = None
        self.mutated = False

    def save(self):
        (self.folder / 'result.json').write_text(json.dumps(self.result, indent=2) + '\n', encoding='utf-8')

    def choose(self, name):
        _, suffix, x = next(row for row in ROSTER if row[0] == name)
        current = observe(self.args.pid)
        if current['hero'] == 0x02E0000000000000 + suffix and first_person_ready(self.args.pid):
            return
        if first_person_ready(self.args.pid):
            self.driver.send('key 0x48')
            time.sleep(.65)
        self.driver.send(f'click {x} 1224')
        time.sleep(.65)
        self.driver.send('click 1280 1358')
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            self.identity.health()
            current = observe(self.args.pid)
            if current['hero'] == 0x02E0000000000000 + suffix and first_person_ready(self.args.pid):
                return
            time.sleep(.15)
        raise ValueError('Actual original hero selection did not settle: ' + name)

    def setup(self):
        self.identity.health()
        require(self.driver.send('rect').split()[-2:] == ['2560', '1440'],
                'Known native picker coordinates require a 2560x1440 client area')
        self.driver.send('focus')
        self.choose('Genji')
        self.choose('Tracer')
        deadline = time.monotonic() + 12
        while True:
            h = self.identity.health()
            body = report(ROOT / f'native-host/build/body-sync-{self.args.pid}.json')
            emission = report(ROOT / f'native-host/build/native-emissions-{self.args.pid}.json')
            try:
                wire = self.scope_reader.read(self.args.pid)
            except (OSError, ValueError):
                require(time.monotonic() < deadline, 'Fresh shared-memory guest scope did not settle')
                time.sleep(.1)
                continue
            if (body.get('pid') == self.args.pid and body.get('hero') == HERO
                    and body.get('worldStable') and body.get('enabled') and not body.get('failures')
                    and body.get('sourcePid') == self.args.mc_pid
                    and all(u64(body.get(key, 0)) == u64(wire[key])
                            for key in ('sourcePid', 'hostGeneration', 'guestGeneration', 'worldId'))
                    and u64(h.get('hostGeneration', 0)) == u64(wire['hostGeneration'])
                    and emission.get('hero') == HERO and emission.get('combatReady')
                    and emission.get('modelId') == body.get('modelId')):
                break
            require(time.monotonic() < deadline, 'Actual Tracer/native channels did not settle')
            time.sleep(.1)
        self.native = Native(self.args.pid)
        require(self.native.model == body['modelId'], 'Native diagnostic refers to another model')
        self.scope = {key: body[key] for key in ('modelId', 'hostGeneration', 'guestGeneration', 'worldId')}
        self.result['scope'] = self.scope
        binding = report(ROOT / f'native-host/build/native-recall-request-{self.args.pid}.json')
        times = [ctypes.create_string_buffer(8) for _ in range(4)]
        process = self.native.process
        process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p] * 4)]
        require(process.kernel.GetProcessTimes(process.handle, *times), 'Cannot read actual native creation FILETIME')
        creation = struct.unpack('<Q', times[0].raw)[0]
        require(binding.get('pid') == self.args.pid and binding.get('creation') == creation
                and binding.get('hero') == HERO and binding.get('modelId') == self.native.model,
                'Recall request belongs to another native PID/creation/model')
        self.result['binding'] = binding
        self.result['nativeCreationFileTime'] = creation
        self.post('flight-open')
        time.sleep(.35)
        self.aim()
        require(self.identity.health()['player']['flying'], 'Fixture flight must prevent cleanup-induced falls')
        # Spend real original ammunition; no artificial magazine write.
        self.fire()
        time.sleep(.3)
        require(0 < self.native.sample()['ammo'] < 40, 'Need a real partly spent original magazine')
        self.post('recall-hurt')
        self.wait_health(2)
        time.sleep(.2)

    def post(self, action):
        self.identity.health()
        answer = request('combat/test/' + action, post=True)
        self.mutated = True
        return answer

    def aim(self):
        for _ in range(2):
            combat = request('combat')
            delta = (180 - combat['yaw'] + 180) % 360 - 180
            self.driver.send(f'rel {round(delta / .1)} {round(-combat["pitch"] / .1)}')
            time.sleep(.2)
        combat = request('combat')
        require(abs((180 - combat['yaw'] + 180) % 360 - 180) <= 2 and abs(combat['pitch']) <= 2,
                'Actual original aim did not settle')

    def fire(self):
        self.driver.send('mdown 1280 720')
        try:
            time.sleep(.15)
        finally:
            self.driver.send('mup')

    def wait_health(self, expected):
        deadline = time.monotonic() + 2
        while True:
            health = self.identity.health()
            if abs(health['player']['health'] - expected) < .001:
                return health
            require(time.monotonic() < deadline, 'Real MC health did not match fixture: ' + str(expected))
            time.sleep(.025)

    def snapshot(self):
        health = self.identity.health()
        # HTTP exposes a zero generation when its independently polled pose is
        # temporarily unavailable. Observe only; send no input or old-scope
        # events during that gap. A positive foreign identity is never retried.
        if not health.get('hostGeneration'):
            started=time.monotonic()
            while not health.get('hostGeneration') and time.monotonic()-started<.25:
                require(self.driver.foreground(), 'Focus interference during source suspension')
                time.sleep(.025)
                health=self.identity.health()
            self.result.setdefault('sourceSuspensions',[]).append(dict(
                wall=time.time()*1000, duration=time.monotonic()-started,
                resumedGeneration=health.get('hostGeneration'), inputSent=False))
        require(self.driver.foreground(), 'Focus interference during the controlled observation')
        body = report(ROOT / f'native-host/build/body-sync-{self.args.pid}.json')
        emission = report(ROOT / f'native-host/build/native-emissions-{self.args.pid}.json')
        require(body.get('pid') == self.args.pid and body.get('enabled') and not body.get('failures'),
                'Current native body is unavailable')
        for key, value in self.scope.items():
            require(u64(body[key]) == u64(value), 'Native/MC scope changed during the controlled cast: ' + key)
        wire = self.scope_reader.read(self.args.pid)
        require(wire['sourcePid'] == self.args.mc_pid
                and all(u64(wire[key]) == u64(self.scope[key])
                        for key in ('worldId', 'guestGeneration', 'hostGeneration'))
                and u64(health.get('hostGeneration', 0)) == u64(self.scope['hostGeneration']),
                'Fresh shared-memory/HTTP identity differs from the pinned cast: '
                + json.dumps(dict(wire=wire, httpSource=health.get('sourcePid'),
                                  httpGeneration=health.get('hostGeneration'), expected=self.scope)))
        combat = request('combat')
        return dict(wall=time.time() * 1000, player=health['player'], recall=combat.get('recall', {}),
                    body={key: body.get(key) for key in BODY_KEYS}, combat=combat,
                    factoryCalls=emission.get('factoryCalls', 0), native=self.native.sample())

    def screenshot(self, name):
        self.identity.input_target()
        subprocess.run(['um', 'win', 'shot', '--exe', EXE.name, str(self.folder / (name + '.png')),
                        '--scale', '.33'], cwd=ROOT, capture_output=True, check=True, timeout=20)

    def cast_trace(self, baseline, row, empty=False):
        old_tick = baseline['native']['states']['31']['tick']
        if empty:
            row['queued'] = self.post('recall-empty-history')
            deadline = time.monotonic() + 1
            while True:
                combat = request('combat', timeout=1)
                recall = combat.get('recall', {})
                if recall.get('historyTestPaused'):
                    break
                if time.monotonic() >= deadline:
                    raise InvalidAttempt('500ms history fixture was not observed armed: ' + str(recall))
                time.sleep(.005)
            for field, scope in (('historyTestWorld', 'worldId'), ('historyTestSource', 'hostGeneration'),
                                 ('historyTestModel', 'modelId')):
                require(u64(recall[field]) == u64(self.scope[scope]), 'Paused history belongs to another ' + scope)
            require(recall['historySamples'] == 0, 'Fixture pause retained history samples')
            row['armed'] = recall
            if time.time() * 1000 >= recall['historyTestUntil'] - 75:
                raise InvalidAttempt('Too little of the fixed 500ms window remains; no E sent')
        row['inputWall'] = time.time() * 1000
        self.driver.send('key 0x45')
        row['trace'] = []
        start = time.monotonic()
        while time.monotonic() - start < 3.2:
            sample = self.snapshot()
            row['trace'].append(sample)
            cast = sample['native']['states']['31']
            if cast['active'] and cast['tick'] > old_tick and 'begin' not in row:
                row['begin'] = dict(tick=cast['tick'], firstObservedWall=sample['wall'])
            self.save()
            time.sleep(.025)
        row['after'] = self.snapshot()
        require('begin' in row, 'No new actual native Recall Begin was observed; ignored E is not a pass')
        tick = row['begin']['tick']
        accepted = [sample for sample in row['trace']
                    if sample['recall'].get('lastBeginTick') == tick]
        require(accepted, 'MC did not admit the observed original Recall Begin')
        row['mcBegin'] = accepted[0]['recall']['lastBeginWall']
        if empty and not row['armed']['historyTestUntil'] - 500 <= row['mcBegin'] < row['armed']['historyTestUntil']:
            raise InvalidAttempt('Real MC/native Begin missed the scoped fixed pause')
        row['actualAnimationEnd'] = any(not sample['native']['states']['9']['active']
                                       and sample['native']['states']['9']['tick'] >= tick
                                       for sample in row['trace'])
        row['actualCastEnd'] = any(not sample['native']['states']['31']['active']
                                  and sample['native']['states']['31']['tick'] >= tick
                                  for sample in row['trace'])
        require(row['actualAnimationEnd'] and row['actualCastEnd'], 'Original animation/cast did not actually End')
        require(row['after']['body']['recallCompleted'] == baseline['body']['recallCompleted'] + 1,
                'Original root31 completion count did not increase exactly once')
        return row['after']

    def primary_probe(self, row, expected_working):
        self.aim()
        self.post('melee')
        time.sleep(.25)
        before = self.snapshot()
        require(before['combat'].get('targetHealth') == 20 and not before['combat'].get('testError'),
                'Actual full-health MC target was not created')
        self.fire()
        time.sleep(.55)
        after = self.snapshot()
        row['primary'] = dict(before=before, after=after)
        working = (after['combat'].get('targetHealth', 20) < 20
                   and after['native']['ammo'] < before['native']['ammo']
                   and after['factoryCalls'] > before['factoryCalls'])
        locked = (after['combat'].get('targetHealth') == 20
                  and after['native']['ammo'] == before['native']['ammo']
                  and after['factoryCalls'] == before['factoryCalls'])
        row['primary']['working'] = working
        row['primary']['locked'] = locked
        self.screenshot('post-primary-' + ('normal' if row.get('normal') else 'empty'))
        require(working if expected_working else locked,
                'Actual post-Recall primary damage/ammo/factory differs from the expected mode')

    def run_empty(self):
        baseline = self.snapshot()
        require(not baseline['native']['states']['31']['active'], 'Recall must begin from an inactive original baseline')
        require('lastBeginWall' in baseline['recall'], 'Diagnostic fixture build with real Begin wall is required')
        self.screenshot('before-empty')
        # Refresh after the bounded GPU capture; driver is already warm/focused.
        baseline = self.snapshot()
        row = dict(before=baseline)
        self.result['empty'] = row
        after = self.cast_trace(baseline, row, empty=True)
        tick = row['begin']['tick']
        require(abs(after['player']['health'] - baseline['player']['health']) < .001,
                'Empty-history cancellation granted health')
        require(math.dist(position(after['player']), position(baseline['player'])) < .03,
                'Empty-history cancellation moved the real player')
        row['nativeAmmo'] = dict(before=baseline['native']['ammo'], after=after['native']['ammo'],
                                note='The original beta cast may refill itself; adapter writes are checked separately')
        require(after['body']['recallAmmoRestored'] == baseline['body']['recallAmmoRestored'],
                'Empty-history cancellation called native ammo restoration')
        require(not after['recall'].get('historyTestPaused') and after['recall']['historySamples'] > 0,
                'Sampling did not automatically resume after the fixed pause')
        if self.args.mode == 'fixed':
            require(after['recall']['completionPhase'] == 3 and after['recall']['completionBegin'] == tick,
                    'No exact cancellation disposition for the actual native Begin')
            require(after['recall']['emptyHistoryCancellations'] == baseline['recall']['emptyHistoryCancellations'] + 1,
                    'Empty-candidate branch was not observed exactly once')
            require(after['body']['recallHistoryCompleted'] == baseline['body']['recallHistoryCompleted'] + 1
                    and not after['native']['states']['1']['active'], 'Native history1 did not finish exactly once')
        else:
            require(after['recall'].get('completionBegin') != tick,
                    'Before mode already has a terminal disposition; this is not the pre-fix rejection build')
            require(after['body']['recallHistoryCompleted'] == baseline['body']['recallHistoryCompleted']
                    and after['native']['states']['1']['active'], 'Pre-fix history1 lock was not reproduced')
        self.screenshot('after-empty')
        self.primary_probe(row, expected_working=self.args.mode == 'fixed')
        if self.args.mode == 'before':
            from verify_skill_recovery_stress import capture
            row['expectedFailureSnapshot'] = capture(self.args.pid, True)
        row['passed'] = True
        self.save()

    def run_normal(self):
        self.post('cleanup')
        time.sleep(.2)
        self.post('flight-open')
        time.sleep(.3)
        self.aim()
        self.wait_health(20)
        # The declared original cooldown is12s. Wait in bounded observation
        # chunks; do not set the cooldown or send repeated E until it works.
        until = self.result['empty']['mcBegin'] / 1000 + 13
        while time.time() < until:
            self.snapshot()
            time.sleep(.2)
        self.fire()
        time.sleep(.3)
        require(0 < self.native.sample()['ammo'] < 40, 'Normal Recall needs a real partially spent magazine')
        anchor = self.snapshot()
        self.result['normal'] = row = dict(normal=True, healthyHistoryAnchor=anchor)
        start = time.monotonic()
        while time.monotonic() - start < 3.25:
            self.snapshot()
            time.sleep(.1)
        self.driver.send('hold 0x57 500')
        time.sleep(.15)
        require(math.dist(position(anchor['player']), position(self.identity.health()['player'])) > 1,
                'Normal Recall did not acquire a real movement history')
        self.post('recall-hurt')
        self.wait_health(2)
        row['before'] = baseline = self.snapshot()
        after = self.cast_trace(baseline, row)
        tick = row['begin']['tick']
        require(after['recall']['completionPhase'] == 2 and after['recall']['completionBegin'] == tick,
                'Normal Recall did not produce its own successful disposition')
        require(after['player']['health'] == 20 and after['native']['ammo'] == 40,
                'Normal Recall did not restore actual historical health/original magazine')
        require(math.dist(position(after['player']), position(anchor['player'])) < .05,
                'Normal Recall did not return to the actual healthy history location')
        row['adapterAmmoRestoreDelta'] = after['body']['recallAmmoRestored'] - baseline['body']['recallAmmoRestored']
        require(after['recall']['completed'] == baseline['recall']['completed'] + 1
                and after['body']['recallHistoryCompleted'] == baseline['body']['recallHistoryCompleted'] + 1
                and row['adapterAmmoRestoreDelta'] in (0, 1),
                'Normal Recall completion/history/ammo was not exactly once')
        self.screenshot('after-normal')
        self.primary_probe(row, expected_working=True)
        row['passed'] = True
        self.save()


def main(args):
    folder = args.output.resolve()
    require((ROOT / 'research').resolve() in folder.parents, 'Use a private research output directory')
    folder.mkdir(parents=True, exist_ok=False)
    result = dict(mode=args.mode, passed=False, featurePassed=False, input=[],
                  inputProtocol='installed UM WinDrive.ps1 continuous stdin, no automatic retries',
                  acceptanceMeaning='before=reproduced old failure only; fixed=empty cancel and ordinary Recall recovered',
                  visualAcceptance='pending root image review')
    trial = None
    try:
        trial = Trial(args, folder, result)
        trial.setup()
        trial.run_empty()
        if args.mode == 'fixed':
            trial.run_normal()
            result['featurePassed'] = True
            result['outcome'] = 'fixed-empty-cancel-and-normal-recall-passed'
        else:
            # Do not replace/recover the failing native pawn or falsely call
            # the expected pre-fix failure a working feature.
            result['outcome'] = 'reproduced-pre-fix-history-lock-and-primary-failure'
        result['passed'] = True
    except Exception as error:
        result['error'] = repr(error)
        result['invalidAttempt'] = isinstance(error, InvalidAttempt)
        result['outcome'] = 'invalid-attempt' if result['invalidAttempt'] else 'failed'
        if trial and trial.native:
            try:
                from verify_skill_recovery_stress import capture
                result['failureSnapshot'] = capture(args.pid, True)
                trial.screenshot('failed-pawn')
            except Exception as snapshot_error:
                result['failureSnapshotError'] = repr(snapshot_error)
    finally:
        if trial:
            if trial.mutated:
                try:
                    trial.identity.health()
                    if trial.native:
                        trial.native.sample()  # do not reset another hero's skills after interference
                    trial.post('cleanup')
                    time.sleep(.2)
                    combat = request('combat')
                    result['cleaned'] = (combat.get('wallBlocks') == 0 and 'targetHealth' not in combat
                                         and not combat.get('recall', {}).get('historyTestPaused'))
                except Exception as cleanup_error:
                    result['cleanupError'] = repr(cleanup_error)
            if trial.native:
                trial.native.close()
            trial.scope_reader.close()
            try:
                trial.driver.close()
            except Exception as driver_error:
                result['driverCloseError'] = repr(driver_error)
        if not result.get('cleaned'):
            result['passed'] = False
        (folder / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({key: result.get(key) for key in
                          ('mode', 'passed', 'featurePassed', 'outcome', 'error', 'invalidAttempt', 'cleaned')}), flush=True)
    return bool(result['passed'] and result.get('cleaned'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--created', required=True, type=float, help='Exact psutil native create_time()')
    parser.add_argument('--mc-pid', required=True, type=int)
    parser.add_argument('--mc-created', required=True, type=float, help='Exact psutil MC create_time()')
    parser.add_argument('--world', required=True)
    parser.add_argument('--guest-sha256', required=True)
    parser.add_argument('--mode', choices=('before', 'fixed'), required=True)
    parser.add_argument('--output', required=True, type=Path)
    parsed = parser.parse_args()
    raise SystemExit(0 if main(parsed) else 1)
