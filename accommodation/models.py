from django.db import models


class University(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)  # HKU, HKUST, CUHK

    def __str__(self):
        return self.name

class Owner(models.Model):
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Location(models.Model):
    """Model for storing geographical locations"""
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)  # Made optional
    latitude = models.FloatField(null=True, blank=True)  # Made optional
    longitude = models.FloatField(null=True, blank=True)  # Made optional
    geo_address = models.CharField(max_length=255, blank=True)  # from DATA.GOV.HK
    is_campus = models.BooleanField(default=False)  # Flag for campus locations

    def __str__(self):
        return self.name



class Accommodation(models.Model):
    ACCOMMODATION_TYPES = [
        ('hall', 'mini hall'),
        ('room', 'room'),
        ('flat', 'flat'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=ACCOMMODATION_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    beds = models.IntegerField()
    bedrooms = models.IntegerField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='accommodations')
    available_from = models.DateField()
    available_until = models.DateField()
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='accommodations')
    created_at = models.DateTimeField(auto_now_add=True)
    universities = models.ManyToManyField('University', related_name='accommodations')

    def __str__(self):
        return self.title


# Update Reservation model