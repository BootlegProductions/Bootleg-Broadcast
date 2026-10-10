"""Restore evidenced original markdown episodes and author successor runs. No network or guessed runtimes."""
import json,re,urllib.parse,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda f:json.loads((ROOT/f).read_text())
write=lambda f,d:(ROOT/f).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
audit=read('markdown-series-recheck.json');cat=read('source-library.json');defs=read('tools/base-editorial-series.json');config=read('tools/base-editorial-lineups.json');byurl={p['url']:p for p in cat['programmes']}
raw={}
for path in list((ROOT/'tools/runtime-cache').glob('*.json'))+list((ROOT/'tools/markdown-recheck').glob('*.json'))+list((ROOT.parent/'account-source-check').glob('*.json')):
 try:d=json.loads(path.read_text())
 except Exception:continue
 if not isinstance(d,dict) or not isinstance(d.get('files'),list):continue
 identifier=d.get('metadata',{}).get('identifier',path.stem);raw[identifier]=d
 files=[{k:f[k] for k in ['name','length','duration','format','source'] if k in f} for f in d['files'] if f.get('name','').lower().endswith('.mp4')]
 write('tools/runtime-cache/'+identifier+'.json',{'identifier':identifier,'files':files})
fix={
 'Striparella':'Stripperella','Fish police':'Fish Police','Xaoilin Showdown':'Xiaolin Showdown',
 'Harlem Globetrotters (17 Episodes)':'Harlem Globetrotters','The Avengers United They Stand (1999-2000)':'The Avengers: United They Stand',
 'Dan. Vs. Complete Season 1-3 (2011-2013)':'Dan Vs.','Final Space Complete Season 1-3 (2018-2021)':'Final Space',
 'Duck Dodgers (2003) COMPLETE SERIES':'Duck Dodgers','Hi Hi Puffy AmiYumi Remastered':'Hi Hi Puffy AmiYumi',
 'Loonatics Unleashed Complete S01-2 Season 1-2 (2005-2007)':'Loonatics Unleashed','Mucha Lucha - Seasons 1 and 2 (some episodes)':'¡Mucha Lucha!',
 'Secret Mountain Fort Awesome Complete Series':'Secret Mountain Fort Awesome',
 'Skatoony (UK Version) Vol. 2':'Skatoony (UK)','Skatoony (UK Version)':'Skatoony (UK)',
 'TAWOG Season 1 Netflix Ordering':'The Amazing World of Gumball','The Amazing World Of Gumball Season 3':'The Amazing World of Gumball',
 'Teen Titans (Complete Series)':'Teen Titans','Xiaolin Chronicles (2013) (Logoless)':'Xiaolin Chronicles',
 'The Zeta Project (2001–2002)':'The Zeta Project',"Maxie's World The Complete Series":"Maxie's World",
 'Mary Kate And Ashley In Action! Partially Complete Series':'Mary-Kate and Ashley in Action!',
 'Eden Of The East ( BDRip 1080p AC 3 10bit)':'Eden of the East','Moaning Of Life':'The Moaning of Life','The O.C. (2003–2007)':'The O.C.',
 'Man vs Food':'Man v. Food','Man vs Food Nation':'Man v. Food Nation',
 'Doomsday Preppers (2012–2014)':'Doomsday Preppers',"Overhaulin' The Complete First Season":"Overhaulin'",
 'The Melancholy Of Haruhi Susumiya':'The Melancholy of Haruhi Suzumiya',
 'Paranoia Agent Anime Complete English Sub Season 1 (2004)':'Paranoia Agent',
 'Prison School Anime Complete Season 1 [Dubbed] [Uncensored] [720p]':'Prison School',
 'Powerpuff Girls Z Complete Series Dubbed':'Powerpuff Girls Z','Powerpuff Girls Z Japanese Sub':'Powerpuff Girls Z',
 'Adult Swim - Durarara!! Recordings':'Durarara!!',
 'Heavens Lost Property':"Heaven's Lost Property",'Helpful Fox':'The Helpful Fox Senko-san',
 'ChäoS;HEAd (1080p) (English + Japanese)':'Chaos;Head',
 'Clannad [Dual Audio] [OVAs] [Complete]':'Clannad',
 'Gintama (720p) (Complete Series + Movies)':'Gintama',
 'CyberPunk EdgeRunners 1080p':'Cyberpunk: Edgerunners','Dandadan S1-S2':'Dandadan',
 'ItaKiss - Full Series - English Sub':'ItaKiss','Kaichou Wa Maid Sama Animax English Dub':'Maid Sama!',
 'Little Witch Academia - Full Series - English Sub':'Little Witch Academia',
 'Love Hina Again Episode 1':'Love Hina Again','Maison Ikkoku english dub':'Maison Ikkoku',
 'Maken Ki! 1x 12':'Maken-Ki!','Monster Upscale beta':'Monster',
 'Revolutionary Girl Utena Episode 13 ( Dub) Tracing A Path':'Revolutionary Girl Utena',
 'To Love Ru 1x 4':'To Love-Ru',
 'Valkyrie Drive Mermaid Episodes 1-12 and Specials 1-6 (Sub)':'Valkyrie Drive: Mermaid',
 'Vandread Episode 13 English Dub':'Vandread','Witchblade English Dub Episode 23':'Witchblade',
 'Assassination Classroom Season 1 (ENGLISH DUB)':'Assassination Classroom',
 'Assassination Classroom S1 (Dub)':'Assassination Classroom',
 'No Matter How I Look At It, It\'s You Guys\' Fault I\'m Not Popular! Season 1':'WataMote',
 'Rokudenashi Majutsu Koushi To Akashic Records ( Dub)':'Akashic Records of Bastard Magic Instructor',
 'Re Zero Kara Hajimeru Isekai Seikatsu':'Re:Zero',
 'Angels of Death Satsuriku No Tenshi ( Dub)':'Angels of Death',
 '7 Seeds ( Dub) Seasons 1':'7 Seeds','7 Seeds ( Dub) Seasons 2':'7 Seeds',
 'Akagami No Shirayuki Hime Seasons 1( Dub)':'Snow White with the Red Hair',
 'Akagami No Shirayuki Hime Seasons 2( Dub)':'Snow White with the Red Hair',
 'Bakuman S1 (Sub-English)':'Bakuman','Bakuman S2 (Sub-English)':'Bakuman','Bakuman S3 (Sub-English)':'Bakuman','Bakuman (English Dub)':'Bakuman',
 'Genshiken (Season 1 - 2) + Kujibiki Unbalance + OVA (English Dub)':'Genshiken',
}
def label(name):
 name=fix.get(name,name)
 name=re.sub(r'\s*\((?:\s*Dub|Sub-English|English Dub|\d{4}[–-]\d{4}|\d{4}|\d{3,4}p[^)]*)\)\s*',' ',name,flags=re.I)
 name=re.sub(r'\s*\[.*?\]\s*',' ',name).strip()
 return name
