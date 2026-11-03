"""Pure verdict/planning helpers for Junkrat verification; no process or input access."""
import math


class DeferredSkill(Exception):
    def __init__(self,reason,evidence=None):
        super().__init__(reason);self.evidence=evidence or {}


def plan(mode='base'):
    if mode=='all':return ('base','passive','tire','wall')
    if mode not in ('base','passive','tire','wall'):raise ValueError('unknown Junkrat mode: '+str(mode))
    return (mode,)


def gain(before,after,key):
    a,b=before.get(key),after.get(key)
    return isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool) and math.isfinite(a) and math.isfinite(b) and b>a


def base_verdict(steps):
    checks={}
    for name,required in [('grenade',('grenades','explosions','damageApplied')),('trap',('traps',)),('mine',('mines',)),('detonate',('detonations','explosions'))]:
        row=steps.get(name,{})
        if name=='grenade':before=row.get('before',{})
        elif 'before' in row:before=row['before']
        else:
            # Legacy B11 artifacts used one baseline for all four stages.
            before=steps.get('grenade',{}).get('before',{})
        after=row.get('after') or {}
        ok=all(gain(before,after,key) for key in required)
        if name=='grenade':
            hp=row.get('hp') or []
            ok=ok and len(hp)==2 and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in hp) and hp[1]<hp[0]
        checks[name]='PASS' if ok else 'FAIL'
    return dict(status='PASS' if all(s=='PASS' for s in checks.values()) else 'FAIL',checks=checks)


def creation_verdict(before,after,native_before=None,native_after=None):
    q0=before.get('tire') or {};q1=after.get('tire') or {}
    if gain(q0,q1,'casts') and q1.get('active'):return dict(status='PASS',reason='actual MC tire admitted')
    signals0=before.get('signals') or {};signals1=after.get('signals') or {}
    native_observed=gain(signals0,signals1,'tireCreateEvents')
    if native_before and native_after and not native_before.get('error') and not native_after.get('error'):
        if native_before.get('modelId')==native_after.get('modelId'):
            native_observed=native_observed or gain(native_before,native_after,'createTick')
    if gain(q0,q1,'castAttempts') or native_observed:
        return dict(status='FAIL',reason='native create observed or MC cast attempted, but no active tire',rejection=q1.get('lastCastRejection'))
    return dict(status='DEFERRED',reason='no authenticated fresh create32 admission observed; inspect native/binding evidence')


def outcome(cases,cleaned,error=None,cleanup_error=None):
    if error or cleanup_error or not cleaned or any(c.get('status')=='FAIL' for c in cases.values()):return 'FAIL',1
    if not cases or any(c.get('status')!='PASS' for c in cases.values()):return 'BLOCKED',2
    return 'PASS',0
