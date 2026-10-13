"""Check whole-ad placement and programme identities/timing against the previous release."""
from pathlib import Path
import json,calendar,collections,zipfile,contextlib
R=Path(__file__).resolve().parents[1];read=lambda f:json.loads((R/f).read_text());pool=read('nostalgic-american-adverts.json')['adverts'];breaks=read('channel-breaks.json')['channels'];urls={p['url'] for p in pool};errors=[];actual=collections.Counter();days=0;interval_max=0;changes=0
oldzip=R.parent/'channel-ad-input/Bootleg-Broadcast-v0.36.3-GitHub-Pages.zip'
with (zipfile.ZipFile(oldzip) if oldzip.exists() else contextlib.nullcontext(None)) as old:
 for month in range(1,13):
  name='schedules/'+calendar.month_name[month].lower()+'.json';d=read(name);prior=json.loads(old.read(name)) if old else d
  for day,before in zip(d['weeks'][0]['week'],prior['weeks'][0]['week']):
   for ch,oldch in zip(day['channels'],before['channels']):
    days+=1
    programmes=lambda entries:[{k:v for k,v in p.items() if k!='title'} for p in entries if p['type'] not in ['Break','Filler']]
    if programmes(ch['playlist'])!=programmes(oldch['playlist']):changes+=1;errors.append('Programme change: '+name+'/'+day['date']+'/'+ch['name'])
    for p in ch['playlist']:
     if p.get('presentation'):interval_max=max(interval_max,p['broadcast_end_seconds']-p['broadcast_start_seconds'])
     if p['type']!='Break':continue
     t=p['broadcast_start_seconds']
     for i in p['break_sequence']:
      clip=breaks[ch['name']]['ident'] if i==-1 else breaks[ch['name']]['adverts'][i];finish=min(p['broadcast_end_seconds'],t+clip['duration_seconds'])
      if i!=-1 and finish-t+.02<clip['duration_seconds']:errors.append('Cut advert: '+clip['title'])
      if clip['url'] in urls:
       actual[clip['url']]+=1
       if 'halloween' in clip.get('seasonal_tags',[]) and month!=10:errors.append('Halloween advert outside October')
       if ch['name']=='Off-Licence TV':errors.append('American advert in UK pool')
      t=finish
for p in pool:
 if p['url'] not in actual:errors.append('New advert never actually airs: '+p['title'])
 if p['codec_check']['video']!='h264' or p['codec_check']['audio']!='aac' or p['full_file_check']['decode']!='passed':errors.append('Unchecked media: '+p['title'])
 if '.ia.mp4' in p['url'] or not p['url'].endswith('.mp4') or '/Commercials.zip/' in p['url']:errors.append('Unsuitable direct link')
result={'version':'0.36.4','status':'passed' if not errors else 'failed','fully_decoded_new_adverts':len(pool),'new_adverts_actually_scheduled':len(actual),'channel_days':days,'changed_programme_days':changes,'comparison_scope':'Programme identity, source, episode order and timing; display-title cleanup is permitted','previous_release_compared':oldzip.exists(),'maximum_remaining_interval_seconds':round(interval_max,3),'new_ad_screenings':sum(actual.values()),'errors':errors,'scope':'Exact MP4/runtime/codec/full decode evidence, complete advert placement and unchanged programme lineup across 2026. Uploader English declaration is not an independent full listening review.'};(R/'advert-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'errors':errors[:12]},indent=2));raise SystemExit(bool(errors))
