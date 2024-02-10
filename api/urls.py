# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accommodation.views import (
    OwnerViewSet, LocationViewSet, AccommodationViewSet,
    ReservationViewSet, RatingViewSet, NotificationViewSet, UniversityViewSet
)

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'accommodations', AccommodationViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'ratings', RatingViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'owners', OwnerViewSet)
router.register(r'universities', UniversityViewSet)


schema_view = get_schema_view(
   openapi.Info(
      title="UniHaven API",
      default_version='v1',
      description="API for UniHaven accommodation service",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@unihaven.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # Add other paths as needed
]