slug=lambda s:re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
# Collection headings are aliases, not separate seasons or shows.
existing={re.sub(r'[^a-z0-9]','',v['name'].lower()):k for k,v in defs.items()}
report={'restored':{},'held_for_mapping':[],'rules':['Original user Japanime sources accepted as English dub or English subtitles, as confirmed by the user.','No guessed runtime. No DVD disc/menu/bonus is passed off as a numbered episode.','Existing working original markdown URLs preserved; exact originals preferred over duplicate IA encodes.']}
channel_new=collections.defaultdict(list)
def numbering(filename,p,show):
 text=urllib.parse.unquote(filename).replace('_',' ');base=text.rsplit('/',1)[-1];base=re.sub(r'\[[^\]]*\]','',base);base=re.sub(r'\([^)]*(?:\bBD|DVD|WEB|1080|720|480|1440|Dual|AAC|x264|x265)[^)]*\)','',base,flags=re.I)
 if re.search(r'\b(?:DISC\s*\d*|MENU|VTS|BONUS|MOVIE|TRAILER|OPENING|ENDING|SPECIALS?)\b|\bD\d+(?:B\d+)?\b|\bB\d[ _-]*t\d|\bSCN\b|\bVOL(?:UME)?\s*\d|/Extras/',text,re.I):return None
 sm=re.search(r'(?:Season|Temporada|Series|\bS)[ ._-]*(\d+)',text,re.I);season=int(sm[1]) if sm else 1
 leading=re.match(r'^\s*0*(\d{1,3})[ ._-]',base)
 if leading and not re.match(r'^\d',show):return season,int(leading[1])
 patterns=[r'\bS(\d+)[ -]+(\d+)\b',r'\bS\s*(\d+)\s*[ ._-]*(?:EP?|Episode)\s*0*(\d+)',r'\b(\d+)\s*[x-]\s*(\d+)\b',r'Season\s*(\d+).*?Episode\s*(\d+)']
 if show=='The Helpful Fox Senko-san':
  m=re.search(r'HFS0*(\d+)-EN',base,re.I)
  if m:return 1,int(m[1])
 for pattern in patterns:
  m=re.search(pattern,base,re.I)
  if m:return int(m[1]),int(m[2])
 for pattern in [r'\b(?:Episode|Ep\.?|Chapter|cap|E)\s*[- ]*0*(\d+)\b',r'^0*(\d{1,3})\b',r'\s[-–]\s*0*(\d{1,3})\b',r'\bepisode0*(\d+)s\d+',r'\bDXD0*(\d+)\b']:
  m=re.search(pattern,base,re.I)
  if m:return season,int(m[1])
 # Number following the actual show title; ignore years and release resolution.
 cleaned=re.sub(r'\[[^\]]*\]|\([^)]*\)','',base)
 m=re.search(r'(?<!\d)0*(\d{1,3})(?=\s|\.|-|$)',cleaned)
 if m and not re.search(r'\b(?:DVD|DISC|SCN|B\d[_ -]t\d)\b',base,re.I) and re.sub(r'[^a-z]','',cleaned[:m.start()].lower()) in {re.sub(r'[^a-z]','',show.lower()), 'hfs', 'dxd', 'monster', 'overhaulin', 'thelandbeforetime'}:
  n=int(m[1])
  if show=='The Land Before Time' and 100<n<200:return 1,n-100
  if show=="Overhaulin'" and 100<n<200:return 1,n-100
  return season,n
 return None
