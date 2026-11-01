"""Validate October/December daily movie programming and preserved morning blocks.
Outputs counts by channel and any dates with fewer than two complete features.
"""
import pathlib,json,collections,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
READ=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
cinema=READ('holiday-cinema-windows.json')
bookings=READ('holiday-film-appointments.json')['film_windows']
summary={'status':'passed','year':2026,'target_features_per_channel_day':2,
         'dates':0,'channel_days':0,'feature_airings':0,'actual_movie_airings':0,
         'feature_length_specials':0,'days_with_two_or_more':0,
         'days_with_one':0,'days_with_none':0,'by_channel':{},
         'low_coverage':[],'holiday_film_appointments':len(bookings),
         'sample_film_bookings':bookings[:18]}
for month,label in [(10,'october'),(12,'december')]:
 monthData=READ('schedules/'+label+'.json')
 days=monthData['weeks'][0]['week']
 assert len(days)==(31 if month==10 else 31),(label,len(days))
 summary['dates']+=len(days)
 for d in days:
  assert len(d['channels'])==len(cinema['channels']),d['date']
  for ch in d['channels']:
   name=ch['name'];all_slots=ch['playlist']
   selected=[p for p in all_slots if
       (p.get('type')=='Movie' and float(p.get('duration_seconds',0))>=1800)
       or (p.get('type')=='Special' and 'film' in p.get('block','').lower()
           and float(p.get('duration_seconds',0))>=2400)]
   movies=[p for p in selected if p['type']=='Movie']
   specials=[p for p in selected if p['type']=='Special']
   names=[p['title'] for p in selected]
   row=summary['by_channel'].setdefault(name,{'days':0,'movies':0,'features':0,'feature_specials':0,
                   'two_or_more':0,'one':0,'none':0,'unique_movies':set(),'sample':[]})
   row['days']+=1;row['movies']+=len(movies)
   row['features']+=len(selected);row['feature_specials']+=len(specials)
   row['unique_movies'].update((p.get('url') or '') for p in movies)
   if len(row['sample'])<7:row['sample'].append({'date':label+' '+d['date'],'titles':names})
   summary['channel_days']+=1
   summary['feature_airings']+=len(selected)
   summary['actual_movie_airings']+=len(movies)
   summary['feature_length_specials']+=len(specials)
   tier='two_or_more' if len(selected)>=2 else 'one' if len(selected)==1 else 'none'
   row[tier]+=1
   summary[{'two_or_more':'days_with_two_or_more','one':'days_with_one','none':'days_with_none'}[tier]]+=1
   if len(selected)<2:
    summary['low_coverage'].append({'date':label+' '+d['date'],'channel':name,
            'count':len(selected),'feature_titles':names})
   # Fixed breakfast shows and the overnight fireplace are not moved.
   if name=='90s Toons':
    breakfast=[p for p in all_slots if 7*3600<=p['broadcast_start_seconds']<10*3600
               and p['type']=='Episode']
    assert len(breakfast)>=5,'Missing 90s Toons morning action block '+label+' '+d['date']
   if month==12:
    fireplaces=[p for p in all_slots if p.get('loop') and
                'fireplace' in p.get('block','').lower()]
    assert fireplaces,'Missing Christmas overnight fireplace '+name+' '+d['date']
   last=-1
   for p in all_slots:
    assert p['broadcast_end_seconds']>p['broadcast_start_seconds'],name
    assert p['broadcast_start_seconds']>=last-0.05,name
    last=p['broadcast_end_seconds']
for ch,v in summary['by_channel'].items():
 v['unique_movies']=len(v['unique_movies'])
summary['coverage_percent']=round(100*summary['days_with_two_or_more']/summary['channel_days'],1)
summary['low_coverage']=summary['low_coverage'][:90]
print(json.dumps({'preflight_coverage':{
 'channel_days':summary['channel_days'],
 'days_without_feature':summary['days_with_none'],
 'days_with_one':summary['days_with_one'],
 'days_with_two_or_more':summary['days_with_two_or_more'],
 'actual_movies':summary['actual_movie_airings'],
 'specials':summary['feature_length_specials'],
 'per_channel':{ch:{k:v[k] for k in ['movies','features','two_or_more','one','none','unique_movies']}
                 for ch,v in summary['by_channel'].items()},
 'missing_first_25':summary['low_coverage'][:25]}},ensure_ascii=False,indent=2))
# Never silently pass a channel that lost all holiday movie days.
assert summary['days_with_none']==0,'At least one feature missing on some channel-days'
assert summary['days_with_two_or_more']>=round(summary['channel_days']*.8),'Most days should feature two films'
(ROOT/'holiday-cinema-validation.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':summary['status'],'days':summary['channel_days'],
 'features':summary['feature_airings'],'movies':summary['actual_movie_airings'],
 'specials':summary['feature_length_specials'],'two_films_days':summary['days_with_two_or_more'],
 'coverage_percent':summary['coverage_percent'],'low_coverage':summary['low_coverage'][:18],
 'by_channel':{ch:{k:v[k] for k in ['movies','features','two_or_more','one','none','unique_movies']}
                 for ch,v in summary['by_channel'].items()}},indent=2,ensure_ascii=False))
