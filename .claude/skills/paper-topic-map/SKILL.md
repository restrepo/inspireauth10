---
name: paper-topic-map
description: Draw where one INSPIRE paper's citation links fall on the topic map of this repository - every reference and citing paper placed in its main topic, shown as the real linked papers clustered by topic around the paper (own topic, the five topics with most links, a grey cluster for the rest) and as a radial map of all the topics it reaches, with hover pop-ups and links to INSPIRE and the topic timelines. Use whenever someone working in a clone of restrepo/inspireauth10 asks for the topics of a paper, how a paper connects to other topics or fields, a link or citation map of a paper (by INSPIRE recid or URL), the paper maps of the topics board (its Paper maps tab, the most cited paper of each area), or to add a paper to that tab.
---

# Topic map of one paper

Run from the repository root after the topic clustering (skill `inspire-topics`): it needs
`out/clusters/network.npz`, `out/clusters/topics_final.npz`, `out/clusters/topics_final.json` and the tables
`data/papers.jsonl.gz` and `data/papers_text.jsonl.gz`. Python with numpy (`/home/restrepo/prog/claude/.venv`).

## What a link is

A link is one citing pair between the paper and another paper of the network, in either direction, counted once
(a paper that both cites it and is cited by it counts once). Each link goes to the **main topic of the paper at the
other end**. The same counts give the second and third topics of `secondary.py`, so a paper's "topics" are this
map's largest rows; the share in its own topic says how far it reaches outside it.

## Make the maps

```bash
python reproduce/topics/paper_maps.py out/clusters/network.npz out/clusters/topics_final.npz \
    out/clusters/topics_final.json data/ out/topics_dash/paper_maps/ [RECID ...] [--html DIR]   # ~40 s
```

- No RECID: the most cited paper (citations inside the network) of each of the six areas. In 2026-11-09: Geant4
  2003 (593382), Planck 2018 VI (1682902), GW150914 (1421100), Bennett et al. 1993 teleportation (332268), Wiringa
  et al. 1995 AV18 (375634), Bardeen-Cooper-Schrieffer 1957 (3541).
- Writes `<recid>.json` (topic rows, drawn papers and their citation edges, header) and `index.json` (the papers
  in order, read by the page's selector and the board tab). Running it with other RECIDs replaces `index.json`, so
  pass every paper the tab should list.
- Papers with fewer than `--all-below 400` links draw **every** linked paper (topics past the sixth go to the grey
  "Other topics" cluster). Above that, the most cited `--own 24` of its own topic and `--per 16` of each of the next
  five topics.
- `--html DIR` also writes `DIR/<recid>.html`, a self-contained page (map inlined, topic links to the Pages board,
  `--base` to change it). Publish that file as an Artifact (icon `graph`) when someone asks for one paper's map;
  send it with SendUserFile too.
- The header (journal reference, collaboration) comes from the INSPIRE API; `--no-api` skips it.

## The page and the board

- `reproduce/topics/board/paper.html?recid=N` reads `paper_maps/<recid>.json`, next to it. Views: **Papers** (real
  papers by topic cluster, hollow = references, filled = citing papers, grey lines = citations among them, hover a
  paper or a cluster name for details, click to open INSPIRE) and **Topics** (every topic reached, closer and larger
  with more links). The list on the right ranks all topics and opens each one's `timeline.html`.
- The **Paper maps** tab of the topics board (`board/index.html`) fetches `paper_maps/index.json` and shows one
  button per paper over an iframe of `paper.html`. The self-contained board (`board.py`) has no `paper_maps/`, so
  there the tab only says where the maps are; they work on GitHub Pages.
- To publish on Pages, copy `paper.html` and `out/topics_dash/paper_maps/` (about 170 kB for six papers) next to
  the board in gh-pages `boards/<date>/topics/`, with the rebuilt `index.html`. Pushing gh-pages publishes: do it
  only when the user asks.

## Check

Open the page through a local server (`python3 -m http.server` in a folder with `index.html`, `paper.html`,
`timeline.html`, `paper_maps/`, `timelines/`): no console errors, every cluster drawn, no horizontal scroll at
phone width.

## Limits

- Only citations between papers of the network count; INSPIRE misses references of some old or non-HEP papers.
- For a paper with thousands of links the Papers view is a sample (the most cited per topic); the Topics view and
  the list count all of them.
- A paper without a topic (no citation link) has no map.
