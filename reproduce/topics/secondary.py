"""Second and third topics of every paper, scored against its main topic. A paper's citation links
(references and citing papers, counted once per pair) are counted by the topic of the paper at the
other end; the main topic is the paper's own topic (score 1), and the second and third are the other
topics with the most links, scored as links to that topic / links to the main topic, capped at 1.
Papers with no topic (unassigned by the clustering) get as main topic the topic they have most
links to, marked as inferred. Papers with no link to any topic keep no topic.

Writes an npz aligned with network.npz: recid, topic (3 columns, -1 if none), score (3 columns),
links (3 columns), n_links (links to papers with a topic) and inferred.

Usage: python secondary.py network.npz topics_final.npz topics_multi.npz
"""
import sys

import numpy as np

net, clusters, out = sys.argv[1:4]
z = np.load(net)
n = len(z['recid'])
lo, hi = np.minimum(z['src'], z['dst']), np.maximum(z['src'], z['dst'])
pairs = np.unique(lo[lo != hi].astype(np.int64) * n + hi[lo != hi])
lo, hi = pairs // n, pairs % n
del pairs
topic = np.load(clusters)['topic']
m = int(topic.max()) + 1
# One row per (paper, topic of a linked paper), both directions of each pair.
p = np.concatenate([lo[topic[hi] >= 0], hi[topic[lo] >= 0]])
t = np.concatenate([topic[hi[topic[hi] >= 0]], topic[lo[topic[lo] >= 0]]])
del lo, hi
k, c = np.unique(p * m + t, return_counts=True)
del p, t
p, t = k // m, k % m
o = np.lexsort((-c, p))  # by paper, most links first
p, t, c = p[o], t[o], c[o]
n_links = np.bincount(p, weights=c, minlength=n).astype(np.int64)

main = topic.copy()
inferred = (main < 0) & (n_links > 0)
first = np.r_[True, p[1:] != p[:-1]]
main[p[first & inferred[p]]] = t[first & inferred[p]]
own = t == main[p]
main_links = np.zeros(n, dtype=np.int64)
main_links[p[own]] = c[own]
p, t, c = p[~own], t[~own], c[~own]
start = np.r_[0, np.flatnonzero(p[1:] != p[:-1]) + 1]
rank = np.arange(len(p)) - np.repeat(start, np.diff(np.r_[start, len(p)]))

T = -np.ones((n, 3), dtype=np.int16)
L = np.zeros((n, 3), dtype=np.int32)
T[:, 0], L[:, 0] = main, main_links
for r in (1, 2):
    s = rank == r - 1
    T[p[s], r], L[p[s], r] = t[s], c[s]
S = np.zeros((n, 3), dtype=np.float32)
S[main >= 0, 0] = 1
with np.errstate(divide='ignore', invalid='ignore'):
    ratio = np.where(L[:, 0:1] > 0, L[:, 1:] / L[:, 0:1], 1.0)
S[:, 1:] = np.where(T[:, 1:] >= 0, np.minimum(ratio, 1), 0)
np.savez_compressed(out, recid=z['recid'], topic=T, score=S, links=L, n_links=n_links, inferred=inferred)

has = T[:, 0] >= 0
print(f'{n} papers: {has.sum()} with a main topic ({(topic >= 0).sum()} from the clustering, {inferred.sum()} inferred), '
      f'{(T[:, 1] >= 0).sum()} with a second topic, {(T[:, 2] >= 0).sum()} with a third')
print(f'second topic links above the main topic\'s (score capped at 1): {((L[:, 1] > L[:, 0]) & (T[:, 1] >= 0)).sum()}')
for r in (1, 2):
    v = S[T[:, r] >= 0, r]
    print(f'score of topic {r + 1}: median {np.median(v):.3f}, quartiles {np.percentile(v, 25):.3f}-{np.percentile(v, 75):.3f}')
