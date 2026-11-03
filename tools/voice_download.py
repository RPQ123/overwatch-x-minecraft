"""按 research/voice-catalog-20261025/download.json 下载中文英雄语音（私有素材，不进 JAR、不进提交）。

保存到 ~/.universal-modder/assets/ow1-zhcn-2016/thnu-full/<hero>/<hash>.mp3，已存在的跳过；
校验 MP3 文件头，写 manifest.json。20261026b起只允许默认白名单台词；旧可选参数不再恢复已清退音频。
"""
import argparse, hashlib, json, sys, time, urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LIST = ROOT / 'research/voice-catalog-20261025/download.json'
DEST = Path.home() / '.universal-modder/assets/ow1-zhcn-2016/thnu-full'


def is_mp3(b):
    return len(b) > 512 and (b[:3] == b'ID3' or (b[0] == 0xFF and b[1] & 0xE0 == 0xE0))


def approved_url(row):
    u=urlparse(row['url'])
    return (u.scheme in {'http','https'} and u.hostname in {'vo.kaikai.men','ow.thnuclub.com'}
            and u.username is None and u.password is None and u.path.endswith('/'+row['hash']+'.mp3'))


class ApprovedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self,row):self.row=row
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not approved_url(dict(self.row,url=newurl)):raise ValueError('Unapproved redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--optional', action='store_true'); p.add_argument('--list', type=Path, default=LIST)
    p.add_argument('--dry-run',action='store_true',help='只读统计本地可复用/待下载；不联网、不写私有目录'); a = p.parse_args()
    allowed = {(r['hero'],r['event'],r['hash']) for r in json.loads((ROOT/'research/voice-20261026b/download-default.json').read_text(encoding='utf-8'))}
    requested=json.loads(a.list.read_text(encoding='utf-8'))
    rows = [r for r in requested if (r['hero'],r['event'],r['hash']) in allowed]
    if len(rows)!=len(requested):raise ValueError('清单含未准入条目；先运行prune_voice_defaults.py更新默认白名单')
    mpath = DEST / 'manifest.json'
    manifest = json.loads(mpath.read_text(encoding='utf-8')) if mpath.exists() else {}
    if a.dry_run:
        downloadable=[r for r in rows if not r.get('localOnly')]
        if any(not approved_url(r) for r in downloadable):raise ValueError('Unapproved download URL')
        local=sum(is_mp3((DEST/r['hero']/(r['hash']+'.mp3')).read_bytes()) for r in downloadable if (DEST/r['hero']/(r['hash']+'.mp3')).is_file())
        print(json.dumps(dict(requested=len(rows),localReusable=local,needDownload=len(downloadable)-local,localOnly=len(rows)-len(downloadable),dryRun=True)));return
    DEST.mkdir(parents=True, exist_ok=True)
    # 语音挂接：旧manifest也执行默认准入；仅修剪条目，不删除已有音频。
    filtered = {h:r for h,r in manifest.items() if (r.get('hero'),r.get('event'),h) in allowed}
    if len(filtered) != len(manifest):
        backup=mpath.with_name('manifest.before-20261026b-voice.json')
        if not backup.exists(): backup.write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
        manifest=filtered
    got = skipped = failed = reused = 0; total = 0
    for i, r in enumerate(rows):
        f = DEST / r['hero'] / (r['hash'] + '.mp3')
        if f.exists() and r['hash'] in manifest:
            skipped += 1; continue
        if r.get('localOnly'):
            failed += 1; print('local-only: run tools/prune_voice_defaults.py --apply-private first',file=sys.stderr); continue
        try:
            if not approved_url(r):raise ValueError('Unapproved download URL')
            # 语音挂接：修剪只删清单、不删MP3；恢复条目时校验本地MP3并重建SHA，避免再次下载。
            existing=f.is_file();b=f.read_bytes() if existing else None
            if not existing:
                req = urllib.request.Request(r['url'], headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://ow.thnuclub.com/'})
                with urllib.request.build_opener(ApprovedRedirect(r)).open(req, timeout=30) as resp:
                    if not approved_url(dict(r,url=resp.geturl())):raise ValueError('Unapproved redirect')
                    b = resp.read()
            if not is_mp3(b):
                raise ValueError('not mp3')
            if not existing:f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(b)
            manifest[r['hash']] = dict(hero=r['hero'], event=r['event'], optional=bool(r.get('optional')), url=r['url'],
                                       sourcePage=f"http://ow.thnuclub.com/?q={r['hash']}", bytes=len(b),
                                       sha256=hashlib.sha256(b).hexdigest(), reusedLocal=existing,earliestRecordingDateVerified=False)
            if existing:reused+=1
            else:got += 1; total += len(b)
        except Exception as e:
            failed += 1; print('fail', r['hero'], r['hash'], repr(e)[:80], file=sys.stderr)
        if (i + 1) % 100 == 0:
            mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            print(f'{i + 1}/{len(rows)} got={got} MB={total / 1e6:.1f}', file=sys.stderr)
        time.sleep(.05)
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(dict(requested=len(rows), downloaded=got,reusedLocal=reused, skipped=skipped, failed=failed, MB=round(total / 1e6, 2))))
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
