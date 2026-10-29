"""Curate the three supplied holiday Archive collections for existing TV channels.

Never label trailers, fragments or unverified encodings as complete programmes.
Do not invent media links; derive from scanned original MP4 filenames and lengths.
"""
import json, pathlib, re, hashlib, collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
sources=json.loads((ROOT/"seasonal-archive-inventory.json").read_text())
catalogue=json.loads((ROOT/"source-library.json").read_text())
old={p.get("url") for p in catalogue.get("programmes",[])}
norm=lambda s:re.sub(r"[^a-z0-9]","",str(s or "").casefold())
title_index={norm(p.get("title")) for p in catalogue.get("programmes",[]) if p.get("title")}
episode_index=set()
for p in catalogue.get("programmes",[]):
 try:season=int(p.get("season_number"));episode=int(p.get("episode_number"))
 except (TypeError,ValueError):continue
 if season>=0 and episode>0:
  episode_index.add((norm(p.get("show") or p.get("series_id")),season,episode))
uk="ChristmasSpecials";us="christmas-episodes-and-specials";ads="yt-PL059E38785A0BB5F6"
def channel_of(source,name):
 n=name.casefold()
 if source==uk:
  if re.search(r"basil.brush|super.gran|rentaghost|crackerjack|emu.s|french.fields",n):return "GirlyPop"
  if re.search(r"star.wars.holiday|fresh.prince",n):return "Star Spangled TV"
  if re.search(r"father.ted|rab.c.nesbitt|gimme|the.fast.show|trigger.happy|catherine.tate|smack.the.pony|men.behaving|"
               r"harry.enfield|the.league.of.gentlemen|absolutely.fabulous|till.death.us|in.sickness.in.health",n):return "AAA"
  return "Off-Licence TV"
 if re.search(r"father.ted|miranda|vicar.of.dibley|outnumbered|mrs.?browns|mr.?bean|hepburn|green.wing|"
              r"league.of.gentlemen|man.down|mount.pleasant|agatha.raisin",n):return "Off-Licence TV"
 if re.search(r"icar!y|icarly|how.2.r0ck|how.to.rock|ravho|life.w.boys|"
              r"mentors|life.w.derek|sbtbell|saved.by.the.bell|city.guys",n):return "Dickleodeon"
 if re.search(r"boy.meets.world|the.raven|mk\+a|franklin.s.magic|that.girl|hang.time",n):return "Dizzy"
 if re.search(r"sabrina|full.house|fu!!_h0us3|melissa_joey|life.in.pieces|"
              r"baby.blues|aliens.in.the.family|sweet.valley.high|i.m.with.her",n):return "GirlyPop"
 if re.search(r"always.sunny|d3xt3r|dexter|two.br0ke|th3_0ffice|seinfeld|s3!nf3ld|"
              r"childrens.hospital|family.guy|superstore|the.league.of.gentlemen",n):return "AAA"
 if re.search(r"ncis|bones|psych|monk|coroner|law.and.order|charmed|"
              r"9-1-1|early.edition|picket.fenc|lie.2.me|body.of.proof|"
              r"crossing.lines|scandal|royal.pains|hawaii.five|st.elsewhere|"
              r"burn.notice|once.and.again",n):return "What"
 return "Star Spangled TV"
def title_of(name):
 t=re.sub(r"\.mp4$","",name,flags=re.I)
 t=re.sub(r"\b(1080p|720p|480p|HDTV|DVDRip|WEB[- .]?DL|x264|x265)\b","",t,flags=re.I)
 t=re.sub(r"[-_\.]+"," ",t)
 t=re.sub(r"\s+"," ",t).strip()
 return t[:150]
def episode_info(name):
 for rx in [r"[sS](\d{1,2})[\s._-]*[eE][pP]?(\d{1,3})\b",
            r"season[\W_]*(\d{1,2})[\W_]*episode[\W_]*(\d{1,3})",
            r"\b(\d{1,2})x(\d{1,3})\b"]:
  m=re.search(rx,name,re.I)
  if m:return int(m[1]),int(m[2])
 return None
