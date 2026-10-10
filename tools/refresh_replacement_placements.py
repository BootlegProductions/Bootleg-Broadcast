"""Keep source-library month/day filters accurate for the restored collections."""
import json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ids={'h2o-just-add-water-season-one','h2o-just-add-water-seasontwo','h2o-just-add-water-seasonthree','evadubbed'};cat=json.loads((ROOT/'source-library.json').read_text());rows=[p for p in cat['programmes'] if p.get('archive_identifier') in ids];wanted={p['url'] for p in rows};dates=collections.defaultdict(lambda:collections.defaultdict(set));month_numbers={m:i+1 for i,m in enumerate(['january','february','march','april','may','june','july','august','september','october','november','december'])}
for file in (ROOT/'schedules').glob('*.json'):
 for day in json.loads(file.read_text())['weeks'][0]['week']:
  for ch in day['channels']:
   for p in ch['playlist']:
    if p.get('url') in wanted:dates[p['url']][file.stem].add(int(day['date']))
for p in rows:
 p['scheduled_dates']={m:sorted(ds) for m,ds in dates[p['url']].items()};p['schedule_months']=sorted(month_numbers[m] for m in dates[p['url']])
assert len(rows)==104 and all(dates[p['url']] for p in rows)
(ROOT/'source-library.json').write_text(json.dumps(cat,ensure_ascii=False,separators=(',',':')));print('All 104 restored episodes appear in the compiled calendar; catalogue date/month filters refreshed.')
