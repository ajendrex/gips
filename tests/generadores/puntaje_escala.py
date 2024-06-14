import base64
from io import BytesIO

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

        nombre_resultado = (
            "APTO" if puntajes["GENERAL"]["nivel"] == "BAJO"
            else "CON_RESERVAS" if puntajes["GENERAL"]["nivel"] == "MODERADO"
            else "NO_APTO"
        )
        resultado_evaluacion = self.resultado.test.resultados_posibles.get(nombre=nombre_resultado)

        return evaluacion, resultado_evaluacion

    def _generar_informe(self, qr_image: PilImage) -> bytes:
        output = BytesIO()
        qr_image.save(output, format="PNG")
        qr_image_uri = base64.b64encode(output.getvalue()).decode('ascii')

        html = self._generar_html_informe(qr_image_uri)

        if settings.DEBUG:
            with open("informe.html", "w") as file:
                file.write(html)

        return HTML(string=self._generar_html_informe(qr_image_uri), base_url=settings.BASE_DIR).write_pdf()

    def _generar_html_informe(self, qr_image_uri: str) -> str:
        domain = settings.BASE_URL.replace("http://", "").replace("https://", "")
        sicologo = self.resultado.acceso.entrevistas.last().entrevistador

        html = f"""
                <html>
                  <head>{self._estilos()}</head>
                  <body>
                    <h1>CERTIFICADO EVALUACIÓN PSICOLÓGICA<br />CONTROL DE LOS IMPULSOS</h1>
                    <div class="informe">
                        {self.generar_html_evaluacion()}
                    </div>
                    <div class="box-firma">
                      <img src="{sicologo.firma.path}" alt="Firma {sicologo}" class="firma-img" />
                      <hr>
                      <p>{sicologo}<br>Psicólogo<br><span>N° Reg: {sicologo.nro_registro}</span></p>
                    </div>
                    <div class="verification">
                        <hr>
                        <div class="column image-column">
                            <img src="data:image/png;base64,{qr_image_uri}" alt="Código QR">
                        </div>
                        <div class="column content-column">
                            Para verificar la autenticidad escanee el código QR o visite<br>
                            <a
                             href="{settings.BASE_URL}/verificar/{self.resultado.acceso.codigo}"
                             >
                                {domain}/verificar/{self.resultado.acceso.codigo}
                            </a> e ingrese el código <b>{self.resultado.clave_archivo}</b><br>
                            Este documento fue emitido el {self.resultado.fecha_emision.strftime("%d/%m/%Y")} y caducará
                            el {self.resultado.fecha_vencimiento.strftime("%d/%m/%Y")}
                        </div>
                    </div>
                  </body>
                </html>
                """

        return html

    def generar_html_evaluacion(self) -> str:
        p1 = self._generar_parrafo1()
        p2 = self._generar_parrafo2()
        p3 = self._generar_parrafo3()
        texto_no_planificada = self.resultado.evaluacion["puntajes"]["NO_PLANIFICADA"]["texto"]
        texto_atencional = self.resultado.evaluacion["puntajes"]["COGNITIVA"]["texto"]
        texto_motora = self.resultado.evaluacion["puntajes"]["MOTORA"]["texto"]

        entrevista = self.resultado.acceso.entrevistas.last()

        if entrevista and entrevista.resultado_entrevista:
            apto_no_apto = entrevista.resultado_entrevista.texto
        else:
            tramo_general = self.resultado.evaluacion["puntajes"]["GENERAL"]["nivel"]

            if tramo_general == "BAJO":
                apto_no_apto = "apto"
            elif tramo_general == "MODERADO":
                apto_no_apto = "apto con reservas"
            else:
                apto_no_apto = "no apto"

        labor = self.resultado.acceso.get_cargo_display()

        return f"""
            <p>{p1}</p>
            <p>{p2}</p>
            <ul>
              <li>{texto_no_planificada}</li>
              <li>{texto_atencional}</li>
              <li>{texto_motora}</li>
            </ul>
            <p>{p3}</p>
            <p>En conclusión, se determina que el Sr(a) <b>{self.resultado.persona.nombre_completo}</b>
             es <b>{apto_no_apto}</b> para el cargo de <b>{labor}</b>.</p>
        """

    @staticmethod
    def _estilos() -> str:
        return """
        <style>
            @page {
                size: Letter;
                margin: 20mm; /* Set margin on each page */
                margin-top: 12mm;
                margin-bottom: 12mm;
            }
            body {
                font-size: 13px;
                font-family: 'DejaVu Serif', serif;
            }
            h1 {
                font-size: 18px;
                text-align: center;
            }
            p {
                text-align: justify;
            }
            li {
                text-align: justify;
                margin: 10px 0 10px 0;
            }
            
            .informe {
                margin: 20px 0 20px 0;
            }
            
            .firma-img {
                height: 150px;
                width: auto;
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
            
            .verification {
                font-size: 0;
                position: fixed;
                bottom: 0;
                width: 100%;
            }
            
            .column {
                font-size: 12px;
                display: inline-block;
                vertical-align: bottom;
                margin-top: 10px;
            }
            
            .image-column {
                width: 20%;
            }
            
            .content-column {
                text-align: right;
                width: 80%;
            }
        </style>
        """

    def _generar_parrafo1(self) -> str:
        persona = self.resultado.persona
        nombre_completo = persona.nombre_completo
        run = rut_chile.format_rut_with_dots(persona.rut)
        nacionalidad = Gentilicio.objects.get(pais=persona.nacionalidad).gentilicio

        return (
            "El profesional que firma este documento certifica que el Sr(a) "
            f"<b>{nombre_completo}</b> RUN <b>{run}</b> Nacionalidad <b>{nacionalidad}</b> ha realizado una evaluación "
            f"psicológica del control de los impulsos."
        )

    def _generar_parrafo2(self):
        texto_general = self.resultado.evaluacion["puntajes"]["GENERAL"]["texto"]
        return (
            f"Pruebas psicológicas indican {texto_general}. Sub-escalas de impulsividad no planificada, atencional "
            "y motora (BIS-11) arrojan el siguiente resultado:"
        )

    def _generar_parrafo3(self):
        return self.resultado.entrevista.observaciones
