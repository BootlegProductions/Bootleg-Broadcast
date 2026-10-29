"""Probe a representative sample of newly sourced station idents and programmes.

HTTP HEAD only: no full video downloads, and browser codec/audio compatibility
cannot be inferred solely from HTTP status.
"""
import pathlib,json,urllib.request,concurrent.futures
root=pathlib.Path(__file__).resolve().parents[1]
s=(root/'channel-idents.js').read_text(encoding='utf-8')
idents=json.loads(s.split('globalThis.BOOTLEG_IDENT_POOLS=',1)[1].rsplit(';',1)[0])['channels']
s=(root/'nick-uploader-programmes.js').read_text(encoding='utf-8')
programmes=json.loads(s.split(' const data=',1)[1].split(';\n root.BOOTLEG_UPLOADER_PROGRAMMES=data;',1)[0])['programmes']
sample=[]
for ch,clips in idents.items():
 regular=[x for x in clips if not x.get('months')]
 seasonal=[x for x in clips if x.get('months')]
 for item in (regular[:4]+seasonal[:2]):
  sample.append({'category':'ident','channel':ch,'title':item['title'],'url':item['url']})
for show in ('Figure It Out','I Spy','Splatalot'):
 for item in [p for p in programmes if p['show']==show][:2]:
  sample.append({'category':'series','channel':item['channel'],'title':item['title'],'url':item['url']})
for p in programmes:
 if p['type'] in ('Movie','Special'):
  sample.append({'category':'film_or_special','channel':p['channel'],'title':p['title'],'url':p['url']})
def check(p):
 result=dict(p)
 try:
  request=urllib.request.Request(p['url'],method='HEAD',headers={'User-Agent':'Mozilla/5.0','Accept':'video/mp4,*/*'})
  with urllib.request.urlopen(request,timeout=22) as response:
   result['status']=response.status
   result['mime']=response.headers.get('Content-Type','')
   result['http_reachable']=response.status in (200,206) and 'video' in result['mime']
 except Exception as e:
  result['http_reachable']=False
  result['error']=str(e)[:250]
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 results=list(pool.map(check,sample))
report={'checked':len(results),'http_reachable':sum(x['http_reachable'] for x in results),
        'results':results,'note':'HTTP HEAD only. Video/audio playback and rights not verified.'}
(root/'nick-boomerang-link-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checked':len(results),'http_reachable':report['http_reachable'],
'failed':[{'title':x['title'],'error':x.get('error'),'status':x.get('status')} for x in results if not x['http_reachable']]},indent=2))
