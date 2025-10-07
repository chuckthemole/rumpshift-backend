from django.urls import path
from .views import CounterSessionDataView

urlpatterns = [
    path(
        'counter-session-data/',
        CounterSessionDataView.as_view(),
        name='counter_session_data'),

]
