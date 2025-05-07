from django.shortcuts import render, redirect
from .models import VagaDeEmprego
from django.db import connection
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password  # Importando o check_password
from django.contrib.auth.hashers import make_password  # Importe o make_password

class CustomBackend(ModelBackend):
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT PAGINA, NOME_EMPRESA, SENHA FROM controle_login WHERE EMAIL_CANDIDATO = %s
                """, [email])
                resultado = cursor.fetchone()

                if resultado:
                    pagina, nome_empresa, senha_db = resultado  # Obtemos a senha da base de dados

                    # Verifica se a senha fornecida bate com a senha armazenada no banco de dados
                    if check_password(senha, senha_db):  # Usando check_password para verificar a senha criptografada
                        # Criação de um usuário fictício para manter a sessão
                        user, created = User.objects.get_or_create(username=email, email=email)
                        login(request, user)  # Realiza o login do usuário no Django

                        # Armazena o nome da empresa na sessão
                        request.session['nome_empresa'] = nome_empresa

                        # Redireciona para a página correta com base na 'pagina'
                        if pagina == 'CANDIDATO':
                            return redirect('candidatos')
                        elif pagina == 'EMPRESA':
                            return redirect('empresas')
                        else:
                            messages.error(request, 'Página desconhecida')
                    else:
                        messages.error(request, 'Senha incorreta')
                else:
                    messages.error(request, 'Email não encontrado')

        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')

    return render(request, 'vagas/login.html')


def registro_empresa(request):
    return render(request, 'vagas/registro_empresa.html')

from django.db import connection
from django.contrib import messages
from django.shortcuts import render, redirect

def registro_candidato(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        data_nascimento = request.POST.get('data_nascimento')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        genero = request.POST.get('genero')
        senha = request.POST.get('senha')

        print("Recebi POST:")
        print(f"Nome: {nome}, Sobrenome: {sobrenome}, Data Nasc: {data_nascimento}, Email: {email}, Telefone: {telefone}, Gênero: {genero}, Senha: {senha}")

        try:
            # Criptografar a senha antes de enviá-la para o banco de dados
            senha_criptografada = make_password(senha)

            # Verifique o print aqui, se a senha criptografada está sendo gerada corretamente
            print(f"Senha criptografada: {senha_criptografada}")

            # Certifique-se de passar todos os dados corretamente para a procedure
            with connection.cursor() as cursor:
                cursor.callproc('plataforma_empregos.candidatos_spi', [
                    nome,
                    sobrenome,
                    data_nascimento,
                    email,  # Passando o email corretamente
                    telefone,
                    genero,
                    senha_criptografada  # Aqui passamos a senha criptografada
                ])

            connection.commit()  # <-- ADICIONAR ISTO AQUI!
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            print(f"Erro: {e}")  # Para entender o erro exato

    return render(request, 'vagas/registro_candidato.html')


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

@login_required(login_url='login')  # Redireciona para login se não estiver autenticado
def novas_vagas(request):
    if request.method == 'POST':
        nome_empresa = request.session.get('nome_empresa', 'Empresa Desconhecida')

        descricao = request.POST.get('descricao')
        localizacao = request.POST.get('localizacao')
        area = request.POST.get('area')
        info_adicionais = request.POST.get('info_adicionais')
        beneficios = request.POST.get('beneficios')

        with connection.cursor() as cursor:
            cursor.callproc('adicionar_vaga_spi', [nome_empresa, descricao, localizacao, area, info_adicionais, beneficios])
            cursor.execute("SELECT @id_requisito")
            id_requisito = cursor.fetchone()[0]

        connection.commit()
        print(f"Vaga criada com id_requisito: {id_requisito}")
        return redirect('sucesso', id_requisito=id_requisito)

    return render(request, 'vagas/novas_vagas.html')



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