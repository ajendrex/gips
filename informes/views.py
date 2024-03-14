from django.http import HttpResponse
from django.shortcuts import render

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
