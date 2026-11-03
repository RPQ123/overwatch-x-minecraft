# Native hero lifecycle: Genji, McCree, Winston

## Winston native phase to MC damage (emission 10)

Request v4/168 binds original script00fe, literal damage60, rate20, period1,
ammo variable0035, range0670=8 and angle00f3=40. Protocol3 kind2/flags217 carries
owner, phase begin, original tick, duration, native camera direction and fresh
MC world identity. Native graph timing owns every interval. Begin is ChaseVar
vtable15c8e30+110/f531f0; Finish/Abort is+158/f53270. Slot+118/f53200 is re-entry,
not end: rejected emission9 demonstrated post-release damage. Do not reuse it.

MC checks each living target center in the original8m/20-degree half-cone, then
raycasts real MC block geometry independently. All unobstructed targets receive
60 OW HP/s scaled by0.1 into MC HP, exactly once per retained native interval.
Entity targets do not occlude one another. Depletion, stale world/pose, hero
replacement, long sampling stalls and native clock rollback fail closed. It does
not credit Genji ultimate for Winston/McCree damage. Native target arcs and other
Winston abilities/health are not supplied by this base-weapon implementation.

Actual4980:576ms->3.456MC HP while firing; no damage after release;48ms short
phase->0.288HP; natural leaf obstruction preserved20HP;100ammo phase stopped at
5s despite5.4s held input. Actual7412 after cold restart:4m/6m targets both
20->16.543991;9m/30-degree targets20; replay unchanged. Then McCree20->13 and
Genji20->9.5. Native adapters restored normally on4980, failures0. Full guest
checks, native phase/journal and real-MinHook callback/restoration fixtures pass.
Private proof is research/emission10-*.json. This proves base beam damage, not
full Winston gameplay or the overall150FPS/playability goal.

## Latest: native McCree rays -> actual MC damage (emission 8)

This supersedes the emission7 diagnostic-only status below. Request v3/136 bytes
binds current native hero/model, original weapon script and both literal damage
config objects. Emission8/protocol2 retains acknowledged native hitscan events.
Kind1 uses owner/volley/nativeTick/shot/pellet as its identity, entity0, flags57
(fresh world1, native feet8, calibrated damage16, original factory32). It accepts
the measured original type1/resource2a7 factory with status0 or the observed
offline status8. Other status/config combinations are refused. No successful
native projectile spawn is claimed for status8.

The source is the original factory after scatter, never the mouse button. Original
computed config+48=0 speed, +4c=0 lifetime, +50=100 range. Read-only native
initialization104550f maps those from definition fields; instantaneous code at
1033066 and1034020 multiplies direction by+50 and traces the resulting segment.
This corrects an earlier tentative interpretation of100 as lifetime. Private
evidence: mccree-config-initialize-full.json, native-config-range-reads.json and
mccree-functions-10340d1.json. Base damage70 is reflected from both weapon nodes
33/38, declared STUConfigVarInt.m_value, and validated again in the native observer.

Guest maps the original origin relative to native feet into MC feet/eye space
(McCree native eye1.55, current MC eye1.62) and resolves one immediate segment.
Minecraft owns loaded-chunk validation, nearest collision and actual damage.
70 OW base body HP maps to7 MC HP. Repeated callbacks/batches cannot cause another
hit. Falloff/headshot behavior is not yet implemented, and no complete McCree
ability/ultimate claim is made. Launcher therefore continues to expose pending
Genji-only skill channels when McCree is selected.

Actual native1164: two left shots20->13->6; replay unchanged; natural leaf
obstruction kept a fresh target20 while blockHits increased. Fan emitted six
native rays, with original spread: three MC entity hits killed a20HP target and
three hit blocks. Winston->McCree return's first shot20->13; subsequent Genji
return emitted three shuriken20->9.5, replay unchanged. A requested temporary
test wall was refused due to occupied terrain; it is not used as blocking proof.
All test entities cleaned. Native1164 stop restored both native hooks and all
other adapters, zero failures. Cold native28580 repeated McCree20->13 and returned
to healthy Genji. No game terrain was edited.

Evidence in research: emission8-mccree-first-shot.json,
emission8-mccree-natural-occlusion.json, emission8-mccree-fan.json,
emission8-mccree-fan-replay.json, emission8-mccree-return-first-shot.json,
emission8-genji-return-first-shot.json, emission8-genji-return-replay.json,
emission8-real-restoration.json, emission8-cold-mccree-shot.json.
Native journal and real MinHook fixtures cover ray capture/dedup/range and world
refusal/hero lifecycle/dual restoration; full guest build/check and Python checks
pass. Actual distinct FPS remains98.82 in the20s1164 sample;150 not achieved.

This is the original supplied offline beta plus real MC. It does not replace the
heroes with MC models or manufacture attacks from mouse buttons. Full multi-hero
combat remains incomplete.

## Implemented

Body adapter6 follows the native controller/model replacement on the original
movement callback thread. It retains the MC world/position anchor, resolves fresh
component ownership and uses measured native eye heights: Genji1.20, McCree1.55,
Winston1.50 metres. No departed hero component is written after identity changes.
Missing/intermediate identities wait for a new valid local hero. Fixture coverage
includes original-field rollback and all three eye heights; the shared identity
resolver has a fixture with replaced controller and model objects.

Compositor23 recognizes the native McCree60-degree and Winston55-degree hand
lenses in addition to Genji's measured idle/Dragonblade range. The world70-degree
lens remains excluded. Winston has an actual distinct-buffer trace; McCree's
original crosshair projection supplied its candidate, then the actual fused
first-person image verified the result. Native depth-pair foreground and original
HUD remain the source of the hand layer; no image cutout or draw replay is used.

Weapon gate8 wraps three original WeaponVolley virtual callbacks in the shared
native table. Each call checks the current local model owner and a calibrated
hero/script pair before temporarily granting the existing native execution bit.
Other entities/scripts call the original callback unchanged. The shared table
avoids retaining state-object vtables after a hero is destroyed. Original return
values, nested calls and flag ownership are preserved. Three exact original table
slots are restored at stop. V7 introduced this route; V8 additionally prevents an
unrelated entity's callback thread from choosing the local hero's owner thread.
The lifecycle fixture explicitly exercises that case before the first local shot.

The launcher refreshes reflected locomotion bindings when body6 reports a new
hero/model. Request publication is atomic and rechecks native identity before
publishing. Combat readiness is still independently required; a new speed binding
does not turn a failed attack channel into a ready game.

## Real evidence

- Native28152 / gate7: Genji24->21 with3 original emitted projectiles; H then
  McCree6->5 and R->6; gate followed the new object with zero failures. All three
  original callback addresses were independently reread after restoration.
- Winston100->83.6800003 during an800ms hold. No Volley callback ran and no active
  Volley runtime state was found. This proves original ammo consumption, not that
  this gate drives Winston damage. His beam path needs a separate observer.
- Native18104 / compositor23 / body6 / gate7: McCree original revolver and
  Winston Tesla gun both appeared over actual MC. Genji->McCree->Winston->Genji
  and another McCree->Genji roundtrip kept body/gate callbacks healthy.
- McCree900ms strafe moved MC4.95blocks and native presentation4.9502m, remaining
  grounded. Winston movement measured5.225blocks over19 MC ticks; native body
  followed. Eye heights matched their own original camera values.
- The launcher's actual binding-refresh class followed McCree->Genji automatically
  and the live guest reported5.5/4.95/5.5 then6/5.4/6, with no refresh errors.

Final cold native19412/MC5680 also validated gate8 on Genji:24->21 and3 accepted
original emissions, all four adapters healthy.

Private evidence: research/weapon-v7-*.json, hero-v23-mccree-walk-shot.json,
hero-v23-winston-walk-shot.json, hero-v23-automatic-binding-roundtrip.json,
hero-v23-mccree-firstperson.png and hero-v23-winston-firstperson.png.

## Remaining requirements

Emission6 now keeps its original initializer observer installed across hero changes.
Non-Genji and transitional owners produce no projectile events. The launcher
atomically refreshes native Genji damage/dash/ultimate bindings on return; the DLL
validates the fresh model and script ownership before admitting its emissions.
The request reader shares delete access and closes immediately, allowing Windows
atomic replacement. V5 exposed the earlier long-lived input-stream lock and was
restored/replaced by V6 in a cold process.

