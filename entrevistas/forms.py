from django import forms

from entrevistas.models import Sicologo, Entrevista


class EntrevistaForm(forms.ModelForm):
    entrevistador_choice = forms.ModelChoiceField(
        queryset=Sicologo.objects.all(),
        required=True,
        label="Sicólogo",
        help_text="Seleccione un sicólogo para realizar la entrevista."
    )

    class Meta:
        model = Entrevista
        fields = ['entrevistador_choice', 'fecha_inicio', 'fecha_fin', 'observaciones']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.entrevistador:
            self.fields['entrevistador_choice'].initial = self.instance.entrevistador.pk

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.entrevistador = self.cleaned_data['entrevistador_choice']
        if commit:
            instance.save()
        return instance
