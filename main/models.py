from typing import Iterable
from django.db import models
import random
from django.contrib.auth.models import AbstractUser, User

# Create your models here.

class Images(models.Model):
    url = models.TextField(unique=True)
    description = models.TextField(null = True)
    randomized = models.IntegerField(null=True)
    is_active = models.BooleanField(default=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        if  self.description != None:
            return  self.description
        else:
            return 'No name'
        
    def save(self, *args, **kwargs) -> None:
        if self.randomized == None:
            self.randomized = random.randint(1,10000)
        return super().save(*args, **kwargs)
    class Meta:
        ordering = ['-id']
    
    class User():
        def save(self, *args, **kwargs):
            if not User.objects.filter(email = self.email).first():
                return super().save(*args, **kwargs)
    


