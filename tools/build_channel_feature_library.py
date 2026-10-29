"""Build the channel Film and Christmas guide from existing verified metadata.

Existing programme URLs and durations are taken from source-library.json.
This does not make unverified new links or alter authored broadcast slots.
"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,re,urllib.parse
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'source-library.json').read_text(encoding='utf-8'))
channels=list(json.loads((root/'editorial-lineups.json').read_text(encoding='utf-8'))['channels'])
christmas_word=re.compile(
 r"\b(?:christmas|x[\s-]?mas|santa(?:'s)?|grinch|rudolph|frosty|"
 r"scrooge|no[eë]l|nutcracker|jingle|yule|yuletide|"
 r"polar express|holiday special|holidays|winter vacation|"
 r"hearth'?s warming|miser brothers|snowman)\b",re.I)
non_english={'non-english','reported-non-english'}
def channels_of(p):
    names=p.get('channels') or [p.get('channel')]
    if isinstance(names,str):names=[names]
    return [n for n in dict.fromkeys(names) if n in channels]
def normalized(s):
    return re.sub(r'[^a-z0-9]','',str(s or '').casefold())
candidates=defaultdict(dict)
for p in data.get('programmes',[]):
    url=p.get('url') or ''
    if not url.startswith('https://archive.org/download/') or not url.lower().endswith('.mp4'):
        continue
    if p.get('broadcast_held') or p.get('language_status') in non_english:continue
    try:duration=float(p.get('duration_seconds') or 0)
    except(ValueError,TypeError):continue
    if duration<120:continue
    kind=p.get('type') or ''
    title=str(p.get('title') or '').strip()
    show=str(p.get('show') or '')
    tags=p.get('seasonal_tags') or []
    events=p.get('holiday_events') or []
    winter=('christmas' in tags or 'christmas' in events or bool(christmas_word.search(title)))
    movie=kind=='Movie' and duration>=1500
    if not movie and not winter:continue
    if not title or not url:continue
    identifier=urllib.parse.urlsplit(url).path.split('/')[2] if '/download/' in url else ''
    row={'id':'catalogue-'+hashlib.sha1(url.encode()).hexdigest()[:12],
         'title':title,'show':show,'channel':None,
         'type':kind,'url':url,'duration_seconds':round(duration,3),
         'movie':movie,'christmas':winter,
         'content_id':p.get('content_id') or None,
         'source_page':p.get('source_page') or ('https://archive.org/details/'+identifier if identifier else ''),
         'library_origin':'existing_catalogue'}
    for channel in channels_of(p):
        dedup=normalized(title)
        if not dedup:continue
        item=dict(row,channel=channel)
        before=candidates[channel].get(dedup)
        # Preserve full feature vs a short excerpt and prefer a curated original.
        priority=(bool(p.get('preferred_source')),p.get('catalogue_status')=='broadcast',
                  not url.endswith('.ia.mp4'),duration)
        if not before or priority>before[0]:
            candidates[channel][dedup]=(priority,item)
records=[]
report={'from_catalogue':len(data.get('programmes',[])),'by_channel':{}}
for channel in channels:
    rows=[row for _,row in candidates[channel].values()]
    rows.sort(key=lambda r:(not r['christmas'],not r['movie'],r['title'].casefold()))
    records.extend(rows)
    report['by_channel'][channel]={'movies':sum(p['movie'] for p in rows),
        'christmas':sum(p['christmas'] for p in rows),
        'total':len(rows),
        'example_movies':[p['title'] for p in rows if p['movie']][:8],
        'example_christmas':[p['title'] for p in rows if p['christmas']][:8]}
report['total_channel_records']=len(records)
report['note']='Catalogue metadata only; no browser playback or content rights verification from this build.'
asset='/* Browsable existing movie and Christmas programme source listings, filtered by channel. */\n'+\
      'globalThis.BOOTLEG_FEATURE_LIBRARY='+json.dumps({'version':'2026-10-29','programmes':records},
        ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n'
(root/'channel-feature-library.js').write_text(asset,encoding='utf-8')
(root/'channel-feature-library-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
