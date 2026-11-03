# Bastion Tank movement and cannon

## 2026-10-24 current baseline: forms and self-repair actual acceptance

`research/sprint-20261024/bastion-forms-current4/result.json` actually passed and
cleaned, current six42/26/11/16/10/1 owners/guestaf92f746 unchanged. Original
Genji->Bastion replacement, Recon grounded movement2.75m, Sentry grounded movement0,
actual Sentry damage20->2MC HP and return-to-Recon damage20->16 passed. Original
ModifyHealth Begin/End drove actual self-repair2->8.75MC HP at declared5MC HP/s;
release stopped healing and the20HP cap held. It did not heal from the E key alone.
Root viewed forms contact.jpg and final original animated picker. This is one
current Overworld isolated lab, not a new four-world or full-kit fidelity claim.
Tank collision/damage/terrain/End acceptance remains its separate smoke receipt.

Three earlier harness failures remain: start() removed its own floor and the
grounded gun fell past the fixed target; a same-hero selection retained Sentry
instead of producing fresh Recon; Sentry correctly refused F6 takeoff. The final
test uses an actual prior Genji replacement and existing explicit flight-open
fixture for the damage-only phase after grounded immobility was already proved.
This does not enable gameplay Sentry flight or bypass its actual native root.
Profile/config/source backup: private menu-publication-20261024-080437. No runtime
DLL/JAR or gameplay source was changed merely to make these tests pass.

## Latest user MC rule: real explosions also affect terrain

The user now requires every actual explosion to destroy eligible MC blocks,
with different strengths. This explicitly overrides the earlier Tank
no-terrain policy. It is an **MC gameplay customization**, not a change to the
original Beta damage/ring/flight declarations or a claim that original OW Tank
cannon destroyed map geometry. Keep the original effect.terrain0 and its typed
guard intact; apply a separate named MC terrain policy at the actual server
detonation. Earlier receipts showing35 stone blocks preserved remain valid for
their old build but do not accept the newly requested terrain behavior.

The source audit found three further real detonation paths outside the common
NativeRocketExplosion adapter: NativeFlashbangRuntime, NativeConcussiveRuntime
and NativePulseRuntime. The user subsequently explicitly exempted Flashbang
and Concussive Blast: their newly added terrain explosions are removed, while
original flash/air presentation, damage/status and impulse remain. Pulse still
uses the positive terrain policy. Genji sweeps, Deadeye blood, pressure-shell
rendering and other decorative callbacks do not create terrain explosions.
End crystals already use actual vanilla damage/explosions and must not gain a
second synthetic explosion. See EXPLOSIVE-TERRAIN.md for the six actual skill
tests and their narrower acceptance scope.

Terrain work must occur after the existing target exposure/damage/impulse
calculation, remain scoped to the same loaded server world and exact-once
detonation, and avoid a second entity damage/knockback or sound pass. Different
terrain strengths do not alter the calibrated native damage metadata. The
cannon and charge receipts below predate this policy; new block destruction,
cover behavior, replay, loaded-chunk bounds and cleanup need separate actual
acceptance. Source audit and the pre-edit document backup are retained under
`research/bastion-cannon-20261023/mc-shell/terrain-audit/`.

## 2026-10-23 follow-up: Tank charge suppression and cold Twilight acceptance

The charging gap observed in the first cannon build is now addressed in
`NativeChargeController`. Bastion polls the existing NativeSkillReader profile
for original graph012f Recon8/Sentry9/Tank105, using the current source/model/hero
and the exact three form entries. A unique original Recon or Sentry permits
ordinary credit; actual Tank105 active suppresses both time and damage credit.
Missing, empty, conflicting or replaced form state refuses credit as well.
`NativeChargeBudget` observes cumulative damage even while blocked and clears
pending credit, so Tank damage and time cannot be banked and granted at End.
Only fresh idle credit resumes after the actual native form returns. No Q-key
state or fixed guessed Tank duration controls this policy. Existing world/session
revocation and the prior Pharah/76/McCree/Reaper policies remain in place.

