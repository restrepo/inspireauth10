"""Write reproduce/drive_files.json (read by get_data.py) from the repository's Google Drive folder, for maintainers.

Needs rclone with a Google Drive remote that can read the folder (`rclone config`). The folder and its files must be
shared as "anyone with the link"; get_data.py downloads them anonymously.

Usage: python reproduce/drive_manifest.py --remote gdrive: --folder 1AQav5Ho8sruJFZ3qeBSFb7_8RZyk3XNp
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Drive path -> (group, local path in the repository)
PLACES = {
    'papers.jsonl.gz': ('tables', 'data/papers.jsonl.gz'),
    'authors.jsonl.gz': ('tables', 'data/authors.jsonl.gz'),
    'institutions.jsonl.gz': ('tables', 'data/institutions.jsonl.gz'),
    'experiments.jsonl.gz': ('tables', 'data/experiments.jsonl.gz'),
    'text/papers_text.jsonl.gz': ('text', 'data/papers_text.jsonl.gz'),
    'text/papers_abstracts.jsonl.gz': ('text', 'data/papers_abstracts.jsonl.gz'),
    'topics/topics.jsonl.gz': ('topics', 'data/topics.jsonl.gz'),
    'topics/paper_topics.jsonl.gz': ('topics', 'data/paper_topics.jsonl.gz'),
    'clusters/topics_final.npz': ('topics', 'out/clusters/topics_final.npz'),
    'clusters/topics_final.json': ('topics', 'out/clusters/topics_final.json'),
    'clusters/areas_final.json': ('topics', 'out/clusters/areas_final.json'),
    'clusters/topics_multi.npz': ('topics', 'out/clusters/topics_multi.npz'),
    'clusters/topics_2010_s1.npz': ('topics', 'out/clusters/topics_2010_s1.npz'),
    'topics/papers_topics.csv.gz': ('exports', 'out/topics_csv/papers_topics.csv.gz'),
    'topics/topics.csv': ('exports', 'out/topics_csv/topics.csv'),
    'vosviewer/topics_vosviewer.json': ('exports', 'out/vosviewer/topics_vosviewer.json'),
    'vosviewer/topics_map.txt': ('exports', 'out/vosviewer/topics_map.txt'),
    'vosviewer/topics_network.txt': ('exports', 'out/vosviewer/topics_network.txt'),
    'collaborations/collab_authors.jsonl.gz': ('collaborations', 'data/collab_authors.jsonl.gz'),
    'collaborations/collab_profiles.jsonl.gz': ('collaborations', 'data/collab_profiles.jsonl.gz'),
}

ap = argparse.ArgumentParser()
ap.add_argument('--remote', default='gdrive:')
ap.add_argument('--folder', default='1AQav5Ho8sruJFZ3qeBSFb7_8RZyk3XNp')
ap.add_argument('--date', default='2026-11-09', help='date of the INSPIRE download')
ap.add_argument('--out', default=str(ROOT / 'reproduce' / 'drive_files.json'))
a = ap.parse_args()
out = subprocess.run(['rclone', 'lsjson', '-R', '--hash', '--drive-root-folder-id', a.folder, a.remote],
                     check=True, capture_output=True, text=True).stdout
found = {x['Path']: x for x in json.loads(out) if not x['IsDir']}
missing = sorted(set(PLACES) - set(found))
if missing:
    raise SystemExit(f'not in the Drive folder: {missing}')
groups = ['tables', 'text', 'topics', 'exports', 'collaborations']
files = [{'group': g, 'path': p, 'drive_path': k, 'id': found[k]['ID'], 'size': found[k]['Size'],
          'md5': found[k]['Hashes']['md5']} for k, (g, p) in PLACES.items()]
files.sort(key=lambda f: (groups.index(f['group']), f['path']))
m = {'title': f'inspireauth10 data, INSPIRE-HEP download of {a.date}', 'date': a.date,
     'folder_url': f'https://drive.google.com/drive/folders/{a.folder}', 'groups': groups, 'files': files}
Path(a.out).write_text(json.dumps(m, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'{a.out}: {len(files)} files')
