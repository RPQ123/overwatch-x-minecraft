# Dragonblade voice and responsive walking — 2026-10-20

## 2026-10-21 — Classic recording research and actual audio acceptance

User explicitly requested the earliest versions and allowed voice archive sites.
The Omnic Talking distinguishes OW1/classic Genji1FEDD from successor059BBD and
marks1FEDF unused; do not substitute that unused line for native Dragonblade.
Installed private source is the classic1FEDD archive OGG, SHA256
1dcda15f9f4a10451be06679c1b32be73f72b8b7e6983648a3638e02fa2723d5.
At decoded8k mono it is sample-identical to the previous retail-extracted clip;
the installer permits migration only from the known old hash. The archive's
2026 upload date does not establish recording age. Exact2015-earliest status is
unverified, despite checking official2015 Genji overview and a2016 collection.
Current actual native Begin schedules once; mixed MC output correlates.99999998.
McCree AB63/AB5E archive clips are retained; live E/Q correlations.753/.943.
Official2015 McCree gameplay contains matching phrasing/audio candidates but is
not proof of exact original clean-file provenance. All recordings remain private.
Evidence/provenance/comparison failures: research/mccree-polish-20261021/.

References:
* https://theomnictalking.altervista.org/en/hero-dialogues/genji/
* https://theomnictalking.altervista.org/en/hero-dialogues/cassidy-x/
* https://theomnictalking.altervista.org/en/overwatch-classic-eng/
* https://www.youtube.com/watch?v=XkoRX2n9TSA (official McCree gameplay2015-05-20)
* https://www.youtube.com/watch?v=lYOjIDhJIG0 (official Genji overview2015-11-06)

Genji's actual native Dragonblade Begin event now plays a private original
callout through Minecraft's sound engine. Reaper and Soldier:76 ordinary
horizontal walking uses current input and each native directional base speed,
retaining a measured native boost. Minecraft still owns vertical movement,
block collision and saves. Other motor heroes and Bastion form locks are
unchanged. Quarantined Reaper Wraith/lifetime experiments remain disabled;
this increment does not complete Reaper's unfinished combat integration.

## Private voice

The owner's `D:/ow/over/Overwatch` client was read using existing
[OWLib DataTool](https://github.com/overtools/OWLib), version
`2.25.0.0+1151+68397365`, `extract-hero-voice`, `--online=false`,
`--language=zhCN`, `--rcn`. Extraction reported build `2.25.0.0.154088`.
No retail process was launched or attached.

Selected default Japanese Ultimate line: `00000001FEDD.0B2`, localized subtitle
`（日语）：尝尝神龙之刃！`, SHA256
`e8787b207de16eb9d8125d8990a241fe0f2098eb3a83f055547b98850ce1c7ae`.
Decoded duration2.630667s. Chinese `人竜合一！` and skin variants were also
extracted but are not the selected event. The official
[Cyber Demon article](https://news.blizzard.com/en-us/article/23875434/deconstructing-the-cyber-demon-genji-mythic-skin-with-the-overwatch-team)
documents skin-specific audio, so those variants must not be mistaken for default.

Extracted audio stays under private `.universal-modder/assets`.
`tools/genji_voice_assets.py` verifies the pinned hash, creates the local
`guest-passthrough-client/resourcepacks/owmc-private-voice` (MC1.21.1 format34),
and selects it while preserving other packs and volume settings. The launcher
calls it before MC startup. Missing source is optional; differing hashes fail
closed. A provenance manifest stays with the pack. Neither the mod JAR nor
source contains extracted audio; the profile and extraction are ignored/private.

Event `owmcguest:genji.dragonblade` plays once, relative to the listener, without
distance attenuation, in MC's VOICE category. Master/voice volumes remain
effective. There is no Q shortcut, synthesized speech, stop-all, or new callback.

`NativeUltimateController` observes the existing verified graph Begin node17.
`UltimateCalloutGate` baselines each source/model/world/session then admits only
a later Begin tick. Inactive zero ticks retain the high-water mark. The bounded
queue rechecks session/world/source/model and age<300ms on the MC client thread.
Hero/world/session changes stop this sound and discard pending callouts.
Binding during an existing ultimate does not manufacture a new shout.

## Movement

Accumulated native motor displacement could keep pointing along the old world
direction after reversal, unlike Genji's direct native-speed adapter.
For Reaper and Soldier76, `NativeMotorIntent.responsive` now uses current
input and the six native walk/crouch speeds. Native horizontal speed above
base supplies a boost ratio, retaining Soldier's real sprint. Sub-base native
startup acceleration no longer delays normal walking. Opposing/no input gives
zero displacement despite residual native velocity. Native totals are consumed
so they cannot replay later. Identity/freshness/numeric guards remain required.
Creative flight, swimming, vehicles and MC vertical gravity retain their routes.
This is a responsive offline adapter, not full modern air-control/knockback/root
equivalence for every skill or hero.

## Evidence and limits

Backup: `~/.universal-modder/backups/genji-voice-motor-20261020/20261020-124811.zip`
(939 files). Existing normal stop controls restored callbacks and saved MC before
deployment; native DLLs were unchanged.

- Build/check30 Gradle tasks passed, plus the direct HTTP contract entry point.
  Gate fixtures cover active initial bind, repetition, inactive zero/old Begin,
  world/model/session changes and reset. Motor fixtures cover reversal/release,
  sprint and invalid values. Pack fixture covers hash, idempotence, preservation,
  missing optional source and corrupt source rejection.
- `research/voice-motor-fixed.json`: grounded non-flying Genji comparison;
  Reaper/Soldier reversal projection -0.990m/-0.7425m along the former direction
  within about180ms, release drift0. Soldier sprint8.249989m/s. Invalid Q silent;
  native Dragonblade one callout; repeated Q and hero switching did not replay.
  Earlier attempts with simultaneous user input were discarded.
- `research/genji-dragonblade-voice-live.*`: MC process audio/video.
  `research/_archive/2026-10/genji-voice-audio-verification.json` compares recorded 48kHz mono PCM
  to decoded original: correlation0.99999990, offset1.862167s. This proves process
  audio output beyond a scheduled counter; no human listening acceptance claimed.
- `research/_archive/2026-10/voice-motor-worlds.json`: Nether/End × Soldier76/Reaper/Genji (6 rows):
  full positive native HP, grounded non-flying MC, stable body, zero callback
  failures, no false callout. A second real Dragonblade after return spoke again.
  Temporary blocks removed. `research/_archive/2026-10/voice-motor-accepted.png` was actually
  inspected: MC forest plus native Genji hands/HUD. No new FPS/full-kit claim.
- These reports preceded the final high-water dedup guard. The final build adds
  that stricter fixture-tested guard; `research/_archive/2026-10/voice-motor-final-deployment.json`
  records its fresh identities/JAR and post-deployment Q smoke test.

Repeat only in a backed-up Switch clone with no simultaneous user input:
`.venv/Scripts/python.exe tools/verify/verify_voice_motor.py`. This performs real input
and a four-byte lab charge grant on the SHA256-guarded offline executable,
captures process audio, releases keys and cleans temporary test objects.

Final deployment passed: JAR SHA256 `e622e6181ec02c6cfd43b22a7c8dc141f37a6f88d04ea64afceba8a5d9c34809`. Fresh-process invalid Q stayed silent, actual Dragonblade scheduled/played once, repeated Q stayed once, and the end returned to inactive with natural charge progression. Native blade and animated picker screenshots were actually inspected over the MC background. The normal independent supervisor and both games remain alive at the native Genji picker; temporary fixtures were removed in the previous saved session. Historical PIDs are not reusable.
