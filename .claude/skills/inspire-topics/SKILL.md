---
name: inspire-topics
description: Build research topics for the INSPIRE-HEP corpus of this repository from scratch, by Leiden clustering of its direct-citation network (the CWTS method behind OpenAlex topics, but with no reference to OpenAlex's taxonomy) - build the network from data/papers.jsonl.gz, cluster it into topics and broad areas, choose the resolution, describe each cluster (arXiv categories, journals, years, countries, most cited papers with their INSPIRE titles), name the clusters, and keep the step log. Use whenever someone working in a clone of restrepo/inspireauth10 asks for topics, fields, clusters or a classification of the HEP papers, to rerun or change the clustering, to compare clusters with arXiv categories, or for the state of the topic work.
---

# Topics of the HEP corpus by citation clustering

Run from the repository root with the tables in `data/` (README, "Download"). Needs
`pip install igraph leidenalg numpy` (the shared environment `/home/restrepo/prog/claude/.venv` has
igraph 1.0.0 and leidenalg 0.12.0). Outputs go to `out/clusters/` (not in git).

## Method

The topics come only from this data. Papers are nodes; an undirected link joins two papers when one
cites the other (`references[].recid` of `papers.jsonl.gz` that are papers of the table, all of
them, the corpus of 1 to 10 authors and the collaboration papers above 10). Leiden clustering
(Traag, Waltman & van Eck 2019) of that direct-citation network, as in Waltman & van Eck (2012)
and in the CWTS classification behind OpenAlex topics. Nothing is mapped to OpenAlex, ASJC or
arXiv: names come from each cluster's own papers.

1. **Network** (`reproduce/topics/build_network.py`): node index = line of `papers.jsonl.gz`;
   `network.npz` holds `recid`, `year`, `n_authors`, `cats` (main arXiv category) and the directed
   edges `src -> dst` (citing -> cited, self-citations of a record dropped).
2. **Topics** (`reproduce/topics/cluster.py`): undirected graph, each pair once; Leiden
   maximizing modularity with resolution `--res` (the RB configuration model; higher = more,
   smaller clusters), `--iter` passes, with igraph's `community_leiden` (`--engine igraph`,
   default) or `leidenalg` (`--engine leidenalg`, slower); clusters under `--min`
   papers are merged into the cluster they share the most links with; papers with no link stay
   unassigned (`topic = -1`); topics are numbered by size.
3. **Areas** (same script): Leiden on the graph of topics, weighted by the links between them, at
   `--res-area`; `area_of_topic` maps each topic to its area, so the hierarchy nests.
4. **Description** (`reproduce/topics/describe.py`): per topic, papers, median and 10-90% years,
   top arXiv categories, journals and countries (shares), and the `--top` most cited papers with
   their titles from the INSPIRE API (the tables have no titles); `topics.json`, `areas.json`.
5. **Names** (`reproduce/topics/names_r16.py`, `TOPICS` by topic number and `AREAS`): written
   from the titles of each topic's most cited papers, checked against its arXiv categories and
   journals. They belong to one clustering (resolution 16, seed 1, tables of 2026-11-09): any
   rerun renumbers the topics, so write the names again from the new `topics_*.json`.

```bash
python reproduce/topics/build_network.py data/papers.jsonl.gz out/clusters/network.npz          # ~3 min
python reproduce/topics/cluster.py out/clusters/network.npz out/clusters/clusters_r8.npz --res 8 --min 100
python reproduce/topics/describe.py out/clusters/clusters_r8.npz data/papers.jsonl.gz \
    out/clusters/topics_r8.json out/clusters/areas_r8.json
```

## Choosing the resolution

Scan `--res` and keep a value where (a) most linked papers fall in topics of a few hundred to a
few tens of thousands of papers, (b) the clusters are stable across `--seed` values, and (c) the
most cited papers of each topic share an evident subject. Record every run in the log below.

## Pitfalls

- About 15% of the papers have no citation link in the table (old records, theses, notes); they
  get no topic. They could be placed later by arXiv category and journal; say so when counting.
- The citation network includes the papers with more than 10 authors; filter by `n_authors` in
  `network.npz` to describe the corpus of 1 to 10 authors only.
- Leiden is randomized: fix `--seed`, and compare seeds before trusting a small cluster.
- Never run Leiden with `--iter -1` (until no change) on the whole network: a run at resolution 8
  went 7 hours without finishing. Two passes are the library's default and enough.
- `network.npz` is about 140 MB. leidenalg grows past 7.6 GB on this graph; igraph's Leiden needs
  less. On the 15 GB machine, run at most two resolutions at once and check `free -m` first.

## Step log

Keep this log and the artifact "INSPIRE Topic Map" in step: each run with date, command,
parameters and result.

| Date | Step | Result |
|---|---|---|
| 2026-11-12 | Network from the tables of 2026-11-09 | 1,872,221 papers, 44,428,313 citation links (directed), 1,586,301 papers with a link; 44,344,518 undirected links; 2 min 47 s |
| 2026-11-13 | Leiden, `--res 8 --min 100 --seed 1`, iterations until no change (`-1`) | stopped after 7 h 19 min with no result (one core, 6.2 GB); `-1` repeats Leiden until no improvement, far too slow at this size |
| 2026-11-13 | `cluster.py` gets `--iter` (default 2) and prints each pass | - |
| 2026-11-13 | Leiden (leidenalg), `--res 8 --min 100 --seed 1 --iter 2` | stopped after 13 min, first pass not done, at 7.6 GB: it left too little memory for a second run |
| 2026-11-13 | `cluster.py --engine igraph` (default): igraph's `community_leiden`, modularity with resolution, in C; one thread per run, so resolutions run as parallel processes (the machine: i7-7700HQ, 4 cores / 8 threads, 15 GB) | - |
| 2026-11-13 | Leiden (igraph), `--res 8 --min 100 --seed 1 --iter 2` | 6 min 38 s, 8.9 GB peak; 287,372 clusters (most are papers with no link), modularity 0.559; 144 topics of 100+ papers (median 9,277, largest 70,586), 1,583,351 papers assigned, 288,870 unassigned; 5 areas |
| 2026-11-13 | Leiden (igraph), `--res 4`, same options | 5 min 31 s; modularity 0.614; 69 topics (median 20,071, largest 80,871); 5 areas |
| 2026-11-13 | Leiden (igraph), `--res 16`, same options | 5 min 27 s, 9.3 GB peak; modularity 0.500; 307 topics (median 4,535, largest 31,906; 251 between 1k and 10k papers, 29 under 1k); 6 areas |
| 2026-11-13 | Leiden (igraph), `--res 32`, same options | 5 min 21 s; modularity 0.445; 623 topics (median 2,169, largest 23,802; 131 under 1k); 7 areas; 81.0% of the papers of each topic sit in one resolution-16 topic |
| 2026-11-13 | Resolution 16, `--seed 2` | 303 topics, 5 areas; against seed 1: NMI 0.829, ARI 0.654 on 1,583,351 papers (topics fairly stable, areas not) |
| 2026-11-13 | `describe.py` on resolution 16, `--top 8` | 3 min 11 s; `topics_r16.json`, `areas_r16.json`; every topic's top papers share an evident subject |
| 2026-11-13 | Names, `reproduce/topics/names_r16.py` | 307 topic names and 6 area names (Theory; Experiment and phenomenology; Strong interactions; Astrophysics and gravitational waves; Quantum physics; Nuclear structure and reactions); the Quantum physics area (248,230 papers, 50% quant-ph) is the boards' growing "Other arXiv" block |
