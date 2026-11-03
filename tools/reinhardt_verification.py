"""Pure numeric evidence classification; never reads inputs or creates effects."""


class NativeEvidenceBlocked(RuntimeError):
    pass


def snapshot(combat):
    keys = ('reinhardt', 'reinhardtError', 'locomotion', 'testError', 'heroLab',
            'shieldProbe', 'targetHealth', 'yaw', 'pitch')
    return {key: combat[key] for key in keys if key in combat}


def gain(before, samples, counter):
    base = before.get('reinhardt', {}).get(counter, 0)
    return max([0, *[c.get('reinhardt', {}).get(counter, base) - base for c in samples]])


def node_begin(before, samples, key):
    old = before.get('reinhardt', {}).get('nativeCandidates', {}).get(key)
    if not old or not old.get('readable'):
        return False
    return any((n := c.get('reinhardt', {}).get('nativeCandidates', {}).get(key))
               and n.get('readable') and n.get('begins', 0) > old.get('begins', 0) for c in samples)


def volley_commit(before, samples, key):
    old = before.get('reinhardt', {}).get('nativeCandidates', {}).get(key)
    if not old or not old.get('readable') or old.get('active'):
        return False
    return any((n := c.get('reinhardt', {}).get('nativeCandidates', {}).get(key))
               and n.get('readable') and n.get('tick', 0) > old.get('tick', 0)
               and (n.get('begins', 0) > old.get('begins', 0)
                    or n.get('ends', 0) > old.get('ends', 0)) for c in samples)


def signal_outcome(case, before, samples):
    if case == 'reinhardt-charge':
        observed = node_begin(before, samples, 'charge.movement')
        reason = 'No native TrackMovement6 Begin; animation attempt is not charge movement/impact'
    elif case == 'reinhardt-fire':
        observed = volley_commit(before, samples, 'fire.volley')
        reason = 'No fresh native FireStrike Volley3 commit'
    elif case == 'reinhardt-shatter':
        observed = node_begin(before, samples, 'shatter.shockwave')
        reason = 'No native Shockwave1 Begin'
    else:
        raise ValueError('Unknown Reinhardt signal case: ' + case)
    return dict(status='PASSED' if observed else 'BLOCKED', nativeCommitObserved=observed,
                reason='Native signal observed; MC effect acceptance remains false' if observed else reason,
                effectAccepted=False)


def barrier_outcome(before, samples):
    begins = node_begin(before, samples, 'barrier.pet')
    casts = gain(before, samples, 'barrierCasts')
    plane = any(c.get('reinhardt', {}).get('barrierActive')
                and c['reinhardt'].get('barrierBlocks', 0) > 0 for c in samples)
    evidence = dict(nativePetBegin=begins, admittedCasts=casts, mcPlaneObserved=plane,
                    nativeButtonStateVerified=False, nativeCooldownVerified=False)
    if not begins and casts == 0:
        if plane:
            return dict(status='FAILED', reason='MC barrier appeared without a new native admission', **evidence)
        return dict(status='BLOCKED', reason='No fresh original Pet58 Begin/admission; MC plane implementation not exercised', **evidence)
    if casts != 1:
        return dict(status='FAILED', reason='Native Pet58 Begin was not admitted exactly once', **evidence)
    if not plane:
        return dict(status='FAILED', reason='Native barrier admitted, but no real MC barrier plane was generated', **evidence)
    # Arrow collision and removal still need separate checks before acceptance.
    return dict(status='READY', reason='Native admission and MC plane observed; verify arrows and removal', **evidence)


def attempt_outcome(before, samples):
    begins = node_begin(before, samples, 'charge.anim')
    attempts = gain(before, samples, 'chargeAttempts')
    evidence = dict(nativeAnimationBegin=begins, admittedAttempts=attempts,
                    movementBegin=node_begin(before, samples, 'charge.movement'), impactAccepted=False)
    if attempts > 0:
        return dict(status='PASSED', reason='Native animation attempt observed; no movement/impact acceptance implied', **evidence)
    if begins:
        return dict(status='FAILED', reason='Native animation Begin observed but attempt counter did not advance', **evidence)
    return dict(status='BLOCKED', reason='No fresh original Shift animation110 Begin/admission', **evidence)


def result_code(result):
    if result.get('cleanupError') or not result.get('cleaned') or result.get('error'):
        return 1
    if result.get('status') == 'BLOCKED' and not result.get('passed'):
        return 2
    return 0 if result.get('passed') else 1
