# Tutorial 2: Integrating Django Vector Database

Welcome to Tutorial 2! In the [previous tutorial][previous-tutorial], we setup our Blog Post project that we will use for the rest of the tutorial to demonstrate the feature of `django-vectordb`. In this tutorial, we will integrate `django-vectordb` into our Blog Site. By the end of this tutorial, we will:

- Integrate `django-vectordb` into our project.
- Update our Post model to allow `django-vectordb` to automatically extract the text for vector search, as well as any metadata we want to filter on.
- Update the vector database with all the blog Posts that are currently on our site.
- Configure our site to automatically sync with the vector database whenever we `create`, `update` or `delete` posts.
- Configure our site to display related blog recommendations using the `django-vectordb`.

Let's get started!

## Adding VectorDB to the Project

If you haven't installed vectordb already, install it with the following command:

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

First we need to pick the text we want to search by. For this tutorial we use both the `title` and the `description` of each blog. We tell `vectordb` about the text we want to use through the `get_vectordb_text` method.
Second, we need to select the metadata we want to use for filtering. For this example, we will use the `user_id`, `username` and `created_at` of each blog post. We will break down the `create_at` into `year`, `month` and `day` to demonstrate nested filtering. We tell `django-vectordb` about the metadata we want to use through the `get_vectordb_metadata` method. If we don,t provide this method, vectordb will use the django serializer to serialize the entire model. This maybe suboptimal for large models.

```python title="blog/models.py" linenums="1" hl_lines="14-26"
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
            "created_at": {
                "year": self.created_at.year,
                "month": self.created_at.month,
                "day": self.created_at.day,
            },
        }
```

## Update VectorDB with Existing Posts

Django vector database provides a management command to update the vector database with existing models. It takes two arguments the `app_name` and the `model_name`, which in this case are `blog` and `Post`.
Lets run this command to update the vector database with all the existing posts.

```bash
./manage.py vectordb_sync <app_name> <model_name>
```

```bash
./manage.py vectordb_sync blog Post
```

!!! info

    Django vector database also provides a management command for reseting the vector database. Note that this is distractive and irreversible.

    ```bash
    ./manage.py vectordb_reset
    ```

## Summary

In this tutorial, we successfully integrated the Django vector database into our blog post project. Additionally, we synced our existing blog posts with the Django vector database using the `vectordb_sync` management command. In the [upcoming tutorial][next-tutorial], we will set up our blog post app to automatically synchronize with the Django vector database whenever we `create`, `update`, or `delete` blog posts.

[django-bulk-create]: https://docs.djangoproject.com/en/4.2/ref/models/querysets/#bulk-create
[previous-tutorial]: 1-project-setup.md
[next-tutorial]: 3-automatically-updating-vector-database.md
