from django.shortcuts import render, redirect
from .models import VagaDeEmprego
from django.db import connection
import json
from django.http import JsonResponse


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

def pesquisa_vagas(request):
    query = request.GET.get('pesquisa_vagas', '')  # Obtém o valor do input (ou '' se estiver vazio)
    
    if query:
        vagas = VagaDeEmprego.objects.filter(nome_empresa__icontains=query)  # Filtra pelo nome da empresa
    else:
        vagas = VagaDeEmprego.objects.all()  # Se não houver pesquisa, exibe todas as vagas

    return render(request, 'vagas/candidatos.html', {'vagas': vagas, 'query': query})

def novas_vagas(request):
    vagas = VagaDeEmprego.objects.all()  # Exemplo de consulta ao banco
    return render(request, 'vagas/novas_vagas.html', {'vagas': vagas})

from django.shortcuts import render, redirect
from django.db import connection

from django.db import connection
from django.shortcuts import render, redirect

def criar_vaga(request):
    if request.method == 'POST':
        # Pegando os dados do formulário
        nome_empresa = request.POST.get('nome_empresa')
        descricao = request.POST.get('descricao')
        localizacao = request.POST.get('localizacao')
        area = request.POST.get('area')
        info_adicionais = request.POST.get('info_adicionais')
        beneficios = request.POST.get('beneficios')

        # Chamando a procedure para adicionar a vaga
        with connection.cursor() as cursor:
            # Chamando a procedure sem passar id_requisito como parâmetro
            cursor.callproc('adicionar_vaga_spi', [nome_empresa, descricao, localizacao, area, info_adicionais, beneficios])

            # Recuperando o ID gerado
            cursor.execute("SELECT @id_requisito")  
            id_requisito = cursor.fetchone()[0]  # Captura o valor retornado

        # Commit para garantir a inserção no banco
        connection.commit()

        # Exibir no terminal para depuração
        print(f"Vaga criada com id_requisito: {id_requisito}")

        # Redireciona para a página de sucesso com o ID da vaga
        return redirect('sucesso', id_requisito=id_requisito)

    # Se não for POST, renderiza o formulário para criar a vaga
    return render(request, 'vagas/area_empresa.html')

def sucesso_view(request, id_requisito):
    # Buscar os requisitos já cadastrados para a vaga
    cursor = connection.cursor()
    cursor.execute("SELECT REQUISITOS FROM plataforma_empregos.requisitos_da_vaga WHERE id_requisito = %s", [id_requisito])
    requisitos = [{'requisito': row[0]} for row in cursor.fetchall()]

    return render(request, 'vagas/sucesso.html', {'id_requisito': id_requisito, 'requisitos': requisitos})

def adicionar_requisito(request):
    if request.method == "POST":
        data = json.loads(request.body)
        id_requisito = data.get("id_requisito")
        requisito = data.get("requisito")

        if id_requisito and requisito:
            cursor = connection.cursor()
            cursor.callproc('adicionar_requisito_spi', [id_requisito, requisito])
            connection.commit()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Dados inválidos"})

    return JsonResponse({"success": False, "error": "Método não permitido"})

def sucesso(request):
    return render(request, 'vagas/sucesso.html')  # Renderiza o template de sucesso

def area_empresa(request):
    # Exemplo de valores passados, esses dados podem vir de um formulário ou do banco
    context = {
        'nome_empresa': 'Nome da Empresa',
        'descricao': 'Descrição da vaga',
        'localizacao': 'Localização da vaga',
        'area': 'Área da vaga',
        'info_adicionais': 'Informações adicionais',
        'beneficios': 'Benefícios oferecidos',
    }
    return render(request, 'vagas/area_empresa.html', context)
