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


