from django.urls import path

from tests.views import TestView, RespuestaLikertNOASView

urlpatterns = [
    path('tests/', TestView.as_view(), name='test-view'),
    path('respuestas_likert_noas/', RespuestaLikertNOASView.as_view(), name='respuesta-likert-noas-view'),
]
