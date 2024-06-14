import json
from datetime import date, datetime
from typing import List, Optional
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import make_aware

from entrevistas.models import Entrevista
from tests.models import Persona, Test, PreguntaLikertNOAS, AccesoTest, AccesoTestPersona, Resultado, \
    RespuestaLikertNOAS, TramoCategoriaEvaluacion, Gentilicio, ResultadoEvaluacion
from utils.admin import link_whatsapp
from utils.fechas import month_to_str, weekday_to_str, TZ_CHILE


@admin.register(Gentilicio)
class GentilicioAdmin(admin.ModelAdmin):
    pass


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'email', 'telefono', 'nacionalidad', 'fecha_nacimiento')
    search_fields = ('rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'email', 'telefono')
    list_filter = 'es_natural',
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

    def has_change_permission(self, request, obj=None):
        return False

    def url(self, obj: AccesoTestPersona):
        return format_html('<a href="{}" target="blank"><img src="{}" style="width: 20px" alt="Visit"/></a>',
                           obj.url,
                           '/static/admin/img/icon-viewlink.svg')
    url.short_description = 'Acceder al test'

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

        return link_whatsapp(
            persona,
            f'*¡Hola {persona}!* Esperamos que estés bien. Somos *El Sicológico*, especialistas '
            'en evaluaciones psicológicas en linea.\n\n' +
            (
                'Nos solicitaste'
                if empresa.rut == persona.rut
                else f'*{empresa}* nos solicitó'
            ) +
            ' evaluar tus impulsos para tu acreditación como personal de seguridad.\n\n'
            'Te evaluaremos en 2 etapas:\n'
            '-	En la primera contestarás un test online.\n'
            '-	En la segunda tendrás una entrevista psicológica por video llamada de WhatsApp.\n\n'
            'Si tienes dudas o algún problema, avísanos por este chat.\n\n'
            'Cuando estés listo/a, toca el siguiente enlace para empezar el test:\n'
            f'{obj.url}\n\n'
            'Cuando lo termines, elige el día y la hora que te acomoden para realizar la entrevista.\n\n'
            'Te Saluda,\n'
            '*Equipo El sicológico*\n'
            'www.elsicologico.cl',
        'Abrir Presentación en Whatsapp',
        )
    presentacion_whatsapp.short_description = 'Mensaje Inicial'

    def confirmacion_whatsapp(self, obj: AccesoTestPersona):
        entrevista: Optional[Entrevista] = obj.entrevistas.last()

        if not entrevista:
            return 'Sin entrevista programada'

        if entrevista.resultado.informe:
            return 'Evaluación finalizada'
        if entrevista.fecha_fin < make_aware(datetime.now(), timezone=TZ_CHILE):
            return 'Entrevista fuera de plazo'

        local_fecha_inicio = timezone.localtime(entrevista.fecha)
        dia = weekday_to_str[local_fecha_inicio.weekday()]
        mes = month_to_str[local_fecha_inicio.month]
        fecha = f'{local_fecha_inicio.day} de {mes}'
        hora = local_fecha_inicio.strftime('%H:%M')

        return link_whatsapp(
            obj.persona,
            f'¡Hola {obj.persona.nombres}!\n\n'
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
    confirmacion_whatsapp.short_description = "Confirmación de Entrevista"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            formset.form.base_fields['cargo'].initial = obj.cargo_predefinido
        return formset

    def link_entrevista(self, obj: AccesoTestPersona) -> str:
        entrevista = obj.entrevistas.last()
        if entrevista:
            return format_html(
                '<a href="{}"><img src="/static/admin/img/icon-changelink.svg" alt="Ver"></a>',
                reverse('admin:entrevistas_entrevista_change', args=[entrevista.pk]),
            )
        return ""

    def has_add_permission(self, request, obj):
        return False


class AccesoTestPersonaSinEntrevista(AccesoTestPersonaInline):
    verbose_name_plural = "Accesos sin entrevista"
    readonly_fields = ('inicio_respuestas_ts', 'fin_respuestas_ts', 'codigo', 'url', 'presentacion_whatsapp')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(entrevistas__isnull=True)

    def has_add_permission(self, request, obj):
        return True


class AccesoTestPersonaConEntrevista(AccesoTestPersonaInline):
    verbose_name_plural = "Accesos con entrevista"
    readonly_fields = (
        'inicio_respuestas_ts', 'fin_respuestas_ts', 'codigo', 'link_entrevista', 'confirmacion_whatsapp',
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(entrevistas__resultado__informe="").distinct()


class AccesoTestPersonaConInforme(AccesoTestPersonaInline):
    verbose_name_plural = "Accesos con informe"
    readonly_fields = ('inicio_respuestas_ts', 'fin_respuestas_ts', 'codigo', 'link_entrevista', 'cierre_whatsapp')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(entrevistas__isnull=False).exclude(entrevistas__resultado__informe="").distinct()

    def cierre_whatsapp(self, obj: AccesoTestPersona) -> str:
        entrevista = obj.entrevistas.last()
        resultado = obj.resultado
        fv = obj.resultado.fecha_vencimiento
        fecha_vencimiento = f'{fv.day} de {month_to_str[fv.month]} de {fv.year}' if fv else "indefinida"

        if entrevista:
            empresa = obj.acceso_test.mandante
            persona = obj.persona

            return link_whatsapp(
                persona,
                f'{obj.persona.nombres},\n\n'
                f'{"Te hemos" if empresa.rut == persona.rut else "Hemos"} enviado tu informe de control de impulsos' +
                (
                    f'a {obj.acceso_test.mandante}'
                    if persona.rut != empresa.rut
                    else ''
                ) +
                f'. El resultado de tu evaluación es: {resultado.resultado} '
                f'para realizar labores de {obj.get_cargo_display()}.\n\n'
                'El informe tiene una vigencia de 90 días desde la fecha de emisión, es decir, será válido hasta el '
                f'{fecha_vencimiento}.\n\n'
                'Si tienes alguna pregunta o necesitas más información, no dudes en contactarnos.\n\n'
                'Saludos,\n'
                'El equipo de El Sicológico',
                'Abrir Cierre en Whatsapp',
            )
        return ""
    cierre_whatsapp.short_description = "Cierre de Entrevista"


@admin.register(AccesoTest)
class AccesoTestAdmin(admin.ModelAdmin):
    list_display = ('mandante', 'test',  'fecha_creacion', 'fecha_vencimiento', 'valor_unitario', 'cant_evaluaciones')
    search_fields = ('test__nombre', 'mandante__nombres', 'mandante__apellido_paterno', 'mandante__apellido_materno')
    date_hierarchy = 'fecha_creacion'
    list_filter = ('test', 'mandante__es_natural')
    inlines = [AccesoTestPersonaSinEntrevista, AccesoTestPersonaConEntrevista, AccesoTestPersonaConInforme]

    @staticmethod
    def cant_evaluaciones(obj: AccesoTest):
        return obj.ruts.count()


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
    list_display = ('persona', 'test', 'fecha_emision', 'resultado_test')
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
        'fecha_emision',
        'resultado_test',
        'evaluacion_pretty',
        'informe',
        'clave_archivo',
        'inicio_test',
        'fin_test',
    )
    inlines = [RespuestaLikertNOASInline]
    fieldsets = (
        (None, {
            'fields': (('persona', 'fecha_emision', 'resultado_test'),)
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
