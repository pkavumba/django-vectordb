# Tutorial 3: Setting Up Django Vector Database to Automatically Sync with Our Models

Welcome to Tutorial 3! In the [previous tutorial][previous-tutorial], we added `django-vectordb` to our Blog Post project. We also saw how to add existing instance to django vector database using management commands. In this tutorial, we will set up our site to automatically sync with the vector database whenever we `create`, `update`, or `delete` post instances.

Let's get started!

## Configure Django Vector Database to Automatically Sync with our Models

One of the common pain points while using vector databases is the process of keeping them in sync with our application's data. Synchronizing data can be time-consuming and prone to errors, making it a hassle for developers to manage different data sources effectively.

Django Vector Database provides an effortless solution for this issue by enabling automatic synchronization with our models. By configuring the Django Vector Database AutoSync feature, you can ensure that our site stays in sync with the vector database every time you `create`, `update`, or `delete` posts.

To achieve this seamless integration, you can use the Django Vector Database a convenient shortcut, `autosync_model_to_vectordb`, which allows you to register our models `post_save` and `post_delete` signals with django vector database. This shortcut register signals that will automatically sync our models with the vector database whenever you `create`, `update`, or `delete` instances.

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

    Although this example focuses on a single model (`Post`), you can incorporate as many models as desired into the Django vector database.

!!! note

    The automatic synchronization relies on the `post_save` and `post_delete` signals. As such, synchronization will not occur when using `bulk_create` since it does not trigger the `post_save` signal. If you need to sync after employing `bulk_create`, you must manually add the instances to the Django vector database. For more information, consult the [django-bulk-create] documentation.

If you prefer, you can manually register the signals by importing the following signal handlers and registering them with our models' `post_save` and `post_delete` signals:

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

## Summary

In this tutorial, we learned how to configure Django Vector Database to automatically sync with our models. We also learned how to use the `autosync_model_to_vectordb` shortcut to register our models' `post_save` and `post_delete` signals with the Django Vector Database. In the [upcoming tutorial][next-tutorial], we will look at how to manually add data to the django vector database.

[previous-tutorial]: 3-automatically-updating-vector-database.md
[next-tutorial]: 4-manually-updating-vector-database.md
