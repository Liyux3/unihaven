from rest_framework import viewsets, filters, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg
from django.shortcuts import render
from django.utils import timezone

from .models import Owner, Location, Accommodation, Reservation, Rating, Notification, University
from .serializers import OwnerSerializer, LocationSerializer, AccommodationSerializer, ReservationSerializer, RatingSerializer, NotificationSerializer, UniversitySerializer
from .utils import calculate_distance, lookup_address

def test_search_view(request):
    """Simple view to test the search functionality"""
    campuses = Location.objects.filter(is_campus=True)
    return render(request, 'test_search.html', {'campuses': campuses})

def specialist_dashboard(request):
    """View for the CEDARS specialist dashboard"""
    owners = Owner.objects.all()
    permission_classes = [permissions.AllowAny]
    return render(request, 'specialist_dashboard.html', {'owners': owners})

class OwnerViewSet(viewsets.ModelViewSet):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
    ppermission_classes = [permissions.AllowAny]

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    ppermission_classes = [permissions.AllowAny]

class LocationViewSet(viewsets.GenericViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    ppermission_classes = [permissions.AllowAny]
    authentication_classes = []

    # In LocationViewSet
    @action(detail=False, methods=['post'])
    def lookup_address(self, request):
        """
        Lookup address using DATA.GOV.HK API
        ---
        request_body:
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            building_name:
                                type: string
                                description: Name of the building to lookup
                        required:
                            - building_name
        responses:
            201:
                description: Address found and location created
            400:
                description: Invalid request or address not found
        """
        building_name = request.data.get('name')
        if not building_name:
            return Response({'error': 'Building name is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Use the function from utils.py
        location_data = lookup_address(building_name)

        if location_data:
            serializer = self.get_serializer(data=location_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Failed to lookup address'}, status=status.HTTP_400_BAD_REQUEST)
