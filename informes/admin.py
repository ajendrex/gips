from django.contrib import admin
from django.db import models
from django.forms import BaseInlineFormSet
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget

from informes.models import Prueba, Pregunta, Alternativa, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = 'nombre',


class PreguntaAdminMixin:
    def texto_formato_html(self, instance):
        """Renderiza el campo 'texto' como HTML seguro en el admin."""
        return format_html(instance.texto)

    texto_formato_html.short_description = "Texto"  # Nombre que aparecerá en el Admin


class PreguntaInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.form.base_fields['categoria'].queryset = self.instance.categorias.all()


class PreguntaInline(admin.TabularInline, PreguntaAdminMixin):
    model = Pregunta
    extra = 0
    readonly_fields = ('texto_formato_html', 'pagina', 'posicion', 'id_externo')
    exclude = 'texto',
    show_change_link = True
    formset = PreguntaInlineFormSet


@admin.register(Prueba)
class PruebaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plataforma', 'fecha_creacion', 'fecha_actualizacion')
    readonly_fields = ('nombre', 'plataforma', 'fecha_creacion', 'fecha_actualizacion')
    exclude = ('metadata',)
    search_fields = 'nombre',
    list_filter = 'plataforma',
    inlines = PreguntaInline,
    filter_horizontal = 'categorias',
    formfield_overrides = {
        # fields.JSONField: {'widget': JSONEditorWidget}, # if django < 3.1
        models.JSONField: {'widget': JSONEditorWidget},
    }


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 0
    readonly_fields = ('texto', 'posicion', 'id_externo')


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin, PreguntaAdminMixin):
    list_display = ('prueba', 'pagina', 'posicion', 'id_externo', 'texto_formato_html')
    readonly_fields = ('prueba', 'pagina', 'posicion', 'id_externo', 'texto_formato_html')
    exclude = 'texto',
    list_filter = 'prueba',
    inlines = AlternativaInline,

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            categoria_field = form.base_fields['categoria']
            categoria_field.queryset = obj.prueba.categorias.all()
        return form
