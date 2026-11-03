"""Pure acceptance assertions for actual body displacement/native camera samples."""
import math


def angular(a,b):return abs((a-b+180)%360-180)


def dragon_render_snapshot(combat):
    """Missing diagnostics are unknown, never the zero value of a live counter.

    Each successful twin body submission increments exactly one of skinDraws /
    skinFallbackDraws and dragonDraws. Arrow draws increment neither skin count.
    """
    def counter(key):
        value=combat.get(key)
        return value if isinstance(value,int) and not isinstance(value,bool) and value>=0 else None
    explicit=counter('hanzoDragonDraws');skin=counter('hanzoDragonSkinDraws');fallback=counter('hanzoDragonSkinFallbackDraws')
    if explicit is not None:draws,source=explicit,'hanzoDragonDraws'
    elif skin is not None and fallback is not None:draws,source=skin+fallback,'hanzoDragonSkinDraws+hanzoDragonSkinFallbackDraws'
    else:draws,source=None,'unavailable'
    return dict(available=draws is not None,bodyDraws=draws,source=source,
                explicitBodyDraws=explicit,skinDraws=skin,skinFallbackDraws=fallback,
                arrowFrames=counter('hanzoDragonArrowFrames'),frames=counter('hanzoDragonRendererFrames'),
                errors=counter('hanzoDragonRendererErrors'),error=combat.get('hanzoDragonRendererError'),
                missing=[k for k in ['hanzoDragonDraws','hanzoDragonSkinDraws','hanzoDragonSkinFallbackDraws','hanzoDragonArrowFrames'] if k not in combat])


def dragon_draw_contract(before, current, dragons):
    if not before['available'] or not current['available']:
        return dict(passed=False,status='BLOCKED',reason='Dragon body draw diagnostics unavailable; no missing-key-to-zero substitution',bodyDrawDelta=None)
    if before['source']!=current['source']:
        return dict(passed=False,status='FAIL',reason='Dragon counter source changed during one test',bodyDrawDelta=None)
    difference=current['bodyDraws']-before['bodyDraws']
    if difference<0:return dict(passed=False,status='FAIL',reason='Dragon body counter reset during one test',bodyDrawDelta=difference)
    error_delta=None if before['errors'] is None or current['errors'] is None else current['errors']-before['errors']
    if error_delta is not None and error_delta>0:
        return dict(passed=False,status='FAIL',reason='Dragon renderer added errors: '+str(current['error']),bodyDrawDelta=difference,errorDelta=error_delta)
    passed=dragons>0 and difference>0
    return dict(passed=passed,status='PASS' if passed else 'WAIT',bodyDrawDelta=difference,errorDelta=error_delta,
                reason='new body mesh submissions' if passed else 'no new live Dragon body mesh submission yet',source=current['source'])


def control_contract(rows, actual_cast):
    """Require physical suppression and recovery, with two explicit same-cast receipts."""
    def ranges(samples):
        moved=max((math.dist(a['position'],b['position']) for a in samples for b in samples),default=0)
        yaw=max((angular(a['mcYaw'],b['mcYaw']) for a in samples for b in samples),default=0)
        pitch=max((abs(a['mcPitch']-b['mcPitch']) for a in samples for b in samples),default=0)
        native_yaw=max((angular(a['nativeYaw'],b['nativeYaw']) for a in samples for b in samples),default=0)
        native_pitch=max((abs(a['nativePitch']-b['nativePitch']) for a in samples for b in samples),default=0)
        return dict(displacement=moved,mcYawRange=yaw,mcPitchRange=pitch,nativeYawRange=native_yaw,nativePitchRange=native_pitch)
    locked=[r for r in rows if r['phase']=='locked'];restored=[r for r in rows if r['phase']=='recovered']
    a,b=ranges(locked),ranges(restored)
    begin=locked[0]['controls'].get('nativeBegin',0) if locked else 0
    release=restored[0]['controls'] if restored else {}
    start=locked[0]['controls'].get('startedWall',0) if locked else 0
    end=release.get('nativeEndWall',0);dragon=release.get('releasedWall',0)
    release_wall=restored[0]['wall']*1000 if restored else 0
    native_frames=[r.get('nativeInput',{}).get('hanzoMotionFrames') for r in locked]
    native_frames=[v for v in native_frames if isinstance(v,int) and not isinstance(v,bool)]
    checks=dict(actualNativeCast=actual_cast,sampledLock=len(locked)>=2,sampledRecovery=len(restored)>=4,
                sameCast=begin>0 and all(r['controls'].get('nativeBegin')==begin for r in locked) and all(r['controls'].get('nativeBegin') in (begin,0) for r in restored),
                lockedMotion=a['displacement']<=.06,lockedYaw=a['mcYawRange']<=.25,lockedPitch=a['mcPitchRange']<=.25,
                nativeMouseSuppressed=a['nativeYawRange']<=.3 and a['nativePitchRange']<=.3,
                velocityZero=bool(locked) and all(math.dist(r['velocity'],[0,0,0])<=.001 for r in locked),
                drivenDuringLock=bool(locked) and all(r.get('driving') for r in locked),
                nativeProtocol=bool(locked) and all(r.get('nativeInput',{}).get('hanzoControlProtocol')==2 for r in locked),
                nativeFilterReceipt=any(r.get('nativeInput',{}).get('hanzoMotionLocked') is True for r in locked),
                nativeFilterFrames=bool(native_frames) and max(native_frames)>min(native_frames),
                dragonReleasedReceipt=dragon>=start>0,
                waitedForRelease=bool(restored) and release_wall>=dragon>0,
                noEarlyUnlock=bool(locked) and all(r['controls'].get('locked') for r in locked),
                releasePrompt=bool(restored) and 0<=release_wall-dragon<=300,
                restoredMotion=b['displacement']>=.4,restoredYaw=b['nativeYawRange']>=2,restoredPitch=b['nativePitchRange']>=1,
                mcFollowsNative=bool(restored) and all(angular(r['mcYaw'],r['nativeYaw'])<3 and abs(r['mcPitch']-r['nativePitch'])<3 for r in restored),
                noRelock=bool(restored) and all(not r['controls'].get('locked') for r in restored),
                dragonBodyDraw=any((r.get('dragonDrawEvidence') or {}).get('passed') for r in rows))
    return dict(passed=all(checks.values()),assertions=checks,locked=a,recovered=b,
                duration=dict(nativeCastMillis=release.get('nativeCastMillis'),observedLockMillis=release.get('lockMillis'),
                              beginWall=start,nativeEndWall=end,dragonReleasedWall=dragon,firstUnlockedWall=release_wall),
                castScope='original graph0101:19 Begin until the same-cast dragon is released (like McCree ult lock); MC adaptation requested by user')
