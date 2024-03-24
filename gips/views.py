from django.conf import settings
from django.http import HttpResponse
from django.views import View
import os


class FrontendAppView(View):
    def get(self, request):
        try:
            with open(settings.BASE_DIR / 'frontend/tests/build/index.html') as f:
                return HttpResponse(f.read())
        except FileNotFoundError:
            return HttpResponse(
                """
                Ha ocurrido un error.
                """,
                status=501,
            )
