"""Write the direct-citation network of the papers published in a range of years, for cluster.py.

Keeps the papers with FROM <= year <= TO (year 0, unknown, left out) and the citation links between them; node
order follows network.npz.

Usage: python reproduce/topics/window_network.py out/clusters/network.npz out/clusters/network_2010.npz --to 2010
       python reproduce/topics/window_network.py out/clusters/network.npz out/clusters/network_2000.npz --from 2000
"""
import argparse

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('network')
ap.add_argument('out')
ap.add_argument('--from', dest='lo', type=int, default=1)
ap.add_argument('--to', dest='hi', type=int, default=9999)
a = ap.parse_args()
z = np.load(a.network)
y, s, d = z['year'], z['src'], z['dst']
keep = (y >= a.lo) & (y <= a.hi) & (y > 0)
idx = np.full(len(y), -1, np.int64)
idx[keep] = np.arange(keep.sum())
m = keep[s] & keep[d]
nodes = {k: z[k][keep] for k in z.files if k not in ('src', 'dst') and z[k].shape == y.shape}
np.savez_compressed(a.out, src=idx[s[m]].astype(np.int32), dst=idx[d[m]].astype(np.int32), **nodes)
print(f'{a.out}: {keep.sum():,} papers, {m.sum():,} links')
