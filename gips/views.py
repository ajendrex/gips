from django.conf import settings
from django.http import HttpResponse
from django.views import View
import os


class FrontendFileViewBase(View):
    filename = None

    def get(self, request):
        try:
            with open(self.file_path()) as f:
                return HttpResponse(f.read())
        except FileNotFoundError:
            return HttpResponse(
                """
                Ha ocurrido un error.
                """,
                status=501,
            )

    @classmethod
    def file_path(cls):
        return settings.BASE_DIR / 'frontend/tests/build' / cls.filename


class FrontendAppView(FrontendFileViewBase):
    filename = 'index.html'


class ManifestView(FrontendFileViewBase):
    filename = 'manifest.json'
