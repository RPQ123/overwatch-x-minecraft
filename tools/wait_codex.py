"""阻塞等待一个或多个 Codex 线程的当前回合结束（读本地 ~/.codex/sessions 的 rollout 记录，不走网络）。

用法（Claude 派活后在后台运行，线程全部结束时进程退出，从而唤醒 Claude）：
    .venv/Scripts/python.exe tools/wait_codex.py <thread_id> [<thread_id> ...] [--timeout 10800]
判定：rollout 文件里最后一个 task_started 之后出现 task_complete 或 turn_aborted。
"""
import argparse, json, time
from pathlib import Path

SESSIONS = Path.home() / '.codex' / 'sessions'
END = {'task_complete', 'turn_aborted'}


def rollout(thread):
    found = sorted(SESSIONS.glob(f'*/*/*/rollout-*-{thread}.jsonl'), key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None


def state(thread):
    path = rollout(thread)
    if path is None:
        return 'missing'
    last = None
    with path.open(encoding='utf-8', errors='replace') as f:
        for line in f:
            if '"task_started"' not in line and '"task_complete"' not in line and '"turn_aborted"' not in line:
                continue
            try:
                kind = json.loads(line).get('payload', {}).get('type')
            except ValueError:
                continue
            if kind == 'task_started' or kind in END:
                last = kind
    return 'done' if last in END else 'running' if last == 'task_started' else 'unknown'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('threads', nargs='+')
    p.add_argument('--timeout', type=float, default=10800)
    p.add_argument('--interval', type=float, default=15)
    a = p.parse_args()
    # 刚派出的回合可能还没写 task_started：先给 60 s 让它出现，避免把上一回合的 complete 当成结束。
    grace = time.monotonic() + 60
    deadline = time.monotonic() + a.timeout
    seen_running = set()
    while True:
        states = {t: state(t) for t in a.threads}
        seen_running |= {t for t, s in states.items() if s == 'running'}
        done = all(s == 'done' and (t in seen_running or time.monotonic() > grace) for t, s in states.items())
        if done or time.monotonic() > deadline:
            print(json.dumps({'allDone': done, 'states': states}, ensure_ascii=False))
            return 0 if done else 1
        time.sleep(a.interval)


if __name__ == '__main__':
    raise SystemExit(main())
