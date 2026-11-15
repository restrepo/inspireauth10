"""Topic maps of single papers: where each paper's citation links fall on the topic map.

For each paper, every citation link (a reference or a citing paper, a pair counted once) is assigned to the main
topic of the paper at the other end. The board page `board/paper.html?recid=N` draws the result twice: the linked
papers themselves, clustered by topic around the paper (own topic and the five topics with most links, plus a grey
cluster for the rest when every link is shown), and the topics as a radial map.

Usage (from the repository root, after cluster.py and names.py):
  python reproduce/topics/paper_maps.py out/clusters/network.npz out/clusters/topics_final.npz \
      out/clusters/topics_final.json data/ out/topics_dash/paper_maps/ [RECID ...] [--all-below 400] [--html DIR]

With no RECID it maps the most cited paper (citations inside the network) of each area. Writes <recid>.json per paper
and index.json (the papers in order, for the page's selector and the board's Paper maps tab). Papers with fewer than
--all-below links show every linked paper; above that, the most cited --own in its own topic and --per in each of
the next five topics. With --html DIR it also writes DIR/<recid>.html, a self-contained page of each map whose topic
links go to the board on GitHub Pages. Titles come from data/papers_text.jsonl.gz, journal references from the
INSPIRE API (optional).
"""

import argparse
import gzip
import json
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("network")
ap.add_argument("topics")
ap.add_argument("names")
ap.add_argument("data")
ap.add_argument("out")
ap.add_argument("recids", nargs="*", type=int)
ap.add_argument("--all-below", type=int, default=400, help="show every linked paper when the links are fewer")
ap.add_argument("--own", type=int, default=24, help="papers drawn in the own topic (large papers)")
ap.add_argument("--per", type=int, default=16, help="papers drawn in each other topic (large papers)")
ap.add_argument("--clusters", type=int, default=6)
ap.add_argument("--html", help="also write a self-contained <recid>.html per paper into this folder")
ap.add_argument(
    "--base",
    default="https://restrepo.github.io/inspireauth10/boards/2026-11-09/topics/",
    help="board the self-contained pages link to",
)
ap.add_argument("--no-api", action="store_true", help="skip the INSPIRE API (no journal reference)")
a = ap.parse_args()

z = np.load(a.network)
f = np.load(a.topics)
top, area_of = f["topic"], f["area_of_topic"]
TT = json.loads(Path(a.names).read_text())
T = {x["topic"]: x for x in TT}
areas = [n for _, n in sorted({(int(x["area"]), x["area_name"]) for x in TT})]
rec, s, d, yr = z["recid"], z["src"], z["dst"], z["year"]
indeg = np.bincount(d, minlength=len(rec))
row_of = {int(r): k for k, r in enumerate(rec)}

recids = a.recids
if not recids:  # the most cited paper of each area
    area = np.where(top >= 0, area_of[np.maximum(top, 0)], -1)
    recids = [int(rec[np.flatnonzero(area == k)[np.argmax(indeg[area == k])]]) for k in range(len(areas))]

maps = []
for recid in recids:
    i = row_of[recid]
    own = int(top[i])
    refs = set(d[s == i].tolist()) - {i}
    cit = set(s[d == i].tolist()) - {i}
    nb = refs | cit
    every = len(nb) < a.all_below
    # topic rows: links split into references and citing papers (a pair counts once)
    cr = Counter(int(top[j]) for j in refs)
    cc = Counter(int(top[j]) for j in cit - refs)
    cr.pop(-1, None)
    cc.pop(-1, None)
    rows = sorted(
        ([t, T[t]["name"], int(T[t]["area"]), cr[t], cc[t], T[t]["papers"]] for t in set(cr) | set(cc)),
        key=lambda r: -(r[3] + r[4]),
    )
    # paper clusters: own topic first, then the topics with most links
    order = [own] + [r[0] for r in rows if r[0] != own]
    TOP = order[: a.clusters]
    REST = order[a.clusters :]
    sel = []
    for t in TOP:
        c = sorted([j for j in nb if top[j] == t], key=lambda j: -indeg[j])
        sel += c if every else c[: a.own if t == own else a.per]
    if every and REST:
        sel += sorted([j for j in nb if top[j] in REST], key=lambda j: -indeg[j])
    idx = {j: k for k, j in enumerate(sel)}
    m = np.isin(s, sel) & np.isin(d, sel)
    E = sorted({(idx[x], idx[y]) for x, y in zip(s[m].tolist(), d[m].tolist()) if x != y})
    maps.append(
        {
            "recid": recid,
            "i": i,
            "own": own,
            "refs": refs,
            "cit": cit,
            "rows": rows,
            "TOP": TOP,
            "REST": REST,
            "sel": sel,
            "E": E,
            "every": every,
        }
    )

