from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_vectordb_text(self):
        return self.title + " " + self.description

    def get_vectordb_metadata(self):
        return {
            "user_id": self.user.id,
            "username": self.user.username,
            "created_at_year": self.created_at.year,
            "created_at_month": self.created_at.month,
        }

    def __str__(self):
        return self.title
