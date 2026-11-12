# Data schema

`build/build_inspire10.py` writes four gzipped JSON Lines tables (one JSON object per line).
They are too large for git, so they are not in the repository: a release attaches them (see
the README). [`inspire10.schema.json`](inspire10.schema.json) is the machine-readable version
(JSON Schema 2020-12, one definition per table), and `python docs/validate_schema.py data/`
checks the files against it (it needs `pip install jsonschema`).

| File | One line per | Joins |
|---|---|---|
| `papers.jsonl.gz` | INSPIRE-HEP literature record with at least one author (the corpus: 1 to 10 authors; above 10, with collaborations instead of authors) | `authors[].profile_id` → authors, `authors[].affiliations[].institution_id` → institutions, `collaborations[].experiment_id` → experiments, `references[].recid` → papers |
| `authors.jsonl.gz` | author profile that appears in a paper | `positions[].institution_id` → institutions |
| `institutions.jsonl.gz` | INSPIRE-HEP institution | |
| `experiments.jsonl.gz` | INSPIRE-HEP experiment | |

```python
import gzip, json

def rows(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            yield json.loads(line)

papers = {p['recid']: p for p in rows('data/papers.jsonl.gz')}   # several GB in memory: stream when you can
```

## The corpus

The corpus is every INSPIRE-HEP literature record with 1 to 10 authors (`ac 1->10`), of any document type,
with or without affiliations. This is the same limit as restrepo/inspireauth: papers of large
collaborations are left out of it.

The papers with more than 10 authors (`ac 11->100000`) are lines of `papers.jsonl.gz` too, outside
the corpus. They have the same fields, but `authors` is empty and `collaborations` lists their
collaborations; `countries` still holds the countries of all their authors' institutions. Only
these papers have `collaborations`, so `'collaborations' not in p` selects the corpus.

## `papers.jsonl.gz`

