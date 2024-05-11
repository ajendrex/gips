from django.contrib import admin
from django.utils.html import format_html

from tests.models import Persona, Test, PreguntaLikertNOAS, AccesoTest, AccesoTestPersona, Resultado, \
    RespuestaLikertNOAS, TramoCategoriaEvaluacion


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'email', 'telefono', 'nacionalidad', 'fecha_nacimiento')
    search_fields = ('rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'email', 'telefono')
    list_filter = ('nacionalidad', 'es_natural')
    date_hierarchy = 'fecha_nacimiento'
    ordering = ('-id',)


class PreguntaLikertNOASInline(admin.TabularInline):
    model = PreguntaLikertNOAS
    extra = 0

    class Media:
        css = {
            'all': ('css/admin_custom_inline.css',)
        }

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'texto':
            field.widget.attrs['style'] = 'height: 20px;'
        return field


class TramoCategoriaEvaluacionInline(admin.TabularInline):
    model = TramoCategoriaEvaluacion
    extra = 0


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
    readonly_fields = ('codigo', 'url')

    def url(self, obj):
        return format_html('<a href="{}" target="blank"><img src="{}" style="width: 20px" alt="Visit"/></a>',
                           f'/?codigo={obj.codigo}',
                           '/static/admin/img/icon-viewlink.svg')
    url.short_description = 'Acceder al test'


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
    fields = ('persona', 'test', 'fecha_creacion')
    readonly_fields = ('persona', 'test', 'fecha_creacion')
    inlines = [RespuestaLikertNOASInline]
