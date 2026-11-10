---
name: inspire10-boards
description: Work with this repository's worldwide INSPIRE-HEP corpus (every paper with 1 to 10 authors, with authors, affiliations and the INSPIRE ids of its references flagged in_corpus; papers with more than 10 authors, outside the corpus, with their collaborations and experiment ids instead of authors) and its board - build or test the tables (build/build_inspire10.py), validate them, compute indicators by country (papers, authors, citations from all of INSPIRE or from the corpus, h-index, citation flows between countries, PhD advisor generations, gender), build the self-contained HTML board, add new indicators or tabs, or answer a question from the data. Use whenever someone working in a clone of restrepo/inspireauth10 asks for any of these.
---

# Worldwide HEP corpus and board

Run from the repository root with Python ≥ 3.10, after `pip install -r reproduce/requirements.txt`.

## Pipeline

```bash
python build/build_inspire10.py --out data/ [--recids 2000001 2019000]   # tables; --recids for a quick test
python docs/validate_schema.py data/ [--sample 50]
python reproduce/indicators.py data/ out/dash/ [--year YYYY]
python reproduce/standalone.py out/dash/ out/board.html --set DATE=YYYY-MM-DD
```

- **The download** is about 5,500 requests and takes several hours. Run it in the background. It is
  cached in `build/cache/` by windows of record numbers, so a stopped run resumes. Use a new
  `--cache` folder for a new date, because an old cache returns old data.
- **The tables** (`docs/data-schema.md`) are JSON Lines: read them line by line or with DuckDB, never
  all at once with `json.load`. Papers join authors by `profile_id` and institutions by
  `institution_id`; `references[].recid` joins papers, and `in_corpus` says whether it can.
  Papers with more than 10 authors are lines of the papers table too, with `collaborations`
  (joining `experiments` by `experiment_id`) and empty `authors`: skip them when counting the
  corpus (`'collaborations' not in p`), as `reproduce/indicators.py` does.
- **Counting rules:** the docstring of `reproduce/indicators.py`.

## Add an indicator

1. **Compute it** in `reproduce/indicators.py` `main()`, streaming the tables, and write it with
   `dump('<key>', rows)`, where `rows` is a list of flat dicts.
2. **Title it** in `reproduce/board_datasets.py`.
3. **Draw it** in `reproduce/board/index.html`:
   - a card in a tab `<section>`;
   - a `<div class="chart" data-draw="name" data-source="<key>">`;
   - `dash.draw('name', (el) => …)` with d3 v7, copying an existing drawer.
4. **Rebuild and check:** run the last two commands, open `out/board.html`, and check that every tab
   draws with no console errors.

A one-off question needs no board: read the data with a short script and state the counting rule used.

## Publish

Work on a branch and open a pull request, never on `main`. Releases tagged `v*` run the full
download, attach the tables and the board to the release, and add the board to GitHub Pages.
Never commit the tables: they are larger than git allows.
