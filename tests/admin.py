from django.contrib import admin

from tests.models import Persona, Test, PreguntaLikertNOAS


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


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('nombre',)
    date_hierarchy = 'fecha_creacion'
    ordering = ('-id',)
    inlines = [PreguntaLikertNOASInline]
