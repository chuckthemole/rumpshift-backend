from apps.notion_api.utils import send_to_notion  # utility function
from django.http import JsonResponse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from shared.utils.enums.notion import NotionAction, NotionConstants

logger = logging.getLogger(__name__)

# Disable CSRF for Arduino requests (since no CSRF token will be sent)


@csrf_exempt
def arduino_test(request):
    if request.method == "POST":
        try:
            # Try to parse JSON if Arduino sends it
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            data = {"error": "Invalid JSON"}

        print("Received from Arduino:", data)  # Logs to console
        # Make response minimal for arduino
        return HttpResponse("OK", content_type="text/plain")

    return HttpResponse("POST required", status=405)


@csrf_exempt
def log_from_client(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        source = data.get("source")
        target_api = data.get("target_api")
        meta = data.get("meta", {})
        payload = data.get("payload", {})

        logger.info(
            f"Received log from {source} for {target_api}: {payload}, meta: {meta}")

        if target_api == "notion":
            # default to creating a page
            mode = meta.get("mode", NotionAction.CREATE_PAGE)
            page_id = meta.get("page_id")  # optional

            status, result = send_to_notion(
                source, payload, mode=mode, page_id=page_id)
            logger.info(f"Notion response: {status}, {result}")

        else:
            logger.warning(
                f"Unknown target API '{target_api}', skipping relay")

        return JsonResponse({
            "status": "success",
            "message": "Log received",
            "echo": {
                "source": source,
                "target_api": target_api,
                "meta": meta
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
