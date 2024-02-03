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
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='reservations')
    user_id = models.CharField(max_length=100)  # ID from CEDARS system
    member_name = models.CharField(max_length=100, default='')
    member_email = models.EmailField(default='')
    member_phone = models.CharField(max_length=20, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    university = models.ForeignKey('University', on_delete=models.CASCADE, related_name='reservations', null=True)
    start_date = models.DateField()  # Start date of the reservation
    end_date = models.DateField()  # End date of the reservation

    def __str__(self):
        return f"Reservation for {self.accommodation.title} by {self.user_id}"


class Rating(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='ratings')
    user_id = models.CharField(max_length=100)
    score = models.IntegerField(choices=[(i, i) for i in range(6)])  # 0-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['accommodation', 'user_id']

    def __str__(self):
        return f"Rating {self.score}/5 for {self.accommodation.title}"



class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reservation_created', 'Reservation Created'),
        ('reservation_cancelled', 'Reservation Cancelled'),
        ('reservation_confirmed', 'Reservation Confirmed'),
        ('reservation_completed', 'Reservation Completed'),
    ]

    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    university = models.ForeignKey('University', on_delete=models.CASCADE, related_name='notifications', null=True)

    def __str__(self):
        return f"{self.type} - {self.created_at}"

