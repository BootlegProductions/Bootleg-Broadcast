"""Compile hand-authored TV lineups into static monthly schedules. Python stdlib only.
Run refresh_runtimes.py first, then: python tools/build_broadcast.py [year]
Unknown-length sources remain searchable and are never given guessed airtime.
"""
import json,re,math,datetime,calendar,sys,urllib.parse,collections,unicodedata
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];ZONE=ZoneInfo('Europe/London');UTC=datetime.timezone.utc
read=lambda name:json.loads((ROOT/name).read_text())
write=lambda name,data:(ROOT/name).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
config=read('editorial-lineups.json');YEAR=int(sys.argv[1]) if len(sys.argv)>1 else config['year'];defs=read('editorial-series.json');catalogue=read('source-library.json');records=catalogue['programmes'];oldbreaks=read('seasonal-breaks.json');adverts=read('adverts.json')['channels'];local=read('tools/local-runtimes.json');metadata={}
for file in (ROOT/'tools/runtime-cache').glob('*.json'):
 d=json.loads(file.read_text());metadata[d['identifier']]={p['name']:p for p in d['files']}
lookups={s:key for key,d in defs.items() for s in d['shows']};profiles=collections.defaultdict(list);report={'year':YEAR,'schema':'written-tv-v1','missing_runtime':[],'missing_series':[],'substitutions':collections.Counter(),'empty_appointments':collections.Counter(),'series':{},'metadata_collections':len(metadata),'channel_days':0,'programme_slots':0,'break_seconds':0,'filler_minutes_by_channel':collections.defaultdict(float),'notes':['Titles use collection/filename evidence; no invented episode names.','IA lengths and local ffprobe durations are measurements, not complete playback or language reviews.','Editorial assignments are in editorial-lineups.json. Rebuild next year with tools/build_broadcast.py YEAR.']}
def number(value,default=None):
 try:return int(value)
 except (TypeError,ValueError):return default
def source_fields(p):
 u=p.get('url','');identifier=p.get('archive_identifier');filename=p.get('filename')
 if not identifier:
  tail=u.split('/download/',1)[-1] if '/download/' in u else u.split('/items/',1)[-1]
  if tail!=u and '/' in tail:identifier,filename=tail.split('/',1);filename=urllib.parse.unquote(filename)
 if not filename and '/download/' in u:filename=urllib.parse.unquote(u.split('/download/',1)[1].split('/',1)[1])
 return identifier,filename
