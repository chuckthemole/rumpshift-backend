from django.urls import path
from .views import (
    arduino_test,
    log_from_client,
    arduino_task_update,
    get_tasks,
    arduino_task_status,
    remove_machine,
    add_machine,
    get_machine,
    get_machines,
    delete_all_machines,
    arduino_wakeup,
    update_wakeup_payload
)

urlpatterns = [
    path("test/", arduino_test, name="arduino_test"),
    path("log-from-client/", log_from_client, name="log_from_client"),

    # Task endpoints
    path("arduino/task-update/", arduino_task_update, name="arduino_task_update"),
    path("arduino/get-tasks/", get_tasks, name="get_tasks"),
    path("arduino/task-status/<str:ip>/",
         arduino_task_status, name="arduino_task_status"),
    path("arduino/wakeup/<str:machine_id>/",
         arduino_wakeup, name="arduino_wakeup"),
    path("arduino/wakeup/<str:machine_id>/update",
         update_wakeup_payload, name="update_wakeup_payload"),

    # Machine endpoints
    path("arduino/remove-machine/", remove_machine, name="remove_machine"),
    path("arduino/add-machine/", add_machine, name="add_machine"),
    path("arduino/get-machine/<str:identifier>/", get_machine, name="get_machine"),
    path("arduino/get-machines/", get_machines, name="get_machines"),
    path("arduino/delete-machines/", delete_all_machines, name="delete_machines")
]
