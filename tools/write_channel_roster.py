"""List programmes that actually appear in the compiled calendar, excluding breaks."""
import json,collections,calendar
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];read=lambda f:json.loads((ROOT/f).read_text())
config=read('editorial-lineups.json');groups={ch:collections.defaultdict(lambda:collections.defaultdict(set)) for ch in config['channels']};dates=collections.defaultdict(lambda:collections.defaultdict(set));url_channels=collections.defaultdict(set)
for month in range(1,13):
 for day in read('schedules/'+calendar.month_name[month].lower()+'.json')['weeks'][0]['week']:
  for ch in day['channels']:
   for p in ch['playlist']:
    if p['type'] in ['Break','Ident','Advert','Filler']:continue
    kind='Series' if p['type']=='Episode' else 'Films' if p['type']=='Movie' else 'Specials and one-offs'
    name=p.get('series_label') or p['show'] if kind=='Series' else p['title']
    groups[ch['name']][kind][name].add(p['content_id']);dates[p['url']][calendar.month_name[month].lower()].add(int(day['date']));url_channels[p['url']].add(ch['name'])
result={'version':'0.36.1','year':config['year'],'scope':'Actual compiled calendar; excludes adverts, idents and fireplace filler. Series counts count programme identities, not individual episodes. Films/specials count distinct displayed titles.','channels':{}}
lines=['BOOTLEG BROADCAST v0.36.1 — WHAT ACTUALLY PLAYS','Ten channels; compiled 2026 calendar. Seasonal programmes are included.','Counts below come from the finished schedules, not the source library.','Episode counts are distinct episodes actually scheduled during this year.','Films/specials are listed separately; adverts, idents and fireplace filler are excluded.','']
for ch,categories in groups.items():
 out={kind:[{'name':name,'distinct_episodes':len(ids)} for name,ids in sorted(rows.items(),key=lambda x:x[0].casefold())] for kind,rows in categories.items()};counts={kind:len(out.get(kind,[])) for kind in ['Series','Films','Specials and one-offs']};result['channels'][ch]={'counts':counts,'programmes':out};lines+=['',ch.upper(),f"{counts['Series']} series; {counts['Films']} films; {counts['Specials and one-offs']} specials/one-offs."]
 for kind in ['Series','Films','Specials and one-offs']:
  if not out.get(kind):continue
  lines+=['',kind+':']
  lines += ['- '+p['name']+(f" ({p['distinct_episodes']} distinct episodes)" if kind=='Series' else '') for p in out[kind]]
lines+=['','NOT CURRENTLY SCHEDULED: Samurai Jack, Zoey 101, Fullmetal Alchemist/Brotherhood (unavailable original collection).','Futurama is a partial replacement: three television episodes on Sundays and four films on occasional first-Sunday AAA feature nights.','Friday 22:00 UK AAA: Pilot & Oddities Night, an explicit four-week programme.','Rude Removal uses the released censored copy. Pilots and unaired shows are not automatically classified as banned.','New source English claims come from uploaders; these are not complete independent audio reviews.','A scheduled source can subsequently disappear; browser flags hold it without shifting broadcast times.']
(ROOT/'CHANNEL-LINEUP.txt').write_text('\n'.join(lines)+'\n');(ROOT/'channel-lineup.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
# Keep the catalogue filters and actual channel assignments aligned with every finished timetable.
cat=read('source-library.json');month_numbers={calendar.month_name[i].lower():i for i in range(1,13)}
for p in cat['programmes']:
 p['scheduled_dates']={m:sorted(ds) for m,ds in dates[p['url']].items()};p['schedule_months']=sorted(month_numbers[m] for m in dates[p['url']]);p['scheduled_channels']=sorted(url_channels[p['url']])
(ROOT/'source-library.json').write_text(json.dumps(cat,ensure_ascii=False,separators=(',',':')))
print(json.dumps({ch:v['counts'] for ch,v in result['channels'].items()},indent=2))
