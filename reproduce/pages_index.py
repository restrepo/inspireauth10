"""Keep the list of dashboards served by GitHub Pages.

The site (branch gh-pages) holds one folder per board, boards/<id>/index.html,
a manifest boards.json and index.html, which lists every board from the manifest.

Usage:
  python reproduce/pages_index.py add SITE --id 2027-02-01 --board board.html \\
      --scalars dash/scalars.json --title "Data of 2027-02-01" [--note "..."] [--release v2.0.0]
  python reproduce/pages_index.py render SITE
"""
import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

CSS = """
:root { color-scheme: light dark; --fg: #1f1e1d; --muted: #6b6966; --bg: #faf9f5; --panel: #fff; --line: #e3e0d8;
  --accent: #3266ad; }
@media (prefers-color-scheme: dark) { :root { --fg: #ecebe7; --muted: #a6a39c; --bg: #1c1b19; --panel: #262523;
  --line: #3a3936; --accent: #6f9be0; } }
html { background: var(--bg); }
body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; color: var(--fg); background: var(--bg); }
main { max-width: 60rem; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-family: Georgia, "Times New Roman", serif; font-weight: 400; font-size: 30px; margin: 0 0 8px; }
p { color: var(--muted); line-height: 1.5; max-width: 70ch; }
a { color: var(--accent); }
.list { display: grid; gap: 12px; margin-top: 24px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; }
.card h2 { font-size: 18px; font-weight: 550; margin: 0 0 4px; }
.card .meta { color: var(--muted); font-size: 13px; }
.stats { display: flex; flex-wrap: wrap; gap: 8px 24px; margin-top: 10px; font-variant-numeric: tabular-nums; }
.stats div { font-size: 13px; color: var(--muted); }
.stats b { display: block; font-size: 18px; color: var(--fg); font-weight: 500; }
.tag { display: inline-block; font-size: 12px; border: 1px solid var(--line); border-radius: 99px; padding: 1px 8px;
  margin-left: 6px; color: var(--muted); vertical-align: middle; }
"""


def stats(scalars):
    s = {r['id']: r['value'] for r in json.load(open(scalars, encoding='utf-8'))}
    return {k: s[k] for k in ['papers', 'authors', 'countries', 'references', 'references_in']}


def add(site, id, board, scalars, title, note='', release=''):
    site = Path(site)
    dest = site / 'boards' / id
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(board, dest / 'index.html')
    manifest = site / 'boards.json'
    boards = json.load(open(manifest, encoding='utf-8')) if manifest.exists() else []
    boards = [b for b in boards if b['id'] != id]
    boards.append({'id': id, 'title': title, 'note': note, 'release': release,
                   'added': datetime.now(timezone.utc).strftime('%Y-%m-%d'), **stats(scalars)})
    manifest.write_text(json.dumps(boards, indent=1, ensure_ascii=False), encoding='utf-8')
    render(site)


def render(site):
    site = Path(site)
    boards = json.load(open(site / 'boards.json', encoding='utf-8'))
    boards.sort(key=lambda b: b['id'], reverse=True)  # newest data first
    latest = boards[0]['id'] if boards else None
    cards = []
    for b in boards:
        e = html.escape
        tags = ''.join(f'<span class="tag">{t}</span>' for t in
                       (['latest'] if b['id'] == latest else []) + [])
        rel = (f' · release <a href="https://github.com/restrepo/inspireauth10/releases/tag/{e(b["release"])}">'
               f'{e(b["release"])}</a>') if b.get('release') else ''
        cards.append(f"""<div class="card">
<h2><a href="boards/{e(b['id'])}/">{e(b['title'])}</a>{tags}</h2>
<div class="meta">{e(b.get('note') or '')}{rel}</div>
<div class="stats"><div><b>{b['papers']:,}</b>papers</div><div><b>{b['authors']:,}</b>authors</div>
<div><b>{b['countries']:,}</b>countries</div><div><b>{b['references']:,}</b>references</div>
<div><b>{b['references_in']:,}</b>to the corpus</div></div>
</div>""")
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HECAP Worldwide Boards</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>HECAP worldwide boards</h1>
<p>Each board shows indicators of high-energy physics, cosmology and astroparticle physics for every country, from
one download of all INSPIRE-HEP papers with up to 10 authors and their references (repository
<a href="https://github.com/restrepo/inspireauth10">restrepo/inspireauth10</a>). It extends the study of Latin America
by Morales-Alvarado, Quevedo, Ramos-Hamud and Restrepo (<a href="https://restrepo.github.io/inspireauth/">its
boards</a>). A new board is built each time a release of the repository is published. Every board is a
self-contained page that also works offline.</p>
<div class="list">
{chr(10).join(cards)}
</div>
</main>
</body>
</html>
"""
    (site / 'index.html').write_text(doc, encoding='utf-8')
    (site / '.nojekyll').write_text('', encoding='utf-8')
    print(f'{site / "index.html"}: {len(boards)} boards')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('add')
    p.add_argument('site')
    p.add_argument('--id', required=True)
    p.add_argument('--board', required=True)
    p.add_argument('--scalars', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--note', default='')
    p.add_argument('--release', default='')
    p = sub.add_parser('render')
    p.add_argument('site')
    a = ap.parse_args(argv)
    if a.cmd == 'add':
        add(a.site, a.id, a.board, a.scalars, a.title, a.note, a.release)
    else:
        render(a.site)


if __name__ == '__main__':
    main()