BAD_AUDIO=re.compile(r'serbian|croatian|greek|spanish|french|german|italian|russian|portuguese|castellano|latino|español',re.I)
BAD_EXTRA=re.compile(r'\b(?:menu|trailer|teaser|disc\s*\d|bonus|opening|credits|commercial|promo)\b|(?:VTS_\d|SUPER_MARIO_BROS_VOL)',re.I)
def decorate(p):
 p=dict(p);identifier,filename=source_fields(p);f=metadata.get(identifier,{}).get(filename,{})
 length=f.get('length') or f.get('duration')
 try:duration=float(length or p.get('duration_seconds') or 0)
 except (ValueError,TypeError):duration=0
 if duration>0:p['duration_seconds']=round(duration,3);p['duration_evidence']='IA exact filename length' if length else p.get('duration_evidence','Previously recorded runtime')
 p.setdefault('source_show',p.get('show'));key=lookups.get(p.get('source_show')) or (p.get('series_id') if p.get('series_id') in defs else None);stem=(filename or p.get('title','')).rsplit('/',1)[-1];text=urllib.parse.unquote(stem)
 text=text.replace('_',' ')
 season=number(p.get('season_number',p.get('season')),1);episode=number(p.get('episode_number',p.get('episode')));part=p.get('episode_part','')
 m=re.search(r'(?:\bS(\d+)\s*[._ -]*E|\b(\d+)x)(\d+)([abc](?=[^a-z]|$))?',text,re.I) or re.search(r'\bs(\d+)\s+ep(\d+)\b',text,re.I)
 if m:
  if len(m.groups())==2:season,episode=map(int,m.groups())
  else:season=int(m[1] or m[2]);episode=int(m[3]);part=(m[4] or '').lower()
 else:
  m=re.search(r'\b(?:ep(?:isode)?\.?\s*|AG)(\d+)\b',text,re.I) or re.search(r'(?:Dragon Ball Kai\s*[- ]*|TheLegendOfZelda)(\d+)\b',text,re.I) or re.match(r'(\d{1,3})\s*[-.]',text)
  if m:episode=int(m[1])
  sm=re.search(r'(?:Season|Series)[ _-]*(\d+)\b',filename or '',re.I)
  if sm:season=int(sm[1])
 if p.get('restoration_evidence'):
  season=number(p.get('evidenced_season',p.get('season_number')),1);episode=number(p.get('evidenced_episode',p.get('episode_number')));part=p.get('episode_part','')
 # Several collections number episodes after a show name rather than SxxExx.
 if key in ['bebop','ouran']:
  numbered=re.search(r'\s-\s*(\d{1,3})\b',text)
  if numbered:episode=int(numbered[1])
 if key=='pokemon':
  numbered=re.search(r'Pok[eé]mon\s*-\s*0*(\d+)\b',text,re.I)
  if numbered:episode=int(numbered[1]);season=1
 if key:p['series_id']=key;p['series_label']=defs[key]['name'];p['show']=defs[key]['name']
 if episode is not None:p['season']=str(season);p['season_number']=season;p['episode']=episode;p['episode_number']=episode;p['episode_part']=part
 p.setdefault('source_title',p.get('title',''))
 # Presentation text never displays codecs, scene-group names or raw filenames.
 detail=p['source_title'];detail=re.sub(r'\.(?:ia\.)?(?:mp4|mkv|avi)$','',detail,flags=re.I);detail=detail.replace('_',' ')
 detail=re.sub(r'\[[^\]]*\]','',detail);detail=re.sub(r'\b(?:1080p|720p|480p|576i|HDTV|WEB[ .-]?DL|WEBRip|DVD[ .-]?(?:Rip|Remux)|x26[45]|H[ .]?26[45]|BDRip|AAC|AC3|10bit|DD[ .]?[25]|MPEG2|NTSC|PAL)\b.*','',detail,flags=re.I)
 detail=re.sub(r'\([^)]*(?:\bBD|DVD|1440|10bit|Dual.Audio)[^)]*\)','',detail,flags=re.I)
 detail=detail.replace('.',' ');detail=re.sub(r'([a-z])([A-Z])',r'\1 \2',detail);detail=re.sub(r'\s+',' ',detail).strip(' -—')
 names=[p.get('show',''),p.get('series_label','')]
 if key:names+=defs[key]['shows']
 for name in sorted(set(names),key=len,reverse=True):
  clean_name=re.sub(r'[^a-z0-9]','',name.lower())
  if len(clean_name)>4 and re.sub(r'[^a-z0-9]','',detail.lower()).startswith(clean_name):
   # Match punctuation-insensitively without removing episode-title words.
   pattern=r'^[\W_]*'+r'[\W_]*'.join(map(re.escape,re.findall(r'[a-z0-9]+',name,re.I)))
   detail=re.sub(pattern,'',detail,flags=re.I).strip(' -—');break
 detail=re.sub(r'^(?:S\d+\s*E\d+(?:[abc](?=[^a-z]|$))?|\d+x\d+(?:[abc](?=[^a-z]|$))?|S\d+\s+EP\d+|EP(?:ISODE)?\s*\d+|\d+)\s*[-—: ]*','',detail,flags=re.I)
 detail=re.sub(r'^(?:Series|Season)\s*\d+\s*[- ]*\d*\s*(?:Episode|Ep)\s*\d+','',detail,flags=re.I).strip(' -—')
 detail=re.sub(r'\b[bp][a-z0-9]{7}\b.*','',detail,flags=re.I).strip(' -—')
 detail=re.sub(r'^199\d\s*[-— ]*','',detail).strip(' -—')
 generic=not detail or re.fullmatch(r'(?:Ep(?:isode)?\s*\d+|S\d+\s*E\d+|Pokemon\s*\d+|TheLegendOfZelda\d*|InShot.*|video.*|original)',detail,re.I)
 name=p.get('series_label') or p.get('show') or 'Untitled source'
 if re.fullmatch(r'\d{4}[a-z]?',name,re.I):name=detail or p['source_title'];p['show']=name
 if key=='tom-jerry' and ('InShot' in p['source_title']):
  clue=(identifier or '').replace('tom-and-jerry-','');clue=re.split(r'-\d{4}|-ep\d+',clue)[0];detail=clue.replace('-',' ').title();generic=not detail
 if p.get('type') in ['Movie','Special']:p['title']=detail or name
 elif episode is not None:p['title']=name+' — '+f'S{season:02d}E{episode:02d}'+part+(' — '+detail if not generic else '')
 else:p['title']=name+(' — '+detail if not generic and detail.lower()!=name.lower() else '')
 if key in ['bebop','ouran'] and episode is not None:
  # Keep a supplied readable episode title, otherwise use the evidenced episode number.
  p['title']=name+f' — S{season:02d}E{episode:02d}'+(' — '+re.split(r'—',p['source_title'])[-1].strip() if '—' in p['source_title'] else '')
 if key in ['pokemon','pokemon-advanced']:
  named=re.sub(r'^.*?(?:AG\d+|Pokemon\s*-\s*\d+)\s*-\s*','',detail,flags=re.I)
  p['title']=name+f' — S{season:02d}E{episode:02d}'+(' — '+named if named!=detail else '') if episode is not None else name
 if key=='chuckle':
  named=re.sub(r'^.*?s\d+\s+ep\d+\s*-\s*199\d\s*-\s*','',detail,flags=re.I);p['title']=name+f' — S{season:02d}E{episode:02d} — '+named
 if key=='blackmirror':
  named=re.sub(r'^.*?S\d+E\d+\s*','',detail,flags=re.I);named=re.sub(r'《.*?》','',named);p['title']=name+f' — S{season:02d}E{episode:02d} — '+named.strip()
 p['title']=re.sub(r'\bRosha[ .]*N[ .]*T[ .]*L\b|\bRCVR\b','',p['title'],flags=re.I).strip(' -—')
 p['title']=re.sub(r'\s*\([^)]*(?:Dual Audio|Hi10|BD$)[^)]*\)?','',p['title'],flags=re.I).strip(' -—')
 # DVD chapter names do not establish an episode name. Display their evidence plainly.
 if re.search(r'\bDISC[ _-]*\d|\bD\d+B\d',stem,re.I):
  evidence=re.search(r'(?:SERIES|\bS)[ _-]*(\d+)',stem,re.I);disc=re.search(r'(?:DISC[ _-]*|\bD)(\d+)',stem,re.I)
  p['title']=name+' — DVD programme'+(' (Series '+evidence[1]+')' if evidence else '')+(' — Recording '+disc[1] if disc else '')
 if p.get('type') in ['Movie','Special']:
  # Full film/special names must survive; stripping the show prefix collapsed many to ')'.
  full=p['source_title'];full=re.sub(r'\.(?:ia\.)?(?:mp4|mkv|avi)$','',full,flags=re.I)
  full=full.replace('_',' ');full=re.sub(r'\[[^\]]*\]','',full)
  full=re.sub(r'\b(?:1080p|720p|480p|WEB[ .-]?DL|WEBRip|BluRay|BRRip|BDRip|DVDRip|x26[45]|H[ .]?26[45]|AAC|10bit)\b.*','',full,flags=re.I)
  full=full.replace('.',' ');full=re.sub(r'\s+',' ',full).strip(' -—')
  full=re.sub(r'^\d{4}[ab]\s*-\s*','',full)
  if p.get('type')=='Movie' and ('The Amazing Spider-Man' in p.get('source_show','') or p.get('source_show')=='Super Size Me (2004)'):full=p['source_show']
  if not re.search(r'[a-z0-9]',full,re.I):full=p.get('source_show') or name
  p['title']=full
 if p.get('title_override'):p['title']=p['title_override']
 # A show+number+segment is stable across alternate files; MIB additionally has title-based source identities.
 if key=='mib' and p.get('content_id'):pass
 elif key and episode is not None and p.get('type')=='Episode':p['content_id']=key+':'+str(season)+':'+str(episode)+':'+part
 elif p.get('type') in ['Movie','Special']:p['content_id']='special:'+re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',p['title'].lower()))
 else:p.setdefault('content_id',p.get('broadcast_identity') or p.get('url'))
 if p.get('type')=='Movie':
  # Editorial seasonal fit supplements the supplied tags; it does not claim a holiday episode date.
  if re.search(r'vampire|halloween|hellraiser|gremlins|beetlejuice|coraline|blair witch|cabin in the woods|chain.?saw|scream|perfect blue|paprika|franken|scooby|\bmisery\b|the thing|elm street|friday the 13|silent hill|bayonetta|paranorman|monster house|corpse bride|nightmare before christmas|\bakira\b|ghost in the shell|spirited away|\bgodzilla\b',p['title'],re.I):p['seasonal_tags']=list(dict.fromkeys(p.get('seasonal_tags',[])+['halloween']))
  if re.search(r'christmas|\bxmas\b|nutcracker|tokyo godfathers|nightmare before christmas',p['title'],re.I):p['seasonal_tags']=list(dict.fromkeys(p.get('seasonal_tags',[])+['christmas']))
 if re.search(r'christmas|\bxmas\b',p['title'],re.I):p['holiday_events']=list(set(p.get('holiday_events',[])+['christmas']))
 return p
