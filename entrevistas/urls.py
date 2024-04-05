from django.urls import path

from entrevistas.views import horarios_disponibles

urlpatterns = [
    path('horarios-disponibles/', horarios_disponibles, name='test-view'),
]
