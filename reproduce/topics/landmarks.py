"""Landmark papers of the citation network: where their citations come from, and how disruptive they are.

impact.json      the TOP most cited papers of the network (citations inside it), with the number of
                 citing papers in each of the six areas
disruption.json  the CD_5 disruption index (Funk & Owen-Smith 2017; Park, Leahey & Funk 2023) of every
                 paper with at least MIN_CITES citations and MIN_REFS references inside the network,
                 published up to LAST_YEAR. For a focal paper f with references R, among the papers
                 published from f's year to five years later: n_i cite f but none of R, n_j cite f and
                 some of R, n_k cite some of R but not f; D = (n_i - n_j) / (n_i + n_j + n_k), from -1
                 (consolidating) to 1 (disruptive). `cd` is the same index with no time limit, for papers recognized late.

Usage: python reproduce/topics/landmarks.py out/clusters/network.npz out/clusters/topics_final.npz out/topics_dash/
"""
import json
import sys
from pathlib import Path

import numpy as np
from numba import njit, prange

TOP, MIN_CITES, MIN_REFS, WINDOW, LAST_YEAR = 300, 100, 5, 5, 2020

net, clusters, out = (Path(p) for p in sys.argv[1:4])
z, c = np.load(net), np.load(clusters)
recid, year, src, dst = z['recid'], z['year'].astype(np.int32), z['src'], z['dst']
area, topic = c['area'], c['topic']
n = len(recid)
cites, refs = np.bincount(dst, minlength=n), np.bincount(src, minlength=n)

# citing papers of each paper (CSC), sorted by year; references of each paper (CSR)
o = np.lexsort((year[src], dst))
cit_ptr, cit = np.r_[0, np.cumsum(cites)], src[o].astype(np.int32)
cit_year = year[cit]
o = np.argsort(src, kind='stable')
ref_ptr, ref = np.r_[0, np.cumsum(refs)], dst[o].astype(np.int32)

top = np.argsort(-cites)[:TOP]
impact = []
for i in top:
    a = area[cit[cit_ptr[i]:cit_ptr[i + 1]]]
    impact.append({'recid': int(recid[i]), 'year': int(year[i]), 'area': int(area[i]), 'topic': int(topic[i]),
                   'citations': int(cites[i]), 'by_area': np.bincount(a[a >= 0], minlength=6).tolist()})
(out / 'impact.json').write_text(json.dumps(impact, separators=(',', ':')))
print(f'impact.json: {len(impact)} papers', file=sys.stderr)


@njit
def window(ptr, yr, i, lo, hi):
    a, b = ptr[i], ptr[i + 1]
    return a + np.searchsorted(yr[a:b], lo), a + np.searchsorted(yr[a:b], hi, side='right')


@njit(parallel=True)
def cd(focal, year, cit_ptr, cit, cit_year, ref_ptr, ref, w, n, chunks):
    m = len(focal)
    D, NI, NJ, NK = np.zeros(m), np.zeros(m), np.zeros(m), np.zeros(m)
    for c in prange(chunks):
        is_ref = np.full(n, -1, np.int32)  # is_ref[p] == t: p is a reference of focal t
        seen = np.full(n, -1, np.int32)    # seen[p] == t: p already counted for focal t
        for t in range(c, m, chunks):
            f = focal[t]
            lo, hi = year[f], year[f] + w
            for q in range(ref_ptr[f], ref_ptr[f + 1]):
                is_ref[ref[q]] = t
            seen[f] = t
            ni = nj = nk = 0
            a, b = window(cit_ptr, cit_year, f, lo, hi)
            for k in range(a, b):
                p = cit[k]
                seen[p] = t
                both = False
                for q in range(ref_ptr[p], ref_ptr[p + 1]):
                    if is_ref[ref[q]] == t:
                        both = True
                        break
                if both:
                    nj += 1
                else:
                    ni += 1
            for q in range(ref_ptr[f], ref_ptr[f + 1]):
                a, b = window(cit_ptr, cit_year, ref[q], lo, hi)
                for k in range(a, b):
                    p = cit[k]
                    if seen[p] != t:
                        seen[p] = t
                        nk += 1
            NI[t], NJ[t], NK[t] = ni, nj, nk
            tot = ni + nj + nk
            D[t] = (ni - nj) / tot if tot else 0.0
    return D, NI, NJ, NK


focal = np.flatnonzero((cites >= MIN_CITES) & (refs >= MIN_REFS) & (year > 0) & (year <= LAST_YEAR)).astype(np.int32)
D, NI, NJ, NK = cd(focal, year, cit_ptr, cit, cit_year, ref_ptr, ref, WINDOW, n, 64)
DA = cd(focal, year, cit_ptr, cit, cit_year, ref_ptr, ref, 200, n, 64)[0]
rows = [{'recid': int(recid[f]), 'year': int(year[f]), 'area': int(area[f]), 'topic': int(topic[f]), 'citations': int(cites[f]),
         'refs': int(refs[f]), 'cd5': round(float(d), 4), 'ni': int(i), 'nj': int(j), 'nk': int(k), 'cd': round(float(da), 4)}
        for f, d, i, j, k, da in zip(focal, D, NI, NJ, NK, DA)]
(out / 'disruption.json').write_text(json.dumps(rows, separators=(',', ':')))
print(f'disruption.json: {len(rows)} papers, median CD_5 {np.median(D):.4f}', file=sys.stderr)
