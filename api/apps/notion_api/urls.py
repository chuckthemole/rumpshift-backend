from django.urls import path
from .views import get_notion_database, search_notion_databases, list_notion_page_contents, log_to_notion, run_coffee_grinder_script, run_notion_manager_script, create_log_database, clear_database, delete_database, log_to_notion_temp
from django.conf import settings
from api.url_constants import GET_NOTION_DATABASE, SEARCH_NOTION_DATABASES, LIST_NOTION_PAGE_CONTENTS, LOG_TO_NOTION

urlpatterns = [
    path(GET_NOTION_DATABASE, get_notion_database),
    path(SEARCH_NOTION_DATABASES, search_notion_databases),
    path(LIST_NOTION_PAGE_CONTENTS,  list_notion_page_contents),
    path(LOG_TO_NOTION, log_to_notion),
    path("run-coffee-grinder/", run_coffee_grinder_script,
         name="run_coffee_grinder"),
    path("run-notion-manager/", run_notion_manager_script,
         name="run_notion_manager"),
    path("create-log-database/", create_log_database,
         name="create_log_database"),
    path("clear-database/", clear_database,
         name="clear_database"),
    path("delete-database/", delete_database,
         name="delete_database"),

    path("log_temp/", log_to_notion_temp, name="log_to_notion_temp")
]
