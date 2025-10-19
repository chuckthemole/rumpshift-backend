# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import ArduinoTask, ArduinoMachine
from django.utils import timezone
from shared.logger.logger import get_logger

# -----------------------------------------------------------------------------
# Logger
# -----------------------------------------------------------------------------
logger = get_logger(__name__)


@api_view(['POST'])
def arduino_task_update(request):
    """
    Create or update a task for a machine.
    - For status 'kill', deletes the task.
    - For 'running' or 'paused', updates/creates the task.
    Expects JSON: 
      { "id": <optional>, "ip": <optional>, "alias": "...", "taskName": "...", "notes": "...", "status": "running|paused|kill" }
    Either 'id' or 'ip' must be provided.
    """
    data = request.data
    machine_id = data.get('id')
    ip = data.get('ip')
    alias = data.get('alias')
    task_name = data.get('taskName')
    notes = data.get('notes', '')
    task_status = data.get('status')

    if not task_status:
        return Response({"error": "Missing required field: status"}, status=status.HTTP_400_BAD_REQUEST)

    # Only require alias and task_name for non-kill operations
    if task_status != 'kill' and (not alias or not task_name):
        return Response(
            {"error": "Missing required fields for running/paused task"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not (machine_id or ip):
        return Response({"error": "Provide either 'id' or 'ip' to identify the machine"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Determine lookup
        if machine_id:
            lookup_field = 'id'
            lookup_value = machine_id
        else:
            lookup_field = 'ip'
            lookup_value = ip

        filter_kwargs = {lookup_field: lookup_value}

        # Get or create the machine
        machine, _ = ArduinoMachine.objects.get_or_create(
            defaults={'alias': alias}, **filter_kwargs)

        if task_status == 'kill':
            # Delete the specific task if it exists
            task_qs = ArduinoTask.objects.filter(
                machine=machine, task_name=task_name)
            deleted_count = task_qs.count()
            task_qs.delete()
            return Response(
                {"message": f"Task killed, {deleted_count} task(s) removed"},
                status=status.HTTP_200_OK
            )

        # Create or update the task
        task, created = ArduinoTask.objects.get_or_create(
            machine=machine,
            task_name=task_name,
            defaults={'notes': notes, 'status': 'idle'}
        )
        task.status = task_status
        task.notes = notes
        machine.alias = alias  # Update alias if changed
        machine.save()
        task.save()

        return Response({
            "message": f"Task {task_status}",
            "task": {
                "id": machine.id,
                "ip": machine.ip,
                "alias": machine.alias,
                "taskName": task.task_name,
                "notes": task.notes,
                "status": task.status
            }
        }, status=status.HTTP_200_OK)

    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def arduino_task_status(request, identifier):
    """
    Returns all running tasks for a given machine by IP or ID.

    URL example:
    /api/arduino_task_status/<identifier>/

    `identifier` can be:
      - machine IP (string)
      - machine ID (numeric)

    Example:
    /api/arduino_task_status/192.168.0.5/
    /api/arduino_task_status/3/
    """
    machine = None

    try:
        # Try to parse identifier as an integer ID
        machine_id = int(identifier)
        machine = ArduinoMachine.objects.get(id=machine_id)
    except ValueError:
        # Not an integer, treat as IP
        try:
            machine = ArduinoMachine.objects.get(ip=identifier)
        except ArduinoMachine.DoesNotExist:
            return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)
    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)

    tasks = ArduinoTask.objects.filter(machine=machine, status='running')
    return Response([
        {"taskName": t.task_name, "notes": t.notes, "status": t.status}
        for t in tasks
    ])


@api_view(['GET'])
def arduino_wakeup(request, machine_id):
    """
    Return the current time and notify the backend that this machine is awake.
    """
    try:
        machine = ArduinoMachine.objects.get(id=machine_id)
    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    formatted_time = now.isoformat(timespec='milliseconds')

    return Response({
        "datetime": formatted_time,
        "payload": machine.wakeup_payload or {}
    })


@api_view(['POST'])
def update_wakeup_payload(request, machine_id):
    """
    Update the wakeup_payload for a given Arduino machine.
    Expected JSON body:
    {
        "payload": { ... }  # arbitrary JSON object
    }
    """
    try:
        machine = ArduinoMachine.objects.get(id=machine_id)
    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)

    payload = request.data.get("payload")
    if payload is None:
        return Response({"error": "Missing 'payload' in request body"}, status=status.HTTP_400_BAD_REQUEST)

    machine.wakeup_payload = payload
    machine.save(update_fields=["wakeup_payload"])

    return Response({
        "message": "wakeup_payload updated successfully",
        "payload": machine.wakeup_payload
    })


@api_view(['GET'])
def get_tasks(request):
    """
    Returns all tasks grouped by machine.
    Only includes tasks that are running or paused.
    """
    tasks = ArduinoTask.objects.filter(
        status__in=['running', 'paused']).select_related('machine')
    data = [
        {
            "id": t.machine.id,
            "ip": t.machine.ip,
            "alias": t.machine.alias,
            "taskName": t.task_name,
            "notes": t.notes,
            "status": t.status
        }
        for t in tasks
    ]
    return Response(data)


@api_view(['POST'])
def remove_machine(request):
    """
    Removes a machine if it has no active (running or paused) tasks.
    Expects JSON payload: { "ip": "192.168.0.10" }
    """
    ip = request.data.get('ip')
    id = request.data.get('id')
    if not ip and not id:
        return Response({"error": "Missing identifier"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        machine = None
        if id:
            machine = ArduinoMachine.objects.get(id=id)
        elif ip:
            machine = ArduinoMachine.objects.get(ip=ip)

        # Check for active tasks
        active_tasks = machine.tasks.filter(status__in=['running', 'paused'])
        if active_tasks.exists():
            return Response(
                {"error": "Cannot remove machine with active tasks"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete idle tasks (if any) and then the machine
        idle_tasks = machine.tasks.filter(status='idle')
        count = idle_tasks.count()
        idle_tasks.delete()
        machine.delete()

        return Response(
            {"message":
                f"Machine removed successfully, {count} idle task(s) deleted"},
            status=status.HTTP_200_OK
        )

    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def add_machine(request):
    try:
        logger.debug("add_machine called with data: %s", request.data)

        alias = request.data.get('alias')
        ip = request.data.get('ip', None)  # Optional field

        if not alias:
            logger.warning("Missing required field: alias")
            return Response({"error": "Missing required field: alias"}, status=status.HTTP_400_BAD_REQUEST)

        logger.debug("Using alias='%s', ip='%s'", alias, ip)

        try:
            if ip is None:
                logger.debug(
                    "IP is None, creating machine with alias=%s", alias)
                machine = ArduinoMachine.objects.create(alias=alias, ip=None)
                created = True  # because you always created it
            else:
                machine, created = ArduinoMachine.objects.get_or_create(
                    ip=ip,
                    defaults={'alias': alias}
                )
                logger.debug(
                    "get_or_create called with ip=%s, alias=%s", ip, alias
                )
            logger.debug(
                "Machine returned: %s, created: %s", machine, created
            )
        except Exception as db_exc:
            logger.exception("Database error during get_or_create")
            return Response({"error": f"Database error: {str(db_exc)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not created:
            try:
                logger.debug(
                    "Machine already exists, updating alias to '%s'", alias)
                machine.alias = alias
                machine.save()
            except Exception as save_exc:
                logger.exception("Error saving updated machine")
                return Response({"error": f"Error updating machine: {str(save_exc)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {"ip": machine.ip, "alias": machine.alias},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Unhandled exception in add_machine")
        return Response(
            {"error": f"Unhandled exception: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_machine(request, identifier):
    """
    Returns the details of a single machine by IP or ID.
    Mirrors the structure of get_machines for consistency.
    Backward compatible: existing IP-based requests still work.
    """
    try:
        # Detect if identifier looks like an integer → treat as ID
        lookup_field = "id" if identifier.isdigit() else "ip"
        filter_kwargs = {lookup_field: identifier}

        machine = (
            ArduinoMachine.objects
            .prefetch_related('tasks')
            .get(**filter_kwargs)
        )

        # Filter tasks (optional)
        tasks = machine.tasks.filter(status__in=['running', 'paused'])

        data = {
            "id": machine.id,
            "ip": machine.ip,
            "alias": machine.alias,
            "wakeup_payload": machine.wakeup_payload,
            "time": {
                "created_at": machine.created_at,
                "update_at": machine.updated_at,
            },
            "tasks": [
                {
                    "taskName": t.task_name,
                    "notes": t.notes,
                    "status": t.status,
                }
                for t in tasks
            ],
        }

        return Response(data, status=status.HTTP_200_OK)

    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_machines(request):
    """
    Returns a list of all machines with their tasks.
    Only includes tasks that are running or paused by default.
    """
    try:
        machines = ArduinoMachine.objects.all().prefetch_related('tasks')
        data = []
        for m in machines:
            tasks = m.tasks.filter(
                status__in=['running', 'paused'])  # optional filter
            data.append({
                "id": m.id,
                "ip": m.ip,
                "alias": m.alias,
                "wakeup_payload": m.wakeup_payload,
                "time": {
                    "created_at": m.created_at,
                    "update_at": m.updated_at
                },
                "tasks": [
                    {
                        "taskName": t.task_name,
                        "notes": t.notes,
                        "status": t.status
                    } for t in tasks
                ]
            })
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def delete_all_machines(request):
    """
    Deletes all machines and their tasks.
    - If `force_clean=true` is passed, deletes everything regardless of task status.
    - Otherwise, only deletes machines that have no active tasks (running/paused).
    """
    try:
        force_clean = str(request.data.get(
            "force_clean", "false")).lower() == "true"

        if force_clean:
            # Nuke everything
            ArduinoTask.objects.all().delete()
            count, _ = ArduinoMachine.objects.all().delete()
            return Response(
                {"message": f"Force deleted {count} machines and all tasks"},
                status=status.HTTP_200_OK
            )

        # Strict mode: only delete idle machines
        machines = ArduinoMachine.objects.all()
        removed_count = 0
        skipped = 0
        for m in machines:
            active_tasks = m.tasks.filter(status__in=["running", "paused"])
            if active_tasks.exists():
                skipped += 1
                continue
            # delete idle tasks first
            m.tasks.filter(status="idle").delete()
            m.delete()
            removed_count += 1

        return Response(
            {"message": f"Deleted {removed_count} machines, skipped {skipped} with active tasks"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
