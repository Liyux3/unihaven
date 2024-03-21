from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import University, Owner, Location, Accommodation, Reservation, Rating, Notification
from .utils import calculate_distance
from decimal import Decimal
import datetime


class DistanceCalculationTest(TestCase):
    """Test the distance calculation function"""

    def test_calculate_distance(self):
        """Test distance calculation between two points"""
        # HKU Main Campus and HKUST Campus
        hku = (22.28405, 114.13784)
        hkust = (22.33584, 114.26355)

        # Calculate distance
        distance = calculate_distance(hku, hkust)

        # The actual distance should be around 13-14 km
        self.assertGreater(distance, 12)
        self.assertLess(distance, 15)

    def test_calculate_distance_same_point(self):
        """Test distance calculation when points are the same"""
        point = (22.28405, 114.13784)

        # Calculate distance
        distance = calculate_distance(point, point)

        # Distance should be zero or very close to it
        self.assertLess(distance, 0.001)

    def test_calculate_distance_north_south(self):
        """Test distance calculation along north-south axis"""
        point1 = (22.0, 114.0)
        point2 = (23.0, 114.0)  # 1 degree north

        # Calculate distance
        distance = calculate_distance(point1, point2)

        # 1 degree of latitude is approximately 111 km
        self.assertGreater(distance, 110)
        self.assertLess(distance, 112)

    def test_calculate_distance_east_west(self):
        """Test distance calculation along east-west axis"""
        point1 = (22.0, 114.0)
        point2 = (22.0, 115.0)  # 1 degree east

        # Calculate distance
        distance = calculate_distance(point1, point2)

        # 1 degree of longitude at this latitude is approximately 102 km
        self.assertGreater(distance, 100)
        self.assertLess(distance, 105)


class UniversityAPITest(TestCase):
    """Test the University API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.hku = University.objects.create(name='The University of Hong Kong', code='HKU')
        self.hkust = University.objects.create(name='Hong Kong University of Science and Technology', code='HKUST')

    def test_list_universities(self):
        """Test retrieving a list of universities"""
        url = reverse('university-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_university(self):
        """Test retrieving a single university"""
        url = reverse('university-detail', args=[self.hku.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'HKU')

    def test_create_university(self):
        """Test creating a new university"""
        url = reverse('university-list')
        data = {'name': 'The Chinese University of Hong Kong', 'code': 'CUHK'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(University.objects.count(), 3)

    def test_update_university(self):
        """Test updating a university"""
        url = reverse('university-detail', args=[self.hku.id])
        data = {'name': 'HKU - The University of Hong Kong', 'code': 'HKU'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.hku.refresh_from_db()
        self.assertEqual(self.hku.name, 'HKU - The University of Hong Kong')

    def test_delete_university(self):
        """Test deleting a university"""
        url = reverse('university-detail', args=[self.hkust.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(University.objects.count(), 1)


class LocationAPITest(TestCase):
    """Test the Location API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.location = Location.objects.create(
            name='Test Campus',
            address='123 Test Street',
            latitude=22.28405,
            longitude=114.13784,
            geo_address='Test GeoAddress',
            is_campus=True
        )

    def test_lookup_address(self):
        """Test the address lookup endpoint"""
        url = reverse('location-lookup-address')
        data = {'name': 'Central Plaza'}
        response = self.client.post(url, data, format='json')
        # Note: This might fail if the external API is unavailable
        # We're just testing our endpoint works, not the external API
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])


