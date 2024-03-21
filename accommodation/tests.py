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

