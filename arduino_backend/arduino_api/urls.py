from django.urls import path
from .views import StartPumpView, toggle_view, receive_print_job

urlpatterns = [
    path("start-pump/", StartPumpView.as_view()),
    path('toggle/<str:switch_id>/', toggle_view, name='toggle'),
    path("print-job/", receive_print_job, name="receive_print_job"),

]
