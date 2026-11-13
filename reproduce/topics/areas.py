"""Recompute the areas of a clustering (cluster.py output) at another area resolution, without
rerunning the topics: Leiden on the graph of topics with the links inside each topic as
self-loops, the best of --seeds runs. Rewrites area, area_of_topic and area_quality in place.

Usage: python areas.py network.npz clusters.npz [--res-area 0.3] [--seeds 50]
"""
import argparse

import igraph as ig
import leidenalg as la
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('network')
ap.add_argument('clusters')
ap.add_argument('--res-area', type=float, default=0.3)
ap.add_argument('--seeds', type=int, default=50)
a = ap.parse_args()
z = np.load(a.network)
n = len(z['recid'])
lo, hi = np.minimum(z['src'], z['dst']), np.maximum(z['src'], z['dst'])
pairs = np.unique(lo.astype(np.int64) * n + hi)
lo, hi = (pairs // n).astype(np.int32), (pairs % n).astype(np.int32)
c = dict(np.load(a.clusters))
topic = c['topic']
m = topic.max() + 1
tl, th = topic[lo], topic[hi]
ok = (tl >= 0) & (th >= 0)
k, w = np.unique(np.minimum(tl[ok], th[ok]).astype(np.int64) * m + np.maximum(tl[ok], th[ok]), return_counts=True)
tg = ig.Graph(n=m, edges=np.column_stack([k // m, k % m]), directed=False)
tg.es['weight'] = w.tolist()
runs = [la.find_partition(tg, la.RBConfigurationVertexPartition, weights='weight', resolution_parameter=a.res_area,
                          n_iterations=-1, seed=s) for s in range(1, a.seeds + 1)]
best = max(runs, key=lambda q: q.quality())
counts = np.bincount([len(q) for q in runs])
print('areas over seeds: ' + ', '.join(f'{c_} runs with {k_}' for k_, c_ in enumerate(counts) if c_))
area_of_topic = np.array(best.membership)
asize = np.bincount(area_of_topic, weights=np.bincount(topic[topic >= 0]))
rank = np.empty(len(asize), dtype=np.int64)
rank[np.argsort(-asize)] = np.arange(len(asize))
area_of_topic = rank[area_of_topic]
c.update(area_of_topic=area_of_topic, area=np.where(topic >= 0, area_of_topic[np.maximum(topic, 0)], -1),
         area_quality=best.quality(), res_area=a.res_area)
np.savez_compressed(a.clusters, **c)
print(f'{len(asize)} areas at resolution {a.res_area}, sizes {sorted(asize.astype(int).tolist(), reverse=True)}')
