"""Check selected exact files without downloading full videos."""
import json,urllib.request,concurrent.futures,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];cat=json.loads((R/'source-library.json').read_text())['programmes'];summary=json.loads((R/'addition-import-summary.json').read_text());urls=list(summary['standalone_urls'].values())+list(summary['feature_film_urls'].values())
for key in summary['series_episode_counts']:
 rows=[p for p in cat if p.get('series_id')==key and p.get('preferred_source') and not p.get('broadcast_held')]
 if rows:urls += [rows[0]['url'],rows[-1]['url']]
def check(url):
 try:
  req=urllib.request.Request(url,headers={'Range':'bytes=0-4095','User-Agent':'BootlegBroadcastSourceReview/0.35.2'})
  with urllib.request.urlopen(req,timeout=25) as r:
   body=r.read(4096);return {'url':url,'status':r.status,'content_type':r.headers.get('Content-Type'),'mp4_header':b'ftyp' in body[:128],'bytes_read':len(body)}
 except Exception as e:return {'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(check,dict.fromkeys(urls)))
out={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'First/last imported episode per series and all added one-offs/films; first 4096 bytes only. This does not verify full playback, spoken language or subtitle tracks.','results':results};(R/'addition-file-probes.json').write_text(json.dumps(out,indent=2));print(json.dumps({'checked':len(results),'failed':[r for r in results if not r.get('mp4_header')]},indent=2))
