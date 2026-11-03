"""Independent Junkrat cases using the existing guarded Suite; imported without game access."""
import json
import time

from junkrat_verification import DeferredSkill,base_verdict,creation_verdict,outcome,plan

HERO=0x02e0000000000065


def require(ok,message):
    if not ok:raise ValueError(message)


def sample(s):
    c=s.data();require(not c.get('testError'),'fixture: '+str(c.get('testError')))
    return c,c.get('junkrat') or {}


def wait(s,label,predicate,seconds=6,reader=None):
    until=time.monotonic()+seconds
    while True:
        c,v=(reader or sample)(s)
        if predicate(c,v):return c,v
        require(time.monotonic()<until,label+' deadline: '+json.dumps(dict(junkrat=v),ensure_ascii=False))
        time.sleep(.1)


def native_snapshot(s):
    """Read actual logger rows, never infer a native create from MC casts=0."""
    try:
        s.identity.health();require(s.driver.foreground(),'Input interference')
        state=s.states.sample_weapon(False,True)
        wanted={'0580000000000232':{7,10,11,32},'058000000000022b':{31},'058000000000096a':{12},'05800000000009ba':{7}}
        rows=[{k:row.get(k) for k in ('script','node','nativeTick','finished')} for row in state['records'].values()
              if row.get('node') in wanted.get(row.get('script'),set())]
        create=max((row['nativeTick'] for row in rows if row['script']=='0580000000000232' and row['node']==32),default=0)
        return dict(modelId=state['modelId'],createTick=create,rows=rows)
    except Exception as error:return dict(error=repr(error))


def recreate_actor(s,r,label):
    """Normal picker roundtrip through another hero; same-card confirmation is not recreation."""
    before=native_snapshot(s)
    anchor=s.choose('Soldier76');actor=s.choose('Junkrat')
    require(actor.get('hero')==HERO and actor.get('modelId') and actor['modelId']!=anchor.get('modelId'),'fresh Junkrat model was not created')
    if before.get('modelId') is not None:require(actor['modelId']!=before['modelId'],'same native model reused across Junkrat cases')
    from observe_native_weapon_states import WeaponStates
    s.states=WeaponStates(s.native)
    r.setdefault('freshActors',{})[label]=dict(before=before.get('modelId'),anchor=anchor.get('modelId'),model=actor['modelId'])
    r['actor']=r['bastion']=actor
    return actor


def prepare(s,r,label,level):
    actor=recreate_actor(s,r,label);level(s)
    until=time.monotonic()+8
    while True:
        _,v=sample(s);signals=v.get('signals') or {}
        wanted=('primary','mine','trap') if label=='base' else ()
        if signals.get('ready') and signals.get('model')==actor['modelId'] and all((signals.get(k) or {}).get('ready') for k in wanted):return actor
        if time.monotonic()>=until:
            raise DeferredSkill('current native bindings/baseline not ready; deploy the B11-fix diagnostics JAR',dict(signals=signals,model=actor['modelId']))
        time.sleep(.1)


def fixture(s,name):
    s.post(name);time.sleep(.5);return sample(s)


def death_fixture_health(s):
    s.identity.quick()
    from verify_recall_empty_history import request
    health=request('health');player=health.get('player') or {}
    require(health.get('sourcePid')==s.args.mc_pid and health.get('worldName')==s.args.world,'death fixture source PID/world mismatch')
    require(player and player.get('survival') is False,'death fixture is not the owned creative player')
    return health


def death_fixture_request(s,route):
    """Only the owned death fixture may read combat/respawn while the normal Suite alive gate is false."""
    require(route in ('combat','combat/test/junk-respawn-lab'),'unapproved death fixture route')
    death_fixture_health(s)
    from verify_recall_empty_history import request
    return request(route,post=route!='combat')


def death_sample(s):
    c=death_fixture_request(s,'combat');require(not c.get('testError'),'death fixture: '+str(c.get('testError')))
    return c,c.get('junkrat') or {}


