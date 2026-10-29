"""Check representative original MP4 URLs from the three supplied holiday sets.

HEAD checks do not prove full file decoding, audio, or rights; never replace
a working video solely due to a temporary HEAD failure.
"""
import concurrent.futures, json, pathlib, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/"seasonal-archive-inventory.json").read_text())
by={x["identifier"]:x["files"] for x in inventory["items"]}
sample=[]
for identifier,files in by.items():
 categories=[[],[],[]]
 for f in files:
  if not f["name"].lower().endswith(".mp4"):continue
  t=f["seconds"];bucket=0 if t<90 else 1 if t<3900 else 2
  if t>0:categories[bucket].append(f)
 selected=[]
 for group,num in zip(categories,[6,7,3]):
  if not group:continue
  step=max(1,len(group)//num)
  selected.extend(group[::step][:num])
 if identifier=="yt-PL059E38785A0BB5F6":selected=categories[0][::max(1,len(categories[0])//8)][:8]
 for f in selected:sample.append((identifier,f))
def probe(row):
 identifier,f=row
 base={"source":identifier,"name":f["name"],"url":f["url"],"seconds":f["seconds"]}
 try:
  req=urllib.request.Request(f["url"],method="HEAD",headers={"User-Agent":"Mozilla/5.0","Accept":"video/mp4,*/*"})
  with urllib.request.urlopen(req,timeout=24) as resp:
   base.update({"http":resp.status,"mime":resp.headers.get("Content-Type",""),
     "head_reachable":resp.status in (200,206) and "video" in resp.headers.get("Content-Type","")})
 except Exception as exc:base.update({"head_reachable":False,"error":str(exc)[:175]})
 return base
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
 results=list(ex.map(probe,sample))
report={"checked":len(results),"http_reachable":sum(bool(x["head_reachable"]) for x in results),
 "by_source":{item:{"checked":sum(x["source"]==item for x in results),
                   "head_reachable":sum(x["source"]==item and x["head_reachable"] for x in results)}
              for item in by},
 "results":results,
 "note":"HTTP HEAD availability only; actual browser decoding, audio, streaming stability and usage rights not verified."}
(ROOT/"seasonal-link-check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
