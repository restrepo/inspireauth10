"""Build the text tables of the papers: titles, arXiv numbers, DOIs, keywords and abstracts.

Every paper of papers.jsonl.gz (INSPIRE-HEP literature records with at least one author,
`ac 1->100000`) gets one line in each table, linked to papers.jsonl.gz by `recid`:

    papers_text.jsonl.gz       title, arxiv_eprint, dois, keywords (with their schema and source)
    papers_abstracts.jsonl.gz  abstracts (each with its source), only for papers that have one

The text is kept out of papers.jsonl.gz so that the indicators, which read every paper, do not
have to read it. The download goes through the same record-number windows as build_inspire10.py,
cached in --cache/text (gzipped raw responses), so a stopped run resumes where it was; it is
about 3,500 requests (a few hours). Only the record numbers present in --papers are written.

Usage: python build/build_papers_text.py [--cache build/cache] [--papers data/papers.jsonl.gz] [--out data/]
                                         [--last N] [--recids FIRST LAST] [--cached]
--last N: the last literature record number (default: the largest recid of --papers).
--recids: only that range, for a test run.
--cached: write the tables from the cache only, with no request to INSPIRE.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_inspire10 as b  # noqa: E402

TEXT_FIELDS = 'control_number,titles,arxiv_eprints,dois,keywords,abstracts'


def text_row(w):
    titles = w.get('titles') or []
    eprints = w.get('arxiv_eprints') or []
    dois = list(dict.fromkeys(d['value'] for d in w.get('dois') or [] if d.get('value')))
    keywords = [{k: v for k, v in (('value', kw.get('value')), ('schema', kw.get('schema')), ('source', kw.get('source')))
                 if v} for kw in w.get('keywords') or [] if kw.get('value')]
    return {'recid': w['control_number'], 'title': titles[0].get('title') if titles else None,
            'arxiv_eprint': eprints[0].get('value') if eprints else None, 'dois': dois, 'keywords': keywords}


def abstract_row(w):
    abstracts = [{k: v for k, v in (('value', x.get('value')), ('source', x.get('source'))) if v}
                 for x in w.get('abstracts') or [] if x.get('value')]
    return {'recid': w['control_number'], 'abstracts': abstracts} if abstracts else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cache', default=str(Path(__file__).resolve().parent / 'cache'))
    ap.add_argument('--papers', default=str(b.ROOT / 'data' / 'papers.jsonl.gz'))
    ap.add_argument('--out', default=str(b.ROOT / 'data'))
    ap.add_argument('--last', type=int)
    ap.add_argument('--recids', nargs=2, type=int, metavar=('FIRST', 'LAST'))
    ap.add_argument('--cached', action='store_true')
    a = ap.parse_args(argv)
    cache, out = Path(a.cache), Path(a.out)
    if a.cached:
        def search(*args, **kw):
            sys.exit(f'--cached: {args[:2]} is not in the cache {cache / "text"}')
        b.search = search

    recids = {p['recid'] for p in b.read_jsonl_gz(a.papers)}
    first, last = a.recids or (1, a.last or max(recids))
    b.log(f'{len(recids)} papers in {a.papers}; literature records {first} to {last}')
    files = b.harvest('literature', lambda lo, hi: f'ac 1->100000 and recid {lo}->{hi}', TEXT_FIELDS, first, last,
                      cache / 'text')

    def works():
        for p in files:
            for w in sorted(b.read_jsonl_gz(p), key=lambda w: w['control_number']):
                if first <= w['control_number'] <= last and w['control_number'] in recids:
                    yield w

    out.mkdir(parents=True, exist_ok=True)
    seen = set()

    def texts():
        for w in works():
            seen.add(w['control_number'])
            yield text_row(w)
    n = b.write_jsonl_gz(out / 'papers_text.jsonl.gz', texts())
    want = {r for r in recids if first <= r <= last}
    b.log(f'papers_text.jsonl.gz: {n} (papers of {a.papers} in the range with no text record: {len(want - seen)})')
    n = b.write_jsonl_gz(out / 'papers_abstracts.jsonl.gz', (r for r in map(abstract_row, works()) if r))
    b.log(f'papers_abstracts.jsonl.gz: {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
