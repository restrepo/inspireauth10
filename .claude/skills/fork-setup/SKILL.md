---
name: fork-setup
description: Set up a fork or clone of restrepo/inspireauth10 so its owner can work on it independently - create the Python environment, download every table and the topic clustering from the public Google Drive folder with MD5 checks (reproduce/get_data.py), rebuild the citation network, verify that the boards and topics scripts run, publish boards on the fork's own GitHub Pages, and pull later changes from upstream. Use whenever someone opens this repository for the first time, asks to fork it, set it up, get or download the data, says data/ is empty or a script cannot find a table, wants their own copy of the boards, or asks how to stay in step with the original repository.
---

# Set up a fork of inspireauth10

Everything runs from the repository root. Large files (`data/`, `out/`) are not in git; they come from the public
Google Drive folder listed in `reproduce/drive_files.json`. Nothing here needs a key or an account other than
GitHub.

## 1. Fork and clone (once)

If the user has no copy yet, with their go-ahead (a fork is created under their GitHub account):

```bash
gh repo fork restrepo/inspireauth10 --clone      # keeps gh-pages too, so the boards come along
cd inspireauth10
```

`gh` must be signed in (`gh auth status`); signing in is the user's to do. Without `gh`: fork on github.com, then
`git clone https://github.com/OWNER/inspireauth10`. A fork keeps a remote `upstream` to the original repository
(add it if missing: `git remote add upstream https://github.com/restrepo/inspireauth10`).

## 2. Python environment

Python 3.10 or newer, about 3 GB of disk for the data and 10 GB of RAM to recluster (2 GB for everything else).

```bash
python3 -m venv .venv
.venv/bin/pip install -r reproduce/requirements.txt
```

Use `.venv/bin/python` for every command below (on Windows `.venv\Scripts\python`). If `venv` is missing (Debian:
`apt install python3-venv`), tell the user rather than installing system packages yourself.

## 3. Data from Google Drive

```bash
.venv/bin/python reproduce/get_data.py --list     # what will come, with sizes
.venv/bin/python reproduce/get_data.py            # tables + text + topics, about 1.2 GB, MD5 checked
```

| Group | Files | Size |
|---|---|---|
| `tables` | `data/papers`, `authors`, `institutions`, `experiments` (`.jsonl.gz`) | 432 MB |
| `text` | `data/papers_text` (titles, arXiv, DOIs), `data/papers_abstracts` | 702 MB |
| `topics` | `out/clusters/topics_final.npz`, `topics_final.json`, `areas_final.json`, `topics_multi.npz`, `topics_2010_s1.npz`; `data/topics`, `data/paper_topics` | 60 MB |
| `exports` | topic CSVs and VOSviewer files (`--groups exports`) | 25 MB |

Files already present with the right MD5 are skipped, so a failed run is resumed by running it again. Drive can
refuse a big file for a while when it has been downloaded many times ("returned a page instead of the file"): wait
and retry, or download it by hand from the folder link the script prints. `--check` verifies without downloading.

Then rebuild the citation network (not on Drive, about 3 minutes, 2 GB of RAM):

```bash
.venv/bin/python reproduce/topics/build_network.py data/papers.jsonl.gz out/clusters/network.npz
```

## 4. Check that it works

```bash
.venv/bin/python reproduce/get_data.py --check
.venv/bin/python -c "import numpy, igraph, leidenalg, jsonschema; print('ok')"
.venv/bin/python docs/validate_schema.py data/ --sample 50
.venv/bin/python reproduce/indicators.py data/ out/dash/ && .venv/bin/python reproduce/standalone.py out/dash/ out/board.html --set DATE=2026-11-09
```

The last line makes the worldwide board as a single HTML file; open it in a browser. The topics board and its tabs
are in the skill `inspire-topics` (section "Topics board"); the paper maps in `paper-topic-map`. Report to the user what was
downloaded, what was verified and anything that failed.

## 5. Your own boards on GitHub Pages (optional)

The fork's `gh-pages` branch already holds the original boards. To serve them from the fork, the user enables Pages
(Settings → Pages → Deploy from a branch → `gh-pages`, `/ (root)`), or, with their go-ahead:

```bash
gh api -X POST repos/OWNER/inspireauth10/pages -f 'source[branch]=gh-pages' -f 'source[path]=/'
```

The site is then `https://OWNER.github.io/inspireauth10/`. New boards are added to `gh-pages` with
`reproduce/pages_index.py` (see `inspire10-boards` and `inspire-topics`). Pages that link to the topics board take a
base URL (for example `paper_maps.py --base https://OWNER.github.io/inspireauth10/boards/DATE/topics/`).
Pushing to `gh-pages` publishes: ask before each push.

GitHub Actions are off in a new fork. The workflow `update-data.yml` downloads INSPIRE again and runs only on a
release or by hand; leave it off unless the user wants their own data updates.

## 6. Share your own derived data (optional)

To give others your new files the same way: put them in a Google Drive folder shared as "anyone with the link",
configure `rclone` for that Drive (the user's own sign-in), add the files to `PLACES` in
`reproduce/drive_manifest.py`, and run

```bash
.venv/bin/python reproduce/drive_manifest.py --remote gdrive: --folder FOLDER_ID
```

which rewrites `reproduce/drive_files.json` with ids, sizes and MD5s. Commit it; anyone with the fork can then run
`get_data.py`. Uploading to Drive publishes: ask first.

## 7. Follow the original repository

```bash
git fetch upstream
git merge upstream/main            # or open a pull request on the fork
.venv/bin/python reproduce/get_data.py --check   # new data? the manifest may list new files
```

When `reproduce/drive_files.json` changes upstream, run `get_data.py` again: it fetches only what is new or
changed. To propose changes back, push a branch to the fork and open a pull request to `restrepo/inspireauth10`.
