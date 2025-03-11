from django.urls import path
from . import views

urlpatterns = [
    path('dados-customizados/', views.listar_dados_customizados, name='listar_dados_customizados'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('empresas/', views.empresas, name='empresas'),
    path('candidatos/', views.candidatos, name='candidatos'),
    path('pesquisa-vagas/', views.pesquisa_vagas, name='pesquisa_vagas'),  # Modificada
]

