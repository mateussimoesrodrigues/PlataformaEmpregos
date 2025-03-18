from django import forms
from .models import VagaDeEmprego

class VagaForm(forms.ModelForm):
    class Meta:
        model = VagaDeEmprego
        fields = ['nome_empresa', 'descricao', 'localizacao', 'area', 'info_adicionais', 'beneficios', 'cargo']
