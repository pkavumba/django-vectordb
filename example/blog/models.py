from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title

    def get_text(self):
        return f"{self.title} -- {self.description}"

    def to_json(self):
        return {"title": self.title, "description": self.description}
