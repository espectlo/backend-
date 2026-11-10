from django import forms

from .models import Herramienta, Insumo


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['nombre', 'cantidad', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'maxlength': 120}),
            'cantidad': forms.NumberInput(attrs={'min': 0}),
            'stock_minimo': forms.NumberInput(attrs={'min': 0}),
        }


class HerramientaForm(forms.ModelForm):
    class Meta:
        model = Herramienta
        fields = ['nombre', 'estado', 'tratamiento']
        widgets = {'nombre': forms.TextInput(attrs={'maxlength': 120})}