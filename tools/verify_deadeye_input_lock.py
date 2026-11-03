"""Controlled real Deadeye control-lock acceptance; never run against a user save.

Requires exact current PID/create-time/JAR identities on the fully modded
disposable Twilight Switch profile. Only the already installed UM input protocol
is used. Typed lab grants are diagnostic, not natural-charge acceptance. No
native Begin/End, animation, damage or lock proof is fabricated. The root operator
must back up the profile and ensure an uninterrupted input window before running.
"""
from __future__ import annotations
import argparse
import ctypes
import json
import math
from pathlib import Path
import struct
import subprocess
import threading
import time

from calibrate_hero_roster import ROSTER, observe, report
from launch_passthrough_session import first_person_ready, installed_modules
from native_binding_scope import GuestBindingScope, GuestScopeExpired, decode_scope
from native_charge import grant_for_test
from observe_native_weapon_states import WeaponStates
from observe_overwatch import ROOT, ResearchProcess, PoseReader
from verify_recall_empty_history import Identity, PersistentDrive, request, digest

HERO = 0x02E0000000000042
DEY1 = 0x31594544
RESOURCE = '058000000000022f'


class HostPoseGap(ValueError):
    """A correctly identified camera mapping has no <=150ms frame yet."""

class GuestBodyGap(ValueError):
    """Same admitted session temporarily has no fresh body; observe only."""


def require(ok, message):
    if not ok:
        raise ValueError(message)


def client_command(command, size):
    """Scale only absolute menu/fire positions, never native mouse deltas.

    These are measured original-menu positions in the 2560x1440 reference.
    Scaling input to the existing client must never resize the render window.
    """
    width, height = size
    # Actual 2376x1080 drew the picker but ignored both scaled and internal
    # positions. Matching the accepted native 1920x1080 mode restored selection.
    # Do not turn the earlier arithmetic fixture into a live compatibility claim.
    require(size in ((2560, 1440), (1920, 1080)),
            'Original picker requires an accepted 16:9 client; do not resize just for this test')
    parts = command.split()
    if len(parts) >= 3 and parts[0] in ('click', 'mdown', 'move'):
        x, y = map(int, parts[1:3])
        require(0 <= x < 2560 and 0 <= y < 1440, 'Reference mouse position outside client')
        parts[1:3] = [str(round(x*width/2560)), str(round(y*height/1440))]
        return ' '.join(parts)
    return command


def angular(a, b):
    return abs((a-b+180) % 360-180)


def distance(a, b, horizontal=False):
    indexes = (0, 2) if horizontal else (0, 1, 2)
    return math.sqrt(sum((a[i]-b[i])**2 for i in indexes))


def decode_pose(raw, pid, now):
    u32 = lambda off: struct.unpack_from('<I', raw, off)[0]
    u64 = lambda off: struct.unpack_from('<Q', raw, off)[0]
    require(len(raw) == 4096 and raw[:8] == b'OWPOSE01'
            and (u32(8), u32(12), u32(16), u32(32)) == (1, 4096, pid, 1), 'Host pose identity')
    require(u64(64) > 0 and not u64(64) & 1, 'Host pose sequence')
    require(u64(24) > 0 and u64(72) > 0, 'Host pose generation/frame')
    age = now-u64(80)
    require(age >= 0, 'Host pose timestamp is in the future')
    if age > 150:
        raise HostPoseGap(f'Host pose stale: age={age}ms frame={u64(72)}')
    basis = list(struct.unpack_from('<9f', raw, 128))
    require(all(math.isfinite(v) for v in basis), 'Nonfinite native camera basis')
    return dict(generation=u64(24), frame=u64(72), wall=u64(80), flags=u32(88),
                inputActive=bool(u32(328)), capabilities=u32(332), basis=basis,
                eye=list(struct.unpack_from('<3f', raw, 168)), movementBits=u32(324),
                yaw=math.degrees(math.atan2(basis[6], -basis[8])),
                pitch=math.degrees(math.atan2(basis[7], math.hypot(basis[6], basis[8]))))


def decode_body(raw, pid, now):
    scope = decode_scope(raw, pid, now)
    u32 = lambda off: struct.unpack_from('<I', raw, off)[0]
    u64 = lambda off: struct.unpack_from('<Q', raw, off)[0]
    magic = u32(176)
    require(magic in (0, DEY1), 'Unknown Deadeye control extension')
    return dict(**scope, wall=u64(72), grounded=bool(u32(80)),
                position=list(struct.unpack_from('<3d', raw, 96)),
                velocity=list(struct.unpack_from('<3f', raw, 120)), magic=magic,
                firing=bool(u32(180)), model=u32(184), begin=u64(192),
                script=u64(200), logger=u64(208), observed=u64(216), deadeyeWorld=u64(224))


