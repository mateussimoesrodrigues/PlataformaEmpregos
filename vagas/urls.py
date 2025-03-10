from django.urls import path
from . import views

urlpatterns = [
    path('dados-customizados/', views.listar_dados_customizados, name='listar_dados_customizados'),
]
