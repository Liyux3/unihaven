from rest_framework import serializers
from .models import Owner, Location, Accommodation, Reservation, Rating, Notification, University


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ['id', 'name', 'contact']


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'code']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'latitude', 'longitude', 'geo_address', 'is_campus']


class AccommodationSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=Owner.objects.all(),
        source='owner',
        write_only=True
    )
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True
    )
    average_rating = serializers.SerializerMethodField()
    universities = UniversitySerializer(many=True, read_only=True)
    university_ids = serializers.PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        source='universities',
        write_only=True,
        many=True,
        required = False  # Make it optional for now
    )

    class Meta:
        model = Accommodation
        fields = [
            'id', 'title', 'description', 'type', 'price',
            'beds', 'bedrooms', 'location', 'location_id',
            'available_from', 'available_until', 'owner', 'owner_id',
            'universities', 'university_ids', 'average_rating', 'created_at'
        ]

    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if not ratings:
            return None
        return sum(r.score for r in ratings) / len(ratings)


