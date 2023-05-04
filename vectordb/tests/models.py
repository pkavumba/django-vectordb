from django.db import models


class ExampleModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

    def get_text(self):
        return self.description

    def serialize(self):
        return {"name": self.name, "description": self.description}
