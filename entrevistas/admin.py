from django.contrib import admin

from entrevistas.models import Disponibilidad, Entrevistador, Bloqueo, Entrevista


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
