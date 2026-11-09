"""Titles and descriptions of the board's datasets (shown in the board's Sources section)."""

DATASETS = {
    'scalars': ('Dataset totals', 'Papers, authors, profiles, countries and references of the corpus.'),
    'countries': ('Indicators by country', 'Per country and for the world: papers, authors, citations (all of INSPIRE '
                  'and from the corpus), h-index, share of citations from the same country and female share.'),
    'papers_per_year': ('Papers per year', 'Papers of each country, and of the world, by publication year.'),
    'citation_flows': ('Citation flows', 'For the 20 countries with the most papers: citations between papers of the '
                       'corpus from each citing country to each cited country, and their share of the cited '
                       "country's citations."),
    'advisor_generations': ('Generations of PhD advisors', 'Advisors and parent advisors (no registered PhD advisor) '
                            'of each country by the number of generations of PhD students below them.'),
    'collaborations': ('Collaborations', 'The 40 collaborations with the most papers among the papers with more than '
                       '10 authors (outside the corpus): experiment id, papers, citations and countries.'),
}