for row in audit:
 if row.get('priority')!='Strong restoration candidate':continue
 name=label(row['show']);key=existing.get(re.sub(r'[^a-z0-9]','',name.lower()),'restored-'+slug(name));ch=row['channel'];count=0
 for f in row.get('exact_files',[]):
  url=f['url'];old=byurl.get(url,{})
  # Substitute an original only when this exact path exists in fetched metadata.
  if f['filename'].endswith('.ia.mp4'):
   original=f['filename'].replace('.ia.mp4','.mp4');ff=next((x for x in raw.get(f['collection'],{}).get('files',[]) if x['name']==original and x.get('length')),None)
   if ff:f={**f,'filename':original,'length':ff['length']};url='https://archive.org/download/'+f['collection']+'/'+urllib.parse.quote(original,safe='/');old=byurl.get(url,old)
   elif url not in byurl:continue
  try:runtime=float(f.get('length') or 0)
  except Exception:continue
  if not 600<=runtime<=4500:continue
  nums=numbering(f['filename'],old,name)
  named=not nums and name in ['Drake & Josh','Sacred Weeds'] and not re.search(r'christmas|special|movie',f['filename'],re.I)
  if not nums and not named:continue
  if nums and nums[1]<=0:continue
  # Mixed Genshiken bundle includes a separate series: keep its identity separate.
  if name=='Genshiken' and 'kujibiki' in f['filename'].lower():continue
  if name=='Total Drama Island' and not re.search(r'Total Drama Island',f['filename'],re.I):continue
  if nums and nums[0]==0:continue
  defs.setdefault(key,{'name':name,'shows':[],'max_episode_seconds':4500 if runtime>2100 else 2100})
  defs[key]['max_episode_seconds']=max(defs[key].get('max_episode_seconds',2100),int(runtime)+1)
  for alias in [row['show'],old.get('source_show'),name]:
   if alias and alias not in defs[key]['shows']:defs[key]['shows'].append(alias)
  p=byurl.get(url)
  if p is None:
   p={'url':url,'channels':[ch],'channel':ch,'source_page':'https://archive.org/details/'+f['collection'],'catalogue_origins':['original-markdown-restoration']};cat['programmes'].append(p);byurl[url]=p
  season,ep=nums or (1,None)
  if nums:p['evidenced_season']=season;p['evidenced_episode']=ep
  p.update(type='Episode',series_id=key,series_label=name,show=name,source_show=name,archive_identifier=f['collection'],filename=f['filename'],duration_seconds=runtime,duration_evidence='IA exact filename length',season_number=season,episode_number=ep,season=str(season),episode=ep,catalogue_status='broadcast',restoration_evidence='Original markdown exact file + measured runtime',broadcast_held=False)
  p.setdefault('source_title',f['filename'].rsplit('/',1)[-1]);p.setdefault('title',p['source_title'])
  if ch=='Japanime':p.update(language_status='user-confirmed-english-access',language_label='English dub or English subtitles — user confirmed original collection',language_evidence='User confirmation of original Japanime markdowns')
  p['preferred_source']=bool(re.search(r'\b(?:dub|english|EN[ _-])\b',f['filename'],re.I))
  p.pop('title_override',None)
  if named:
   detail=re.sub(r'\.(?:ia\.)?mp4$','',f['filename'].rsplit('/',1)[-1],flags=re.I);detail=re.sub(r'^Sacred Weeds\s*','',detail,flags=re.I)
   p['title_override']=name+' — '+detail;p['editorial_order']=count;p['content_id']=key+':named:'+slug(detail);p.pop('episode',None);p.pop('episode_number',None)
  count+=1
 if count:
  report['restored'].setdefault(key,{'name':defs[key]['name'],'channel':ch,'source_files':0})['source_files']+=count
  if key not in channel_new[ch]:channel_new[ch].append(key)
 else:report['held_for_mapping'].append({'channel':ch,'show':row['show'],'reason':'Available files lack a confidently mapped, measured full episode (disc recordings, extras, or movies are not regular episodes).'})
