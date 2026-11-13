"""Write the topics board as one self-contained HTML file, with the builder of the other boards.

Usage: python reproduce/topics/board.py out/topics_dash/ out/topics_2026-11-09.html --date 2026-11-09
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import standalone  # noqa: E402
from board_datasets import DATASETS  # noqa: E402  (reproduce/topics/board_datasets.py, first on the path)

ap = argparse.ArgumentParser()
ap.add_argument('dash')
ap.add_argument('out')
ap.add_argument('--date', required=True)
a = ap.parse_args()
standalone.main(a.dash, a.out, {'DATE': a.date, 'TITLE': 'topics'}, page=HERE / 'board/index.html', datasets=DATASETS,
                credit='Computed by <code>reproduce/topics/</code> of restrepo/inspireauth10 from the tables in '
                       '<code>data/</code> (INSPIRE-HEP, CC0) and their citation network, clustered with Leiden '
                       '(igraph 1.0, leidenalg 0.12).')
