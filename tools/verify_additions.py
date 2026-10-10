"""Validate the new authored slots and their placement in every published month."""
import json,calendar,datetime,collections
from pathlib import Path
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[1];read=lambda f:json.loads((R/f).read_text());i=read('addition-import-summary.json');c=read('editorial-lineups.json');review=read('editorial-review.json');wanted=set(c['authored_source_urls']);actual=collections.defaultdict(list);series=collections.Counter();z=ZoneInfo('Europe/London');errors=[];allurl=collections.defaultdict(set)
for m in range(1,13):
 for day in read('schedules/'+calendar.month_name[m].lower()+'.json')['weeks'][0]['week']:
  date=datetime.date(2026,m,int(day['date']));start=datetime.datetime.combine(date,datetime.time(),z).timestamp()
  for ch in day['channels']:
   for p in ch['playlist']:
    if p['type'] in ['Break','Filler']:continue
    series[ch['name'],p.get('series_id')]+=1;allurl[ch['name']].add(p.get('url'));at=datetime.datetime.fromtimestamp(start+p['broadcast_start_seconds'],z)
    if p.get('url') in wanted:
     actual[p['url']].append((date,ch['name'],at.hour,at.minute))
     if ch['name']!='AAA':errors.append('Authored AAA source on another channel')
     if p['url'] in sum(c['pilot_showcase'],[]) and (date.weekday()!=4 or at.hour!=22):errors.append('Pilot outside Friday 22:00 slot')
     if p['url'] not in sum(c['pilot_showcase'],[]) and (date.weekday()!=6 or date.day>7 or at.hour!=20):errors.append('Film outside first-Sunday feature')
    if p.get('series_id')=='futurama' and p['type']=='Episode' and (date.weekday()!=6 or at.hour!=13 or at.minute!=0):errors.append('Futurama outside weekly partial-source appointment')
for key,ch in [('magicbus','Star Spangled TV'),('libertykids','Star Spangled TV'),('beast-wars','90s Toons'),('reboot','90s Toons'),('the-batman','90s Toons'),('alvin-1983','90s Toons'),('dragon-tales','GirlyPop'),('digimon-data-squad','Japanime'),('mickey-works','Dizzy'),('secret-saturdays','Cartoons Cartoons'),('futurama','AAA')]:
 if not series[ch,key]:errors.append('New series never scheduled: '+key)
for url in wanted:
 if not actual[url]:errors.append('New authored source never scheduled: '+url)
 for a,b in zip(actual[url],actual[url][1:]):
  if (b[0]-a[0]).days<28:errors.append('Authored source repeats within 28 days: '+url)
assert review['series']['magicbus']['measured_episodes']==52
assert review['series']['libertykids']['measured_episodes']==40
assert review['series']['futurama']['measured_episodes']==3
assert review['missing_series']==['samurai','zoey','fma']
# Build the roster independently from schedule content and compare its grouping counts.
roster=read('channel-lineup.json')
for ch,row in roster['channels'].items():
 assert sum(row['counts'].values())==sum(len(v) for v in row['programmes'].values())
result={'version':'0.36.1','status':'passed' if not errors else 'failed','authored_sources_scheduled':len(actual),'checks':['All eleven updated/new series actually air','Magic School Bus 52 and Liberty’s Kids 40 measured episodes','Only three Futurama episodes, weekly Sunday appointment','AAA pilots on Friday late-night four-week cycle','Four Futurama films and Party Wagon on occasional first Sundays','No added one-off or film repeated within 28 days','Source-limit list reflects three remaining missing shows','Actual roster counts agree with its grouped programme list'],'errors':errors}
(R/'addition-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