# User upload titled Finale actually contains the US Office series. Exact metadata proves filenames/runtimes.
for identifier,name,key,ch in [('the-office-us-9x-23-finale','The Office (US)','office-us','Star Spangled TV'),('btvs_20260710','Buffy the Vampire Slayer','buffy','Star Spangled TV')]:
 defs.setdefault(key,{'name':name,'shows':[name],'max_episode_seconds':4500});count=0
 for f in raw.get(identifier,{}).get('files',[]):
  fn=f['name'];m=re.search(r'S(\d+)E(\d+)',fn,re.I) or re.search(r'(?:/|\b)(\d+)-(\d+)_',fn)
  try:runtime=float(f.get('length',0))
  except Exception:continue
  if not fn.endswith('.mp4') or '/._' in fn or not m or not 900<=runtime<=4500:continue
  season,ep=map(int,m.groups());url='https://archive.org/download/'+identifier+'/'+urllib.parse.quote(fn,safe='/');p=byurl.get(url)
  if p is None:p={'url':url};byurl[url]=p;cat['programmes'].append(p)
  detail=fn.rsplit('/',1)[-1];p.update(type='Episode',show=name,source_show=name,series_id=key,series_label=name,season_number=season,episode_number=ep,season=str(season),episode=ep,source_title=detail,title=detail,archive_identifier=identifier,filename=fn,duration_seconds=runtime,duration_evidence='IA exact filename length',channels=[ch],channel=ch,source_page='https://archive.org/details/'+identifier,catalogue_status='broadcast',preferred_source=True,language_status='uploader-english',language_label='Uploader reports English',restoration_evidence='Public account collection exact filename + measured runtime');count+=1
 if count:report['restored'][key]={'name':name,'channel':ch,'source_files':count};channel_new[ch].append(key)
# Explicit successor chains, chosen for the block audience. Keep core breakfast and evening anchors.
run_defs={}
def run(ch,at,keys,block,episodes=2,start_existing=True):
 slot=next(s for s in config['channels'][ch] if s['at']==at)
 if start_existing:keys=[slot['series']]+keys
 keys=list(dict.fromkeys(k for k in keys if k in defs))
 if not keys:return
 chain=slug(ch)+'-'+at.replace(':','');run_defs[chain]={'name':block,'series':keys,'repeat_after_full_cycle':True};slot.update(series='@run:'+chain,episodes=episodes,block=block)
 slot.pop('fallback',None)
def keymatch(ch,terms):
 return [k for k in channel_new[ch] if any(t.lower() in defs[k]['name'].lower() for t in terms)]
