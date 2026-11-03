"""语音挂接：第五次反馈明确恢复的逐条审核清单；只生成元数据，不下载/修改私有目录。"""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
# 逐英雄人工阅读目录字幕后固定一条就绪提示，不把战术邀请/后期新大招混进来。
READY={
 'bastion':'337a98557c065b741efa89f5c1800c97',
 'dva':'1b0980668bd985f2824f6f4463a6f665',
 'genji':'44db1ab6866677ef8a566869f0ac64fe',
 'hanzo':'1619618f07582ad5a7802eb772e3b757',
 'junkrat':'c3cc1c4813f4fb7cd8634d5ba6f9960b',
 'lucio':'8f9e7bac5bd84b7c7f5be28515297e52',
 'mccree':'fa261aeabadbefef92e5ef5e5a978eff',
 'mei':'682b58757ead92c789e731cfe3196d2d',
 'mercy':'3207ff3aedefe82f81513d29d401945e',
 'pharah':'a804d58c1a265c4bd06ba0b405fba33f',
 'reaper':'dc882495dd606a4145c202b3204ac627',
 'reinhardt':'0d1a66cccb98abf20ebcd02e03f46366',
 'roadhog':'60a474ba32be67f1b4bb93928cd27268',
 'soldier76':'39b549cb40fefd7aa7e4f54ef2b81a39',
 'symmetra':'d7b120fbd11bf5d7849b1c6fa011a8e4',
 'torbjorn':'968610d1962f31ccfa25b0ad0a071971',
 'tracer':'3844cff1fcc089365aa1690433a8eda4',
 'widowmaker':'7d059c52bccaca932de36fdef2e3e027',
 'winston':'0f967d1531a8e0299aac2f47714c2de0',
 'zarya':'4ea3e1521b0d8c64aabb52f9b26185ae',
 'zenyatta':'79a6aa92a3e2c462f15bf8fda7237394',
}
# 堡垒官方电子音是此次用户明确恢复的例外；不复活其选人/跳跃等语气声。
CAST={'bastion':'5a449ed346d47a7e0180fdda14770b6e',
      'junkrat':'b0ae530103d62c2092581cd00b8e3cc6',
      'zenyatta':'374032df1e8ffb5bcad2af2b695274d9'}


def selected(hero,event,hash_):
    return (READY if event=='ult_ready' else CAST if event=='ult_cast' else {}).get(hero)==hash_


def additions():
    catalog=json.loads((ROOT/'research/voice-catalog-20261025/classified.json').read_text(encoding='utf-8'))
    result=[]
    for event,chosen in [('ult_ready',READY),('ult_cast',CAST)]:
        for hero,hash_ in sorted(chosen.items()):
            row=next(r for r in catalog[hero] if r['hash']==hash_)
            if row['event']!=event or row.get('version_status')=='post_1_30':raise ValueError('Restored clip event/version changed')
            u=urlparse(row['url'])
            if u.scheme not in {'http','https'} or u.hostname not in {'vo.kaikai.men','ow.thnuclub.com'}:raise ValueError('Unapproved source')
            result.append(dict(hero=hero,hash=hash_,url=row['url'],event=event))
    return result


def generate():
    out=ROOT/'research/voice-20261027-feedback5';out.mkdir(parents=True,exist_ok=True)
    rows=additions();(out/'download-additions.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(added=len(rows),ult_ready=len(READY),ult_cast=len(CAST),estimatedKB=len(rows)*25)))


if __name__=='__main__':generate()
