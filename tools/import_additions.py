"""Curated imports reviewed 9 October 2026; exact MP4 names, measured runtimes."""
import json,re,urllib.parse,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];read=lambda f:json.loads((ROOT/f).read_text());cat=read('source-library.json');defs=read('editorial-series.json');existing={p['url'] for p in cat['programmes']};counts=collections.Counter();new_urls=[]
series=[('magicbus','The Magic School Bus','MSBTVSeries','Star Spangled TV'),('libertykids','Liberty’s Kids','libertys-kids-est-1776-full-animated-series','Star Spangled TV'),('beast-wars','Beast Wars: Transformers','beastwarstransformers1080p','90s Toons'),('reboot','ReBoot','Reboot-HD','90s Toons'),('the-batman','The Batman (2004)','the-batman-03x-01','90s Toons'),('alvin-1983','Alvin and the Chipmunks (1983)','1983-alvin-and-the-chipmunks-complete','90s Toons'),('dragon-tales','Dragon Tales','DragonTalesTVSeries','GirlyPop'),('digimon-data-squad','Digimon Data Squad','digimon-data-squad-the-complete-series','Japanime'),('mickey-works','Mickey Mouse Works','Mickey-Mouse-Works','Dizzy'),('secret-saturdays','The Secret Saturdays','the-secret-saturdays-the-complete-series-2008','Cartoons Cartoons'),('futurama','Futurama','futurama.-benders.-big.-score.-2007.720p.-web-dl.x-265-heteam_202502','AAA')]
def metadata(i):
 d=read('tools/additions-research/'+i+'.json');out={'identifier':i,'language':d.get('metadata',{}).get('language'),'files':[{k:f[k] for k in ['name','length','duration','format','size'] if k in f} for f in d.get('files',[])]};(ROOT/'tools/runtime-cache'/ (i+'.json')).write_text(json.dumps(out,ensure_ascii=False));return d
for key,show,ident,ch in series:
 d=metadata(ident);defs.setdefault(key,{'name':show,'shows':[show]});defs[key]['shows']=list(set(defs[key]['shows']+[show]));rows=[]
 for f in d.get('files',[]):
  name=f['name'];stem=name.rsplit('/',1)[-1]
  if not name.endswith('.mp4') or name.endswith('.ia.mp4') or re.search(r'Serbian|\{cut\}|/Extras/|/Commercials/|/Specials/|/Movies/',name,re.I):continue
  try:length=float(f.get('length') or 0)
  except ValueError:continue
  if not 700<length<2100:continue
  season=1;part='';m=re.search(r'(?:S(\d+)[ ._-]*E|(\d+)x)(\d+)([ab](?=[^a-z]|$))?',stem,re.I)
  if m:season=int(m[1] or m[2]);ep=int(m[3]);part=(m[4] or '').lower();detail=stem[m.end():].lstrip(' -_')
  elif key=='reboot':
   m=re.search(r'Season (\d+) Episode (\d+)\s*-\s*(.*)',stem,re.I)
   if not m:continue
   season=int(m[1]);ep=int(m[2]);detail=m[3]
  else:
   m=re.match(r'(?:Ep)?(\d+)\s*[- ]\s*(.*)',stem,re.I)
   if not m:continue
   ep=int(m[1]);detail=m[2]
  if not ep:continue
  if key=='alvin-1983' and 'Season ' not in name:continue # standard whole episodes, not alternate partial segments
  detail=re.sub(r'\.mp4$','',detail,flags=re.I);detail=re.sub(r'\[[^\]]*\]|\((?:4K Upscale|1080p.*)\)','',detail,flags=re.I);detail=re.sub(r'WEBRip.*|WEB-DL.*|1080p.*|720p.*|\[VHSRip\].*|\[DVB\].*','',detail,flags=re.I);detail=re.sub(r'\s+',' ',detail.replace('.',' ')).strip(' -_.');detail=re.sub(r'^-\s*\(\d+\)\s*','',detail)
  human=show+' — '+(f'Episode {ep:02d}' if key=='magicbus' else f'S{season:02d}E{ep:02d}{part}')+(' — '+detail if detail else '')
  url='https://archive.org/download/'+ident+'/'+urllib.parse.quote(name,safe='/');old=next((p for p in cat['programmes'] if p['url']==url),None)
  p=old if old else {'type':'Episode','url':url}
  p.update({'show':show,'source_show':show,'series_id':key,'filename':name,'archive_identifier':ident,'source_page':'https://archive.org/details/'+ident,'title':human,'source_title':human,'title_override':human,'season_number':season,'episode_number':ep,'episode_part':part,'channel':ch,'channels':[ch],'duration_seconds':length,'duration_evidence':'IA exact filename length','catalogue_status':'broadcast','language_status':'english-declared','language_label':'Uploader/collection declares English; audio not independently reviewed','preferred_source':True,'broadcast_held':False,'notes':'Curated full-episode MP4 import, 9 October 2026. '+('Global numbered collection order 1–52; filename does not give season numbers.' if key=='magicbus' else 'Season and episode identity from filename.')})
  if old is None:cat['programmes'].append(p);new_urls.append(url)
  rows.append(p);counts[key]+=1
 # Use complete numbered collections over shorter/uncertain old subsets, preserving old links for reference.
 if key in ['magicbus','libertykids']:
  for p in cat['programmes']:
   if p.get('series_id')==key and p.get('archive_identifier')!=ident:p['broadcast_held']=True;p['notes']='Superseded in broadcast by the reviewed fuller numbered collection; existing source retained for reference.'
