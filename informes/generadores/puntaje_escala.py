from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ValidationError
from rut_chile import rut_chile
from weasyprint import HTML

from informes.generadores.base import Generador


class GeneradorPuntajeEscala(Generador):
    def _validate(self):
        rut = self.resultado.persona.rut

        if not rut_chile.is_valid_rut(rut):
            raise ValidationError(f"El rut {rut} no es válido")

        prueba = self.resultado.prueba
        pregunta_sin_categoria = prueba.preguntas.filter(
            categoria__isnull=True,
        ).exclude(
            id_plataforma__in=prueba.parametros.get('campos_persona').values(),
        ).first()

        if pregunta_sin_categoria:
            raise ValidationError(f"Hay preguntas sin categoría, por ejemplo: {pregunta_sin_categoria.texto}")

        parametros = prueba.parametros

        if not parametros:
            raise ValidationError("La prueba no tiene parámetros")

        categorias = parametros.get('categorias')

        if not categorias:
            raise ValidationError("Los parámetros de la prueba no tienen categorías")

        if not isinstance(categorias, list):
            raise ValidationError("Las categorías no son una lista")

        categorias_preguntas = self.resultado.prueba.categorias.all()

        if len(categorias) != len(categorias_preguntas) + 1:
            raise ValidationError("Las categorías no coinciden con las preguntas de la prueba")

        nombres_categorias_parametros = [categoria.get('nombre') for categoria in categorias]

        for categoria in categorias_preguntas:
            if categoria.nombre not in nombres_categorias_parametros:
                raise ValidationError(f"La categoría {categoria.nombre} no está en los parámetros de la prueba")

        if "General" not in nombres_categorias_parametros:
            raise ValidationError("La categoría General no está en los parámetros de la prueba")

        for parametros_categoria in categorias:
            nombre = parametros_categoria["nombre"]

            tramos = parametros_categoria.get('tramos')

            if not tramos:
                raise ValidationError(f"categoría {nombre}: Faltan los tramos de la categoría")

            if not isinstance(tramos, list):
                raise ValidationError(f"categoría {nombre}: Los tramos no son una lista")

            for tramo in tramos:
                nombre_tramo = tramo.get('nombre')

                if not nombre_tramo:
                    raise ValidationError(f"categoría {nombre}: Falta el nombre del tramo")

                puntaje_minimo = tramo.get('min')

                if not isinstance(puntaje_minimo, (int, float)):
                    raise ValidationError(f"categoría {nombre} ({nombre_tramo}): El puntaje mínimo no es un número")

                puntaje_maximo = tramo.get('max')

                if not isinstance(puntaje_maximo, (int, float)):
                    raise ValidationError(f"categoría {nombre} ({nombre_tramo}): El puntaje máximo no es un número")

                if not tramo.get('texto'):
                    raise ValidationError(f"categoría {nombre} ({nombre_tramo}): Falta el texto del tramo")

        respuesta_sin_puntaje = self.resultado.respuestas.filter(
            pregunta__categoria__isnull=False,
            alternativa__isnull=True,
        ).first()

        if respuesta_sin_puntaje:
            raise ValidationError(
                f"Hay respuestas con categoría pero sin puntaje, por ejemplo: {respuesta_sin_puntaje.pregunta.texto}"
            )

    def _validar_puede_generar_informe(self):
        self._validate()

        entrevista = getattr(self.resultado, 'entrevista', None)

        if not entrevista:
            raise ValidationError("Falta la entrevista")

        if not entrevista.observaciones:
            raise ValidationError("La entrevista no tiene observaciones")

        persona = self.resultado.persona

        if not persona:
            raise ValidationError("Falta la persona")

        if not persona.nombre_completo:
            raise ValidationError("Falta el nombre completo de la persona")

        if not persona.rut:
            raise ValidationError("Falta el rut de la persona")

        if not persona.nacionalidad:
            raise ValidationError("Falta la nacionalidad de la persona")

    def _evaluar(self) -> dict:
        evaluacion = {}

        puntajes = {
            "General": {"puntaje": 0},
            **{
                categoria.nombre: {"puntaje": 0}
                for categoria in self.resultado.prueba.categorias.all()
            }
        }

        for respuesta in self.resultado.respuestas.exclude(pregunta__categoria__isnull=True):
            categoria = respuesta.pregunta.categoria.nombre
            puntaje = respuesta.alternativa.puntaje
            puntajes[categoria]["puntaje"] += puntaje
            puntajes["General"]["puntaje"] += puntaje

        for parametros in self.resultado.prueba.parametros["categorias"]:
            nombre_categoria = parametros["nombre"]
            puntaje = puntajes[nombre_categoria]["puntaje"]

            for tramo in parametros["tramos"]:
                nombre_tramo = tramo["nombre"]
                puntaje_minimo = tramo["min"]
                puntaje_maximo = tramo["max"]
                texto = tramo["texto"]

                if puntaje_minimo <= puntaje <= puntaje_maximo:
                    puntajes[nombre_categoria]["nivel"] = nombre_tramo
                    puntajes[nombre_categoria]["texto"] = texto
                    break

        if puntajes["General"]["nivel"] == "bajo":
            evaluacion["observaciones_initial"] = (
                "En entrevista presenta una conducta adecuada, ajustada a la situación, motivación por logro de "
                "objetivos, manejo de la ansiedad, preocupación por el autocuidado, tolerancia a la frustración "
                "frente a situaciones desconocidas o que requieren concentración y procesamiento cognitivo "
                "para tomar de decisiones."
            )

        evaluacion["puntajes"] = puntajes

        return evaluacion

    def _generar_informe(self) -> bytes:
        p1 = self._generar_parrafo1()
        p2 = self._generar_parrafo2()
        p3 = self._generar_parrafo3()
        texto_no_planificada = self.resultado.evaluacion["puntajes"]["No Planificada"]["texto"]
        texto_atencional = self.resultado.evaluacion["puntajes"]["Cognitiva"]["texto"]
        texto_motora = self.resultado.evaluacion["puntajes"]["Motora"]["texto"]

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
        nacionalidad = persona.nacionalidad

        tramo_general = self.resultado.evaluacion["puntajes"]["General"]["nivel"]

        if tramo_general == "bajo":
            apto_no_apto = "apto"
        elif tramo_general == "moderado":
            apto_no_apto = "apto con reservas"
        else:
            apto_no_apto = "no apto"

        labor = "&lt;TODO: crear pregunta en surveymonkey&gt;"

        return (
            "El profesional que firma este documento certifica que el Sr(a) "
            f"<b>{nombre_completo}</b> RUN <b>{run}</b> Nacionalidad <b>{nacionalidad}</b> ha realizado una evaluación "
            f"psicológica del control de los impulsos, encontrándole {apto_no_apto} para realizar labores de "
            f"{labor}."
        )

    def _generar_parrafo2(self):
        return self.resultado.entrevista.observaciones

    def _generar_parrafo3(self):
        texto_general = self.resultado.evaluacion["puntajes"]["General"]["texto"]
        return (
            f"Pruebas psicológicas indican un {texto_general}. Sub-escalas de impulsividad no planificada, atencional "
            "y motora (BIS-11) arrojan el siguiente resultado:"
        )
