"""Analyze saved read-only Blink observations and compositor41's numeric ring.

No game/process/mapping/graphics access. Native state changes have bounded sample
intervals, not invented exact frame timestamps. Initial logger rows are baseline.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLINK = '0580000000000024'
PISTOLS = '0580000000000016'
LABELS = {2: 'Blink root', 5: 'teleport action A', 10: 'teleport action B',
          8: 'BlinkEffect', 35: 'Blink animation', 57: 'declared .1s wait'}


def analyze(data, radius_ms=120):
    pid = data['pid']
    rows = data.get('rows', [])
    frames, conflicts, events, samples = {}, [], [], []
    previous, last_scoped = {}, {}
    trace_enabled = False
    generations = set()
    for row in rows:
        report = row.get('compositor') or {}
        if report.get('pid') == pid:
            generation = report.get('generation', 0)
            if generation:
                generations.add(generation)
                trace_enabled |= report.get('handMaskTraceEnabled') is True
                for frame in report.get('handMaskTrace', []):
                    if not isinstance(frame.get('frame'), int) or not isinstance(frame.get('wall'), int):
                        continue
                    key = generation, frame['frame']
                    value = dict(frame, generation=generation)
                    if key in frames and frames[key] != value:
                        conflicts.append(dict(generation=generation, frame=frame['frame']))
                    else:
                        frames[key] = value
        model = row.get('modelId')
        if not model or 'readError' in row:
            continue
        wall = row.get('wallMs', 0)
        end = row.get('sampleEndWallMs', wall)
        scoped_key = model
        baseline = scoped_key not in last_scoped
        for record in row.get('states', []):
            script = record.get('script')
            if script not in (BLINK, PISTOLS) or not isinstance(record.get('node'), int):
                continue
            key = model, record.get('instanceAddress'), script, record['node']
            old = previous.get(key)
            changed = old is None or (old.get('nativeTick'), old.get('finished')) != (record.get('nativeTick'), record.get('finished'))
            if changed and not baseline:
                kind = 'End-observed' if record.get('finished') else 'Begin-observed'
                if old is None:
                    kind = 'new-row-' + kind
                if old is not None and old.get('finished') and old.get('nativeTick') != record.get('nativeTick') and record.get('finished'):
                    kind = 'End-observed; intervening Begin may be lost'
                label = LABELS.get(record['node'], 'Blink node' + str(record['node'])) if script == BLINK else 'Pulse Pistols node' + str(record['node'])
                event = dict(modelId=model, instance=record.get('instanceAddress'), script=script,
                             node=record['node'], label=label,
                             kind=kind, nativeTick=record.get('nativeTick'),
                             wallInterval=[last_scoped[scoped_key], end],
                             mappedBefore=row.get('mappedBefore'), mappedAfter=row.get('mappedAfter'))
                events.append(event)
            previous[key] = record
        last_scoped[scoped_key] = wall
        samples.append(row)
    ordered = sorted(frames.values(), key=lambda f: (f['wall'], f['generation'], f['frame']))
    walls = [f['wall'] for f in ordered]
    for event in events:
        low, high = event['wallInterval']
        near = ordered[bisect_left(walls, low - radius_ms):bisect_right(walls, high + radius_ms)]
        event['nearbyFrames'] = near
        event['reasonCounts'] = dict(Counter(reason(f) for f in near))
        # An exact shared mapping frame can be identified; the state event
        # itself is still only located within the logger read interval.
        event['mappedFrameMatches'] = []
        for edge in ('mappedBefore', 'mappedAfter'):
            mapped = event.get(edge) or {}
            host = mapped.get('host') or {}
            frame = frames.get((host.get('generation'), host.get('frame')))
            if frame is not None:
                event['mappedFrameMatches'].append(dict(edge=edge, kind='current host frame', frame=frame))
            mc = mapped.get('mc') or {}
            frame = frames.get((mc.get('hostGeneration'), mc.get('hostFrame')))
            if frame is not None:
                event['mappedFrameMatches'].append(dict(edge=edge, kind='MC acknowledged host frame', frame=frame,
                                                       mcFrame=mc.get('mcFrame'), mcGeneration=mc.get('generation')))
    gaps = []
    for generation in generations:
        ids = sorted(f['frame'] for f in ordered if f['generation'] == generation)
        gaps.extend(dict(generation=generation, after=a, before=b, missing=b-a-1)
                    for a, b in zip(ids, ids[1:]) if b > a+1)
    relevant = [f for f in ordered if f.get('viewMode') == 1]
    return dict(pid=pid, creation=data.get('creation'), traceEnabledObserved=trace_enabled,
                generations=sorted(generations), uniqueFrames=len(ordered), duplicateConflictFrames=conflicts,
                frameGaps=gaps, frameReasonCounts=dict(Counter(reason(f) for f in relevant)),
                events=events, eventCount=len(events),
                eventScriptCounts=dict(Counter(event['script'] for event in events)),
                validNativeSamples=len(samples),
                provenCompositorCause=False, originalNativePixelsCompared=False,
                limits='Frame keys join exact generation/frame metadata; native Begin/End timing is a read interval. '
                       'The original logger is lossy; no missing Begin/End is inferred as an event. '
                       'A valid depth pair does not prove nonempty gun pixels; original-native video is a separate control.')


def reason(frame):
    if frame.get('viewMode') != 1:
        return 'outside first person'
    if frame.get('preserved'):
        return 'valid hand pair preserved'
    if frame.get('resumed', 0):
        return 'resumed first-person group refused'
    if frame.get('depthChanges', 0):
        return 'depth identity changed'
    if frame.get('invalid'):
        return 'invalid pair; other or unrecorded cause'
    if not frame.get('handDraws', 0):
        return 'no accepted hand draw; lens/stage/native pixels unresolved'
    if not frame.get('before'):
        return 'accepted draw without captured before'
    if not frame.get('after'):
        return 'before captured but after boundary missing'
    return 'valid pair not composed; coverage/source/HUD requires separate evidence'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--radius-ms', type=int, default=120)
    args = parser.parse_args()
    source = (ROOT / args.input).resolve()
    output = (ROOT / args.output).resolve()
    if ROOT / 'research' not in source.parents or ROOT / 'research' not in output.parents or not 0 <= args.radius_ms <= 500:
        parser.error('Use private research JSON paths and0..500ms context')
    result = analyze(json.loads(source.read_text(encoding='utf-8')), args.radius_ms)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key not in ('events', 'frameGaps', 'limits')}))


if __name__ == '__main__':
    main()
