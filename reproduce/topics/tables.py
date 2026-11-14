"""Write the topic tables of the data (docs/data-schema.md), linked to papers.jsonl.gz by recid:

    topics.jsonl.gz        one line per topic: name, area, papers, years, papers in 2011-2015 and
                           2021-2025, the change of its share of all papers, and its trend
    paper_topics.jsonl.gz  one line per paper with a topic: up to three topics with score and links
                           (secondary.py), and its number of links to papers with a topic

Trend and share_ratio: see trends.py.

Usage: python reproduce/topics/tables.py out/topics_dash/topics.json out/clusters/topics_multi.npz data/ \\
           --clustering '{"date": "2026-11-13", ...}'
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'build'))
from build_inspire10 import write_jsonl_gz  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trends import add_trends  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('topics')
ap.add_argument('multi')
ap.add_argument('out')
ap.add_argument('--clustering', default='{}', help='JSON object describing the clustering, copied to every topic')
a = ap.parse_args()
T = json.load(open(a.topics))
clustering = json.loads(a.clustering)
add_trends(T)


def row(t):
    return {'topic': t['topic'], 'name': t['name'], 'area': t['area'], 'area_name': t['area_name'],
            'papers': t['papers'], 'year_median': t['year_median'], 'year_p10': t['year_p10'], 'year_p90': t['year_p90'],
            'papers_2011_2015': t['papers_2011_2015'], 'papers_2021_2025': t['papers_2021_2025'],
            'share_ratio': t['share_ratio'], 'trend': t['trend'], 'clustering': clustering}


out = Path(a.out)
rows = [row(t) for t in T]
n = write_jsonl_gz(out / 'topics.jsonl.gz', rows)
print(f'topics.jsonl.gz: {n};', {k: sum(r['trend'] == k for r in rows) for k in ('Growing', 'Stable', 'Shrinking')})

z = np.load(a.multi)
recid, topic, score, links, n_links = z['recid'], z['topic'], z['score'], z['links'], z['n_links']


def papers():
    for i in np.flatnonzero(topic[:, 0] >= 0):
        yield {'recid': int(recid[i]),
               'topics': [{'topic': int(topic[i, k]), 'score': round(float(score[i, k]), 4), 'links': int(links[i, k])}
                          for k in range(3) if topic[i, k] >= 0],
               'n_links': int(n_links[i])}


n = write_jsonl_gz(out / 'paper_topics.jsonl.gz', papers())
print(f'paper_topics.jsonl.gz: {n}')
