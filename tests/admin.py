import json
from datetime import date, datetime
from typing import List, Optional
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import make_aware

from tests.models import Persona, Test, PreguntaLikertNOAS, AccesoTest, AccesoTestPersona, Resultado, \
    RespuestaLikertNOAS, TramoCategoriaEvaluacion, Gentilicio, ResultadoEvaluacion
from utils.fechas import month_to_str, weekday_to_str, TZ_CHILE


@admin.register(Gentilicio)
class GentilicioAdmin(admin.ModelAdmin):
    pass


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'email', 'telefono', 'nacionalidad', 'fecha_nacimiento')
    search_fields = ('rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'email', 'telefono')
    list_filter = ('nacionalidad', 'es_natural')
    date_hierarchy = 'fecha_nacimiento'
    ordering = ('-id',)


class ShortTextoInlineMixin:
    style_height = "20px"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'texto':
            field.widget.attrs['style'] = f'height: {self.style_height};'
        return field


class PreguntaLikertNOASInline(ShortTextoInlineMixin, admin.TabularInline):
    model = PreguntaLikertNOAS
    extra = 0

    class Media:
        css = {
            'all': ('css/admin_custom_inline.css',)
        }


class TramoCategoriaEvaluacionInline(ShortTextoInlineMixin, admin.TabularInline):
    model = TramoCategoriaEvaluacion
    extra = 0
    style_height = "50px"


class ResultadoEvaluacionForm(forms.ModelForm):
    class Meta:
        model = ResultadoEvaluacion
        fields = "__all__"
        help_texts = {
            "texto": mark_safe(
                'Se intercalará en la frase &quot;Encontrándole &lt;texto&gt; para realizar las funciones de...&quot;')
        }


class ResultadoEvaluacionInline(ShortTextoInlineMixin, admin.TabularInline):
    model = ResultadoEvaluacion
    extra = 0
    form = ResultadoEvaluacionForm


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('nombre',)
    date_hierarchy = 'fecha_creacion'
    ordering = ('-id',)
    inlines = [TramoCategoriaEvaluacionInline, ResultadoEvaluacionInline, PreguntaLikertNOASInline]


class AccesoTestPersonaInline(admin.TabularInline):
    model = AccesoTestPersona
    extra = 0
    readonly_fields = ('inicio_respuestas_ts', 'fin_respuestas_ts', 'codigo', 'url', 'presentacion_whatsapp', 'confirmacion_whatsapp')

    def has_change_permission(self, request, obj=None):
        return False

    def url(self, obj):
        return format_html('<a href="{}" target="blank"><img src="{}" style="width: 20px" alt="Visit"/></a>',
                           f'/?codigo={obj.codigo}',
                           '/static/admin/img/icon-viewlink.svg')
    url.short_description = 'Acceder al test'

    def _link_whatsapp(self, obj: AccesoTestPersona, msg: str, title: str):
        telefono = obj.persona.telefono

        if telefono.startswith('+'):
            telefono = telefono[1:]

        return format_html(
            '<a href="https://wa.me/{}/?{}" target="blank">{}</a>',
            telefono,
            urlencode({'text': msg,}),
            title,
        )

    def presentacion_whatsapp(self, obj: AccesoTestPersona):
        entrevista = obj.entrevistas.last()

        if entrevista:
            if entrevista.resultado.informe:
                return 'Evaluación finalizada'
            if entrevista.fecha_fin < make_aware(datetime.now(), timezone=TZ_CHILE):
                return 'Entrevista fuera de plazo'
            return 'Entrevista programada'

        persona = obj.persona
        empresa = obj.acceso_test.mandante

        return self._link_whatsapp(
            obj,
            f'*¡Hola {persona}!* Esperamos que estés bien. Somos *El Sicológico*, especialistas '
                'en evaluaciones psicológicas en linea.\n\n'
                f'*{empresa}* nos solicitó evaluar tus impulsos para tu acreditación como '
                f'personal de seguridad.\n\n'
                'Te evaluaremos en 2 etapas:\n'
                '-	En la primera contestarás un test online.\n'
                '-	En la segunda tendrás una entrevista psicológica por video llamada de WhatsApp.\n\n'
                'Si tienes dudas o algún problema, avísanos por este chat.\n\n'
                'Cuando estés listo/a, toca el siguiente enlace para empezar el test:\n'
                f'{settings.BASE_URL}/?codigo={obj.codigo}\n\n'
                'Cuando lo termines, elige el día y la hora que te acomoden para realizar la entrevista.\n\n'
                'Te Saluda,\n'
                '*Equipo El sicológico*\n'
                'www.elsicologico.cl',
            'Abrir Presentación en Whatsapp',
        )
    presentacion_whatsapp.short_description = 'Presentación en Whatsapp'

    def confirmacion_whatsapp(self, obj: AccesoTestPersona):
        entrevista = obj.entrevistas.last()

        if not entrevista:
            return 'Sin entrevista programada'

        if entrevista.resultado.informe:
            return 'Evaluación finalizada'
        if entrevista.fecha_fin < make_aware(datetime.now(), timezone=TZ_CHILE):
            return 'Entrevista fuera de plazo'

        dia = weekday_to_str[entrevista.fecha.weekday()]
        mes = month_to_str[entrevista.fecha.month]
        fecha = f'{entrevista.fecha.day} de {mes}'
        hora = entrevista.fecha.strftime('%H:%M')

        return self._link_whatsapp(
            obj,
            f'¡Hola {obj.persona}!\n\n'
            'Tu entrevista psicológica está confirmada. '
            f'Nos vemos el día {dia} {fecha} a las {hora} hrs a través de video llamada.\n\n'
            'Antes de la hora programada, un miembro de nuestro equipo de psicólogos se pondrá en contacto '
            'contigo a través de WhatsApp para afinar los detalles de la entrevista y video llamada. '
            'Si por alguna razón necesitas re agendar o tienes algún problema, no dudes en escribirnos. '
            'Estamos aquí para ayudarte en lo que necesites.\n\n'
            '¡Nos vemos pronto y que tengas un excelente día!\n\n'
            'Te saluda,\n'
            'El equipo de El Sicológico',
            'Abrir Confirmación en Whatsapp',
        )

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            formset.form.base_fields['cargo'].initial = obj.cargo_predefinido
        return formset


@admin.register(AccesoTest)
class AccesoTestAdmin(admin.ModelAdmin):
    list_display = ('test', 'fecha_creacion', 'fecha_vencimiento', 'mandante', 'valor_unitario')
    search_fields = ('test__nombre', 'mandante__nombres', 'mandante__apellido_paterno', 'mandante__apellido_materno')
    date_hierarchy = 'fecha_creacion'
    list_filter = ('test', 'mandante__es_natural')
    inlines = [AccesoTestPersonaInline]


class RespuestaLikertNOASInline(admin.TabularInline):
    model = RespuestaLikertNOAS
    extra = 0
    can_delete = False
    fields = ('pregunta', 'categoria', 'alternativa', 'puntaje')
    readonly_fields = ('pregunta', 'categoria', 'alternativa', 'puntaje')

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj):
        return False


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ('persona', 'test', 'fecha_creacion')
    search_fields = (
        'acceso__persona__nombres',
        'acceso__persona__apellido_paterno',
        'acceso__persona__apellido_materno',
        'acceso__persona__rut',
    )
    list_filter = ('acceso__acceso_test__test', 'acceso__persona__nacionalidad', 'acceso__persona__es_natural')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = (
        'persona',
        'test',
        'fecha_creacion',
        'evaluacion_pretty',
        'informe',
        'clave_archivo',
        'inicio_test',
        'fin_test',
    )
    inlines = [RespuestaLikertNOASInline]
    fieldsets = (
        (None, {
            'fields': (('persona', 'fecha_creacion'),)
        }),
        ('Evaluación', {
            'fields': ('test', 'inicio_test', 'fin_test', 'informe', 'clave_archivo', 'evaluacion_pretty'),
        }),
    )

    def inicio_test(self, instance: Resultado) -> Optional[datetime]:
        return instance.acceso.inicio_respuestas_ts
    inicio_test.short_description = "Inicio del test"

    def fin_test(self, instance: Resultado) -> Optional[datetime]:
        return instance.acceso.fin_respuestas_ts
    fin_test.short_description = "Fin del test"

    def evaluacion_pretty(self, instance: Resultado) -> str:
        if instance and instance.evaluacion:
            return format_html(
                "<pre>{}</pre>",
                json.JSONEncoder(indent=2, sort_keys=True).encode(instance.evaluacion),
            )
        return ""
    evaluacion_pretty.short_description = "Evaluación"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if not request.user.is_superuser:
            queryset = queryset.filter(entrevista__entrevistador__usuario=request.user)

        return queryset
