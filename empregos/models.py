from django.db import models

class Vaga(models.Model):
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    localizacao = models.CharField(max_length=100)
    data_postagem = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo
