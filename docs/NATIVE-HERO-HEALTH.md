# Original hero health initialization

The supplied offline spawner initializes every hero to169/200 normal health.
The creative passthrough launcher now reads each original hero's HealthPool
configuration and initializes the corresponding native base pools after each
confirmed model change. It does not implement survival damage, regeneration,
temporary armor or ultimate health transitions.

## Source and ownership

Original graph0580000000000033 has HealthPool nodes1,7,3 for normal/armor/shields
(pool kinds0,1,2). Each declared m_amount points to expression typeec502a81.
The measured bytecode31,0,0 loads one dynamic variable and returns it. Paths are
script-localc7,6c8,dd respectively. Native numeric values are200/0/0 for Genji
and McCree,400/100/0 for Winston. These are read values, not a copied hero table.

Native gettercc4250 confirms type0/1/2 selects component28 offsets98/1d8/318,
each with16slots of20bytes, skipping disabled slots. Initialization changes only
the first slot's12bytes: enabled, maximum, current. Native metadata at12..19,
other slots and game functions remain untouched. The exact component vtable,
script/graph/bag, current model/reference/hero and primitive source are checked.
Nonfinite/out-of-range values, unsupported expressions/heroes, extra enabled
pools and unexpected zero-config pools are refused. Failed writes roll back
already-written base slots only while the same native owner remains valid.

This path requires the actual MC player to be alive, invulnerable and full20HP.
It runs once per native model recreation, with failed setup eligible for retry.
It is not a continuous heal loop or a substitute for native damage mechanics.

## Evidence

- Actual23620 Winston changed169/200 to500/500 and the original HUD displayed
  its yellow100HP armor segment. Screenshot native-health-winston-23620_small.png
  and native-health-winston-fill.json are private evidence.
- Actual McCree became200/200. After cold native6760, hero switching automatically
  initialized McCree200, Winston400+100 and returning Genji200; check-only reads
  confirmed no manual fill was needed. Genji's first2.4s read preceded the
  supervisor refresh; the later ready=true check confirmed200. Evidence:
  health-auto-winston-6760.json, health-auto-genji-6760.json and
  native-health-fill-6760.json (the latter changes on later check-only runs).
- Five malformed/pool-preservation tests and21launcher/rebinding tests pass.
  Health configuration changes also abort initialization; rollback rechecks
  ownership separately from mutable configuration.
- Final cold21372 exposed a resource-ID guard accidentally using the pointer
  validator. The graph ID at script+150 is now read as raw64-bit data; no memory
  writes occurred before that failed check. After normal stop/save, fresh8828
  automatically initialized Genji169->200 and reached ready=true; check-only
  confirmed200/200. Evidence body10-final-cold-ready.json and
  native-health-fill-8828.json. Real composed pixels were inspected in
  body10-final-cold_small.png.

Survival health/damage, Winston Primal Rage health and other temporary pools
remain unverified and must not be reported as implemented by this initializer.