The expanded NativeChargeScopeCheck exercises Tank Begin/End, both eligible
ordinary forms, unknown/conflicting/replaced forms, pre-existing pending credit,
repeated Tank damage/time and model/world/session reset. The charge-fix build
log records48 Gradle tasks and BUILD SUCCESSFUL. These fixture results are
separate from the actual-client result below. The source-stage change-audit.json
still accurately says that its author had not built/deployed/tested at that
earlier point; it must not be substituted for the later receipts.

After strict restoration and cold deployment, the actual mod-complete Twilight
run `research/bastion-cannon-20261023/mc-shell/charge-fix/twilight-cold/result.json`
passed=true and cleaned=true. The exact scope was native29836 created
1792743170.490644, MC24420 created1792743153.1612751, model2147485806 and Twilight
world identity2517721119721470821. Guest SHA256:
8e021969f14da01a409507a8613eca65dd85f1a648db2ed96497f445a335243c.
Emission16 and gate11 retain the hashes recorded below. This remains an explicit
lab Q grant, not natural charging all the way to1200.

Three real03ce cannon shots passed direct/near/edge/outside/cover, block impact,
48block travel, replay, End/Recon attack recovery and cleanup. The splash and
far samples both show actual Tank active=true, skillsReady=true and charge0.
After actual native End and ordinary form recovery, charge0.1093389988 resumed
with active=false/skillsReady=true; Tank damage was not released as banked credit.
The first direct sample still contained the old1200 meter observation while its
worker had already seen Tank active; it is not evidence that the meter writes
or status publication are instantaneous. The later active-phase zero and End
checks are the accepted charge evidence.

Earlier Twilight attempts remain failed: the first could not finish yaw
alignment, and twilight-v2/v3 did not observe a new native Q Begin (Recon remained
and the1200 grant was not consumed). Their missing Begin cause is unproved.
The cold run's success does **not** establish that charge suppression fixed
those earlier input/native-start failures. The initial charge-fix four-dimension
wrapper also failed its Overworld End check by sampling the independent charge
worker's old transition status (skillsReady=false, actual charge0) at the same
instant the native Recon record appeared. That failed receipt is retained;
the revised harness waits at most500ms for independently ready same-scope
worker status. Its four-dimensions-v2 results must be accepted separately after
completion, not inferred from this Twilight run.

## 2026-10-23: emission16 cannon implementation and actual Overworld acceptance

The original Tank cannon now drives an MC projectile with real collision and
damage. The accepted route is original graph024f/node25 → original d354b0
factory → the existing single emission16 owner → typed armory admission → MC
swept flight/entity or block collision → one direct/blast result. Neither Q or
left-click input nor the last-state Volley logger manufactures a cannon shot.
The gate11 discovery below is the prerequisite, not a substitute for this test.

`tools/native_armory_binding.py` and `native-host/src/native_armory.hpp` admit
04000000000003ce only for Bastion0015, graph024f/node25, the verified current
owner and shared Volley class, and the29-node/22-state graph with
m_states[19]==m_nodes[25]. Both adapters validate the original typed declarations:
direct INT50, blast INT140, speed variable18e0 with INT60, lifetime INT5,
range FLOAT100, one projectile/shot and one shot/second, empty motion/gravity0,
and damage rings(1,1)/(4,.30000001192092896). The actual factory must also have
status8/type1/result0 and resolved60/5/100. Unknown declarations, owner changes
and incompatible factory results are refused. The generic blast structure
already represented both rings, so Pharah/Helix did not need a replacement
falloff format. At this accepted baseline, Tank terrain destruction was0; the
later user MC terrain override is recorded above and needs separate acceptance.

The MC adapter applies direct50OW=5MC HP and up to blast140OW=14MC HP, with
the measured ring declarations, distance to the target's nearest bounding-box
point and real block exposure. The blast avoids a second vanilla damage pass.
Its ServerWorld explosion packet supplies the vanilla MC explosion burst and
sound to the actual client. `BastionTankRenderer` supplies an **MC-authored shell**
following the admitted shot and retiring at actual impact; it is not an exported
original OW mesh. Native OW still owns the Tank transformation, gun, hands and
HUD. Four-slot blast knockback declarations and self-knockback remain
uncalibrated; no guessed rocket-jump or self-impulse was added.

