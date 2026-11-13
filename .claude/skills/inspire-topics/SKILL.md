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
3. **Areas** (same script, or `reproduce/topics/areas.py` to redo only this step): Leiden on the
   graph of topics weighted by the links between them, with the links inside each topic as
   self-loops (the network coarsened to topics), at `--res-area` (default 0.3, the steadiest: 6
   areas), the best of 50 seeds; `area_of_topic` maps each topic to its area, so the hierarchy
   nests.
4. **Choosing among seeds** (`reproduce/topics/compare.py`): NMI and ARI of every pair of seeds,
   for topics and areas; keep the medoid, the run with the highest mean topic NMI to the others.
5. **Description** (`reproduce/topics/describe.py`): per topic, papers, median and 10-90% years,
   top arXiv categories, journals and countries (shares), and the `--top` most cited papers with
   their titles from the INSPIRE API (the tables have no titles); `topics.json`, `areas.json`.
6. **Names** (`reproduce/topics/names.py`, `TOPICS` by topic number and `AREAS`): written from
   the titles of each topic's most cited papers, checked against its arXiv categories and
   journals. They belong to the kept clustering (below); any rerun renumbers the topics. Carry
   names over by overlap: a new topic that shares 60% or more of its papers both ways with an old
   one keeps its name; name the rest again. `names_r16.py` holds the names of the first run.

The kept clustering of the tables of 2026-11-09 (`out/clusters/topics_final.npz`, 304 topics,
6 areas) is reproduced by:

```bash
python reproduce/topics/build_network.py data/papers.jsonl.gz out/clusters/network.npz          # ~3 min
for s in 1 2 3 4; do                                                                             # ~20 min each, 2 at a time
  python reproduce/topics/cluster.py out/clusters/network.npz out/clusters/steady_r16_s$s.npz --res 16 --min 100 --iter 20 --seed $s
done
python reproduce/topics/compare.py out/clusters/steady_r16_s*.npz                                # medoid: seed 1
python reproduce/topics/describe.py out/clusters/steady_r16_s1.npz data/papers.jsonl.gz \
    out/clusters/topics_final.json out/clusters/areas_final.json --top 8
```

## Topics board

An independent, self-contained board ("HECAP topics"), built by the same `standalone.py` as the
other boards with its own page and datasets:

```bash
python reproduce/topics/indicators.py data out/clusters/topics_final.npz out/clusters/topics_final.json \
    out/clusters/network.npz out/topics_dash/                                                   # ~2 min
python reproduce/topics/board.py out/topics_dash/ out/topics_2026-11-09.html --date 2026-11-09
python reproduce/pages_index.py topics out/site --id 2026-11-09 --board out/topics_2026-11-09.html \
    --scalars out/topics_dash/scalars.json                                                      # boards/<id>/topics/
```

- Datasets (`reproduce/topics/board_datasets.py`): scalars, areas, topics (with map position),
  topic_links, topic_year, area_year, country_area and country_topic (countries with 1,000+
  papers with a topic, 73 in 2026-11-09).
- Tabs: Overview (totals, areas, a map of the topics placed by a force layout of each topic's 6
  strongest links by association strength), Topics (search, sort, detail with papers per year,
  arXiv, journals, countries and most cited papers linked to INSPIRE), Trends (areas per year,
  growing and shrinking topics, 2021-2025 against 2011-2015), Countries (area shares against all
  papers, topics with a specialization index), Method.
