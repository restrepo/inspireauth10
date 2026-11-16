# inspireauth10: notes for Claude

Worldwide INSPIRE-HEP corpus (papers with 1 to 10 authors and their references), boards of indicators by country and
region, and research topics made by Leiden clustering of the citation network. Anyone can fork it and work on it
independently; the data are public on Google Drive.

## First thing in a new clone or fork

If `data/papers.jsonl.gz` is missing, follow the skill `fork-setup` (`.claude/skills/fork-setup/SKILL.md`): virtual
environment, `python reproduce/get_data.py` (tables, titles and abstracts, topic clustering, about 1.2 GB from
Drive), the citation network, and a check. Do not start the INSPIRE download (`build/build_inspire10.py`, hours) to
get data that Drive already has.

## Where things are

| What | Where | In git |
|---|---|---|
| Tables (papers, authors, institutions, experiments, titles, abstracts, topics) | `data/*.jsonl.gz` | no (Drive) |
| Author lists of the papers with more than 10 authors (optional) | `data/collab_authors.jsonl.gz`, `data/collab_profiles.jsonl.gz` | no |
| Citation network, topic clustering | `out/clusters/` | no (Drive, or rebuilt) |
| Board datasets and pages | `out/dash*/`, `out/topics_dash/`, `out/*.html` | no (rebuilt) |
| Code | `build/` (download), `reproduce/` (indicators, boards), `reproduce/topics/` (topics) | yes |
| Board templates | `reproduce/board.html`, `reproduce/topics/board/` | yes |
| Data schema | `docs/data-schema.md` | yes |
| List of the Drive files (ids, MD5) | `reproduce/drive_files.json` | yes |

## Skills of this repository

- `fork-setup`: set up a clone or fork, get the data, publish your own boards, follow upstream.
- `inspire10-boards`: the tables, indicators by country and region, the country boards.
- `inspire-topics`: the topics (network, Leiden, names, topics board) and the log of every run.
- `paper-topic-map`: where one paper's citation links fall on the topic map.

## Rules

- Large files never go into git: `data/` and `out/` are ignored. Share them through Drive (`reproduce/get_data.py`
  reads `reproduce/drive_files.json`; `reproduce/drive_manifest.py` rewrites it for whoever owns the folder).
- GitHub Actions only update `gh-pages`: `.github/workflows/pages.yml` is the only workflow. Do not add or re-enable
  workflows that do anything else (the old data workflow is parked, inactive, in `build/update-data.yml`). Make a
  release only when the owner of the repository asks for it.
- Pushing to `gh-pages`, uploading to Drive and merging pull requests publish; confirm with the user first.
  A merge to `main` also runs `.github/workflows/pages.yml`, which copies `docs/leiden.html`, the pages of
  `reproduce/topics/board/` and the site index to `gh-pages`; boards and their data are still pushed by hand.
- Read the tables line by line (or with DuckDB), never with one `json.load`: `papers.jsonl.gz` is 1.9 million lines.
- The topics are seed-dependent: work with the shared `out/clusters/topics_final.npz` unless the task is to recluster.
- Log every topic step in the step log of `.claude/skills/inspire-topics/SKILL.md`.
