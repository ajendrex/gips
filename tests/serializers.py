from rest_framework import serializers

from tests.models import Test, PreguntaLikertNOAS, RespuestaLikertNOAS


class PreguntaLikertNOASSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreguntaLikertNOAS
        fields = ("id", "texto")


class TestSerializer(serializers.ModelSerializer):
    preguntalikertnoas_set = PreguntaLikertNOASSerializer(many=True)

    class Meta:
        model = Test
        fields = ("preguntalikertnoas_set",)


class RespuestaLikertNOASSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resultado = self.context["resultado"]

    class Meta:
        model = RespuestaLikertNOAS
        fields = ("pregunta", "alternativa")

    def create(self, validated_data):
        respuesta = self.Meta.model(**validated_data)
        respuesta, created = RespuestaLikertNOAS.objects.update_or_create(
            resultado=self.resultado,
            pregunta=respuesta.pregunta,
            defaults={
                "alternativa": respuesta.alternativa,
                "puntaje": respuesta.puntaje,  # actualizado en RespuestaLikertNOAS.save()
            },
        )
        return respuesta
