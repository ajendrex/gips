from rest_framework import serializers

from tests.models import Test, PreguntaLikertNOAS


class PreguntaLikertNOASSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreguntaLikertNOAS
        fields = ("id", "texto")


class TestSerializer(serializers.ModelSerializer):
    preguntalikertnoas_set = PreguntaLikertNOASSerializer(many=True)

    class Meta:
        model = Test
        fields = ("preguntalikertnoas_set",)