| Field | Type | Description |
|---|---|---|
| `recid` | integer | INSPIRE literature record number: `https://inspirehep.net/api/literature/<recid>`. |
| `year` | string | Journal year, else preprint year, else INSPIRE creation year; `"0000"` when none is known. |
| `citation_count` | integer, null | Citations in all of INSPIRE when the data were downloaded, including citing papers outside the corpus. |
| `journal_id` | string, null | INSPIRE journal record number of the first publication, or null. INSPIRE links a journal record for only some publications (about half before 2021), so null does not mean unpublished. |
| `journal` | string, null | Abbreviated journal title of the first publication that has one (`Phys.Rev.D`), or null when INSPIRE knows no journal. |
| `pub_note` | string, null | INSPIRE's free-text publication note (`pubinfo_freetext`) of the first publication that has one, kept when INSPIRE could not parse it into a journal (`Physics of Complex Systems, 2022, vol. 3, no. 3`), else null. |
| `arxiv_categories` | list of strings | arXiv categories of the first e-print, primary first; empty if not on arXiv. |
| `document_type` | list of strings | INSPIRE document types, e.g. `article`, `conference paper`, `thesis`. |
| `n_authors` | integer | Number of authors (1 to 10 in the corpus; more above). |
| `countries` | list of strings | Countries of the authors' institutions, sorted, each once; empty when no affiliation has a known country. |
| `authors` | list | The authors in INSPIRE order (below); empty above 10 authors. |
| `collaborations` | list | Only above 10 authors: `{collaboration, experiment_id}` per collaboration, with the INSPIRE experiment record number (e.g. CMS → `1108642`, https://inspirehep.net/api/experiments/1108642), taken from the paper's link or, when INSPIRE did not link it, from the experiment of that collaboration name (null if there is none). A paper with no collaboration has `[{"collaboration": "Not Collaboration", "experiment_id": "0000000"}]`. |
| `references` | list | The references INSPIRE links to a literature record (below). |

### `authors[]`

| Field | Type | Description |
|---|---|---|
| `full_name` | string | Name as written in the paper, `"Family, Given"`. |
| `author_id` | string, null | INSPIRE BAI in this paper, e.g. `D.Restrepo.1`. |
| `profile_id` | string, null | INSPIRE author record number: a line of `authors.jsonl.gz`. |
| `affiliations` | list | `{institution_id, institution}`: the record number (or null) and the short name of each affiliation in this paper. |

### `references[]`

| Field | Type | Description |
|---|---|---|
| `recid` | integer | INSPIRE literature record number of the cited paper. |
| `in_corpus` | boolean | `true` when the cited paper is in the corpus (1 to 10 authors); `false` when it is outside: more than 10 authors (also a line of `papers.jsonl.gz`, with `collaborations`), no authors, or not a literature record of this download. |

Each cited record appears once, in the order of the paper's reference list; a paper never cites
itself. References that INSPIRE has not matched to a record are not included (about a quarter of
recent reference lists).

## `authors.jsonl.gz`

Only profiles that appear as `profile_id` in a paper.

| Field | Type | Description |
|---|---|---|
| `profile_id` | string | INSPIRE author record number. |
| `author_id` | string, null | INSPIRE BAI of the profile. |
| `name` | object, null | INSPIRE name block: `value`, `preferred_name`, `name_variants`, `native_names`, … |
| `ids` | list | `{schema, value}`: INSPIRE BAI, INSPIRE ID, ORCID, … |
| `positions` | list | INSPIRE positions (`institution`, `rank`, `start_date`, `end_date`, `current`, `record`, …), each with `institution_id` and the `country` of that institution added. |
| `advisors` | list | Thesis advisors: `name`, `degree_type` (`phd`, `master`, …), `ids`, `record`. |
| `country` | string, null | Country of the author's first affiliation with a known country, in record-number order of the papers. |
| `first_names` | string | Given names without initials; empty when only initials are known. |
| `gender` | string | `male`, `female` or `unknown`, inferred from `first_names` and `country` with genderize-offline (World Gender Name Dictionary 2.0). An estimate, not self-reported gender. |
| `gender_probability` | number | 0.5–1, or 0 for `unknown`. Count a gender only at 0.9 or more. |

E-mail addresses are not included.

## `institutions.jsonl.gz`

| Field | Type | Description |
|---|---|---|
| `institution_id` | string | INSPIRE institution record number. |
| `institution` | string, null | INSPIRE short name (ICN), e.g. `Antioquia U.` |
| `country` | string, null | Country of the first address. |
| `country_code` | string, null | Its ISO 3166-1 alpha-2 code. |

## `experiments.jsonl.gz`

| Field | Type | Description |
|---|---|---|
| `experiment_id` | string | INSPIRE experiment record number. |
| `name` | string, null | INSPIRE legacy name, e.g. `CERN-LHC-CMS`. |
| `collaboration` | string, null | Name of its collaboration, e.g. `CMS`. |
| `accelerator` | string, null | e.g. `LHC`. |

## Rules and pitfalls

- **Countries** come from institutions, not from people. A paper belongs to every country of its
  authors' affiliations.
- **Citations:** `citation_count` counts citing papers in all of INSPIRE. Citations from the
  corpus, or citations up to a given year, come from the `references` of the papers (each citing
  paper has a `year`).
- **Published or not:** a paper is published when it has a `journal` or, failing that, a
  `pub_note`; with neither, INSPIRE knows no publication: a preprint never published, or not yet
  (many of the last two years). Do not use `journal_id` for this: INSPIRE links a journal record
  for only about half of the published papers before 2021. INSPIRE's `refereed` flag is not in the
  tables (the download does not ask for it). `year` is the journal year of a published paper.
- **Rank at publication:** restrepo/inspireauth stores the rank held when each paper was published.
  Here it can be computed from `positions` (same institution, paper year between start and end).
- **Size:** `papers.jsonl.gz` holds tens of millions of references. Read it line by line, or load
  it into DuckDB (`read_json('data/papers.jsonl.gz', format='newline_delimited')`).
