"""Author flows between topics, datasets of the topics board (author_flows.json, flow_periods.json).

For each pair of periods, every author with an INSPIRE profile and at least MIN_PAPERS papers with a
topic in the early period gets as early topic the topic with most of their papers there, each paper
counting 1/(number of authors); papers with more than MAX_AUTHORS authors are left out. The late
topic is found the same way in the late period (any paper), or the author "stopped" (to = -1).
For each early topic, the KEEP largest destinations are kept and the others are summed into one
row (to = -2, with the number of topics in `topics`).

Also writes flow_periods.json (the three pairs of periods).

Usage: python reproduce/topics/author_flows.py data/ out/clusters/topics_final.npz out/topics_dash/
"""
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

MAX_AUTHORS, MIN_PAPERS, KEEP = 10, 2, 15
PAIRS = [((1986, 1998), (2003, 2015)), ((1996, 2008), (2013, 2025)), ((2006, 2013), (2018, 2025))]

data, clusters, out = (Path(p) for p in sys.argv[1:4])
c = np.load(clusters)
top = dict(zip(c['recid'].tolist(), c['topic'].tolist()))
W = defaultdict(lambda: defaultdict(Counter))  # profile -> year -> topic -> weight ('n': papers)
for line in gzip.open(data / 'papers.jsonl.gz', 'rt'):
    p = json.loads(line)
    t = top.get(p['recid'], -1)
    if t < 0 or not p['year'] or p['n_authors'] > MAX_AUTHORS or int(p['year']) < PAIRS[0][0][0]:
        continue
    y = int(p['year'])
    for a in p['authors']:
        if a.get('profile_id'):
            W[a['profile_id']][y][t] += 1 / len(p['authors'])
            W[a['profile_id']][y]['n'] += 1


def main_topic(years, lo, hi, min_papers):
    w, n = Counter(), 0
    for y in range(lo, hi + 1):
        if y in years:
            n += years[y]['n']
            w.update({k: v for k, v in years[y].items() if k != 'n'})
    return w.most_common(1)[0][0] if w and n >= min_papers else None


rows, periods = [], []
for i, ((a0, a1), (b0, b1)) in enumerate(PAIRS):
    F = defaultdict(Counter)
    for years in W.values():
        e = main_topic(years, a0, a1, MIN_PAPERS)
        if e is not None:
            late = main_topic(years, b0, b1, 1)
            F[e][-1 if late is None else late] += 1
    periods.append({'period': i, 'early': f'{a0}–{a1}', 'late': f'{b0}–{b1}'})
    for e in sorted(F):
        stop = F[e].pop(-1, 0)
        ranked = F[e].most_common()
        for t, n in ranked[:KEEP] + [(-1, stop)] * bool(stop):
            rows.append({'period': i, 'from': e, 'to': t, 'authors': n})
        if len(ranked) > KEEP:
            rows.append({'period': i, 'from': e, 'to': -2, 'authors': sum(n for _, n in ranked[KEEP:]), 'topics': len(ranked) - KEEP})
    print(f'{a0}-{a1} -> {b0}-{b1}: {sum(sum(f.values()) for f in F.values())} authors who still publish', file=sys.stderr)
(out / 'author_flows.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
(out / 'flow_periods.json').write_text(json.dumps(periods, ensure_ascii=False, separators=(',', ':')))
print(f'author_flows.json: {len(rows)} rows', file=sys.stderr)