def observe(s,seconds):
    until=time.monotonic()+seconds;c,v=sample(s)
    while time.monotonic()<until:time.sleep(.2);c,v=sample(s)
    return c,v


def base(s,r,click):
    steps={};r['baseNativeBefore']=native_snapshot(s)
    c,before=fixture(s,'mei-lab');hp=c.get('targetHealth');click(s);c,after=observe(s,3.5)
    steps['grenade']=dict(before=before,after=after,hp=[hp,c.get('targetHealth')])
    steps['grenade']['tuning']=dict(scale=after.get('grenadeScale'),fuseTicks=after.get('grenadeFuseTicks'),fuseStarts=after.get('grenadeFuseStarts'),
        groundContacts=after.get('grenadeGroundContacts',0)-before.get('grenadeGroundContacts',0),
        fuseExplosions=after.get('grenadeFuseExplosions',0)-before.get('grenadeFuseExplosions',0),lastFuseElapsedTicks=after.get('lastGrenadeFuseElapsedTicks'),
        directDamage=after.get('grenadeDirectDamage'),blastDamage=after.get('grenadeBlastDamage'),terrainStrength=after.get('grenadeTerrainStrength'),
        terrainBursts=after.get('terrainBursts',0)-before.get('terrainBursts',0),terrainBlocks=after.get('terrainBlocks',0)-before.get('terrainBlocks',0),terrainError=after.get('terrainError'))
    # Fresh targets keep grenade/trap/mine evidence independent of a previous kill.
    c,before=fixture(s,'mei-lab');hp=c.get('targetHealth');s.driver.send('hold 0x45 120');c,after=observe(s,2.5)
    steps['trap']=dict(before=before,after=after,hp=[hp,c.get('targetHealth')])
    _,before=fixture(s,'mei-lab');s.driver.send('hold 0x10 120');_,after=observe(s,2.5)
    steps['mine']=dict(before=before,after=after)
    from verify_deadeye_input_lock import client_command
    s.driver.send(client_command('mdown 1280 720 right',s.client_size));time.sleep(.15);s.driver.send('mup right')
    c,detonated=observe(s,1.5);steps['detonate']=dict(before=after,after=detonated,hp=c.get('targetHealth'),
        selfImpulse=dict(requests=detonated.get('mineImpulseRequests',0)-after.get('mineImpulseRequests',0),
            pushes=detonated.get('mineImpulses',0)-after.get('mineImpulses',0),nativePid=detonated.get('lastMineNativePid'),nativeTick=detonated.get('lastMineNativeTick'),
            shared=c.get('rocketSelfImpulse')))
    r['steps'].update(steps);r['baseNativeAfter']=native_snapshot(s)
    verdict=base_verdict(steps)
    verdict['coverage']='grenade throw/explosion/actual HP; trap throw; mine throw/adapted detonation. Trap trigger/HP and mine HP are recorded, not silently promoted to extra acceptance.'
    return verdict


