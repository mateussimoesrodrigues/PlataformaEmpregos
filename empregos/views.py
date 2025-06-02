from django.shortcuts import render

# Função para a página inicial
def index(request):
    return render(request, 'empregos/index.html')