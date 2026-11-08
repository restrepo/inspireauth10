# Data schema

`build/build_inspire10.py` writes three gzipped JSON Lines tables (one JSON object per line).
They are too large for git, so they are not in the repository: a release attaches them (see
the README). [`inspire10.schema.json`](inspire10.schema.json) is the machine-readable version
(JSON Schema 2020-12, one definition per table), and `python docs/validate_schema.py data/`
checks the files against it (it needs `pip install jsonschema`).

| File | One line per | Joins |
|---|---|---|
| `papers.jsonl.gz` | INSPIRE-HEP literature record with 1 to 10 authors | `authors[].profile_id` → authors, `authors[].affiliations[].institution_id` → institutions, `references[].recid` → papers |
| `authors.jsonl.gz` | author profile that appears in a paper | `positions[].institution_id` → institutions |
| `institutions.jsonl.gz` | INSPIRE-HEP institution | |

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
collaborations are left out.

## `papers.jsonl.gz`

| Field | Type | Description |
|---|---|---|
| `recid` | integer | INSPIRE literature record number: `https://inspirehep.net/api/literature/<recid>`. |
| `year` | string | Journal year, else preprint year, else INSPIRE creation year; `"0000"` when none is known. |
| `citation_count` | integer, null | Citations in all of INSPIRE when the data were downloaded, including citing papers outside the corpus. |
| `journal_id` | string, null | INSPIRE journal record number of the first publication, or null. |
| `arxiv_categories` | list of strings | arXiv categories of the first e-print, primary first; empty if not on arXiv. |
| `document_type` | list of strings | INSPIRE document types, e.g. `article`, `conference paper`, `thesis`. |
| `n_authors` | integer | Number of authors (1 to 10). |
| `countries` | list of strings | Countries of the authors' institutions, sorted, each once; empty when no affiliation has a known country. |
| `authors` | list | The authors in INSPIRE order (below). |
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
| `in_corpus` | boolean | `true` when the cited paper is in the corpus (a line of `papers.jsonl.gz`); `false` when it is outside: more than 10 authors, no authors, or not a literature record of this download. |

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

## Rules and pitfalls

- **Countries** come from institutions, not from people. A paper belongs to every country of its
  authors' affiliations.
- **Citations:** `citation_count` counts citing papers in all of INSPIRE. Citations from the
  corpus, or citations up to a given year, come from the `references` of the papers (each citing
  paper has a `year`).
- **Rank at publication:** restrepo/inspireauth stores the rank held when each paper was published.
  Here it can be computed from `positions` (same institution, paper year between start and end).
- **Size:** `papers.jsonl.gz` holds tens of millions of references. Read it line by line, or load
  it into DuckDB (`read_json('data/papers.jsonl.gz', format='newline_delimited')`).
