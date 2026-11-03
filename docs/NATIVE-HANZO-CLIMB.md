# Hanzo wall climb: current motor acceptance

## 2026-10-24 09:33

This round verifies the existing contact-driven motor; it does not introduce a
new climb implementation or claim exact original numerical/animation parity.
The production JAR remains a33b051c7de7918e85871bd0c15c7d0d92ce9fa10816ed4abb9ba4ab56621e55;
native compositor42/body26/gate11/emission16/bootstrap10/localhero1 are unchanged.

`research/sprint-20261024/hanzo-climb-acceptance.json` indexes real receipts:

| Actual dimension/control | Receipt | Result |
| --- | --- | --- |
| Overworld | hanzo-climb-current2 | Rise4.1768m; completed mantle, release/land, bow20->7.5 |
| Nether | hanzo-climb-nether | Rise4.1768m; completed mantle, release/land, bow20->7.5 |
| End | hanzo-climb-end | Rise4.1768m; completed mantle, release/land, bow20->7.5 |
| Twilight Forest | hanzo-climb-twilight | Rise4.0244m; completed mantle, release/land, bow20->7.5 |
| Soldier76 non-climber | hanzo-climb-nonclimber | Ordinary jump1.2522m, no motor starts/native climb ticks; rifle recovers |

Each used exact native/MC process creation, executable/JAR hashes and six unique
owners, fresh native input, actual MC collision on a reversible four-block wall,
flight explicitly OFF while climbing, native body climb-tick progress, alive HP,
and real attack damage afterward. Actual recordings exited0 and fixtures were
cleaned. Root viewed the four actual stone-wall images in
`hanzo-climb-wall-contact.jpg`, the Overworld movement sequence, and the final
original Hanzo animated picker. The separate later `hanzo-climb-four-dimensions.jpg`
samples show sky after cresting the air fixture; they are not wall-contact proof.

The initial `hanzo-climb-current1` failed its post-release height assertion. It
remains failed. Its actual trace shows the motor completed0.96m mantle at1.00s,
then the fixed1.2s W hold walked past the far edge of the one-block-thick wall.
Changing the harness to release upon observed mantle completion passed. No
production movement lock/teleport/flight or motor change was used to hide this.

This accepts the current four-block wall/ledge and post-climb attack slice in
four dimensions, not every ceiling, slab, corner, tall-wall exhaustion, death,
mid-climb identity transition or full original hand-animation sequence. Existing
WallClimbPhase6m/30tick and .30m/tick limits remain documented MC adapter settings.
Original classic wall-climb semantics were rechecked with Blizzard's
[Classic overview](https://overwatch.blizzard.com/en-us/news/24146047/); those
semantics do not certify these numerical adapter settings as Beta24919 constants.
No Minewatch code/assets were imported in this round.

Final user state: original Hanzo picker, MC Overworld, owned targets/walls/reveal
cleared, independent background usable. Current identity is in the runtime audit;
historical PID/creation in this document is not future authorization.