def allremaining(ch,assigned):return [k for k in channel_new[ch] if k not in assigned]
run('90s Toons','12:00',keymatch('90s Toons',['Robocop','Street Sharks','Avengers']), 'Afternoon action — complete series runs')
run('90s Toons','17:00',keymatch('90s Toons',['Sherlock','Globetrotters']), 'Classic adventure — complete series runs')
run('AAA','20:00',keymatch('AAA',['Final Space','Oblongs','Dan Vs','Fish Police']), 'Animation comedy — complete series runs')
run('AAA','00:00',keymatch('AAA',['Aeon','Stripperella']), 'Late animation — complete series runs')
assigned=keymatch('Cartoons Cartoons',['Land Before','Puffy','Skatoony','Duck Dodgers'])
run('Cartoons Cartoons','17:00',assigned,'After school cartoons — complete series runs')
remaining=allremaining('Cartoons Cartoons',assigned);run('Cartoons Cartoons','16:00',remaining,'Afternoon action — complete series runs')
run('Dickleodeon','11:00',keymatch('Dickleodeon',["Maxie",'Zeta']),'Nick afternoon adventures — complete series runs')
run('Dickleodeon','17:00',keymatch('Dickleodeon',['Drake']),'Nick comedy — complete series runs')
run('Dizzy','14:00',channel_new['Dizzy'],'Afternoon animation — complete series runs')
run('GirlyPop','15:00',channel_new['GirlyPop'],'After school adventures — complete series runs')
run('Off-Licence TV','17:00',keymatch('Off-Licence TV',['Moaning','Kitchen']),'Travel and kitchen programmes — complete series runs',1)
run('Off-Licence TV','00:00',keymatch('Off-Licence TV',['Utopia','Sacred']),'After dark drama and documentaries — complete series runs',1)
run('Off-Licence TV','23:00',keymatch('Off-Licence TV',['Gervais','Brass','Ali G']),'Late comedy — complete series runs',1)
run('Star Spangled TV','18:00',keymatch('Star Spangled TV',['O.C.','Buffy']),'US evening drama — complete series runs',1)
run('Star Spangled TV','22:00',keymatch('Star Spangled TV',['Norm','Predator']),'Late US factual and comedy — complete series runs',1)
run('Star Spangled TV','15:00',keymatch('Star Spangled TV',['Office']),'US comedy — complete series runs',1)
run('What','13:00',keymatch('What',['Pawn','Food','Overhaulin']),'Factual daytime — complete series runs',1)
run('What','18:00',keymatch('What',['Doomsday','Maximum','Shocking','Louis']),'Factual evenings — complete series runs',1)
# Japanime: young audiences at breakfast, teen stories in the afternoon, adult shows at night.
jp=channel_new['Japanime']
kids=keymatch('Japanime',['Powerpuff Girls Z','Little Witch','Chance Pop','Cross Game','Bakuman','Barakamon','Helpful Fox'])
late=keymatch('Japanime',['Elfen','Prison','High School DxD','Sekirei','Queen','Valkyrie','To Love','Maken','Golden Boy','Panty','Heaven','Hajimete','Witchblade','Angel Cop'])
thriller=keymatch('Japanime',['Parasyte','Monster','Paranoia','Ergo','Gilgamesh','Another','Angels of Death','Chaos','91 Days','Death Parade','Cyberpunk','Jormungand','Desert Punk','Dominion','Gunsmith','Dirty Pair'])
late=list(dict.fromkeys(late));thriller=[k for k in thriller if k not in late];teen=[k for k in jp if k not in kids+late+thriller]
# Parallel authored chains give the restored collection room to complete without placing adult material in mornings.
for at,keys,block in [('14:00',kids,'Family anime afternoons'),('15:00',teen[::3],'Afternoon anime stories'),('16:00',teen[1::3],'Afternoon anime adventures'),('20:00',teen[2::3],'Evening anime stories'),('19:00',thriller[::2],'Evening anime mystery'),('22:00',thriller[1::2],'Late anime thrillers'),('00:00',late[::2],'Adults after midnight'),('01:00',late[1::2],'Adults after midnight')]:
 run('Japanime',at,keys,block+' — complete series runs')
config['series_runs']=run_defs
config['note']='Hand-authored appointments and successor series runs. Each run plays evidenced episodes in order; the next series takes over after completion. The browser reads finished monthly JSON files.'
# Explain candidates not silently treated as restored.
assigned={k for r in run_defs.values() for k in r['series']}
report['restored_series_count']=len(report['restored']);report['unassigned_restored']=[v['name'] for k,v in report['restored'].items() if k not in assigned]
write('source-library.json',cat);write('editorial-series.json',defs);write('editorial-lineups.json',config);write('restoration-report.json',report)
print(json.dumps({'restored_series':len(report['restored']),'source_files':sum(x['source_files'] for x in report['restored'].values()),'held':report['held_for_mapping'],'unassigned':report['unassigned_restored']},indent=2))