`research/bastion-cannon-20261023/mc-shell/overworld-v3/result.json` is the first
accepted actual cannon run: passed=true and cleaned=true, native18276 created
1792740140.6759446, MC25008 created1792740123.5148902, current model2147485793.
It used an explicit lab Q grant; this is not a natural-full-charge test. Each of
the three cannon shots had its own real current-owner03ce factory identity,
status8/type1/result0 and resolved60/5/100.

| Actual case | Observed MC result |
| --- | --- |
| Direct target | 20→1HP; direct credit5 plus full splash14 |
| Direct-impact near / edge targets | 8.930981 /15.137648HP |
| Outside / screened targets | Both remained20HP |
| Stone screen during direct test | 35blocks before and after |
| Block-impact near target | 7.593459HP; direct credit did not increase |
| Block-impact outside / behind-wall targets | Both remained20HP |
| Target48blocks away | 20→1HP |
| Detonations / presentation | Three explosions, three shell models,222 cumulative render frames |
| Replayed native transport | No repeated damage or explosion |
| Original Tank End and Recon recovery | Tank105 End1370220, Recon8 Begin1371220; Recon target20→16HP |
| Fixture cleanup | cannonLab=false, no test targets, wallBlocks=0 |

The accepted `contact.jpg` was actually viewed: the original Tank weapon/HUD
and transformation are composed over the real MC terrain, with the disposable
targets and impact/shell presentation. `combat.mkv` and `combat.audio.raw` are
retained; audio identity/timing was not separately authenticated by this audit.
The observed counters prove presentation work occurred; they do not establish
an exact original mesh, muzzle/impact effect or audio match.

The first `mc-shell/overworld/` harness run failed because freshly started MC
had not yet published yaw. `overworld-v2/` then failed its Tank-settle check:
the native video shows the actual Q transformation, but the harness queried
`motor.form` while creative flying. The production motor intentionally resets
its movement session in flight, so that field was not a valid native-form
oracle. v3 instead reads original graph012f Recon8/Sentry9/Tank105 state records
with current-owner checks. These two failures remain failures; the production
motor was not relaxed to make the fixture pass.

Acceptance boundaries and remaining work:

- This section certifies the actual Overworld run only. Four-dimension and
  interrupted-cast results must be recorded separately after their own tests.
- The48block hit is real travel evidence, **not** an actual100block cutoff
  acceptance. The native100 declaration and fixture expiry tests do not prove
  a real-client shot expires exactly there. The near/edge observations show
  attenuation and cover, not a complete empirical reconstruction of its curve.
- Self-damage, four-slot knockback integration and rocket-jump physics remain
  unproved. Original full effect/audio fidelity and the complete Bastion kit
  remain outside this cannon acceptance.
- The real form trace exposed a separate charging gap in this first build: while Tank105 remained
  active, `nativeCharge.active` was false and the meter had already re-earned
  333.181152/1200 before Tank End. This build's NativeChargeController reads
  active ultimate state only for Pharah/76/McCree/Reaper. Suppressing passive and
  damage credit during Bastion Tank needed its own fix and actual retest; see
  the later charge-fix/cold-Twilight receipt above. This first cannon result
  alone does not certify the full charging lifecycle.
- A successful bounded battle and no new error report do not establish that
  the open native TIMER/Loop Exit issues are fixed, or certify sustained FPS.

Accepted guest SHA256:
bc18158c1034facdcf4095767e72bf619d454f6bf05e676ad0f54ab2410a228d.
Accepted emission16 SHA256:
899033a800bdd0b772199c7a3bcc82c1beeb0db4bb7702d5e9ff40339e342da9.
The exact offline executable remains SHA256
f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f.
Source/profile backups, metadata9 and native/Java/HTTP fixture evidence are
kept under `research/bastion-cannon-20261023/mc-shell/`; these are distinct from
the real-client receipt above. Normal restoration and cold deployment preceded
the run; no mapped DLL was overwritten and no callback owner was stacked.

