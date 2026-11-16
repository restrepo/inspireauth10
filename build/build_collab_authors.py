"""Download the author lists of the papers with more than 10 authors (the large collaborations).

papers.jsonl.gz leaves out the authors of the papers with more than 10 authors: those lines have
`collaborations` and an empty `authors`. This script adds them as two more tables in --out (see
docs/data-schema.md), kept compact because the lists hold about 17 million author entries:

    collab_authors.jsonl.gz   one line per paper with more than 10 authors of papers.jsonl.gz:
                              {"recid": 123, "authors": [[profile_id, [institution_id, ...], name], ...]}
                              in INSPIRE order; `name` is the full name only when the author has no
                              profile (profile_id null), else null
    collab_profiles.jsonl.gz  the profiles of those authors that authors.jsonl.gz does not have, with
                              the same fields as authors.jsonl.gz

It covers the papers of the papers.jsonl.gz in --out, so the two match: the download goes through
the record-number windows of build_inspire10.py (`ac 11->100000`) up to the last record of that
file and keeps only its papers. Every window is cached in build/cache/collab_authors/ (raw
responses, gzipped), so a stopped run resumes where it was; the profiles come from the cache of
build_inspire10.py (build/cache/authors/), or are fetched when that cache is missing. The download
is about 6,000 requests and a few GB of transfer: several hours.

Usage: python build/build_collab_authors.py [--cache build/cache] [--out data/] [--recids FIRST LAST]
--recids: only papers in that record range, for a test run.
Output files are byte-reproducible (no name or time in the gzip header).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_inspire10 import (  # noqa: E402
    AUTHOR_FIELDS,
    bai,
    harvest,
    log,
    read_jsonl_gz,
    ref_id,
    remove_initials,
    search,
    write_jsonl_gz,
)

ROOT = Path(__file__).resolve().parent.parent
FIELDS = 'control_number,authors.record,authors.full_name,authors.affiliations.record'
SIZE = 25  # a page of 25 papers with thousands of authors each is already tens of MB


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cache', default=str(Path(__file__).resolve().parent / 'cache'))
    ap.add_argument('--out', default=str(ROOT / 'data'))
    ap.add_argument('--recids', nargs=2, type=int, metavar=('FIRST', 'LAST'), help='record range, for a test run')
    a = ap.parse_args(argv)
    cache, out = Path(a.cache), Path(a.out)

    # the papers with more than 10 authors of papers.jsonl.gz, and the profiles it already has
    big = set()
    for p in read_jsonl_gz(out / 'papers.jsonl.gz'):
        if 'collaborations' in p and (not a.recids or a.recids[0] <= p['recid'] <= a.recids[1]):
            big.add(p['recid'])
    known = {r['profile_id'] for r in read_jsonl_gz(out / 'authors.jsonl.gz')}
    first, last = a.recids or (1, max(big))
    log(f'{len(big)} papers with more than 10 authors, records {first} to {last}')

    files = harvest('literature', lambda lo, hi: f'ac 11->100000 and recid {lo}->{hi}', FIELDS, first, last,
                    cache / 'collab_authors', size=SIZE)

    inst_country = {r['institution_id']: r['country'] for r in read_jsonl_gz(out / 'institutions.jsonl.gz')}
    first_country, seen_name, n_entries = {}, {}, [0]

    def rows():
        for path in files:
            for w in sorted(read_jsonl_gz(path), key=lambda w: w['control_number']):
                if w['control_number'] not in big:
                    continue
                authors = []
                for au in w.get('authors') or []:
                    pid = ref_id(au)
                    iids = [i for i in (ref_id(x) for x in au.get('affiliations') or []) if i]
                    authors.append([pid, iids, None if pid else au.get('full_name')])
                    if pid and pid not in known:
                        seen_name.setdefault(pid, au.get('full_name'))
                        c = next((inst_country[i] for i in iids if inst_country.get(i)), None)
                        if c:
                            first_country.setdefault(pid, c)
                n_entries[0] += len(authors)
                yield {'recid': w['control_number'], 'authors': authors}

    n = write_jsonl_gz(out / 'collab_authors.jsonl.gz', rows())
    log(f'collab_authors.jsonl.gz: {n} papers, {n_entries[0]} author entries, {len(seen_name)} new profiles')

    # the new profiles, as in authors.jsonl.gz
    prof_dir = cache / 'authors'
    if prof_dir.exists() and not a.recids:
        prof_files = sorted(prof_dir.glob('*.jsonl.gz'))
    else:
        path = cache / 'collab_test_profiles.jsonl.gz'
        todo = sorted(seen_name)
        got = []
        for i in range(0, len(todo), 100):
            got += search('authors', 'control_number:(' + ' OR '.join(todo[i:i + 100]) + ')', AUTHOR_FIELDS)
        write_jsonl_gz(path, got)
        prof_files = [path]
    from genderize_offline import guess

    def profiles():
        for path in prof_files:
            for m in sorted(read_jsonl_gz(path), key=lambda m: int(m['control_number'])):
                k = str(m['control_number'])
                if k not in seen_name:
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

    n = write_jsonl_gz(out / 'collab_profiles.jsonl.gz', profiles())
    log(f'collab_profiles.jsonl.gz: {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
