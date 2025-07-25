from django.urls import path
from .views import ArduinoStatus

urlpatterns = [
    path('status/', ArduinoStatus.as_view(), name='arduino-status'),
]
