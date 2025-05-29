from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from vagas import views  

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro_empresa/', views.registro_empresa, name='registro_empresa'),  
    path('registro_candidato/', views.registro_candidato, name='registro_candidato'),  
    path('empresas/', views.empresas, name='empresas'),
    path('candidatos/', views.candidatos, name='candidatos'),
    path('nova-vaga/', views.novas_vagas, name='novas_vagas'),  
    path('sucesso/<str:id_requisito>/', views.sucesso_view, name='sucesso'),
    path('adicionar-requisito/', views.adicionar_requisito, name='adicionar_requisito'),
    path('admin/', admin.site.urls),
    path('minhas-vagas/', views.minhas_vagas, name='minhas_vagas'),
    path('candidatar_vaga/<str:id_vaga>/', views.candidatar_vaga, name='candidatar_vaga'),
    path('chat/enviar/<int:chat_id>/', views.enviar_mensagem, name='enviar_mensagem'),
    path('chat/<int:chat_id>/atualizar/', views.atualizar_mensagens, name='atualizar_mensagens'),
    path('chat/fullpage/', views.chat_fullpage, name='chat_fullpage'),
    path('curriculo', views.curriculo, name='curriculo'),
    path('candidatura/<int:id_vaga>/', views.candidatura, name='candidatura'),
    path('minhas_candidaturas', views.minhas_candidaturas, name='minhas_candidaturas'),
    path('ver_candidatos/<int:id_vaga>/', views.ver_candidatos, name='ver_candidatos'),
    path('detalhes_candidatos/<int:id_vaga>/', views.detalhes_candidatos, name='detalhes_candidatos'),
    ]