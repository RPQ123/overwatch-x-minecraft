# Native hero-picker publication gap

## 2026-10-24 current-session evidence

Research: `research/sprint-20261024/menu-publication-trace1/` and
`menu-publication-deadeye1/`. The new observer is bounded120seconds and read-only:
both4096-byte mappings are opened FILE_MAP_READ and sampled independently with
seqlocks. Expired samples are diagnostic data, never attack or input authority.
It checks exact native/MC creation and the SHA-guarded executable. No callback,
native write, input owner or producer is installed. It completed5694samples and
closed both mappings. No same-session reader remains from this run.

The original Deadeye sequence again passed charge walk/look, confirmed-fire
movement/view/F6 lock, native End, movement recovery and ordinary actual damage.
H during the next real firing sequence failed the unchanged3second menu wait.
It is an actual failure, despite later returning to the native picker.

Native host pose sequence381532/frame190789/stamp1792800319617 remained unchanged
up to7322ms, with its last gameplay input flag1. The last MC body timestamp was
1792800320102,485ms after the last native pose. Body max age was6879ms.
MC health continued returning, captured1044additional real frames and world time
advanced100ticks during the observed body-expired interval. The compositor failure
snapshot showed viewMode2, frames191211/poses190766/heldFrames430, failures0;
the native Present/draw observation continued but valid pose publication did not.

This evidence distinguishes the upstream native camera publication gap from an
MC client-tick stall. `WorldFrameMapping.publishBody` obtains a new validated
`HostPoseReader.latest()` on each client tick, rejects missing/expired poses and
therefore stops after the existing500ms pose deadline. When the native pose
returned with menu input0, MC body publication resumed within a client tick.
It does not prove which native camera/constant-buffer/viewport/depth/draw-stage
predicate stopped producing samples. It does not prove engine death or the old
TIMER write-corruption cause. Do not call idle survival/no error a crash-free proof.

Root viewed the actual10frame H-contact sheet: the last composed hand/sepia image
was held through the recorded transition. The final picker later appeared.
Same-pawn Esc->real cleanup acknowledgement->H cleanup was recorded separately
in `menu-publication-separate-cleanup1/result.json`; it is not a passing H test.

## Next bounded investigation

Preserve150ms combat/input and500ms pose provenance checks, the original3second
observation deadline, model/world/source isolation and strict stop lifecycle.
Never stamp an old pose/body as current or invent a camera to pass the harness.
Inspect `pose_observer.cpp::observe` original slot9 buffer upload, viewmodel-lens
filter, viewport/depth pairing, `poseFromScene` and selection transition. Existing
per-frame hold logic intentionally avoids flashing a raw original OW map.
If a cold diagnostic build is needed, normal-stop first; use a distinct candidate
artifact and one existing owner, never overwrite a loaded DLL or promote the
unaccepted43/44 candidates. Timebox this unknown so independent defense work can
continue. Earlier warm v3 success does not supersede the current reproducible gap.