Real native21604 completed Genji->McCree->Winston->Genji with emission6 enabled
throughout and zero failures. Before and after, three actual emitted shuriken
reduced separate MC test villagers20->9.5HP. Explicit journal replay caused no
extra damage. All test entities were removed. research/_archive/2026-10/emission6-roundtrip-shot.json.

Additional live tests found two dash lifecycle bugs: no idle logger row made the
first real Shift a baseline; a newly spawned hero's execution clock restarted
below the previous hero's clock. The reader now returns a non-executing idle state,
and dash/ultimate consumers include native model identity in phase and event
identity. Real16964 first dash95,392 then, after McCree->Genji, first dash20,288
both entered the MC motor, with two distinct begins and tree collision stopping
movement. research/_archive/2026-10/hero-combat-first-dash.json and
hero-combat-roundtrip-first-dash.json. Ultimate bindings reconnect, and charge
writes recheck the native owner; actual post-return sword test passed on11112: after Winston->Genji, original
projectile hits charged1200, Q drained0, first click20->8HP/one swing, second
click8->0HP/two total. The native End timestamp formerly counted as an extra
swing; active-only reads and a Win64 nested-map fixture now exclude it. Test
villagers were cleaned. research/_archive/2026-10/hero-combat-final-ultimate-single-hit.json.

New heroes still need real native hitscan/beam events, MC damage, abilities and
hero-specific health (the supplied spawner hard-codes169/200 for every hero).
The launcher therefore does not declare their combat ready. Genji on return
regains the creative200HP setting. The native F1 help banner after hero changes
is separate from the hero-selection-availability flag and remains visible.

Lighting still uses Hollywood and a hand gamma lift, not coupled MC sun/block
lighting. Map ambient audio and >=150 distinct composed FPS remain unresolved.


## McCree original pellet factory observed (emission 7)

Actual native PID 24016, current offline hash guard, emission 7 and weapon 8:
Genji -> McCree -> Genji completed while both observers stayed active. Original
McCree left fire produced two contexts 500 ms apart. Original fan produced six
contexts at 139..161 ms intervals, each with its own native scatter direction.
Resource 04000000000002a7, config type 1, native factory result null/status 8 on
all eight contexts. This is diagnostic evidence, not MC damage or a successful
native entity spawn. The initializer at d35c20 receives no McCree bullet because
the earlier factory d354b0 fails first. Observed d3550c continuation checks the
native admin's +210 factory and can return status 8. No server is fabricated.

Emission 7 observes d354b0 after the original function, bounds diagnostic rows to
256, preserves arguments/return, filters exact current local McCree/resource,
and retains Genji's existing journal separately. Both hooks restore their exact
original bytes. Fixture and actual shutdown restored=true/failures=0 passed.
Native function prologue starts with a redundant 40 prefix; the initial byte
check missed it, rejected installation without hooking, and was corrected from
live bytes before the successful cold run. Prepare now checks both prefixes.

Read-only reflection now decodes the primitive hash getter mov eax,[rcx+28];ret.
McCree graph nodes 33 and 38 both follow declared projectileImpact ->
m_modifyHealth -> m_amount -> STUConfigVarInt.m_value (s32), yielding 70 OW HP.
This is the beta build's base amount, not a claim about distance/headshot rules.
Both use ammo path 0d80000000000035. Future hitscan transport must carry the actual
factory context's world/owner identity and native direction. Dedup must include
native tick: observed volley ID persists across successive shots and shot/pellet
are both zero. Do not reuse Genji's entity-ID-only dedup for these failed spawns.
Range/falloff/headshot semantics and actual MC ray damage remain to implement.

Returning Genji actually hit an MC villager three times: 20 -> 9.5 HP, replay
stayed 9.5. Fixture entities cleaned, no terrain changed. Guest build/check,
8 reflection tests, 20 launcher tests, and native hook fixtures pass. Evidence:
research/_archive/2026-10/emission7-mccree-factory-left-right.json,
research/_archive/2026-10/mccree-damage-calibrated.json,
research/_archive/2026-10/emission7-genji-return-combat.json,
research/_archive/2026-10/emission7-real-restoration.json. Native 11112, 7284 and 24016 restored and
stopped; MC saved before the next cold launch. Do not label McCree combat-ready.
