"""Fetch exact IA filename metadata. No guessed runtimes or invented file URLs."""
import concurrent.futures,json,urllib.request,time,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CACHE=ROOT/'tools/runtime-cache';CACHE.mkdir(exist_ok=True)
cat=json.loads((ROOT/'source-library.json').read_text())['programmes'];defs=json.loads((ROOT/'editorial-series.json').read_text());wanted={s for v in defs.values() for s in v['shows']}
rows=[p for p in cat if (p.get('show') in wanted or p.get('type') in ['Movie','Special'] or p.get('holiday_events')) and not p.get('broadcast_held')]
# Keep measured holiday sources, fetch the selected series and all short-form break collections.
ads=json.loads((ROOT/'adverts.json').read_text())['channels'];breaks=json.loads((ROOT/'seasonal-breaks.json').read_text());rows+=sum(ads.values(),[])
for season in ['october','december','regular']:rows+=breaks.get(season,{}).get('adverts',[])
ids=set()
for p in rows:
 u=p.get('url','');identifier=p.get('archive_identifier')
 if not identifier and '/download/' in u:identifier=u.split('/download/',1)[1].split('/')[0]
 if identifier and (p.get('show') in wanted or p.get('type')=='Advert' or not p.get('duration_seconds')):ids.add(identifier)
def get(identifier):
 target=CACHE/(identifier+'.json')
 if target.exists():return identifier,'cached'
 try:
  req=urllib.request.Request('https://archive.org/metadata/'+identifier,headers={'User-Agent':'BootlegBroadcastScheduleReview/0.35'})
  with urllib.request.urlopen(req,timeout=18) as resp:data=json.load(resp)
  if 'files' not in data:return identifier,'No files'
  # Persist only scheduling evidence, not unnecessary collection metadata.
  output={'identifier':identifier,'files':[{k:p[k] for k in ['name','length','duration','format','size'] if k in p} for p in data['files']],'language':data.get('metadata',{}).get('language')}
  target.write_text(json.dumps(output,ensure_ascii=False));return identifier,'ok'
 except Exception as e:return identifier,type(e).__name__+': '+str(e)
results={}
with concurrent.futures.ThreadPoolExecutor(max_workers=14) as ex:
 for i,(identifier,status) in enumerate(ex.map(get,sorted(ids)),1):
  results[identifier]=status
  if i%40==0:print(f'Metadata collections reviewed: {i}/{len(ids)}',flush=True)
local={}
for p in (ROOT/'assets').rglob('*.mp4'):
 try:
  n=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(p)],timeout=8))
  local[str(p.relative_to(ROOT))]=n
 except Exception:pass
(ROOT/'tools/local-runtimes.json').write_text(json.dumps(local,indent=2));(ROOT/'runtime-review.json').write_text(json.dumps({'metadata_results':results,'local_asset_runtimes':local,'note':'IA filename metadata and local ffprobe durations. This is not spoken-language verification or a complete playback review.'},indent=2));print('Done:',len(results),'collections;',len(local),'local video runtimes.',flush=True)
