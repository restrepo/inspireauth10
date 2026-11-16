"""The citation community of an experiment: its papers and every paper citing them, as a list of works for
citation-topics (https://github.com/restrepo/citation-topics), which finds its topics and makes its board.

Each work: id (INSPIRE record number), references (only those inside the community), year, title, abstract,
keywords, journal, categories (arXiv), countries, citations (INSPIRE citation count), url, author_count,
collaborations, authors (the first 10 names; above 10 authors from collab_authors.jsonl.gz and the profiles,
when those optional tables are in DATA), and `own`: true for the experiment's papers.

Usage: python reproduce/topics/community.py data/ out/communities/cms/works.jsonl.gz --experiment 1108642
       (CMS 1108642, ATLAS 1108541, ALICE 1110642, LHCb 1110643: experiments.jsonl.gz)
"""
import argparse
import gzip
import json
from pathlib import Path

MAX_AUTHORS = 10


def rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('data')
ap.add_argument('out')
ap.add_argument('--experiment', required=True, help='INSPIRE experiment record number')
a = ap.parse_args()
data = Path(a.data)

own = {p['recid'] for p in rows(data / 'papers.jsonl.gz')
       if any(c['experiment_id'] == a.experiment for c in p.get('collaborations') or [])}
works = {}
for p in rows(data / 'papers.jsonl.gz'):
    refs = [r['recid'] for r in p['references']]
    if p['recid'] in own or any(r in own for r in refs):
        works[p['recid']] = p
print(f'{len(own)} papers of experiment {a.experiment}, {len(works) - len(own)} citing papers')

text = {r['recid']: r for r in rows(data / 'papers_text.jsonl.gz') if r['recid'] in works}
abstract = {}
for r in rows(data / 'papers_abstracts.jsonl.gz'):
    if r['recid'] in works and r.get('abstracts'):
        abstract[r['recid']] = r['abstracts'][0].get('value')

# names of the first authors of the papers with more than 10 authors
big_names = {}
if (data / 'collab_authors.jsonl.gz').exists():
    first = {}
    for r in rows(data / 'collab_authors.jsonl.gz'):
        if r['recid'] in works:
            first[r['recid']] = r['authors'][:MAX_AUTHORS]
    wanted = {pid for x in first.values() for pid, _, _ in x if pid}
    name = {}
    for f in ('authors.jsonl.gz', 'collab_profiles.jsonl.gz'):
        for m in rows(data / f):
            if m['profile_id'] in wanted:
                name[m['profile_id']] = (m.get('name') or {}).get('value')
    big_names = {k: [name.get(pid) or nm for pid, _, nm in x if name.get(pid) or nm] for k, x in first.items()}

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
with gzip.open(a.out, 'wt', encoding='utf-8') as f:
    for k in sorted(works):
        p, t = works[k], text.get(k, {})
        collabs = [c['collaboration'] for c in p.get('collaborations') or [] if c['experiment_id'] != '0000000']
        authors = [x['full_name'] for x in p['authors'][:MAX_AUTHORS]] or big_names.get(k, [])
        w = {'id': k, 'references': [r['recid'] for r in p['references'] if r['recid'] in works and r['recid'] != k],
             'year': int(p['year']) if p['year'] != '0000' else None, 'title': t.get('title'),
             'abstract': abstract.get(k),
             'keywords': [x.get('value') if isinstance(x, dict) else x for x in t.get('keywords') or []],
             'journal': p.get('journal'),
             'categories': p['arxiv_categories'], 'countries': p['countries'], 'citations': p['citation_count'],
             'url': f'https://inspirehep.net/literature/{k}', 'author_count': p['n_authors'],
             'collaborations': collabs, 'authors': authors, 'own': k in own}
        f.write(json.dumps(w, ensure_ascii=False, separators=(',', ':')) + '\n')
print(f'{a.out}: {len(works)} works')
