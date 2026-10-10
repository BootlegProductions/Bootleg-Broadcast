"""Verify actual dated features, complete runtimes and per-channel repeat gaps."""
import json,datetime,calendar,collections,re
from pathlib import Path
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[1];read=lambda f:json.loads((R/f).read_text());zone=ZoneInfo('Europe/London');plan=read('editorial-film-calendar.json');errors=[];actual={};last={};counts=collections.Counter();unique=collections.defaultdict(set);lines=[]
for month in range(1,13):
 data=read('schedules/'+calendar.month_name[month].lower()+'.json')
 for day in data['weeks'][0]['week']:
  date=datetime.date(data['schedule_year'],month,int(day['date']));start=datetime.datetime.combine(date,datetime.time(),zone).timestamp()
  for ch in day['channels']:
   for p in ch['playlist']:
    if p['type']!='Movie':continue
    label=f"{date} {ch['name']} {p['title']}";identity=(ch['name'],p['content_id']);actual[date.isoformat(),ch['name'],p['url']]=(p,start);counts[ch['name']]+=1;unique[ch['name']].add(p['content_id'])
    if identity in last and (date-last[identity]).days<28:errors.append(label+': repeat within 28 days')
    last[identity]=date
    if abs(p['duration_seconds']-(p['broadcast_end_seconds']-p['broadcast_start_seconds']))>.02:errors.append(label+': cut film')
    if not re.search(r'[a-zA-Z0-9]',re.sub(r'\(\d{4}\)','',p['title'])) or re.search(r'\.mp4|\.ia\b',p['title'],re.I):errors.append(label+': unreadable film title')
    time=datetime.datetime.fromtimestamp(start+p['broadcast_start_seconds'],zone).strftime('%H:%M');lines.append(f"{date} {time}  {ch['name']} — {p['title']}")
for row in plan['features']:
 found=actual.get((row['date'],row['channel'],row['url']))
 if not found:errors.append('Missing dated film: '+str(row));continue
 p,start=found;at=datetime.datetime.fromtimestamp(start+p['broadcast_start_seconds'],zone).strftime('%H:%M')
 if at!=row['at']:errors.append('Film outside authored start: '+str(row))
 if abs(p['duration_seconds']-row['duration_seconds'])>.02:errors.append('Film runtime changed: '+str(row))
if set(counts)!=set(read('editorial-lineups.json')['channels']):errors.append('A channel has no films')
result={'version':'0.36.1','status':'passed' if not errors else 'failed','authored_film_appointments':len(plan['features']),'actual_film_screenings':sum(counts.values()),'distinct_films':len(set().union(*unique.values())),'screenings_by_channel':dict(counts),'distinct_films_by_channel':{ch:len(ids) for ch,ids in unique.items()},'errors':errors,'scope':'Full 2026 static calendar; exact authored copies, complete measured lengths, readable film titles and 28-day per-channel film repeat gap. External playback and spoken language not re-reviewed.'}
(R/'film-validation.json').write_text(json.dumps(result,indent=2)+'\n');(R/'FILM-CALENDAR.txt').write_text('BOOTLEG BROADCAST v0.36.1 — ACTUAL FILM CALENDAR\nAll times Europe/London. '+str(sum(counts.values()))+' screenings, '+str(result['distinct_films'])+' distinct films; minimum 28-day repeat gap per channel.\n\n'+'\n'.join(sorted(lines))+'\n');print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
