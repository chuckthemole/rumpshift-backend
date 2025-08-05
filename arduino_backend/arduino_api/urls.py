from django.urls import path
from .views import StartPumpView, toggle_view

urlpatterns = [
    path("start-pump/", StartPumpView.as_view()),
    path('toggle/<str:switch_id>/', toggle_view, name='toggle'),
]
