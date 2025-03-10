from django.db import models

class VagaDeEmprego(models.Model):
    id_vaga = models.AutoField(primary_key=True)  # Definição correta do ID
    nome_empresa = models.CharField(max_length=50)
    descricao = models.TextField()
    localizacao = models.CharField(max_length=70, null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    info_adicionais = models.TextField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    id_requisito = models.CharField(max_length=255, null=True, blank=True)
    beneficios = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'vagas_de_emprego'  # Mapeia para a tabela real do banco
        verbose_name = 'Vaga de Emprego'
        verbose_name_plural = 'Vagas de Emprego'

    def __str__(self):
        return f'{self.nome_empresa} - {self.area}'
