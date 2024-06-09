import json

from django import forms
from django.contrib import admin, messages
from django.contrib.humanize.templatetags.humanize import naturalday
from django.http import HttpResponseRedirect, HttpRequest
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from entrevistas.forms import EntrevistaForm
from entrevistas.models import Disponibilidad, Sicologo, Bloqueo, Entrevista
from tests.generadores.base import get_generador
from utils.admin import link_whatsapp


class DisponibilidadInline(admin.TabularInline):
    model = Disponibilidad
    extra = 0


class BloqueoInline(admin.TabularInline):
    model = Bloqueo
    extra = 0

    def get_ordering(self, request):
        return ['-fecha_inicio']


@admin.register(Sicologo)
class SicologoAdmin(admin.ModelAdmin):
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
    list_display = (
        "entrevistado",
        "entrevistador",
        "email_entrevistado",
        "fecha_inicio",
        "fecha_creacion",
        "presentacion_whatsapp",
    )
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
    form = EntrevistaForm
    readonly_fields = (
        "tiempo_test",
        "link_informe",
        "resultado",
        "previsualizacion",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("entrevistador_choice", "fecha_inicio", "fecha_fin"),
                    ("resultado", "tiempo_test"),
                    "observaciones",
                    "resultado_entrevista",
                    "previsualizacion",
                    "link_informe",
                ),
            },
        ),
    )

    def presentacion_whatsapp(self, obj: Entrevista) -> str:
        ahora = timezone.now()

        if obj.fecha_fin.date() < ahora.date():
            return "Entrevista ya realizada"

        persona = obj.entrevistado
        rol = "psicólogo" if obj.entrevistador.genero == "M" else "psicóloga"
        local_fecha_inicio = timezone.localtime(obj.fecha_inicio)
        local_hora_inicio = local_fecha_inicio.strftime("%H:%M")

        cuando = "en breve" if (local_fecha_inicio - ahora).seconds < 60 * 60 else "pronto"

        return link_whatsapp(
            persona,
            f"Hola {persona.nombres}!\n\n"
            f"Soy {obj.entrevistador.usuario.first_name}, {rol} del equipo de El Sicológico. "
            f"Te escribo para recordarte que {naturalday(local_fecha_inicio.date())} a las "
            f"{local_hora_inicio} hrs tenemos agendada tu entrevista psicológica"
            " por videollamada de WhatsApp para completar tu evaluación de impulsos.\n\n"
            "Seré yo quien realice la videollamada. Durante la entrevista, por favor, ten tu cámara encendida "
            "y el micrófono activado, ya que es un requisito para evaluarte.\n\n"
            "Te sugiero que busques un lugar tranquilo y sin distracciones para que podamos aprovechar al máximo "
            "nuestro tiempo juntos.\n\n"
            "La entrevista durará entre 15 y 20 minutos. Quiero que te sientas lo más cómodo/a posible, así que tómate "
            "un momento para respirar profundamente y relajarte antes de que comencemos.\n\n"
            "Si tienes alguna pregunta o necesitas aclarar algo, no dudes en escribirme.\n\n"
            f"¡Nos vemos {cuando} y te deseo mucha suerte!\n\n"
            "Un abrazo,\n"
            f"{obj.entrevistador}\n"
            f"{obj.entrevistador.titulo}\n"
            "El Sicológico",
            "Abrir presentación en Whatsapp",
        )
    presentacion_whatsapp.short_description = "Mensaje Previo"

    def get_formset_kwargs(self, request: HttpRequest, obj: Entrevista, inline, prefix):
        form = super().get_formset_kwargs(request, obj, inline, prefix)

        if obj:
            form.fields["resultado_entrevista"].queryset = obj.acceso.test.resultados_posibles.all()

        return form

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
            read_only_fields += ('entrevistador', 'acceso', 'fecha_inicio', 'fecha_fin')

        return read_only_fields

    def evaluacion_pretty(self, instance: Entrevista) -> str:
        if instance and instance.resultado and instance.resultado.evaluacion:
            return format_html(
                "<pre>{}</pre>",
                json.JSONEncoder(indent=2, sort_keys=True).encode(instance.resultado.evaluacion),
            )
        return ""
    evaluacion_pretty.short_description = "Evaluación"

    def previsualizacion(self, instance: Entrevista) -> str:
        generador = get_generador(instance.resultado)

        if generador:
            try:
                return mark_safe(generador.generar_html_evaluacion())
            except Exception as e:
                return f"Error al previsualizar evaluación: {e}"

        return "No se puede generar previsualización"
    previsualizacion.short_description = "Previsualización de evaluación en el informe"

    def link_informe(self, instance: Entrevista) -> str:
        if instance and instance.resultado and instance.resultado.informe:
            return format_html(
                '<a href="{}" target="_blank">Informe</a>',
                instance.resultado.informe.url
            )
        return ""
    link_informe.short_description = "Informe"

    def tiempo_test(self, instance: Entrevista) -> str:
        return instance.acceso.tiempo_test
    tiempo_test.short_description = "Tiempo de Test"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        if request.method == "GET":
            self._evaluar(request, object_id)

            entrevista: Entrevista = self.get_object(request, object_id)
            extra_context["puede_generar_informe"] = False
            generador = get_generador(entrevista.resultado if entrevista else None, request)

            if generador:
                extra_context["puede_generar_informe"] = generador.is_valid() and generador.puede_generar_informe()

        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/change/evaluar/', self.admin_site.admin_view(self.evaluar)),
            path('<path:object_id>/change/generar_informe/', self.admin_site.admin_view(self.generar_informe)),
        ]
        return my_urls + urls

    def evaluar(self, request, object_id):
        self._evaluar(request, object_id)

        change_form_url = reverse('admin:entrevistas_entrevista_change', args=(object_id,))
        return HttpResponseRedirect(change_form_url)

    def _evaluar(self, request, object_id):
        entrevista: Entrevista = self.get_object(request, object_id)

        generador = get_generador(entrevista.resultado, request)

        if generador:
            generador.evaluar()

    def generar_informe(self, request, object_id):
        entrevista = self.get_object(request, object_id)

        generador = get_generador(entrevista.resultado, request)

        if generador:
            generador.generar()

        change_form_url = reverse('admin:entrevistas_entrevista_change', args=(object_id,))
        return HttpResponseRedirect(change_form_url)

    def save_model(self, request: HttpRequest, obj: Entrevista, form: forms.ModelForm, change: bool):
        if change:
            if "resultado_entrevista" in form.changed_data or "observaciones" in form.changed_data:
                if obj.resultado.informe:
                    obj.resultado.informe = None
                    obj.resultado.save()
                    self.message_user(request, "Informe eliminado, se debe regenerar!", messages.WARNING)

        super().save_model(request, obj, form, change)
