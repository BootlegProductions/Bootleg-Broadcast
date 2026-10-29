"""Probe a representative sample of published holiday links without downloading movies.

HEAD verifies HTTP reachability only; neither codec playback nor rights are asserted.
"""
import concurrent.futures
import json
import pathlib
import urllib.request
import urllib.error

root = pathlib.Path(__file__).resolve().parents[1]
registry = json.loads((root / 'holiday-programmes-report.json').read_text())
source = (root / 'holiday-programmes.js').read_text()
# The asset is JS rather than JSON; isolate the embedded JSON object safely.
marker = 'const db='
start = source.index(marker) + len(marker)
end = source.index(';\n root.BOOTLEG_HOLIDAY_MEDIA=db;', start)
db = json.loads(source[start:end])
items = db['programmes']
sample = []
seen_channels = set()
# One or more sources per channel, then additional large feature films.
for row in items:
    if row['channel'] not in seen_channels:
        sample.append(row)
        seen_channels.add(row['channel'])
for row in items:
    if row['type'] == 'Movie' and row['id'] not in {p['id'] for p in sample}:
        sample.append(row)
    if len(sample) >= 18:
        break

def check(item):
    request = urllib.request.Request(item['url'], method='HEAD',
        headers={'User-Agent': 'Mozilla/5.0 (Bootleg Broadcast link checker)',
                 'Accept': 'video/mp4,*/*'})
    try:
        with urllib.request.urlopen(request, timeout=18) as response:
            status = response.status
            content_type = response.headers.get('Content-Type','')
            return {'channel': item['channel'], 'title': item['title'],
                    'status': status, 'content_type': content_type,
                    'head_reachable': status in (200,206),
                    'url': item['url']}
    except Exception as exc:
        return {'channel': item['channel'], 'title': item['title'],
                'head_reachable': False, 'error': str(exc)[:220],
                'url': item['url']}

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    results = list(pool.map(check,sample))
report={'checked':len(results),'http_reachable':sum(x['head_reachable'] for x in results),
        'results':results,'note':'HEAD only; browser-compatible audio/video and rights are not verified.'}
(root/'holiday-link-check.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'checked':report['checked'],'http_reachable':report['http_reachable'],
                  'failed':[x['title'] for x in results if not x['head_reachable']]},indent=2))
