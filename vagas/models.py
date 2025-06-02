from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    criado_em = models.DateTimeField()

    participantes = models.ManyToManyField(User, through='ChatParticipante')

    class Meta:
        managed = False  # <- Django não vai criar nem alterar a tabela
        db_table = 'chat'

    def __str__(self):
        return f"Chat {self.id}"

class ChatParticipante(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'chat_participantes'

class Mensagem(models.Model):
    id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    remetente = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'mensagem'

    def __str__(self):
        return f"{self.remetente.username} às {self.timestamp}"
