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
  of students below them, and parent advisors have no registered PhD advisor;
- per million inhabitants: the World Bank population of reproduce/world_bank.csv (latest year),
  for countries of 1 million inhabitants or more; the correlations (Figs. 15-17 of the Latin
  American paper) fit a line to authors, papers and citations per million against the average
  R&D expenditure (% of GDP, 1996 on) over those countries;
- arXiv categories: the papers of each year by the main (first) arXiv category of the paper,
  without its subject class (astro-ph.CO is astro-ph), with nucl-th and nucl-ex as nucl, for the
  total and the countries of the region (the world: the six regions of reproduce/regions.py, each
  counting the papers with an author there, and the 30 countries with the most papers), 1991 on;
- document types: the papers of the total of each year, 1991 on, by document type (the first
  INSPIRE type: article, conference paper, thesis, proceedings, book (with book chapter) or other),
  whether they are published (a journal or a publication note), and main arXiv category;
- female share per year (Fig. 21): distinct profiles with gender probability 0.9 or more with a
  paper of the year affiliated to the country; by rank (Table 8): profiles holding a declared
  rank (in the region, for a regional board) in a year in which they published.

Regional boards only, as restrepo/inspireauth's Latin American board:
- the region's share of the corpus papers and of their citations, by year (Figs. 1-2);
- ranks and mobility (Figs. 4, 37-39): for each country, the positions with a declared rank of the
  profiles with a ranked position in the country, held where the author published a paper (same
  institution, a year of the position), by where the position was: the same country, another
  country of the region, or outside it; each position counts once;
- PhD destinations: profiles with a PhD position in a country of the region, by where their
  current (else latest) later position is, not counting student or visitor ranks;
- co-authorship (Figs. 22-23): the share of a row country's papers co-authored with the column
  country, for the region's 20 countries with the most papers and the 10 countries outside the
  region with the most papers co-authored with it.

Regional boards (--region, the countries of reproduce/regions.py): the countries are those of
the region, and the total row, named after the region instead of World, counts the papers with an
author in the region, the authors affiliated there, the corpus citations received by papers with
an author there, the profiles whose first affiliation is there, and the advisors with a position
there. Each country's share of citations from the same country still counts citations from every
country. The references, profiles and papers with more than 10 authors of the scalars are those
of the region's papers and profiles.

Usage: python reproduce/indicators.py data/ out/dash/ [--year 2026] [--region "Latin America"]
--year: the last year of the per-year counts (default: the current year)
--region: a region of reproduce/regions.py (default: the world)
"""
import csv
import gzip
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from regions import REGIONS

HERE = Path(__file__).resolve().parent
TOP_FLOWS = 20
TOP_COLLABS = 40
TOP_GENDER = 30
DOCTYPES = ['article', 'conference paper', 'thesis', 'proceedings', 'book']
CATEGORIES = ['hep-ph', 'hep-th', 'hep-ex', 'hep-lat', 'astro-ph', 'gr-qc', 'nucl']
MIN_POP = 1_000_000
RANK_GROUPS = {'Undergraduate, Master, PhD': {'UNDERGRADUATE', 'MASTER', 'PHD'}, 'Postdoc': {'POSTDOC'},
               'Junior or Staff': {'JUNIOR', 'STAFF'}, 'Senior': {'SENIOR'}}
MOBILITY_RANKS = ['UNDERGRADUATE', 'PHD', 'POSTDOC', 'JUNIOR', 'SENIOR']


def rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def corpus_rows(data):
    """The papers of the corpus: those with 1 to 10 authors."""
    return (p for p in rows(data / 'papers.jsonl.gz') if not p.get('collaborations'))


def span(pos, year):
    """(first, last) year of a position: its end, else the current year if current, else its start."""
    try:
        start = int(str(pos['start_date'])[:4])
        end = int(str(pos['end_date'])[:4]) if pos.get('end_date') else year if pos.get('current') else start
    except (KeyError, ValueError):
        return None
    return (start, end) if 1900 <= start <= end else None


def bits(first, last):
    """The bit mask of the years first..last, bit 0 being 1900."""
    return ((1 << (last - first + 1)) - 1) << (first - 1900)


def linfit(xs, ys):
    n, mx, my = len(xs), sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    slope = sxy / sxx if sxx else 0
    return {'slope': slope, 'intercept': my - slope * mx, 'r2': sxy * sxy / (sxx * syy) if sxx and syy else 0, 'n': n}


def frac(genders):
    """n, female % and its 95% margin of a {key: gender} or a Counter of genders."""
    c = Counter(genders.values()) if isinstance(genders, dict) else genders
    n = c['male'] + c['female']
    f = c['female'] / n if n else 0
    return n, round(100 * f, 2), round(100 * 1.96 * math.sqrt(f * (1 - f) / n), 2) if n else 0


def doctype(p):
    """The first INSPIRE document type of a paper, grouped as the board's chart."""
    t = (p['document_type'] or ['other'])[0]
    t = 'book' if t == 'book chapter' else t
    return t if t in DOCTYPES else 'other'


