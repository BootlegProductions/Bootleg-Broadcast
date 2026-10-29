"""Create restrained ident pools from measured original Archive MP4 clips.

No long montages, programme announcements or no-sound versions.
Each source is selected by its exact measured Archive filename.
"""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'archive-nick-boomerang-review.json').read_text())
sources={p["identifier"]:{x["name"]:x for x in p["short_clips"]} for p in inventory["items"]}
nick="nick-ids-comp_202202";boomer="yt-OldMcBarney"
picks={
 "Dickleodeon":[
  (nick,"NICKELODEON GOLD 10 Image Piece - Short.mp4"),
  (nick,"NICKELODEON SILVER 10 Image Piece - Short.mp4"),
  (nick,"Nick Games (2002, highest quality).mp4"),
  (nick,"Nick Rebrand IDs.mp4"),
  (nick,"Nickelodeon - Orange Soda ID (Theatrical HD).mp4"),
  (nick,"Nickelodeon Bumper - Barbershop Quartet (2013) (480p SD).mp4"),
  (nick,"Nickelodeon Bumper - Nick is Everyday 3-D (HQ).mp4"),
  (nick,"Nickelodeon Bumper - Time Machine (HQ_Rare).mp4"),
  (nick,"Nickelodeon ID - Toaster.mp4"),
  (nick,"Nickelodeon Orange You Glad Bumper.mp4"),
  (nick,"Nickelodeon Skateboard Ident.mp4"),
  (nick,"Nicktoons 'Blob' ID (1993).mp4"),
  (nick,"Nickelodeon - Seasonal Ident - BEACH WAVE.mp4"),
  (nick,"Nickelodeon - Seasonal Ident - SANTA SACK.mp4"),
  (nick,"Nickelodeon - Seasonal Ident - PRESENTS.mp4"),
  (nick,"Nickelodeon - Seasonal Ident - EGGY EASTER.mp4"),
  (nick,"Nickelodeon - Seasonal Ident - VALENTINE BALLOONS.mp4"),
 ],
 "90s Toons":[
  (boomer,"Boomerang 50 Years of the Flintstones Bumper.mp4"),
  (boomer,"Boomerang Atom Ant Bumper.mp4"),
  (boomer,"Boomerang Paddington Bear Bumper #2.mp4"),
  (boomer,"Boomerang Paddington Bear Bumper.mp4"),
  (boomer,"Cartoon Network Boomerang 1976 Bumper.mp4"),
 ],
 "Cartoons Cartoons":[
  (boomer,"CN Bumper - Dexter getting dizzy.mp4"),
  (boomer,"CN Logo Riding A Car.mp4"),
  (boomer,"CN Toilet Bumper.mp4"),
  (boomer,"Cartoon Network Baboon Bumper.mp4"),
  (boomer,"Cartoon Network Billy & Mandy Bumper.mp4"),
  (boomer,"Cartoon Network Captain Planet Bumper (Back to the Show).mp4"),
  (boomer,"Cartoon Network Courage Bumper.mp4"),
  (boomer,"Cartoon Network Cow & Chicken Bumper.mp4"),
  (boomer,"Cartoon Network Coyote Bumper.mp4"),
  (boomer,"Cartoon Network Dexter's Laboratory Bumpers #3.mp4"),
  (boomer,"Cartoon Network Dexter's Laboratory Bumpers #4.mp4"),
  (boomer,"Cartoon Network Ed, Edd & Eddy Bumper.mp4"),
  (boomer,"Cartoon Network Kids Next Door Bumper.mp4"),
  (boomer,"Cartoon Network Logo Chase.mp4"),
  (boomer,"Cartoon Network Old Logo Bumpers.mp4"),
  (boomer,"Cartoon Network Old Logo Station ID #2.mp4"),
  (boomer,"Cartoon Network Old Logo Station ID.mp4"),
  (boomer,"Cartoon Network Scooby-Doo Masks Bumper.mp4"),
  (boomer,"Cartoon Network Space Ghost Bumper.mp4"),
  (boomer,"Old Cartoon Network Jester Bumper.mp4"),
  (boomer,"Old Cartoon Network Soup Bumper.mp4"),
  (boomer,"Cartoon Network Christmas Party Bumper.mp4"),
 ],
}
tags={
 "BEACH WAVE":list(range(6,9)),
 "SANTA SACK":[12],"PRESENTS":[12],"EGGY EASTER":[3,4],
 "VALENTINE BALLOONS":[2],"Christmas Party":[12],
}
rows={};seen=set()
for channel,choices in picks.items():
 rows[channel]=[]
 for identifier,name in choices:
  f=sources.get(identifier,{}).get(name)
  if f is None:raise ValueError("Archive file not present: "+identifier+"/"+name)
  if not 3<=f["seconds"]<=22:raise ValueError("Not a short ident: "+name+" "+str(f["seconds"]))
  if f["url"] in seen:raise ValueError("Duplicate ident URL: "+f["url"])
  seen.add(f["url"])
  months=next((m for tag,m in tags.items() if tag.lower() in name.lower()),None)
  rows[channel].append({"type":"Ident","show":channel,"title":name.removesuffix(".mp4"),
   "url":f["url"],"duration_seconds":f["seconds"],"source_identifier":identifier,
   "source_page":"https://archive.org/details/"+identifier,
   "months":months,"duration_evidence":"Internet Archive original MP4 metadata length",
   "link_status":"archive-metadata-listed; playback not yet confirmed"})
all_count=sum(map(len,rows.values()))
out="/* Measured short station ident pool. At most one ident per channel per hour. */\n"+\
 "globalThis.BOOTLEG_IDENT_POOLS="+json.dumps({"version":"2026-10-29","channels":rows},
  ensure_ascii=False,separators=(",",":")).replace("</","<\\/")+";\n"
(ROOT/'channel-idents.js').write_text(out,encoding="utf-8")
report={"ident_count":all_count,"channels":{c:{"count":len(items),"regular":sum(not v["months"] for v in items),
 "seasonal":[{"title":v["title"],"months":v["months"]} for v in items if v["months"]]} for c,items in rows.items()},
 "sources":["https://archive.org/details/"+i for i in (nick,boomer)],
 "note":"Only exact original MP4 files with measured runtime 3–22 seconds. No compilations. Requires direct playback check."}
(ROOT/'channel-ident-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2,ensure_ascii=False))
