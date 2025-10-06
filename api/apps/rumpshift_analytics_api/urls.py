from django.urls import path
from .views import ExampleDataView, CounterSessionDataView

urlpatterns = [
    path('example/', ExampleDataView.as_view(), name='example_data'),
    path('counter-session-data/', CounterSessionDataView.as_view(),
         name='counter_session_data'),

]
