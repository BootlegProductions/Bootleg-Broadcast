"""Render the current authored lineups and three reproducible sample days."""
from pathlib import Path
from zoneinfo import ZoneInfo
import json,datetime,calendar,random
ROOT=Path(__file__).resolve().parents[1];read=lambda f:json.loads((ROOT/f).read_text());c=read('editorial-lineups.json');defs=read('editorial-series.json');report=read('editorial-review.json');year=c['year'];zone=ZoneInfo(c['timezone'])
lines=['BOOTLEG BROADCAST v0.36.1 — WRITTEN TV LINEUPS','All times Europe/London. Programme starts within each block use measured media runtimes.','Named fallbacks only cover missing/unfitting sources. No random programme selection.','After hours 02:30–07:00. December fireplace 03:00–04:00.','']
for ch,slots in c['channels'].items():
 lines+=['',ch.upper()]
 for s in slots:
  name=' → '.join(defs[k]['name'] for k in c['series_runs'][s['series'][5:]]['series']) if s['series'].startswith('@run:') else defs.get(s['series'],{'name':s['series']})['name']
  lines.append(s['at']+'  '+name+(' — double bill' if s['episodes']==2 else f' — up to {s["episodes"]} episodes' if s['episodes']>2 else ''))
 lines+=['Weekly changes: '+json.dumps(c.get('weekly_overrides',{}).get(ch,{}),ensure_ascii=False)]
 for w in c.get('film_windows',[]):
  if w['channel']==ch:lines.append(calendar.day_name[w['weekday']]+' '+w['at']+'–'+w['end']+'  '+w['block']+(' — first week only' if w.get('month_days_max') else '')+'; exact films in FILM-CALENDAR.txt')
lines+=['','SUCCESSOR RUN HANDOVERS']
for row in read('series-run-calendar.json')['runs']:
 lines.append(row['channel']+' '+row['run'].rsplit('-',1)[-1]+' '+row['starts']+' → '+(row['ends'] or 'unfinished in this calendar')+'  '+row['series_name'])
lines+=['','SOURCE LIMITS','Not scheduled: '+', '.join(defs[k]['name'] for k in report['missing_series'])+'. No compatible, identified replacement files were found for these shows. Their existing catalogue links remain searchable.','Requested UK Prank Patrol and individual Creature Comforts episodes still need usable full-episode sources.','Archive runtime metadata and uploader language declarations are evidence, not complete viewing/audio verification.','Some DVD sources have no evidenced episode names; these are labelled DVD programmes rather than given invented titles.','H2O: all 78 episodes imported; English declared by uploaders. Evangelion: 26 regular episodes from evadubbed; uploader declares original English dub.','14 February at 19:00 on Dickleodeon: H2O S03E04 — Valentine’s Day, followed by the regular series sequence.','entiretyofeva MP4s excluded because the uploader warns about incorrect audio/subtitle conversions.','', 'AAA Friday 22:00: Pilot & Oddities Night, four-week authored cycle. See CHANNEL-LINEUP.txt for all actual programme names.', 'Futurama: three episodes on Sundays at 13:00, four movies in occasional first-Sunday AAA features.', 'THREE COMPLETE SAMPLE DAYS — programme guide (short adverts/idents omitted)']
r=random.Random(35);dates=[datetime.date(year,6,r.randint(1,30)),datetime.date(year,10,r.randint(1,31)),datetime.date(year,12,r.randint(1,31))]
for date in dates:
 day=next(x for x in read('schedules/'+calendar.month_name[date.month].lower()+'.json')['weeks'][0]['week'] if int(x['date'])==date.day);start=datetime.datetime.combine(date,datetime.time(),zone).timestamp();lines+=['',str(date)+' '+date.strftime('%A')]
 for ch in day['channels']:
  lines+=['',ch['name']]
  for p in ch['playlist']:
   if p['type']=='Break':continue
   time=lambda offset:datetime.datetime.fromtimestamp(start+offset,zone).strftime('%H:%M')
   lines.append(time(p['broadcast_start_seconds'])+'–'+time(p['broadcast_end_seconds'])+'  '+p['title'])
(ROOT/'BROADCAST-LINEUP-GUIDE.txt').write_text('\n'.join(lines)+'\n')
