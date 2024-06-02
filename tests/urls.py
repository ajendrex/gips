from django.urls import path

from tests.views import TestView, RespuestaLikertNOASView, iniciar_test, finalizar_test

urlpatterns = [
    path('tests/', TestView.as_view(), name='test-view'),
    path('tests/iniciar/', iniciar_test, name='iniciar-test'),
    path('tests/finalizar/', finalizar_test, name='finalizar-test'),
    path('respuestas-likert-noas/', RespuestaLikertNOASView.as_view(), name='respuesta-likert-noas-view'),
]
