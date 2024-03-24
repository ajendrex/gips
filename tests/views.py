from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, AuthenticationFailed
from rest_framework.generics import RetrieveAPIView

from tests.models import AccesoTestPersona
from tests.serializers import TestSerializer


class TestView(RetrieveAPIView):
    serializer_class = TestSerializer

    def get_object(self):
        try:
            acceso = AccesoTestPersona.objects.get(codigo=self.request.GET.get('codigo'))
        except AccesoTestPersona.DoesNotExist:
            raise AuthenticationFailed("No parece que tengas acceso a un test.")

        return acceso.acceso_test.test
