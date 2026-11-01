"""Audit Halloween/Christmas film choices before building daily holiday cinema.
Reads full repo catalogue and already-imported Archive feeds.
"""
import json,collections,re,pathlib,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
j=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
cat=j('source-library.json')['programmes']
cfg=j('editorial-lineups.json')
calendar=j('editorial-film-calendar.json')
def js_data(file,marker,until):
 s=(ROOT/file).read_text(encoding='utf-8')
 return json.loads(s.split(marker,1)[1].split(until,1)[0])
holiday=js_data('holiday-programmes.js',' const db=',';\n root.BOOTLEG_HOLIDAY_MEDIA=db;')['programmes']
seasonal=js_data('seasonal-programmes.js',' const db=',';\n root.BOOTLEG_SEASONAL_MEDIA=db;')['programmes']
nick=js_data('nick-uploader-programmes.js',' const data=',';\n root.BOOTLEG_UPLOADER_PROGRAMMES=data;')['programmes']
def valid(p):
 u=p.get('url','')
 if not u.startswith('https://archive.org/download/') or not re.search(r'\.mp4(?:$|\?)',u,re.I):return False
 if p.get('broadcast_held') or p.get('language_status') in ['non-english','reported-non-english']:return False
 if re.search(r'\bx265\b|\bhevc\b|full.collection|trailer|bonus|menu',p.get('filename','') or '',re.I):return False
 return 1800<=float(p.get('duration_seconds') or 0)<=10500
def channels(p):
 cc=p.get('channels') or p.get('channel') or []
 if isinstance(cc,str):cc=[cc]
 return [c for c in cc if c in cfg['channels']]
sources=[('catalogue',cat),('new-holiday',holiday),('seasonal',seasonal),('nick',nick)]
counts={}
examples={}
for ch in cfg['channels']:
 rows=[]
 for origin,items in sources:
  for p in items:
   if ch not in channels(p) or not valid(p):continue
   if p.get('type') not in ['Movie','Special']:continue
   title=p.get('title') or ''
   tags=p.get('seasonal_tags') or []
   christmas=bool('christmas' in tags or re.search(r'christmas|xmas|santa|snow|winter|noel|rudolph|frosty',title,re.I))
   halloween=bool('halloween' in tags or re.search(r'halloween|spooky|scary|monster|ghost|witch|vampir|coraline|paranorman|franken',title,re.I))
   rows.append({'origin':origin,'title':title,'seconds':p.get('duration_seconds'),'type':p.get('type'),'url':p['url'],'christmas':christmas,'halloween':halloween})
 byurl={r['url']:r for r in rows}
 v=list(byurl.values())
 counts[ch]={'all':len(v),'movies':sum(x['type']=='Movie' for x in v),'specials':sum(x['type']=='Special' for x in v),'halloween':sum(x['halloween'] for x in v),'christmas':sum(x['christmas'] for x in v),'new_imports':sum(x['origin']!='catalogue' for x in v)}
 examples[ch]={'halloween':[x['title'] for x in v if x['halloween']][:12],'christmas':[x['title'] for x in v if x['christmas']][:12]}
old=collections.Counter()
for key,url in calendar['appointments'].items():
 if key.startswith('2026-10-'):old['october']+=1
 if key.startswith('2026-12-'):old['december']+=1
out={'counts':counts,'existing_holiday_appointments':dict(old),'existing_calendar_entries':len(calendar['appointments']),'samples':examples,'origins':{orig:len(p) for orig,p in sources}}
(ROOT/'holiday-film-inventory-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'counts':counts,'existing_holiday_appointments':dict(old),'origins':out['origins']},indent=2,ensure_ascii=False))
