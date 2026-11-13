"""Direct-citation network of the papers table: nodes are papers, an edge links a paper to each
paper of the table it cites. Writes network.npz with recid, year, n_authors, cats (main arXiv
category) and the edges as node indices src -> dst."""
import gzip, json, sys
from array import array
import numpy as np

path, out = sys.argv[1], sys.argv[2]
recids, years, nauth, cats, refs = array('q'), array('h'), array('i'), [], []
for line in gzip.open(path, 'rt', encoding='utf-8'):
    p = json.loads(line)
    recids.append(p['recid'])
    years.append(int(p['year']) if p['year'].isdigit() else 0)
    nauth.append(p['n_authors'])
    cats.append((p['arxiv_categories'] or [''])[0].split('.')[0])
    refs.append(array('q', (r['recid'] for r in p['references'])))
recid = np.frombuffer(recids, dtype=np.int64)
order = np.argsort(recid)
src, dst = array('i'), array('i')
for i, rs in enumerate(refs):
    if not rs:
        continue
    r = np.frombuffer(rs, dtype=np.int64)
    k = np.searchsorted(recid, r, sorter=order)
    k = np.minimum(k, len(order) - 1)
    hit = recid[order[k]] == r
    j = order[k[hit]]
    j = j[j != i]
    src.extend([i] * len(j))
    dst.extend(j.tolist())
    refs[i] = None
src, dst = np.frombuffer(src, dtype=np.int32), np.frombuffer(dst, dtype=np.int32)
np.savez_compressed(out, recid=recid, year=np.frombuffer(years, dtype=np.int16), n_authors=np.frombuffer(nauth, dtype=np.int32),
                    cats=np.array(cats), src=src, dst=dst)
print(f'{len(recid)} papers, {len(src)} citation links, {np.count_nonzero(np.bincount(np.r_[src, dst], minlength=len(recid)))} papers with a link')
