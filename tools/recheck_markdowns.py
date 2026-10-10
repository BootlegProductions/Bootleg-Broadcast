"""Reconcile the uploaded original channel headings with actual aired series, then check candidate metadata and sampled MP4s."""
import json,re,urllib.parse,urllib.request,concurrent.futures,collections,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];U=R.parent/'uploaded-markdowns/markdowns';out=R/'tools/markdown-recheck';out.mkdir(exist_ok=True)
norm=lambda s:re.sub('[^a-z0-9]','',s.lower())
def canon(u):return urllib.parse.unquote(urllib.parse.urlsplit(u.rstrip(')>.,')).path).replace('/items/','/download/')
cat=json.loads((R/'source-library.json').read_text())['programmes'];defs=json.loads((R/'editorial-series.json').read_text());byurl=collections.defaultdict(list)
for p in cat:byurl[canon(p['url'])].append(p)
aired=collections.defaultdict(set);here=collections.defaultdict(set)
for f in (R/'schedules').glob('*.json'):
 for day in json.loads(f.read_text())['weeks'][0]['week']:
  for ch in day['channels']:
   for p in ch['playlist']:
    if p['type']=='Episode':aired[ch['name']].add(norm(p.get('series_label') or p['show']));here[canon(p['url'])].add(ch['name'])
def already(name,ch):
 n=norm(name);aliases=set(aired[ch])
 for key,d in defs.items():
  if norm(d['name']) in aired[ch]:aliases.update(norm(s) for s in d['shows'])
 # Known collection headings that refer to an existing series rather than another series.
 aliases|={norm(s) for s in {'90s Toons':['Men in Black The Animated Series'],'AAA':['Beavis and Butthead','The Venture Bros'],'Cartoons Cartoons':['Kids Next Door','Courage The Cowardly Dog','Dexters Laboratory','Megas XLR','The Secret Saturdays','The Amazing World of Gumball'] if False else []}.get(ch,[])}
 # A long prefix is safe for codecs/collection labels; sequel identities are protected below.
 for a in sorted(aliases,key=len,reverse=True):
  if len(a)<5:continue
  if n==a:return True
  if n.startswith(a):
   tail=n[len(a):]
   if tail.startswith(('complete','thecomplete','cartoonseries','cartoon','mtvcomplete','season','fullseries','tv','dvd','vol','kingturd','time','theanimatedseries')):return True
 return False
rows=[]
for f in sorted(U.glob('Schedule Links - *.md')):
 ch=f.stem.removeprefix('Schedule Links - ')
 if ch in ['october','december']:continue
 name='Unlabelled';links=collections.defaultdict(list)
 for line in f.read_text().splitlines():
  m=re.match(r'^###\s+(.+)',line)
  if m:name=m[1].strip().strip('*').rstrip(':').strip().strip('“”')
  for u in re.findall(r'https?://[^\s<>]+',line):
   if '/download/' in u and '.mp4' in u:links[name].append(u)
 for name,us in links.items():
  urls=list(dict.fromkeys(us));ps=[p for u in urls for p in byurl[canon(u)]]
  current=already(name,ch) or any(ch in here[canon(u)] for u in urls)
  ids={p.get('series_id') for p in ps}-{None,''}
  if any(norm(defs[k]['name']) in aired[ch] for k in ids if k in defs):current=True
  known=bool(re.search(r'^(?:Futurama|Family Guy|Full Metal Alchemist|Samurai Jack|Zoey 101)$',name,re.I))
  foreign=bool(re.search(r'Greek Dub|\(French\)|International versions',name,re.I))
  film=bool(re.search(r'\(\d{4}\)|\bMovie\b|Motion Picture|Wizards|Heavy Metal|Fritz The Cat|Cool World|American Pop|Coonskin|Hey Good Looking|Heavy Traffic|Fire & Ice|GEN 13|Hellboy Blood|Killer Bean|Spirited Away|Castle In The Sky|Princess Mononoke|The Boy And The Heron|Akira|Gundam [IVX]+$|Barbie',name,re.I)) and not re.search(r'TV Series|TV series|\d{4}[–-]\d{4}',name)
  mixed=bool(re.search(r'Complete (?:Classic )?CN Shows|Cartoon Cartoons.*COMPLETE COLLECTION|Franchise|Short Anime Collection|ADV Films|Documentaries|Wildlife Nature|The Yellowson|World Series|Mission Weekend|GameTap|Banned Episodes',name,re.I))
  status='Already scheduled series/alias' if current else 'Known problem source; excluded unless a sample works' if known else 'Language caution; excluded from shortlist' if foreign else 'Film/special; review separately' if film else 'Mixed collection/special; requires identification' if mixed else 'Missing series candidate'
  rows.append({'channel':ch,'show':name,'original_links':len(urls),'status':status,'urls':urls,'collections':sorted({urllib.parse.urlsplit(u).path.split('/download/',1)[1].split('/')[0] for u in urls}),'catalogue_names':sorted({p.get('source_show') or p['show'] for p in ps})})