# Exact standalone programmes. Authentic copies, no AI decensoring and no unidentified DVD chapters.
standalone=[('Korgoth of Barbaria','Korgoth of Barbaria — Pilot','korgoth-of-barbaria-s-01-e-01',None),('The Modifyers','The Modifyers — Pilot','the-modifyers-pilot',None),('Constant Payne','Constant Payne — Pilot','constant_payne',None),('The Groovenians','The Groovenians — Pilot','the_groovenians',None),('The Amazing Screw-On Head','The Amazing Screw-On Head — Pilot','the-amazing-screw-on-head-2006',None),('He-Hog the Atomic Pig','He-Hog the Atomic Pig — Unaired pilot','he-hog-the-atomic-pig-unedited-pilot-john-k-1999',None),('Welcome to Eltingville','Welcome to Eltingville — Pilot','tomp-3.cc-welcome-to-eltingville-dvd-rip-full-version-360p',None),('Dexter’s Laboratory','Dexter’s Laboratory — Rude Removal','dexters.-laboratory.-s-00-e-01-rude.-removal.-banned.-episode.-1080p.-aac-2.0.x-264-obfuscated',None),('Boo Boo Runs Wild','Boo Boo Runs Wild — One-off special','ren-stimpy-extras','Boo Boo Runs Wild'),('Party Wagon','Party Wagon (2004)','party-wagon-2004',None)]
selected={}
for show,title,ident,match in standalone:
 d=metadata(ident);files=[f for f in d.get('files',[]) if f['name'].endswith('.mp4') and not f['name'].endswith('.ia.mp4') and (not match or match.lower() in f['name'].lower())]
 if not files:raise RuntimeError('Missing standalone source '+ident)
 f=files[0];name=f['name'];duration=float(f.get('length') or 0);assert duration>0;url='https://archive.org/download/'+ident+'/'+urllib.parse.quote(name,safe='/')
 p={'type':'Special','show':show,'title':title,'source_title':title,'title_override':title,'url':url,'source_page':'https://archive.org/details/'+ident,'archive_identifier':ident,'filename':name,'duration_seconds':duration,'duration_evidence':'IA exact filename length','channels':['AAA'],'channel':'AAA','catalogue_status':'broadcast','language_status':'english-declared','language_label':'Uploader declares English; audio not independently reviewed','notes':'AAA Pilot & Oddities Night. '+('Unaired/withdrawn Dexter short; not an AI-decensored reconstruction.' if 'Rude Removal' in title else 'Pilot or standalone special, not labelled as a banned episode.'),'editorial_kind':'withdrawn-episode' if 'Rude Removal' in title else 'pilot-or-special'}
 if url not in existing:cat['programmes'].append(p);new_urls.append(url);existing.add(url)
 selected[show]=url;counts['standalone_specials']+=1
# Four full Futurama films get occasional named feature appointments, never daily circulation.
ident=series[-1][2];d=metadata(ident);films={}
for f in d['files']:
 name=f['name']
 if not name.startswith('Futurama.') or not name.endswith('.mp4') or name.endswith('.ia.mp4') or float(f.get('length') or 0)<4000:continue
 title=re.sub(r'\b(?:2007|2008|2009|720p|1080p|WEB|BluRay)\b.*','',name.replace('.',' ')).strip();title=title.replace('Benders','Bender’s').replace('Futurama ','Futurama: ')
 url='https://archive.org/download/'+ident+'/'+urllib.parse.quote(name)
 if url not in existing:cat['programmes'].append({'type':'Movie','show':'Futurama','title':title,'source_title':title,'title_override':title,'url':url,'source_page':'https://archive.org/details/'+ident,'archive_identifier':ident,'filename':name,'duration_seconds':float(f['length']),'duration_evidence':'IA exact filename length','channels':['AAA'],'channel':'AAA','catalogue_status':'broadcast','language_status':'english-declared','language_label':'Uploader declares English; audio not independently reviewed'});new_urls.append(url);existing.add(url)
 films[title]=url
(ROOT/'editorial-series.json').write_text(json.dumps(defs,indent=2,ensure_ascii=False));(ROOT/'source-library.json').write_text(json.dumps(cat,separators=(',',':'),ensure_ascii=False));(ROOT/'addition-import-summary.json').write_text(json.dumps({'series_episode_counts':dict(counts),'standalone_urls':selected,'feature_film_urls':films,'new_urls':new_urls,'notes':['Counts describe reviewed sources, not all-time upload title promises.','Futurama is a partial recovery: three numbered episodes and four films.','English is uploader metadata evidence; full audio not independently reviewed.','Serbian Mickey files, cut episodes and .ia.mp4 derivatives excluded.','Samurai Jack source was adverts; Zoey source had no direct MP4; FMA candidate was Brotherhood in Matroska, not original series.']},indent=2,ensure_ascii=False));print(json.dumps(dict(counts),indent=2))
