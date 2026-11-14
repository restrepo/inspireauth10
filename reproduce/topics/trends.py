"""Trend of a topic: its share of all papers with a topic in 2021-2025 divided by its share in
2011-2015 (share_ratio); Growing above 1.5, Shrinking below 2/3, else Stable. Using shares instead
of counts takes out the growth of the whole corpus (x1.32 between those periods in 2026-11-09)."""
GROWING, SHRINKING = 1.5, 2 / 3


def add_trends(topics):
    """Set share_ratio and trend on each topic dict (papers_2011_2015, papers_2021_2025); returns topics."""
    s11 = sum(t['papers_2011_2015'] for t in topics)
    s21 = sum(t['papers_2021_2025'] for t in topics)
    for t in topics:
        p11, p21 = t['papers_2011_2015'], t['papers_2021_2025']
        ratio = (p21 / s21) / (p11 / s11) if p11 else None
        t['share_ratio'] = round(ratio, 3) if ratio is not None else None
        t['trend'] = 'Growing' if ratio is None or ratio > GROWING else 'Shrinking' if ratio < SHRINKING else 'Stable'
    return topics
