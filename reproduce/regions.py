"""The countries of each regional board, by INSPIRE-HEP's country names (institutions.jsonl.gz).

Latin America is the list of restrepo/inspireauth (reproduce/reproduce.py, LA), so its board can be
compared with that repository's. The other regions follow the continents of the UN geoscheme, with
Russia in Europe and Türkiye, Cyprus and the Caucasus in Asia; former states (USSR, Yugoslavia,
Czechoslovakia, GDR) are in Europe. North America is Canada and the United States, plus Bermuda,
Greenland and Saint Pierre and Miquelon. The other countries of the Americas (the Caribbean and
Central and South American countries outside inspireauth's list) and Antarctica are in no region.
"""

LATIN_AMERICA = ['Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Costa Rica', 'Cuba', 'Dominican Republic',
                 'Ecuador', 'El Salvador', 'Guatemala', 'Honduras', 'Mexico', 'Panama', 'Paraguay', 'Peru', 'Uruguay',
                 'Venezuela']

NORTH_AMERICA = ['Bermuda', 'Canada', 'Greenland', 'Saint Pierre and Miquelon', 'United States']

AFRICA = ['Algeria', 'Angola', 'Benin', 'Botswana', 'British Indian Ocean Territory', 'Burkina Faso', 'Burundi',
          'Cabo Verde', 'Cameroon', 'Central African Republic', 'Chad', 'Comoros', 'Congo',
          'Congo, The Democratic Republic of the', "Côte d'Ivoire", 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea',
          'Eswatini', 'Ethiopia', 'French Southern Territories', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau',
          'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Mayotte',
          'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Réunion', 'Rwanda',
          'Saint Helena, Ascension and Tristan da Cunha', 'Sao Tome and Principe', 'Senegal', 'Seychelles',
          'Sierra Leone', 'Somalia', 'South Africa', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Western Sahara',
          'Zambia', 'Zimbabwe']

ASIA = ['Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Bhutan', 'Brunei Darussalam', 'Cambodia',
        'China', 'Christmas Island', 'Cocos (Keeling) Islands', 'Cyprus', 'Georgia', 'Hong Kong', 'India', 'Indonesia',
        'Iran', 'Iraq', 'Israel', 'Japan', 'Jordan', 'Kazakhstan', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Macao',
        'Malaysia', 'Maldives', 'Mongolia', 'Myanmar', 'Nepal', 'Neutral Zone', 'North Korea', 'Oman', 'Pakistan',
        'Palestine, State of', 'Philippines', 'Qatar', 'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka', 'Syria',
        'Taiwan', 'Tajikistan', 'Thailand', 'Timor-Leste', 'Türkiye', 'Turkmenistan', 'United Arab Emirates',
        'Uzbekistan', 'Vietnam', 'Yemen']

EUROPE = ['Åland Islands', 'Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria',
          'Croatia', 'Czechia', 'Czechoslovakia', 'Denmark', 'Estonia', 'Faroe Islands', 'Finland', 'France',
          'German Democratic Republic', 'Germany', 'Gibraltar', 'Greece', 'Holy See (Vatican City State)', 'Hungary',
          'Iceland', 'Ireland', 'Italy', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova',
          'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 'Romania',
          'Russian Federation', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Svalbard and Jan Mayen',
          'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom', 'USSR, Union of Soviet Socialist Republics',
          'Yugoslavia, (Socialist) Federal Republic of']

OCEANIA = ['American Samoa', 'Australia', 'Cook Islands', 'Fiji', 'French Polynesia', 'Guam', 'Kiribati',
           'Marshall Islands', 'Micronesia, Federated States of', 'Nauru', 'New Caledonia', 'New Zealand', 'Niue',
           'Norfolk Island', 'Northern Mariana Islands', 'Palau', 'Papua New Guinea', 'Pitcairn', 'Samoa',
           'Solomon Islands', 'Tokelau', 'Tonga', 'Tuvalu', 'United States Minor Outlying Islands', 'Vanuatu',
           'Wallis and Futuna']

REGIONS = {'Latin America': LATIN_AMERICA, 'Africa': AFRICA, 'Asia': ASIA, 'Europe': EUROPE,
           'North America': NORTH_AMERICA, 'Oceania': OCEANIA}