## 2026-10-23 prerequisite: original Tank cannon factory reached with gate11

The current gate11 fixes one proved native execution gap. The original Tank
graph024f/node25 had flags408003 at idle and400083 in the real Begin callback;
gate9 rejected its extra bit2. Its animation/Volley End therefore did not imply
that the original d354b0 projectile factory ran. The current real pre-fix probe
recorded zero factory calls, one filtered callback and an unchanged20HP MC target.

gate11 permits only the measured Bastion0015/graph024f/node25 flags and inherited
authority bit8. It verifies the original shared Volley class, current owner/admin,
the29-node/22-state graph and m_states[19]==m_nodes[25]. An early interpretation
of definition+6c as the runtime state index was wrong: its value11 is a different,
unidentified field. gate10 was rejected in the real client and remains failed
evidence; no guessed state index or global execution-bit exception was retained.
The two flags and both original lists now use actual current-client evidence.

The cold-loaded gate11 real probe passed on native22116: exactly one original
04000000000003ce factory call, current owner/model, status8/type1/result0,
actual speed60/lifetime5/range100, no filtered Tank callback and original flags
restored after callback. Existing single emission15 captured this event; there
is no new hook, input-derived projectile or Volley-logger damage shortcut.
The original Tank model/HUD over real Twilight terrain was captured and viewed.

At this earlier gate11/emission15 stage, the armory still excluded03ce, the
actual MC target remained unchanged and cannonDamageAccepted=false. This was
native factory acceptance only. The emission16 typed binding and actual MC
collision/damage acceptance are recorded above. Motion is empty/gravity0;
blast knockback's four-slot integration/self-knockback semantics remain unproved.

Evidence: research/bastion-cannon-20261023/{before-gate10,after-gate10,after-gate11},
tank-declarations-live2016.json and gate11-live-correction.json. Both gate fixtures
passed; the initial fixture-loader mismatch (building10 but loading9) and first
startup version mismatch were corrected and retained as failed attempts. Attach
and supervision now share tools/native_weapon_gate_version.py. No mapped DLL
was overwritten. Gate11 SHA256:
b53f738e2096ebb7043f8fffbb706a98de25e6e42c47be68365a544ef7a5ee51.

## 2026-10-21 historical movement-only slice

The following records the earlier MC movement repair during the original Tank
ultimate, when cannon attacks were still unavailable. It is preserved as scoped
historical evidence, not the current cannon status. Recon, Sentry, original
model/animations/HUD, native speed and MC collision retain their existing
ownership. It was not a complete Bastion kit.

### Actual movement fault and correction

The old NativeMotorController bound only original Recon8 and Sentry9 from graph
058000000000012f. It labelled every other state a transition and zeroed horizontal
motion. During actual native Q, Recon ended, the transform ran, and distinct
Tank105 began. The native actor had nonzero W velocity while MC displacement
remained exactly0. This was an adapter fault, not absent native movement.

The exact-SHA beta/current-owner read verified Tank105 as typea7213568, the same
original state class used by Recon8/Sentry9, in the192-node graph. Actual Q trace
showed a1500ms transform before105 began; it also enabled the native Tank view
and original cannon Volley graph. No new fixed ultimate timer was introduced.

The binding now includes Tank105. NativeSkillReader validates its exact profile,
graph membership/vtable, current model/script/reference and process creation,
and reads actual original Begin/End. NativeMotorIntent allows movement only for
a unique Recon or Tank state. Sentry, missing/invalid reads, no active form and
conflicting form states remain locked. Cumulative motion is consumed while
locked, preserving the existing no-delayed-displacement policy. Q itself, native
velocity, speed modifiers, duration, visual configuration and MC collision were
not replaced by an input-driven mode or guessed numeric boost.

### Version reference and then-unavailable cannon

