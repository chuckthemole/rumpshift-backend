# End points:
# root
ADMIN_URL = 'admin/'
NOTION_API = 'api/notion/'
ARDUINO_CONSUMER_API = 'api/arduino_consumer/'
RUMPSHIFT_ANALYTICS_API = 'api/rumpshift-analytics/'

# notion_api
GET_NOTION_DATABASE = 'db/<str:db_id>/'
SEARCH_NOTION_DATABASES = 'databases/'
LIST_NOTION_PAGE_CONTENTS = 'page/<str:page_id>/'
LOG_TO_NOTION = 'log/'
