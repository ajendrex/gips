from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.static import serve

from informes.models import Resultado


# Create your views here.
def verificar(request, clave_archivo):
    if request.method == "POST":
        clave_acceso = request.POST.get("clave_acceso")

        try:
            resultado = Resultado.objects.get(clave_archivo=clave_archivo, clave_acceso=clave_acceso)
        except Resultado.DoesNotExist:
            return render(request, "informes/no_verificado.html", {"clave_archivo": clave_archivo})

        # responder el contenido del informe
        try:
            with resultado.informe.open('rb') as pdf:
                # Leer el contenido del archivo
                pdf_content = pdf.read()

                # Crear una respuesta HTTP con el contenido del PDF
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="%s"' % resultado.informe.name

                return response
        except Exception as e:
            # Manejar el error o devolver una respuesta de error
            return render(request, "informes/error_verificacion.html")

    return render(request, "informes/verificar.html")


@login_required
def serve_protected_media(request, path):
    """
    Sirve los archivos de media con protección basada en autenticación.
    """
    print("hola!!!")
    document_root = settings.MEDIA_ROOT
    return serve(request, path, document_root=document_root)
