# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..models import ArduinoTask, ArduinoMachine
from django.utils import timezone


@api_view(['POST'])
def arduino_task_update(request):
    """
    Create or update a task for a machine.
    - For status 'kill', deletes the task.
    - For 'running' or 'paused', updates/creates the task.
    Expects JSON: { "ip": "...", "alias": "...", "taskName": "...", "notes": "...", "status": "running|paused|kill" }
    """
    data = request.data
    ip = data.get('ip')
    alias = data.get('alias')
    task_name = data.get('taskName')
    notes = data.get('notes', '')
    task_status = data.get('status')

    if not ip or not task_status:
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    # Only require alias and task_name for non-kill operations
    if task_status != 'kill' and (not alias or not task_name):
        return Response(
            {"error": "Missing required fields for running/paused task"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Get or create the machine
        machine, _ = ArduinoMachine.objects.get_or_create(
            ip=ip, defaults={'alias': alias})

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

        # Create or update the task for this machine
        task, created = ArduinoTask.objects.get_or_create(
            machine=machine,
            task_name=task_name,
            defaults={'notes': notes, 'status': 'idle'}
        )
        task.status = task_status
        task.notes = notes
        machine.alias = alias  # Update machine alias if changed
        machine.save()
        task.save()

        return Response({
            "message": f"Task {task_status}",
            "task": {
                "ip": machine.ip,
                "alias": machine.alias,
                "taskName": task.task_name,
                "notes": task.notes,
                "status": task.status
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def arduino_task_status(request, ip):
    """
    Returns all running tasks for a given machine IP.
    """
    try:
        machine = ArduinoMachine.objects.get(ip=ip)
        tasks = ArduinoTask.objects.filter(machine=machine, status='running')
        return Response([
            {"taskName": t.task_name, "notes": t.notes, "status": t.status}
            for t in tasks
        ])
    except ArduinoMachine.DoesNotExist:
        return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)


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
        "date_time": formatted_time,
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
    if not ip:
        return Response({"error": "Missing machine IP"}, status=status.HTTP_400_BAD_REQUEST)

    try:
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
    ip = request.data.get('ip')
    alias = request.data.get('alias')
    if not ip or not alias:
        return Response({"error": "Missing required fields"}, status=400)
    machine, created = ArduinoMachine.objects.get_or_create(
        ip=ip, defaults={'alias': alias})
    if not created:
        machine.alias = alias
        machine.save()
    return Response({"ip": machine.ip, "alias": machine.alias}, status=200)


@api_view(['GET'])
def get_machine(request, ip):
    """
    Returns the details of a single machine by IP.
    """
    try:
        machine = ArduinoMachine.objects.get(ip=ip)
        # Include all tasks (optional: you can filter by status if needed)
        tasks = machine.tasks.all()
        data = {
            "ip": machine.ip,
            "alias": machine.alias,
            "tasks": [
                {
                    "taskName": t.task_name,
                    "notes": t.notes,
                    "status": t.status
                } for t in tasks
            ]
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
                "ip": m.ip,
                "alias": m.alias,
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
