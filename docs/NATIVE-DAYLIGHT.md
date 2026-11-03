# Native daylight white point

Bootstrap9 retains the verified Hollywood scene and map-audio filter, and changes
its original first-person illumination RGB to neutral daylight. It does not tint
the final screen or replace hero materials. The existing compositor gamma1.3 is
unchanged, making the before/after test isolate native illumination.

The owned24919 map08000000000002af has a0x320-byte pre-fixup header with
FNV1a845f1cd9031e5cd6. Its+14c unit vector matches the header rotation matrix.
The adjacent+158 RGB is(3.5200715,3.2676265,2.6564093). The function preserves
weighted linear luminance .2126R+.7152G+.0722B and sets all three components to
that value. It changes only12lighting bytes, in addition to the20audio bytes
already validated in MAP-AUDIO.md. All other header bytes, direction/shadow
transforms, light probes, geometry and hero resources remain identical.

Actual causal test: neutral bootstrap9 native26736 and blue-only diagnostic
bootstrap10 native21324. The diagnostic changes the same RGB to(0,0,4), keeping
all other code/data identical. The first-person hand and weapon became strongly
blue while MC scenery/HUD remained normal. Both full and reduced captures were
inspected. This establishes an actual native illumination effect, not merely
that a write occurred. Picker lighting changed much less, indicating additional
local lighting dominates there; this change must not be described as a complete
replacement of the picker's lighting rig or MC block-light/shadow transport.

Diagnostic10 was normally stopped/restored/saved. Its generated source is private
research/_archive/2026-10/daylight-bootstrap-blue.cpp; no production path selects it. The default
build, request and launcher all use9. Final cold native10652/MC10380 was started
from the normal launcher, first selecting McCree, then Winston, then Genji. All
three first-person screenshots were inspected. Original base health200/500/200
and weapon ammo6/100/24 are visible. Genji ready=true; other heroes retain honest
pending Genji-specific channel errors as documented in the existing lifecycle.

Private evidence: daylight-{neutral,blue}-{picker,hands}.png,
daylight-before-cold.png, daylight-final-{mccree,winston,genji}-{picker,hands}.png,
daylight-final-three-heroes.json. Native map-cache read-only decoding from
9c6470/9cb480 confirmed the original and changed resource identity; the resource
cache uses an eight-byte FNV hash, key+10/next+18/value+0, bucket array18a19a8 and
count18a19b8. No native getter was executed for this inspection.

Alternative diagnostics DynamicAmbient0, SinglePointAmbient1 and both showed no
clear improvement and were restored. temporary_render_settings now supports only
those two additional booleans, using one-byte operations. Three actual Win64
private-buffer tests prove adjacent bytes are preserved, integer writes remain
four bytes, exceptions restore values and invalid booleans refuse mutation.
No persistent INI/profile audio or graphics setting was altered by this helper.

map_daylight_data_test covers800single-byte corruption refusals, wrong map,
reapplication, unchanged bytes outside the12RGB/20audio byte sets, finite neutral
RGB and preserved weighted luminance.23launcher tests still pass. The fixture
requires the user's private extracted headers and does not redistribute them.

Backup after native26592/MC2368 normal stop/save:
<USERPROFILE>/.universal-modder/backups/owmc-daylight/20261016-083222.zip
(72,284,013compressed bytes). All subsequent tests retained the same world,
created no temporary blocks/entities, and used normal shutdown between native
versions. Native26736 and21324 are no longer running.

## Motion cadence follow-up

The45s first-person movement/turning run on10652/compositor26 produced186.303
new composed frames/s, held0/unmasked0. One of85report windows fell to143.689FPS;
this bounded run does not satisfy sustained150. Source still published~210FPS in
that window. Evidence research/_archive/2026-10/daylight-motion-perf.json and daylight-motion-path.json.

Compositor27 reuses three exclusively writable CPU buffers. The first45s run on
22876 averaged188.890FPS, but one of87windows fell to116.959; held0/unmasked0.
MC simultaneously fell to174FPS with a29.6ms maximum render interval. Both runs'
worst window coincided with the first large turn. Buffer pooling alone is not a
stutter fix. Subsequent Sodium trial/results are tracked in the current takeover.
