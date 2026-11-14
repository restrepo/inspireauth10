"""Datasets of the topics board from a kept clustering (cluster.py), its description (describe.py)
and its names (names.py).

Writes into OUT/: scalars, areas, topics (with a map position and trend), topic_links, topic_year,
area_year, country_area and country_topic (JSON lists, as reproduce/indicators.py).

Usage: python reproduce/topics/indicators.py data/ out/clusters/topics_final.npz \\
           out/clusters/topics_final.json out/clusters/network.npz out/topics_dash/ [--min-country 1000]
"""
import argparse
import gzip
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import igraph as ig
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import AREAS, TOPICS  # noqa: E402
from trends import add_trends  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('data')
ap.add_argument('clusters')
ap.add_argument('described')
ap.add_argument('network')
ap.add_argument('out')
ap.add_argument('--min-country', type=int, default=1000, help='keep the countries with at least this many papers with a topic')
a = ap.parse_args()
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)


def dump(name, value):
    json.dump(value, open(out / f'{name}.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
    print(name, len(value))


c = np.load(a.clusters)
topic_of = dict(zip(c['recid'].tolist(), c['topic'].tolist()))
area_of_topic = c['area_of_topic']
nt = len(area_of_topic)
described = {t['topic']: t for t in json.load(open(a.described, encoding='utf-8'))}

# one pass over the papers
year_t = Counter()                      # (topic, year) -> papers
cits = np.zeros(nt)
corpus = np.zeros(nt, dtype=int)        # papers with 1 to 10 authors
country_t = Counter()                   # (country, topic) -> papers
country_n = Counter()
unassigned = linked = total = 0
for line in gzip.open(Path(a.data) / 'papers.jsonl.gz', 'rt', encoding='utf-8'):
    p = json.loads(line)
    total += 1
    t = topic_of[p['recid']]
    if t < 0:
        unassigned += 1
        continue
    y = int(p['year']) if p['year'].isdigit() else 0
    if 1900 < y <= 2026:
        year_t[t, y] += 1
    cits[t] += p['citation_count'] or 0
    corpus[t] += not p.get('collaborations')
    for k in p['countries']:
        country_t[k, t] += 1
        country_n[k] += 1
size = np.bincount(c['topic'][c['topic'] >= 0], minlength=nt)

# topic graph: links between topics, association strength for the map
z = np.load(a.network)
n = len(z['recid'])
lo, hi = np.minimum(z['src'], z['dst']), np.maximum(z['src'], z['dst'])
pairs = np.unique(lo.astype(np.int64) * n + hi)
lo, hi = (pairs // n).astype(np.int32), (pairs % n).astype(np.int32)
tp = c['topic']
tl, th = tp[lo], tp[hi]
ok = (tl >= 0) & (th >= 0) & (tl != th)
k, w = np.unique(np.minimum(tl[ok], th[ok]).astype(np.int64) * nt + np.maximum(tl[ok], th[ok]), return_counts=True)
ea, eb = (k // nt).astype(int), (k % nt).astype(int)
strength = np.bincount(np.r_[ea, eb], weights=np.r_[w, w], minlength=nt)
assoc = w / (strength[ea] * strength[eb]) * strength.sum()
g = ig.Graph(n=nt, edges=list(zip(ea.tolist(), eb.tolist())))
# keep each topic's 6 strongest links for the layout, so the map shows neighbourhoods
keep = set()
for t in range(nt):
    idx = np.flatnonzero((ea == t) | (eb == t))
    keep.update(idx[np.argsort(-assoc[idx])[:6]].tolist())
keep = sorted(keep)
lg = ig.Graph(n=nt, edges=[(int(ea[i]), int(eb[i])) for i in keep])
random.seed(1)
ig.set_random_number_generator(random)
lay = lg.layout_fruchterman_reingold(weights=[math.log1p(assoc[i]) for i in keep], niter=2000)
xy = np.array(lay.coords)
xy = (xy - xy.mean(0)) / np.abs(xy - xy.mean(0)).max()
dump('topic_links', [{'a': int(ea[i]), 'b': int(eb[i]), 'links': int(w[i]), 'assoc': round(float(assoc[i]), 2)} for i in keep])

recent, earlier = range(2021, 2026), range(2011, 2016)
topics = []
for t in range(nt):
    d = described[t]
    r = sum(year_t[t, y] for y in recent)
    e = sum(year_t[t, y] for y in earlier)
    topics.append({
        'topic': t, 'name': TOPICS[t], 'area': int(area_of_topic[t]), 'area_name': AREAS[int(area_of_topic[t])],
        'papers': int(size[t]), 'corpus_papers': int(corpus[t]), 'citations': int(cits[t]),
        'citations_per_paper': round(cits[t] / size[t], 1), 'year_median': d['year_median'],
        'year_p10': d['year_p10'], 'year_p90': d['year_p90'], 'papers_2011_2015': e, 'papers_2021_2025': r,
        'arxiv': d['arxiv'], 'journals': d['journals'], 'countries': d['countries'],
        'top_papers': d['top_papers'][:6], 'x': round(float(xy[t, 0]), 4), 'y': round(float(xy[t, 1]), 4)})
dump('topics', add_trends(topics))
dump('topic_year', [{'topic': t, 'year': y, 'papers': v} for (t, y), v in sorted(year_t.items())])
area_year = Counter()
for (t, y), v in year_t.items():
    area_year[int(area_of_topic[t]), y] += v
dump('area_year', [{'area': ar, 'year': y, 'papers': v} for (ar, y), v in sorted(area_year.items())])
areas = []
for ar, name in AREAS.items():
    ts = [t for t in topics if t['area'] == ar]
    ax = Counter()
    for t in ts:
        for cat, pct in t['arxiv']:
            ax[cat] += pct * t['papers'] / 100
    tot = sum(t['papers'] for t in ts)
    areas.append({'area': ar, 'name': name, 'papers': tot, 'topics': len(ts), 'citations': sum(t['citations'] for t in ts),
                  'arxiv': [[k_, round(100 * v / tot, 1)] for k_, v in ax.most_common(5)],
                  'papers_2011_2015': sum(t['papers_2011_2015'] for t in ts), 'papers_2021_2025': sum(t['papers_2021_2025'] for t in ts)})
dump('areas', areas)
top_c = [k_ for k_, v in country_n.most_common() if v >= a.min_country]
dump('country_topic', [{'country': k_, 'topic': t, 'papers': v} for (k_, t), v in sorted(country_t.items())
                       if k_ in top_c])
country_area = Counter()
for (k_, t), v in country_t.items():
    if k_ in top_c:
        country_area[k_, int(area_of_topic[t])] += v
dump('country_area', [{'country': k_, 'area': ar, 'papers': v} for (k_, ar), v in sorted(country_area.items())])
dump('scalars', [{'id': k_, 'value': v} for k_, v in [
    ('papers', total), ('assigned', int(size.sum())), ('unassigned', unassigned), ('topics', nt), ('areas', len(AREAS)),
    ('citation_links', int(len(pairs))), ('resolution', 16), ('area_resolution', float(c['res_area']) if 'res_area' in c else 0.3),
    ('countries', len(top_c))]])
