from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from arduino_client.client import ArduinoClient

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

arduino = ArduinoClient(settings.ARDUINO_HOST, settings.ARDUINO_PORT)


class StartPumpView(APIView):
    def post(self, request):
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
