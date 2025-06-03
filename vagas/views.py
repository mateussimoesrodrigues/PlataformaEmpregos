# Importações necessárias para as funcionalidades do Django, banco de dados, manipulação de JSON,
# autenticação, sessões, mensagens, modelos de chat e manipulação de datas.
from django.shortcuts import render, redirect
from django.db import connection
import json
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404
from .models import Chat, Mensagem  # Importa os modelos de Chat e Mensagem do seu aplicativo
from django.db.models import OuterRef, Subquery, Count
from datetime import datetime


# ---
## Backend de Autenticação Personalizado
# ---
class CustomBackend(ModelBackend):
    """
    Este backend de autenticação personalizado permite que o Django encontre usuários
    com base no ID. É um componente padrão quando se precisa de um controle mais granular
    sobre como os usuários são carregados durante o processo de autenticação.
    """
    def get_user(self, user_id):
        """
        Retorna uma instância de usuário dado seu ID.
        Usado internamente pelo sistema de autenticação do Django.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

# ---
## Funções de Autenticação e Registro
# ---

def login_view(request):
    """
    Controla o processo de login de usuários (candidatos e empresas).
    Processa requisições POST com email e senha, valida as credenciais
    diretamente no banco de dados e redireciona o usuário para a página
    apropriada (candidato ou empresa) após o login bem-sucedido.
    Também armazena informações essenciais na sessão do usuário.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            # Abre uma conexão com o banco de dados para executar uma consulta SQL direta.
            with connection.cursor() as cursor:
                # Busca a página (tipo de usuário), nome da empresa e senha criptografada
                # na tabela 'controle_login' com base no email fornecido.
                cursor.execute("""
                    SELECT PAGINA, NOME_EMPRESA, SENHA FROM controle_login WHERE EMAIL_CANDIDATO = %s
                """, [email])
                resultado = cursor.fetchone()

                if resultado:
                    pagina, nome_empresa, senha_db = resultado

                    # Verifica se a senha fornecida pelo usuário corresponde à senha criptografada
                    # armazenada no banco de dados, usando a função `check_password` do Django.
                    if check_password(senha, senha_db):
                        # Se a senha estiver correta, cria ou obtém um objeto User do Django.
                        # Isso é feito para integrar com o sistema de sessões e autenticação do Django.
                        user, created = User.objects.get_or_create(username=email, email=email)
                        login(request, user)  # Realiza o login do usuário no Django.

                        # Armazena o nome da empresa e o email do candidato na sessão
                        # para uso posterior em outras partes do aplicativo.
                        request.session['nome_empresa'] = nome_empresa
                        request.session['EMAIL_CANDIDATO'] = email

                        # Redireciona o usuário para a página específica de acordo com seu perfil.
                        if pagina == 'CANDIDATO':
                            return redirect('candidatos')
                        elif pagina == 'EMPRESA':
                            return redirect('minhas_vagas')
                        else:
                            messages.error(request, 'Página desconhecida.')
                    else:
                        messages.error(request, 'Senha incorreta.')
                else:
                    messages.error(request, 'Email não encontrado.')

        except Exception as e:
            # Captura e exibe qualquer erro que ocorra durante a operação do banco de dados.
            messages.error(request, f'Ocorreu um erro: {e}')

    # Se a requisição não for POST (primeiro acesso à página de login)
    # ou se o login falhar, renderiza o template de login.
    return render(request, 'vagas/login.html')


