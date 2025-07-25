from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ArduinoStatus(APIView):
    def get(self, request):
        # Placeholder for status from Arduino
        data = {
            'temperature': 25.0,
            'mode': 'IDLE',
            'message': 'Arduino status OK'
        }
        return Response(data, status=status.HTTP_200_OK)