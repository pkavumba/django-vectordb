# Tutorial 2: Integrating Django Vector Database in our Blog Site

Welcome to Tutorial 2! In this tutorial, we will be integrating the `django-vectordb` into our Blog Site. By the end of this tutorial, we will:

- Integrate `django-vectordb` into our project.
- Update our Post model to allow `django-vectordb` to automatically extract the text for vector search, as well as any metadata we want to filter on.
- Update the vector database with all the blog Posts that are currently on our site.
- Configure our site to automatically sync with the vector database whenever we `create`, `update` or `delete` posts.
- Configure our site to display related blog recommendations using the `django-vectordb`.

Let's get started!

## Adding VectorDB

If you haven't installed vectordb already install it

```bash
pip install "django-vectordb[standard]"
```

Next lets add `django-vectordb` to the `INSTALLED_APPS`. Open `tutorial/settings.py` and add `vectordb` to the installed apps.

```python title="tutorial/settings.py" hl_lines="10"
# settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "blog",
    "vectordb", # <--
]
```

Finally, lets run the migrations to create the `vectordb` table.

```bash
./manage.py migrate
```

## Update Post Model for VectorDB to Automatically Extract Text and Metadata

Next lets add to methods to our model to allow vectordb to properly index our Posts.

First we need to pick the text we want to search by. For this tutorial we use both the `title` and the `description` of each blog.

```python title="blog/models.py" linenums="1" hl_lines="14-23"
# blog/models.py
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
```

Documentation Writing in progress -- check back soon!
