from rest_framework import serializers

from entrevistas.models import Entrevista


class EntrevistaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrevista
        fields = ('id', 'fecha_inicio', 'fecha_fin')