(R/'markdown-series-recheck.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
# Retrieve fresh exact-filename metadata for candidate sources; only clear failures are recorded as unavailable.
ids=sorted({i for x in rows if x['status'] in ['Missing series candidate','Known problem source; excluded unless a sample works'] for i in x['collections']})
def get(i):
 try:
  with urllib.request.urlopen(urllib.request.Request('https://archive.org/metadata/'+i,headers={'User-Agent':'BootlegBroadcastSourceRecheck/0.35.2'}),timeout=18) as f:d=json.load(f)
  (out/(i+'.json')).write_text(json.dumps(d,ensure_ascii=False));return i,d
 except Exception as e:return i,{'request_error':str(e)}
metadata={}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
 for n,(i,d) in enumerate(ex.map(get,ids),1):
  metadata[i]=d
  if n%30==0:print('Fresh metadata:',n,'/',len(ids),flush=True)
for x in rows:
 if x['status'] not in ['Missing series candidate','Known problem source; excluded unless a sample works']:continue
 matching=[];langs=set();descs=[];failures=[]
 for u in x['urls']:
  tail=urllib.parse.unquote(urllib.parse.urlsplit(u).path.split('/download/',1)[1]);i,fn=tail.split('/',1);d=metadata.get(i,{})
  lang=d.get('metadata',{}).get('language',[]);langs.update(lang if isinstance(lang,list) else [str(lang)])
  fs={f['name']:f for f in d.get('files',[])};f=fs.get(fn)
  if f:matching.append({'url':u,'filename':fn,'length':f.get('length') or f.get('duration'),'format':f.get('format'),'collection':i})
 for i in x['collections']:
  d=metadata.get(i,{});descs.append(str(d.get('metadata',{}).get('description','')))
  if d.get('request_error'):failures.append(i+': '+d['request_error'])
 x.update({'exact_files_found':len(matching),'exact_files':matching,'uploader_languages':sorted(langs), 'metadata_errors':failures,'description_audio_clues':list(dict.fromkeys(re.findall(r'.{0,55}(?:English dub|English audio|English sub|Dual audio|incorrect audio|Japanese audio).{0,85}',' '.join(descs),flags=re.I)))[:5]})
(R/'markdown-series-recheck.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print(json.dumps({'headings':len(rows),'fresh_collections':len(ids),'statuses':dict(collections.Counter(x['status'] for x in rows))},indent=2),flush=True)
# Range-check first and last exact files for a series, every collection of a known problem.
jobs=[]
for idx,x in enumerate(rows):
 fs=x.get('exact_files',[])
 if fs:
  sample=[fs[0],fs[-1]] if len(fs)>1 else fs
  jobs.extend((idx,f['url']) for f in sample)
def probe(job):
 idx,u=job
 try:
  req=urllib.request.Request(u,headers={'Range':'bytes=0-1023','User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=18) as f:b=f.read(1024);return idx,{'url':u,'status':f.status,'mp4_header':b'ftyp' in b[:128]}
 except Exception as e:return idx,{'url':u,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
 for n,(idx,res) in enumerate(ex.map(probe,jobs),1):
  rows[idx].setdefault('sample_checks',[]).append(res)
  if n%30==0:print('Sampled files:',n,'/',len(jobs),flush=True)
(R/'markdown-series-recheck.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print('Done',flush=True)
