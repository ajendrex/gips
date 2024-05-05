from django.urls import path

from entrevistas.views import crear_entrevista, horarios_disponibles

urlpatterns = [
    path('horarios-disponibles/', horarios_disponibles, name='horarios-disponibles'),
    path('crear-entrevista/', crear_entrevista, name='crear-entrevista'),
]
