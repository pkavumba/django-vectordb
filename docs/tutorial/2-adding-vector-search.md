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

## Configure VectorDB to Automatically Sync with our Models

Next we need to configure our site to automatically sync with the vector database whenever we `create`, `update` or `delete` posts. We do this by adding a `post_save` and `post_delete` signal to our `Post` model. We will use a shortcut, `autosync_model_to_vectordb`, provide by django vector database to register the `post_save` and `post_delete` signals.

```python title="blog/apps.py" linenums="1" hl_lines="8-14"
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        from vectordb.shortcuts import autosync_model_to_vectordb

        from .models import Post

        autosync_model_to_vectordb(Post)
```

!!! info

    While this example only considers one model (`Post`), you can add as many models as you want to django vector database method.

!!! note

    This auto sync depends on the `post_save` and `post_delete` signals. Thus, sync won't happen when you use bulk_create because it does not trigger the `post_save` signal. If you want to sync after using `bulk_create` you will need to manually add the instances to django vector database. Refer to the [django-bulk-create] documentation for more information.

Alternatively, you can import the following signals and register them by yourself:

```python linenums="1" title="blog/signals.py"
# blog/signals.py
from django.db.models.signals import post_save, post_delete

from vectordb.sync_signals import (
    sync_vectordb_on_create_update,
    sync_vectordb_on_delete,
)

from .models import Post

post_save.connect(
    sync_vectordb_on_create_update,
    sender=Post,
    dispatch_uid="update_vector_index_super_unique_id",
)

post_delete.connect(
    sync_vectordb_on_delete,
    sender=Post,
    dispatch_uid="delete_vector_index_super_unique_id",
)
```

If you choose to manually register the signals you will need to make the following changes to the `apps.py`:

```python linenums="1" title="blog/apps.py" hl_lines="9 10"
# blog/apps.py
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        import blog.signals
```

Documentation Writing in progress -- check back soon!

[django-bulk-create]: https://docs.djangoproject.com/en/4.2/ref/models/querysets/#bulk-create
