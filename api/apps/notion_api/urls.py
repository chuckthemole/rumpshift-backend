from django.urls import path
from .views import get_notion_database, search_notion_databases, list_notion_page_contents, log_to_notion
from django.conf import settings

urlpatterns = [
    path(settings.GET_NOTION_DATABASE, get_notion_database),
    path(settings.SEARCH_NOTION_DATABASES, search_notion_databases),
    path(settings.LIST_NOTION_PAGE_CONTENTS,  list_notion_page_contents),
    path(settings.LOG_TO_NOTION, log_to_notion),
]
