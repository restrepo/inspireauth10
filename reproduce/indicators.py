"""Compute the board's datasets from the three tables of build/build_inspire10.py.

Counting rules (docs/data-schema.md has the fields):
- the corpus is the papers with 1 to 10 authors; the papers with more than 10 authors, which
  papers.jsonl.gz also holds (with collaborations instead of authors), are counted only in
  `collaborations` and the scalar `big_papers`;
- a country's papers are the papers with an author affiliated to one of its institutions
  (`countries` of the paper), each counted once;
- its authors are the distinct authors with such an affiliation (profile, else BAI, else full name);
- citations are INSPIRE's `citation_count` (all of INSPIRE) summed over the country's papers,
  and the h-index is computed on them; corpus citations count only citing papers of the corpus,
  from the `references` of every paper;
- citation flows: each reference from a paper of the corpus to another counts once for every
  pair (citing country, cited country) of the two papers;
- gender: authors with a profile and gender probability 0.9 or more, by their country;
- PhD advisors: as in restrepo/inspireauth, advisors (degree phd, linked by record or INSPIRE ID)
  count in every country where their profile has a position; generations are the longest chain
  of students below them, and parent advisors have no registered PhD advisor.

Usage: python reproduce/indicators.py data/ out/dash/ [--year 2026]
--year: the last year of the per-year counts (default: the current year)
"""
import gzip
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

TOP_FLOWS = 20
TOP_COLLABS = 40


def rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def corpus_rows(data):
    """The papers of the corpus: those with 1 to 10 authors."""
    return (p for p in rows(data / 'papers.jsonl.gz') if not p.get('collaborations'))


def h_index(cits):
    cits = sorted(cits, reverse=True)
    return sum(1 for i, c in enumerate(cits) if c >= i + 1)


