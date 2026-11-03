# Early Chinese voices — active, not completed

## 2026-10-22 — historical reference pairing correction

The old bili-BV1Hs411q779/reference-manifest.json incorrectly paired heroes,
videos and audio. Newly viewed contact sheets show P01 video=Pharah and
P20 video=Winston; P01 audio actually says McCree's callout, P02 audio contains
Pharah's Mandarin callout. Do not cite that manifest as21 individually verified
audio/video pairs. The private thnu-three installed selection/skill clips are a
separate source and remain unchanged. The Pharah post-callout SFX adaptation and
its limits are documented in [PHARAH-BARRAGE.md](PHARAH-BARRAGE.md); it is not a
clean voice replacement or proof of an earliest recording date.

## 2026-10-21T22:11 — 21 selections, delayed confirmation and original Q variants

Latest user directions supersede the old Japanese-only/English defaults below.
All21 original roster selection events are now installed:20 classic Mandarin
recordings from http://ow.thnuclub.com/ and Bastion's original language-neutral
OW1 selection AA64 from
https://theomnictalking.altervista.org/en/hero-dialogues/bastion/ . The site's
metadata tags are not authoritative: the old McCree selection is tagged English,
but its actual recording and independent language detection are Mandarin.
All20 spoken selection files were decoded and identified as Chinese, probability
>=.931. Exact2015/earliest recording dates are not certified; source upload dates
must not be presented as recording dates. No TTS, skin/tutorial/unused substitutes.
Private assets and per-file provenance/SHA256 stay under
~/.universal-modder/assets/ow1-zhcn-2016/thnu-three (name retained for continuity).
Nothing is bundled into the mod JAR or intended for source commits.

HeroSelectCalloutGate now waits1000ms after a confirmed hero change. The original
flags==1 only establishes a real scene pose; it includes the picker. Admission now
also requires the existing host inputActive (native viewMode==1 plus foreground),
live MC player, valid model/world and native source identity. Hover must not speak.
A different hero replaces the pending line; leaving first person/focus or a native
session reset cancels it. Same-hero H/back, model, dimension and respawn do not
repeat it. A genuinely new native source or returning after another hero can speak.
The gate's clock is monotonic, not wall time.

Actual final roster run native21144/MC29288 passed all21 selections, no hover
speech, no same-hero H/back replay. Process-only MC audio matched every individual
recording: correlation .90656.. .99857. QPC audio timestamps (raw sample0 is
start_hns; do NOT add video audio_offset_s) measured1.063..1.151s after observed
native first-person confirmation. Gate admission was1000..1051ms.
Receipt: research/three-hero-chinese-20261021/roster/actual-roster.json and
actual-audio.json, both passed=true; actual native contact sheet inspected.
The separate185s native audio capture produced no VAD speech segments; this is a
bounded absence-of-overlap observation, not proof for every possible voice event.
Earlier first/quiet-1 runs failed or had unplanned hero changes; retained as failures.

Three requested heroes' currently verified spoken skill events:
- Genji native Dragonblade Begin: classic Mandarin recording, plus original OW1
  Japanese1FEDD at equal random weight. User explicitly authorized this exception
  to the Mandarin-only preference. Actual two native Q activations naturally chose
  both variants, and actual MC audio correlations were .99999998 and .99952018.
- McCree actual native flashbang event: classic Mandarin clip, actual audio .80439.
  Existing accepted classic Mandarin Deadeye is preserved, actual new audio1.0.
- Pharah actual original barrage node12 Begin: classic Mandarin clip, actual
  MC audio .99677. Not a Q-key-triggered line.
Receipt: core/actual-core.json and core/actual-audio.json, both passed=true and
cleaned=true. No invented speech was attached to original nonverbal skill SFX.

Installer early_chinese_voice_assets.py validates every source and existing private
file before mutation; sounds.json replace=true avoids merging old Japanese/English
versions at random. Pack goes last without duplication, preserving other packs and
voice volume. Only Genji Q deliberately lists the two user-approved language
variants. Five profile-preservation/hash/random-variant fixtures and36 Gradle tasks
passed; proper bridge/test_contract.py fixture entry also passed.
Installed combined guest SHA256 e0d9998247222ef06d43f6e2ac91e1a45c8c36307573e8b8bf078dd84dd311ce.

