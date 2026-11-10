"""Make the board of every region of reproduce/regions.py from the tables of data/.

Usage: python reproduce/regional_boards.py data/ out/ --date 2026-11-09 [--year 2026]
writes out/dash_<slug>/ (the datasets) and out/board_<slug>_<date>.html for each region; the
slugs are latin-america, africa, asia, europe, north-america and oceania.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import indicators  # noqa: E402
import standalone  # noqa: E402
from regions import REGIONS  # noqa: E402


def slug(region):
    return region.lower().replace(' ', '-')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('data')
    ap.add_argument('out')
    ap.add_argument('--date', required=True)
    ap.add_argument('--year', type=int)
    a = ap.parse_args(argv)
    out = Path(a.out)
    for region, countries in REGIONS.items():
        dash = out / f'dash_{slug(region)}'
        indicators.main(a.data, dash, a.year, region)
        note = (f' This board counts the {len(countries)} countries of {region} '
                '(<code>reproduce/regions.py</code>); the row "' + region + '" counts the papers with an author '
                'there.')
        standalone.main(dash, out / f'board_{slug(region)}_{a.date}.html',
                        {'DATE': a.date, 'SCOPE': f'in {region}', 'SCOPE_NOTE': note, 'TOTAL': region,
                         'TITLE': region})
    return 0


if __name__ == '__main__':
    sys.exit(main())