def registro_empresa(request):
    """
    Gerencia o processo de registro de novas empresas.
    Recebe os dados do formulário de registro via POST, criptografa a senha
    e chama uma stored procedure no banco de dados ('empresas_spi') para inserir
    as informações da nova empresa.
    """
    if request.method == 'POST':
        # Coleta os dados do formulário de registro de empresa.
        nome_empresa = request.POST.get('nome_empresa')
        cnpj = request.POST.get('cnpj')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        endereco = request.POST.get('endereco')
        descricao = request.POST.get('descricao')
        senha = request.POST.get('senha')

        # Para fins de depuração, imprime os dados recebidos.
        print("Recebi POST (EMPRESA):")
        print(f"Nome: {nome_empresa}, CNPJ: {cnpj}, Email: {email}, Telefone: {telefone}, Endereço: {endereco}")

        try:
            # Criptografa a senha fornecida pelo usuário usando `make_password` do Django
            # antes de armazená-la no banco de dados, garantindo a segurança.
            senha_criptografada = make_password(senha)
            print(f"Senha criptografada: {senha_criptografada}")

            with connection.cursor() as cursor:
                # Chama a stored procedure 'empresas_spi' no banco de dados para inserir
                # os dados da nova empresa, incluindo a senha criptografada.
                cursor.callproc('empresas_spi', [
                    nome_empresa,
                    cnpj,
                    email,
                    telefone,
                    endereco,
                    descricao,
                    senha_criptografada
                ])

            connection.commit()  # Confirma a transação no banco de dados.
            messages.success(request, 'Cadastro da empresa realizado com sucesso!')
            return redirect('login')  # Redireciona para a página de login após o registro.

        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            print(f"Erro ao cadastrar empresa: {e}")

    # Se a requisição não for POST, renderiza o formulário de registro de empresa.
    return render(request, 'vagas/registro_empresa.html')


def registro_candidato(request):
    """
    Gerencia o processo de registro de novos candidatos.
    Recebe os dados do formulário, criptografa a senha e chama uma stored procedure
    no banco de dados ('plataforma_empregos.candidatos_spi') para registrar o candidato.
    """
    if request.method == 'POST':
        # Coleta os dados do formulário de registro de candidato.
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        data_nascimento = request.POST.get('data_nascimento')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        genero = request.POST.get('genero')
        senha = request.POST.get('senha')

        # Para fins de depuração, imprime os dados recebidos.
        print("Recebi POST:")
        print(f"Nome: {nome}, Sobrenome: {sobrenome}, Data Nasc: {data_nascimento}, Email: {email}, Telefone: {telefone}, Gênero: {genero}, Senha: {senha}")

        try:
            # Criptografa a senha antes de enviá-la para o banco de dados.
            senha_criptografada = make_password(senha)
            print(f"Senha criptografada: {senha_criptografada}")

            with connection.cursor() as cursor:
                # Chama a stored procedure 'plataforma_empregos.candidatos_spi' para inserir
                # os dados do candidato no banco de dados.
                cursor.callproc('plataforma_empregos.candidatos_spi', [
                    nome,
                    sobrenome,
                    data_nascimento,
                    email,
                    telefone,
                    genero,
                    senha_criptografada
                ])

            connection.commit()  # Confirma a transação.
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            print(f"Erro: {e}")

    # Renderiza o formulário de registro de candidato.
    return render(request, 'vagas/registro_candidato.html')

# ---
## Views de Páginas Diversas
# ---

def empresas(request):
    """
    Renderiza a página principal para usuários do tipo 'empresa'.
    Esta é uma view simples que apenas exibe um template.
    """
    return render(request, 'vagas/empresas.html')


