"""Download the data of this repository from its public Google Drive folder, checking every file's MD5.

The files and their Drive ids are listed in reproduce/drive_files.json, by group:
  tables    the four tables of the corpus (data/papers, authors, institutions, experiments), 432 MB
  text      titles, arXiv numbers, DOIs and abstracts of every paper (data/papers_text, papers_abstracts), 702 MB
  topics    the topic clustering of the boards (out/clusters/topics_final.npz, its names, second and third topics,
            the 2010 clustering) and the topic tables (data/topics, paper_topics), 60 MB
  exports   the topic tables as CSV and the VOSviewer files (out/topics_csv/, out/vosviewer/), 25 MB
Files already present with the right MD5 are skipped, so the script can be run again after a failure.
Needs only Python's standard library and anonymous access to Google Drive.

Usage: python reproduce/get_data.py                 # tables, text and topics
       python reproduce/get_data.py --groups tables  # only some groups
       python reproduce/get_data.py --list           # what would be downloaded, with sizes
       python reproduce/get_data.py --check          # verify the local files only
"""
import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://drive.usercontent.google.com/download?export=download&confirm=t&id={}'


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def size(n):
    return f'{n / 1e6:,.1f} MB' if n >= 1e6 else f'{n / 1e3:,.0f} kB'


def fetch(item, dest):
    tmp = dest.with_name(dest.name + '.part')
    req = urllib.request.Request(URL.format(item['id']), headers={'User-Agent': 'inspireauth10-get-data'})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, 'wb') as f:
        if 'text/html' in r.headers.get('Content-Type', ''):
            raise RuntimeError('Google Drive returned a page instead of the file (quota or permission)')
        done = 0
        while block := r.read(1 << 20):
            f.write(block)
            done += len(block)
            print(f'\r  {dest.relative_to(ROOT)}: {size(done)} of {size(item["size"])}', end='', flush=True)
    print()
    if md5(tmp) != item['md5']:
        tmp.unlink()
        raise RuntimeError('MD5 does not match the manifest; try again')
    tmp.replace(dest)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--groups', nargs='+', default=['tables', 'text', 'topics'])
    ap.add_argument('--manifest', default=str(ROOT / 'reproduce' / 'drive_files.json'))
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    m = json.loads(Path(a.manifest).read_text(encoding='utf-8'))
    groups = m['groups'] if a.groups == ['all'] else a.groups
    unknown = set(groups) - set(m['groups'])
    if unknown:
        sys.exit(f'unknown group(s) {sorted(unknown)}; choose from {list(m["groups"])}')
    items = [x for x in m['files'] if x['group'] in groups]
    print(f'{m["title"]}\nDrive folder: {m["folder_url"]}\n{len(items)} files, {size(sum(x["size"] for x in items))}')
    if a.list:
        for x in items:
            print(f'  {x["group"]:8s} {x["path"]:45s} {size(x["size"]):>10s}')
        return
    need = sum(x['size'] for x in items)
    free = shutil.disk_usage(ROOT).free
    if not a.check and free < need:
        sys.exit(f'not enough disk space: {size(free)} free, {size(need)} needed')
    bad = 0
    for x in items:
        dest = ROOT / x['path']
        if dest.exists() and dest.stat().st_size == x['size'] and md5(dest) == x['md5']:
            print(f'  ok        {x["path"]}')
            continue
        if a.check:
            print(f'  {"wrong" if dest.exists() else "missing":9s} {x["path"]}')
            bad += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            fetch(x, dest)
        except Exception as e:  # noqa: BLE001  (report and go on with the other files)
            print(f'\n  FAILED    {x["path"]}: {e}')
            bad += 1
    if bad:
        sys.exit(f'{bad} file(s) missing or wrong; run the same command again')
    print('All files present and verified.')


if __name__ == '__main__':
    main()
