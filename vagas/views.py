from django.shortcuts import render, redirect
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
from django.shortcuts import render, get_object_or_404, redirect
from .models import Chat, Mensagem
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import OuterRef, Subquery
from django.db.models import Count


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
                        request.session['EMAIL_CANDIDATO'] = email

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


def empresas(request):
    return render(request, 'vagas/empresas.html')


def candidatos(request):
    query = request.GET.get('candidatos', '') 
    
    if query:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT NOME_EMPRESA, DESCRICAO, LOCALIZACAO, AREA, INFO_ADICIONAIS, BENEFICIOS, CARGO, DATA_ENCERRAMENTO, id_vaga FROM plataforma_empregos.vagas_de_emprego WHERE CURDATE() <= DATA_ENCERRAMENTO AND NOME_EMPRESA = %s;""", [query])
            colunas = [col[0] for col in cursor.description]        
            vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    else:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT NOME_EMPRESA, DESCRICAO, LOCALIZACAO, AREA, INFO_ADICIONAIS, BENEFICIOS, CARGO, DATA_ENCERRAMENTO, id_vaga FROM plataforma_empregos.vagas_de_emprego WHERE CURDATE() <= DATA_ENCERRAMENTO;""")
            colunas = [col[0] for col in cursor.description]        
            vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    return render(request, 'vagas/candidatos.html', {'vagas': vagas})

def candidatar_vaga(request, id_vaga):
    # Buscar os requisitos já cadastrados para a vaga
    cursor = connection.cursor()
    cursor.execute("SELECT ve.id_requisito, ve.CARGO, ve.NOME_EMPRESA, date(ve.DATA_CRIACAO) as DATA_CRIACAO, ve.DATA_ENCERRAMENTO, ve.LOCALIZACAO, ve.AREA, ve.DESCRICAO, ve.INFO_ADICIONAIS, ve.BENEFICIOS FROM plataforma_empregos.vagas_de_emprego ve WHERE id_vaga = %s limit 1", [id_vaga])
    colunas = [col[0] for col in cursor.description]
    vaga = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    cursor = connection.cursor()
    cursor.execute("SELECT REQUISITOS FROM plataforma_empregos.requisitos_da_vaga WHERE id_requisito = (SELECT id_requisito FROM plataforma_empregos.vagas_de_emprego  WHERE id_vaga = %s)", [id_vaga])
    colunas_req = [col[0] for col in cursor.description]
    vaga_req = [dict(zip(colunas_req, row)) for row in cursor.fetchall()]

    return render(request, 'vagas/candidatar_vaga.html', {'vaga': vaga, 'vaga_req': vaga_req})

@login_required
def minhas_vagas(request):
    nome_empresa = request.session.get('nome_empresa', 'Empresa Desconhecida')

    # Consulta SQL direta para filtrar as vagas pela empresa
    with connection.cursor() as cursor:
        cursor.execute("""SELECT NOME_EMPRESA, DESCRICAO, LOCALIZACAO, AREA, INFO_ADICIONAIS, BENEFICIOS, CARGO, DATA_ENCERRAMENTO, id_requisito FROM plataforma_empregos.vagas_de_emprego WHERE NOME_EMPRESA = %s""", [nome_empresa])

        colunas = [col[0] for col in cursor.description]  # nomes das colunas
        vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]  # transformar em dicionários

    return render(request, 'vagas/minhas_vagas.html', {'vagas': vagas})

@login_required(login_url='login')  # Redireciona para login se não estiver autenticado
def novas_vagas(request):
    if request.method == 'POST':
        nome_empresa = request.session.get('nome_empresa', 'Empresa Desconhecida')

        descricao = request.POST.get('descricao')
        localizacao = request.POST.get('localizacao')
        area = request.POST.get('area')
        info_adicionais = request.POST.get('info_adicionais')
        beneficios = request.POST.get('beneficios')
        cargo = request.POST.get('cargo')
        data_encerramento = request.POST.get('data_encerramento')

        with connection.cursor() as cursor:
            cursor.callproc('adicionar_vaga_spi', [nome_empresa, descricao, localizacao, area, info_adicionais, beneficios, cargo, data_encerramento])
            cursor.execute("SELECT @id_requisito")
            id_requisito = cursor.fetchone()[0]

        connection.commit()
        print(f"Vaga criada com id_requisito: {id_requisito}")
        return redirect('sucesso', id_requisito=id_requisito)

    return render(request, 'vagas/novas_vagas.html')

@login_required(login_url='login')
def curriculo(request):
    candidato = request.session.get('EMAIL_CANDIDATO', 'Candidato Desconhecido')

    if request.method == 'POST':

        habilidade = request.POST.get('habilidade')
        if habilidade:
            cursor = connection.cursor()
            cursor.callproc('adicionar_habilidade_spi', [candidato, int(habilidade)])
            cursor.close()

        return redirect('curriculo')
        

    cursor = connection.cursor()
    cursor.execute("SELECT id, nome FROM plataforma_empregos.habilidade")
    habilidades = [{'habilidade': row[0], 'nome': row[1]} for row in cursor.fetchall()]  

    cursor = connection.cursor()
    cursor.callproc('habilidade_sps', [candidato])   
    habilidades_candidato = [{'nome': row[0]} for row in cursor.fetchall()]
    cursor.close()

    return render(request, 'vagas/curriculo.html', {'habilidades': habilidades, 'habilidades_candidato': habilidades_candidato})

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


@login_required
def chat_fullpage(request):
    chats = obter_chats_do_usuario(request.user)
    erro = None
    chat_id_para_abrir = request.GET.get('chat')

    if request.method == 'POST':
        email_destino = request.POST.get('email_destino')
        destinatario = User.objects.filter(email=email_destino).first()

        if not destinatario:
            return render(request, 'vagas/chat_fullpage.html', {
                'chats': chats,
                'erro': 'Usuário não encontrado.'
            })

        # Verifica se já existe um chat entre exatamente esses dois usuários
        chat_existente = Chat.objects.annotate(num_participantes=Count('participantes')) \
            .filter(participantes=request.user) \
            .filter(participantes=destinatario) \
            .filter(num_participantes=2) \
            .first()

        if chat_existente:
            chat_id_para_abrir = chat_existente.id
        else:
            novo_chat = Chat.objects.create()
            novo_chat.participantes.add(request.user, destinatario)
            chat_id_para_abrir = novo_chat.id

    return render(request, 'vagas/chat_fullpage.html', {
        'chats': chats,
        'chat_id_para_abrir': chat_id_para_abrir,
        'erro': erro
    })


@login_required
def atualizar_mensagens(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if request.user not in chat.participantes.all():
        return HttpResponse(status=403)
    mensagens = chat.mensagem_set.order_by('timestamp')
    return render(request, 'vagas/mensagens_parciais.html', {'mensagens': mensagens, 'user': request.user})

@login_required
def enviar_mensagem(request, chat_id):
    if request.method == 'POST':
        texto = request.POST.get('mensagem')
        chat = get_object_or_404(Chat, id=chat_id)
        if request.user in chat.participantes.all():
            Mensagem.objects.create(chat=chat, remetente=request.user, texto=texto)
            return HttpResponse(status=200)
    return HttpResponse(status=400)

# Função que você já tinha para pegar os chats do usuário
def obter_chats_do_usuario(user):
    return Chat.objects.filter(participantes=user).annotate(
        outro_email=Subquery(
            Chat.participantes.through.objects
            .filter(chat_id=OuterRef('pk'))
            .exclude(user_id=user.id)
            .values('user__email')[:1]
        )
    )