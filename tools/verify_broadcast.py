"""Verify every finished channel-day, including clocks changing in the UK."""
import json,datetime,calendar,collections
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];zone=ZoneInfo('Europe/London');errors=[];counts=collections.Counter();sizes={};breaks=json.loads((ROOT/'channel-breaks.json').read_text())['channels'];days=0
for file in sorted((ROOT/'schedules').glob('*.json')):
 data=json.loads(file.read_text());month=list(calendar.month_name).index(file.stem.title());year=data['schedule_year'];sizes[file.name]=file.stat().st_size
 for day in data['weeks'][0]['week']:
  date=datetime.date(year,month,int(day['date']));start=datetime.datetime.combine(date,datetime.time(),zone).timestamp();end=datetime.datetime.combine(date+datetime.timedelta(days=1),datetime.time(),zone).timestamp();length=end-start
  for ch in day['channels']:
   days+=1;last=0;seen=set()
   for p in ch['playlist']:
    a=p['broadcast_start_seconds'];b=p['broadcast_end_seconds'];label=f'{date} {ch["name"]}: {p["title"]}'
    if abs(a-last)>.01:errors.append(label+f': gap/overlap {last}→{a}')
    if b<=a:errors.append(label+': nonpositive slot')
    last=b
    if p['type']=='Break':
     duration=sum(breaks[ch['name']]['ident']['duration_seconds'] if i==-1 else breaks[ch['name']]['adverts'][i]['duration_seconds'] for i in p['break_sequence'])
     if duration+0.02<b-a:errors.append(label+': insufficient measured break clips')
     continue
    if p['type']=='Filler':continue
    counts['programme_slots']+=1
    identity=p['content_id']
    if identity in seen:errors.append(label+': repeated content in same UK day')
    seen.add(identity)
    if abs((b-a)-p['duration_seconds'])>.01:errors.append(label+': airtime differs from measured length')
    if '.mp4' in p['title'] or not p['title'].strip():errors.append(label+': raw or blank title')
    if 'christmas' in p.get('holiday_events',[]) and month!=12 and not (month==10 and 'nightmare before christmas' in p['title'].lower()):errors.append(label+': Christmas outside December')
    if ch['name']=='Cartoons Cartoons' and '08:00'<=datetime.datetime.fromtimestamp(start+a,zone).strftime('%H:%M')<'12:00' and p.get('series_id') not in ['jetsons','flintstones','tom-jerry','wacky','looney','popeye']:errors.append(label+': unsuitable classics slot')
    if ch['name']=='Japanime' and p['type']=='Movie' and p['duration_seconds']>=3600 and (date.weekday()!=5 or not 19<=datetime.datetime.fromtimestamp(start+a,zone).hour<=21):errors.append(label+': anime film outside weekly cinema')
   if abs(last-length)>.01:errors.append(f'{date} {ch["name"]}: day does not end at UK midnight {last}/{length}')
for ch,d in breaks.items():
 for p in d['adverts']:
  t=p['title'].lower()
  if any(x in t for x in ['cartoon network','toon city','cn city']) and ch!='Cartoons Cartoons':errors.append('CN bumper on '+ch)
  if 'disney' in t and ch!='Dizzy':errors.append('Disney bumper on '+ch)
result={'version':'0.36.1','channel_days':days,**counts,'month_file_bytes':sizes,'errors':errors,'status':'passed' if not errors else 'failed','scope':'Static schedule integrity, measured runtimes, same-day duplicates, day coverage including UK daylight saving, brand routing, classic mornings and weekly anime films. Full external video playback/audio was not tested.'}
(ROOT/'release-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({**result,'month_file_bytes':{},'errors':errors[:20]},indent=2));raise SystemExit(bool(errors))
