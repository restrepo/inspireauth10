"""Check the four tables of data/ against docs/inspire10.schema.json, line by line.

Usage: python docs/validate_schema.py [data/] [--sample N]
--sample N: check only every N-th line (the full papers table takes a while).
Needs: pip install jsonschema
"""
import gzip
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
TABLES = {'papers.jsonl.gz': 'paper', 'authors.jsonl.gz': 'author', 'institutions.jsonl.gz': 'institution',
          'experiments.jsonl.gz': 'experiment'}


def main(folder='data', sample=1):
    schema = json.loads((HERE / 'inspire10.schema.json').read_text(encoding='utf-8'))
    bad = 0
    for name, d in TABLES.items():
        v = Draft202012Validator({**schema, '$ref': f'#/$defs/{d}'})
        n = errors = 0
        with gzip.open(Path(folder) / name, 'rt', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i % sample:
                    continue
                n += 1
                for e in v.iter_errors(json.loads(line)):
                    errors += 1
                    if errors <= 5:
                        print(f'{name} line {i + 1}: {"/".join(map(str, e.absolute_path))}: {e.message[:150]}')
        print(f'{name}: {n} lines checked, {errors} errors')
        bad += errors
    return 1 if bad else 0


if __name__ == '__main__':
    argv = sys.argv[1:]
    s = 1
    if '--sample' in argv:
        i = argv.index('--sample')
        s = int(argv[i + 1])
        del argv[i:i + 2]
    sys.exit(main(*argv[:1], sample=s))
