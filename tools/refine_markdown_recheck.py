import json,re,collections,urllib.parse,urllib.request,concurrent.futures,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1];U=R.parent/'uploaded-markdowns/markdowns';rows=json.loads((R/'markdown-series-recheck.json').read_text());cat=json.loads((R/'source-library.json').read_text())['programmes'];defs=json.loads((R/'editorial-series.json').read_text());cache=R/'tools/markdown-recheck'
def norm(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower();s=re.sub(r'\b(?:the|and|of)\b','',s);return re.sub('[^a-z0-9]','',s)
def canon(u):return urllib.parse.unquote(urllib.parse.urlsplit(u.rstrip(')>.,')).path)
byurl={canon(p['url']):p for p in cat};aired=collections.defaultdict(set);names=collections.defaultdict(set)
for f in (R/'schedules').glob('*.json'):
 for day in json.loads(f.read_text())['weeks'][0]['week']:
  for ch in day['channels']:
   for p in ch['playlist']:
    if p['type']=='Episode':
     names[ch['name']].add(p.get('series_label') or p['show']);aired[ch['name']].add(norm(p.get('series_label') or p['show']))
for ch in aired:
 for d in defs.values():
  if norm(d['name']) in aired[ch]:aired[ch].update(norm(n) for n in d['shows'])
 def match(n):return n in aired[ch]
def same_series(x,ch):
 n=norm(x['show']);same=[n]+[norm(s) for s in x.get('catalogue_names',[])]
 for a in aired[ch]:
  for s in same:
   if s==a:return True
   if len(a)>=4 and s.startswith(a) and re.match(r'^(?:complete|full|cartoon|mtv|season|dvd|vol|kingturd|timelife|tv|platinum|remaster|[0-9]*complete)',s[len(a):]):return True
 return False
# Metadata supplied type is a useful film/TV cross-check, not a claim of correct episode identity.
explicit_tv=re.compile(r'Duck Dodgers|Kyouran|Welcome to the NHK|Nanaka|Chance Pop|Colorful|Powerpuff Girls \(2016\)|Xiaolin Chronicles|The Batman \(2004|Frie?ren|The Life and Times of Juniper Lee',re.I)
for x in rows:
 ps=[byurl[canon(u)] for u in x['urls'] if canon(u) in byurl];types=collections.Counter(p.get('type') for p in ps);old=x['status'];known=re.fullmatch(r'Futurama|Family Guy|Full Metal Alchemist|Samurai Jack|Zoey 101',x['show'],re.I)
 if known:x['category']='Known problem original source'
 elif old.startswith('Already') or same_series(x,x['channel']):x['category']='Already scheduled; alternate upload or season'
 elif old.startswith('Language caution'):x['category']='Wrong-language/international collection caution'
 elif old.startswith('Mixed') or re.search(r'Cartoon Cartoons.*COMPLETE COLLECTION',x['show'],re.I):x['category']='Mixed collection; individual programmes need sorting'
 elif explicit_tv.search(x['show']) or (types['Episode']>0 and types['Episode']>=sum(types.values())*.7):x['category']='Missing series candidate'
 elif types['Movie'] and types['Movie']>=sum(types.values())*.5 or old.startswith('Film') or re.search(r'Special From|Ego Trip|Deck The Mall|Documentary|Life of Adolf|Rango|Rambo|Lord Of The Rings',x['show'],re.I):x['category']='Film or standalone special; separate review'
 else:x['category']='Missing series candidate'
 x['other_channels']=[ch for ch in aired if ch!=x['channel'] and same_series(x,ch)]
 x['user_checked_channel']=x['channel'] in ['90s Toons','Cartoons Cartoons','AAA'] and not known
 # Enrich newly identified TV headings from files fetched in the first pass, or get only missing collections.
 if x['category'] in ['Missing series candidate','Known problem original source'] and 'exact_files' not in x:
  matching=[];langs=set()
  for u in x['urls']:
   tail=urllib.parse.unquote(urllib.parse.urlsplit(u).path.split('/download/',1)[1]);i,fn=tail.split('/',1);p=cache/(i+'.json')
   if not p.exists():
    try:
     with urllib.request.urlopen('https://archive.org/metadata/'+i,timeout=8) as f:d=json.load(f)
     p.write_text(json.dumps(d,ensure_ascii=False))
    except Exception as e:
     p.write_text(json.dumps({'request_error':str(e)}));continue
   d=json.loads(p.read_text());l=d.get('metadata',{}).get('language',[]);langs.update(l if isinstance(l,list) else [str(l)]);f=next((f for f in d.get('files',[]) if f.get('name')==fn),None)
   if f:matching.append({'url':u,'filename':fn,'length':f.get('length') or f.get('duration'),'format':f.get('format'),'collection':i})
  x['exact_files']=matching;x['exact_files_found']=len(matching);x['uploader_languages']=sorted(langs)
# One additional direct original-file test when the first pass has no MP4 check (including no metadata).
jobs=[]
for idx,x in enumerate(rows):
 if x['category'] in ['Missing series candidate','Known problem original source'] and not x.get('sample_checks'):
  fs=x.get('exact_files',[]);jobs.append((idx,(fs[0]['url'] if fs else x['urls'][0])))
def probe(job):
 idx,u=job
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'Range':'bytes=0-1023','User-Agent':'Mozilla/5.0'}),timeout=10) as f:b=f.read(1024);return idx,{'url':u,'status':f.status,'mp4_header':b'ftyp' in b[:128]}
 except Exception as e:return idx,{'url':u,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
 for idx,res in ex.map(probe,jobs):rows[idx].setdefault('sample_checks',[]).append(res)
for x in rows:
 fs=x.get('exact_files',[]);positive=[f for f in x.get('sample_checks',[]) if f.get('mp4_header')];episode_like=[];odd=[]
 for f in fs:
  try:n=float(f.get('length') or 0)
  except (ValueError,TypeError):n=0
  if 600<=n<=4500 and not re.search(r'menu|trailer|promo|credits|bonus|intro|opening',f['filename'],re.I):episode_like.append(f)
  elif n:odd.append(f)
 x['sample_mp4_successes']=len(positive);x['measured_episode_length_files']=len(episode_like);x['non_episode_length_files']=len(odd)
 x['availability_note']='MP4 sample returned' if positive else 'Exact filenames still listed; direct sample not verified' if fs else 'Not verified; metadata/sample did not establish availability'
 x['language_note']='Uploader labels English (not spoken-audio verification)' if any(str(l).lower() in ['eng','en','english'] for l in x.get('uploader_languages',[])) else 'English/subtitle verification still needed'
 if x['category']=='Missing series candidate':
  if x['other_channels']:x['priority']='Channel placement review: already airs elsewhere'
  elif positive and (re.search(r'DVD ISO|DVD collection|Complete Video Collection',x['show'],re.I) or any(re.search(r'VTS_|VOL[0-9]+_D|\bD[0-9]+B[0-9]+',f['filename'],re.I) for f in fs)):x['priority']='DVD/video collection; episode mapping needed'
  elif positive and episode_like:x['priority']='Strong restoration candidate'
  elif positive:x['priority']='Playable sample; episode identity/duration needs sorting'
  elif x.get('user_checked_channel'):x['priority']='User-checked channel; direct verification still incomplete'
  else:x['priority']='Unverified candidate; keep for review'
 x.pop('status',None)
(R/'markdown-series-recheck.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps({'categories':dict(collections.Counter(x['category'] for x in rows)),'candidates':dict(collections.Counter(x.get('priority') for x in rows if x['category']=='Missing series candidate'))},indent=2))
