from django.urls import path
from . import views


urlpatterns = [
    path('student/', views.test_search_view, name='test_search'),
    path('specialist/', views.specialist_dashboard, name='specialist_dashboard'),
]

