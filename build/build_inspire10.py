"""Build the worldwide INSPIRE-HEP corpus of papers with at most 10 authors.

The corpus is every INSPIRE-HEP literature record with 1 to 10 authors (`ac 1->10`),
with its authors, their affiliations and the INSPIRE ids of its references. Each
reference is flagged `in_corpus` when it points to a paper of the corpus; references
to papers with more than 10 authors, or with no authors, are kept with `in_corpus: false`.
References that INSPIRE has not linked to a record are not included.

The papers with more than 10 authors (`ac 11->100000`) are also written to papers.jsonl.gz,
outside the corpus: instead of their authors (`authors` is empty) they have their
collaborations, each with the INSPIRE id of its experiment (`collaborations`; a paper with no
collaboration has one entry "Not Collaboration" with id "0000000"), and they keep the
countries of their authors' affiliations and their references.

It writes four gzipped JSON Lines tables to --out (see docs/data-schema.md):

    papers.jsonl.gz        one line per paper: year, citations, journal, arXiv categories,
                           authors with their affiliations (or, above 10 authors, the
                           collaborations), countries, references
    authors.jsonl.gz       one line per author profile cited by a paper: name, ids,
                           positions (with institution_id and country), advisors, gender
    institutions.jsonl.gz  one line per INSPIRE institution: name and country
    experiments.jsonl.gz   one line per INSPIRE experiment: name, collaboration, accelerator

The rules follow restrepo/inspireauth (build/build_inspire_LA.py): the year of a paper is
its journal year, else its preprint year, else its INSPIRE creation year; first_names drop
initials; genders come from genderize-offline (World Gender Name Dictionary 2.0), with the
country of the author's first affiliation in the corpus (papers in record-number order).

The download goes through record-number windows of 9,500 ids, so no query passes INSPIRE's
limit of 10,000 results. Every window is cached (raw responses, gzipped), so a stopped run
resumes where it was. The whole download is about 5,500 requests (several hours), plus about
2 GB for the papers with more than 10 authors.

Usage: python build/build_inspire10.py [--cache build/cache] [--out data/] [--recids FIRST LAST] [--shard I/N] [--cached] [--last N]
--recids: only literature records in that range, for a test run (profiles and institutions
          are then fetched only for what those papers cite).
--shard I/N: only download the windows I, I+N, I+2N, ... into the cache and stop; N jobs with
          I = 0..N-1 share the download, and a last run without --shard on the merged caches
          writes the tables (the release workflow does this, to stay under the 6 h job limit).
--cached: write the tables from the cache only, up to its last window, with no request to INSPIRE
          (to rebuild the tables of a past download with a new version of this script).
--last N: the last literature record number of the tables (default: INSPIRE's newest record, or
          with --cached the end of the last cached window); with --cached, the `last` that the
          log of the original build printed rebuilds the same papers.
Output files are byte-reproducible (no name or time in the gzip header).
"""

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = 'https://inspirehep.net/api'
ROOT = Path(__file__).resolve().parent.parent
LIT_FIELDS = ('control_number,citation_count,arxiv_eprints,publication_info,preprint_date,legacy_creation_date,'
              'document_type,references.record,authors.ids,authors.full_name,authors.affiliations,authors.record')
BIG_FIELDS = ('control_number,citation_count,arxiv_eprints,publication_info,preprint_date,legacy_creation_date,'
              'document_type,references.record,collaborations,author_count,authors.affiliations.record')
EXP_FIELDS = 'control_number,legacy_name,collaboration,name_variants,accelerator'
NO_COLLABORATION = {'collaboration': 'Not Collaboration', 'experiment_id': '0000000'}
AUTHOR_FIELDS = 'control_number,name,positions,ids,advisors'
INST_FIELDS = 'control_number,legacy_ICN,addresses'
SLEEP = 0.35  # INSPIRE allows 15 requests per 5 s
WINDOW = 9500  # record numbers per window: never more than INSPIRE's 10,000 results per query
SIZE = 500
BIG_SIZE = 100  # papers with more than 10 authors: a page of 500 can pass 50 MB
UA = 'inspireauth10 (https://github.com/restrepo/inspireauth10)'


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def get(url, tries=8):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.load(r)
            time.sleep(SLEEP)
            return out
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ConnectionError) as e:
            wait = 60 if getattr(e, 'code', None) == 429 else 5 * (k + 1)
            log(f'retry {k + 1} in {wait}s: {e} {url[:120]}')
            time.sleep(wait)
    raise RuntimeError(f'failed: {url}')


def search(kind, q, fields, size=SIZE):
    """All hits of an INSPIRE search, following `links.next`."""
    url = f'{API}/{kind}?size={size}&page=1&q={urllib.parse.quote(q)}&fields={fields}'
    hits = []
    while url:
        d = get(url)
        hits += [h['metadata'] for h in d['hits']['hits']]
        url = d.get('links', {}).get('next')
    return hits