records=[decorate(p) for p in records];catalogue['programmes']=records
urls={p['url'] for p in records}
def usable(p):
 return bool(p.get('url','').lower().endswith('.mp4') and not p.get('broadcast_held') and p.get('language_status') not in ['non-english','reported-non-english'] and not BAD_AUDIO.search(p.get('show','')+' '+p.get('filename','')) and p.get('duration_seconds',0)>0 and not BAD_EXTRA.search((p.get('filename') or '').rsplit('/',1)[-1]))
for p in records:
 key=p.get('series_id')
 if key not in defs or p.get('type') not in ['Episode','Movie','Special']:continue
 if not usable(p):
  if not p.get('duration_seconds'):report['missing_runtime'].append(p['url'])
  continue
 if '.ia.mp4' in p['url']:
  original=p['url'].replace('.ia.mp4','.mp4')
  if original in urls:continue
  # Preserve working derivatives already in the user's broadcast catalogue. No new .ia links are imported.
  if p.get('catalogue_status')!='broadcast':continue
 if p.get('type')!='Episode' and key!='wallace':continue
 if p.get('duration_seconds',0)>7200:continue
 if p.get('type')=='Episode' and p.get('episode_number')==0:continue
 if re.search(r'all episodes|episodes \d+.*\d+|full season|complete season|complete series',p.get('filename','').rsplit('/',1)[-1],re.I) and key!='trapdoor':continue
 profiles[key].append(p)
