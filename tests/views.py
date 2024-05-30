from time import sleep
from typing import Dict, Any

from django.http import JsonResponse
from rest_framework.generics import RetrieveAPIView, CreateAPIView

from tests.models import Resultado
from tests.serializers import TestSerializer, RespuestaLikertNOASSerializer
from utils.request import get_and_validate_acceso


class TestView(RetrieveAPIView):
    serializer_class = TestSerializer

    def get_object(self):
        acceso = get_and_validate_acceso(self.request)
        return acceso.acceso_test.test


class RespuestaLikertNOASView(CreateAPIView):
    serializer_class = RespuestaLikertNOASSerializer

    def dispatch(self, request, *args, **kwargs):
        # return JsonResponse({"message": "No se puede acceder a esta vista."}, status=403)
        # sleep(1)
        return super().dispatch(request, *args, **kwargs)

    def get_serializer_context(self) -> Dict[str, Any]:
        acceso = get_and_validate_acceso(self.request)
        resultado, created = Resultado.objects.get_or_create(acceso=acceso)

        context = super().get_serializer_context()
        context["resultado"] = resultado
        return context
