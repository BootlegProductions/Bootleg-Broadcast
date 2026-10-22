"""Check dated editorial appointments, overnight boundaries and local site links."""
import json, calendar, collections, urllib.parse, re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((ROOT / path).read_text())
plan = read('seasonal-programming.json')
catalogue = read('source-library.json')['programmes']
by_url = {p['url']: p for p in catalogue}
errors, actual, summaries = [], {}, {}
fireplace_count = 0
for month in range(1, 13):
    data = read('schedules/' + calendar.month_name[month].lower() + '.json')
    unique, movies, tagged = collections.defaultdict(set), [], collections.Counter()
    for day in data['weeks'][0]['week']:
        date = f'{data["schedule_year"]}-{month:02d}-{int(day["date"]):02d}'
        for channel in day['channels']:
            name = channel['name']
            programmes = channel['playlist']
            actual[date, name] = programmes
            fires = [p for p in programmes if p['type'] == 'Filler' and p.get('loop')]
            if month == 12:
                if len(fires) != 1:
                    errors.append(f'{date} {name}: expected one fireplace appointment')
                for p in fires:
                    fireplace_count += 1
                    expected = plan['fireplaces'].get(name, plan['fireplaces']['default'])
                    if p['url'] != expected['url'] or p['broadcast_start_seconds'] != 4*3600 or p['broadcast_end_seconds'] != 5*3600:
                        errors.append(f'{date} {name}: incorrect fireplace source/time')
            elif fires:
                errors.append(f'{date} {name}: fireplace outside December')
            for p in programmes:
                if p['type'] in ['Break', 'Filler', 'Advert', 'Ident']:
                    continue
                unique[name].add(p['url'])
                if set(p.get('seasonal_tags', [])) & {'winter', 'christmas', 'halloween'}:
                    tagged[name] += 1
                if p['type'] == 'Movie':
                    movies.append({'date': day['date'], 'channel': name, 'title': p['title']})
    if month in [10, 12]:
        summaries[calendar.month_name[month].lower()] = {
            'days': len(data['weeks'][0]['week']),
            'source': 'Actual compiled timetable; not a historic rotation estimate',
            'distinct_scheduled_sources': {ch: len(urls) for ch, urls in unique.items()},
            'seasonally_tagged_screenings': dict(tagged),
            'featured_movies': movies,
        }

for appointment in plan['appointments']:
    rows = actual[appointment['date'], appointment['channel']]
    h, m = map(int, appointment['at'].split(':'))
    start = h*3600 + m*60
    for url in appointment['urls']:
        if not any(p.get('url') == url and p['broadcast_start_seconds'] >= start and p['block'] == appointment['block'] for p in rows):
            errors.append('Missing authored seasonal source: ' + str(appointment))
        if '.ia.mp4' in url or not url.endswith('.mp4'):
            errors.append('Invalid new seasonal source: ' + url)
        if by_url[url].get('broadcast_held'):
            errors.append('Held source in seasonal plan: ' + url)

for p in catalogue:
    if p.get('archive_identifier') == 'adv-films-complete-collection':
        folder = re.sub(r'\s*\(ADV Films\)', '', p['filename'].split('/')[0], flags=re.I)
        if p['show'] != folder or not p.get('episode_mapping_required') or p.get('episode_number') is not None:
            errors.append('Mixed DVD collection is incorrectly labelled: ' + p['url'])

pools = read('broadcast-pools.json')['channels']
series_sizes = {}
for channel, key, minimum in [('Cartoons Cartoons', 'powerpuff', 78), ('AAA', 'simpsons', 400)]:
    episodes = [p for p in pools[channel] if p.get('series_id') == key]
    identities = [(p.get('season_number'), p.get('episode_number')) for p in episodes]
    series_sizes[key] = len(episodes)
    if len(episodes) < minimum or any(e is None for s, e in identities) or len(set(identities)) != len(identities):
        errors.append(key + ': missing episode mapping or duplicate copies in the regular run')

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.paths = []
    def handle_starttag(self, tag, attrs):
        self.paths += [value for key, value in attrs if key in ['href', 'src'] and value]

checked = 0
for page in ROOT.glob('*.html'):
    parser = Links(); parser.feed(page.read_text())
    for url in parser.paths:
        part = urllib.parse.urlsplit(url)
        if part.scheme or part.netloc or not part.path:
            continue
        checked += 1
        if not (page.parent / urllib.parse.unquote(part.path)).exists():
            errors.append(f'{page.name}: missing local link {url}')

result = {'version': '0.37.0', 'status': 'failed' if errors else 'passed',
          'dated_appointments': len(plan['appointments']),
          'distinct_appointed_sources': len({u for p in plan['appointments'] for u in p['urls']}),
          'december_fireplace_hours': fireplace_count, 'local_links_checked': checked,
          'identified_regular_episode_pools': series_sizes,
          'errors': errors,
          'scope': 'Static calendar and local links. External availability is recorded separately in seasonal-source-review.json; no full audio review.'}
(ROOT/'seasonal-validation.json').write_text(json.dumps(result, indent=2)+'\n')
(ROOT/'seasonal-summary.json').write_text(json.dumps(summaries, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, indent=2)); raise SystemExit(bool(errors))
