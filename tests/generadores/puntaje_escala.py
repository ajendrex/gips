import base64
from io import BytesIO

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ValidationError
from qrcode.image.pil import PilImage
from rut_chile import rut_chile
from weasyprint import HTML

from tests.generadores.base import Generador
from tests.models import Gentilicio


class GeneradorPuntajeEscala(Generador):
    def _validate(self):
        if not self.resultado:
            raise ValidationError("Falta el resultado")

        rut = self.resultado.persona.rut

        if not rut_chile.is_valid_rut(rut):
            raise ValidationError(f"El rut {rut} no es válido")

        test = self.resultado.test

        if not test.tramos.exists():
            raise ValidationError("El test no tiene tramos")

        categorias_preguntas = test.preguntalikertnoas_set.values_list('categoria', flat=True).distinct()

        for categoria in categorias_preguntas:
            if categoria not in test.categorias_tramos:
                raise ValidationError(f"La categoría {categoria} no está en los tramos de la prueba")

        if "GENERAL" not in test.categorias_tramos:
            raise ValidationError("La categoría General no está en los tramos de la prueba")

    def _validar_puede_generar_informe(self):
        self._validate()

        entrevista = getattr(self.resultado, 'entrevista', None)

        nacion = self.resultado.persona.nacionalidad
        if not Gentilicio.objects.filter(pais=nacion).exists():
            pais = self.resultado.persona.get_nacionalidad_display()
            raise ValidationError(f"No existe gentilicio para el país de la persona ({pais})")

        if not entrevista:
            raise ValidationError("Falta la entrevista")

        if not entrevista.observaciones:
            raise ValidationError("La entrevista no tiene observaciones")

        persona = self.resultado.persona

        if not persona.nombre_completo:
            raise ValidationError("Falta el nombre completo de la persona")

        if not persona.rut:
            raise ValidationError("Falta el rut de la persona")

        if not persona.nacionalidad:
            raise ValidationError("Falta la nacionalidad de la persona")

    def _evaluar(self) -> dict:
        evaluacion = {}

        puntajes = {
            **{
                categoria: {"puntaje": 0}
                for categoria in self.resultado.test.categorias_tramos
            }
        }

        for respuesta in self.resultado.respuestalikertnoas_set.all():
            categoria = respuesta.pregunta.categoria
            puntajes[categoria]["puntaje"] += respuesta.puntaje
            puntajes["GENERAL"]["puntaje"] += respuesta.puntaje

        for categoria in self.resultado.test.categorias_tramos:
            for tramo in self.resultado.test.tramos.filter(categoria=categoria):
                if tramo.puntaje_minimo <= puntajes[categoria]["puntaje"] <= tramo.puntaje_maximo:
                    puntajes[categoria]["nivel"] = tramo.nombre
                    puntajes[categoria]["texto"] = tramo.texto
                    break

        if puntajes["GENERAL"]["nivel"] == "BAJO":
            evaluacion["observaciones_initial"] = (
                "En entrevista presenta una conducta adecuada, ajustada a la situación, motivación por logro de "
                "objetivos, manejo de la ansiedad, preocupación por el autocuidado, tolerancia a la frustración "
                "frente a situaciones desconocidas o que requieren concentración y procesamiento cognitivo "
                "para toma de decisiones."
            )

        evaluacion["puntajes"] = puntajes

        return evaluacion

    def _generar_informe(self, qr_image: PilImage) -> bytes:
        p1 = self._generar_parrafo1()
        p2 = self._generar_parrafo2()
        p3 = self._generar_parrafo3()
        texto_no_planificada = self.resultado.evaluacion["puntajes"]["NO_PLANIFICADA"]["texto"]
        texto_atencional = self.resultado.evaluacion["puntajes"]["COGNITIVA"]["texto"]
        texto_motora = self.resultado.evaluacion["puntajes"]["MOTORA"]["texto"]

        output = BytesIO()
        qr_image.save(output, format="PNG")
        qr_image_uri = base64.b64encode(output.getvalue()).decode('ascii')

        html = f"""
        <html>
          <head>{self._estilos()}</head>
          <body>
            <h1>CERTIFICADO</h1>
            <h2>EVALUACIÓN PSICOLÓGICA<br>DEL CONTROL DE LOS IMPULSOS</h2>
            <p>{p1}</p>
            <p>{p2}</p>
            <p>{p3}</p>
            <ul>
              <li>{texto_no_planificada}</li>
              <li>{texto_atencional}</li>
              <li>{texto_motora}</li>
            </ul>
            <div class="box-firma">
              <img src="informes/assets/firmas/pruiz.png" alt="Firma Pablo Ruiz Urbina" class="firma-img" />
              <hr>
              <p>Pablo Ruiz Urbina<br>Psicólogo<br><span>N° Reg: 123851</span></p>
            </div>
            <img src="data:image/png;base64,{qr_image_uri}" alt="Código QR">
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        print(soup.prettify())
        return HTML(string=html, base_url=settings.BASE_DIR).write_pdf()

    @staticmethod
    def _estilos() -> str:
        return """
        <style>
            h1, h2 {
                text-align: center;
            }
            p {
                text-align: justify;
            }
            li {
                text-align: justify;
                margin: 10px 0 10px 0;
            }
            .firma-img {
                width: 200px;
                height: auto;
                display: block;
                margin: auto;
            }
            .box-firma {
                width: 250px;
                margin: auto;
            }
            .box-firma p {
                text-align: center;
            }
        </style>
        """

    def _generar_parrafo1(self) -> str:
        persona = self.resultado.persona
        nombre_completo = persona.nombre_completo
        run = rut_chile.format_rut_with_dots(persona.rut)
        nacionalidad = Gentilicio.objects.get(pais=persona.nacionalidad).gentilicio

        tramo_general = self.resultado.evaluacion["puntajes"]["GENERAL"]["nivel"]

        if tramo_general == "BAJO":
            apto_no_apto = "apto"
        elif tramo_general == "MODERADO":
            apto_no_apto = "apto con reservas"
        else:
            apto_no_apto = "no apto"

        labor = "&lt;POR HACER?&gt;"

        return (
            "El profesional que firma este documento certifica que el Sr(a) "
            f"<b>{nombre_completo}</b> RUN <b>{run}</b> Nacionalidad <b>{nacionalidad}</b> ha realizado una evaluación "
            f"psicológica del control de los impulsos, encontrándole {apto_no_apto} para realizar labores de "
            f"{labor}."
        )

    def _generar_parrafo2(self):
        return self.resultado.entrevista.observaciones

    def _generar_parrafo3(self):
        texto_general = self.resultado.evaluacion["puntajes"]["GENERAL"]["texto"]
        return (
            f"Pruebas psicológicas indican un {texto_general}. Sub-escalas de impulsividad no planificada, atencional "
            "y motora (BIS-11) arrojan el siguiente resultado:"
        )