# inspireauth10

> **Boards:** [**restrepo.github.io/inspireauth10**](https://restrepo.github.io/inspireauth10/): indicators for every country and region, and the
> [topics board](https://restrepo.github.io/inspireauth10/boards/2026-11-09/topics/) (304 citation-based topics, landmark papers,
> citation timelines), in the browser, with nothing to install.

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
| `papers.jsonl.gz` | paper: year, citations, journal (title, INSPIRE record and publication note, so you can tell whether it was published), arXiv categories, document type, countries, authors with affiliations (above 10 authors: collaborations), references |
| `authors.jsonl.gz` | author profile: name, ids, positions, PhD advisors, inferred gender |
| `institutions.jsonl.gz` | INSPIRE institution: name and country |
| `experiments.jsonl.gz` | INSPIRE experiment: name, collaboration, accelerator |

Each reference is an INSPIRE record id flagged `in_corpus`: `true` when the cited paper is in the
corpus (1 to 10 authors), `false` when it is outside it. With the references you can count citations
from the corpus only, citations up to any year, and citation flows between countries.

The tables are too large for git (hundreds of MB), so they are not in the repository. A release
attaches them, and they can be built locally (below).

### Download

No release has been made yet. The tables of the local download of **2026-11-09** (literature
records up to 3213510, the data of the boards on GitHub Pages) are on Google Drive, public, in the
folder [`inspireauth10_2026-11-09`](https://drive.google.com/drive/folders/1AQav5Ho8sruJFZ3qeBSFb7_8RZyk3XNp):

| File | Size | MD5 |
|---|---|---|
| [`papers.jsonl.gz`](https://drive.google.com/file/d/1VKd-X-zV4xCrRZJtWXHMko259s0nBPWe/view) | 406 MB | `eb3590c74f8b3a71ed27093b53f20448` |
| [`authors.jsonl.gz`](https://drive.google.com/file/d/1W-c6_ZQUXAq5HQpd42WlDIUNbpvklMr2/view) | 25.5 MB | `76e2693f9ca8ea5bbc20ed406fbf1dbb` |
| [`institutions.jsonl.gz`](https://drive.google.com/file/d/1Hz1j9W4eVf5FzEOkyzlS8R0qwnxlcbUH/view) | 207 kB | `3ad7c9b85360ed1220d9c108f5a3ede0` |
| [`experiments.jsonl.gz`](https://drive.google.com/file/d/1_RIPAMfXOOe2nXlIrodLEOUKLC6GTEgz/view) | 43 kB | `21fff3661aafe0e7355a7e2e3e8516b6` |

```bash
mkdir -p data
curl -L -o data/papers.jsonl.gz 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1VKd-X-zV4xCrRZJtWXHMko259s0nBPWe'
curl -L -o data/authors.jsonl.gz 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1W-c6_ZQUXAq5HQpd42WlDIUNbpvklMr2'
curl -L -o data/institutions.jsonl.gz 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1Hz1j9W4eVf5FzEOkyzlS8R0qwnxlcbUH'
curl -L -o data/experiments.jsonl.gz 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1_RIPAMfXOOe2nXlIrodLEOUKLC6GTEgz'
md5sum data/*.jsonl.gz
```

## Building

```bash
pip install -r reproduce/requirements.txt
python build/build_inspire10.py --out data/            # several hours; cached in build/cache/, resumes if stopped
python docs/validate_schema.py data/ --sample 50
python reproduce/indicators.py data/ out/dash/
python reproduce/standalone.py out/dash/ out/board.html --set DATE=YYYY-MM-DD
```

For a quick test, `--recids 2000001 2019000` builds the tables of two windows of record numbers.

To rebuild the tables of a past download with a newer version of the build script, without
asking INSPIRE for anything, add `--cached`: it writes them from `build/cache/` up to its last
window.

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

Besides the tabs of the worldwide board, the regional boards recover three tabs of restrepo/inspireauth's
Latin American board: **Regional trends** (the region's share of the papers and citations of the
corpus, by year), **Ranks & mobility** (where the authors of each country held the ranks under which
they published, and where the region's PhDs go next) and the co-authorship heatmaps of
**Collaborations**. Every board has the **Correlations** of authors, papers and citations per million
inhabitants with R&D spending (Figs. 15–17 of the paper; log-log axes by default, with a power-law fit, or linear) and the **Gender** tab (female share per
year and by rank).

The Overview tab of the worldwide board also shows the papers per year by arXiv category for the
world or each of the six regions, the arXiv categories of the 30 leading countries, and the document
types (article, conference paper, thesis…, published in a journal or not) against arXiv, with the share of articles never published, year by year.

Population and R&D spending (% of GDP) come from the World Bank, in
[`reproduce/world_bank.csv`](reproduce/world_bank.csv); `python reproduce/world_bank.py` downloads them again.

## Topics

[`reproduce/topics/`](reproduce/topics) defines research topics from scratch, by Leiden clustering of
the direct-citation network of all the papers of the tables (the method CWTS used for the OpenAlex
topics, with no reference to any outside taxonomy): for the tables of 2026-11-09, 304 named topics
in 6 areas, the most typical of four seeds. A separate board,
[HECAP topics](https://restrepo.github.io/inspireauth10/boards/2026-11-09/topics/), shows them: a map
of the topics, each topic's papers per year, journals, countries and most cited papers, the growing
and shrinking topics, and the topics of each country. The skill `.claude/skills/inspire-topics` has
the commands and the log of every run.

Each paper has up to three topics. The main topic is the paper's own topic and has score 1. The
second and third are the two other topics with the most citation links (references and citing
papers), each scored as its number of links divided by the links to the main topic, capped at 1.
`reproduce/topics/secondary.py` computes them. The tables are on Google Drive in the folder
[`topics`](https://drive.google.com/drive/folders/1vWw2pQJzx7WeUhgdvc0zJuaF0AtmD_ON) of the backup
above:

| File | Size | MD5 |
|---|---|---|
| [`papers_topics.csv.gz`](https://drive.google.com/file/d/1wwUjXf9DLSyt8dBSvOjzMy9zWiAR63MK/view) | 21 MB | `5afa1a868165184be38af2bd26a697ec` |
| [`topics.csv`](https://drive.google.com/file/d/1KC7kY2oGBti0P0EkcQiTTV-Ddr5eZN8A/view) | 31 kB | `0ed70fffb1b5efd23acef3f9e2a6f77b` |

- `papers_topics.csv.gz` has one row per paper with a topic, 1,583,351 in all. Its columns are
  `recid`, then `topic_k`, `score_k` and `links_k` for k = 1, 2, 3 (empty when the paper has no
  such topic), and `n_links`.
- `topics.csv` gives the number, name, area and paper count of each of the 304 topics.

The 288,870 papers that have no citation link get no topic.

```bash
curl -L -o papers_topics.csv.gz 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1wwUjXf9DLSyt8dBSvOjzMy9zWiAR63MK'
curl -L -o topics.csv 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1KC7kY2oGBti0P0EkcQiTTV-Ddr5eZN8A'
```

The graph of topics, for [VOSviewer](https://www.vosviewer.com/) (1.6.16+ or VOSviewer Online), is
on Google Drive in the folder
[`vosviewer`](https://drive.google.com/drive/folders/19x_PdTijtNm3qeNNv0ZylPaX2mm92iT0) of the
backup above. It has 304 topics as items, with the area as cluster, papers and citation links as
weights, and the median year as score. It also has 39,502 links between topics, each weighted by the
citation links between their papers. `reproduce/topics/vosviewer.py` writes these files:

| File | Size | MD5 |
|---|---|---|
| [`topics_vosviewer.json`](https://drive.google.com/file/d/1k15nF6PStcnobW4nW53f97H44riRwQxU/view) (VOSviewer JSON) | 2.2 MB | `1bac4c0b1d83f1034cd164f6452ad37c` |
| [`topics_map.txt`](https://drive.google.com/file/d/1NbhTXkxYiRY9OI3Qg2UEpdvr7spKzyiV/view) (map file) | 18 kB | `cd1f8690b49513976990e437ad6cc01c` |
| [`topics_network.txt`](https://drive.google.com/file/d/1FoxTPVx_YkbJbKFeCb53pLh_F1BQSyrS/view) (network file) | 408 kB | `7db10cb76ac38c06b66d887cc63aaf57` |

```bash
curl -L -o topics_vosviewer.json 'https://drive.usercontent.google.com/download?export=download&confirm=t&id=1k15nF6PStcnobW4nW53f97H44riRwQxU'
```

**Open it in VOSviewer Online** (in the browser, nothing to install):

- One click: [open the topics graph in VOSviewer Online](https://app.vosviewer.com/?json=https://restrepo.github.io/inspireauth10/vosviewer/topics_vosviewer.json).
  The `json=` parameter loads the copy of `topics_vosviewer.json` on the GitHub Pages site
  (https://restrepo.github.io/inspireauth10/vosviewer/topics_vosviewer.json, the same file as on Drive).
- From a downloaded file: go to https://app.vosviewer.com/, click **Open** (top left), keep
  **File type: VOSviewer JSON file**, choose `topics_vosviewer.json` and click **OK**.

The map shows 304 topics coloured by area (the 6 clusters), sized by papers, with 39,502 links. In the
**Visualization** panel, **Color** switches from the clusters to the median year (the score), and
**Minimum strength** or **Maximum links** thins out the links. VOSviewer for the desktop (1.6.16+) opens
the same JSON file, and also the map and network text files.

The repository includes a skill for Claude Code (`.claude/skills/inspire10-boards`), so you can
ask for new indicators in plain language after cloning it.

## Licence

Data from INSPIRE-HEP (CC0). Genders come from the World Gender Name Dictionary 2.0 (CC0) through
genderize-offline; they are name-based estimates, not self-reported gender.
