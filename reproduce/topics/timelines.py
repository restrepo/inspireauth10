"""Citation timelines of every topic, for reproduce/topics/board/timeline.html (one JSON file per topic, loaded
when a topic is chosen, so the board stays small).

For each topic: its TOTAL most cited papers (INSPIRE citation counts), with its most cited papers with Latin
American authors first (at most LA_SHARE of them); the citations between them (network.npz); titles and arXiv
numbers from data/papers_text.jsonl.gz. Orange = Latin American authors, blue = the LANDMARKS most cited.

Writes OUT/<topic>.json ({n, e, meta}, the format of the hep-citation-graph pages) and OUT/index.json.

Usage: python reproduce/topics/timelines.py data/ out/clusters/ out/topics_dash/timelines/ [TREND topics.json]

With TREND (Growing, Stable or Shrinking) and the board's topics.json (reproduce/topics/trends.py), only the topics of
that trend get a timeline; the board shows the timeline of the topics listed in OUT/index.json.
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

TOTAL, LA_SHARE, LANDMARKS, LA_LABELS = 500, 0.2, 15, 20
LA = {'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Costa Rica', 'Cuba', 'Ecuador', 'El Salvador',
      'Guatemala', 'Honduras', 'Mexico', 'Nicaragua', 'Panama', 'Paraguay', 'Peru', 'Uruguay', 'Venezuela',
      'Dominican Republic', 'Puerto Rico'}

data, clusters, out = (Path(p) for p in sys.argv[1:4])
out.mkdir(parents=True, exist_ok=True)
c = np.load(clusters / 'topics_final.npz')
z = np.load(clusters / 'network.npz')
TOP = {t['topic']: t for t in json.load(open(clusters / 'topics_final.json'))}
AREA = {a['area']: a['name'] for a in json.load(open(clusters / 'areas_final.json'))}
topic_of = dict(zip(c['recid'].tolist(), c['topic'].tolist()))
if len(sys.argv) > 5:
    only = {t['topic'] for t in json.load(open(sys.argv[5])) if t['trend'] == sys.argv[4]}
    topic_of = {r: t if t in only else -1 for r, t in topic_of.items()}

# pass 1: citations and Latin American countries of every paper with a topic
cites, la = {}, {}
for line in gzip.open(data / 'papers.jsonl.gz', 'rt'):
    p = json.loads(line)
    if topic_of.get(p['recid'], -1) >= 0:
        cites[p['recid']] = p['citation_count']
        if LA & set(p.get('countries') or []):
            la[p['recid']] = sorted(LA & set(p['countries']))
by_topic = {}
for r in cites:
    by_topic.setdefault(topic_of[r], []).append(r)

keep, land, lab = {}, set(), set()
for t, rs in by_topic.items():
    ranked = sorted(rs, key=lambda r: -cites[r])
    las = [r for r in ranked if r in la]
    n = min(TOTAL, len(ranked))
    pick = las[:int(n * LA_SHARE)]
    chosen = set(pick)
    pick += [r for r in ranked if r not in chosen][:n - len(pick)]
    keep[t] = pick
    land |= set(ranked[:LANDMARKS])
    lab |= set(ranked[:LANDMARKS]) | set(las[:LA_LABELS])
wanted = {r for rs in keep.values() for r in rs}

# pass 2: details of the chosen papers; titles from papers_text
P = {}
for line in gzip.open(data / 'papers.jsonl.gz', 'rt'):
    r = int(line[9:line.index(',')])
    if r in wanted:
        p = json.loads(line)
        P[r] = [(p['authors'] or [{'full_name': '?'}])[0]['full_name'].split(',')[0], p['n_authors'], int(p['year'] or 0)]
text = {}
if (data / 'papers_text.jsonl.gz').exists():
    for line in gzip.open(data / 'papers_text.jsonl.gz', 'rt'):
        r = int(line[9:line.index(',')])
        if r in wanted:
            p = json.loads(line)
            text[r] = ((p.get('title') or '').replace('$', ''), p.get('arxiv_eprint') or '')
print(f'{len(wanted)} papers, {len(text)} with a title', file=sys.stderr)

# citations between papers of the same topic's selection
recid = z['recid']
pos = -np.ones(len(recid), dtype=np.int64)
top = -np.ones(len(recid), dtype=np.int64)
idx = {r: i for i, r in enumerate(recid.tolist())}
for t, rs in keep.items():
    ii = [idx[r] for r in rs]
    pos[ii], top[ii] = np.arange(len(rs)), t
src, dst = z['src'], z['dst']
m = (top[src] >= 0) & (top[src] == top[dst]) & (src != dst)
es, ed, et = pos[src[m]], pos[dst[m]], top[src[m]]
order = np.argsort(et, kind='stable')
es, ed, et = es[order], ed[order], et[order]
bounds = np.searchsorted(et, np.arange(max(keep) + 2))

index = []
for t in sorted(keep):
    rs, d = keep[t], TOP[t]
    n = []
    for r in rs:
        first, nauth, year = P[r]
        title, arxiv = text.get(r, ('', ''))
        role = 'direct' if r in la else 'seed' if r in land else 'other'
        note = (f"Latin American authors from {', '.join(la[r])}." if r in la else '') + \
               (f' Among the {LANDMARKS} most cited papers of its topic.' if r in land else '')
        n.append([str(r), arxiv, title or f'INSPIRE record {r}', first, nauth, year, cites[r], role, note.strip(), 0, int(r in lab)])
    E = sorted(set(zip(es[bounds[t]:bounds[t + 1]].tolist(), ed[bounds[t]:bounds[t + 1]].tolist())))
    cnt = Counter(x[7] for x in n)
    nla = sum(1 for r in by_topic[t] if r in la)
    meta = {
        'headline': f"{d['name']}: citation network over the years",
        'dek': f"Topic {t} of the INSPIRE citation clustering ({AREA[d['area']].split(':')[0]}), {d['papers']:,} papers, median year "
               f"{d['year_median']}. Shown: its {len(n):,} most cited papers, {cnt['direct']} of them with Latin American authors "
               f"(the most cited of those come first, up to {LA_SHARE:.0%}); placed by year, every line is one paper citing another inside this set.",
        'foot': f"Source: data/ and out/clusters/ of restrepo/inspireauth10 (INSPIRE-HEP tables of 2026-11-09), made by "
                f"reproduce/topics/timelines.py. {len(n)} papers, {len(E)} citation links; {cnt['direct']} with Latin American authors "
                f"(of {nla:,} in the topic). Labels: the {LANDMARKS} most cited and the {LA_LABELS} most cited with Latin American "
                "authors. Citations are INSPIRE's totals.",
        'labels': {'direct': 'With Latin American authors', 'partial': 'Partial', 'seed': f'Top {LANDMARKS} most cited'},
        'groups': [d['name']], 'coreMinLinks': 4}
    (out / f'{t}.json').write_text(json.dumps({'n': n, 'e': [list(e) for e in E], 'meta': meta}, ensure_ascii=False, separators=(',', ':')))
    index.append({'topic': t, 'name': d['name'], 'area': d['area'], 'area_name': AREA[d['area']]})
(out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')))
size = sum(f.stat().st_size for f in out.glob('*.json'))
print(f'{len(index)} topics, {size / 1e6:.1f} MB -> {out}', file=sys.stderr)
