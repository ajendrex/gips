from django.contrib import admin

from tests.models import Persona, Test, PreguntaLikertNOAS, AccesoTest, AccesoTestPersona


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


class AccesoTestPersonaInline(admin.TabularInline):
    model = AccesoTestPersona
    extra = 0
    readonly_fields = ('codigo',)


@admin.register(AccesoTest)
class AccesoTestAdmin(admin.ModelAdmin):
    list_display = ('test', 'fecha_creacion', 'fecha_vencimiento', 'mandante', 'valor_unitario')
    search_fields = ('test__nombre', 'mandante__nombres', 'mandante__apellido_paterno', 'mandante__apellido_materno')
    date_hierarchy = 'fecha_creacion'
    list_filter = ('test', 'mandante__es_natural')
    inlines = [AccesoTestPersonaInline]
