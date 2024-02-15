from django.contrib import admin
from .models import Owner, Accommodation, Reservation, Rating

admin.site.register(Owner)
admin.site.register(Accommodation)
admin.site.register(Reservation)
admin.site.register(Rating)