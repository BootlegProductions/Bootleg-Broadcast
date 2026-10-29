"""Add extra short, measured catalogue programmes for continuity gaps.

Only direct non-held MP4 Episode/Special items, with a spread of shows per
channel. This is a small runtime pool, not a rewrite of the TV timetable.
"""
from pathlib import Path
from collections import defaultdict,Counter
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
catalogue=json.loads((ROOT/'source-library.json').read_text(encoding='utf-8'))['programmes']
names=list(json.loads((ROOT/'editorial-lineups.json').read_text(encoding='utf-8'))['channels'])
script=(ROOT/'continuity-pools.js').read_text(encoding='utf-8')
continuity=json.loads(script.split('globalThis.BOOTLEG_CONTINUITY=',1)[1].rsplit(';',1)[0])['channels']
already={ch:{p.get('url') for p in clips} for ch,clips in continuity.items()}
by=defaultdict(list)
for p in catalogue:
    url=str(p.get('url') or '')
    if not url.startswith('https://archive.org/download/') or not url.endswith('.mp4') or '.ia.mp4' in url:continue
    if p.get('broadcast_held') or p.get('language_status') in ('non-english','reported-non-english'):continue
    if p.get('type') not in ('Episode','Special'):continue
    try:dur=float(p.get('duration_seconds') or 0)
    except(ValueError,TypeError):continue
    if not 220<=dur<=780:continue
    channels=p.get('channels') or [p.get('channel')]
    if isinstance(channels,str):channels=[channels]
    show=str(p.get('series_id') or p.get('show') or '').casefold()
    title=str(p.get('title') or '').strip()
    if not title or not show:continue
    # Do not put DVD menus, chapter rips, credits or generic extras on air
    # merely because they happen to be several minutes long.
    technical=re.compile(r'disc[-_ ]*\d|dvd|blu.?ray|\biso\b|\bmenus?\b|\btrailer\b|\bteaser\b|'
        r'music video|behind.the.scenes|making.of|commentary|\bcredits\b|\bbumpers?\b|'
        r'\bopening\b|\bending\b|\bpromo\b|\bq ?& ?a\b',re.I)
    if technical.search(title) or technical.search(str(p.get('show') or '')):continue
    if len(re.findall(r'[A-Za-z]{3,}',title))<3 or re.fullmatch(r'(?:EP|Episode|Special)\s*\d+',title,re.I):continue
    if re.search(r'queen.?s blade|berserk|high school dxd|prison school|hentai',title+' '+str(p.get('show') or ''),re.I):continue
    tags=list(p.get('seasonal_tags') or [])
    events=list(p.get('holiday_events') or [])
    if re.search(r'christmas|xmas|santa|rudolph|frosty|yule',title,re.I) and 'christmas' not in tags:
        tags.append('christmas')
    if re.search(r'halloween|trick.or.treat|spooky|jack.o.lantern',title,re.I) and 'halloween' not in tags:
        tags.append('halloween')
    row={k:p[k] for k in ['type','show','title','url','duration_seconds','duration_evidence','series_id','content_id','season','episode','season_number','episode_number','source_page','language_status'] if k in p}
    row.update(duration_seconds=round(dur,3),seasonal_tags=tags,holiday_events=events)
    for ch in dict.fromkeys(channels):
        if ch in names and url not in already.get(ch,set()):
            by[ch].append((show,row))
out={}
report={}
for ch in names:
    unique={}
    for show,row in by[ch]:
        key=row.get('content_id') or row['url']
        current=unique.get(key)
        if not current or len(row['title'])>len(current[1]['title']):unique[key]=(show,row)
    # Spread across shows rather than selecting hundreds from one series.
    ranked=sorted(unique.values(),key=lambda pair:(
        int(pair[1]['duration_seconds']//120),
        hashlib.sha1(pair[1]['url'].encode()).hexdigest()))
    selected=[];show_counts=Counter()
    for show,row in ranked:
        if show_counts[show]>=7:continue
        selected.append(row);show_counts[show]+=1
        if len(selected)>=180:break
    out[ch]=selected
    report[ch]={'extra_short_programmes':len(selected),
       'below_six_minutes':sum(p['duration_seconds']<=360 for p in selected),
       'six_to_ten_minutes':sum(360<p['duration_seconds']<=600 for p in selected),
       'ten_to_thirteen_minutes':sum(600<p['duration_seconds']<=780 for p in selected),
       'sample_titles':[p['title'] for p in selected[:12]]}
artifact='/* Measured catalogue shorts for broadcast continuity; no invented runtimes. */\n'+\
 'globalThis.BOOTLEG_EXTRA_SHORTS='+json.dumps({'version':'2026-10-29','channels':out},
  ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n'
(ROOT/'channel-shorts.js').write_text(artifact,encoding='utf-8')
(ROOT/'channel-shorts-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