# one pass over the paper tables for everything the maps need
want = {int(rec[j]) for mp in maps for j in mp["sel"]} | set(recids)
info, title = {}, {}
with gzip.open(Path(a.data) / "papers.jsonl.gz", "rt") as fh:
    for line in fh:
        r = int(line[9 : line.index(",")])
        if r in want:
            p = json.loads(line)
            au = p["authors"]
            info[r] = {
                "first": au[0]["full_name"].split(",")[0] if au else "?",
                "na": p["n_authors"],
                "cites": p["citation_count"],
            }
with gzip.open(Path(a.data) / "papers_text.jsonl.gz", "rt") as fh:
    for line in fh:
        r = int(line[9 : line.index(",")])
        if r in want:
            p = json.loads(line)
            title[r] = [p["title"].replace("$", "").replace("\\", ""), p.get("arxiv_eprint") or ""]


def inspire(recid):
    if a.no_api:
        return {}
    url = f"https://inspirehep.net/api/literature/{recid}?fields=titles,publication_info,collaborations"
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))["metadata"]
    except (OSError, ValueError, KeyError):
        return {}


out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
index = []
for mp in maps:
    recid, i, TOP, REST = mp["recid"], mp["i"], mp["TOP"], mp["REST"]
    nodes = []
    for j in mp["sel"]:
        r = int(rec[j])
        x = info.get(r, {})
        tt = title.get(r, ["?", ""])
        tj = int(top[j]) if int(top[j]) in TOP else -2
        nodes.append(
            [
                r,
                tt[1],
                tt[0],
                x.get("first", "?"),
                x.get("na", 0),
                int(yr[j]),
                x.get("cites", int(indeg[j])),
                tj,
                int(j in mp["refs"]),
                int(top[j]),
            ]
        )
    other = [[-2, f"Other topics ({len(REST)})"]] if mp["every"] and REST else []
    papers = {"n": nodes, "e": mp["E"], "topics": [[t, T[t]["name"]] for t in TOP] + other}
    m_ = inspire(recid)
    pi = (m_.get("publication_info") or [{}])[0]
    ref = " ".join(
        str(x)
        for x in [pi.get("journal_title"), pi.get("journal_volume"), pi.get("artid") or pi.get("page_start")]
        if x
    )
    year = int(yr[i])
    me = info.get(recid, {})
    first, na = me.get("first", "?"), me.get("na", 0)
    coll = [c["value"] for c in m_.get("collaborations", [])]
    hub = coll[0] if coll else first
    lead = f"{coll[0]} Collaboration" if coll else f"{first}{' et al.' if na > 2 else ' + 1' if na == 2 else ''}"
    ttl = (m_.get("titles") or [{}])[0].get("title") or title.get(recid, ["?"])[0]
    meta = {
        "recid": recid,
        "own": mp["own"],
        "title": ttl.replace("$", ""),
        "lead": lead,
        "hub": hub,
        "year": year,
        "eyebrow": f"INSPIRE {recid}" + (f" · {ref} ({year})" if ref else f" ({year})"),
        "all": mp["every"],
    }
    data = {
        "rows": mp["rows"],
        "areas": areas,
        "n_refs": len(mp["refs"]),
        "n_cit": len(mp["cit"]),
        "overlap": len(mp["refs"] & mp["cit"]),
    }
    J = json.dumps({"data": data, "papers": papers, "meta": meta}, separators=(",", ":"), ensure_ascii=False)
    (out / f"{recid}.json").write_text(J)
    if a.html:
        page = (Path(__file__).resolve().parent / "board/paper.html").read_text()
        safe = J.replace("</", "<\\/")
        inline = (
            f"<script>window.PAPER_MAP={safe};window.PAPER_BASE={json.dumps(a.base)};</script>\n"
            '<script src="https://cdnjs'
        )
        Path(a.html).mkdir(parents=True, exist_ok=True)
        (Path(a.html) / f"{recid}.html").write_text(page.replace('<script src="https://cdnjs', inline, 1))
    links = len(mp["refs"] | mp["cit"])
    own_n = next(r[3] + r[4] for r in mp["rows"] if r[0] == mp["own"])
    index.append(
        {
            "recid": recid,
            "area": int(T[mp["own"]]["area"]),
            "area_name": areas[int(T[mp["own"]]["area"])],
            "lead": lead,
            "year": year,
            "title": meta["title"],
            "cites": me.get("cites", int(indeg[i])),
            "links": links,
            "topics": len(mp["rows"]),
            "own": mp["own"],
            "own_name": T[mp["own"]]["name"],
            "own_share": round(own_n / max(1, sum(r[3] + r[4] for r in mp["rows"])), 3),
        }
    )
    print(
        recid,
        lead,
        year,
        "own",
        mp["own"],
        "links",
        links,
        "topics",
        len(mp["rows"]),
        "papers",
        len(nodes),
        "edges",
        len(mp["E"]),
    )
(out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