def candidatos(request):
    """
    Exibe as vagas de emprego para os candidatos.
    Permite buscar vagas por nome de empresa e também mostra vagas recomendadas
    com base nas habilidades do candidato logado.
    """
    query = request.GET.get('candidatos', '')
    email = request.session.get('EMAIL_CANDIDATO', 'Candidato Desconhecido')

    # Busca vagas de emprego. Se houver uma query, filtra por nome da empresa;
    # caso contrário, busca todas as vagas ativas.
    if query:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT NOME_EMPRESA, DESCRICAO, LOCALIZACAO, AREA, INFO_ADICIONAIS, BENEFICIOS, CARGO, DATA_ENCERRAMENTO, id_vaga
                FROM plataforma_empregos.vagas_de_emprego
                WHERE CURDATE() <= DATA_ENCERRAMENTO AND NOME_EMPRESA = %s;
            """, [query])
            colunas = [col[0] for col in cursor.description]
            vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT NOME_EMPRESA, DESCRICAO, LOCALIZACAO, AREA, INFO_ADICIONAIS, BENEFICIOS, CARGO, DATA_ENCERRAMENTO, id_vaga
                FROM plataforma_empregos.vagas_de_emprego
                WHERE CURDATE() <= DATA_ENCERRAMENTO;
            """)
            colunas = [col[0] for col in cursor.description]
            vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    # Busca vagas recomendadas para o candidato logado, baseando-se nas habilidades do candidato.
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT v.NOME_EMPRESA, v.DESCRICAO, v.LOCALIZACAO, v.AREA, v.INFO_ADICIONAIS, v.BENEFICIOS, v.CARGO, v.DATA_ENCERRAMENTO, v.id_vaga
            FROM candidato c
            JOIN candidato_habilidade ch ON c.id_candidato = ch.id_candidato
            JOIN habilidade h ON ch.id_habilidade = h.id
            JOIN requisitos_da_vaga r ON LOWER(CONCAT(' ', r.REQUISITOS, ' ')) LIKE CONCAT('%% ', LOWER(h.nome), ' %%')
            JOIN vagas_de_emprego v ON r.id_requisito = v.id_requisito
            WHERE c.EMAIL_CANDIDATO = %s AND CURDATE() <= v.DATA_ENCERRAMENTO
        """, [email])
        colunas_recomendadas = [col[0] for col in cursor.description]
        vagas_recomendadas = [dict(zip(colunas_recomendadas, row)) for row in cursor.fetchall()]

    # Renderiza a página de candidatos, passando as vagas encontradas e as recomendadas.
    return render(request, 'vagas/candidatos.html', {'vagas': vagas, 'vagas_recomendadas': vagas_recomendadas})


def candidatar_vaga(request, id_vaga):
    """
    Exibe os detalhes de uma vaga específica para que um candidato possa se candidatar.
    Busca informações detalhadas da vaga e seus requisitos associados.
    """
    # Busca os detalhes da vaga de emprego pelo ID da vaga.
    cursor = connection.cursor()
    cursor.execute("""
        SELECT ve.id_vaga, ve.id_requisito, ve.CARGO, ve.NOME_EMPRESA, date(ve.DATA_CRIACAO) as DATA_CRIACAO,
               ve.DATA_ENCERRAMENTO, ve.LOCALIZACAO, ve.AREA, ve.DESCRICAO, ve.INFO_ADICIONAIS, ve.BENEFICIOS
        FROM plataforma_empregos.vagas_de_emprego ve
        WHERE id_vaga = %s
        LIMIT 1
    """, [id_vaga])
    colunas = [col[0] for col in cursor.description]
    vaga = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    # Busca os requisitos associados à vaga.
    cursor = connection.cursor()
    cursor.execute("""
        SELECT REQUISITOS
        FROM plataforma_empregos.requisitos_da_vaga
        WHERE id_requisito = (SELECT id_requisito FROM plataforma_empregos.vagas_de_emprego WHERE id_vaga = %s)
    """, [id_vaga])
    colunas_req = [col[0] for col in cursor.description]
    vaga_req = [dict(zip(colunas_req, row)) for row in cursor.fetchall()]

    # Renderiza a página de detalhes da vaga, passando os dados da vaga e seus requisitos.
    return render(request, 'vagas/candidatar_vaga.html', {'vaga': vaga, 'vaga_req': vaga_req})


def detalhes_candidatos(request, id_candidato):
    """
    Esta função parece ter um erro lógico, pois tenta buscar detalhes de vaga
    usando `id_vaga` (que não está disponível no parâmetro da função) e depois
    tenta buscar habilidades com `id_candidato` mas a subquery ainda usa `id_vaga`.
    Para fins de demonstração, os comentários assumem o que a função *poderia* fazer
    se corrigida para mostrar detalhes de um candidato.
    """
    # **NOTA**: A lógica atual desta função parece estar incorreta, pois está usando `id_vaga`
    # (que não é passado para a função) para buscar detalhes de vaga, em vez de detalhes do candidato
    # passado como `id_candidato`.

    # Se a intenção fosse mostrar detalhes do candidato e suas habilidades:
    # cursor = connection.cursor()
    # cursor.execute("SELECT NOME_COMPLETO, EMAIL_CANDIDATO, TELEFONE, GENERO, DATA_NASCIMENTO FROM candidato WHERE id_candidato = %s", [id_candidato])
    # colunas_candidato = [col[0] for col in cursor.description]
    # candidato_detalhes = [dict(zip(colunas_candidato, row)) for row in cursor.fetchall()]

    # cursor.execute("SELECT h.nome FROM habilidade h JOIN candidato_habilidade ch ON h.id = ch.id_habilidade WHERE ch.id_candidato = %s", [id_candidato])
    # colunas_habilidades = [col[0] for col in cursor.description]
    # habilidades_candidato = [dict(zip(colunas_habilidades, row)) for row in cursor.fetchall()]

    # return render(request, 'vagas/detalhes_candidatos.html', {'candidato': candidato_detalhes, 'habilidades': habilidades_candidato})

    # Mantendo a lógica original (com o erro aparente) para fins de comentário direto ao código:
    cursor = connection.cursor()
    # A linha abaixo está usando `id_vaga` que não está disponível nesta função.
    # Provavelmente deveria ser `id_candidato` e buscar dados do candidato.
    cursor.execute("SELECT ve.id_vaga, ve.id_requisito, ve.CARGO, ve.NOME_EMPRESA, date(ve.DATA_CRIACAO) as DATA_CRIACAO, ve.DATA_ENCERRAMENTO, ve.LOCALIZACAO, ve.AREA, ve.DESCRICAO, ve.INFO_ADICIONAIS, ve.BENEFICIOS FROM plataforma_empregos.vagas_de_emprego ve WHERE id_vaga = %s limit 1", [id_vaga])
    colunas = [col[0] for col in cursor.description]
    vaga = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    cursor = connection.cursor()
    # A linha abaixo também parece incorreta, tentando usar `id_candidato` em uma subquery para `id_vaga`.
    # Provavelmente deveria buscar habilidades do candidato.
    cursor.execute("SELECT HABILIDADES FROM plataforma_empregos.requisitos_da_vaga WHERE id_requisito = (SELECT id_requisito FROM plataforma_empregos.vagas_de_emprego  WHERE id_candidato = %s)", [id_candidato])
    colunas_req = [col[0] for col in cursor.description]
    vaga_req = [dict(zip(colunas_req, row)) for row in cursor.fetchall()]

    return render(request, 'vagas/detalhes_candidatos.html', {'vaga': vaga, 'vaga_req': vaga_req})


@login_required
def candidatura(request, id_vaga):
    """
    Permite que um candidato se candidate a uma vaga específica.
    Requer que o usuário esteja logado.
    Chama uma stored procedure no banco de dados ('candidatura_spi') para registrar a candidatura.
    Após a candidatura, redireciona o candidato para a página de "minhas candidaturas".
    """
    # Obtém o email do candidato logado da sessão.
    email = request.session.get('EMAIL_CANDIDATO', 'Candidato Desconhecido')

    # Abre uma conexão com o banco de dados.
    cursor = connection.cursor()
    # Chama a stored procedure 'candidatura_spi' passando o ID da vaga e o email do candidato.
    cursor.callproc('candidatura_spi', [id_vaga, email])
    cursor.close() # Garante que o cursor seja fechado.

    return redirect('minhas_candidaturas') # Redireciona para a página de candidaturas do usuário.


@login_required
def minhas_candidaturas(request):
    """
    Exibe a lista de vagas às quais o candidato logado se candidatou.
    Requer que o usuário esteja logado.
    Chama uma stored procedure ('candidatura_sps') para buscar as candidaturas do usuário.
    """
    # Obtém o email do candidato logado da sessão.
    email = request.session.get('EMAIL_CANDIDATO', 'Candidato Desconhecido')

    # Abre uma conexão com o banco de dados.
    cursor = connection.cursor()
    # Chama a stored procedure 'candidatura_sps' para buscar as candidaturas do candidato.
    cursor.callproc('candidatura_sps', [email])
    rows = cursor.fetchall() # Obtém todas as linhas resultantes da stored procedure.

    # Mapeia as linhas retornadas para uma lista de dicionários, facilitando o acesso no template.
    vagas = [{'nome_empresa': row[0],'descricao': row[1],'localizacao': row[2],'area': row[3],'info_adicionais': row[4],'beneficios': row[5],'cargo': row[6],'data_encerramento': row[7],'id_vaga': row[8], 'status': row[9],
    } for row in rows]
    cursor.close()

    # Renderiza a página 'minhas_candidaturas.html' passando as vagas candidatas.
    return render(request, 'vagas/minhas_candidaturas.html', {'vagas': vagas})


@login_required
def ver_candidatos(request, id_vaga):
    """
    Permite que uma empresa visualize os candidatos que se candidataram a uma vaga específica.
    Requer que o usuário esteja logado.
    Executa uma consulta SQL para obter detalhes dos candidatos e suas habilidades.
    """
    with connection.cursor() as cursor:
        # Consulta SQL que busca informações dos candidatos (nome, email, gênero, telefone, idade)
        # e agrupa suas habilidades, para uma dada vaga.
        cursor.execute("""
            SELECT
                c.NOME_COMPLETO,
                c.EMAIL_CANDIDATO,
                c.GENERO,
                c.TELEFONE,
                CONCAT(TIMESTAMPDIFF(YEAR, c.DATA_NASCIMENTO, CURDATE()), ' anos') AS IDADE,
                GROUP_CONCAT(h.nome SEPARATOR ', ') AS HABILIDADES
            FROM candidatura a
            LEFT JOIN candidato c ON a.id_candidato = c.id_candidato
            LEFT JOIN candidato_habilidade ch ON c.id_candidato = ch.id_candidato
            LEFT JOIN habilidade h ON ch.id_habilidade = h.id
            WHERE a.id_vaga = %s
            GROUP BY
                c.NOME_COMPLETO,
                c.EMAIL_CANDIDATO,
                c.GENERO,
                c.TELEFONE,
                c.DATA_NASCIMENTO
        """, [id_vaga])

        colunas = [col[0] for col in cursor.description]
        vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    # Renderiza a página 'ver_candidatos.html' com a lista de candidatos para a vaga.
    return render(request, 'vagas/ver_candidatos.html', {'vagas': vagas})


@login_required
def minhas_vagas(request):
    """
    Exibe as vagas publicadas pela empresa logada.
    Requer que o usuário esteja logado.
    Consulta diretamente o banco de dados para filtrar vagas pelo nome da empresa.
    """
    # Obtém o nome da empresa logada da sessão.
    nome_empresa = request.session.get('nome_empresa', 'Empresa Desconhecida')

    # Executa uma consulta SQL direta para buscar as vagas publicadas por esta empresa.
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT NOME_EMPRESA, DESCRICAO, LOCALIZACAO, AREA, INFO_ADICIONAIS, BENEFICIOS, CARGO, DATA_ENCERRAMENTO, id_requisito, id_vaga
            FROM plataforma_empregos.vagas_de_emprego
            WHERE NOME_EMPRESA = %s
        """, [nome_empresa])

        colunas = [col[0] for col in cursor.description]
        vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    # Renderiza a página 'minhas_vagas.html' com as vagas da empresa.
    return render(request, 'vagas/minhas_vagas.html', {'vagas': vagas})