def show_of(source,name,title):
 t=name.casefold()
 if source==uk:
  pattern=[
   (r"dad.s.army","Dad's Army"),(r"father.ted","Father Ted"),(r"miranda","Miranda"),
   (r"ghosts","Ghosts (UK)"),(r"vicar.of.dibley","The Vicar of Dibley"),
   (r"mrs.?brown","Mrs Brown's Boys"),(r"all[o0].?all[o0]","'Allo 'Allo!"),
   (r"still.?game","Still Game"),(r"father.ted","Father Ted"),(r"basil.brush","The Basil Brush Show"),
   (r"are.you.being.served","Are You Being Served?"),(r"rab.c.nesbitt","Rab C. Nesbitt"),
   (r"upstart.crow","Upstart Crow"),(r"terry.*june","Terry and June"),
   (r"only.fools","Only Fools and Horses"),(r"keeping.up.appearances","Keeping Up Appearances"),
   (r"absolutely.fabulous","Absolutely Fabulous"),(r"the.goes.wrong","The Goes Wrong Show")]
 else:
  pattern=[
   (r"3o.r0ck","30 Rock"),(r"8_simple|8simp","8 Simple Rules"),(r"friends|fr!3nds","Friends"),
   (r"full.house|fu!!_h0us3","Full House"),(r"community","Community"),
   (r"mr.?bean","Mr Bean"),(r"father.ted","Father Ted"),(r"sabrina","Sabrina the Teenage Witch"),
   (r"icar!y","iCarly"),(r"boy.meets.world","Boy Meets World"),(r"family.guy","Family Guy"),
   (r"psych","Psych"),(r"modern.family","Modern Family"),(r"the.0ffice|th3_0ffice","The Office (US)"),
   (r"always.sunny","It's Always Sunny in Philadelphia"),(r"that.7os.show","That '70s Show"),
   (r"two.br0ke","2 Broke Girls"),(r"n3w.gir!","New Girl"),(r"miranda","Miranda"),
   (r"vicar.of.dibley","The Vicar of Dibley"),(r"mrs.?brown","Mrs Brown's Boys"),
   (r"how.2.r0ck","How to Rock"),(r"saved.by.the.bell|sbtbell","Saved by the Bell"),
   (r"raven.?s.home|ravho","Raven's Home"),(r"life.w.derek","Life with Derek"),
   (r"gilmore|gi!m0re","Gilmore Girls"),(r"green.wing","Green Wing"),
   (r"buffy","Buffy the Vampire Slayer"),(r"monk","Monk"),
   (r"bones","Bones"),(r"ncis","NCIS"),(r"9-1-1","9-1-1"),
   (r"baby.blues","Baby Blues")]
 for regex,show in pattern:
  if re.search(regex,t,re.I):return show
 # For show/episode names, give the segment before the episode identifier priority.
 m=re.search(r"\b(?:s\d{1,2}e\d{1,3}|season[_\W]*\d+[_\W]*episode[_\W]*\d+|\d{1,2}x\d{1,3})\b",title,re.I)
 if m:
  before=title[:m.start()].strip(" ._-")
  if 3<len(before)<70:return before
 return title[:55]
def accept(source,f):
 name=f["name"]
 if not name.lower().endswith(".mp4") or f["seconds"]<150 or f["seconds"]>9500:return False
 if re.search(r"x265|hevc|non.?english|diff.language|^[-+].*sec|"
              r"\b1[_ /]3\b|\b2[_ /]3\b|\b3[_ /]3\b|"
              r"\bpart [123]\b|\bPt[. ]*[123]\b|"
              r"open(?:ing)? and clos(?:ing)?|"
              r"commercial.?intact|"
              r"see.other.for|same.as.ep|looks.the.same.as|"
              r"first.15.seconds|mkv.file|clip.only|clip -|VTS_|"
              r"\bpromo\b|\btrailer\b",name,re.I):return False
 if source==us and re.search(r"\bposs\b|\bi think\b|maybe|christmas.or.nye|"
                            r"part.1|part.2|part.3",name,re.I):return False
 return True
