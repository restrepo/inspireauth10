"""Agreement between clusterings of the same network (different seeds): NMI and ARI of every pair,
for topics and for areas, on the papers that all of them assign. Prints the table and the medoid,
the clustering with the highest mean topic NMI to the others, which is the one to keep.

Usage: python compare.py clusters_a.npz clusters_b.npz [...]
"""
import itertools
import sys

import igraph as ig
import numpy as np

files = sys.argv[1:]
runs = [np.load(f) for f in files]
mask = np.logical_and.reduce([r['topic'] >= 0 for r in runs])
print(f'{len(files)} clusterings, {mask.sum()} papers assigned in all')
for f, r in zip(files, runs):
    t = r['topic']
    print(f'  {f}: {t.max() + 1} topics, {r["area"].max() + 1} areas, quality {float(r["quality"]):.6g}'
          if 'quality' in r else f'  {f}: {t.max() + 1} topics, {r["area"].max() + 1} areas')
mean = np.zeros(len(runs))
for level in ('topic', 'area'):
    print(level)
    for i, j in itertools.combinations(range(len(runs)), 2):
        a, b = runs[i][level][mask].tolist(), runs[j][level][mask].tolist()
        nmi, ari = ig.compare_communities(a, b, 'nmi'), ig.compare_communities(a, b, 'ari')
        print(f'  {files[i]} vs {files[j]}: NMI {nmi:.3f}, ARI {ari:.3f}')
        if level == 'topic':
            mean[i] += nmi
            mean[j] += nmi
best = int(np.argmax(mean))
print(f'medoid: {files[best]} (mean topic NMI {mean[best] / (len(runs) - 1):.3f})')
