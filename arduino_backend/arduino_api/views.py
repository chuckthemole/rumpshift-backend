from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from arduino_client.client import ArduinoClient

from django.http import JsonResponse
# Arduino won't send CSRF tokens
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


class StartPumpView(APIView):
    def post(self, request):
        arduino = ArduinoClient(settings.ARDUINO_HOST, settings.ARDUINO_PORT)
        duration = request.data.get("duration", 1000)
        arduino.send_command("start_pump", {"duration": duration})
        return Response({"status": "sent"})


# In-memory storage (just for prototyping)
TOGGLE_STATES = {}


@require_http_methods(["GET", "POST"])
@csrf_exempt
def toggle_view(request, switch_id):
    if request.method == "GET":
        state = TOGGLE_STATES.get(switch_id, False)
        return JsonResponse({"state": state})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            state = bool(data.get("state", False))
            TOGGLE_STATES[switch_id] = state
            return JsonResponse({"state": state})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def receive_print_job(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        # Example: expect {"printer_id": "office1", "job": "Hello world"}
        printer_id = data.get("printer_id")
        job_data = data.get("job")

        if not printer_id or not job_data:
            return JsonResponse({"status": "error", "message": "Missing fields"}, status=400)

        # TODO: enqueue to a print system, save to DB, etc.
        print(f"Received print job for printer {printer_id}: {job_data}")

        return JsonResponse({"status": "ok", "message": "Job received"})

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)