long_series={'utopia','jeremy','robotwars','topgear','doctorwho','countdown','idiot','moaning','blackmirror','beinghuman','sherlock','cosmos','attenborough','nova','river','mayday','ancient','haunted','hauntedhistory','scariest','afhv','dukes','jerry','madtv'}
for key in defs:
 maxlen=defs[key].get('max_episode_seconds') or (7200 if key=='sherlock' else 4500 if key in ['cosmos','jeremy'] else 5400 if key=='hauntedhistory' else 3600 if key in long_series or key=='reboot' else 2100)
 rows=[p for p in profiles[key] if (not defs[key].get('require_mapped_episode') or p.get('restoration_evidence')) and p['duration_seconds']<=maxlen and (key not in ['topgear','doctorwho','cosmos','countdown','beinghuman','blackmirror'] or p['duration_seconds']>=1200)];rows.sort(key=lambda p:(p.get('season_number',1),p.get('episode_number') if p.get('episode_number') is not None else p.get('editorial_order',99999),p.get('episode_part',''),not p.get('preferred_source',False),p.get('title','')))
 seen=set();profiles[key]=[p for p in rows if not(p['content_id'] in seen or seen.add(p['content_id']))]
 report['series'][key]={'name':defs[key]['name'],'measured_episodes':len(profiles[key])}
 if not profiles[key]:report['missing_series'].append(key)
# Station idents come from the user's original channel files, never another channel's brand.
ident_files={'90s Toons':'90s Toons ident.mp4','AAA':'AAA ident.mp4','Cartoons Cartoons':'Cartoons Cartoons ident.mp4','Dickleodeon':'Dickleodeon ident.mp4','Dizzy':'Dizzy Ident.mp4','GirlyPop':'Girly Pop Ident.mp4','Japanime':'Japanime Ident.mp4','Off-Licence TV':'Off Licence Tv Ident.mp4','Star Spangled TV':'Star Spangled Tv Ident.mp4','What':'What Ident.mp4'}
channel_breaks={}
for channel in config['channels']:
 path='assets/idents/'+ident_files[channel]
 if not local.get(path):raise RuntimeError('Missing measured channel ident: '+path)
 ident={'type':'Ident','show':channel,'title':channel+' — Station ident','url':path,'duration_seconds':local[path]}
 selected=[];pool=adverts.get(channel,[])[:]
 if channel=='Cartoons Cartoons':pool+=oldbreaks.get('city',[])+sum([oldbreaks.get(s,{}).get('adverts',[]) for s in ['october','december']],[])
 if channel=='AAA':pool+=sum([oldbreaks.get(s,{}).get('adverts',[]) for s in ['october','december']],[])
 seen=set()
 for a in pool:
  p=decorate(a);title=a.get('title','');u=p.get('url','');l=p.get('duration_seconds',0)
  if not u.endswith('.mp4') or '.ia.mp4' in u or '/Commercials.zip/' in u or not 5<=l<=90 or u in seen:continue
  cn=bool(re.search(r'\bCN\b|cartoon network|CN City|toon city',title,re.I));disney=bool(re.search(r'disney',title,re.I));adult=bool(re.search(r'adult.?swim|AdultswimBumps',title+' '+u,re.I));nick=bool(re.search(r'nickelodeon|nicktoons|nick bumper',title,re.I))
  if cn and channel!='Cartoons Cartoons':continue
  if disney and channel!='Dizzy':continue
  if adult and channel not in ['AAA','Cartoons Cartoons']:continue
  if nick and channel!='Dickleodeon':continue
  if channel=='Cartoons Cartoons' and adult and not cn:continue
  if channel=='AAA' and cn:continue
  if 'halloween' in title.lower() or 'pumpkin' in title.lower():p['seasonal_tags']=['halloween']
  if 'christmas' in title.lower() or 'xmas' in title.lower():p['seasonal_tags']=['christmas']
  p['title']=channel+' — '+title;p['type']='Advert';seen.add(u);selected.append(p)
 channel_breaks[channel]={'ident':ident,'adverts':selected[:120]}
