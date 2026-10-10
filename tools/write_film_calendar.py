"""Author explicit dated film appointments from the measured, named existing film collection."""
import json,datetime,re,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];read=lambda f:json.loads((R/f).read_text());c=read('editorial-lineups.json');cat=read('source-library.json')['programmes'];authored=set(c['authored_source_urls']);pools=collections.defaultdict(list);seen=collections.defaultdict(set)
for p in cat:
 if p.get('type')!='Movie' or p['url'] in authored or p.get('broadcast_held') or not p['url'].endswith('.mp4') or p.get('language_status') in ['non-english','reported-non-english'] or p.get('duration_seconds',0)<1800:continue
 for ch in p.get('channels',[p.get('channel')]):
  if p['content_id'] in seen[ch]:continue
  seen[ch].add(p['content_id']);pools[ch].append(p)
last={};appointments={};details=[]
for offset in range(366):
 date=datetime.date(c['year'],1,1)+datetime.timedelta(days=offset)
 if date.year!=c['year']:break
 windows=[w for w in c['film_windows'] if w['weekday']==date.weekday() and date.day<=w.get('month_days_max',31)]
 if (date.month,date.day)==(3,17):windows+=c['holiday_film_windows']
 for w in windows:
  ch=w['channel'];start,end=[sum(int(x)*mult for x,mult in zip(t.split(':'),[3600,60])) for t in [w['at'],w['end']]]
  preferred=['halloween','horror'] if date.month==10 else ['christmas','winter','snow'] if date.month==12 else [w.get('event')] if w.get('event') else ['easter'] if date==datetime.date(2026,4,5) else []
  def eligible(p):
   tags=p.get('holiday_events',[]);name=p['title'].lower()
   if 'nightmare before christmas' in name:
    if date.month not in [10,12]:return False
   elif 'christmas' in tags or 'christmas' in p.get('seasonal_tags',[]):
    if date.month!=12:return False
   elif tags and not any((t=='st-patrick' and (date.month,date.day)==(3,17)) or (t=='easter' and date==datetime.date(2026,4,5)) for t in tags):return False
   return p['duration_seconds']<=end-start and offset-last.get((ch,p['content_id']),-10000)>=c['movie_cooldown_days']
  choices=[p for p in pools[ch] if eligible(p)]
  # Alternate Pokemon with other anime features outside the themed months.
  theme=[p for p in choices if any(t in p.get('seasonal_tags',[])+p.get('holiday_events',[]) for t in preferred)]
  if theme:choices=theme
  elif ch=='Japanime' and date.month not in [10,12]:
   pokemon=(offset//7)%2==1;alternate=[p for p in choices if bool(re.search(r'pok[eé]mon',p['title'],re.I))==pokemon]
   if alternate:choices=alternate
  choices.sort(key=lambda p:(last.get((ch,p['content_id']),-10000),p['title'].casefold()))
  if choices:
   p=choices[0];key=date.isoformat()+'|'+ch+'|'+w['at'];appointments[key]=p['url'];details.append({'date':date.isoformat(),'channel':ch,'at':w['at'],'end':w['end'],'title':p['title'],'url':p['url'],'content_id':p['content_id'],'duration_seconds':p['duration_seconds'],'block':w['block']});last[ch,p['content_id']]=offset
(R/'editorial-film-calendar.json').write_text(json.dumps({'year':c['year'],'timezone':'Europe/London','note':'Explicit feature choices for the finished calendar. Edit appointments to choose a specific film; build_broadcast.py does not substitute a random film.','appointments':appointments,'features':details},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'dated_film_appointments':len(details),'unique_films':len(set(p['content_id'] for p in details)),'by_channel':dict(collections.Counter(p['channel'] for p in details))},indent=2))
