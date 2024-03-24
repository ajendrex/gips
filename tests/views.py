from typing import Dict, Any

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import RetrieveAPIView, CreateAPIView

from tests.models import AccesoTestPersona, Resultado
from tests.serializers import TestSerializer, RespuestaLikertNOASSerializer


class TestView(RetrieveAPIView):
    serializer_class = TestSerializer

    def get_object(self):
        try:
            acceso = AccesoTestPersona.objects.get(codigo=self.request.GET.get('codigo'))
        except AccesoTestPersona.DoesNotExist:
            raise AuthenticationFailed("No parece que tengas acceso a un test.")

        return acceso.acceso_test.test


class RespuestaLikertNOASView(CreateAPIView):
    serializer_class = RespuestaLikertNOASSerializer

    def get_serializer_context(self) -> Dict[str, Any]:
        context = super().get_serializer_context()
        try:
            acceso = AccesoTestPersona.objects.get(codigo=self.request.GET.get("codigo"))
        except AccesoTestPersona.DoesNotExist:
            raise AuthenticationFailed("No parece que tengas acceso a un test.")

        resultado, created = Resultado.objects.get_or_create(acceso=acceso)
        context["resultado"] = resultado
        return context