write('channel-breaks.json',{'channels':channel_breaks})
film_calendar=read('editorial-film-calendar.json') if (ROOT/'editorial-film-calendar.json').exists() else None
# Calendar specials only enter designated editorial appointments.
specials=collections.defaultdict(list)
authored_urls=set(config.get('authored_source_urls',[]))
for p in records:
 if p.get('url') in authored_urls:continue
 if not usable(p) or ('.ia.mp4' in p['url'] and p.get('catalogue_status')!='broadcast'):continue
 explicit=p.get('type') in ['Movie','Special'] or bool(re.search(r'halloween|terror tales|christmas|xmas|valentine|thanksgiving|new year|easter|st.?patrick',p['title'],re.I))
 if not explicit:continue
 for ch in p.get('channels',[p.get('channel')]):
  if ch in config['channels']:specials[ch].append(p)
for ch,rows in specials.items():
 seen=set();planned_urls=set(film_calendar['appointments'].values()) if film_calendar else set();rows.sort(key=lambda p:(0 if p['url'] in planned_urls else 1,0 if p.get('type')=='Movie' else 1,p['title'].casefold()));specials[ch]=[p for p in rows if not(p['content_id'] in seen or seen.add(p['content_id']))]
cursors=collections.defaultdict(int);special_last={};ad_cursor=collections.defaultdict(int)
def events_on(date):
 # Western Easter computus, fourth Thursday of November and fixed annual holidays.
 y=date.year;a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451;n=h+l-7*m+114
 out=[]
 for name,match in [('valentine',(date.month,date.day)==(2,14)),('st-patrick',(date.month,date.day)==(3,17)),('easter',(date.month,date.day)==(n//31,n%31+1)),('thanksgiving',date.month==11 and date.weekday()==3 and 22<=date.day<=28),('new-year',(date.month,date.day) in [(1,1),(12,31)]),('christmas',date.month==12 and date.day in [24,25,26])]:
  if match:out.append(name)
 return out
def allowed(p,date):
 tags=p.get('holiday_events',[])
 if 'nightmare before christmas' in p.get('title','').lower():return date.month in [10,12]
 if 'christmas' in tags or ('christmas' in p.get('seasonal_tags',[]) and p.get('type') in ['Movie','Special']):return date.month==12
 return not tags or any(t in events_on(date) for t in tags)
def episode(ch,key,date,used,capacity):
 rows=profiles[key]
 if not rows:return None
 idx=cursors[ch,key]%len(rows);skipped=0
 while not allowed(rows[idx],date) and skipped<len(rows):
  skipped+=1;idx=(idx+1)%len(rows)
 if skipped==len(rows):return None
 p=rows[idx]
 if p['content_id'] in used or p['duration_seconds']>capacity:return None
 cursors[ch,key]+=skipped+1;return p

run_states={};run_log=[]
def run_episode(ch,run_id,date,used,capacity):
 chain=config['series_runs'][run_id]['series'];state=run_states.setdefault((ch,run_id),{'index':0,'end':None})
 for _ in range(len(chain)+1):
  key=chain[state['index']];rows=profiles[key]
  if not rows:
   state['index']=(state['index']+1)%len(chain);state['end']=None;continue
  if state['end'] is None:
   state['end']=cursors[ch,key]+len(rows)-cursors[ch,key]%len(rows)
   run_log.append({'channel':ch,'run':run_id,'series':key,'series_name':defs[key]['name'],'starts':date.isoformat(),'from_episode_index':cursors[ch,key]%len(rows),'ends':None})
  if cursors[ch,key]>=state['end']:
   next((r for r in reversed(run_log) if r['channel']==ch and r['run']==run_id and r['ends'] is None),{})['ends']=date.isoformat()
   state['index']=(state['index']+1)%len(chain);state['end']=None;continue
  p=episode(ch,key,date,used,capacity)
  return p
 return None

slim_keys=['type','show','title','url','duration_seconds','duration_evidence','series_id','series_label','content_id','season','episode','episode_number','season_number','episode_part','source_page','language_status','seasonal_tags','holiday_events','editorial_kind','editorial_run']
def slim(p):return {k:p[k] for k in slim_keys if k in p}
month_outputs={m:{'schema_version':'written-tv-v1','schedule_year':YEAR,'timezone':'Europe/London','weeks':[{'week':[]}]} for m in range(1,13)}
for ordinal in range(366 if calendar.isleap(YEAR) else 365):
 date=datetime.date(YEAR,1,1)+datetime.timedelta(days=ordinal);active=events_on(date)
 start=datetime.datetime.combine(date,datetime.time(),ZONE).timestamp();next_start=datetime.datetime.combine(date+datetime.timedelta(days=1),datetime.time(),ZONE).timestamp()
 day={'date':str(date.day),'day':date.strftime('%A'),'holiday_events':active,'channels':[]}
 def offset(at):
  hh,mm=map(int,at.split(':'))
  if hh==24:return next_start-start
  return datetime.datetime.combine(date,datetime.time(hh,mm),ZONE).timestamp()-start
 for ch,base in config['channels'].items():
  slots=[dict(s) for s in base];overrides=config.get('weekly_overrides',{}).get(ch,{}).get(str(date.weekday()),{})
  for at,patch in overrides.items():
   slots=[s for s in slots if not(at<=s['at']<patch.get('end',at)) and s['at']!=at];slots.append({'at':at,**patch})
  for window in config.get('film_windows',[]):
   if window['channel']==ch and date.weekday()==window['weekday'] and date.day<=window.get('month_days_max',31):
    slots=[s for s in slots if not window['at']<=s['at']<window['end']]
    slots.append({**window,'series':'@film','episodes':12})
  for window in config.get('holiday_film_windows',[]):
   if window['channel']==ch and window['event'] in active:
    slots=[s for s in slots if not window['at']<=s['at']<window['end']]
    slots.append({**window,'series':'@film','episodes':12})
  if date.month==10 and ch=='Cartoons Cartoons' and date.weekday()==5:
   slots=[s for s in slots if s['at']!='16:00'];slots.append({'at':'16:00','series':'secret-saturdays','episodes':2,'block':'October cryptid cartoons'})
  for feature in config.get('monthly_features',[]):
   if ch==feature['channel'] and date.weekday()==6 and date.day<=7:
    slots=[s for s in slots if not feature['at']<=s['at']<feature['end']];slots.append({**feature,'series':'@aaa-feature','episodes':2,'fallback':['home-movies','beavis'],'block':'AAA animation feature'})
  if date.month==10 and ch=='Cartoons Cartoons':
   for slot in slots:
    if slot['at']=='18:00' and slot['series']=='courage':slot['episodes']=4
  if date.month==12:
   slots=[s for s in slots if not('03:00'<=s['at']<'04:00')];slots.append({'at':'03:00','end':'04:00','series':'@fireplace','episodes':1,'block':'Christmas overnight fireplace'})
  # Preserve the 02:30–07:00 UK boundary in every channel's published day.
  slots.sort(key=lambda s:s['at']);playlist=[];used=set();season='october' if date.month==10 else 'december' if date.month==12 else None
  def append(p,t,seconds,label):
   entry=slim(p);entry.update({'broadcast_start_seconds':round(t,3),'broadcast_end_seconds':round(t+seconds,3),'block':label})
   if p.get('loop'):entry['loop']=True
   playlist.append(entry);return t+seconds
  def breaks(t,stop,label):
   ads=[a for a in channel_breaks[ch]['adverts'] if (not a.get('seasonal_tags') or ('halloween' in a['seasonal_tags'] and date.month==10) or ('christmas' in a['seasonal_tags'] and date.month==12)) and (date.month!=10 or not('christmas' in a.get('holiday_events',[])))]
   count=0
   while stop-t>.0001:
    ident=channel_breaks[ch]['ident'];p=ident
    if count%4!=0 and ads:
     p=ads[ad_cursor[ch]%len(ads)];ad_cursor[ch]+=1
    length=min(p['duration_seconds'],stop-t)
    t=append(p,t,length,label);count+=1
   report['filler_minutes_by_channel'][ch]+=(stop-(playlist[-count]['broadcast_start_seconds'] if count else stop))/60 if count else 0
   return stop
  for ix,appointment in enumerate(slots):
   t=offset(appointment['at']);stop=offset(appointment.get('end') or (slots[ix+1]['at'] if ix+1<len(slots) else '24:00'))
   if stop<=t:continue
   hour=int(appointment['at'][:2]);label=appointment.get('block') or ('After hours' if '02:30'<=appointment['at']<'07:00' else 'Late night' if hour<7 or hour>=21 else 'Morning' if hour<12 else 'Afternoon' if hour<18 else 'Evening')
   calendar_pick=next((config.get('holiday_overrides',{}).get(event,{}).get(ch,{}).get(appointment['at']) for event in active if config.get('holiday_overrides',{}).get(event,{}).get(ch,{}).get(appointment['at'])),None)
   key=appointment['series'];feature=bool(calendar_pick) or (appointment['at'] in config.get('seasonal_slots',{}).get(season,{}).get(ch,[])) or (active and appointment['at']==config['holiday_spotlight_at'])
   if key=='@fireplace':
    p={**oldbreaks['fireplace'],'type':'Filler','show':ch,'title':'Christmas overnight fireplace','loop':True};t=append(p,t,stop-t,label);breaks(t,offset(slots[ix+1]['at']) if ix+1<len(slots) else next_start-start,label);continue
   if key in ['@pilot-showcase','@aaa-feature']:
    source_urls=config['pilot_showcase'][(date.toordinal()//7)%len(config['pilot_showcase'])] if key=='@pilot-showcase' else [appointment['feature_urls'][(date.month-1)%len(appointment['feature_urls'])]]
    for url in source_urls:
     p=next((p for p in records if p.get('url')==url),None)
     if not p or not usable(p) or p['content_id'] in used or p['duration_seconds']>stop-t:raise RuntimeError('Invalid authored appointment: '+str(date)+' '+url)
     t=append(p,t,p['duration_seconds'],label);used.add(p['content_id']);report['programme_slots']+=1;t=breaks(t,min(stop,t+channel_breaks[ch]['ident']['duration_seconds']),label)
    feature=False
   if key=='@film':
    candidates=[p for p in specials[ch] if p.get('type')=='Movie' and p['content_id'] not in used and allowed(p,date) and 1800<=p['duration_seconds']<=stop-t and date.toordinal()-special_last.get((ch,p['content_id']),0)>=config['movie_cooldown_days']]
    if film_calendar is not None:
     chosen=film_calendar['appointments'].get(date.isoformat()+'|'+ch+'|'+appointment['at'])
     candidates=[p for p in candidates if p['url']==chosen]
    preferred=['halloween','horror'] if date.month==10 else ['christmas','winter','snow'] if date.month==12 else active
    # Publish a date-specific, fixed feature appointment. Themes rank only inside this authored window.
    candidates.sort(key=lambda p:(0 if preferred and any(tag in p.get('seasonal_tags',[])+p.get('holiday_events',[]) for tag in preferred) else 1,special_last.get((ch,p['content_id']),0),p['title'].casefold()))
    if candidates:
     p=candidates[0];t=append(p,t,p['duration_seconds'],label);used.add(p['content_id']);report['programme_slots']+=1;special_last[ch,p['content_id']]=date.toordinal();t=breaks(t,min(stop,t+channel_breaks[ch]['ident']['duration_seconds']),label)
    feature=False
   if key=='@anime-film':feature=True
   if feature:
    tags=['halloween'] if date.month==10 else ['christmas'] if date.month==12 else active
    if key=='@anime-film':tags=[]
    choices=[p for p in specials[ch] if (key=='@anime-film' or p.get('type')!='Movie') and p['content_id'] not in used and allowed(p,date) and p['duration_seconds']<=stop-t and (not tags or any(tag in p.get('seasonal_tags',[])+p.get('holiday_events',[]) for tag in tags)) and (date.toordinal()-special_last.get((ch,p['content_id']),0)>=(config['movie_cooldown_days'] if p.get('type')=='Movie' else config['special_cooldown_days'])) and (key!='@anime-film' or p.get('type')=='Movie' and p['duration_seconds']>=3600)]
    # Oldest-aired first, alphabetical tie-break. A special cannot dominate multiple slots or days.
    if calendar_pick:choices=[p for p in choices if p['content_id']==calendar_pick['special_content_id']]
    choices.sort(key=lambda p:(special_last.get((ch,p['content_id']),0),p['title']))
    if choices:
     p=choices[0];t=append(p,t,p['duration_seconds'],('Saturday anime cinema' if key=='@anime-film' else 'Halloween spotlight' if date.month==10 else 'Christmas spotlight' if date.month==12 else 'Holiday spotlight'));used.add(p['content_id']);report['programme_slots']+=1;special_last[ch,p['content_id']]=date.toordinal();t=breaks(t,min(stop,t+min(60,channel_breaks[ch]['ident']['duration_seconds'])),label)
   choices=[key]+appointment.get('fallback',[])
   if key.startswith('@run:'):choices=[key]
   if key.startswith('@') and not key.startswith('@run:'):choices=appointment.get('fallback',[])
   n=0
   for series in choices:
    for _ in range(appointment.get('episodes',1)):
     p=run_episode(ch,series[5:],date,used,max(0,stop-t)) if series.startswith('@run:') else episode(ch,series,date,used,max(0,stop-t))
     if not p:break
     if series.startswith('@run:'):p={**p,'editorial_run':series[5:]}
     if series!=key:report['substitutions'][ch+' | '+key+' → '+series]+=1
     t=append(p,t,p['duration_seconds'],label);used.add(p['content_id']);n+=1;report['programme_slots']+=1
     t=breaks(t,min(stop,t+min(60,channel_breaks[ch]['ident']['duration_seconds'])),label)
    if n and key not in ['@pilot-showcase','@aaa-feature','@film']:break
   if not n and key not in ['@fireplace','@anime-film','@pilot-showcase','@aaa-feature','@film'] and not feature:report['empty_appointments'][ch+' | '+key+' | '+appointment['at']]+=1
   breaks(t,stop,label)
  # Store each break once with compact indices; expand its measured clips at playback.
  compact=[];indices={p['url']:i for i,p in enumerate(channel_breaks[ch]['adverts'])}
  for p in playlist:
   if p['type'] in ['Ident','Advert']:
    index=-1 if p['type']=='Ident' else indices[p['url']]
    if compact and compact[-1]['type']=='Break':
     compact[-1]['break_sequence'].append(index);compact[-1]['broadcast_end_seconds']=p['broadcast_end_seconds']
    else:compact.append({'type':'Break','title':ch+' — Channel break','show':ch,'break_sequence':[index],'broadcast_start_seconds':p['broadcast_start_seconds'],'broadcast_end_seconds':p['broadcast_end_seconds'],'block':p['block']})
   else:compact.append(p)
  day['channels'].append({'name':ch,'playlist':compact});report['channel_days']+=1
 month_outputs[date.month]['weeks'][0]['week'].append(day)
for m,data in month_outputs.items():write('schedules/'+calendar.month_name[m].lower()+'.json',data)
write('schedule.json',month_outputs[10]);write('source-library.json',catalogue)
# The searchable catalogue stays complete. This file lists sources selected by the editor, not a browser rotation pool.
pool_keys={ch:list(dict.fromkeys([k for s in base for k in (config['series_runs'][s['series'][5:]]['series'] if s['series'].startswith('@run:') else [s['series']]) if not k.startswith('@')]+[k for patches in config.get('weekly_overrides',{}).get(ch,{}).values() for s in patches.values() for k in [s['series']] if not k.startswith('@')])) for ch,base in config['channels'].items()}
write('broadcast-pools.json',{'channels':{ch:[slim(p) for key in keys for p in profiles[key]] for ch,keys in pool_keys.items()}})
write('series-run-calendar.json',{'year':YEAR,'timezone':'Europe/London','runs':run_log,'note':'Run end dates indicate handover, not an invented broadcast duration. A null end means the series has not finished in this calendar; future calendars require rebuilding.'})
report['substitutions']=dict(report['substitutions']);report['empty_appointments']=dict(report['empty_appointments']);report['filler_minutes_by_channel']=dict(report['filler_minutes_by_channel']);write('editorial-review.json',report)
print(json.dumps({k:report[k] for k in ['channel_days','programme_slots','missing_series','empty_appointments','substitutions']},indent=2))
