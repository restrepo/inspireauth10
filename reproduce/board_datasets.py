"""Titles and descriptions of the board's datasets (shown in the board's Sources section)."""

DATASETS = {
    'scalars': ('Dataset totals', 'Papers, authors, profiles, countries and references of the corpus.'),
    'countries': ('Indicators by country', 'Per country and for the world: papers, authors, citations (all of INSPIRE '
                  'and from the corpus), h-index, share of citations from the same country, female share, and '
                  'population (World Bank), R&D expenditure and papers, authors and citations per million inhabitants.'),
    'fits': ('Correlations with R&D', 'Straight-line fits of authors, papers and citations per million inhabitants '
             'against the average R&D expenditure (% of GDP), over the countries of 1 million inhabitants or more.'),
    'gender_year': ('Female share per year', 'Profiles with gender probability 0.9 or more who published in each year, '
                    'by country, and their female share with its 95% margin.'),
    'gender_rank': ('Female share by rank', 'Profiles holding a declared rank in a year in which they published, by '
                    'group of ranks, and their female share with its 95% margin.'),
    'region_share': ('Share of the world', "Regional boards: the region's papers and their citations as a share of "
                     'the corpus, by year.'),
    'mobility': ('Ranks and mobility', 'Regional boards: positions with a declared rank, held where the author '
                 'published, of the authors with a ranked position in each country, by rank and by where they were.'),
    'phd_destination': ('Where PhDs go next', 'Regional boards: authors with a PhD position in a country of the '
                        'region, by where their current (else latest) later position is.'),
    'coauthorship': ('Co-authorship between countries', "Regional boards: the share of each row country's papers "
                     'co-authored with each column country.'),
    'papers_per_year': ('Papers per year', 'Papers of each country, and of the world, by publication year.'),
    'citation_flows': ('Citation flows', 'For the 20 countries with the most papers: citations between papers of the '
                       'corpus from each citing country to each cited country, and their share of the cited '
                       "country's citations."),
    'advisor_generations': ('Generations of PhD advisors', 'Advisors and parent advisors (no registered PhD advisor) '
                            'of each country by the number of generations of PhD students below them.'),
    'collaborations': ('Collaborations', 'The 40 collaborations with the most papers among the papers with more than '
                       '10 authors (outside the corpus): experiment id, papers, citations and countries.'),
}
