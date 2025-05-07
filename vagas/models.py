from django.db import models


class Vaga(models.Model):
    nome = models.CharField(max_length=200)
    
class Requisito(models.Model):
    requisito = models.CharField(max_length=200)
    vaga = models.ForeignKey(Vaga, related_name='requisitos', on_delete=models.CASCADE)

    def __str__(self):
        return self.descricao

class VagaDeEmprego(models.Model):
    id_vaga = models.AutoField(primary_key=True)
    nome_empresa = models.CharField(max_length=50)
    descricao = models.TextField()
    localizacao = models.CharField(max_length=70, null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    info_adicionais = models.TextField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    beneficios = models.CharField(max_length=255, null=True, blank=True)
    cargo = models.CharField(max_length=255)
    
    # Relacionamento com Requisito
    requisitos = models.ManyToManyField(Requisito, related_name='vagas')

    class Meta:
        db_table = 'vagas_de_emprego'
        verbose_name = 'Vaga de Emprego'
        verbose_name_plural = 'Vagas de Emprego'

    def __str__(self):
        return f'{self.nome_empresa} - {self.area}'
