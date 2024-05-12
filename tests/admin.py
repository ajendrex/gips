import json
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from tests.models import Persona, Test, PreguntaLikertNOAS, AccesoTest, AccesoTestPersona, Resultado, \
    RespuestaLikertNOAS, TramoCategoriaEvaluacion, Gentilicio


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


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('nombre',)
    date_hierarchy = 'fecha_creacion'
    ordering = ('-id',)
    inlines = [TramoCategoriaEvaluacionInline, PreguntaLikertNOASInline]


class AccesoTestPersonaInline(admin.TabularInline):
    model = AccesoTestPersona
    extra = 0
    readonly_fields = ('codigo', 'url', 'link_whatsapp')

    def url(self, obj):
        return format_html('<a href="{}" target="blank"><img src="{}" style="width: 20px" alt="Visit"/></a>',
                           f'/?codigo={obj.codigo}',
                           '/static/admin/img/icon-viewlink.svg')
    url.short_description = 'Acceder al test'

    def link_whatsapp(self, obj: AccesoTestPersona):
        persona = obj.persona
        empresa = obj.acceso_test.mandante
        telefono = persona.telefono

        if telefono.startswith('+'):
            telefono = telefono[1:]

        return format_html(
            '<a href="https://wa.me/{}/?{}" target="blank">Abrir mensaje</a>',
            telefono,
            urlencode({
                'text': f'*¡Hola {persona}!* Esperamos que estés bien. Somos *El Sicológico*, especialistas '
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
            }),
        )
    link_whatsapp.short_description = 'Presentación en Whatsapp'


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
    readonly_fields = ('persona', 'test', 'fecha_creacion', 'evaluacion_pretty', 'clave_archivo')
    inlines = [RespuestaLikertNOASInline]
    fieldsets = (
        (None, {
            'fields': (('persona', 'fecha_creacion'),)
        }),
        ('Evaluación', {
            'fields': (('test', 'informe', 'clave_archivo'), 'evaluacion_pretty',),
        }),
    )

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
