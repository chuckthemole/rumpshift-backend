from django.urls import path
from .views import get_notion_database, search_notion_databases, list_notion_page_contents

urlpatterns = [
    path('db/<str:db_id>/', get_notion_database),
    path('databases/', search_notion_databases),
    path('page/<str:page_id>/',  list_notion_page_contents),
]
