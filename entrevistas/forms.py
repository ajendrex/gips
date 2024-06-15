from django import forms

from entrevistas.models import Sicologo, Entrevista


class EntrevistaForm(forms.ModelForm):
    entrevistador_choice = forms.ModelChoiceField(
        queryset=Sicologo.objects.all(),
        required=True,
        label="Sicólogo",
        help_text="Seleccione un sicólogo para realizar la entrevista."
    )
    cerrar_evaluacion = forms.BooleanField(
        required=False,
        label="Cerrar evaluación",
        help_text="Marque esta casilla si desea cerrar la evaluación después de realizar la entrevista."
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

    def clean(self):
        cleaned_data = super().clean()
        resultado = self.instance.resultado

        if cleaned_data.get('cerrar_evaluacion') and not resultado.informe:
            msg = "No se puede cerrar la evaluación sin haber generado el informe."
            self.add_error("cerrar_evaluacion", msg)
            raise forms.ValidationError(msg)

        return cleaned_data