records=[];seen_urls=set();seen_keys=set();skipped=collections.Counter()
for item in sources["items"]:
 source=item["identifier"]
 if source==ads:continue
 for f in item["files"]:
  if not accept(source,f):
   skipped["not_a_complete_compatible_programme"]+=1;continue
  if f["url"] in old or f["url"] in seen_urls:
   skipped["exact_source_exists"]+=1;continue
  title=title_of(f["name"])
  if norm(title) in title_index:
   skipped["existing_title"]+=1;continue
  season_ep=episode_info(f["name"])
  show=show_of(source,f["name"],title)
  key=(norm(show),season_ep) if season_ep else (norm(title),None)
  if key in seen_keys:
   skipped["duplicate_episode_or_title_in_batch"]+=1;continue
  if season_ep and (norm(show),season_ep[0],season_ep[1]) in episode_index:
   skipped["existing_episode"]+=1;continue
  if season_ep and season_ep[1]>200:continue
  # Don't treat filename ambiguity as evidence of a verified episode mapping.
  typ="Episode" if season_ep else "Movie" if f["seconds"]>=3900 else "Special"
  ch=channel_of(source,f["name"])
  title=(show+" — S%02dE%02d — "%season_ep+title) if season_ep else title
  row={"id":"seasonal-"+hashlib.sha1(f["url"].encode()).hexdigest()[:15],
   "type":typ,"show":show,"title":title,"channel":ch,"url":f["url"],
   "duration_seconds":f["seconds"],"duration_evidence":"Internet Archive original MP4 file length",
   "archive_identifier":source,"filename":f["name"],
   "source_page":"https://archive.org/details/"+source,
   "seasonal_tags":["christmas"],
   "content_id":"archive-seasonal:"+hashlib.sha1(f["url"].encode()).hexdigest()[:15],
   "language_status":"unknown","broadcast_held":False,
   "library_origin":"christmas_archive_2026","verified_playback":False}
  if season_ep:row.update(season_number=season_ep[0],episode_number=season_ep[1])
  records.append(row);seen_urls.add(f["url"]);seen_keys.add(key)
records.sort(key=lambda p:(p["channel"],p["show"],p["title"]))
# Keep year-round schedule positions: only fill already-existing December
# continuity intervals, never move ordinary shows or dedicated film nights.
seasonal_js=(
 "/* Curated individual Christmas shows; original source URLs and measured durations. */\n"
 "(function(root){\n const db="+json.dumps({"version":"2026-10-29","programmes":records},
 ensure_ascii=False,separators=(",",":")).replace("</","<\\/")+";\n"
 " root.BOOTLEG_SEASONAL_MEDIA=db;\n"
 " const pool=root.BOOTLEG_CONTINUITY?.channels;\n"
 " if(!pool)return;\n"
 " for(const p of db.programmes){\n"
 "  if(p.duration_seconds>3000||p.duration_seconds<180)continue;\n"
 "  if(!pool[p.channel])pool[p.channel]=[];\n"
 "  if(!pool[p.channel].some(q=>q.url===p.url||q.content_id===p.content_id))pool[p.channel].push(p);\n"
 " }\n})(globalThis);\n")
(ROOT/"seasonal-programmes.js").write_text(seasonal_js,encoding="utf-8")
ad_files=next(x for x in sources["items"] if x["identifier"]==ads)["files"]
new_ads=[];used=set()
for f in ad_files:
 if not (5<=f["seconds"]<=61 and f["name"].lower().endswith(".mp4")):continue
 if re.search(r"budweiser|alcohol|beer|whiskey",f["name"],re.I):ch="Star Spangled TV"
 elif re.search(r"coca|m.?m|oreo|capt.n.crunch|peanuts|santa|mcdonald|kfc|kmart|toy|holiday",f["name"],re.I):ch="90s Toons"
 else:ch="Star Spangled TV"
 if f["url"] in used:continue
 used.add(f["url"])
 new_ads.append({"type":"Advert","show":"Classic Christmas Commercials",
  "title":title_of(f["name"]),"url":f["url"],"duration_seconds":f["seconds"],
  "duration_evidence":"Internet Archive original MP4 file length",
  "seasonal_tags":["christmas"],"content_id":"archive-xmas-ad:"+hashlib.sha1(f["url"].encode()).hexdigest()[:15],
  "channel":ch,"product_advert":True,"source_page":"https://archive.org/details/"+ads})
(ROOT/"seasonal-commercials.js").write_text("/* December-only classic commercials, same existing advert cap. */\n"
 "globalThis.BOOTLEG_SEASONAL_COMMERCIALS="+json.dumps({"version":"2026-10-29","adverts":new_ads},
 ensure_ascii=False,separators=(",",":")).replace("</","<\\/")+";\n",encoding="utf-8")
summary={"programmes":len(records),
 "per_channel":dict(collections.Counter(p["channel"] for p in records)),
 "per_collection":dict(collections.Counter(p["archive_identifier"] for p in records)),
 "programme_types":dict(collections.Counter(p["type"] for p in records)),
 "christmas_commercials":len(new_ads),
 "ad_channels":dict(collections.Counter(p["channel"] for p in new_ads)),
 "skipped":dict(skipped),
 "examples":{ch:[p["title"] for p in records if p["channel"]==ch][:13]
   for ch in sorted({p["channel"] for p in records})},
 "note":"Archive filenames and durations are verified metadata; not full playback or rights verification. Content is only eligible for December."}
(ROOT/"seasonal-curation-report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(summary,ensure_ascii=False,indent=2))
