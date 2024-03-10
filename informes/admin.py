from django.contrib import admin
from django.db import models
from django.forms import BaseInlineFormSet
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget
from reversion.admin import VersionAdmin

from informes.models import Prueba, Pregunta, Alternativa, Categoria, Persona, Resultado, Respuesta


class PreguntaAdminMixin:
    def texto_formato_html(self, instance):
        """Renderiza el campo 'texto' como HTML seguro en el admin."""
        return format_html(instance.texto)

    texto_formato_html.short_description = "Texto"  # Nombre que aparecerá en el Admin


class PreguntaInline(admin.TabularInline, PreguntaAdminMixin):
    model = Pregunta
    extra = 0
    readonly_fields = ('texto_formato_html', 'pagina', 'posicion', 'id_plataforma', 'tipo', 'plataforma', 'prueba')
    exclude = 'texto',
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


class PreguntaInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.form.base_fields['categoria'].queryset = self.instance.categorias.all()


class PreguntaInlineForPrueba(PreguntaInline):
    readonly_fields = ('texto_formato_html', 'pagina', 'posicion', 'id_plataforma', 'tipo', 'plataforma')
    formset = PreguntaInlineFormSet


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = 'nombre',
    inlines = PreguntaInline,


@admin.register(Prueba)
class PruebaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plataforma', 'fecha_creacion', 'fecha_actualizacion')
    readonly_fields = ('nombre', 'plataforma', 'fecha_creacion', 'fecha_actualizacion')
    exclude = ('metadata',)
    search_fields = 'nombre',
    list_filter = 'plataforma',
    inlines = PreguntaInlineForPrueba,
    filter_horizontal = 'categorias',
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 0
    readonly_fields = ('texto', 'posicion', 'id_plataforma', 'puntaje')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin, PreguntaAdminMixin):
    list_display = ('texto_formato_html', 'categoria', 'prueba', 'pagina', 'posicion', 'id_plataforma')
    list_editable = 'categoria',
    readonly_fields = ('prueba', 'pagina', 'posicion', 'id_plataforma', 'texto_formato_html', 'tipo')
    exclude = 'texto',
    list_filter = 'prueba', 'categoria'
    inlines = AlternativaInline,

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            categoria_field = form.base_fields['categoria']
            categoria_field.queryset = obj.prueba.categorias.all()
        return form


class ResultadoInline(admin.TabularInline):
    model = Resultado
    extra = 0
    fields = 'prueba', 'fecha', 'informe', 'email_envio'
    readonly_fields = 'prueba', 'fecha', 'informe'
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


@admin.register(Persona)
class PersonaAdmin(VersionAdmin):
    list_display = 'rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'email', 'nacionalidad', 'fecha_nacimiento'
    search_fields = 'rut', 'nombres', 'apellido_paterno', 'apellido_materno', 'email'
    list_filter = 'nacionalidad',
    inlines = ResultadoInline,


class RespuestaInline(admin.TabularInline):
    model = Respuesta
    extra = 0
    readonly_fields = 'pregunta', 'alternativa', 'valor'
    exclude = 'metadata',
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = 'id', 'prueba', 'persona', 'fecha'
    search_fields = 'id', 'persona__rut', 'persona__nombres', 'persona__apellido_paterno'
    readonly_fields = 'persona', 'prueba', 'id_plataforma', 'fecha', 'metadata', 'clave_acceso', 'informe'
    list_filter = 'prueba',
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
    inlines = RespuestaInline,


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = 'resultado', 'pregunta', 'valor'
    search_fields = 'resultado_id', 'pregunta__texto', 'alternativa__texto'
    list_filter = 'resultado__prueba',
    readonly_fields = 'resultado', 'pregunta', 'alternativa', 'valor', 'metadata'
    show_change_link = True
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
