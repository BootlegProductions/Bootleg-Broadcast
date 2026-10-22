"""Check channel routing, hard duration cap and actual seasonal interstitial airtime."""
from pathlib import Path
import json,calendar,collections,urllib.parse
R=Path(__file__).resolve().parents[1];read=lambda f:json.loads((R/f).read_text());clips=read('channel-interstitials.json')['clips'];byurl={p['url']:p for p in clips};breaks=read('channel-breaks.json')['channels'];errors=[];actual=collections.Counter();days=0
for ch,group in breaks.items():
 for p in group['adverts']:
  if p['duration_seconds']>60:errors.append('Over one minute: '+ch+' '+p['title'])
  if p['url'] in byurl and byurl[p['url']]['channel']!=ch:errors.append('Wrong channel in pool: '+p['title'])
for month in range(1,13):
 for day in read('schedules/'+calendar.month_name[month].lower()+'.json')['weeks'][0]['week']:
  for ch in day['channels']:
   days+=1
   for p in ch['playlist']:
    if p['type']!='Break':continue
    for i in p['break_sequence']:
     if i==-1:continue
     clip=breaks[ch['name']]['adverts'][i];original=byurl.get(clip['url'])
     if not original:continue
     actual[clip['url']]+=1
     if ch['name']!=original['channel']:errors.append('Wrong actual channel: '+clip['title'])
     if 'christmas' in clip.get('holiday_events',[]) and month!=12:errors.append('Christmas advert outside December')
for p in clips:
 if p['url'] not in actual:errors.append('Never actually airs: '+p['title'])
 if not p['url'].endswith('.mp4') or '.ia.mp4' in p['url'] or '/Commercials.zip/' in p['url']:errors.append('Unsuitable file URL')
 if p['full_file_check']['decode']!='passed' or p['codec_check']['video']!='h264' or p['codec_check']['audio']!='aac':errors.append('Missing file verification')
 if p['duration_seconds']>60:errors.append('Long curated source')
result={'version':'0.37.0','status':'passed' if not errors else 'failed','curated_clips':len(clips),'actually_scheduled':len(actual),'by_channel':dict(collections.Counter(p['channel'] for p in clips)),'channel_days':days,'maximum_compiled_advert_seconds':max(p['duration_seconds'] for c in breaks.values() for p in c['adverts']),'errors':errors,'scope':'Complete static calendar, exact source/routing/seasonal placement and measured media checks. No full independent listening or browser streaming review.'};(R/'channel-interstitial-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'errors':errors[:15]},indent=2));raise SystemExit(bool(errors))
