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

class AccommodationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing accommodations.

    Allows searching, filtering, and viewing details of available accommodations.
    Distance filtering is available when specifying a campus ID and maximum distance.
    """
    queryset = Accommodation.objects.all()
    serializer_class = AccommodationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'type']
    ordering_fields = ['price', 'beds', 'bedrooms', 'created_at']
    ppermission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Filter accommodations based on query parameters.

        Supports filtering by type, price range, number of beds/bedrooms, and distance from campus.
        """
        queryset = Accommodation.objects.all()

        # Apply filters from query parameters
        accommodation_type = self.request.query_params.get('type')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        min_beds = self.request.query_params.get('min_beds')
        min_bedrooms = self.request.query_params.get('min_bedrooms')
        available_from = self.request.query_params.get('available_from')
        available_until = self.request.query_params.get('available_until')
        university_code = self.request.query_params.get('university')

        if university_code:
            queryset = queryset.filter(universities__code=university_code)
        if available_from and available_until:
            # First, filter by the accommodation's overall availability
            queryset = queryset.filter(
                available_from__lte=available_from,
                available_until__gte=available_until
            )
            # Then exclude accommodations with overlapping reservations
            reserved_ids = Reservation.objects.filter(
                status__in=['pending', 'confirmed'],
                start_date__lt=available_until,
                end_date__gt=available_from
            ).values_list('accommodation_id', flat=True)
            queryset = queryset.exclude(id__in=reserved_ids)
        if accommodation_type:
            queryset = queryset.filter(type=accommodation_type)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if min_beds:
            queryset = queryset.filter(beds__gte=min_beds)
        if min_bedrooms:
            queryset = queryset.filter(bedrooms__gte=min_bedrooms)

        # Handle distance filtering
        near_campus_id = self.request.query_params.get('near_campus_id')
        max_distance = self.request.query_params.get('max_distance')

        if near_campus_id:
            try:
                campus = Location.objects.get(id=near_campus_id, is_campus=True)

                # Convert queryset to list to manipulate
                accommodations = list(queryset)

                # Calculate distances
                for accommodation in accommodations:
                    accommodation.distance = calculate_distance(
                        (campus.latitude, campus.longitude),
                        (accommodation.location.latitude, accommodation.location.longitude)
                    )

                # Filter by distance if max_distance is provided
                if max_distance:
                    before_count = len(accommodations)
                    accommodations = [a for a in accommodations if a.distance <= float(max_distance)]
                    after_count = len(accommodations)

                # Sort by distance (always do this if near_campus_id is provided)
                accommodations.sort(key=lambda a: a.distance)

                return accommodations
            except Location.DoesNotExist:
                pass
            except Exception:
                pass

        return queryset


    def list(self, request, *args, **kwargs):
        """Override list to include distance in the response"""
        queryset = self.get_queryset()

        # If it's a list, it's been processed for distance
        if isinstance(queryset, list):
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

            # Add distance to each item
            for i, item in enumerate(data):
                item['distance'] = queryset[i].distance

            return Response(data)

        # Otherwise, use the standard pagination approach
        return super().list(request, *args, **kwargs)


