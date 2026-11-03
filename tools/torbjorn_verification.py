"""Torbjorn stage verdicts and bounded read-only calibration snapshots."""
import time
import traceback

from junkrat_verification import gain as changed


def calibration_snapshot(reader,model,failures,phase,check,*,local=None,pause=time.sleep):
    """Discard a torn Map read and retry the WHOLE sample, at most three times.

    The returned gap flag forces the caller to rebase edges. A recovered gap
    still fails capture quality; no new input/grant is repeated by this helper.
    Other errors and any identity change remain immediate failures.
    """
    for attempt in range(1,4):
        check()
        try:sample=reader.sample_weapon(False,True)
        except ValueError as error:
            if str(error)!='Map cycle or count mismatch':raise
            frames=traceback.extract_tb(error.__traceback__)
            failure=dict(phase=phase,attempt=attempt,error=str(error),stack=[dict(file=f.filename,line=f.lineno,function=f.name) for f in frames])
            cursor=error.__traceback__
            while cursor:
                frame=cursor.tb_frame
                if frame.f_code.co_name=='snapshot_map':
                    values=frame.f_locals
                    failure['map']={key:values.get(key) for key in ('address','key_format','head','count','root','node')}
                    failure['map']['visited']=len(values.get('seen',()))
                cursor=cursor.tb_next
            failures.append(failure)
            if attempt==3:raise
            pause(.04);continue
        if sample.get('modelId')!=model or local is not None and sample.get('localId')!=local:
            raise ValueError('Calibration native model/controller changed')
        return sample,attempt>1


def hammer_verdict(before,after,native_before=None,native_after=None):
    if changed(before,after,'hammerSwings'):return dict(status='PASS',reason='MC admitted actual native hammer signal')
    observed=changed(before.get('signals') or {},after.get('signals') or {},'hammerRequests')
    if native_before and native_after and native_before.get('modelId')==native_after.get('modelId'):
        observed=observed or changed(native_before,native_after,'strikeTick')
    if observed:return dict(status='FAIL',reason='native hammer strike observed but no MC admission')
    return dict(status='BLOCKED',reason='no authenticated fresh f3:24 hammer strike; selection/cosmetic states are insufficient')


def deployment_verdict(before,after):
    if changed(before,after,'deploys') and after.get('turret'):return dict(status='PASS')
    if changed(before,after,'deployAttempts') or changed(before.get('signals') or {},after.get('signals') or {},'deployRequests'):
        return dict(status='FAIL',reason='MC placement attempted but no turret',rejection=after.get('lastDeployRejection'))
    return dict(status='BLOCKED',reason='no authenticated placement admission observed; inspect f4 anim/ghost and binding diagnostics')


def calibration_signals(result):
    nodes=result.get('changedNodesByPhase') or {}
    return dict(calibrationOnly=True,mcSkillAcceptance=False,
        hammerCommitObserved='05800000000000f3:24' in nodes.get('hammer-swing',[]),
        placementAnimationObserved='05800000000000f4:29' in nodes.get('shift-turret',[]))
