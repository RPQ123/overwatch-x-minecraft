# F8 portal selection —2026-10-24

Human request: consolidate the portal builders into F8, then select by digits or
numeric keypad. F7 Nether and F9 Twilight shortcuts remain; F8 no longer directly
creates an End portal. F8 opens/closes the menu,1–8 select the current page,
9 advances and0 goes back. Both digit rows share the same release-to-arm edges.
F8/F12 menus are mutually exclusive. Input is scoped to the exact native OW
foreground, live creative MC player and current model/source/world. Casting,
pending requests, focus loss and session changes reject or reset selections.

PortalCatalog enumerates actual installed dimensions and blocks. Legacy AoA
dimensions absent from this version are not invented. Vanilla Nether/End,
installed Aether/Twilight and registered usable AoA portals are candidates.
Only actual original portal blocks are placed. Aether activation calls its
original portal-shape method; Twilight retains real diamond activation. AoA
uses its author frame method outside Overworld; that method intentionally skips
Overworld, so the explicit creative builder there uses the installed5x6 frame,
actual frame block and actual portal block/axis. Transport remains mod-owned.
Reference: author AoAPortal.java pinned7919b5fe48599e6105c5740937ce36c36ef21d16:
https://github.com/Tslat/Advent-Of-Ascension/blob/7919b5fe48599e6105c5740937ce36c36ef21d16/source/content/world/teleporter/AoAPortal.java

The immediate build is bounded to loaded terrain inside height/border, rejects
containers/unbreakable blocks, snapshots its affected volume and rolls it back
on failure. This explicit creative action can replace ordinary terrain in front.
Diagnostics are /world portalMenu/portalCatalog/portalBuild. Gradle key fixtures
cover held/focus, ambiguous digits, pending requests, page wrap and absent rows.
Fixture checks alone are not actual portal construction/transport acceptance.

Actual portal-live3(d195492c) built all14 actual portal types successfully using
both digit rows and paging.13 owned structures reverted; the End test cleanup
correctly refused its then-unrecognized original EndPortalBlockEntity. This was
a cleanup failure, not a missing portal. The cleanup now permits only that exact
non-container original entity on an unchanged owned End portal. portal-final4
(3af7a245) passed Nether/End/Aether/Abyss builds and all four exact owned reversions.
Nether/Aether/Abyss actual walking portal transport also passed and source portals
were reverted. Returns in these isolated tests used the explicit world-switch
fixture, so they do not certify every mod's original return-portal algorithm.
All14 dimension roundtrips and all hero/portal combinations are not claimed.
57Gradle tasks and the correct independent HTTP contract entry passed.

Finalb89986b9 cold End/Abyss build+undo, real menu exclusion and final
grounded movement/picker passed. F8 now uses volatile cross-thread admission and
the existing generic active-ultimate/Reaper guards. The full14 construction
matrix was earlierd195; no portal geometry changed in the final guard increment.