Actual lifecycle follow-up passed in the same21144/29288: a confirmed Genji
selection canceled at650ms did NOT speak, the following confirmed McCree spoke
once after its own delay. Main/Nether/End/Twilight/main switches did not replay
selection or old ability lines, current McCree remained200/200. Receipt:
research/three-hero-chinese-20261021/lifecycle/result.json passed=true/cleaned=true.
The first200ms-H attempt stayed on Genji and never reached the requested McCree;
its result-first-200ms.json remains failed, not cancellation acceptance.

Coverage boundary: ALL21 SELECT calls are complete; this does not mean all21
heroes' complete skill/ultimate/banter inventories are translated. Other heroes'
spoken skill events still need source/version/event matrices and real native
admission before deployment. Do not manufacture them from keys or reuse a taunt as
a skill line. Preserve McCree per-shot damage/animation,76 visor and all prior
initialization/light repairs. Read latest TAKEOVER for current process identities.


User requests all21 roster heroes in early Mandarin, including selection and
skill/ultimate lines. This supersedes the previous Japanese Genji default and
English McCree E preference. Current adapters are still Genji Q and McCree E/Q;
there is no complete all-hero selection/skill replacement yet.

Current installed McCree Q is the accepted early Chinese “午时已到” clip; preserve
its actual per-shot animation/damage and mixed-audio acceptance from NATIVE-MCCREE.
Current Genji Q is classic Japanese1FEDD, not Mandarin; current McCree E is English
AB5E. Do not label either as the requested completed Mandarin conversion.

## New historical reference, 2026-10-21

Original uploader collection dated2016-06-14:
https://www.bilibili.com/video/BV1Hs411q779/
The uploader describes recording all heroes and making MP3s. The21 public clips
were obtained without login/access bypass using the public player/page responses.
Private copies, SHA256 manifests and source URLs are under:
`~/.universal-modder/assets/ow1-zhcn-2016/bili-BV1Hs411q779/`.
The archive upload date establishes that reference's age, not an exact2015 date.
These contain game SFX, sometimes other characters, and normal team/self language
differences; they are **references**, not ready-to-install clean voice clips.

Visible native hands/HUD identify P1..21 as McCree, Mei, Bastion, Reinhardt,
Lucio, Junkrat, Reaper, Widowmaker, Zarya, Hanzo, Genji, Torbjorn, Mercy, Symmetra,
Zenyatta, Soldier76, Roadhog, Tracer, Winston, Pharah, DVa. Contact sheet actually
inspected: research/all-hero-zhcn-20261021/all-ult-reference.jpg. Bastion/animal/
nonverbal audio is not a missing Mandarin spoken sentence. A collection of Q
clips does not cover selected-hero or every skill event.

## Local extraction limitation

Owner's installed retail client is now2.25.0.1.154504. Official latest OWLib
release v2.25.0.0+1151 supports154088:
https://github.com/overtools/OWLib/releases/tag/v2.25.0.0%2B1151
Develop's TACTLib129f977b also has154088 providers, no154504 provider (checked
official GitHub tree). The normal tool rejects154504. A private isolated host
tested its existing AttemptFallbackManifests switch; it failed reading the TRG
manifest (Stream length bounds). No retail files were changed, launched or
attached. Do not relabel a failed fallback as extracted Chinese hero audio.
Logs/scripts are private under research/all-hero-zhcn-20261021/.

Existing154088 Genji Chinese extraction remains private and usable for further
verification: classic HeroSelect BA14, Ultimate B1A9 plus skill categories. A low
GUID or matching subtitle alone does not prove identical2016 recording. Avoid
skin-specific, unused, successor or merely renamed subtitle replacements.

Old Chinese-labelled catalogues can actually link English soundboards. The
qqan2016 archive host failed three bounded attempts; do not hammer it. No installer
or unknown executable was downloaded/run. Early uploader reference plus cleaned
individual recordings, or a compatible official offline extractor, is next.

## Next acceptance

Create a per-hero/event provenance and clean-audio matrix, then use real confirmed
native selection/spawn and skill events to play the corresponding private clip.
Never fire lines from keypress alone or every dimension rebind. Preserve exactly-
once/session/focus guards. Generic voice replacement must also suppress only the
matching original English callout; global SFX mute/stop-all is not equivalent.
Prove actual mixed MC audio and absence of overlapping old-language speech.
Keep audio private, out of the JAR/source/commits. No TTS substitutes.