def main(data, outdir, year=None):
    data, out = Path(data), Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    year = year or datetime.now().year

    def dump(name, value):
        json.dump(value, open(out / f'{name}.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
        print(name, len(value))

    # pass 1: per-country papers, authors, citations, years; countries of every paper
    papers, authors, cits, years = Counter(), defaultdict(set), defaultdict(list), defaultdict(Counter)
    countries_of, n_refs, n_refs_in = {}, 0, 0
    for p in corpus_rows(data):
        cs = p['countries']
        if cs:
            countries_of[p['recid']] = tuple(cs)
        y = int(p['year']) if str(p['year']).isdigit() else None
        for c in cs + ['World']:
            papers[c] += 1
            cits[c].append(p['citation_count'] or 0)
            if y and 1950 <= y <= year:
                years[c][y] += 1
        n_refs += len(p['references'])
        n_refs_in += sum(1 for r in p['references'] if r['in_corpus'])
        for a in p['authors']:
            authors['World'].add(a['profile_id'] or a['author_id'] or a['full_name'])
    # authors of a country: those with an affiliation to one of its institutions
    inst_country = {r['institution_id']: r['country'] for r in rows(data / 'institutions.jsonl.gz')}
    for p in corpus_rows(data):
        for a in p['authors']:
            key = a['profile_id'] or a['author_id'] or a['full_name']
            for aff in a['affiliations']:
                c = inst_country.get(aff['institution_id'])
                if c:
                    authors[c].add(key)

    # papers with more than 10 authors, by collaboration
    n_big, collab, collab_cits, collab_countries = 0, Counter(), Counter(), defaultdict(set)
    for p in rows(data / 'papers.jsonl.gz'):
        if not p.get('collaborations'):
            continue
        n_big += 1
        for c in p['collaborations']:
            k = c['collaboration'], c['experiment_id']
            collab[k] += 1
            collab_cits[k] += p['citation_count'] or 0
            collab_countries[k].update(p['countries'])

    # pass 2: references between papers of the corpus
    corpus_cits, flows = Counter(), Counter()
    for p in corpus_rows(data):
        src = countries_of.get(p['recid'], ())
        for r in p['references']:
            if not r['in_corpus']:
                continue
            dst = countries_of.get(r['recid'], ())
            corpus_cits['World'] += 1
            for b in dst:
                corpus_cits[b] += 1
                for a in src:
                    flows[a, b] += 1

    # authors' gender and PhD advisors
    gender = defaultdict(Counter)
    profiles = {}
    for a in rows(data / 'authors.jsonl.gz'):
        profiles[a['profile_id']] = a
        if a['gender_probability'] >= 0.9 and a['gender'] in ('male', 'female'):
            for c in {a['country'], 'World'} - {None}:
                gender[c][a['gender']] += 1

    ref = {}
    for k, a in profiles.items():
        ref[k] = k
        for i in a['ids']:
            if i.get('schema') == 'INSPIRE ID':
                ref[i['value']] = k
    students, with_advisor = defaultdict(set), set()
    for k, a in profiles.items():
        for ad in a['advisors']:
            if ad.get('degree_type') != 'phd':
                continue
            with_advisor.add(k)
            keys = [(ad.get('record') or {}).get('$ref', '').rsplit('/', 1)[-1],
                    *(i['value'] for i in ad.get('ids') or [] if i.get('schema') == 'INSPIRE ID')]
            t = next((ref[x] for x in keys if x in ref), None)
            if t and t != k:
                students[t].add(k)
    gens = {}
    def generations(a):
        # iterative longest chain below a, ignoring cycles
        stack, onpath = [(a, iter(sorted(students.get(a, ()))))], {a}
        best = {}
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                onpath.discard(node)
                gens[node] = best.get(node, 0)
                if stack:
                    parent = stack[-1][0]
                    best[parent] = max(best.get(parent, 0), gens[node] + 1)
                continue
            if nxt in onpath:
                continue
            if nxt in gens:
                best[node] = max(best.get(node, 0), gens[nxt] + 1)
                continue
            onpath.add(nxt)
            stack.append((nxt, iter(sorted(students.get(nxt, ())))))
        return gens[a]
    tree = defaultdict(Counter)
    for k in students:
        g = generations(k) if k not in gens else gens[k]
        if not g:
            continue
        cs = {p['country'] for p in profiles[k]['positions'] if p.get('country')}
        for c in [*cs, 'World'] if cs else []:
            tree[c]['parent', g] += k not in with_advisor
            tree[c]['all', g] += 1

    # datasets
    names = sorted((c for c in papers if c != 'World'), key=lambda c: -papers[c])
    top = names[:TOP_FLOWS]
    dump('scalars', [
        {'id': 'papers', 'label': 'Papers with 1 to 10 authors', 'value': papers['World']},
        {'id': 'authors', 'label': 'Distinct authors', 'value': len(authors['World'])},
        {'id': 'profiles', 'label': 'Authors with an INSPIRE profile', 'value': len(profiles)},
        {'id': 'countries', 'label': 'Countries with papers', 'value': len(names)},
        {'id': 'references', 'label': 'References linked to an INSPIRE record', 'value': n_refs},
        {'id': 'references_in', 'label': 'References to papers of the corpus', 'value': n_refs_in},
        {'id': 'big_papers', 'label': 'Papers with more than 10 authors (outside the corpus)', 'value': n_big},
        {'id': 'year', 'label': 'Last year counted', 'value': year},
    ])
    dump('collaborations', [{'collaboration': k[0], 'experiment_id': k[1], 'papers': n, 'citations': collab_cits[k],
                             'countries': len(collab_countries[k])}
                            for k, n in sorted(collab.items(), key=lambda kv: (-kv[1], kv[0][0]))[:TOP_COLLABS]])

    def gpct(c):
        n = gender[c]['male'] + gender[c]['female']
        return (round(100 * gender[c]['female'] / n, 1) if n else None), n
    country_rows = []
    for c in ['World', *names]:
        f, n = gpct(c)
        recv = sum(flows[a, c] for a in names) if c != 'World' else None
        country_rows.append({
            'country': c, 'papers': papers[c], 'authors': len(authors[c]), 'citations': sum(cits[c]),
            'citations_per_paper': round(sum(cits[c]) / papers[c], 2) if papers[c] else 0,
            'h_index': h_index(cits[c]), 'corpus_citations': corpus_cits[c],
            'self_citation_pct': round(100 * flows[c, c] / recv, 1) if recv else None,
            'female_pct': f, 'gender_n': n})
    dump('countries', country_rows)
    dump('papers_per_year', [{'country': c, 'year': y, 'papers': n}
                             for c in ['World', *names] for y, n in sorted(years[c].items())])
    flow_rows = []
    for b in top:
        recv = sum(flows[a, b] for a in names)
        for a in top:
            flow_rows.append({'citing': a, 'cited': b, 'n': flows[a, b],
                              'pct': round(100 * flows[a, b] / recv, 2) if recv else 0})
    dump('citation_flows', flow_rows)
    dump('advisor_generations', [
        {'country': c, 'generations': g, 'parents': v['parent', g], 'advisors': v['all', g]}
        for c, v in sorted(tree.items(), key=lambda kv: -sum(n for (k, _), n in kv[1].items() if k == 'all'))
        for g in sorted({g for _, g in v}) if v['all', g]])


if __name__ == '__main__':
    argv = sys.argv[1:]
    y = None
    if '--year' in argv:
        i = argv.index('--year')
        y = int(argv[i + 1])
        del argv[i:i + 2]
    main(*argv[:2], y)
