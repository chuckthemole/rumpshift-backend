from django.urls import path
from .views import arduino_test, log_from_client
from django.conf import settings

urlpatterns = [
    path("test/", arduino_test, name="arduino_test"),
    path("log-from-client/", log_from_client, name="log_from_client"),

]