def check_firing_proof(row, model):
    b, root, fire = row['body'], row['nativeStates']['18'], row['nativeStates']['44']
    require(b['magic'] == DEY1 and b['firing'] and root['active']
            and b['model'] == model == row['nativeModel']
            and b['deadeyeWorld'] == b['worldId']
            and b['begin'] == root['tick'] and b['script'] == root['instance']
            and fire['tick'] >= b['begin'] and 0 <= row['wall']-b['observed'] <= 150,
            'Actual firing proof mismatches root/model/source/world/deadline')


def check_locked_rows(rows, model):
    locked = [r for r in rows if r['body']['firing'] and r['nativeStates']['18']['active']]
    require(len(locked) >= 6, 'Insufficient actual locked samples; not an acceptance pass')
    for row in locked:
        check_firing_proof(row, model)
    anchor = locked[0]
    require(max(distance(anchor['mcPosition'], r['mcPosition']) for r in locked) < .06,
            'Confirmed firing allowed MC motion or F6 flight escape')
    require(max(angular(anchor['pose']['yaw'], r['pose']['yaw']) for r in locked) < .2
            and max(abs(anchor['pose']['pitch']-r['pose']['pitch']) for r in locked) < .2,
            'Confirmed firing allowed native camera rotation')
    require(all(r['player']['flying'] for r in locked), 'Locked F6 changed creative flight')


class Mappings:
    def __init__(self, pid):
        self.pid = pid
        self.body = GuestBindingScope()
        self.handle = self.view = None

    def read(self):
        # Reuse the existing read-only body mapping and its sequence guard.
        self.body.read(self.pid)
        kernel = self.body.kernel
        if self.view is None:
            self.handle = kernel.OpenFileMappingW(4, False, 'Local\\OWMCHostPose')
            require(self.handle, 'Current native host pose mapping absent')
            self.view = kernel.MapViewOfFile(self.handle, 4, 0, 0, 4096)
            require(self.view, 'Cannot map native host pose read-only')
        values = []
        for view, offset, size in ((self.body.view, 1536, 256), (self.view, 0, 4096)):
            for _ in range(5):
                seq = ctypes.string_at(view+offset+64, 8)
                data = ctypes.string_at(view+offset, size)
                if seq == data[64:72] == ctypes.string_at(view+offset+64, 8):
                    values.append(data)
                    break
            else:
                raise ValueError('Shared mapping changed during bounded read')
        now = round(time.time()*1000)
        return decode_body(values[0], self.pid, now), decode_pose(values[1], self.pid, now)

    def close(self):
        if self.view:
            self.body.kernel.UnmapViewOfFile(self.view)
        if self.handle:
            self.body.kernel.CloseHandle(self.handle)
        self.body.close()


