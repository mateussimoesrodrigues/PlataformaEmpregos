from django.shortcuts import render
from .models import VagaDeEmprego

def listar_dados_customizados(request):
    # Consulta a tabela 'vagas_de_emprego' e limita a 10 registros
    vagas = VagaDeEmprego.objects.all()[:10]  # Limita a 10 registros

    # Passa os dados para o template
    return render(request, 'vagas/lista_customizada.html', {'vagas': vagas})
