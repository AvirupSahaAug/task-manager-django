from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    color = models.CharField(max_length=7, default="#ffffff")
    completed = models.BooleanField(default=False)
    # Use ManyToManyField so a task can be assigned to one or more users.
    users = models.ManyToManyField(User)

    def __str__(self):
        return self.title


# models.py
from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    streak = models.PositiveIntegerField(default=0)
    last_checked = models.DateField(null=True, blank=True)