def tire(s,a,r,level,grant,wall=False):
    key='wall' if wall else 'tire';level(s);c,before=fixture(s,'climb-wall' if wall else 'mei-lab')
    evidence=dict(before=before,nativeBefore=native_snapshot(s),checks={})
    r['steps'][key]=evidence
    if not ((before.get('signals') or {}).get('tireCreate') or {}).get('ready'):
        raise DeferredSkill('RIP-Tire create32 binding is not ready',evidence)
    q_pressed=False
    try:
        proof=grant(s.native,a.pid);require(proof,'explicit diagnostic tire grant failed')
        r['explicitLabQGrant']=True;evidence['labGrant']=dict(labGrant=bool(proof.get('labGrant')),payloadBytesWritten=proof.get('payloadBytesWritten'))
        q_pressed=True;s.driver.send('hold 0x51 120')
        until=time.monotonic()+6
        while True:
            c,after=sample(s)
            if (after.get('tire') or {}).get('casts',0)>(before.get('tire') or {}).get('casts',0) and (after.get('tire') or {}).get('active'):break
            if time.monotonic()>=until:break
            time.sleep(.1)
        evidence.update(afterCreate=after,nativeAfter=native_snapshot(s))
        verdict=creation_verdict(before,after,evidence['nativeBefore'],evidence['nativeAfter'])
        evidence['checks']['create']=verdict
        if verdict['status']=='DEFERRED':raise DeferredSkill(verdict['reason'],evidence)
        require(verdict['status']=='PASS',verdict['reason']+': '+str(verdict.get('rejection')))
        q0=before.get('tire') or {}
        try:
            if wall:s.driver.send('key 0x20 down')
            s.driver.send('hold 0x57 '+('800' if wall else '200'))
        finally:
            if wall:s.driver.send('key 0x20 up')
        _,moved=wait(s,'actual tire movement',lambda c,v:(v.get('tire') or {}).get('travelled',0)>q0.get('travelled',0)+.5)
        if wall:require((moved.get('tire') or {}).get('wallTicks',0)>q0.get('wallTicks',0),'actual MC wall was not climbed')
        evidence['moved']=moved;evidence['checks']['movement']='PASS'
        if wall:evidence['checks']['wall']='PASS'
        # No M1 or explosion-damage assertion: the production attack is intentionally disabled.
        raise DeferredSkill('RIP-Tire detonation remains disabled: no authenticated native 0233 commit',evidence)
    finally:
        if q_pressed:
            try:recreate_actor(s,r,'recovery-'+key)
            except Exception as error:r['nativeRecoveryError']=repr(error);raise


def passive(s,r,level):
    level(s);_,before=fixture(s,'enderman-melee')
    try:
        s.post('junk-death-lab')
        _,dropped=wait(s,'actual death creates exactly six bombs',lambda c,v:v.get('deathBombs',0)==before.get('deathBombs',0)+6,reader=death_sample)
        _,after=wait(s,'actual death-bomb explosions',lambda c,v:v.get('explosions',0)>=before.get('explosions',0)+6,4,reader=death_sample)
        require(after.get('deaths',0)==before.get('deaths',0)+1,'one death produced repeated passive batches')
        require(after.get('damageApplied',0)>before.get('damageApplied',0),'death bombs did not damage the actual nearby target')
        r['steps']['passive']=dict(before=before,dropped=dropped,after=after)
        return dict(status='PASS')
    finally:
        death_fixture_request(s,'combat/test/junk-respawn-lab')
        until=time.monotonic()+5
        while True:
            health=death_fixture_health(s);player=health.get('player') or {}
            if player.get('alive') and player.get('screen')=='none':break
            require(time.monotonic()<until,'actual scoped MC respawn did not complete')
            time.sleep(.1)


def run_cases(s,a,r,level,click,grant):
    mode=getattr(a,'junk_mode','base');requested=plan(mode)
    r.update(scope=mode,requestedCases=list(requested),cases={},explicitLabQGrant=False)
    for name in requested:
        try:
            s.post('cleanup');prepare(s,r,name,level)
            if name=='base':verdict=base(s,r,click)
            elif name=='passive':verdict=passive(s,r,level)
            else:verdict=tire(s,a,r,level,grant,wall=name=='wall')
            r['cases'][name]=verdict
        except DeferredSkill as error:
            r['cases'][name]=dict(status='DEFERRED',reason=str(error),evidence=error.evidence)
            r.setdefault('deferred',[]).append(dict(case=name,reason=str(error)))
        except Exception as error:
            r['cases'][name]=dict(status='FAIL',reason=repr(error));r['error']=repr(error)
            break  # Identity/focus failures must never be followed by more input.
    r['status'],_=outcome(r['cases'],True,r.get('error'),r.get('nativeRecoveryError'))
    r['passed']=r['status']=='PASS'
