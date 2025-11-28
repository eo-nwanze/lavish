from django.core.management.base import BaseCommand
from locations.models import Country, State, City

class Command(BaseCommand):
    help = 'Populate countries, states, and cities with sample data'

    def handle(self, *args, **options):
        # Sample countries data (without special characters)
        countries_data = [
            {
                'name': 'United Kingdom',
                'iso_code': 'GB',
                'iso3_code': 'GBR',
                'phone_code': '44',
                'currency': 'GBP',
                'currency_symbol': 'GBP',
                'timezone': 'Europe/London',
                'flag_emoji': 'GB',
                'states': [
                    {
                        'name': 'England',
                        'state_code': 'ENG',
                        'cities': ['London', 'Manchester', 'Birmingham', 'Liverpool', 'Leeds']
                    },
                    {
                        'name': 'Scotland',
                        'state_code': 'SCT',
                        'cities': ['Edinburgh', 'Glasgow', 'Aberdeen', 'Dundee', 'Inverness']
                    },
                    {
                        'name': 'Wales',
                        'state_code': 'WLS',
                        'cities': ['Cardiff', 'Swansea', 'Newport', 'Bangor', 'Wrexham']
                    },
                    {
                        'name': 'Northern Ireland',
                        'state_code': 'NIR',
                        'cities': ['Belfast', 'Derry', 'Lisburn', 'Newry', 'Armagh']
                    }
                ]
            },
            {
                'name': 'United States',
                'iso_code': 'US',
                'iso3_code': 'USA',
                'phone_code': '1',
                'currency': 'USD',
                'currency_symbol': 'USD',
                'timezone': 'America/New_York',
                'flag_emoji': 'US',
                'states': [
                    {
                        'name': 'California',
                        'state_code': 'CA',
                        'cities': ['Los Angeles', 'San Francisco', 'San Diego', 'Sacramento', 'San Jose']
                    },
                    {
                        'name': 'New York',
                        'state_code': 'NY',
                        'cities': ['New York City', 'Buffalo', 'Rochester', 'Albany', 'Syracuse']
                    },
                    {
                        'name': 'Texas',
                        'state_code': 'TX',
                        'cities': ['Houston', 'Dallas', 'Austin', 'San Antonio', 'Fort Worth']
                    },
                    {
                        'name': 'Florida',
                        'state_code': 'FL',
                        'cities': ['Miami', 'Orlando', 'Tampa', 'Jacksonville', 'Tallahassee']
                    }
                ]
            },
            {
                'name': 'Australia',
                'iso_code': 'AU',
                'iso3_code': 'AUS',
                'phone_code': '61',
                'currency': 'AUD',
                'currency_symbol': 'AUD',
                'timezone': 'Australia/Sydney',
                'flag_emoji': 'AU',
                'states': [
                    {
                        'name': 'New South Wales',
                        'state_code': 'NSW',
                        'cities': ['Sydney', 'Newcastle', 'Wollongong', 'Central Coast', 'Blue Mountains']
                    },
                    {
                        'name': 'Victoria',
                        'state_code': 'VIC',
                        'cities': ['Melbourne', 'Geelong', 'Ballarat', 'Bendigo', 'Warrnambool']
                    },
                    {
                        'name': 'Queensland',
                        'state_code': 'QLD',
                        'cities': ['Brisbane', 'Gold Coast', 'Sunshine Coast', 'Cairns', 'Townsville']
                    },
                    {
                        'name': 'Western Australia',
                        'state_code': 'WA',
                        'cities': ['Perth', 'Fremantle', 'Mandurah', 'Bunbury', 'Geraldton']
                    }
                ]
            },
            {
                'name': 'Germany',
                'iso_code': 'DE',
                'iso3_code': 'DEU',
                'phone_code': '49',
                'currency': 'EUR',
                'currency_symbol': 'EUR',
                'timezone': 'Europe/Berlin',
                'flag_emoji': 'DE',
                'states': [
                    {
                        'name': 'Bavaria',
                        'state_code': 'BY',
                        'cities': ['Munich', 'Nuremberg', 'Augsburg', 'Regensburg', 'Wurzburg']
                    },
                    {
                        'name': 'Berlin',
                        'state_code': 'BE',
                        'cities': ['Berlin']
                    },
                    {
                        'name': 'Hamburg',
                        'state_code': 'HH',
                        'cities': ['Hamburg']
                    },
                    {
                        'name': 'North Rhine-Westphalia',
                        'state_code': 'NW',
                        'cities': ['Cologne', 'Dusseldorf', 'Dortmund', 'Essen', 'Bonn']
                    }
                ]
            },
            {
                'name': 'France',
                'iso_code': 'FR',
                'iso3_code': 'FRA',
                'phone_code': '33',
                'currency': 'EUR',
                'currency_symbol': 'EUR',
                'timezone': 'Europe/Paris',
                'flag_emoji': 'FR',
                'states': [
                    {
                        'name': 'Ile-de-France',
                        'state_code': 'IDF',
                        'cities': ['Paris', 'Versailles', 'Saint-Denis', 'Boulogne-Billancourt', 'Nanterre']
                    },
                    {
                        'name': 'Provence-Alpes-Cote dAzur',
                        'state_code': 'PAC',
                        'cities': ['Marseille', 'Nice', 'Toulon', 'Aix-en-Provence', 'Avignon']
                    },
                    {
                        'name': 'Auvergne-Rhone-Alpes',
                        'state_code': 'ARA',
                        'cities': ['Lyon', 'Grenoble', 'Saint-Etienne', 'Clermont-Ferrand', 'Annecy']
                    },
                    {
                        'name': 'Occitanie',
                        'state_code': 'OCC',
                        'cities': ['Toulouse', 'Montpellier', 'Nimes', 'Perpignan', 'Carcassonne']
                    }
                ]
            }
        ]

        # Populate countries, states, and cities
        for country_data in countries_data:
            country, created = Country.objects.get_or_create(
                name=country_data['name'],
                defaults={
                    'iso_code': country_data['iso_code'],
                    'iso3_code': country_data['iso3_code'],
                    'phone_code': country_data['phone_code'],
                    'currency': country_data['currency'],
                    'currency_symbol': country_data['currency_symbol'],
                    'timezone': country_data['timezone'],
                    'flag_emoji': country_data['flag_emoji']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created country: {country.name}'))
            
            # Create states for this country
            for state_data in country_data['states']:
                state, state_created = State.objects.get_or_create(
                    name=state_data['name'],
                    country=country,
                    defaults={'state_code': state_data['state_code']}
                )
                
                if state_created:
                    self.stdout.write(self.style.SUCCESS(f'  Created state: {state.name}'))
                
                # Create cities for this state
                for city_name in state_data['cities']:
                    city, city_created = City.objects.get_or_create(
                        name=city_name,
                        state=state
                    )
                    
                    if city_created:
                        self.stdout.write(self.style.SUCCESS(f'    Created city: {city.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated countries, states, and cities!'))
