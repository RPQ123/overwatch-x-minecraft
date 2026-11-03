"""Positive native picker proof and bounded hero switching; no camera writes.

The default first-person camera and the animated picker are different native
types. An ability camera is neither. Never infer an open picker from !FPS.
"""
from __future__ import annotations

import time
from observe_overwatch import ResearchProcess, PoseReader


def native_view_state(pid):
    process = ResearchProcess(pid)
    try:
        reader = PoseReader(process)
        admin = reader.pointer(process.base + 0x17b7f90)
        items = reader.pointer(admin + 0xb0)
        pointers, count, capacity = reader.unpack('<Qii', items + 0x4f * 24)
        if not 1 <= count <= capacity <= 256:
            raise ValueError('Native camera list bounds changed')
        component = reader.pointer(pointers)
        camera = reader.pointer(component + 0x40)
        active = reader.pointer(camera + 0x260)
        default = reader.pointer(component + 0x50)
        vtable = reader.pointer(active)
        # Same positive types as pose_observer.cpp::nativeViewMode(). Mode0
        # deliberately remains unconfirmed (barrier/charge/other camera).
        mode = (1 if active == default and vtable == process.base + 0x15c7000
                else 2 if vtable == process.base + 0x15f2cf8 else 0)
        if (reader.pointer(process.base + 0x17b7f90) != admin
                or reader.pointer(camera + 0x260) != active):
            raise ValueError('Native camera changed during read')
        return dict(viewMode=mode, activeCamera=active, defaultCamera=default,
                    cameraVtableRva=vtable-process.base)
    finally:
        process.close()


def choose(suite, name, *, timeout=10):
    """Suite.choose replacement; callers retain exact identity/input ownership.

    An unknown camera gets one normal H request and must prove picker mode2
    before any click. H is never blindly toggled twice. No pointer, attack or
    camera state is fabricated. Failure retains numeric before/after evidence.
    """
    from calibrate_hero_roster import ROSTER, observe
    from verify_deadeye_input_lock import client_command

    suffix, x = next((suffix, x) for hero, suffix, x in ROSTER if hero == name)
    diagnostic = dict(target=name, samples=[], hRequested=False)
    suite.result.setdefault('selectionDiagnostics', []).append(diagnostic)

    def sample():
        suite.identity.health()
        if not suite.driver.foreground():
            raise ValueError('Foreground/input interference during native selection')
        size = tuple(map(int, suite.driver.send('rect').split()[-2:]))
        if size != suite.client_size:
            raise ValueError('Native client size changed')
        state = native_view_state(suite.args.pid)
        actor = observe(suite.args.pid)
        row = {**state, 'hero': actor.get('hero'), 'modelId': actor.get('modelId')}
        if not diagnostic['samples'] or row != diagnostic['samples'][-1]:
            diagnostic['samples'].append(row)
            diagnostic['samples'] = diagnostic['samples'][-24:]
        return state, actor

    def wait_mode(mode, hero=None):
        deadline = time.monotonic() + timeout
        while True:
            state, actor = sample()
            if state['viewMode'] == mode and (hero is None or actor['hero'] == hero):
                return actor
            if time.monotonic() >= deadline:
                raise ValueError(f'Native selection did not settle: {name}; expected mode={mode}; last={diagnostic["samples"][-1]}')
            time.sleep(.1)

    try:
        state, _ = sample()
        if state['viewMode'] != 2:
            suite.driver.send('hold 0x48 150')
            diagnostic['hRequested'] = True
            wait_mode(2)
        # Wait for the actual native menu transition before selecting anything.
        time.sleep(.65)
        state, _ = sample()
        if state['viewMode'] != 2:
            raise ValueError('Native picker closed before hero click')
        suite.driver.send(client_command(f'click {x} 1224', suite.client_size))
        time.sleep(.65)
        state, _ = sample()
        if state['viewMode'] != 2:
            raise ValueError('Native picker closed before confirmation')
        suite.driver.send(client_command('click 1280 1358', suite.client_size))
        actor = wait_mode(1, 0x02e0000000000000 + suffix)
        time.sleep(.5)
        diagnostic['passed'] = True
        return actor
    except Exception as error:
        diagnostic.update(passed=False, error=repr(error))
        raise
    finally:
        suite.save()