def write_jsonl_gz(path, rows):
    """Gzipped JSON Lines, byte-reproducible; returns the number of lines."""
    n = 0
    tmp = Path(str(path) + '.tmp')
    with open(tmp, 'wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', compresslevel=6, mtime=0) as gz:
        for r in rows:
            gz.write((json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
            n += 1
    tmp.replace(path)
    return n


def read_jsonl_gz(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)


def harvest(kind, query, fields, first, last, folder, shard=(0, 1), size=SIZE):
    """Cache every record of `kind` in the windows 1-9500, 9501-19000, ... that meet first..last,
    one file per window; returns the files of those windows. With shard (I, N), only the
    windows I, I+N, ... are downloaded."""
    folder.mkdir(parents=True, exist_ok=True)
    windows = range((first - 1) // WINDOW * WINDOW + 1, last + 1, WINDOW)
    files = []
    for i, lo in enumerate(windows):
        hi = lo + WINDOW - 1
        path = folder / f'{lo:08d}-{hi:08d}.jsonl.gz'
        if i % shard[1] != shard[0]:
            continue
        if not path.exists():
            hits = search(kind, query(lo, hi), fields, size)
            write_jsonl_gz(path, hits)
            if i % 20 == 0 or i == len(windows) - 1:
                log(f'{kind}: window {i + 1}/{len(windows)} ({lo}-{hi}): {len(hits)} records')
        files.append(path)
    return files


def max_recid(kind):
    """The largest record number to harvest. Literature, authors and institutions share one
    sequence of record numbers, and sort=mostrecent orders authors by creation date, not number
    (the most recent author profile has number 1011247), so every kind is harvested up to the
    largest number of the three."""
    top = 0
    for k in ('literature', 'authors', 'institutions'):
        d = get(f'{API}/{k}?size=1&sort=mostrecent&fields=control_number')
        top = max(top, int(d['hits']['hits'][0]['metadata']['control_number']))
    return top


def ref_id(obj):
    try:
        return obj['record']['$ref'].rstrip('/').split('/')[-1]
    except (KeyError, TypeError, AttributeError):
        return None


def bai(ids):
    for i in ids or []:
        if i.get('schema') == 'INSPIRE BAI':
            return i.get('value')
    return None


def year_of(w):
    """The paper's year as text: journal year, else preprint year, else creation year, else '0000'."""
    try:
        y = w['publication_info'][0].get('year')
        if y:
            return str(y)
    except (KeyError, IndexError, TypeError):
        pass
    for k in ('preprint_date', 'legacy_creation_date'):
        if w.get(k):
            return str(w[k]).split('-')[0]
    return '0000'


def remove_initials(name):
    """first_names as in gender-genderize.ipynb of restrepo/inspireauth."""
    x = (name or '').split(', ')[-1].replace('-', ' ').strip()
    x = re.sub(r'[\|†•]', '', x).strip()
    x = re.sub(r'\.', ' ', x).strip()
    x = re.sub(r'\s\w\s', '', x).strip()
    x = re.sub(r'^\w\s', '', x).strip()
    x = re.sub(r'\s\w$', '', x).strip()
    x = re.sub(r'^\w$', '', x).strip()
    return re.sub(r'^[A-Z]{2}$', '', x)


def paper_row(w, corpus, inst_country):
    try:
        cats = w['arxiv_eprints'][0]['categories']
    except (KeyError, IndexError, TypeError):
        cats = []
    try:
        journal_id = w['publication_info'][0]['journal_record']['$ref'].split('/')[-1]
    except (KeyError, IndexError, TypeError):
        journal_id = None
    # INSPIRE links the journal record of only some publications; the title is there for all, and a
    # publication it could not parse into a journal keeps only its text
    pubs = w.get('publication_info') or []
    journal = next((p['journal_title'] for p in pubs if p.get('journal_title')), None)
    pub_note = next((p['pubinfo_freetext'] for p in pubs if p.get('pubinfo_freetext')), None)
    authors, countries = [], set()
    for a in w.get('authors') or []:
        affs = []
        for aff in a.get('affiliations') or []:
            iid = ref_id(aff)
            if aff.get('value') or iid:
                affs.append({'institution_id': iid, 'institution': aff.get('value')})
                if inst_country.get(iid):
                    countries.add(inst_country[iid])
        authors.append({'full_name': a.get('full_name'), 'author_id': bai(a.get('ids')), 'profile_id': ref_id(a),
                        'affiliations': affs})
    refs, seen = [], {w['control_number']}
    for r in w.get('references') or []:
        rid = ref_id(r)
        if rid and rid.isdigit() and int(rid) not in seen:
            seen.add(int(rid))
            refs.append({'recid': int(rid), 'in_corpus': int(rid) in corpus})
    return {'recid': w['control_number'], 'year': year_of(w), 'citation_count': w.get('citation_count'),
            'journal_id': journal_id, 'journal': journal, 'pub_note': pub_note, 'arxiv_categories': cats, 'document_type': w.get('document_type') or [],
            'n_authors': len(authors), 'countries': sorted(countries), 'authors': authors, 'references': refs}


def big_row(w, corpus, inst_country, experiment_of):
    """A paper with more than 10 authors: its collaborations instead of its authors."""
    row = paper_row(w, corpus, inst_country)
    n = len(row['authors'])
    collabs, seen = [], set()
    for c in w.get('collaborations') or []:
        name = (c.get('value') or '').strip()
        eid = ref_id(c) or experiment_of.get(name.lower())
        if name and (name, eid) not in seen:
            seen.add((name, eid))
            collabs.append({'collaboration': name, 'experiment_id': eid})
    row.update(n_authors=max(n, w.get('author_count') or 0), authors=[], collaborations=collabs or [NO_COLLABORATION])
    return row


def experiment_row(m):
    return {'experiment_id': str(m['control_number']), 'name': m.get('legacy_name'),
            'collaboration': (m.get('collaboration') or {}).get('value'),
            'accelerator': (m.get('accelerator') or {}).get('value')}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cache', default=str(Path(__file__).resolve().parent / 'cache'))
    ap.add_argument('--out', default=str(ROOT / 'data'))
    ap.add_argument('--recids', nargs=2, type=int, metavar=('FIRST', 'LAST'), help='literature range, for a test run')
    ap.add_argument('--shard', help='I/N: download one share of the windows into the cache and stop')
    ap.add_argument('--cached', action='store_true', help='write the tables from the cache only, with no request')
    ap.add_argument('--last', type=int, help='last literature record number of the tables')
    a = ap.parse_args(argv)
    cache, out = Path(a.cache), Path(a.out)
    if a.cached:
        global max_recid, search

        def max_recid(kind):  # noqa: F811 - the last record number of the cached windows
            return max(int(p.name.split('-')[1].split('.')[0]) for k in ('literature', 'authors', 'institutions')
                       for p in (cache / k).glob('*.jsonl.gz'))

        def search(*args, **kw):  # noqa: F811
            sys.exit(f'--cached: {args[:2]} is not in the cache {cache}')
    if a.shard:
        shard = tuple(map(int, a.shard.split('/')))
        harvest('literature', lambda lo, hi: f'ac 1->10 and recid {lo}->{hi}', LIT_FIELDS, 1, max_recid('literature'),
                cache / 'literature', shard)
        harvest('literature', lambda lo, hi: f'ac 11->100000 and recid {lo}->{hi}', BIG_FIELDS, 1,
                max_recid('literature'), cache / 'collaborations', shard, BIG_SIZE)
        harvest('authors', lambda lo, hi: f'control_number:[{lo} TO {hi}]', AUTHOR_FIELDS, 1, max_recid('authors'),
                cache / 'authors', shard)
        log(f'shard {a.shard} done')
        return 0
    out.mkdir(parents=True, exist_ok=True)

    # 1. literature with 1 to 10 authors, by record-number windows
    first, last = a.recids or (1, a.last or max_recid('literature'))
    log(f'literature records {first} to {last}')
    lit = harvest('literature', lambda lo, hi: f'ac 1->10 and recid {lo}->{hi}', LIT_FIELDS, first, last,
                  cache / 'literature')
    def works(p):
        return sorted((w for w in read_jsonl_gz(p) if first <= w['control_number'] <= last),
                      key=lambda w: w['control_number'])
    corpus, pids, iids = set(), set(), set()
    for p in lit:
        for w in works(p):
            corpus.add(w['control_number'])
            for au in w.get('authors') or []:
                pids.add(ref_id(au))
                iids.update(ref_id(x) for x in au.get('affiliations') or [])
    # papers with more than 10 authors, outside the corpus
    big = harvest('literature', lambda lo, hi: f'ac 11->100000 and recid {lo}->{hi}', BIG_FIELDS, first, last,
                  cache / 'collaborations', size=BIG_SIZE)
    for p in big:
        for w in works(p):
            for au in w.get('authors') or []:
                iids.update(ref_id(x) for x in au.get('affiliations') or [])
    pids.discard(None)
    iids.discard(None)
    log(f'corpus: {len(corpus)} papers, {len(pids)} profiles, {len(iids)} institutions cited')

    # experiments: the id of a collaboration that INSPIRE did not link, by its name
    exp_path = cache / 'experiments.jsonl.gz'
    if not exp_path.exists():
        write_jsonl_gz(exp_path, search('experiments', 'control_number:[1 TO 99999999]', EXP_FIELDS))
    exps = sorted(read_jsonl_gz(exp_path), key=lambda m: m['control_number'])
    experiment_of = {}  # collaboration names first, then subgroups, then other names of the experiment
    for names in (lambda m: [(m.get('collaboration') or {}).get('value')],
                  lambda m: (m.get('collaboration') or {}).get('subgroup_names') or [],
                  lambda m: m.get('name_variants') or []):
        for m in exps:
            for name in names(m):
                if name:
                    experiment_of.setdefault(name.strip().lower(), str(m['control_number']))
    n = write_jsonl_gz(out / 'experiments.jsonl.gz', (experiment_row(m) for m in exps))
    log(f'experiments.jsonl.gz: {n}')

    # 2. institutions (all of them) and author profiles (all, or the cited ones in a test run)
    if a.recids:
        def batch(kind, ids, fields, name):
            path = cache / f'{name}.jsonl.gz'
            have = {str(m['control_number']): m for m in read_jsonl_gz(path)} if path.exists() else {}
            todo = sorted(set(ids) - have.keys())
            for i in range(0, len(todo), 100):
                for m in search(kind, 'control_number:(' + ' OR '.join(todo[i:i + 100]) + ')', fields):
                    have[str(m['control_number'])] = m
            write_jsonl_gz(path, have.values())
            return [path]
        inst_files = batch('institutions', iids, INST_FIELDS, 'test_institutions')
        prof_files = batch('authors', pids, AUTHOR_FIELDS, 'test_authors')
    else:
        inst_files = harvest('institutions', lambda lo, hi: f'control_number:[{lo} TO {hi}]', INST_FIELDS,
                             1, max_recid('institutions'), cache / 'institutions')
        prof_files = harvest('authors', lambda lo, hi: f'control_number:[{lo} TO {hi}]', AUTHOR_FIELDS,
                             1, max_recid('authors'), cache / 'authors')

    insts = {}
    for p in inst_files:
        for m in read_jsonl_gz(p):
            try:
                addr = m['addresses'][0]
            except (KeyError, IndexError, TypeError):
                addr = {}
            insts[str(m['control_number'])] = {'institution_id': str(m['control_number']),
                                               'institution': m.get('legacy_ICN'),
                                               'country': addr.get('country'), 'country_code': addr.get('country_code')}
    inst_country = {k: v['country'] for k, v in insts.items()}
    n = write_jsonl_gz(out / 'institutions.jsonl.gz', (insts[k] for k in sorted(insts, key=int)))
    log(f'institutions.jsonl.gz: {n}')

    # 3. papers, in record-number order; note each profile's first affiliation country and name
    first_country, seen_name = {}, {}
    def papers():
        # lit and big share the windows, so the papers stay in record-number order
        for p, q in zip(lit, big, strict=True):
            rows = [(w['control_number'], 0, w) for w in works(p)] + [(w['control_number'], 1, w) for w in works(q)]
            for _, is_big, w in sorted(rows, key=lambda r: r[:2]):
                if is_big:
                    yield big_row(w, corpus, inst_country, experiment_of)
                    continue
                row = paper_row(w, corpus, inst_country)
                for au in row['authors']:
                    k = au['profile_id']
                    if k:
                        seen_name.setdefault(k, au['full_name'])
                        if k not in first_country:
                            c = next((inst_country.get(x['institution_id']) for x in au['affiliations']
                                      if inst_country.get(x['institution_id'])), None)
                            if c:
                                first_country[k] = c
                yield row
    n = write_jsonl_gz(out / 'papers.jsonl.gz', papers())
    log(f'papers.jsonl.gz: {n}')

    # 4. the profiles cited by the papers, with gender
    from genderize_offline import guess

    def authors():
        for p in prof_files:
            for m in sorted(read_jsonl_gz(p), key=lambda m: int(m['control_number'])):
                k = str(m['control_number'])
                if k not in pids:
                    continue
                positions = []
                for pos in m.get('positions') or []:
                    pos = dict(pos, institution_id=ref_id(pos))
                    pos['country'] = inst_country.get(pos['institution_id'])
                    positions.append(pos)
                name = (m.get('name') or {}).get('value') or seen_name.get(k)
                fn = remove_initials(name)
                g, prob, _ = guess(fn, first_country.get(k) or '')
                yield {'profile_id': k, 'author_id': bai(m.get('ids')), 'name': m.get('name'), 'ids': m.get('ids') or [],
                       'positions': positions, 'advisors': m.get('advisors') or [], 'country': first_country.get(k),
                       'first_names': fn, 'gender': g, 'gender_probability': prob}
    n = write_jsonl_gz(out / 'authors.jsonl.gz', authors())
    log(f'authors.jsonl.gz: {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
