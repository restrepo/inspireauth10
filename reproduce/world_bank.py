"""Write reproduce/world_bank.csv: population and R&D spending of every country, from the World Bank.

Columns: country_code (ISO 3166 alpha-2, as institutions.jsonl.gz), iso3, name (World Bank's),
population and population_year (the latest year with a value, indicator SP.POP.TOTL), rd_avg (the
average R&D expenditure in % of GDP over the years with a value from 1996 on, GB.XPD.RSDV.GD.ZS,
as Table 1 of the Latin American paper) and rd_years (how many years it averages).
The World Bank has no data for Taiwan; its population comes from Taiwan's Ministry of the
Interior (end of 2024) and its R&D is left empty.

Usage: python reproduce/world_bank.py [reproduce/world_bank.csv]
"""
import csv
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = 'https://api.worldbank.org/v2/country/all/indicator/{}?format=json&per_page=1000&date={}&page={}'
EXTRA = [{'country_code': 'TW', 'iso3': 'TWN', 'name': 'Taiwan', 'population': 23400220, 'population_year': 2024,
          'rd_avg': '', 'rd_years': 0}]


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'restrepo/inspireauth10'})
    return json.load(urllib.request.urlopen(req, timeout=120))


def series(indicator, years):
    """{iso2: {year: value}} of the countries (not the aggregates) with a value."""
    meta = get('https://api.worldbank.org/v2/country?format=json&per_page=400')
    countries = {c['id']: c['iso2Code'] for c in meta[1] if c['region']['value'] != 'Aggregates'}
    first = get(API.format(indicator, years, 1))
    rows = first[1] + [r for page in range(2, first[0]['pages'] + 1) for r in get(API.format(indicator, years, page))[1]]
    out, names = defaultdict(dict), {}
    for r in rows:
        iso2 = countries.get(r['countryiso3code']) or (r['country']['id'] if r['country']['id'] in countries.values() else None)
        if iso2 and r['value'] is not None:
            out[iso2][int(r['date'])] = r['value']
            names[iso2] = r['countryiso3code'], r['country']['value']
    return out, names


def main(path=HERE / 'world_bank.csv'):
    pop, names = series('SP.POP.TOTL', '2015:2030')
    rd, _ = series('GB.XPD.RSDV.GD.ZS', '1996:2030')
    rows = []
    for c in sorted(pop):
        y = max(pop[c])
        v = list(rd.get(c, {}).values())
        rows.append({'country_code': c, 'iso3': names[c][0], 'name': names[c][1], 'population': int(pop[c][y]),
                     'population_year': y,
                     'rd_avg': round(sum(v) / len(v), 3) if v else '', 'rd_years': len(v)})
    rows += [r for r in EXTRA if r['country_code'] not in pop]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r['country_code']))
    print(f'wrote {path}: {len(rows)} countries')


if __name__ == '__main__':
    main(*sys.argv[1:2])
