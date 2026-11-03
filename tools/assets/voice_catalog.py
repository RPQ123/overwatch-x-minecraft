"""抓取 ow.thnuclub.com 的中文英雄语音目录（只读 HTML 列表页，不下载音频）。

每个英雄：?tag=<英雄标签>,80&page=N（80=中文语音），只保留台词以【英雄名】开头的条目（该英雄本人说的）。
输出 research/voice-catalog-20261025/catalog.json：{hero: [{hash, text, url, sourcePage}]}。
音频地址按站点规则：https://vo.kaikai.men/<hash前两位>/<hash>.mp3
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import html, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'research/voice-catalog-20261025'
HEROES = {  # 站点标签 id -> (项目内英雄键, 站点显示名)
    10: ('bastion', '堡垒'), 11: ('dva', 'D.VA'), 12: ('genji', '源氏'), 13: ('hanzo', '半藏'), 14: ('junkrat', '狂鼠'),
    15: ('lucio', '卢西奥'), 16: ('mccree', '麦克雷'), 17: ('mei', '美'), 18: ('mercy', '天使'), 19: ('pharah', '法老之鹰'),
    20: ('reaper', '死神'), 21: ('reinhardt', '莱因哈特'), 22: ('roadhog', '路霸'), 23: ('soldier76', '士兵：76'),
    24: ('symmetra', '秩序之光'), 25: ('torbjorn', '托比昂'), 26: ('tracer', '猎空'), 27: ('widowmaker', '黑百合'),
    28: ('winston', '温斯顿'), 29: ('zarya', '查莉娅'), 30: ('zenyatta', '禅雅塔'),
}
ITEM = re.compile(r'<span class="description" title="([0-9a-f]{32})\.mp3">(.*?)</span>', re.S)


def page(tag, n):
    url = f'http://ow.thnuclub.com/?tag={tag},80&page={n}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return url, r.read().decode('utf-8', 'replace')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog, stats = {}, {}
    for tag, (key, name) in HEROES.items():
        rows, seen = [], set()
        for n in range(1, 60):
            url, text = page(tag, n)
            items = [(h, html.unescape(re.sub(r'<[^>]+>', '', t)).strip()) for h, t in ITEM.findall(text)]
            fresh = [(h, t) for h, t in items if h not in seen]
            if not fresh:
                break
            for h, t in fresh:
                seen.add(h)
                if t.startswith('【' + name + '】'):
                    rows.append(dict(hash=h, text=t, url=f'https://vo.kaikai.men/{h[:2]}/{h}.mp3',
                                     sourcePage=f'http://ow.thnuclub.com/?q={h}'))
            time.sleep(.3)
        catalog[key] = rows; stats[key] = len(rows)
        print(key, len(rows), file=sys.stderr)
    (OUT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(total=sum(stats.values()), perHero=stats), ensure_ascii=False))


if __name__ == '__main__':
    main()
