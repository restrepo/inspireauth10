"""Describe the clusters of clusters.npz from the papers table, with the titles of their most cited
papers from INSPIRE. Writes topics.json (one object per topic) and areas.json.

Usage: python describe.py clusters.npz data/papers.jsonl.gz topics.json areas.json [--top 8]
"""
import argparse
import gzip
import json
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('clusters')
ap.add_argument('papers')
ap.add_argument('topics_out')
ap.add_argument('areas_out')
ap.add_argument('--top', type=int, default=8)
a = ap.parse_args()
z = np.load(a.clusters)
topic_of = dict(zip(z['recid'].tolist(), z['topic'].tolist()))
area_of_topic = z['area_of_topic']

n = Counter()
years, cats, journals, countries = defaultdict(list), defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
cites = defaultdict(list)  # (citation_count, recid)
for line in gzip.open(a.papers, 'rt', encoding='utf-8'):
    p = json.loads(line)
    t = topic_of[p['recid']]
    if t < 0:
        continue
    n[t] += 1
    y = int(p['year']) if p['year'].isdigit() else 0
    if y:
        years[t].append(y)
    cats[t][(p['arxiv_categories'] or ['none'])[0]] += 1
    if p.get('journal'):
        journals[t][p['journal']] += 1
    for c in p['countries']:
        countries[t][c] += 1
    cites[t].append((p['citation_count'] or 0, p['recid']))

top = {t: [r for _, r in sorted(v, reverse=True)[:a.top]] for t, v in cites.items()}
want = sorted({r for v in top.values() for r in v})
titles = {}
for i in range(0, len(want), 50):
    q = ' or '.join(f'recid:{r}' for r in want[i:i + 50])
    url = ('https://inspirehep.net/api/literature?size=50&fields=control_number,titles.title&q='
           + urllib.parse.quote(q))
    for attempt in range(5):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'restrepo/inspireauth10'}), timeout=120))
            break
        except Exception:
            time.sleep(5 * (attempt + 1))
    for h in d['hits']['hits']:
        m = h['metadata']
        titles[m['control_number']] = (m.get('titles') or [{}])[0].get('title')
    time.sleep(0.4)

def pct(counter, total, k):
    return [[x, round(100 * c / total, 1)] for x, c in counter.most_common(k)]

rows = []
for t in sorted(n):
    ys = np.array(years[t]) if years[t] else np.array([0])
    rows.append({'topic': t, 'area': int(area_of_topic[t]), 'papers': n[t],
                 'year_median': int(np.median(ys)), 'year_p10': int(np.percentile(ys, 10)), 'year_p90': int(np.percentile(ys, 90)),
                 'arxiv': pct(cats[t], n[t], 5), 'journals': pct(journals[t], n[t], 5), 'countries': pct(countries[t], n[t], 5),
                 'top_papers': [{'recid': r, 'citations': c, 'title': titles.get(r)} for c, r in sorted(cites[t], reverse=True)[:a.top]]})
json.dump(rows, open(a.topics_out, 'w'), ensure_ascii=False, indent=1)

areas = defaultdict(lambda: {'papers': 0, 'topics': [], 'arxiv': Counter()})
for r in rows:
    A = areas[r['area']]
    A['papers'] += r['papers']
    A['topics'].append(r['topic'])
    A['arxiv'].update(cats[r['topic']])
json.dump([{'area': k, 'papers': v['papers'], 'topics': v['topics'], 'arxiv': pct(v['arxiv'], v['papers'], 6)}
           for k, v in sorted(areas.items())], open(a.areas_out, 'w'), ensure_ascii=False, indent=1)
print(f'{len(rows)} topics, {len(areas)} areas, {len(titles)} titles')
