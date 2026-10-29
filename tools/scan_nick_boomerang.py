"""Inspect supplied Nick/Boomerang items and identify the original uploader's other uploads.

Metadata inventory only; do not add long montages as station idents.
"""
import json,re,urllib.parse,urllib.request,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
HEADERS={"User-Agent":"BootlegBroadcast/1.0 Archive metadata review"}
ITEMS=("nick-ids-comp_202202","yt-OldMcBarney")
VIDEO=re.compile(r'\.(?:mp4|m4v|webm)$',re.I)
def fetch(url,timeout=30):
 request=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(request,timeout=timeout) as resp:
  return json.loads(resp.read().decode("utf-8"))
def length(f):
 try:return round(float(f.get("length") or f.get("duration") or 0),3)
 except (TypeError,ValueError):return 0
def original(file):
 n=file.get("name","")
 return isinstance(n,str) and VIDEO.search(n) and not n.lower().endswith(".ia.mp4")
def direct(ident,name):
 return "https://archive.org/download/"+urllib.parse.quote(ident,safe="")+"/"+urllib.parse.quote(name,safe="/")
def describe(ident):
 data=fetch("https://archive.org/metadata/"+urllib.parse.quote(ident))
 meta=data.get("metadata") or {}
 files=data.get("files") or []
 vids=[f for f in files if original(f)]
 rows=[]
 for f in vids:
  name=f["name"];duration=length(f);size=int(f.get("size") or 0)
  rows.append(dict(name=name,seconds=duration,bytes=size,format=f.get("format"),source=f.get("source"),
    url=direct(ident,name)))
 shorts=[v for v in rows if 3<=v["seconds"]<=35 and v["name"].lower().endswith(".mp4")]
 long=[v for v in rows if 600<=v["seconds"]<=13000 and v["name"].lower().endswith(".mp4")]
 metadata={k:meta.get(k) for k in ("title","creator","uploader","date","description","licenseurl","publicdate")}
 return {"identifier":ident,"metadata":metadata,"all_video_count":len(rows),
   "short_clips":shorts[:500],"short_count":len(shorts),
   "long_videos":long[:150],"long_count":len(long),
   "other_videos": [v for v in rows if v not in shorts and v not in long][:65],
   "all_filenames": [v["name"] for v in rows[:550]],
   "file_examples":rows[:100]}
def user_uploads(md):
 # Archive's "uploader" can be an email and is often more reliable than the
 # item's visible creator. Only search uploader if present; never infer handles.
 uploader=md.get("uploader")
 if not isinstance(uploader,str) or not uploader:return {"uploader":uploader,"results":[],"error":"No uploader field."}
 q='uploader:"'+uploader.replace('"','')+'"'
 url="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode({"q":q,"fl[]":"identifier,title,mediatype,year","rows":100,"page":1,"output":"json"})
 try:
  result=fetch(url,timeout=30)
  docs=result.get("response",{}).get("docs",[])
  return {"uploader":uploader,"reported_total":result.get("response",{}).get("numFound"),
  "results":[{"identifier":p.get("identifier"),"title":p.get("title"),"mediatype":p.get("mediatype")} for p in docs if p.get("identifier")]}
 except Exception as e:return {"uploader":uploader,"results":[],"error":str(e)[:200]}
out={"items":[],"errors":[]}
for ident in ITEMS:
 try:
  row=describe(ident);row["uploader_items"]=user_uploads(row["metadata"]) if ident==ITEMS[0] else None
  out["items"].append(row)
 except Exception as e:out["errors"].append({"identifier":ident,"error":str(e)[:250]})
path=ROOT/"archive-nick-boomerang-review.json"
path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({"items":[{"identifier":x["identifier"],"title":x["metadata"]["title"],"uploader":x["metadata"]["uploader"],
 "videos":x["all_video_count"],"shorts":x["short_count"],"long":x["long_count"],
 "uploads":x["uploader_items"] and len(x["uploader_items"]["results"])} for x in out["items"]],"errors":out["errors"]},indent=2))
