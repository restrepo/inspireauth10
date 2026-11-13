"""Titles and descriptions of the topics board's datasets (shown in its Sources section)."""

DATASETS = {
    'scalars': ('Totals', 'Papers of the tables, papers with a topic and without one, topics, areas, citation links '
                'and the clustering resolutions.'),
    'areas': ('Areas', 'The six areas: papers, topics, citations, arXiv mix, and papers in 2011-2015 and 2021-2025.'),
    'topics': ('Topics', 'Each topic: name, area, papers (and those with 1 to 10 authors), citations, years, arXiv '
               'categories, journals and countries (shares), most cited papers, and its position on the map.'),
    'topic_links': ('Links between topics', "Citation links between topics (each topic's 6 strongest by association "
                    'strength), which place the topics on the map.'),
    'topic_year': ('Papers per year by topic', 'Papers of each topic by publication year.'),
    'area_year': ('Papers per year by area', 'Papers of each area by publication year.'),
    'country_area': ('Areas by country', 'Papers in each area of each country with 1,000 or more papers with a topic.'),
    'country_topic': ('Topics by country', 'Papers in each topic of each country with 1,000 or more papers with a topic.'),
}
