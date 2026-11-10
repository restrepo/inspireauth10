# inspireauth10

Every INSPIRE-HEP paper with **1 to 10 authors**, worldwide, with its authors, their affiliations and
the INSPIRE ids of its **references**, and a board of indicators for every country. This is the
worldwide counterpart of [restrepo/inspireauth](https://github.com/restrepo/inspireauth) (Latin
America, the data of *Statistical Analysis of Scientific Metrics in High Energy, Cosmology, and
Astroparticle Physics in Latin America*, M. Morales-Alvarado, F. Quevedo, M. Ramos-Hamud,
D. Restrepo) and of [restrepo/inspireauth_CfA](https://github.com/restrepo/inspireauth_CfA) (Africa).
It uses the same limit of 10 authors for its corpus. The papers with more than 10 authors are in
the tables too, outside the corpus: instead of their authors they have their collaborations, with
the INSPIRE id of each experiment (CMS: [1108642](https://inspirehep.net/api/experiments/1108642)),
and they keep the countries of their authors' institutions.

## The data

Four gzipped JSON Lines tables, described in [`docs/data-schema.md`](docs/data-schema.md):

| File | One line per |
|---|---|
| `papers.jsonl.gz` | paper: year, citations, journal, arXiv categories, document type, countries, authors with affiliations (above 10 authors: collaborations), references |
| `authors.jsonl.gz` | author profile: name, ids, positions, PhD advisors, inferred gender |
| `institutions.jsonl.gz` | INSPIRE institution: name and country |
| `experiments.jsonl.gz` | INSPIRE experiment: name, collaboration, accelerator |

Each reference is an INSPIRE record id flagged `in_corpus`: `true` when the cited paper is in the
corpus (1 to 10 authors), `false` when it is outside it. With the references you can count citations
from the corpus only, citations up to any year, and citation flows between countries.

The tables are too large for git (hundreds of MB), so they are not in the repository. A release
attaches them, and they can be built locally (below).

## Building

```bash
pip install -r reproduce/requirements.txt
python build/build_inspire10.py --out data/            # several hours; cached in build/cache/, resumes if stopped
python docs/validate_schema.py data/ --sample 50
python reproduce/indicators.py data/ out/dash/
python reproduce/standalone.py out/dash/ out/board.html --set DATE=YYYY-MM-DD
```

For a quick test, `--recids 2000001 2019000` builds the tables of two windows of record numbers.

## Releases

Publishing a GitHub release whose tag starts with `v` runs
[`update-data.yml`](.github/workflows/update-data.yml):

1. four jobs share the download (`--shard I/4`), since the whole download is longer than a job may run;
2. a last job merges their caches, writes and validates the tables, and builds the board;
3. it attaches the tables and the board to the release;
4. it adds the board to GitHub Pages (branch `gh-pages`, `reproduce/pages_index.py`).

A pull request that touches the code runs a small test, with nothing published. No release has
been made yet: the boards of a local build of 2026-11-09 were added to the
[GitHub Pages site](https://restrepo.github.io/inspireauth10/) by hand, with `pages_index.py add`.

## Regional boards

`python reproduce/regional_boards.py data/ out/ --date YYYY-MM-DD` makes a board for each region of
[`reproduce/regions.py`](reproduce/regions.py): Latin America (the 18 countries of restrepo/inspireauth),
Africa, Asia, Europe, North America and Oceania. Each counts the countries of its region, and its
total row counts the papers with an author in the region. A release builds them too and adds them
to GitHub Pages next to the worldwide board.

The repository includes a skill for Claude Code (`.claude/skills/inspire10-boards`), so you can
ask for new indicators in plain language after cloning it.

## Licence

Data from INSPIRE-HEP (CC0). Genders come from the World Gender Name Dictionary 2.0 (CC0) through
genderize-offline; they are name-based estimates, not self-reported gender.
