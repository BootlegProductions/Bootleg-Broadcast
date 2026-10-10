"""Check restored airtime and episode succession against the actual compiled sources."""
import json,calendar,collections,re,wave
from pathlib import Path
R=Path(__file__).resolve().parents[1];read=lambda f:json.loads((R/f).read_text());report=read('restoration-report.json');config=read('editorial-lineups.json');defs=read('editorial-series.json');review=read('editorial-review.json');cat=read('source-library.json')['programmes'];errors=[]
pools=read('broadcast-pools.json')['channels'];order={}
for ch,rows in pools.items():
 groups=collections.defaultdict(list)
 for p in rows:
  if p['content_id'] not in [x['content_id'] for x in groups[p['series_id']]]:groups[p['series_id']].append(p)
 for k,ps in groups.items():order[ch,k]=ps
actual=collections.Counter();sequence=collections.defaultdict(list)
for m in range(1,13):
 for day in read('schedules/'+calendar.month_name[m].lower()+'.json')['weeks'][0]['week']:
  for ch in day['channels']:
   for p in ch['playlist']:
    if p.get('series_id') in report['restored'] and p['type']=='Episode':actual[p['series_id']]+=1
    if p.get('editorial_run'):sequence[ch['name'],p['editorial_run']].append((m,int(day['date']),p))
for key,v in report['restored'].items():
 if not actual[key]:errors.append('Restored series has no actual airtime: '+v['name'])
# A newly restored show must progress through its evidenced order within a run.
checked=0
for (ch,rid),entries in sequence.items():
 last=None
 for m,day,p in entries:
  key=p['series_id'];ps=order.get((ch,key),[]);ids=[p['content_id'] for p in ps]
  if p['content_id'] not in ids:errors.append('Programme absent from authored source list');continue
  ix=ids.index(p['content_id'])
  if last and last[0]==key and key in report['restored'] and key.startswith('restored-'):
   prev=last[1];between=ps[prev+1:ix] if ix>prev else []
   seasonal_skips=all('christmas' in q.get('holiday_events',[]) and m!=12 for q in between)
   if ix!=prev+1 and not (ix>prev and seasonal_skips) and not (prev==len(ps)-1 and ix==0):errors.append(f'{ch} {rid}: unordered restored episode {key} {prev}→{ix}')
   checked+=1
  elif last and last[0] in report['restored'] and last[0].startswith('restored-'):
   old=order[ch,last[0]]
   # Handover happens only after the available ordered run finishes.
   if last[1]!=len(old)-1 and not all('christmas' in q.get('holiday_events',[]) for q in old[last[1]+1:]):errors.append(f'{ch} {rid}: premature handover after {last[0]} index {last[1]} of {len(old)}')
  last=(key,ix)
original_urls={url for row in read('markdown-series-recheck.json') for url in row['urls']};current_urls={p['url'] for p in cat}
if not original_urls<=current_urls:errors.append('Original markdown links removed from searchable catalogue')
for p in cat:
 if p.get('restoration_evidence') and p.get('episode_number') is not None and (p['season_number']>30 or p['episode_number']>1000):errors.append('Release resolution parsed as episode: '+p['filename'])
with wave.open(str(R/'assets/static sfx/channel-tune-short.wav')) as w:
 duration=w.getnframes()/w.getframerate()
 if not .1<=duration<=.14:errors.append('Tuning noise is too long')
if review['empty_appointments']:errors.append('Empty authored appointments')
result={'version':'0.36.1','status':'passed' if not errors else 'failed','restored_series_with_actual_airtime':len(actual),'ordered_episode_transitions_checked':checked,'original_markdown_links_preserved':len(original_urls),'tuning_noise_seconds':duration,'errors':errors,'scope':'Static authored runs, measured media metadata, full original catalogue and short tuning audio. Not a complete Archive playback, subtitle or browser visual review.'}
(R/'restoration-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({**result,'errors':errors[:20]},indent=2));raise SystemExit(bool(errors))
