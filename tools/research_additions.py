"""Review candidate Archive collections without assuming every title is a full episode."""
import json,urllib.request,urllib.parse,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];review=ROOT/'tools/additions-research';review.mkdir(exist_ok=True)
ids=['MSBTVSeries','themagicschoolbuscompleteseries','libertys-kids-est-1776-full-animated-series','SamuraiJack_201704','20230208_20230208_2248','fullmetal-alchemist-brotherhood-1080p-x265-2009-2010-lossless-jpn-eng-p1','zoey-101-spring-break-up','futurama.-benders.-big.-score.-2007.720p.-web-dl.x-265-heteam_202502','korgoth-of-barbaria-all-parts-including-real-introduction','KorgothOfBarbariaHDFullPilot','korgoth-of-barbaria-s-01-e-01','TheModifyers','the_modifyers','welcome-to-eltingville','constant_payne','dexters.-laboratory.-s-00-e-01-rude.-removal.-banned.-episode.-1080p.-aac-2.0.x-264-obfuscated','youtube-DShFdAFwWz0','dexters-lab-rude-removal-uncut','1983-alvin-and-the-chipmunks-complete','DragonTalesTVSeries','The-Secret-Saturdays','beastwarstransformers1080p','Reboot-HD','blosc','digimon-data-squad-the-complete-series','Mickey-Mouse-Works','the-batman-03x-01']
def get(i):
 try:
  d=json.load(urllib.request.urlopen('https://archive.org/metadata/'+i,timeout=18));(review/(i+'.json')).write_text(json.dumps(d,ensure_ascii=False));f=[p for p in d.get('files',[]) if p['name'].endswith('.mp4') and not p['name'].endswith('.ia.mp4')];return {'id':i,'title':d.get('metadata',{}).get('title'),'language':d.get('metadata',{}).get('language'),'description':str(d.get('metadata',{}).get('description',''))[:600],'mp4_count':len(f),'examples':[{k:p.get(k) for k in ['name','length','format']} for p in f[:3]]}
 except Exception as e:return {'id':i,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
 results=list(ex.map(get,ids))
(ROOT/'additions-source-review.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
for row in results:print(json.dumps(row,ensure_ascii=False),flush=True)
