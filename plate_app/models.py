from django.db import models
from django.contrib.auth.models import User

class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="history/")
    plate = models.CharField(max_length=20)
    state = models.CharField(max_length=50)
    confidence = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)