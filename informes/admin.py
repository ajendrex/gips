import json

from django.contrib import admin
from django.db import models
from django.forms import BaseInlineFormSet, ModelForm
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget
from reversion.admin import VersionAdmin

from informes.generadores.base import get_generador
from informes.models import Prueba, Pregunta, Alternativa, Resultado, Respuesta, Entrevista


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


class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = 'nombre',
    inlines = PreguntaInline,


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
    save_on_top = True


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 0
    readonly_fields = ('texto', 'posicion', 'id_plataforma', 'puntaje')
    can_delete = False

    def has_add_permission(self, request, obj):
        return False


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


class EntrevistaForm(ModelForm):
    def __init__(self, resultado=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if resultado and resultado.evaluacion:
            self.fields['observaciones'].initial = resultado.evaluacion.get('observaciones_initial', '')


class EntrevistaInline(admin.StackedInline):
    model = Entrevista
    can_delete = True
    form = EntrevistaForm

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)

        class WithParentInstanceFormset(formset_class):
            def _construct_form(self, i, **kwargs):
                return super()._construct_form(i, resultado=obj, **kwargs)

        return WithParentInstanceFormset


class ResultadoAdmin(admin.ModelAdmin):
    list_display = 'id', 'prueba', 'persona', 'fecha'
    search_fields = 'id', 'persona__rut', 'persona__nombres', 'persona__apellido_paterno'
    readonly_fields = 'persona', 'prueba', 'id_plataforma', 'fecha', 'metadata', 'clave_acceso', 'informe', "evaluacion_pretty"
    fieldsets = [
        (
            None,
            {
                "fields": [("prueba", "persona", "fecha", "informe"), ("evaluacion_pretty",)],
            },
        ),
        (
            "Detalles",
            {
                "classes": ["collapse"],
                "fields": ["id_plataforma", "metadata", "clave_acceso"],
            },
        ),
    ]
    list_filter = 'prueba',
    formfield_overrides = {
        #models.JSONField: {'widget': JSONEditorWidget(mode="view")},
    }
    inlines = EntrevistaInline, RespuestaInline,
    change_form_template = "admin/informes/resultado/change_form.html"
    save_on_top = True

    def evaluacion_pretty(self, instance) -> str:
        if instance.evaluacion:
            return format_html(
                "<pre>{}</pre>",
                json.JSONEncoder(indent=2, sort_keys=True).encode(instance.evaluacion),
            )
        return ""
    evaluacion_pretty.short_description = "Evaluación"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        resultado = self.get_object(request, object_id)

        extra_context["puede_evaluar"] = False
        extra_context["puede_generar_informe"] = False

        generador = get_generador(resultado, request)

        if generador:
            extra_context["puede_evaluar"] = generador.is_valid()

            if extra_context["puede_evaluar"]:
                extra_context["puede_generar_informe"] = generador.puede_generar_informe()

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/change/evaluar/', self.admin_site.admin_view(self.evaluar)),
            path('<path:object_id>/change/generar_informe/', self.admin_site.admin_view(self.generar_informe)),
        ]
        return my_urls + urls

    def evaluar(self, request, object_id):
        resultado = self.get_object(request, object_id)

        generador = get_generador(resultado, request)

        if generador:
            generador.evaluar()

        change_form_url = reverse('admin:informes_resultado_change', args=(object_id,))
        return HttpResponseRedirect(change_form_url)

    def generar_informe(self, request, object_id):
        resultado = self.get_object(request, object_id)

        generador = get_generador(resultado, request)

        if generador:
            generador.generar()

        change_form_url = reverse('admin:informes_resultado_change', args=(object_id,))
        return HttpResponseRedirect(change_form_url)


class RespuestaAdmin(admin.ModelAdmin):
    list_display = 'resultado', 'pregunta', 'valor'
    search_fields = 'resultado_id', 'pregunta__texto', 'alternativa__texto'
    list_filter = 'resultado__prueba',
    readonly_fields = 'resultado', 'pregunta', 'alternativa', 'valor', 'metadata'
    show_change_link = True
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }


class PruebaInline(admin.TabularInline):
    model = Prueba
    extra = 0
    readonly_fields = 'nombre', 'plataforma', 'fecha_creacion', 'fecha_actualizacion'
    fields = "nombre", "plataforma", "fecha_creacion", "fecha_actualizacion"
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj):
        return False


class AlgoritmoEvaluacionAdmin(admin.ModelAdmin):
    list_display = 'nombre', 'clase'
    inlines = PruebaInline,
