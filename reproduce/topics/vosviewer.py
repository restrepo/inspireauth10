"""Write the graph of topics as VOSviewer input: one item per topic (label, area as cluster, papers
and citation links as weights, median year as score) and one link per pair of topics, whose strength
is the number of distinct citation links between their papers. Writes a VOSviewer JSON file (opens in
VOSviewer 1.6.16+ and VOSviewer Online) and the classic map and network text files.

Usage: python vosviewer.py network.npz topics_final.npz topics_final.json out_dir/ [--min-links 1]
"""
import argparse
import json
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('network')
ap.add_argument('clusters')
ap.add_argument('described')
ap.add_argument('out')
ap.add_argument('--min-links', type=int, default=1, help='drop links weaker than this')
a = ap.parse_args()
z = np.load(a.network)
n = len(z['recid'])
lo, hi = np.minimum(z['src'], z['dst']), np.maximum(z['src'], z['dst'])
pairs = np.unique(lo.astype(np.int64) * n + hi)
lo, hi = (pairs // n).astype(np.int32), (pairs % n).astype(np.int32)
topic = np.load(a.clusters)['topic']
m = topic.max() + 1
tl, th = topic[lo], topic[hi]
ok = (tl >= 0) & (th >= 0)
k, w = np.unique(np.minimum(tl[ok], th[ok]).astype(np.int64) * m + np.maximum(tl[ok], th[ok]), return_counts=True)
s, t = k // m, k % m
inside = np.bincount(s[s == t], weights=w[s == t], minlength=m).astype(int)
cross = (s != t) & (w >= a.min_links)
s, t, w = s[cross], t[cross], w[cross]
links_of = np.bincount(np.concatenate([s, t]), weights=np.concatenate([w, w]), minlength=m).astype(int)
desc = {d['topic']: d for d in json.load(open(a.described))}

out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
items = [{'id': i + 1, 'label': desc[i]['name'], 'cluster': desc[i]['area'] + 1,
          'description': f"<b>{desc[i]['name']}</b><br>{desc[i]['area_name']}<br>"
                         f"{desc[i]['papers']:,} papers, {desc[i]['year_p10']}–{desc[i]['year_p90']}",
          'weights': {'Papers': desc[i]['papers'], 'Citation links': int(links_of[i]),
                      'Internal citation links': int(inside[i])},
          'scores': {'Median year': desc[i]['year_median']}} for i in range(m)]
links = [{'source_id': int(i) + 1, 'target_id': int(j) + 1, 'strength': int(x)} for i, j, x in zip(s, t, w)]
vos = {'network': {'items': items, 'links': links},
       'config': {'terminology': {'item': 'topic', 'items': 'topics', 'link': 'citation link',
                                  'links': 'citation links', 'link_strength': 'citation links',
                                  'total_link_strength': 'total citation links'}}}
(out / 'topics_vosviewer.json').write_text(json.dumps(vos, ensure_ascii=False))
with open(out / 'topics_map.txt', 'w') as f:
    f.write('id\tlabel\tcluster\tweight<Papers>\tweight<Citation links>\tscore<Median year>\n')
    for it in items:
        f.write(f"{it['id']}\t{it['label']}\t{it['cluster']}\t{it['weights']['Papers']}\t"
                f"{it['weights']['Citation links']}\t{it['scores']['Median year']}\n")
with open(out / 'topics_network.txt', 'w') as f:
    for li in links:
        f.write(f"{li['source_id']}\t{li['target_id']}\t{li['strength']}\n")
print(f'{m} topics, {len(links)} links ({w.sum():,} citation links between topics, {inside.sum():,} inside) -> {out}')
