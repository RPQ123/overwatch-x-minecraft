"""Numeric checks and dependency-injected test selection; no process access."""
import time

MEI = 0x02E00000000000DD
WINSTON = 0x02E0000000000009
CRYO_SETTLE_SECONDS = 15.0  # Test isolation margin, NOT a claimed native cooldown.
MELEE_SETTLE_SECONDS = 2.5  # Test pacing after actual TrackTargets End.


def node_record(row, node):
    return next((r for r in (row.get('native') or {}).get('records', []) if r['node'] == node), None)


def melee_progress(before, after):
    """Distinguish a refused native input, missed admission, and real MC damage.

    sustain.hero=0 is expected on Winston and is deliberately never consulted.
    A newer *finished* TrackTargets timestamp can diagnose a missed execution;
    it cannot authorize a production attack or certify a hit.
    """
    actor = after.get('native') or {}
    prior_actor = before.get('native') or {}
    if actor.get('hero') != WINSTON or actor.get('modelId') != prior_actor.get('modelId'):
        return 'native-owner-changed'
    old, new = node_record(before, 13), node_record(after, 13)
    if new is None or new['nativeTick'] <= (old or {}).get('nativeTick', 0):
        return 'no-new-native-TrackTargets'
    b, a = before.get('melee') or {}, after.get('melee') or {}
    if a.get('accepted', 0) <= b.get('accepted', 0):
        return 'native-TrackTargets-without-client-admission'
    if a.get('heroId') != WINSTON:
        return 'wrong-runtime-owner'
    if a.get('hits', 0) <= b.get('hits', 0):
        return 'accepted-without-target-hit'
    hp0, hp1 = before.get('targetHealth'), after.get('targetHealth')
    if (not isinstance(hp0, (int, float)) or not isinstance(hp1, (int, float)) or hp1 >= hp0
            or a.get('damageApplied', 0) <= b.get('damageApplied', 0)):
        return 'hit-without-real-HP-damage'
    return 'actual-MC-damage'


def timed_native_switch(read_state, send, validate, hero_click, confirm_click,
                        target_hero, old_model, deadline, trace, *, now=time.monotonic, sleep=time.sleep):
    """Bounded selection with the same positive camera gates as Suite.choose.

    The caller supplies guarded input. Return when the actual new FPS model is
    observed, rather than charging Suite's post-selection delay against Cryo.
    No click is allowed without a positive native picker; H is sent at most once.
    """
    def read():
        validate()
        if now() >= deadline:
            raise ValueError('mid-Cryo native selection exceeded the 3s deadline')
        state = read_state()
        trace.append(dict(state, observedAt=now()))
        if now() >= deadline:
            raise ValueError('mid-Cryo native selection exceeded the 3s deadline')
        return state

    def wait_for(predicate):
        while True:
            state = read()
            if predicate(state):
                return state
            sleep(.05)

    state = read()
    if state['viewMode'] != 2:
        send('hold 0x48 150')
        wait_for(lambda v: v['viewMode'] == 2)
    sleep(.65)
    if read()['viewMode'] != 2:
        raise ValueError('native picker closed before mid-Cryo hero click')
    send(hero_click)
    sleep(.65)
    if read()['viewMode'] != 2:
        raise ValueError('native picker closed before mid-Cryo confirmation')
    send(confirm_click)
    return wait_for(lambda v: v['viewMode'] == 1 and v['hero'] == target_hero and v['modelId'] != old_model)
