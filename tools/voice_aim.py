"""语音抽查的只读就绪条件；狂鼠捕兽夹走独立控制器，不依赖主武器发射器。"""
import math


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def aim_readiness(combat,native,hero,model,name):
    loco=combat.get('locomotion') or {}
    voice=combat.get('heroVoice') or {}
    signals=(combat.get('junkrat') or {}).get('signals') or {}
    trap=signals.get('trap') or {}
    independent=name=='Junkrat'
    checks=dict(angles=finite(combat.get('yaw')) and finite(combat.get('pitch')),
                locomotion=loco.get('ready') is True,
                locomotionHero=loco.get('hero')==hero,
                locomotionModel=model!=0 and loco.get('modelId')==model,
                world=loco.get('worldId',0)!=0,
                voiceHero=voice.get('hero')==name.lower())
    if independent:
        checks.update(skillReady=signals.get('ready') is True,skillHero=signals.get('hero')==hero,
                      skillModel=signals.get('model')==model,skillWorld=signals.get('world')==loco.get('worldId'),
                      skillSource=signals.get('source',0)!=0,trapReady=trap.get('ready') is True)
    else:
        checks.update(combatReady=native.get('combatReady') is True,nativeHero=native.get('hero')==hero,
                      nativeModel=native.get('modelId')==model,
                      armory=native.get('armoryVariants',0)>=(3 if hero&0xffff==0x15 else 1),
                      emissionEnabled=native.get('enabled') is True,emissionRestored=native.get('restored') is False)
    snapshot=dict(path='junkrat-trap' if independent else 'native-armory',checks=checks,
                  yaw=combat.get('yaw'),pitch=combat.get('pitch'),
                  locomotion={k:loco.get(k) for k in ['ready','hero','modelId','worldId','error']},
                  native={k:native.get(k) for k in ['hero','modelId','hostGeneration','combatReady','armoryVariants','enabled','restored','heartbeat','readError']},
                  skill={k:signals.get(k) for k in ['ready','hero','model','world','source','error']},trap=trap,
                  flight={k:(combat.get('flight') or {}).get(k) for k in ['ready','barrage','heldSpaceLift','error']},
                  failed=[key for key,ok in checks.items() if not ok])
    return not snapshot['failed'],snapshot


def settle_aim(s,read_native,*,timeout=25,clock=None):
    """最多25秒，连续稳定0.35秒后校正；失稳重建基线，超时保存全部条件。"""
    import time
    clock=clock or time
    selected=s.result['bastion'];hero,model=selected['hero'],selected['modelId']
    name=s.voice_selected
    row=dict(hero=name,expectedHero=hero,expectedModel=model,timeout=timeout,passed=False,samples=[],corrections=0)
    s.result.setdefault('aimDiagnostics',[]).append(row);s.save()
    start=clock.monotonic();deadline=start+timeout;stable_since=None;level_since=None;previous=None;scope=None
    try:
        while clock.monotonic()<deadline:
            combat=s.data()
            try:native=read_native()
            except Exception as error:native={'readError':repr(error)}
            ready,snapshot=aim_readiness(combat,native,hero,model,name)
            signature=repr(snapshot);now=clock.monotonic()
            row['last']=snapshot
            if signature!=previous:
                row['samples'].append(dict(elapsed=round(now-start,3),**snapshot));row['samples']=row['samples'][-100:]
                previous=signature;s.save()
            if not ready:
                stable_since=level_since=None;clock.sleep(.1);continue
            current_scope=(snapshot['locomotion']['worldId'],snapshot['skill'].get('source') if name=='Junkrat' else native.get('hostGeneration'))
            if current_scope!=scope:scope=current_scope;stable_since=level_since=None
            if stable_since is None:stable_since=now
            if now-stable_since<.35:clock.sleep(.1);continue
            delta=(180-combat['yaw']+180)%360-180
            if abs(combat['pitch'])<1 and abs(delta)<1:
                if level_since is None:level_since=now
                if now-level_since>=.15:
                    row.update(passed=True,elapsed=round(now-start,3));s.save();return
                clock.sleep(.1);continue
            level_since=None
            if row['corrections']>=12:clock.sleep(.1);continue
            s.driver.send(f'rel {round(delta/.1)} {round(-combat["pitch"]/.1)}')
            row['corrections']+=1;clock.sleep(.3)
        s.result['aimTimeout']=dict(hero=name,**row.get('last',{}))
        raise ValueError('语音抽查朝向未稳定: '+name+' '+repr(row.get('last',{})))
    except Exception as error:
        row.update(error=repr(error),elapsed=round(clock.monotonic()-start,3));s.save();raise

