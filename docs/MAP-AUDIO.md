# Hollywood map audio filter

Bootstrap8 retains the user-approved Hollywood scene and its original lighting.
At the original map resource constructor, it removes only the map environment
SoundSpace and type12 SOUND placeables. It does not mute SFX, music, voice,
weapons, heroes or Minecraft. Original archives are unchanged; the edit exists
only in the newly loaded process and takes effect on a cold launch.

The exact owned beta24919 map08000000000002af has a0x320-byte pre-fixup header,
FNV1a845f1cd9031e5cd6. Its+120 resource02a0000000000195 is a160-byte
STUSoundSpace7ddbb13b containing an external sound. The type12 range has37
72-byte records at0xd52c8, totaling0xa68bytes; all records carry type12 and
individual sound resources. The modern [OWLib enum](https://github.com/overtools/OWLib/blob/master/TankLib/Enums.cs)
also identifies12 as SOUND, but offsets/fingerprint are established from the
owned24919 bytes, not copied from current OW2 structures.

Only header bytes120..127,240..243,280..283,2c0..2c3 are zeroed. Sky resources,
light/reflection records, entities, effects and geometry remain byte-identical.
Any whole-header mismatch rejects before writing. Bootstrap must observe exactly
one successful map edit and zero map failures before reporting phase3. Its map
constructor callback and Present table are then restored. Existing Lobby_Final
empty-scene experiment remains a separately fingerprinted path, not the default.

Fixture map_audio_data_test rejects800 single-byte corruptions, the Lobby header
and repeated application, and verifies the unchanged bytes. Input fixtures are
private extracted headers; no game bytes are shipped in the source. Compile with
the configured native compiler and supply Hollywood header and Lobby map paths.

Real native26592/MC2368 bootstrapped and fused normally. Eight-second original
process audio before the change had RMS0.0058907. A settled post-change capture
had RMS2.449e-10 and peak6e-10, effectively numerical silence. The immediate
post-selection recording still contains fading startup/hero sounds and must not
be described as silent. Evidence: research/hollywood-audio-{before,after,settled}
and hollywood-audio-comparison.json. This is a bounded idle capture, not a claim
that every event-driven map sound in every future scene has been audited.

Backup after normal shutdown/save:
<USERPROFILE>/.universal-modder/backups/owmc-map-audio/20261016-081306.zip
(72,286,072compressed bytes). Initial live-profile backup encountered a locked
file and failed; the completed stopped-profile backup is the usable snapshot.

A fresh startup also exposed Windows ERROR_BAD_LENGTH while enumerating DLLs.
The launcher now retries only this transient condition up to10times,50ms apart;
other errors fail immediately. It never uses an empty/old inventory on failure.
23launcher tests cover retry success, finite exhaustion and other-error refusal.

The verified30s three-hero clip (hollywood-quiet-verified-heroes.mkv) shows
McCree42/Winston9/Genji29 selection animations, entry, weapons/HUD and native
attacks. All screenshots and contact sheet were inspected. Its original-process
audio RMS0.022403/peak0.317078 with quiet intervals confirms audio is retained.
The first attempted clip used H taps too short for native input polling and
remained Genji throughout; only the subsequent held-H150ms/600ms-wait capture,
validated against actual model IDs, is hero-switch evidence.

20s actual final-composition measurement after this change:186.754FPS,
39report windows minimum163.107, zero below150, held1, unmasked0. One retained
frame was observed; no zero-stutter guarantee is made. Current scene lighting
is unchanged and native MC daytime illumination is still a separate open task.
