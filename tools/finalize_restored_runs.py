"""Finish editorial assignments after restore_schedule_runs.py."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda f:json.loads((ROOT/f).read_text())
c=read('editorial-lineups.json');d=read('editorial-series.json');r=read('restoration-report.json');cat=read('source-library.json')
new='restored-utopia'
if new in d:
 d['utopia']['max_episode_seconds']=4500;d['utopia']['shows']=list(dict.fromkeys(d['utopia']['shows']+d[new]['shows']));del d[new]
 for run in c['series_runs'].values():run['series']=['utopia' if k==new else k for k in run['series']]
 r['restored']['utopia']=r['restored'].pop(new);r['restored']['utopia']['name']='Utopia (UK)'
 for p in cat['programmes']:
  if p.get('series_id')==new:p.update(series_id='utopia',source_show='Utopia',show='Utopia (UK)',series_label='Utopia (UK)')
def extend(ch,at,end,eps):
 slots=c['channels'][ch];s=next(s for s in slots if s['at']==at);c['channels'][ch]=[s for s in slots if not at<s['at']<end];s.update(end=end,episodes=eps)
extend('Off-Licence TV','00:00','02:00',2)
if 'beinghuman' not in c['series_runs']['off-licence-tv-0000']['series']:c['series_runs']['off-licence-tv-0000']['series'].insert(1,'beinghuman')
extend('Star Spangled TV','15:00','17:00',3);extend('Star Spangled TV','22:00','24:00',2)
if 'restored-louis-theroux' in c['series_runs']['what-1800']['series']:c['series_runs']['what-1800']['series'].remove('restored-louis-theroux')
s=next(s for s in c['channels']['What'] if s['at']=='14:00');s.update(series='@run:what-1400',episodes=2,block='Documentary features — complete series runs',end='16:00');s.pop('fallback',None);c['channels']['What']=[s for s in c['channels']['What'] if s['at']!='15:00'];c['series_runs']['what-1400']={'name':s['block'],'series':['restored-louis-theroux','nova'],'repeat_after_full_cycle':True}
for at,key in [('06:30','restored-sonny-boy-english-japanese'),('17:00','restored-vandread')]:
 if key not in d:continue
 for run in c['series_runs'].values():
  if key in run['series']:run['series'].remove(key)
 slot=next(s for s in c['channels']['Japanime'] if s['at']==at);rid='japanime-'+at.replace(':','');c['series_runs'][rid]={'name':'Anime stories — complete series runs','series':[slot['series'],key],'repeat_after_full_cycle':True};slot.update(series='@run:'+rid,block='Anime stories — complete series runs');slot.pop('fallback',None)
for k in r['restored']:
 if k.startswith('restored-') or k in ['utopia','office-us','buffy']:d[k]['require_mapped_episode']=True
 n=d[k]['name'];n=re.sub(r'\s*\((?:English \+ Japanese|Japanese \+ English Subs)\)','',n);n=n.replace('Jormungand Complete Eng Sub 720p Season 1-2','Jormungand');d[k]['name']=n;r['restored'][k]['name']=n
 for p in cat['programmes']:
  if p.get('series_id')==k and p.get('restoration_evidence'):
   p['show']=n;p['series_label']=n
   if n not in d[k]['shows']:d[k]['shows'].append(n)
for fn,x in [('editorial-lineups.json',c),('editorial-series.json',d),('source-library.json',cat),('restoration-report.json',r)]: (ROOT/fn).write_text(json.dumps(x,ensure_ascii=False,separators=(',',':')))
