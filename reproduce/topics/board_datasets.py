"""Titles and descriptions of the topics board's datasets (shown in its Sources section)."""

DATASETS = {
    'scalars': ('Totals', 'Papers of the tables, papers with a topic and without one, topics, areas, citation links '
                'and the clustering resolutions.'),
    'areas': ('Areas', 'The six areas: papers, topics, citations, arXiv mix, and papers in 2011-2015 and 2021-2025.'),
    'topics': ('Topics', 'Each topic: name, area, papers (and those with 1 to 10 authors), citations, years, arXiv '
               'categories, journals and countries (shares), most cited papers, its position on the map, and its trend '
               '(Growing, Stable or Shrinking, by the change of its share of all papers from 2011-2015 to 2021-2025).'),
    'topic_links': ('Links between topics', "Citation links between topics (each topic's 6 strongest by association "
                    'strength), which place the topics on the map.'),
    'topic_year': ('Papers per year by topic', 'Papers of each topic by publication year.'),
    'area_year': ('Papers per year by area', 'Papers of each area by publication year.'),
    'author_flows': ('Author flows', 'For each topic, where its authors (INSPIRE profiles with 2 or more papers in the '
                     'early period) had their main topic in the late period: the 15 largest destinations, the rest '
                     'summed (to = -2), and those who stopped (to = -1), for three pairs of periods.'),
    'flow_periods': ('Periods of the author flows', 'The three pairs of periods of the author flows.'),
    'landmarks': ('Landmark papers', 'The 300 most cited papers of the network (citations between papers of the '
                  'tables), with the number of citing papers in each area, title, first author and arXiv number.'),
    'disruption_top': ('Disruption of highly cited papers', 'Papers up to 2020 with 500 or more citations and 5 or more '
                       'references in the network: CD index over the first 5 years (cd5, with n_i, n_j, n_k) and over all '
                       'years (cd), with title, first author and arXiv number.'),
    'disruption_share': ('Share of disruptive papers', 'For each five-year bin and area (-1 = all), the papers with 100 or '
                         'more citations and those with CD index above 0, over 5 years (cd5_pos) and all years (cd_pos).'),
    'country_area': ('Areas by country', 'Papers in each area of each country with 1,000 or more papers with a topic.'),
    'country_topic': ('Topics by country', 'Papers in each topic of each country with 1,000 or more papers with a topic.'),
}
