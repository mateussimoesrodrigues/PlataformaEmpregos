from django.shortcuts import render
from .models import VagaDeEmprego

def listar_dados_customizados(request):
    # Consulta a tabela 'vagas_de_emprego' e limita a 10 registros
    vagas = VagaDeEmprego.objects.all()[:10]  # Limita a 10 registros

    # Passa os dados para o template
    return render(request, 'vagas/lista_customizada.html', {'vagas': vagas})

def empresas(request):
    vagas = VagaDeEmprego.objects.all()  # Exemplo de consulta ao banco
    return render(request, 'vagas/empresas.html', {'vagas': vagas})

def dashboard(request):
    vagas = VagaDeEmprego.objects.all()  # Exemplo de consulta ao banco
    return render(request, 'vagas/dashboard.html', {'vagas': vagas})

def candidatos(request):
    vagas = VagaDeEmprego.objects.all()  # Exemplo de consulta ao banco
    return render(request, 'vagas/candidatos.html', {'vagas': vagas})