class Suite:
    def __init__(self, args, folder, result):
        self.args, self.folder, self.result = args, folder, result
        self.driver = self.memory = self.maps = None
        self.recordings = []
        self.mutated = False
        self.model = None
        self.identity = Identity(args)
        self.result['identity'] = self.identity.proof
        modules = installed_modules(args.pid)
        owners = {k: str(v) for k, v in modules.items() if k.startswith('owmc-')}
        require(len(owners) == 6, 'Need exactly six existing unique native adapters')
        compositor = f'owmc-live-passthrough-v{args.compositor}.dll'
        require(compositor in modules, 'Required new compositor is not actually loaded')
        self.result['modules'] = {name: dict(path=path, sha256=digest(Path(path))) for name, path in owners.items()}
        self.driver = PersistentDrive(self.identity, folder, result['input'])
        self.result['driver'] = self.driver.proof
        self.client_size = tuple(map(int, self.driver.send('rect').split()[-2:]))
        client_command('click 1280 720', self.client_size)
        self.result['clientSize'] = list(self.client_size)
        self.driver.send('focus')  # Only this initial explicitly authorized focus.
        self.memory = ResearchProcess(args.pid)
        self.weapon = WeaponStates(self.memory)
        self.pose_reader = PoseReader(self.memory)
        self.maps = Mappings(args.pid)

    def save(self):
        (self.folder/'result.json').write_text(json.dumps(self.result, indent=2)+'\n', encoding='utf-8')

    def post(self, name):
        self.identity.health()
        require(self.driver.foreground(), 'Foreground interference; do not refocus')
        answer = request('combat/test/'+name, post=True)
        self.mutated = True
        return answer

    def choose(self, name):
        _, suffix, x = next(row for row in ROSTER if row[0] == name)
        require(tuple(map(int, self.driver.send('rect').split()[-2:])) == self.client_size,
                'Native client changed size; stop instead of guessing picker coordinates')
        if first_person_ready(self.args.pid):
            self.driver.send('hold 0x48 120')
            time.sleep(.65)
        self.driver.send(client_command(f'click {x} 1224', self.client_size))
        time.sleep(.65)
        self.driver.send(client_command('click 1280 1358', self.client_size))
        deadline = time.monotonic()+10
        while True:
            self.identity.health()
            actual = observe(self.args.pid)
            if actual['hero'] == 0x02E0000000000000+suffix and first_person_ready(self.args.pid):
                self.model = actual['modelId']
                time.sleep(.5)
                return actual
            require(time.monotonic() < deadline, 'Actual native selection failed: '+name)
            time.sleep(.1)

    def snapshot(self, phase, allow_menu=False):
        health = self.identity.health()
        require(self.driver.foreground(), 'Foreground interference; stop input')
        combat = request('combat')
        try:
            body, pose = self.maps.read()
        except GuestScopeExpired as error:
            # Expiration is not permission to accept another source/world. A
            # final-menu wait can observe again only under the established scope.
            expected = self.result.get('scope')
            require(expected and error.scope['sourcePid'] == self.args.mc_pid
                    and all(error.scope[k] == expected[k] for k in
                            ('sourcePid', 'guestGeneration', 'hostGeneration', 'worldId')),
                    'Expired body has another source/session/world')
            raise GuestBodyGap(f'Guest body expired: age={error.age}ms') from error
        require(body['sourcePid'] == self.args.mc_pid and body['hostGeneration'] == pose['generation'], 'Source/session changed')
        if 'scope' in self.result:
            require(all(body[k] == self.result['scope'][k] for k in ('sourcePid', 'hostGeneration', 'worldId')), 'World/source changed during single-world test')
        sample = self.weapon.sample_weapon(False, True)
        if not allow_menu:
            require(sample['modelId'] == self.model, 'Unplanned native model change')
        rows = {str(r['node']): dict(tick=r['nativeTick'], active=not r['finished'], instance=r['instanceAddress'])
                for r in sample['records'].values() if r['script'] == RESOURCE and r['node'] in (18, 44, 69)}
        states = {str(n): rows.get(str(n), dict(tick=0, active=False, instance=0)) for n in (18, 44, 69)}
        native_position = self.pose_reader.sample()
        p = health['player']
        row = dict(wall=round(time.time()*1000), phase=phase,
                   player=p, mcPosition=[p['x'], p['feetY'], p['z']],
                   mcYaw=combat.get('yaw'), mcPitch=combat.get('pitch'), body=body, pose=pose,
                   nativeModel=sample['modelId'], nativeStates=states,
                   nativePosition=native_position, deadeye=combat.get('deadeye', {}),
                   nativeCharge=combat.get('nativeCharge', {}), targetHealth=combat.get('targetHealth'),
                   targets=combat.get('beamTargets'), locomotion=combat.get('locomotion'))
        self.result['samples'].append(row)
        return row

    def wait(self, phase, predicate, seconds=5, allow_menu=False, retry_pose_gap=False):
        until = time.monotonic()+seconds
        while True:
            try:
                row = self.snapshot(phase, allow_menu)
            except (HostPoseGap, GuestBodyGap) as error:
                if not retry_pose_gap:
                    raise
                key = 'bodyWaitGaps' if isinstance(error, GuestBodyGap) else 'poseWaitGaps'
                self.result.setdefault(key, []).append(dict(
                    phase=phase, wall=round(time.time()*1000), error=str(error)))
                require(time.monotonic() < until, 'Deadline: '+phase+'; '+str(error))
                # Observe only: no extra H, focus, guessed lock or stale proof.
                time.sleep(.025)
                continue
            if predicate(row):
                return row
            require(time.monotonic() < until, 'Deadline: '+phase)
            time.sleep(.025)

    def trace(self, phase, commands, minimum=.1, allow_menu=False):
        errors = []
        stop = threading.Event()
        def execute():
            try:
                for cmd in commands:
                    if stop.is_set():
                        return
                    self.driver.send(client_command(cmd, self.client_size))
            except Exception as error:
                errors.append(error)
        worker = threading.Thread(target=execute, daemon=True)
        worker.start()
        began = time.monotonic()
        rows = []
        try:
            while worker.is_alive() or time.monotonic()-began < minimum:
                rows.append(self.snapshot(phase, allow_menu))
                require(time.monotonic()-began < 8, 'Bounded input trace exceeded 8 seconds')
                time.sleep(.025)
        finally:
            stop.set()
            worker.join(6)
        require(not worker.is_alive(), 'Input helper did not finish')
        if errors:
            raise errors[0]
        return rows

    def aim(self):
        for _ in range(6):
            c = request('combat')
            delta = (180-c['yaw']+180) % 360-180
            if abs(delta) < 1 and abs(c['pitch']) < 1:
                return
            self.driver.send(f'rel {round(delta/.1)} {round(-c["pitch"]/.1)}')
            time.sleep(.2)
        raise ValueError('Could not obtain a horizontal view')

    def grant(self):
        if self.args.grant == 'typed':
            self.identity.quick()
            self.result['grants'].append(grant_for_test(self.memory, self.args.pid))
        else:
            before = request('combat').get('nativeCharge')
            self.driver.send('key 0x7A')  # F11, explicitly diagnostic.
            time.sleep(.25)
            self.result['grants'].append(dict(method='F11', diagnostic=True, before=before,
                                             after=request('combat').get('nativeCharge')))

    def cast(self, phase):
        before = self.snapshot(phase+'-before')
        self.grant()
        self.driver.send('hold 0x51 120')
        return self.wait(phase+'-began', lambda r: r['nativeStates']['18']['active']
                         and r['nativeStates']['18']['tick'] > before['nativeStates']['18']['tick']
                         and r['deadeye'].get('active') and not r['body']['firing'], 5)

    def record(self, name, seconds):
        prefix = self.folder/name
        proc = subprocess.Popen(['um', 'win', 'record', '--pid', str(self.args.mc_pid),
                                 '--exe', 'GameClientApp.patched.exe',
                                 '--out', str(prefix), '--seconds', str(seconds), '--fps', '60'],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        self.recordings.append((name, proc))
        time.sleep(.8)

    def air_crowd(self):
        if not self.identity.health()['player']['flying']:
            self.driver.send('key 0x75')
            self.wait('enable-air-fixture', lambda r: r['player']['flying'], 2)
        self.aim()
        self.post('deadeye-crowd')
        self.wait('crowd-ready', lambda r: r['targets'] is not None and len(r['targets']) == 12, 2)
        require(not request('combat').get('testError'), 'Deadeye crowd fixture refused')

    def fire(self, phase):
        self.wait(phase+'-locked-targets', lambda r: r['deadeye'].get('readyLocks', 0) >= 12, 5)
        self.driver.send(client_command('mdown 1280 720', self.client_size))
        self.driver.send('mup')
        row = self.wait(phase+'-real-fire', lambda r: r['body']['firing'] and r['deadeye'].get('fired')
                        and r['nativeStates']['18']['active'] and r['nativeStates']['44']['tick'] >= r['body']['begin'], 2)
        check_firing_proof(row, self.model)
        return row

    def run(self):
        self.result['selection'] = [self.choose('Genji'), self.choose('McCree')]
        self.aim()
        row = self.wait('settled', lambda r: r['pose']['capabilities'] == DEY1
                        and r['pose']['inputActive'] and not r['body']['firing'], 8)
        self.result['scope'] = {k: row['body'][k] for k in ('sourcePid', 'hostGeneration', 'guestGeneration', 'worldId')}
        compositor = report(ROOT/f'native-host/build/world-live-{self.args.pid}.json')
        require(compositor.get('probeVersion') == self.args.compositor and compositor.get('deadeyeInputGuardAvailable')
                and not compositor.get('failures'), 'Actual compositor input guard unavailable')
        self.result['compositorBefore'] = compositor
        # A temporary lane is built only in verified empty air. Crowd later
        # removes that floor, so enable creative flight before creating targets.
        self.post('flight-open')
        time.sleep(.35)
        self.post('roll-lane')
        time.sleep(.2)
        require(not request('combat').get('testError'), 'Reversible ground lane refused')
        self.driver.send('key 0x75')
        self.wait('grounded-lane', lambda r: r['player']['onGround'] and not r['player']['flying'], 3)
        charging = self.cast('charging')
        probe = self.trace('charging-motion', ['key 0x57 down', 'rel 40 0', 'sleep 400', 'key 0x57 up', 'rel -40 0'], .6)
        require(all(not r['body']['firing'] for r in probe), 'Charging incorrectly entered firing lock')
        require(max(distance(charging['mcPosition'], r['mcPosition'], True) for r in probe) > .12,
                'Charging did not permit actual ground walking')
        require(max(angular(charging['pose']['yaw'], r['pose']['yaw']) for r in probe) > 2,
                'Charging did not permit actual native camera rotation')
        self.driver.send(client_command('click 1280 720 right', self.client_size))
        self.wait('charging-cancel-root-End', lambda r: not r['nativeStates']['18']['active'] and not r['body']['firing'], 5)
        self.result['chargingPassed'] = True
        self.air_crowd()
        self.record('native-composed-lock', 18)
        self.cast('complete')
        fired = self.fire('complete')
        # Allow the first admitted lock frame to consume already queued motion.
        self.wait('lock-settle', lambda r: r['wall'] >= fired['wall']+100 and r['body']['firing'], .8)
        rows = self.trace('firing-input', ['key 0x57 down', 'key 0x10 down', 'key 0x20 down',
                          'key 0x75 down', 'key 0x75 up', 'rel 220 70', 'sleep 450',
                          'key 0x57 up', 'key 0x10 up', 'key 0x20 up', 'rel -160 -50'], .65)
        check_locked_rows(rows, self.model)
        ended = self.wait('complete-original-End', lambda r: not r['nativeStates']['18']['active'] and not r['body']['firing'], 7)
        idle = self.trace('after-End-idle', ['sleep 550'], .6)
        require(max(distance(ended['mcPosition'], r['mcPosition']) for r in idle) < .04,
                'Old motion/roll replayed after original End')
        require(all(not r['body']['firing'] for r in idle), 'Firing proof replayed after End')
        recovered = self.trace('after-End-move-view', ['key 0x57 down', 'rel 60 0', 'sleep 350', 'key 0x57 up'], .5)
        require(max(distance(idle[-1]['mcPosition'], r['mcPosition'], True) for r in recovered) > .12
                and max(angular(idle[-1]['pose']['yaw'], r['pose']['yaw']) for r in recovered) > 2,
                'Movement/view did not recover after original End')
        self.aim()
        self.post('start')
        self.wait('ordinary-target', lambda r: r['targetHealth'] == 20, 2)
        self.trace('ordinary-after-End', ['mdown 1280 720', 'sleep 80', 'mup'], .4)
        self.wait('ordinary-hit-after-End', lambda r: r['targetHealth'] is not None and r['targetHealth'] < 20, 2)
        self.result['nativeEndPassed'] = True
        self.air_crowd()
        self.record('native-H-interrupt', 10)
        self.cast('interrupt')
        self.fire('interrupt')
        self.driver.send('hold 0x48 100')
        menu = self.wait('H-menu-unlocked', lambda r: not r['body']['firing'] and not r['pose']['inputActive'],
                         3, True, retry_pose_gap=True)
        require(not first_person_ready(self.args.pid), 'H did not reach the original hero picker')
        self.result['HInterruptPassed'] = True
        self.result['menuProof'] = menu
        self.result['featurePassed'] = True
        # Stay at the native picker. Only the owned MC fixture is removed.

    def close(self):
        try:
            if self.driver and self.driver.foreground():
                for key in ('0x57', '0x10', '0x20', '0x75'):
                    self.driver.send('key '+key+' up')
                self.driver.send('mup')
                if self.mutated:
                    # The guarded production cleanup route queues work only
                    # while a real first-person host pose is active. HTTP202
                    # at the picker does not prove that any scene was cleared.
                    # Reenter solely after this suite's accepted H interruption;
                    # never replace a failed native pawn to manufacture a pass.
                    return_to_picker = bool(self.result.get('featurePassed')
                                            and self.result.get('HInterruptPassed')
                                            and not first_person_ready(self.args.pid))
                    if return_to_picker:
                        self.identity.health()
                        require(self.driver.foreground(), 'Cleanup reentry lost foreground; do not refocus')
                        self.result['cleanupReentry'] = self.choose('McCree')
                        self.result['cleanupScope'] = self.wait('cleanup-first-person-scope',
                            lambda r: r['pose']['inputActive'] and not r['body']['firing']
                            and r['nativeModel'] == self.model
                            and (r['locomotion'] or {}).get('ready')
                            and (r['locomotion'] or {}).get('modelId') == self.model, 6)
                        require(first_person_ready(self.args.pid), 'Cleanup reentry lacks original first person')
                    self.post('cleanup')
                    deadline = time.monotonic()+3
                    while True:
                        self.identity.health()
                        require(self.driver.foreground(), 'Cleanup observation lost foreground; do not refocus')
                        c = request('combat')
                        self.result['cleaned'] = c.get('wallBlocks') == 0 and not c.get('beamTargets') and 'targetHealth' not in c
                        self.result['cleanupObserved'] = dict(wallBlocks=c.get('wallBlocks'),
                            beamTargets=c.get('beamTargets'), targetHealth=c.get('targetHealth'),
                            targetPresent='targetHealth' in c)
                        if self.result['cleaned']:
                            break
                        require(time.monotonic() < deadline, 'HTTP cleanup was queued but owned scene remains')
                        time.sleep(.05)
                    if return_to_picker:
                        self.driver.send('hold 0x48 100')
                        self.result['finalPickerProof'] = self.wait('final-picker-after-cleanup',
                            lambda r: not r['body']['firing'] and not r['pose']['inputActive'],
                            3, True, retry_pose_gap=True)
                        require(not first_person_ready(self.args.pid), 'Cleanup did not return to original picker')
                        self.result['finalPicker'] = True
            elif self.mutated:
                self.result['cleanupError'] = 'Foreground interference; preserved scene instead of refocusing'
        finally:
            for name, proc in self.recordings:
                try:
                    stdout, stderr = proc.communicate(timeout=30)
                    videos = [str(p) for p in self.folder.glob(name+'*') if p.suffix.lower() in ('.mp4', '.mkv') and p.stat().st_size > 0]
                    self.result.setdefault('videos', []).append(dict(name=name, exitCode=proc.returncode, files=videos,
                                                                      stdout=stdout.decode(errors='replace')[-1000:], stderr=stderr.decode(errors='replace')[-1000:]))
                except Exception as error:
                    self.result.setdefault('recordingErrors', []).append(repr(error))
            if self.maps:
                self.maps.close()
            if self.memory:
                self.memory.close()
            if self.driver:
                self.driver.close()
            self.save()


def main(args):
    folder = args.output.resolve()
    require((ROOT/'research').resolve() in folder.parents, 'Use a fresh private research output directory')
    folder.mkdir(parents=True, exist_ok=False)
    result = dict(passed=False, featurePassed=False, cleaned=False, input=[], samples=[], grants=[],
                  explicitLabGrants=True, naturalChargeAcceptance=False, visualAcceptance='pending root video review',
                  worldScope='single verified isolated Switch world; no world-load or user-save overwrite',
                  profileBackupAcknowledged=args.profile_backed_up)
    suite = None
    try:
        require(args.profile_backed_up, 'Root must first back up the current disposable profile')
        suite = Suite.__new__(Suite)
        suite.__init__(args, folder, result)
        suite.run()
    except Exception as error:
        result['error'] = repr(error)
        if suite:
            try:
                result['failureCompositor'] = report(ROOT/f'native-host/build/world-live-{args.pid}.json')
            except Exception as secondary:
                result['failureReportError'] = repr(secondary)
    finally:
        if suite:
            try:
                suite.close()
            except Exception as error:
                result['closeError'] = repr(error)
        video_ok = any(r.get('exitCode') == 0 and r.get('files') for r in result.get('videos', []))
        result['passed'] = bool(result['featurePassed'] and result['cleaned'] and video_ok
                                and not result.get('error') and not result.get('closeError'))
        (folder/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({k: result.get(k) for k in ('passed', 'featurePassed', 'chargingPassed', 'nativeEndPassed', 'HInterruptPassed', 'cleaned', 'error', 'closeError')}), flush=True)
    return result['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name, kind in [('pid', int), ('created', float), ('mc-pid', int), ('mc-created', float), ('world', str), ('guest-sha256', str)]:
        parser.add_argument('--'+name, required=True, type=kind)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--compositor', type=int, default=41)
    parser.add_argument('--grant', choices=('typed', 'f11'), default='typed')
    parser.add_argument('--profile-backed-up', action='store_true', help='Explicit operator acknowledgment; this script never backs up/overwrites saves')
    raise SystemExit(0 if main(parser.parse_args()) else 1)