Blizzard's [Classic description](https://news.blizzard.com/en-gb/article/24146047/a-blast-to-the-past-begins-with-overwatch-classic)
describes mobile Tank and immobile Sentry. It concerns May2016 launch1.0, later
than this offline0.8.0.24919. Modern community-mode/perk balance and damage must
not be substituted as this beta's rules.

Read-only current-client calibration identifies Tank weapon graph024f/node25,
projectile04000000000003ce, speed variable18e0=60, lifetime5, range100, direct
health modifier50 and explosion modifier140. These are declarations, not a
working MC shell or a complete blast/self-knockback policy.

One bounded original Q/primary diagnostic used an explicit guarded four-byte
lab grant to the actual meter, not naturally earned full charge. Q drained;
the original Tank animation/view and Volley25 were observed. The real20HP MC
target stayed20, and the existing scoped pellet-factory diagnostic recorded no
current-owner cannon factory observation. This does not establish which missing native/server
path caused the gap. A Volley logger End or a muzzle animation is not a lossless
attack event. Resource03ce was not added to the generic primary whitelist, and
no projectile was manufactured from Q, primary input or those logger rows.

### Historical movement tests and limitations

Private evidence is under `research/bastion-tank-20261021/`, including source,
profiles/settings and old JAR backups, mapped-module audit, native graph dump,
q-probe.json, movement-before.json and movement-after.json. In the same initial
air-floor setup, W600ms changed from0MC movement to2.775390625 after the fix;
both traces contained native velocity. A later stone-lane run observed a lower
actual native speed. The test's initial>4speed assumption incorrectly rejected
real1.84765625movement and is retained in
`lifecycle-speed-assumption-failed.json`. The harness now checks actual original
movement, form, MC displacement and real wall collision rather than imposing
the earlier speed sample. This does not claim an exact universal speed or FPS.

`tools/verify_bastion_tank_movement.py` tests the isolated mod-pinned Switch world
in actual dimensions. It checks grounded Tank W movement and real collision,
release drift, original End followed by Recon movement, Sentry immobility,
active-Q native hero replacement and fresh Recon state, full health/current
light, actual Recon target damage and duplicate replay. It explicitly uses lab
meter grants, not natural-full-charge acceptance. Raw per-row screenshots and
result.json retain the outcomes. All four actual rows passed: Tank W600ms moved
1.72–1.79blocks on the collision lane, stopped7.2blocks from its start at the
actual wall, had zero release drift and zero Sentry displacement, and fresh
Recon shots reduced20HP to16 without duplicate damage. Source/model/world agreement is checked with
the signed world ID normalized before accepting the new body scope.

The full33-task guest build/check passed, including owned Win64 skill-reader
fixtures for Tank Begin/End/definition replacement and existing Visor/Deflect
guards.45supervisor fixtures and the proper HTTP contract entry point passed.
No native DLL or hook schema changed. Normal callback restoration/full shutdown
preceded cold deployment; no mapped DLL was overwritten and no owner stacked.
Post-change real76 Visor also passed passive/damage credit, explicit-grant Q,
off-axis damage, cover/replay/End. Receipt:
research/native-visor-21460-1792542441740716700.json. Final native21460/MC22668
and independent wrapper25588/worker9388 are healthy,76full200/200/MC20 grounded
Overworld/F6OFF, fixtures/projectiles/diagnostic flag cleared. All four Tank
captures and final native76 pixels over MC were inspected. JAR SHA256:
cd5196f73c34be272190ccef724c8b7546147dad44c4cf7cf533d596c872d0c8.
Six mapped native module hashes and settings remain unchanged. Current facts
are also in TAKEOVER.md; final-audit.json retains the raw scope/module/process
evidence. Sampled frame advance proves active transport, not sustained FPS.

At that movement-only checkpoint the center H prompt remained visible. Dynamic
MC day/night weapon-light parity, cannon emission/collision/blast/rocket-jump
behavior, full-kit fidelity and sustained performance were outside that fix.
The cannon slice was explicitly deferred then; the newer implementation and
remaining boundaries are recorded at the top of this document.