@login_required(login_url='login')
def novas_vagas(request):
    """
    Permite que uma empresa cadastre novas vagas de emprego.
    Requer que o usuário esteja logado.
    Processa o formulário de criação de vagas e chama uma stored procedure
    ('adicionar_vaga_spi') para inserir a nova vaga no banco de dados.
    """
    if request.method == 'POST':
        # Obtém o nome da empresa da sessão.
        nome_empresa = request.session.get('nome_empresa', 'Empresa Desconhecida')

        # Coleta os dados do formulário de nova vaga.
        descricao = request.POST.get('descricao')
        localizacao = request.POST.get('localizacao')
        area = request.POST.get('area')
        info_adicionais = request.POST.get('info_adicionais')
        beneficios = request.POST.get('beneficios')
        cargo = request.POST.get('cargo')
        data_encerramento = request.POST.get('data_encerramento')

        with connection.cursor() as cursor:
            # Chama a stored procedure 'adicionar_vaga_spi' para inserir a nova vaga.
            cursor.callproc('adicionar_vaga_spi', [nome_empresa, descricao, localizacao, area, info_adicionais, beneficios, cargo, data_encerramento])
            # Após a execução da stored procedure, obtém o ID do requisito gerado.
            cursor.execute("SELECT @id_requisito")
            id_requisito = cursor.fetchone()[0]

        connection.commit() # Confirma a transação.
        print(f"Vaga criada com id_requisito: {id_requisito}")
        # Redireciona para uma página de sucesso, passando o ID do requisito.
        return redirect('sucesso', id_requisito=id_requisito)

    # Se a requisição não for POST, renderiza o formulário para criar novas vagas.
    return render(request, 'vagas/novas_vagas.html')


