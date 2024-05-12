import json

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html

from entrevistas.models import Disponibilidad, Entrevistador, Bloqueo, Entrevista
from tests.generadores.base import get_generador


class DisponibilidadInline(admin.TabularInline):
    model = Disponibilidad
    extra = 0


class BloqueoInline(admin.TabularInline):
    model = Bloqueo
    extra = 0

    def get_ordering(self, request):
        return ['-fecha_inicio']


@admin.register(Entrevistador)
class EntrevistadorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "first_name", "last_name")
    inlines = [DisponibilidadInline, BloqueoInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if not request.user.is_superuser:
            queryset = queryset.filter(usuario=request.user)

        return queryset

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super().get_readonly_fields(request, obj)

        if not request.user.is_superuser:
            read_only_fields += ('usuario',)

        return read_only_fields


@admin.register(Entrevista)
class EntrevistaAdmin(admin.ModelAdmin):
    list_display = ("entrevistador", "entrevistado", "email_entrevistado", "fecha_inicio", "fecha_creacion")
    list_filter = ("entrevistador",)
    search_fields = (
        "entrevistador__usuario__first_name",
        "entrevistador__usuario__last_name",
        "acceso__persona__nombres",
        "acceso__persona__apellido_paterno",
        "acceso__persona__apellido_materno",
        "acceso__persona__email",
    )
    date_hierarchy = "fecha_inicio"
    change_form_template = "admin/entrevistas/entrevista/change_form.html"
    exclude = ("resultado",)
    readonly_fields = (
        "fecha_inicio",
        "fecha_fin",
        "acceso",
    )

    def email_entrevistado(self, obj):
        return obj.entrevistado.email

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if not request.user.is_superuser:
            queryset = queryset.filter(entrevistador__usuario=request.user)

        return queryset

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super().get_readonly_fields(request, obj)

        if not request.user.is_superuser:
            read_only_fields += ('entrevistador', 'acceso')

        return read_only_fields

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
        entrevista: Entrevista = self.get_object(request, object_id)

        extra_context["puede_evaluar"] = False
        extra_context["puede_generar_informe"] = False

        generador = get_generador(entrevista.resultado, request)

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
        entrevista: Entrevista = self.get_object(request, object_id)

        generador = get_generador(entrevista.resultado, request)

        if generador:
            generador.evaluar()

        change_form_url = reverse('admin:entrevistas_entrevista_change', args=(object_id,))
        return HttpResponseRedirect(change_form_url)

    def generar_informe(self, request, object_id):
        entrevista = self.get_object(request, object_id)

        generador = get_generador(entrevista.resultado, request)

        if generador:
            generador.generar()

        change_form_url = reverse('admin:entrevistas_entrevista_change', args=(object_id,))
        return HttpResponseRedirect(change_form_url)
