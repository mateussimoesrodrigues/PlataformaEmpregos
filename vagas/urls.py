from django.urls import path
from . import views

urlpatterns = [
    path('dados-customizados/', views.listar_dados_customizados, name='listar_dados_customizados'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('empresas/', views.empresas, name='empresas'),
    path('candidatos/', views.candidatos, name='candidatos'),
    path('pesquisa-vagas/', views.pesquisa_vagas, name='pesquisa_vagas'),  
    path('nova-vaga/', views.novas_vagas, name='novas_vagas'),  
    path('criar-vaga/', views.criar_vaga, name='criar_vaga'),
    path('sucesso/<str:id_requisito>/', views.sucesso_view, name='sucesso'),
    path('adicionar-requisito/', views.adicionar_requisito, name='adicionar_requisito'),
    ]

