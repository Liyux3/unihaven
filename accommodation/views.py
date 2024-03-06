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



class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    ppermission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status == 'cancelled':
            return Response({'status': 'reservation already cancelled'})

        # prevent cancelling confirmed or completed reservations
        if reservation.status in ['confirmed', 'completed']:
            return Response(
                {'error': 'Confirmed or completed reservations cannot be cancelled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation.status = 'cancelled'
        reservation.save()

        # Get the university
        university = reservation.university

        # Create notification with university
        Notification.objects.create(
            type='reservation_cancelled',
            message=f'Reservation for {reservation.accommodation.title} by {reservation.user_id} from {reservation.start_date} to {reservation.end_date} has been cancelled',
            reservation=reservation,
            university=university
        )

        recipient_email = 'cedars@hku.hk'  # Default
        if university.code == 'HKUST':
            recipient_email = 'housing@hkust.edu.hk'  # Example
        elif university.code == 'CUHK':
            recipient_email = 'housing@cuhk.edu.hk'  # Example

        # Send email notification
        from django.core.mail import send_mail
        send_mail(
            'Reservation Cancelled',
            f'Reservation for {reservation.accommodation.title} by {reservation.user_id} from {reservation.start_date} to {reservation.end_date} has been cancelled',
            'unihaven@example.com',
            [recipient_email],
            fail_silently=False,
        )

        return Response({'status': 'reservation cancelled'})

    def create(self, request, *args, **kwargs):
        """
        Create a reservation for this accommodation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the university from the request or use a default
        university_id = request.data.get('university_id')

        # Get the accommodation_id before validation
        accommodation_id = request.data.get('accommodation_id')
        if not accommodation_id:
            return Response(
                {'error': 'accommodation_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the dates
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the dates are within the accommodation's availability period
        accommodation = Accommodation.objects.get(id=accommodation_id)
        if start_date < accommodation.available_from.isoformat() or end_date > accommodation.available_until.isoformat():
            return Response(
                {'error': 'Requested dates are outside the accommodation\'s availability period'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for overlapping reservations
        overlapping = Reservation.objects.filter(
            accommodation_id=accommodation_id,
            status__in=['pending', 'confirmed'],  # Only check active reservations
            start_date__lt=end_date,
            end_date__gt=start_date
        ).exists()

        if overlapping:
            return Response(
                {'error': 'The accommodation is already reserved for part or all of the requested period'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Continue with reservation creation
        reservation = serializer.save()

        if university_id:
            try:
                university = University.objects.get(id=university_id)
            except University.DoesNotExist:
                university = University.objects.get(code='HKU')  # Default to HKU
        else:
            university = University.objects.get(code='HKU')  # Default to HKU

        reservation.university = university
        reservation.save()

        # Create notification with university
        university = reservation.university
        Notification.objects.create(
            type='reservation_created',
            message=f'New reservation for {reservation.accommodation.title} by {reservation.member_name} from {reservation.start_date} to {reservation.end_date}',
            reservation=reservation,
            university=university
        )

        # Send email notification with contact info
        from django.core.mail import send_mail
        message = f"""
                New reservation details:

                Accommodation: {reservation.accommodation.title}
                Member Name: {reservation.member_name}
                Member Email: {reservation.member_email}
                Member Phone: {reservation.member_phone}
                Period: {reservation.start_date} to {reservation.end_date}
                Status: {reservation.status}
                Created: {reservation.created_at}
                University: {university.name}
                """

        # Send to the appropriate university email
        recipient_email = 'cedars@hku.hk'  # Default
        if university.code == 'HKUST':
            recipient_email = 'housing@hkust.edu.hk'  # Example
        elif university.code == 'CUHK':
            recipient_email = 'housing@cuhk.edu.hk'  # Example

        send_mail(
            'New Reservation',
            message,
            'unihaven@example.com',
            [recipient_email],
            fail_silently=True,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status == 'confirmed':
            return Response({'status': 'reservation already confirmed'})

        if reservation.status == 'cancelled':
            return Response({'error': 'Cannot confirm a cancelled reservation'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Update status
        reservation.status = 'confirmed'
        reservation.save()

        # Get the university
        university = reservation.university

        # Create notification with university
        Notification.objects.create(
            type='reservation_confirmed',
            message=f'Reservation for {reservation.accommodation.title} by {reservation.user_id} from {reservation.start_date} to {reservation.end_date} has been confirmed',
            reservation=reservation,
            university=university
        )

        # Send email notification
        recipient_email = 'cedars@hku.hk'  # Default
        if university.code == 'HKUST':
            recipient_email = 'housing@hkust.edu.hk'
        elif university.code == 'CUHK':
            recipient_email = 'housing@cuhk.edu.hk'

        from django.core.mail import send_mail
        send_mail(
            'Reservation Confirmed',
            f'Your reservation for {reservation.accommodation.title} from {reservation.start_date} to {reservation.end_date} has been confirmed',
            'unihaven@example.com',
            [recipient_email],
            fail_silently=False,
        )
        return Response({'status': 'reservation confirmed'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status == 'completed':
            return Response({'status': 'reservation already completed'})

        if reservation.status != 'confirmed':
            return Response({'error': 'Only confirmed reservations can be completed'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Update status
        reservation.status = 'completed'
        reservation.save()

        # Get the university
        university = reservation.university

        # Create notification with university
        Notification.objects.create(
            type='reservation_completed',  # Add this to NOTIFICATION_TYPES
            message=f'Reservation for {reservation.accommodation.title} by {reservation.user_id} from {reservation.start_date} to {reservation.end_date} has been completed',
            reservation=reservation,
            university=university
        )

        # Send email notification to member encouraging them to rate their stay
        from django.core.mail import send_mail
        send_mail(
            'Reservation Completed - Rate Your Stay',
            f'Your reservation for {reservation.accommodation.title} from {reservation.start_date} to {reservation.end_date} has been completed. We hope you enjoyed your stay! Please take a moment to rate your experience.',
            'unihaven@example.com',
            [reservation.member_email],
            fail_silently=False,
        )

        return Response({'status': 'reservation completed'})

    # In ReservationViewSet
    def get_queryset(self):
        queryset = super().get_queryset()

        # Check if we're accessing the member or admin endpoint
        path = self.request.path
        is_admin = 'admin' in path

        # Filter by university
        university_code = self.request.query_params.get('university')
        if university_code:
            queryset = queryset.filter(university__code=university_code)

        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # For member endpoints, filter by user_id
        if not is_admin:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        return queryset


class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        accommodation_id = request.data.get('accommodation')
        reservation_id = request.data.get('reservation_id')

        # If reservation_id is provided, check that specific reservation
        if reservation_id:
            try:
                reservation = Reservation.objects.get(id=reservation_id)
                # Check if this reservation is completed and confirmed
                today = timezone.now().date()
                if not (reservation.status == 'completed' and reservation.end_date < today):
                    return Response(
                        {'error': 'You can only rate accommodations after completing a reservation'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Reservation.DoesNotExist:
                return Response(
                    {'error': 'Reservation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Otherwise check if the user had any completed reservation for this accommodation
            today = timezone.now().date()
            completed_reservation = Reservation.objects.filter(
                user_id=user_id,
                accommodation_id=accommodation_id,
                status='completed',
                end_date__lt=today
            ).exists()

            if not completed_reservation:
                return Response(
                    {'error': 'You can only rate accommodations after completing a reservation'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Check if user already rated this accommodation
        if Rating.objects.filter(accommodation_id=accommodation_id, user_id=user_id).exists():
            return Response(
                {"detail": "You have already rated this accommodation. Please edit your existing rating."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().create(request, *args, **kwargs)


# Add to views.py
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    ppermission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by university if provided
        university_code = self.request.query_params.get('university')
        if university_code:
            queryset = queryset.filter(university__code=university_code)

        return queryset
