"""Publish individually measured Nick uploader episodes and a few family movies.

Skip LazyTown (already in catalogue) and duplicate Elmo Christmas Countdown.
Make original episode files available on demand; a small sample is eligible
for normal continuity gaps without replacing authored broadcast appointments.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'nick-uploader-programmes-review.json').read_text())
catalogue=json.loads((ROOT/'source-library.json').read_text())['programmes']
existing_urls={p.get('url') for p in catalogue}
norm=lambda s: re.sub('[^a-z0-9]','',str(s or '').lower())
existing_titles={norm(p.get('title')) for p in catalogue}
series={'I Spy','Figure It Out','Splatalot'}
films={"Piglet's Big Movie","Follow That Bird","Lost And Found","A Child's Christmas"}
seen_ids=set();used_urls=set();episodes=[];features=[];skipped=[]
for source in inventory['sources']:
 if source['name'] not in series|films:continue
 for f in source['videos']:
  if not f.get('url') or not f['url'].endswith('.mp4') or f['seconds']<240:continue
  url=f['url'];filename=f['filename']
  if url in existing_urls or url in used_urls:continue
  if source['name'] in series:
   m=(re.search(r'[sS](\d{1,2})\s*[-._ ]*[eE](\d{1,3})',filename)
      or re.search(r'season[_\W]*(\d{1,2})[_\W]*episode[_\W]*(\d{1,3})',filename,re.I))
   if not m:
    skipped.append({'name':filename,'reason':'Could not confirm season/episode'});continue
   season,ep=map(int,m.groups())
   cid='nick-uploader:'+norm(source['name'])+':'+str(season)+':'+str(ep)
   if cid in seen_ids:
    skipped.append({'name':filename,'reason':'Repeated season/episode'});continue
   suffix='' if source['name']=='Figure It Out' else re.sub(r'^.*?[sS]\d{1,2}\s*[-._ ]*[eE]\d{1,3}\s*[-._ ]*','',filename).removesuffix('.mp4')
   suffix=re.sub(r'[_]+',' ',suffix).strip(' -_.')
   if re.match(r'^[a-f0-9]{10,}$',suffix.lower()):suffix=''
   title=source['name']+' — S%02dE%02d'%(season,ep)+((' — '+suffix) if suffix else '')
   row={'type':'Episode','show':source['name'],'title':title,'channel':source['channel'],
    'url':url,'filename':filename,'archive_identifier':source['identifier'],
    'source_page':'https://archive.org/details/'+source['identifier'],
    'duration_seconds':f['seconds'],'season_number':season,'episode_number':ep,
    'content_id':cid,'id':'archive-'+hashlib.sha1(url.encode()).hexdigest()[:15],
    'seasonal_tags':[],'language_status':'unknown',
    'duration_evidence':'Internet Archive original MP4 metadata length',
    'source_verification':'metadata-listed; playback and audio not independently confirmed'}
   episodes.append(row)
  else:
   # The catalogue sometimes has the same film under a slightly different title.
   # Record ambiguous matches for review rather than duplicate it.
   if norm(source['name']) in existing_titles:
    skipped.append({'name':source['name'],'reason':'Existing catalogue title'});continue
   name=source['name']
   typ='Movie' if f['seconds']>=3600 else 'Special'
   title=name+(' (2008)' if name=='Lost And Found' else '')
   row={'type':typ,'show':name,'title':title,'channel':source['channel'],
    'url':url,'filename':filename,'archive_identifier':source['identifier'],
    'source_page':'https://archive.org/details/'+source['identifier'],
    'duration_seconds':f['seconds'],'content_id':'nick-uploader:'+norm(name),
    'id':'archive-'+hashlib.sha1(url.encode()).hexdigest()[:15],
    'seasonal_tags':['christmas'] if 'Christmas' in name else [],
    'language_status':'unknown','duration_evidence':'Internet Archive original MP4 metadata length',
    'source_verification':'metadata-listed; playback and audio not independently confirmed'}
   features.append(row)
  used_urls.add(url);seen_ids.add(cid if source['name'] in series else row['content_id'])
episodes.sort(key=lambda x:(x['show'],x['season_number'],x['episode_number']))
# Do not stuff hundreds of episodes into the on-air filler pool.
# Offer a small curated starter set, still subject to free interval length.
starter=[]
for show in sorted(series):
 selected=[p for p in episodes if p['show']==show]
 starter.extend(selected[:26])
out={'version':'2026-10-29','programmes':episodes+features}
code='/* Original episode files from the Nickelodeon ident uploader. */\n(function(root){\n'+\
 ' const data='+json.dumps(out,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n'+\
 ' root.BOOTLEG_UPLOADER_PROGRAMMES=data;\n'+\
 ' const pool=root.BOOTLEG_CONTINUITY?.channels?.Dickleodeon;\n'+\
 ' if(Array.isArray(pool))for(const p of data.programmes){\n'+\
 '  if(!p.continuity_candidate)continue;\n'+\
 '  if(!pool.some(x=>x.content_id===p.content_id||x.url===p.url))pool.push(p);\n'+\
 ' }\n})(globalThis);\n'
eligible={p['content_id'] for p in starter}
for p in out['programmes']:p['continuity_candidate']=p['content_id'] in eligible
# Re-render after marking selected candidates.
code='/* Exact-file original episodes and movies from Nick uploader. */\n(function(root){\n'+\
 ' const data='+json.dumps(out,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n'+\
 ' root.BOOTLEG_UPLOADER_PROGRAMMES=data;\n'+\
 ' const pool=root.BOOTLEG_CONTINUITY?.channels?.Dickleodeon;\n'+\
 ' if(Array.isArray(pool))for(const p of data.programmes){\n'+\
 '  if(!p.continuity_candidate)continue;\n'+\
 '  if(!pool.some(x=>x.content_id===p.content_id||x.url===p.url))pool.push(p);\n'+\
 ' }\n})(globalThis);\n'
(ROOT/'nick-uploader-programmes.js').write_text(code,encoding='utf-8')
counts=Counter(p['show'] for p in episodes)
report={'new_episode_sources':len(episodes),'episode_series':dict(counts),
 'on_demand_films_and_specials':[{'title':p['title'],'channel':p['channel'],'minutes':round(p['duration_seconds']/60,1)} for p in features],
 'airing_candidates':len(starter),'duplicates_skipped':skipped[:40],
 'note':'Metadata-backed original MP4 files; subset eligible for continuity where gaps fit. No authored feature slots displaced.'}
(ROOT/'nick-uploader-programmes-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(report,indent=2,ensure_ascii=False))