@login_required(login_url='login')
def curriculo(request):
    """
    Gerencia a página de currículo do candidato, permitindo adicionar habilidades e experiências.
    Requer que o usuário esteja logado.
    Busca e exibe as habilidades e experiências cadastradas pelo candidato.
    """
    candidato_email = request.session.get('EMAIL_CANDIDATO', 'Candidato Desconhecido')
    cursor = connection.cursor()

    # Busca o ID do candidato com base no email.
    cursor.execute("SELECT id_candidato FROM candidato WHERE EMAIL_CANDIDATO = %s", [candidato_email])
    candidato_id = cursor.fetchone()
    if not candidato_id:
        return render(request, 'curriculo.html', {"erro": "Candidato não encontrado."})
    candidato_id = candidato_id[0]

    # Processa as requisições POST para adicionar habilidades ou experiências.
    if request.method == 'POST':
        # Se o POST contém 'habilidade', adiciona uma nova habilidade ao candidato.
        if 'habilidade' in request.POST:
            habilidade = request.POST.get('habilidade')
            if habilidade:
                # Chama a stored procedure 'adicionar_habilidade_spi'.
                cursor.callproc('adicionar_habilidade_spi', [candidato_email, int(habilidade)])

        # Se o POST contém 'adicionar_experiencia', adiciona uma nova experiência profissional.
        elif 'adicionar_experiencia' in request.POST:
            empresa = request.POST.get('empresa')
            cargo = request.POST.get('cargo')
            inicio = request.POST.get('inicio')
            fim = request.POST.get('fim') or None # 'None' se o campo 'fim' estiver vazio
            descricao = request.POST.get('descricao')

            # Insere a nova experiência na tabela 'experiencia'.
            cursor.execute("""
                INSERT INTO experiencia (id_candidato, empresa, cargo, inicio, fim, descricao)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [candidato_id, empresa, cargo, inicio, fim, descricao])

        connection.commit() # Confirma as alterações no banco de dados.
        cursor.close()
        return redirect('curriculo') # Redireciona para a própria página de currículo para atualizar a exibição.

    # Lista as habilidades do candidato.
    cursor.execute("""
        SELECT h.nome FROM habilidade h
        JOIN candidato_habilidade ch ON h.id = ch.id_habilidade
        WHERE ch.id_candidato = %s
    """, [candidato_id])
    habilidades_candidato = [{'nome': row[0]} for row in cursor.fetchall()]

    # Lista as experiências profissionais do candidato.
    cursor.execute("""
        SELECT empresa, cargo, inicio, fim, descricao FROM experiencia
        WHERE id_candidato = %s ORDER BY inicio DESC
    """, [candidato_id])
    experiencias = [
        {
            'empresa': row[0],
            'cargo': row[1],
            'inicio': row[2],
            'fim': row[3],
            'descricao': row[4]
        } for row in cursor.fetchall()
    ]
    cursor.close()

    # Busca todas as habilidades disponíveis no sistema para a seleção.
    cursor = connection.cursor()
    cursor.execute("SELECT id, nome FROM plataforma_empregos.habilidade")
    habilidades = [{'habilidade': row[0], 'nome': row[1]} for row in cursor.fetchall()]
    cursor.close()

    # Essa parte do código parece repetir a busca por habilidades do candidato.
    # Pode ser uma duplicação desnecessária se a primeira busca já for suficiente.
    cursor = connection.cursor()
    cursor.callproc('habilidade_sps', [candidato_email])
    habilidades_candidato = [{'nome': row[0]} for row in cursor.fetchall()]
    cursor.close()


    # Renderiza a página de currículo, passando as habilidades e experiências.
    return render(request, 'vagas/curriculo.html', {
        'habilidades_candidato': habilidades_candidato,
        'experiencias': experiencias,
        'habilidades': habilidades,
    })


def sucesso_view(request, id_requisito):
    """
    Exibe uma página de sucesso após a criação de uma vaga, mostrando os requisitos associados.
    """
    # Busca os requisitos da vaga com base no ID do requisito.
    cursor = connection.cursor()
    cursor.execute("SELECT REQUISITOS FROM plataforma_empregos.requisitos_da_vaga WHERE id_requisito = %s", [id_requisito])
    requisitos = [{'requisito': row[0]} for row in cursor.fetchall()]

    # Renderiza a página de sucesso, passando o ID do requisito e os requisitos.
    return render(request, 'vagas/sucesso.html', {'id_requisito': id_requisito, 'requisitos': requisitos})


def adicionar_requisito(request):
    """
    Permite adicionar novos requisitos a uma vaga existente via requisição AJAX (POST).
    Recebe o ID do requisito e o texto do requisito, e chama uma stored procedure
    ('adicionar_requisito_spi') para inseri-lo no banco de dados.
    Retorna uma resposta JSON indicando o sucesso ou falha da operação.
    """
    if request.method == "POST":
        # Carrega os dados JSON do corpo da requisição.
        data = json.loads(request.body)
        id_requisito = data.get("id_requisito")
        requisito = data.get("requisito")

        if id_requisito and requisito:
            cursor = connection.cursor()
            # Chama a stored procedure 'adicionar_requisito_spi'.
            cursor.callproc('adicionar_requisito_spi', [id_requisito, requisito])
            connection.commit() # Confirma a transação.
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Dados inválidos"})

    return JsonResponse({"success": False, "error": "Método não permitido"})


def sucesso(request):
    """
    Renderiza um template de sucesso genérico.
    Pode ser usado para redirecionamentos simples após ações bem-sucedidas.
    """
    return render(request, 'vagas/sucesso.html')


def area_empresa(request):
    """
    Renderiza uma página para a área da empresa.
    Atualmente, passa dados de exemplo para o contexto, mas pode ser expandido
    para carregar dados dinamicamente.
    """
    context = {
        'nome_empresa': 'Nome da Empresa',
        'descricao': 'Descrição da vaga',
        'localizacao': 'Localização da vaga',
        'area': 'Área da vaga',
        'info_adicionais': 'Informações adicionais',
        'beneficios': 'Benefícios oferecidos',
    }
    return render(request, 'vagas/area_empresa.html', context)

# ---
## Funções de Chat
# ---

@login_required
def chat_fullpage(request):
    """
    Exibe a interface completa do chat para o usuário logado.
    Permite iniciar novos chats com outros usuários e exibe os chats existentes.
    """
    chats = obter_chats_do_usuario(request.user) # Obtém todos os chats do usuário logado.
    erro = None
    chat_id_para_abrir = request.GET.get('chat') # Tenta obter um ID de chat da URL para abrir.

    if request.method == 'POST':
        email_destino = request.POST.get('email_destino')
        # Tenta encontrar o usuário destinatário pelo email.
        destinatario = User.objects.filter(email=email_destino).first()

        if not destinatario:
            # Se o destinatário não for encontrado, exibe uma mensagem de erro.
            return render(request, 'vagas/chat_fullpage.html', {
                'chats': chats,
                'erro': 'Usuário não encontrado.'
            })

        # Verifica se já existe um chat entre os dois usuários.
        chat_existente = Chat.objects.annotate(num_participantes=Count('participantes')) \
            .filter(participantes=request.user) \
            .filter(participantes=destinatario) \
            .filter(num_participantes=2) \
            .first()

        if chat_existente:
            chat_id_para_abrir = chat_existente.id # Se existir, usa o ID do chat existente.
        else:
            novo_chat = Chat.objects.create() # Cria um novo chat.
            novo_chat.participantes.add(request.user, destinatario) # Adiciona os participantes ao novo chat.
            chat_id_para_abrir = novo_chat.id

    # Renderiza a página do chat, passando os chats do usuário e o ID do chat a ser aberto.
    return render(request, 'vagas/chat_fullpage.html', {
        'chats': chats,
        'chat_id_para_abrir': chat_id_para_abrir,
        'erro': erro
    })


@login_required
def atualizar_mensagens(request, chat_id):
    """
    Atualiza as mensagens de um chat específico.
    Usada para carregar as mensagens mais recentes via AJAX.
    """
    chat = get_object_or_404(Chat, id=chat_id) # Busca o objeto Chat pelo ID ou retorna 404.
    # Verifica se o usuário logado é participante do chat para evitar acesso não autorizado.
    if request.user not in chat.participantes.all():
        return HttpResponse(status=403) # Retorna Forbidden se o usuário não for participante.
    mensagens = chat.mensagem_set.order_by('timestamp') # Obtém as mensagens ordenadas por data/hora.
    # Renderiza um template parcial apenas com as mensagens.
    return render(request, 'vagas/mensagens_parciais.html', {'mensagens': mensagens, 'user': request.user})


@login_required
def enviar_mensagem(request, chat_id):
    """
    Permite enviar uma nova mensagem para um chat específico.
    Processa requisições POST com o texto da mensagem.
    """
    if request.method == 'POST':
        texto = request.POST.get('mensagem')
        chat = get_object_or_404(Chat, id=chat_id) # Busca o objeto Chat pelo ID.
        # Verifica se o usuário é participante do chat antes de permitir o envio da mensagem.
        if request.user in chat.participantes.all():
            Mensagem.objects.create(chat=chat, remetente=request.user, texto=texto) # Cria a nova mensagem.
            return HttpResponse(status=200) # Retorna sucesso.
    return HttpResponse(status=400) # Retorna Bad Request se o método não for POST ou se houver erro.

def obter_chats_do_usuario(user):
    """
    Função auxiliar para obter todos os chats de um usuário.
    Adiciona o email do "outro" participante do chat para exibição.
    """
    return Chat.objects.filter(participantes=user).annotate(
        outro_email=Subquery(
            Chat.participantes.through.objects
            .filter(chat_id=OuterRef('pk'))
            .exclude(user_id=user.id)
            .values('user__email')[:1]
        )
    )