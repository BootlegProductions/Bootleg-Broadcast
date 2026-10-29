"""Check a focused selection of the Nick IDs uploader's complete series and movies.

Actual video filenames, measured runtimes and catalogue overlap only.
"""
import json,pathlib,re,urllib.parse,urllib.request,collections
root=pathlib.Path(__file__).resolve().parents[1]
items={
 "lazy-town-s-01-e-03-featuring-sports-day":{"channel":"Dickleodeon","kind":"series","name":"LazyTown"},
 "i-spy-s-01-e-13-a-campfire-night-light-freewheelin-fun_202202":{"channel":"Dickleodeon","kind":"series","name":"I Spy"},
 "figure_it_out_-_season_2_-_episode_06___578412314a427":{"channel":"Dickleodeon","kind":"series","name":"Figure It Out"},
 "splatalot-s-01-e-06-shoved-by-a-rainbow":{"channel":"Dickleodeon","kind":"series","name":"Splatalot"},
 "piglet-s-big-movie":{"channel":"Dizzy","kind":"movie","name":"Piglet's Big Movie"},
 "sesame.-street.-presents-follow.that.-bird.-1985.-web-dl.x-264-fgt":{"channel":"GirlyPop","kind":"movie","name":"Follow That Bird"},
 "lost-and-found-2008-film":{"channel":"GirlyPop","kind":"movie","name":"Lost And Found"},
 "sesame-street-elmos-christmas-countdown_202202":{"channel":"GirlyPop","kind":"christmas","name":"Elmo's Christmas Countdown"},
 "a-child-s-christmas":{"channel":"GirlyPop","kind":"christmas","name":"A Child's Christmas"}
}
catalogue=json.loads((root/'source-library.json').read_text())
existing_urls={p.get('url') for p in catalogue.get('programmes',[])}
byshow=collections.Counter(str(p.get('show') or '').lower().strip() for p in catalogue.get('programmes',[]))
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'BootlegBroadcast/1.0'})
 with urllib.request.urlopen(req,timeout=28) as response:return json.loads(response.read().decode('utf-8'))
out={'sources':[],'errors':[]}
for ident,target in items.items():
 try:
  meta=fetch('https://archive.org/metadata/'+urllib.parse.quote(ident))
  origs=[p for p in meta.get('files',[]) if isinstance(p.get('name'),str) and re.search(r'\.mp4$',p['name'],re.I) and not p['name'].endswith('.ia.mp4')]
  videos=[]
  for f in origs:
   name=f['name']
   try:seconds=round(float(f.get('length') or f.get('duration') or 0),3)
   except(TypeError,ValueError):seconds=0
   if not 240<=seconds<=12500:continue
   url='https://archive.org/download/'+urllib.parse.quote(ident)+'/'+urllib.parse.quote(name,safe='/')
   videos.append({'filename':name,'seconds':seconds,'url':url,'duplicate_url':url in existing_urls})
  videos.sort(key=lambda x:x['filename'])
  out['sources'].append({'identifier':ident,**target,'archive_title':meta.get('metadata',{}).get('title'),
    'eligible_original_mp4':len(videos),'already_in_catalogue_url':sum(v['duplicate_url'] for v in videos),
    'existing_show_count':byshow.get(target['name'].lower(),0),
    'videos':videos[:200],'truncated':len(videos)>200})
 except Exception as exc:out['errors'].append({'identifier':ident,'error':str(exc)[:200]})
(root/'nick-uploader-programmes-review.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'sources':[{'name':p['name'],'mp4':p['eligible_original_mp4'],
'already_in_catalogue':p['already_in_catalogue_url'],'existing_show_count':p['existing_show_count']}
for p in out['sources']],'errors':out['errors']},indent=2))
