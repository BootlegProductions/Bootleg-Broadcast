"""Inventory user-supplied seasonal Archive collections at exact MP4-file level.

No guessing based on item titles; retain original filenames, measured lengths,
and direct links. Exclude derived .ia.mp4 copies and non-video metadata files.
"""
import json, pathlib, re, urllib.parse, urllib.request, collections, traceback
ROOT=pathlib.Path(__file__).resolve().parents[1]
ITEMS=["yt-PL059E38785A0BB5F6","christmas-episodes-and-specials","ChristmasSpecials"]
rx=re.compile(r'\.(mp4|m4v|webm)$',re.I)
def metadata(item):
 req=urllib.request.Request("https://archive.org/metadata/"+urllib.parse.quote(item,safe=""),headers={"User-Agent":"Mozilla/5.0 BootlegBroadcast source auditor"})
 with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode("utf-8"))
def duration(f):
 try:return round(float(f.get("length") or f.get("duration") or 0),3)
 except (TypeError,ValueError):return 0
def direct(item,n):
 return "https://archive.org/download/"+urllib.parse.quote(item,safe="")+"/"+urllib.parse.quote(n,safe="/")
out={"items":[],"errors":[],"summary":{}}
for item in ITEMS:
 try:
  info=metadata(item);meta=info.get("metadata",{})
  raw=[f for f in info.get("files",[]) if isinstance(f.get("name"),str)]
  videos=[]
  for f in raw:
   name=f["name"];source=str(f.get("source") or "")
   if not rx.search(name) or name.lower().endswith(".ia.mp4"):continue
   videos.append({"name":name,"url":direct(item,name),"seconds":duration(f),"size":int(f.get("size") or 0),
      "format":f.get("format"),"source":source,
      "archive_item":item,"has_runtime":duration(f)>0})
  exacts=sorted(videos,key=lambda a:a["name"].lower())
  stats={"original_mp4":sum(x["name"].lower().endswith(".mp4") for x in exacts),
   "unknown_runtime":sum(not x["seconds"] for x in exacts),
   "commercial_3_to_90s":sum(3<=x["seconds"]<=90 for x in exacts),
   "short_91_to_900s":sum(90<x["seconds"]<=900 for x in exacts),
   "episodes_15_to_65min":sum(900<x["seconds"]<=3900 for x in exacts),
   "features_over_65min":sum(x["seconds"]>3900 for x in exacts)}
  out["items"].append({"identifier":item,"title":meta.get("title"),"creator":meta.get("creator"),
     "description":str(meta.get("description") or "")[:1200],
     "files":exacts,"stats":stats,"file_count":len(raw)})
  out["summary"][item]={"title":meta.get("title"),**stats,"video_count":len(exacts),
     "sample": [{"name":v["name"],"seconds":v["seconds"]} for v in exacts[:12]]}
 except Exception as exc:out["errors"].append({"item":item,"error":str(exc)[:350]})
(ROOT/"seasonal-archive-inventory.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"summary":out["summary"],"errors":out["errors"]},indent=2,ensure_ascii=False))
