"""Leiden clustering of the direct-citation network (network.npz), as CWTS did for OpenAlex topics.

Topics: Leiden (modularity with resolution --res, the RB configuration model) on the undirected direct-citation graph;
topics smaller than --min papers are merged into the topic they share the most links with, and
papers with no link stay unassigned (-1). Areas: Leiden (modularity, resolution --res-area) on the
graph of topics weighted by the links between them. Writes clusters.npz (topic and area of each
paper) and prints a summary.

Usage: python cluster.py network.npz clusters.npz [--res 8] [--min 100] [--res-area 1] [--seed 1] [--iter 2] [--engine igraph]
--iter: Leiden passes (each pass refines the previous partition; -1 repeats until no change,
        which on the whole network runs for many hours).
--engine: igraph (Graph.community_leiden, in C, default) or leidenalg; same algorithm and objective,
        igraph is faster and lighter. Both run on one thread: run resolutions in parallel processes.
"""
import argparse
import random
import resource
import time

import igraph as ig
import leidenalg as la
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('network')
ap.add_argument('out')
ap.add_argument('--res', type=float, default=8.0)
ap.add_argument('--min', type=int, default=100)
ap.add_argument('--res-area', type=float, default=1.0)
ap.add_argument('--seed', type=int, default=1)
ap.add_argument('--iter', type=int, default=2)
ap.add_argument('--engine', choices=['igraph', 'leidenalg'], default='igraph')
a = ap.parse_args()
t0 = time.time()
z = np.load(a.network)
n, src, dst = len(z['recid']), z['src'], z['dst']
# undirected, each pair once
lo, hi = np.minimum(src, dst), np.maximum(src, dst)
pairs = np.unique(lo.astype(np.int64) * n + hi)
lo, hi = (pairs // n).astype(np.int32), (pairs % n).astype(np.int32)
g = ig.Graph(n=n, edges=np.column_stack([lo, hi]), directed=False)
print(f'graph: {n} papers, {g.ecount()} links ({time.time() - t0:.0f} s)')

def mem():
    return f'{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20:.1f} GB'


if a.engine == 'igraph':
    random.seed(a.seed)
    ig.set_random_number_generator(random)
    part = None
    for i in range(a.iter):
        part = g.community_leiden(objective_function='modularity', resolution=a.res, n_iterations=1,
                                  initial_membership=part.membership if part else None)
        print(f'leiden pass {i + 1}: {len(part)} clusters, quality {part.quality:.4g} ({time.time() - t0:.0f} s, {mem()})')
    topic = np.array(part.membership)
else:
    part = la.RBConfigurationVertexPartition(g, resolution_parameter=a.res)
    opt = la.Optimiser()
    opt.set_rng_seed(a.seed)
    for i in range(a.iter):
        gain = opt.optimise_partition(part)
        print(f'leiden pass {i + 1}: {len(part)} clusters, quality {part.quality():.4g}, gain {gain:.4g} ({time.time() - t0:.0f} s, {mem()})')
        if gain <= 0:
            break
    topic = np.array(part.membership)

deg = np.bincount(np.r_[lo, hi], minlength=n)
topic[deg == 0] = -1
# merge small topics into the topic they share the most links with, repeatedly
for _ in range(20):
    size = np.bincount(topic[topic >= 0])
    small = np.flatnonzero((size > 0) & (size < a.min))
    if not len(small):
        break
    tl, th = topic[lo], topic[hi]
    ok = (tl >= 0) & (th >= 0) & (tl != th)
    a_, b_ = np.r_[tl[ok], th[ok]], np.r_[th[ok], tl[ok]]
    from_small = np.isin(a_, small) & ~np.isin(b_, small)
    if not from_small.any():
        break
    key = a_[from_small].astype(np.int64) * (topic.max() + 1) + b_[from_small]
    k, c = np.unique(key, return_counts=True)
    src_t, dst_t = k // (topic.max() + 1), k % (topic.max() + 1)
    best = {}
    for s, d, cnt in zip(src_t, dst_t, c):
        if cnt > best.get(s, (0, -1))[0]:
            best[s] = (cnt, d)
    remap = np.arange(topic.max() + 1)
    for s, (_, d) in best.items():
        remap[s] = d
    topic = np.where(topic >= 0, remap[np.maximum(topic, 0)], -1)
size = np.bincount(topic[topic >= 0])
topic = np.where(topic >= 0, np.where(size[np.maximum(topic, 0)] >= a.min, topic, -1), -1)
# renumber by size, largest first
ids, cnt = np.unique(topic[topic >= 0], return_counts=True)
rank = np.empty(topic.max() + 1, dtype=np.int64)
rank[ids[np.argsort(-cnt)]] = np.arange(len(ids))
topic = np.where(topic >= 0, rank[np.maximum(topic, 0)], -1)
print(f'topics: {len(ids)} with {a.min}+ papers, {np.count_nonzero(topic >= 0)} papers assigned, '
      f'{np.count_nonzero(topic < 0)} unassigned ({time.time() - t0:.0f} s)')

# areas: Leiden on the graph of topics
tl, th = topic[lo], topic[hi]
ok = (tl >= 0) & (th >= 0) & (tl != th)
k, w = np.unique(np.minimum(tl[ok], th[ok]).astype(np.int64) * len(ids) + np.maximum(tl[ok], th[ok]), return_counts=True)
tg = ig.Graph(n=len(ids), edges=np.column_stack([k // len(ids), k % len(ids)]), directed=False)
tg.es['weight'] = w.tolist()
ap_ = la.find_partition(tg, la.RBConfigurationVertexPartition, weights='weight', resolution_parameter=a.res_area,
                        n_iterations=a.iter, seed=a.seed)
area_of_topic = np.array(ap_.membership)
tsize = np.bincount(topic[topic >= 0])
asize = np.bincount(area_of_topic, weights=tsize)
arank = np.empty(len(asize), dtype=np.int64)
arank[np.argsort(-asize)] = np.arange(len(asize))
area_of_topic = arank[area_of_topic]
area = np.where(topic >= 0, area_of_topic[np.maximum(topic, 0)], -1)
print(f'areas: {len(asize)} ({time.time() - t0:.0f} s)')
np.savez_compressed(a.out, recid=z['recid'], topic=topic, area=area, area_of_topic=area_of_topic)