- Template: `reproduce/topics/board/index.html` (the other boards' styles, its own drawers).

## VOSviewer

```bash
python reproduce/topics/vosviewer.py out/clusters/network.npz out/clusters/topics_final.npz \
    out/clusters/topics_final.json out/vosviewer/                                               # ~25 s
```

Writes `topics_vosviewer.json` (VOSviewer 1.6.16+ and VOSviewer Online: File → Open → JSON) and
`topics_map.txt` + `topics_network.txt` (classic map and network files). Items are topics (id =
topic + 1, cluster = area + 1, weights Papers, Citation links and Internal citation links, score
Median year); link strength is the number of distinct citation links between two topics' papers.
`--min-links N` drops weaker links (all 39,502 are kept by default; VOSviewer's own "maximum
number of lines" thins the drawing).

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
- Never run leidenalg with `n_iterations=-1` (until no change) on the whole network: a run at
  resolution 8 went 7 hours without finishing. With igraph, `--iter 20` takes about 20 minutes
  and the quality is still creeping up by ~1e-5 per pass at the end, which no longer changes the
  topics noticeably.
- Topics agree between seeds at NMI ~0.85 and ARI ~0.65: individual small topics move between
  seeds, so do not over-interpret one topic's exact borders; areas are steadier (ARI ~0.87).
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
| 2026-11-13 | Steadying: `cluster.py` stops igraph passes when quality stops rising; areas now use the topic graph with the links inside each topic as self-loops (the network coarsened to topics, as CWTS) and keep the best of `--area-seeds 50` runs | - |
| 2026-11-13 | Resolution 16, `--iter 20`, seeds 1 and 2 | ~20 min each, 7.4 GB; quality still rising by ~1e-5 per pass at pass 20; 304 and 299 topics; topic agreement NMI 0.848, ARI 0.692 (2 passes: 0.829, 0.654); with self-loops and area resolution 1.0, 14 and 15 areas (13-17 over area seeds), NMI 0.761, ARI 0.721 |
| 2026-11-13 | Area resolution scan on the topic graphs of seeds 1 and 2 | 0.2: 6/5 areas, ARI 0.721; **0.3: 6/6 areas, NMI 0.843, ARI 0.867**; 0.5: 8/8, ARI 0.861; 0.7: 10/10, ARI 0.829; 1.0: 14/15, ARI 0.721. Default `--res-area` is now 0.3; `areas.py` recomputes areas of an existing clustering |
| 2026-11-13 | Resolution 16, `--iter 20`, seeds 3 and 4; areas of all four at 0.3 | 304 and 307 topics; seed 4 has a seventh area of 134 papers. Four seeds: topic NMI 0.839-0.848, ARI 0.636-0.692; area NMI 0.819-0.866, ARI 0.852-0.902 |
| 2026-11-13 | Kept: seed 1, the medoid (mean topic NMI 0.846); `out/clusters/topics_final.npz` | 304 topics; 6 areas: Particle physics: experiment, phenomenology, QCD and hadrons (529,313 papers, 105 topics); Theory: strings, fields, gravity and cosmology (364,782, 88); Astrophysics and gravitational waves (257,596, 50); Quantum physics: information, optics and condensed matter (250,924, 44); Nuclear structure and reactions (108,651, 10); Accelerator physics (72,085, 7) |
| 2026-11-13 | Topics board: `indicators.py`, `board.py`, `pages_index.py topics` | `out/topics_2026-11-09.html`, 2.3 MB; 304 topics, 6 areas, 73 countries; all tabs draw with no console error, no horizontal scroll at 375 px; added to the Pages site at `boards/2026-11-09/topics/`, pushed 2026-11-13 (gh-pages a2b6467): https://restrepo.github.io/inspireauth10/boards/2026-11-09/topics/ |
| 2026-11-13 | `describe.py` on the kept clustering; names by overlap, `reproduce/topics/names.py` | 295 of 304 topics share 60%+ of their papers both ways with a topic of the first run and keep its name; 9 merged or split topics named again |
| 2026-11-13 | Names, `reproduce/topics/names_r16.py` | 307 topic names and 6 area names (Theory; Experiment and phenomenology; Strong interactions; Astrophysics and gravitational waves; Quantum physics; Nuclear structure and reactions); the Quantum physics area (248,230 papers, 50% quant-ph) is the boards' growing "Other arXiv" block |
| 2026-11-13 | VOSviewer input, `reproduce/topics/vosviewer.py` | `out/vosviewer/`: 304 topics, 6 clusters (areas), 39,502 links; 18,658,344 citation links between topics, 25,684,345 inside; JSON 2.2 MB, map 18 KB, network 408 KB |