def category(p):
    """The main arXiv category of a paper, grouped as the board's chart."""
    if not p['arxiv_categories']:
        return 'none'
    c = p['arxiv_categories'][0].split('.')[0]
    c = 'nucl' if c.startswith('nucl') else c
    return c if c in CATEGORIES else 'other'


def h_index(cits):
    cits = sorted(cits, reverse=True)
    return sum(1 for i, c in enumerate(cits) if c >= i + 1)


def main(data, outdir, year=None, region=None):
    data, out = Path(data), Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    year = year or datetime.now().year
    TOTAL = region or 'World'
    inside = set(REGIONS[region]) if region else None

    def total(cs):
        """[TOTAL] when the countries cs are in the region (always for the world), else []."""
        return [TOTAL] if inside is None or inside.intersection(cs) else []

    def dump(name, value):
        json.dump(value, open(out / f'{name}.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
        print(name, len(value))

    # profiles, their genders, and those with a ranked position in each country of the region
    profiles = {a['profile_id']: a for a in rows(data / 'authors.jsonl.gz')}
    gender_of = {k: a['gender'] for k, a in profiles.items()
                 if a['gender_probability'] >= 0.9 and a['gender'] in ('male', 'female')}
    with_rank = defaultdict(set)
    if inside is not None:
        for k, a in profiles.items():
            for pos in a['positions']:
                if pos.get('rank') and pos.get('country') in inside:
                    with_rank[pos['country']].add(k)
    ranked = set().union(*with_rank.values())

    # pass 1: per-country papers, authors, citations, years; countries of every paper; the world
    # and the region by year; co-authorship of the region's countries
    papers, authors, cits, years = Counter(), defaultdict(set), defaultdict(list), defaultdict(Counter)
    countries_of, n_refs, n_refs_in = {}, 0, 0
    world_year, world_cits_year, total_cits_year, pairs = Counter(), Counter(), Counter(), Counter()
    cat_year = defaultdict(Counter)
    doc_year = defaultdict(Counter)
    region_of = {c: r for r, cs in REGIONS.items() for c in cs}
    for p in corpus_rows(data):
        cs = p['countries']
        if cs:
            countries_of[p['recid']] = tuple(cs)
        y = int(p['year']) if str(p['year']).isdigit() else None
        if y and 1950 <= y <= year:
            world_year[y] += 1
            world_cits_year[y] += p['citation_count'] or 0
            if total(cs):
                total_cits_year[y] += p['citation_count'] or 0
        for c in cs + total(cs):
            papers[c] += 1
            cits[c].append(p['citation_count'] or 0)
            if y and 1950 <= y <= year:
                years[c][y] += 1
                if y >= 1991:
                    cat_year[c, y][category(p)] += 1
        if total(cs) and y and 1991 <= y <= year:
            doc_year[doctype(p), bool(p.get('journal') or p.get('pub_note')), y][category(p)] += 1
        if inside is None and y and 1991 <= y <= year:
            for r in {region_of[c] for c in cs if c in region_of}:
                cat_year[r, y][category(p)] += 1
        if inside is not None:
            for a in inside.intersection(cs):
                for b in cs:
                    pairs[a, b] += 1
        if total(cs):
            n_refs += len(p['references'])
            n_refs_in += sum(1 for r in p['references'] if r['in_corpus'])
        if inside is None:
            for a in p['authors']:
                authors['World'].add(a['profile_id'] or a['author_id'] or a['full_name'])
    # authors of a country: those with an affiliation to one of its institutions; the profiles
    # with gender of each country and year; the years each profile published, and published at
    # each institution (bit masks)
    inst_country, code_of = {}, {}
    for r in rows(data / 'institutions.jsonl.gz'):
        inst_country[r['institution_id']] = r['country']
        if r['country'] and r.get('country_code'):
            code_of[r['country']] = r['country_code']
    gender_year, pub_years, inst_years = defaultdict(dict), Counter(), Counter()
    for p in corpus_rows(data):
        y = int(p['year']) if str(p['year']).isdigit() else None
        y = y if y and 1900 <= y <= year else None
        for a in p['authors']:
            key = a['profile_id'] or a['author_id'] or a['full_name']
            pid, g = a['profile_id'], gender_of.get(a['profile_id'])
            if pid and y:
                pub_years[pid] |= 1 << (y - 1900)
            cs = set()
            for aff in a['affiliations']:
                c = inst_country.get(aff['institution_id'])
                if c:
                    cs.add(c)
                    authors[c].add(key)
                    if inside is not None and c in inside:
                        authors[TOTAL].add(key)
                if y and pid in ranked:
                    inst_years[pid, aff['institution_id']] |= 1 << (y - 1900)
            if g and y and y >= 1970:
                for c in cs | set(total(cs)):
                    gender_year[c, y][pid] = g

    # papers with more than 10 authors, by collaboration
    n_big, collab, collab_cits, collab_countries = 0, Counter(), Counter(), defaultdict(set)
    for p in rows(data / 'papers.jsonl.gz'):
        if not p.get('collaborations') or not total(p['countries']):
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
            if inside is None or inside.intersection(dst):
                corpus_cits[TOTAL] += 1
            for b in dst:
                corpus_cits[b] += 1
                for a in src:
                    flows[a, b] += 1

    # authors' gender and PhD advisors
    gender = defaultdict(Counter)
    n_profiles = 0
    for a in profiles.values():
        in_total = total([a['country']] if a['country'] else [])
        n_profiles += bool(in_total)
        if a['gender_probability'] >= 0.9 and a['gender'] in ('male', 'female'):
            for c in {a['country'], *in_total} - {None}:
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
        for c in [*sorted(cs), *total(cs)] if cs else []:
            tree[c]['parent', g] += k not in with_advisor
            tree[c]['all', g] += 1

    # datasets
    every = [c for c in papers if c != TOTAL]
    names = sorted((c for c in every if inside is None or c in inside), key=lambda c: -papers[c])
    top = names[:TOP_FLOWS]
    dump('scalars', [
        {'id': 'papers', 'label': 'Papers with 1 to 10 authors', 'value': papers[TOTAL]},
        {'id': 'authors', 'label': 'Distinct authors', 'value': len(authors[TOTAL])},
        {'id': 'profiles', 'label': 'Authors with an INSPIRE profile', 'value': n_profiles},
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
    wb = {r['country_code']: r for r in csv.DictReader(open(HERE / 'world_bank.csv', encoding='utf-8'))}
    def context(c):
        """population, R&D (% of GDP) and ISO3 code of a country, or the population of the total."""
        if c == TOTAL:
            return sum(int(r['population']) for k, r in wb.items()
                       if inside is None or any(code_of.get(x) == k for x in inside)), None, None
        r = wb.get(code_of.get(c))
        return (int(r['population']), float(r['rd_avg']) if r['rd_avg'] else None, r['iso3']) if r else (None, None, None)
    country_rows = []
    for c in [TOTAL, *names]:
        f, n = gpct(c)
        recv = sum(flows[a, c] for a in every) if c != TOTAL else None
        pop, rd, iso3 = context(c)
        pmi = (lambda v: round(1e6 * v / pop, 2)) if pop and pop >= MIN_POP else (lambda v: None)
        country_rows.append({
            'country': c, 'code': iso3, 'population': pop, 'rd_avg': rd,
            'papers_pmi': pmi(papers[c]), 'authors_pmi': pmi(len(authors[c])), 'citations_pmi': pmi(sum(cits[c])),
            'papers': papers[c], 'authors': len(authors[c]), 'citations': sum(cits[c]),
            'citations_per_paper': round(sum(cits[c]) / papers[c], 2) if papers[c] else 0,
            'h_index': h_index(cits[c]), 'corpus_citations': corpus_cits[c],
            'self_citation_pct': round(100 * flows[c, c] / recv, 1) if recv else None,
            'female_pct': f, 'gender_n': n})
    dump('countries', country_rows)
    fits = []
    for m in ('authors_pmi', 'papers_pmi', 'citations_pmi'):
        pts = [(r['rd_avg'], r[m]) for r in country_rows[1:] if r['rd_avg'] is not None and r[m] is not None]
        if len(pts) > 2:
            fits.append({'fit': f'{m}|rd_avg', **{k: round(v, 6) for k, v in linfit(*zip(*pts)).items()}})
    dump('fits', fits)

    # gender by year and by rank
    gy = []
    for c in [TOTAL, *names[:TOP_GENDER]]:
        for y in range(1970, year + 1):
            n, f, ci = frac(gender_year.get((c, y), {}))
            if n >= 10:
                gy.append({'country': c, 'year': y, 'authors': n, 'female_pct': f, 'ci95': ci})
    dump('gender_year', gy)
    rank_group = defaultdict(dict)
    for k, g in gender_of.items():
        mask = pub_years.get(k)
        if not mask:
            continue
        for pos in profiles[k]['positions']:
            sp = span(pos, year)
            if not pos.get('rank') or not sp or not mask & bits(*sp):
                continue
            if inside is not None and pos.get('country') not in inside:
                continue
            rank_group['All ranks'][k] = g
            for name, ks in RANK_GROUPS.items():
                if pos['rank'] in ks:
                    rank_group[name][k] = g
    dump('gender_rank', [{'group': k, 'authors': n, 'female_pct': f, 'ci95': ci}
                         for k in ['All ranks', *RANK_GROUPS] for n, f, ci in [frac(rank_group[k])]])

    # regional boards only: share of the world, ranks and mobility, PhD destinations, co-authorship
    def where(c, home):
        return 'same' if c == home else 'region' if c in inside else 'outside'
    share, mobility, dest, coauthors = [], [], defaultdict(Counter), []
    if inside is not None:
        share = [{'year': y, 'papers': years[TOTAL][y], 'world_papers': world_year[y],
                  'pct_papers': round(100 * years[TOTAL][y] / world_year[y], 3),
                  'pct_citations': round(100 * total_cits_year[y] / world_cits_year[y], 3) if world_cits_year[y] else None}
                 for y in sorted(world_year)]
        for c in names:
            counts, seen = Counter(), set()
            for k in sorted(with_rank[c]):
                for pos in profiles[k]['positions']:
                    rk, sp = pos.get('rank'), span(pos, year)
                    if rk not in MOBILITY_RANKS or not sp or not pos.get('country'):
                        continue
                    if not inst_years.get((k, pos.get('institution_id')), 0) & bits(*sp):
                        continue
                    key = k, pos.get('institution_id'), rk, pos.get('start_date'), pos.get('end_date')
                    if key not in seen:
                        seen.add(key)
                        counts[rk, where(pos['country'], c)] += 1
            mobility += [{'country': c, 'rank': rk, 'where': w, 'n': counts[rk, w]}
                         for rk in MOBILITY_RANKS for w in ('same', 'region', 'outside') if counts[rk, w]]
        for k, a in profiles.items():
            ps = a['positions']
            phd = [p for p in ps if p.get('rank') == 'PHD' and p.get('country') in inside]
            if not phd:
                continue
            c = phd[0]['country']
            later = [p for p in ps if p is not phd[0] and p.get('rank') not in ('PHD', 'MASTER', 'UNDERGRADUATE', 'VISITOR')]
            now = [p for p in later if p.get('current')] or sorted(later, key=lambda p: (span(p, year) or (0,))[0])[-1:]
            w = 'none' if not now else where(now[0]['country'], c) if now[0].get('country') else 'unknown'
            dest[c][w] += 1
            dest[TOTAL][w] += 1
        inner = names[:TOP_FLOWS]
        outer = sorted({b for (a, b) in pairs if b not in inside}, key=lambda b: (-sum(pairs[a, b] for a in inside), b))[:10]
        coauthors = [{'scope': scope, 'row': a, 'col': b, 'pct': round(100 * pairs[a, b] / papers[a], 1)}
                     for scope, cols in (('region', inner), ('world', outer)) for a in inner for b in cols]
    dump('region_share', share)
    dump('mobility', mobility)
    dump('phd_destination', [{'country': c, 'destination': w, 'authors': v[w], 'total': sum(v.values())}
                             for c, v in sorted(dest.items(), key=lambda kv: (-sum(kv[1].values()), kv[0]))
                             for w in ('same', 'region', 'outside', 'unknown', 'none') if v[w]])
    dump('coauthorship', coauthors)
    scope = {TOTAL: 'total', **({r: 'region' for r in REGIONS} if inside is None else {})}
    dump('categories_year', [{'country': c, 'scope': scope.get(c, 'country'), 'year': y,
                              **{k: cat_year[c, y][k] for k in [*CATEGORIES, 'other', 'none']}}
                             for c in [TOTAL, *(names if inside is not None else [*REGIONS, *names[:TOP_GENDER]])]
                             for y in range(1991, year + 1) if cat_year[c, y]])
    dump('doctype_year', [{'type': t, 'journal': j, 'year': y, **{k: v[k] for k in [*CATEGORIES, 'other', 'none']}}
                          for (t, j, y), v in sorted(doc_year.items(), key=lambda kv: ([*DOCTYPES, 'other'].index(kv[0][0]), not kv[0][1], kv[0][2]))])
    dump('papers_per_year', [{'country': c, 'year': y, 'papers': n}
                             for c in [TOTAL, *names] for y, n in sorted(years[c].items())])
    flow_rows = []
    for b in top:
        recv = sum(flows[a, b] for a in every)
        for a in top:
            flow_rows.append({'citing': a, 'cited': b, 'n': flows[a, b],
                              'pct': round(100 * flows[a, b] / recv, 2) if recv else 0})
    dump('citation_flows', flow_rows)
    dump('advisor_generations', [
        {'country': c, 'generations': g, 'parents': v['parent', g], 'advisors': v['all', g]}
        for c, v in sorted(tree.items(), key=lambda kv: -sum(n for (k, _), n in kv[1].items() if k == 'all'))
        if c == TOTAL or inside is None or c in inside
        for g in sorted({g for _, g in v}) if v['all', g]])


if __name__ == '__main__':
    argv = sys.argv[1:]
    opt = {}
    for k in ('--year', '--region'):
        if k in argv:
            i = argv.index(k)
            opt[k] = argv[i + 1]
            del argv[i:i + 2]
    if opt.get('--region') and opt['--region'] not in REGIONS:
        sys.exit(f"unknown region {opt['--region']!r}: one of {', '.join(REGIONS)}")
    main(*argv[:2], int(opt['--year']) if '--year' in opt else None, opt.get('--region'))
