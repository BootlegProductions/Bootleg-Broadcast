"""Inventory real catalogue film and holiday content plus December film appointments.

Read-only audit. No assumptions about playability from filenames alone.
"""
from collections import Counter,defaultdict
from pathlib import Path
import json,re,calendar
root=Path(__file__).resolve().parents[1]
cat=json.loads((root/'source-library.json').read_text())
lineups=json.loads((root/'editorial-lineups.json').read_text())
months=['october','december']
keyword=re.compile(r'christmas|xmas|santa|winter|snow|scrooge|grinch|noel|rudolph|frosty|holiday|nutcracker|yule|jingle|miser|polar express|heart[h\']?s warming|sleigh',re.I)
channels=list(lineups['channels'])
assets=defaultdict(lambda:dict(movies=[],christmas=[],other_specials=[]))
all_counts=Counter()
def routes(p):
    names=p.get('channels') or [p.get('channel')]
    if isinstance(names,str):names=[names]
    return list(dict.fromkeys(c for c in names if c in channels))
for p in cat.get('programmes',[]):
    url=p.get('url') or ''
    if not (url.startswith('https://archive.org/download/') and url.lower().endswith('.mp4')
        and not p.get('broadcast_held') and p.get('language_status') not in ['non-english','reported-non-english']
        and float(p.get('duration_seconds') or 0)>=120):continue
    typ=p.get('type');title=str(p.get('title') or '');show=str(p.get('show') or '')
    seasonal=p.get('seasonal_tags') or []
    holiday=(bool(keyword.search(title+' '+show)) or 'christmas' in seasonal or 'christmas' in (p.get('holiday_events') or []))
    group='movies' if typ=='Movie' else 'christmas' if holiday else 'other_specials' if typ=='Special' else None
    if group is None:continue
    all_counts[group]+=1
    for ch in routes(p):
        row=dict(title=title,show=show,type=typ,seconds=p.get('duration_seconds'),url=url,seasonal_tags=seasonal,
                 holiday_events=p.get('holiday_events') or [],content_id=p.get('content_id'))
        assets[ch][group].append(row)
        if group=='movies' and holiday:assets[ch]['christmas'].append(row)
schedule={}
for month in months:
    d=json.loads((root/'schedules'/f'{month}.json').read_text())
    channel_data=defaultdict(lambda:dict(movies=0,specials=0,breaks=0,film_slots=[],long_breaks=[],gap_1845=[]))
    for day in d['weeks'][0]['week']:
        for ch in day['channels']:
            for p in ch['playlist']:
                group=channel_data[ch['name']]
                if p.get('type')=='Movie':
                    group['movies']+=1
                    if len(group['film_slots'])<14:group['film_slots'].append({'day':day['date'],'time':str(round(p['broadcast_start_seconds']/3600,2)),'title':p.get('title')})
                if p.get('type')=='Special':group['specials']+=1
                if p.get('type')=='Break':
                    group['breaks']+=1
                    length=p['broadcast_end_seconds']-p['broadcast_start_seconds']
                    if length>=420:
                        if len(group['long_breaks'])<9:group['long_breaks'].append({'day':day['date'],'start':round(p['broadcast_start_seconds']/60,1),'minutes':round(length/60,1)})
                    if p['broadcast_start_seconds']<=18*3600+45*60<p['broadcast_end_seconds'] and len(group['gap_1845'])<4:
                        group['gap_1845'].append({'day':day['date'],'start':round(p['broadcast_start_seconds']/60,1),'end':round(p['broadcast_end_seconds']/60,1)})
    schedule[month]=channel_data
out={'total_catalogue':len(cat['programmes']),'eligible_counts':dict(all_counts),'library':{ch:{'counts':{k:len(v) for k,v in row.items()},'sample_movies':row['movies'][:15],'sample_christmas':row['christmas'][:17]} for ch,row in assets.items()},'schedule':schedule,'authored_film_windows':lineups.get('film_windows',[])}
(root/'channel-content-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'catalogue':out['total_catalogue'],'eligible':out['eligible_counts'],
  'per_channel':{ch:detail['counts'] for ch,detail in out['library'].items()},
  'december_movies':{ch:d['movies'] for ch,d in schedule['december'].items()},
  'long_ad_break_examples':{ch:len(d['long_breaks']) for ch,d in schedule['december'].items()}},ensure_ascii=False,indent=2))