class AccommodationAPITest(TestCase):
    """Test the Accommodation API endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create universities
        self.hku = University.objects.create(name='The University of Hong Kong', code='HKU')
        self.hkust = University.objects.create(name='Hong Kong University of Science and Technology', code='HKUST')

        # Create owner
        self.owner = Owner.objects.create(name='Test Owner', contact='test@example.com')

        # Create location
        self.location = Location.objects.create(
            name='Test Location',
            address='123 Test St',
            latitude=22.28,
            longitude=114.13,
            geo_address='Test GeoAddress'
        )

        # Create campus
        self.campus = Location.objects.create(
            name='Test Campus',
            address='456 Campus Rd',
            latitude=22.29,
            longitude=114.14,
            geo_address='Campus GeoAddress',
            is_campus=True
        )

        # Create accommodation
        self.accommodation = Accommodation.objects.create(
            title='Test Accommodation',
            description='Test Description',
            type='room',
            price=1000,
            beds=1,
            bedrooms=1,
            location=self.location,
            available_from='2025-01-01',
            available_until='2025-12-31',
            owner=self.owner
        )
        self.accommodation.universities.add(self.hku)

    def test_list_accommodations(self):
        """Test retrieving a list of accommodations"""
        url = reverse('accommodation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_accommodation(self):
        """Test retrieving a single accommodation"""
        url = reverse('accommodation-detail', args=[self.accommodation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Accommodation')

    def test_create_accommodation(self):
        """Test creating a new accommodation"""
        url = reverse('accommodation-list')
        data = {
            'title': 'New Accommodation',
            'description': 'New Description',
            'type': 'flat',
            'price': '2000.00',
            'beds': 2,
            'bedrooms': 2,
            'location_id': self.location.id,
            'available_from': '2025-02-01',
            'available_until': '2025-11-30',
            'owner_id': self.owner.id,
            'university_ids': [self.hku.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Accommodation.objects.count(), 2)

    def test_update_accommodation(self):
        """Test updating an accommodation"""
        url = reverse('accommodation-detail', args=[self.accommodation.id])
        data = {
            'title': 'Updated Accommodation',
            'description': 'Updated Description',
            'type': 'room',
            'price': '1000.00',
            'beds': 1,
            'bedrooms': 1,
            'location_id': self.location.id,
            'available_from': '2025-01-01',
            'available_until': '2025-12-31',
            'owner_id': self.owner.id,
            'university_ids': [self.hku.id, self.hkust.id]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.accommodation.refresh_from_db()
        self.assertEqual(self.accommodation.title, 'Updated Accommodation')
        self.assertEqual(self.accommodation.universities.count(), 2)

    def test_delete_accommodation(self):
        """Test deleting an accommodation"""
        url = reverse('accommodation-detail', args=[self.accommodation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Accommodation.objects.count(), 0)

    def test_filter_by_university(self):
        """Test filtering accommodations by university"""
        # Create a second university
        cuhk = University.objects.create(name='The Chinese University of Hong Kong', code='CUHK')

        # Create a second accommodation for HKUST only
        accommodation2 = Accommodation.objects.create(
            title='HKUST Accommodation',
            description='HKUST Description',
            type='room',
            price=1200,
            beds=1,
            bedrooms=1,
            location=self.location,
            available_from='2025-01-01',
            available_until='2025-12-31',
            owner=self.owner
        )
        accommodation2.universities.add(self.hkust)

        # Create a third accommodation managed by both HKU and HKUST
        accommodation3 = Accommodation.objects.create(
            title='Shared Accommodation',
            description='Managed by multiple universities',
            type='flat',
            price=1500,
            beds=2,
            bedrooms=1,
            location=self.location,
            available_from='2025-01-01',
            available_until='2025-12-31',
            owner=self.owner
        )
        accommodation3.universities.add(self.hku)
        accommodation3.universities.add(self.hkust)

        # Test filtering by HKU - should return first and third accommodations
        url = reverse('accommodation-list') + '?university=HKU'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        titles = [item['title'] for item in response.data]
        self.assertIn('Test Accommodation', titles)
        self.assertIn('Shared Accommodation', titles)

        # Test filtering by HKUST - should return second and third accommodations
        url = reverse('accommodation-list') + '?university=HKUST'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        titles = [item['title'] for item in response.data]
        self.assertIn('HKUST Accommodation', titles)
        self.assertIn('Shared Accommodation', titles)

        # Test filtering by CUHK - should return no accommodations
        url = reverse('accommodation-list') + '?university=CUHK'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Test filtering by non-existent university code
        url = reverse('accommodation-list') + '?university=FAKE'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filter_by_distance(self):
        """Test filtering accommodations by distance from campus"""
        url = reverse('accommodation-list') + f'?near_campus_id={self.campus.id}&max_distance=10'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Since our test location is within 10km of the campus, it should be included
        self.assertEqual(len(response.data), 1)

    def test_distance_sorting_without_max_distance(self):
        """Test sorting accommodations by distance from campus without max_distance"""
        # Create a second accommodation further away
        location2 = Location.objects.create(
            name='Far Location',
            address='999 Far St',
            latitude=22.4,  # Further north
            longitude=114.2,
            geo_address='Far GeoAddress'
        )

        accommodation2 = Accommodation.objects.create(
            title='Far Accommodation',
            description='Far Description',
            type='room',
            price=800,
            beds=1,
            bedrooms=1,
            location=location2,
            available_from='2025-01-01',
            available_until='2025-12-31',
            owner=self.owner
        )
        accommodation2.universities.add(self.hku)

        # Test sorting by distance without max_distance
        url = reverse('accommodation-list') + f'?near_campus_id={self.campus.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Both should have distance field
        self.assertIn('distance', response.data[0])
        self.assertIn('distance', response.data[1])

        # Verify they're sorted by distance (closest first)
        self.assertLess(float(response.data[0]['distance']), float(response.data[1]['distance']))

class ReservationAPITest(TestCase):
    """Test the Reservation API endpoints"""

    def setUp(self):
        self.client = APIClient()

        # Create universities
        self.hku = University.objects.create(name='The University of Hong Kong', code='HKU')
        self.hkust = University.objects.create(name='Hong Kong University of Science and Technology', code='HKUST')

        # Create owner
        self.owner = Owner.objects.create(name='Test Owner', contact='test@example.com')

        # Create location
        self.location = Location.objects.create(
            name='Test Location',
            address='123 Test St',
            latitude=22.28,
            longitude=114.13,
            geo_address='Test GeoAddress'
        )

        # Create accommodation
        self.accommodation = Accommodation.objects.create(
            title='Test Accommodation',
            description='Test Description',
            type='room',
            price=1000,
            beds=1,
            bedrooms=1,
            location=self.location,
            available_from='2025-01-01',
            available_until='2025-12-31',
            owner=self.owner
        )
        self.accommodation.universities.add(self.hku)
        self.accommodation.universities.add(self.hkust)

        # Create reservation with start_date and end_date
        self.reservation = Reservation.objects.create(
            accommodation=self.accommodation,
            user_id='test_user',
            member_name='Test User',
            member_email='test@example.com',
            member_phone='1234 5678',
            status='pending',
            university=self.hku,
            start_date='2025-02-01',
            end_date='2025-02-15'
        )

    def test_list_reservations(self):
        """Test retrieving a list of reservations"""
        url = reverse('reservation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_reservation(self):
        """Test retrieving a single reservation"""
        url = reverse('reservation-detail', args=[self.reservation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['member_name'], 'Test User')

    def test_create_reservation(self):
        """Test creating a new reservation"""
        url = reverse('reservation-list')
        data = {
            'accommodation_id': self.accommodation.id,
            'user_id': 'new_user',
            'member_name': 'New User',
            'member_email': 'new@example.com',
            'member_phone': '9876 5432',
            'university_id': self.hku.id,
            'start_date': '2025-03-01',
            'end_date': '2025-03-15'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 2)

        # Check that a notification was created
        self.assertEqual(Notification.objects.count(), 1)

    def test_cannot_create_overlapping_reservation(self):
        """Test that overlapping reservations are rejected"""
        url = reverse('reservation-list')
        data = {
            'accommodation_id': self.accommodation.id,
            'user_id': 'overlap_user',
            'member_name': 'Overlap User',
            'member_email': 'overlap@example.com',
            'member_phone': '5555 5555',
            'university_id': self.hku.id,
            'start_date': '2025-02-10',  # Overlaps with existing reservation
            'end_date': '2025-02-20'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 1)  # Still only one reservation

    def test_cannot_reserve_outside_availability(self):
        """Test that reservations outside the accommodation's availability period are rejected"""
        url = reverse('reservation-list')
        data = {
            'accommodation_id': self.accommodation.id,
            'user_id': 'outside_user',
            'member_name': 'Outside User',
            'member_email': 'outside@example.com',
            'member_phone': '4444 4444',
            'university_id': self.hku.id,
            'start_date': '2024-12-01',  # Before available_from
            'end_date': '2024-12-15'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try another one after available_until
        data['start_date'] = '2026-01-01'
        data['end_date'] = '2026-01-15'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Reservation.objects.count(), 1)  # Still only one reservation

    def test_cancel_reservation(self):
        """Test cancelling a reservation"""
        url = reverse('reservation-cancel', args=[self.reservation.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'cancelled')

        # Check that a notification was created
        self.assertEqual(Notification.objects.count(), 1)

    def test_confirm_reservation(self):
        """Test confirming a reservation"""
        # First make sure it's pending
        self.assertEqual(self.reservation.status, 'pending')

        url = reverse('reservation-confirm', args=[self.reservation.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'confirmed')

        # Check that a notification was created
        self.assertEqual(Notification.objects.count(), 1)

    def test_complete_reservation(self):
        """Test completing a reservation"""
        # First confirm it
        self.reservation.status = 'confirmed'
        self.reservation.save()

        url = reverse('reservation-complete', args=[self.reservation.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'completed')

        # Check that a notification was created
        self.assertEqual(Notification.objects.count(), 1)

    def test_cannot_complete_unconfirmed_reservation(self):
        """Test that only confirmed reservations can be completed"""
        # Ensure it's pending
        self.assertEqual(self.reservation.status, 'pending')

        url = reverse('reservation-complete', args=[self.reservation.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'pending')

    def test_filter_reservations_by_university(self):
        """Test filtering reservations by university"""
        # Create a second reservation for HKUST
        reservation2 = Reservation.objects.create(
            accommodation=self.accommodation,
            user_id='hkust_user',
            member_name='HKUST User',
            member_email='hkust@example.com',
            member_phone='8765 4321',
            status='pending',
            university=self.hkust,
            start_date='2025-03-01',
            end_date='2025-03-15'
        )

        # Test filtering by HKU
        url = reverse('reservation-list') + '?university=HKU'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['member_name'], 'Test User')

        # Test filtering by HKUST
        url = reverse('reservation-list') + '?university=HKUST'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['member_name'], 'HKUST User')

