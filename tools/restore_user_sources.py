"""Import the five replacement IA collections supplied by Oliver on 9 October 2026."""
import json,urllib.request,urllib.parse,concurrent.futures,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ids=['h2o-just-add-water-season-one','h2o-just-add-water-seasontwo','h2o-just-add-water-seasonthree','entiretyofeva','evadubbed']
cache=ROOT/'tools/runtime-cache';review=ROOT/'tools/new-source-review';review.mkdir(exist_ok=True)
def get(i):
 d=json.load(urllib.request.urlopen('https://archive.org/metadata/'+i,timeout=25));(review/(i+'.json')).write_text(json.dumps(d,ensure_ascii=False));(cache/(i+'.json')).write_text(json.dumps({'identifier':i,'language':d.get('metadata',{}).get('language'),'files':[{k:f[k] for k in ['name','length','duration','format','size'] if k in f} for f in d.get('files',[])]},ensure_ascii=False));return i,d
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:data=dict(ex.map(get,ids))
cat=json.loads((ROOT/'source-library.json').read_text());existing={p['url'] for p in cat['programmes']};added=[];summary={}
for i,d in data.items():
 files=[f for f in d.get('files',[]) if f['name'].endswith('.mp4') and not f['name'].endswith('.ia.mp4')]
 summary[i]={'language':d.get('metadata',{}).get('language'),'original_mp4_files':len(files),'description':d.get('metadata',{}).get('description'),'sample_files':[{k:f.get(k) for k in ['name','length','format']} for f in files[:2]]}
 if i=='entiretyofeva':continue # Preserve evidence; dub preferred over other editions/films.
 for f in files:
  name=f['name'];m=re.search(r'S(\d+)\s*E(\d+)',name,re.I) if i.startswith('h2o') else re.search(r'(\d+)x(\d+)',name)
  if not m or re.search(r'\bDC\b',name):continue
  season,ep=map(int,m.groups());key='h2o' if i.startswith('h2o') else 'evangelion';show='H2O: Just Add Water' if key=='h2o' else 'Neon Genesis Evangelion';ch='Dickleodeon' if key=='h2o' else 'Japanime'
  url='https://archive.org/download/'+i+'/'+urllib.parse.quote(name,safe='/')
  if url in existing:continue
  duration=float(f.get('length') or 0)
  if not duration:continue
  lang=d.get('metadata',{}).get('language');declared=lang in ['eng','English','english','en']
  p={'type':'Episode','show':show,'source_show':show,'series_id':key,'title':name,'source_title':name,'url':url,'source_page':'https://archive.org/details/'+i,'archive_identifier':i,'filename':name,'season_number':season,'episode_number':ep,'channels':[ch],'channel':ch,'catalogue_status':'broadcast','duration_seconds':duration,'duration_evidence':'IA exact filename length','language_status':'english-declared' if declared else 'unknown','language_label':('Uploader declares English'+(' dub' if key=='evangelion' else '')+'; audio not independently reviewed') if declared else 'Language not independently verified','notes':'Replacement source supplied by Oliver, 9 October 2026. '+('Original-dub claim from uploader; director’s cut files excluded from regular episode sequence.' if key=='evangelion' else 'Series/episode numbers and names taken from exact filenames.')}
  if key=='h2o' and re.search('valentine',name,re.I):p.update({'holiday_events':['valentine'],'seasonal_tags':['valentine']})
  cat['programmes'].append(p);added.append(p);existing.add(url)
(ROOT/'source-library.json').write_text(json.dumps(cat,ensure_ascii=False,separators=(',',':')));(ROOT/'replacement-source-review.json').write_text(json.dumps({'collections':summary,'added_episodes':len(added),'by_series':{k:len([p for p in added if p['series_id']==k]) for k in ['h2o','evangelion']},'audio_verification':'Uploader metadata/description evidence only; full audio not independently reviewed.'},indent=2,ensure_ascii=False));print(json.dumps({'collections':summary,'added':len(added)},ensure_ascii=False),flush=True)
