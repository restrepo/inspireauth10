"""Where the topics of an earlier clustering went: papers of each topic of the clustering of the papers up to a year,
by their topic in today's clustering, for the board page board/epoch.html.

Each earlier topic gets a fate against today's topics: same (60% of its papers in one topic of today, and they are
60% of that topic's papers up to the year: the rule used to keep names), absorbed (60% in one topic of today that also
took others), split (two or more topics of today hold 15% each), scattered. Same topics take the name of their topic
of today; the others take their name from names_2010.py.

Usage: python reproduce/topics/epoch_flows.py out/clusters/network.npz out/clusters/topics_final.npz \
    out/clusters/topics_final.json out/clusters/topics_2010_s1.npz out/topics_dash/epoch/flows2010.json --to 2010
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from names_2010 import NAMES

ap = argparse.ArgumentParser()
ap.add_argument("network")
ap.add_argument("topics")
ap.add_argument("names")
ap.add_argument("earlier", help="cluster.py output on window_network.py --to YEAR")
ap.add_argument("out")
ap.add_argument("--to", type=int, default=2010)
a = ap.parse_args()

y = np.load(a.network)["year"]
keep = (y > 0) & (y <= a.to)
now_all = np.load(a.topics)["topic"]
now = now_all[keep]
TT = json.loads(Path(a.names).read_text())
T = {x["topic"]: x for x in TT}
areas = [n for _, n in sorted({(int(x["area"]), x["area_name"]) for x in TT})]
old = np.load(a.earlier)["topic"]
assert len(old) == keep.sum(), "the earlier clustering must be of window_network.py --to YEAR"
no, nn = old.max() + 1, now_all.max() + 1
both = (old >= 0) & (now >= 0)
C = np.zeros((no, nn), np.int64)
np.add.at(C, (old[both], now[both]), 1)
so = np.bincount(old[old >= 0], minlength=no)
sn = C.sum(0)
lost = np.bincount(old[(old >= 0) & (now < 0)], minlength=no)  # papers with no topic today
new_un = np.bincount(now[(old < 0) & (now >= 0)], minlength=nn)  # papers with no topic in the earlier run
after = np.bincount(now_all[(y > a.to) & (now_all >= 0)], minlength=nn)

rows = []
for i in range(no):
    j = int(C[i].argmax())
    share, back = C[i, j] / max(C[i].sum(), 1), C[i, j] / max(sn[j], 1)
    parts = [k for k in np.argsort(-C[i]) if C[i, k] >= 0.15 * C[i].sum()]
    fate = (
        "same"
        if share >= 0.6 and back >= 0.6
        else "absorbed"
        if share >= 0.6
        else "split"
        if len(parts) >= 2
        else "scattered"
    )
    rows.append([i, int(so[i]), j, round(float(share), 3), fate, int(lost[i])])
cnt, seen = Counter(r[2] for r in rows), Counter()
for r in sorted(rows, key=lambda r: -r[1]):  # rank among topics that share a best match (kept for reference)
    seen[r[2]] += 1
    r.append(seen[r[2]] if cnt[r[2]] > 1 else 0)
for r in rows:
    r.append(T[r[2]]["name"] if r[4] == "same" else NAMES[r[0]])
flows = [[int(i), int(j), int(C[i, j])] for i, j in zip(*np.nonzero(C))]
now_rows = [
    [t, T[t]["name"], int(T[t]["area"]), int((now_all == t).sum()), int(after[t]), int(new_un[t])] for t in range(nn)
]
D = {
    "areas": areas,
    "old": rows,
    "now": now_rows,
    "flows": flows,
    "meta": {
        "to": a.to,
        "papers": int(keep.sum()),
        "both": int(both.sum()),
        "old_only": int(lost.sum()),
        "now_only": int(new_un.sum()),
    },
}
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
Path(a.out).write_text(json.dumps(D, separators=(",", ":"), ensure_ascii=False))
print(f"{a.out}: {no} earlier topics ({dict(Counter(r[4] for r in rows))}), {len(flows)} flows")
