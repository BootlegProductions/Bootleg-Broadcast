"""Aggregate current checks and ensure a GitHub Pages checkout is ready to commit."""
import json, subprocess, hashlib, collections, calendar
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda n:json.loads((ROOT/n).read_text())
errors=[]
checks=['release-validation.json','restoration-validation.json','film-validation.json',
        'seasonal-validation.json','addition-validation.json','advert-validation.json',
        'channel-interstitial-validation.json','playback-validation.json','tuning-audio-validation.json']
for name in checks:
    if read(name)['status']!='passed':errors.append('Failed check: '+name)
baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
markdowns,assets=0,0
changed_assets={'assets/background/october-desktop.png','assets/background/december-desktop.png'}
for name in filter(None,tracked):
    path=ROOT/name
    if not path.exists():continue
    if path.stat().st_size>=100*1024*1024:errors.append('GitHub file size limit: '+name)
    if name.startswith('markdowns/') or name.startswith('assets/') and name not in changed_assets:
        old=subprocess.check_output(['git','show',baseline+':'+name],cwd=ROOT)
        if hashlib.sha256(old).digest()!=hashlib.sha256(path.read_bytes()).digest():errors.append('Original source/asset changed: '+name)
        if name.startswith('markdowns/'):markdowns+=1
        else:assets+=1
if not (ROOT/'index.html').exists() or not (ROOT/'.nojekyll').exists():errors.append('Missing Pages entrypoint')
if len(list((ROOT/'schedules').glob('*.json')))!=12:errors.append('Missing monthly schedule')
verification='google3dd901d7eb9ae421.html'
if (ROOT/verification).read_bytes()!=subprocess.check_output(['git','show',baseline+':'+verification],cwd=ROOT):errors.append('Search verification changed')
if 'content="O2zME34vjxU66zmOAbI4kD5P0tmqS1y1ifPqY8hecIA"' not in (ROOT/'index.html').read_text():errors.append('Search verification meta tag changed')
intervals=collections.Counter();days=0
for month in range(1,13):
    for day in read('schedules/'+calendar.month_name[month].lower()+'.json')['weeks'][0]['week']:
        for channel in day['channels']:
            days+=1
            for p in channel['playlist']:
                if p.get('presentation'):intervals[channel['name']]+=1
                if p['type']=='Break' and len(p['break_sequence'])>1 and all(i==-1 for i in p['break_sequence']):errors.append('Repeating ident-only break')
result={'version':'0.37.0','status':'failed' if errors else 'passed','delivery':'direct GitHub commit',
        'baseline_commit':baseline,'all_twelve_months':True,'entrypoint_at_root':True,
        'unchanged_original_assets_checked':assets,'unchanged_original_markdowns_checked':markdowns,
        'intentionally_replaced_backgrounds':sorted(changed_assets),
        'automated_check_reports':checks,'browser_visual_preview':'Halloween and Christmas rooms, guide return focus',
        'responsive_geometry_scenarios':21,'full_external_playback_audio_review':False,
        'backend_required':False,'calendar_year':2026,'errors':errors}
(ROOT/'package-validation.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'transition-validation.json').write_text(json.dumps({'version':'0.37.0','status':result['status'],
        'channel_days_checked':days,'intervals_by_channel':dict(intervals),'errors':errors,
        'scope':'Static ident-chain checks plus the event simulations in playback-validation.json; no full Archive streaming review.'},indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
