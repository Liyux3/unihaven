
from django.core.management.base import BaseCommand
from accommodation.models import Location, Owner, Accommodation, Reservation
from django.utils import timezone
import datetime
from accommodation.utils import lookup_address
import random


class Command(BaseCommand):
    help = 'Adds HKU campus locations to the database'

    def handle(self, *args, **kwargs):
        # Campus data from the email
        campuses = [
            {
                'name': 'Main Campus',
                'address': 'Pokfulam Road, Hong Kong',
                'latitude': 22.28405,
                'longitude': 114.13784,
                'geo_address': 'HKU Main Campus',
                'is_campus': True
            },
            {
                'name': 'Sassoon Road Campus',
                'address': 'Sassoon Road, Hong Kong',
                'latitude': 22.2675,
                'longitude': 114.12881,
                'geo_address': 'HKU Sassoon Road Campus',
                'is_campus': True
            },
            {
                'name': 'Swire Institute of Marine Science',
                'address': 'Cape d\'Aguilar, Hong Kong',
                'latitude': 22.20805,
                'longitude': 114.26021,
                'geo_address': 'HKU Swire Institute of Marine Science',
                'is_campus': True
            },
            {
                'name': 'Kadoorie Centre',
                'address': 'Shek Kong, New Territories',
                'latitude': 22.43022,
                'longitude': 114.11429,
                'geo_address': 'HKU Kadoorie Centre',
                'is_campus': True
            },
            {
                'name': 'Faculty of Dentistry',
                'address': 'Sai Ying Pun, Hong Kong',
                'latitude': 22.28649,
                'longitude': 114.14426,
                'geo_address': 'HKU Faculty of Dentistry',
                'is_campus': True
            }
        ]

        # Add campuses to database
        for campus_data in campuses:
            location, created = Location.objects.get_or_create(
                name=campus_data['name'],
                defaults=campus_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Added campus: {location.name}'))
            else:
                # Update existing campus
                for key, value in campus_data.items():
                    setattr(location, key, value)
                location.save()
                self.stdout.write(self.style.SUCCESS(f'Updated campus: {location.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully added/updated campus locations'))


class Command(BaseCommand):
    help = 'Adds real Hong Kong accommodations to the database using the API'

    def handle(self, *args, **kwargs):
        # Create some owners
        owners = []
        owner_data = [
            {'name': 'John Wong', 'contact': 'jwong@example.com'},
            {'name': 'Sarah Chen', 'contact': '9876-5432'},
            {'name': 'David Lam', 'contact': 'dlam@realestate.hk'},
        ]

        for data in owner_data:
            owner, created = Owner.objects.get_or_create(
                name=data['name'],
                defaults={'contact': data['contact']}
            )
            owners.append(owner)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created owner: {owner.name}'))

        # Real buildings in Hong Kong
        buildings = [
            # Near Main Campus
            'Pokfield Road',
            'Belcher\'s Hill',
            'Imperial Kennedy',
            'The Belcher\'s',

            # Near Sassoon Road
            'Residence Bel-Air',
            'Baguio Villa',
            'Royalton',

            # Near Faculty of Dentistry
            'Island Crest',
            'The Summa',
            'Artisan House',

            # Others
            'Grand Promenade',
            'Festival City',
            'Taikoo Shing',
            'Harbour Grand',
            'The Arch'
        ]

        # Accommodation types and their price ranges
        accommodation_types = [
            {'type': 'mini_hall', 'min_price': 3000, 'max_price': 8000, 'beds': [1, 2], 'bedrooms': [1]},
            {'type': 'room', 'min_price': 5000, 'max_price': 12000, 'beds': [1], 'bedrooms': [1]},
            {'type': 'flat', 'min_price': 15000, 'max_price': 40000, 'beds': [1, 2, 3], 'bedrooms': [1, 2, 3]},
        ]

        # Find campuses for distance reference
        campuses = Location.objects.filter(is_campus=True)
        self.stdout.write(f'Found {len(campuses)} campuses for reference')

        # Add accommodations
        added_count = 0
        for building_name in buildings:
            self.stdout.write(f'Looking up: {building_name}')

            # Use our API function to get location data
            location_data = lookup_address(building_name)

            if location_data:
                # Create the location
                location, created = Location.objects.get_or_create(
                    name=location_data['name'],
                    defaults={
                        'address': location_data['address'],
                        'latitude': location_data['latitude'],
                        'longitude': location_data['longitude'],
                        'geo_address': location_data['geo_address'],
                        'is_campus': False
                    }
                )

                if not created:
                    self.stdout.write(f'Location already exists: {location.name}')
                    continue

                # Create 1-3 accommodations in this building
                for _ in range(random.randint(1, 3)):
                    # Pick a random type
                    accom_type = random.choice(accommodation_types)

                    # Generate random details
                    price = random.randint(accom_type['min_price'], accom_type['max_price'])
                    beds = random.choice(accom_type['beds'])
                    bedrooms = random.choice(accom_type['bedrooms'])

                    # Random available dates (starting within 30 days, lasting 3-12 months)
                    start_date = timezone.now().date() + datetime.timedelta(days=random.randint(0, 30))
                    end_date = start_date + datetime.timedelta(days=random.randint(90, 365))

                    # Random owner
                    owner = random.choice(owners)

                    # Create accommodation
                    accommodation = Accommodation.objects.create(
                        title=f"{accom_type['type'].replace('_', ' ').title()} in {location.name}",
                        description=f"A beautiful {accom_type['type'].replace('_', ' ')} located in {location.name}. Close to public transport and amenities.",
                        type=accom_type['type'],
                        price=price,
                        beds=beds,
                        bedrooms=bedrooms,
                        location=location,
                        available_from=start_date,
                        available_until=end_date,
                        owner=owner
                    )

                    added_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created accommodation: {accommodation.title}'))
            else:
                self.stdout.write(self.style.WARNING(f'Could not find location data for: {building_name}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully added {added_count} accommodations'))




class Command(BaseCommand):
    help = 'Adds test reservations to the database, including completed ones'

    def handle(self, *args, **kwargs):
        # Sample user IDs
        user_ids = ['0', '1', '2']

        # Sample member info
        members = [
            {'name': 'John Student', 'email': 'john@connect.hku.hk', 'phone': '1234-5678'},
            {'name': 'Jane Student', 'email': 'jane@connect.hku.hk', 'phone': '8765-4321'},
            {'name': 'Sam Student', 'email': 'sam@connect.hku.hk', 'phone': '5555-5555'},
        ]

        # Get all accommodations
        accommodations = list(Accommodation.objects.all())

        if not accommodations:
            self.stdout.write(self.style.ERROR('No accommodations found. Please add accommodations first.'))
            return

        # Current date for reference
        today = timezone.now().date()

        # Create reservations
        for user_id, member in zip(user_ids, members):
            # Create active reservations (1-2 per user)
            for _ in range(random.randint(1, 2)):
                accommodation = random.choice(accommodations)

                Reservation.objects.create(
                    accommodation=accommodation,
                    user_id=user_id,
                    member_name=member['name'],
                    member_email=member['email'],
                    member_phone=member['phone'],
                    status='confirmed',
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(10, 30))
                )
                self.stdout.write(self.style.SUCCESS(f'Created active reservation for user {user_id}'))

            # Create completed reservations (1-3 per user)
            for _ in range(random.randint(1, 3)):
                # Find an accommodation with end date in the past
                past_accommodations = [a for a in accommodations if a.available_until < today]

                if not past_accommodations:
                    # Create an accommodation with past end date
                    accommodation = random.choice(accommodations)

                    # Set end date to past
                    past_end_date = today - datetime.timedelta(days=random.randint(1, 30))

                    # This is just for testing, so we'll directly modify the accommodation
                    accommodation.available_until = past_end_date
                    accommodation.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'Updated accommodation {accommodation.id} with past end date'))
                else:
                    accommodation = random.choice(past_accommodations)

                Reservation.objects.create(
                    accommodation=accommodation,
                    user_id=user_id,
                    member_name=member['name'],
                    member_email=member['email'],
                    member_phone=member['phone'],
                    status='confirmed',
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(60, 90))
                )
                self.stdout.write(self.style.SUCCESS(f'Created completed reservation for user {user_id}'))

            # Create some cancelled reservations (0-2 per user)
            for _ in range(random.randint(0, 2)):
                accommodation = random.choice(accommodations)

                Reservation.objects.create(
                    accommodation=accommodation,
                    user_id=user_id,
                    member_name=member['name'],
                    member_email=member['email'],
                    member_phone=member['phone'],
                    status='cancelled',
                    created_at=timezone.now() - datetime.timedelta(days=random.randint(10, 30))
                )
                self.stdout.write(self.style.SUCCESS(f'Created cancelled reservation for user {user_id}'))

        self.stdout.write(self.style.SUCCESS('Successfully added test reservations'))