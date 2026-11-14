"""Datasets of the board's Landmarks tab, from impact.json and disruption.json (landmarks.py):

landmarks.json         the 300 most cited papers, citing papers by area, with title, first author and arXiv number
disruption_top.json    papers with at least MIN_CITES citations and their CD index, with the same details
disruption_share.json  share of disruptive papers (D > 0) by five-year bin, for each area and all (area = -1),
                       over all the 76,811 papers of disruption.json

Titles and arXiv numbers come from data/papers_text.jsonl.gz and the first author from data/papers.jsonl.gz;
--titles FILE ({recid: {title, first, arxiv}}) takes precedence (for example titles fetched from INSPIRE).

Usage: python reproduce/topics/landmarks_board.py data/ out/topics_dash/ [--titles titles.json]
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

MIN_CITES, BIN = 500, 5

ap = argparse.ArgumentParser()
ap.add_argument('data')
ap.add_argument('dash')
ap.add_argument('--titles')
a = ap.parse_args()
data, dash = Path(a.data), Path(a.dash)
impact = json.load(open(dash / 'impact.json'))
cd = json.load(open(dash / 'disruption.json'))
top = [r for r in cd if r['citations'] >= MIN_CITES]
wanted = {p['recid'] for p in impact} | {r['recid'] for r in top}

info = {r: {'title': '', 'first': '', 'arxiv': ''} for r in wanted}
for line in gzip.open(data / 'papers.jsonl.gz', 'rt'):
    r = int(line[9:line.index(',')])
    if r in wanted:
        p = json.loads(line)
        n = p['n_authors']
        first = (p['authors'] or [{'full_name': '?'}])[0]['full_name'].split(',')[0]
        info[r]['first'] = first + (' et al.' if n > 2 else ' + 1' if n == 2 else '')
if (data / 'papers_text.jsonl.gz').exists():
    for line in gzip.open(data / 'papers_text.jsonl.gz', 'rt'):
        r = int(line[9:line.index(',')])
        if r in wanted:
            p = json.loads(line)
            info[r].update(title=(p.get('title') or '').replace('$', ''), arxiv=p.get('arxiv_eprint') or '')
if a.titles:
    for k, v in json.load(open(a.titles)).items():
        if int(k) in info:
            first = v['first'] + ('' if 'Collaboration' in v['first'] else ' et al.' if v['nauth'] > 2 else ' + 1' if v['nauth'] == 2 else '')
            info[int(k)].update(title=v['title'], first=first, arxiv=v['arxiv'])
print(f'{sum(1 for v in info.values() if v["title"])} of {len(info)} papers with a title', file=sys.stderr)

dump = lambda name, rows: (dash / f'{name}.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
dump('landmarks', [{**p, **info[p['recid']]} for p in impact])
dump('disruption_top', [{**r, **info[r['recid']]} for r in top])
share = []
for area in range(-1, 6):
    for b in range(1950, 2021, BIN):
        s = [r for r in cd if b <= r['year'] < b + BIN and (area < 0 or r['area'] == area)]
        if s:
            share.append({'area': area, 'bin': b, 'papers': len(s), 'cd5_pos': sum(r['cd5'] > 0 for r in s), 'cd_pos': sum(r['cd'] > 0 for r in s)})
dump('disruption_share', share)
print(f'landmarks.json {len(impact)}, disruption_top.json {len(top)}, disruption_share.json {len(share)}', file=sys.stderr)
