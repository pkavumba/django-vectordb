# [Django VectorDB][docs]

---

Django Vector DB is a powerful and flexible toolkit for adding vector similarity search to your Django applications. It is built on top of lightening fast approximate nearest neighbor search library: hnswlib.

Some reasons you might want to use Django Vector DB:

- Low latency, because you don't need to call an external API.
- Scalable to a billion vectors with millisecond search results.
- Fast and accurate search.
- Native Django integration.
- Metadata filtering with the full power of the django queryset queries, e.g. `vectordb.filter(metadata__user_id=1).search("some text").only("text")`
- Automatic syncing between your models and the vector index, simply register the provided signals and you can continue about your day. Vectordb will sync the vector database whenever you create, update or delete an instance.
- Out of the box support for incremental updates, allowing you to add or update data without rebuilding the entire index.
- Extensive documentation and support for easy implementation and troubleshooting.

## Requirements

---

Django VectorDB requires the following:

- [Python][python] (3.6, 3.7, 3.8, 3.9, 3.10, 3.11)
- [Django][django] (2.2, 3.0, 3.1, 3.2, 4.0, 4.1, 4.2)
- [HNSWLib][hnswlib] (0.7.0)
- [numpy][numpy]

We **highly recommend** and only officially support the latest patch release of
each Python and Django series.

The following packages are optional:

- [Sentence-Transformers][sentence-transformers] - Add support for converting text into vector embeddings used for similarity search
- [Django Rest Framework][drf] - Add API endpoint for VectorDB.
- [django-filters][django-filters] - Add metadata filtering support on the API endpoint.

---

## Installation

Install using `pip`, it is recommended that you install the optional packages with:

```bash
# This will install the optional dependencies above.
pip install "django-vectordb[standard]"
```

If you dont want to install the optional packages you can run:

```bash
pip install django-vectordb
```

Add `'django-vectordb'` to your `INSTALLED_APPS` setting.

```py hl_lines="3" title="settings.py"
INSTALLED_APPS = [
    ...
    'vectordb',
]
```

Run the migrations to create the `vectordb` table

```bash
$ ./manage.py migrate
```

If you're intending to use the API, you'll probably also want to add vectordb.urls. Add the following to your root `urls.py` file.

```python hl_lines="3" title="urls.py"
urlpatterns = [
    ...
    path('api/', include('vectordb.urls'))
]
```

Note: that the URL path can be whatever you want.

This will expose endpoints for all CRUD actions (`/api/vectordb/`) and searching (`/api/vectordb/search/`).

---

## Example

Lets begin with a simple example for a blog post app. We will assume the app contains the following model in `blog/models.py`.

```python linenums="1" title="blog/models.py"

from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Post(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    def __str__(self):
        return self.title
```

### 1. Working with the Django Vector Database

To begin working with VectorDB, you'll first need to import it into your project. There are two ways to do this, depending on whether you'd like to use the simple proxy to the vector models manager, `Vector.objects`, or the Vector model directly.

#### Option 1: Import the simple proxy [Recommended]

```python
from vectordb import vectordb
```

#### Option 2: Import the Vector model directly

```python
from vectordb import get_vectordb_model

VectorModel = get_vectordb_model()
```

With either of these imports, you'll have access to all the Django manager functions available on the object. Note that you can run the commands detailed below using `vectordb` or `VectorModel.objects`, whichever you've chosen to import. For the rest of this guide we will use `vectordb`.

Now that you've imported VectorDB, it's time to dive in and explore its powerful features!

### Populating the Vector Database

First, let's make a few updates to the model to allow VectorDB to handle most tasks for us: add `get_vectordb_text` and `get_vectordb_metadata` methods.

```python linenums="1" title="blog/models.py" hl_lines="13-19"
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Post(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def get_vectordb_text(self):
        # Use title and description for vector search
        return f"{self.title} -- {self.description}"

    def get_vectordb_metadata(self):
        # Enable filtering by any of these metadata
        return {"title": self.title, "description": self.description, "user_id": self.user.id, "model": "post"}
```

In an existing project, you can run the `vectordb_sync` management command to add all items to the database.

```bash
./manage.py vectordb_sync <app_name> <model_name>
```

For this example:

```bash
./manage.py vectordb_sync blog Post
```

### Automatically Incremental Updates

Making sure that your vector database is up to date can be a pain. Django VectorDB makes this easy by laveraging django a signals that will automatically update the vector database whenever you create, update or delete an instance.

To enable auto sync, register the model to vectordb sync handlers in `apps.py`. The sync handlers are signals defined in `vectordb/sync_signals.py`.

```python linenums="1" title="blog/apps.py" hl_lines="8-11"
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        from .models import Post
        from vectordb.shortcuts import autosync_model_to_vectordb
        autosync_model_to_vectordb(Post)
```

This will automatically sync the vectors when you create and delete instances.

!!! note

    Note that signals are not called in bulk create, so you will need to sync manually when using those methods.

!!! info

    While this example consider only one model class, you can register as many models are needed with django vector database. You can then utilize the versatile django filters to scope your searches. Note searching using a model instance automatically scopes the results to that instance type. See below for more details.

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

These signals will sync the vectors when you create and delete instances

Ensure that your models implement the `get_vectordb_text()` and/or `get_vectordb_metadata()` methods for proper syncing.

#### Manually populating the django vector database

In some instances, you may want to manually populate the vector database. Django vector database provides two utility methods for adding items to the database: `vectordb.add_instance` or `vectordb.add_text`. Note that for adding the instance, you need to provide the `get_vectordb_text` and an optional `get_vectordb_metadata` methods.

##### 1. Adding Model Instances

```python
post1 = models.create(title="post1", description="post1 description", user=user1) # provide valid user

# add to vector database
vectordb.add_instance(post1)
```

##### 2. Adding Text to the Model

To add text to the database, you can use `vectordb.add_text()`:

```python
vectordb.add_text(text="Hello text", id=3, metadata={"user_id": 1})
```

The `text` and `id` are required. Additionally, the `id` must be unique, or an error will occur. `metadata` can be `None` or any valid JSON.

## Vector Similary Search with Django Vector Database

To search, simply call `vectordb.search()`:

```python
vectordb.search("Some text", k=10) # k is the maximum number of results you want.
```

Note: search method returns a query whose results are order from best match. Each item will have the following fields: `id`, `content_object`, `object_id`, `content_type`, `text`, `embedding`, annotated `distance`, and a property `vector` that returns the `np.ndarray` representation of the item. Because search gives us a `QuerySet` we can choose the fiels we want to see like sos:

```python
vectordb.search("Some text", k=10).only('text', 'content_object')
```

Search doesn't only work for `text` you can also search for model instances:

```python
post1 = Post.objects.get(id=1)
# Limit the search scope to a user with an id of 1
results = vectordb.search(post1, k=10)
```

This is also a way to get related posts to `post1`. Thus, you can use `vectordb` for recommendations as well.

!!! note

    Using a model instance will automatically scope the results to only instances of that type. For example, if you search by `post1` you will only get results that are instances of `Post`.

If `k` is not provided, the default value is 10.

## Metadata Filtering with Django Vector Database

Django vector database provides a powerful way to filter on metadata, using the intuitive Django QuerySet methods.

You can filter on `text` or `metadata` with the full power of Django QuerySet filtering. You can combine as many filters as needed. And since Django vector database is built on top of Django QuerySet, you can chain the filters with the search method. You can also filter on nested metadata fields.

```python
# scope the search to user with an id 1
vectordb.filter(metadata__user_id=1).search("Some text", k=10)

# example two with more filters
vectordb.filter(text__icontains="Apple",
    metadata__title__icontains="IPhone",
    metadata__description__icontains="2023"
    ).search("Apple new phone", k=10)
```

If our metadata was nested like follows:

```json
{
  "text": "Sample text",
  "metadata": {
    "date": {
      "year": 2021,
      "month": 7,
      "day": 20,
      "time": {
        "hh": 14,
        "mm": 30,
        "ss": 45
      }
    }
  }
}
```

We can filter on the nested fields like so:

```python
vectordb.filter(
    metadata__date__year=2021,
    metadata__date__time__hh=14
    ).search("Sample text", k=10)
```

Refer to the [Django documentation](https://docs.djangoproject.com/en/4.2/topics/db/queries/) on querying the `JSONField` for more information on filtering.

---

## Settings

You can customize `vectordb` by overriding one of the following settings in `settings.py` file of your project. The following settings are available:

```python title="settings.py"
# settings.py
DJANGO_VECTOR_DB = {
    "DEFAULT_EMBEDDING_CLASS": "vectordb.embedding_functions.SentenceTransformerEncoder",
    "DEFAULT_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
    # Can be "cosine" or "l2"
    "DEFAULT_EMBEDDING_SPACE": "l2"
    "DEFAULT_EMBEDDING_DIMENSION": 384, # Default is 384 for "all-MiniLM-L6-v2"
    "DEFAULT_MAX_N_RESULTS": 10, # Number of results to return from search maximum is default is 10
    "DEFAULT_MIN_SCORE": 0.0, # Minimum score (distance) to return from search default is 0.0
    "DEFAULT_MAX_BRUTEFORCE_N": 10_000, # Maximum number of items to search using brute force default is 10_000. If the number of items is greater than this number, the search will be done using the HNSW index.
}
```

---

## Quickstart

Can't wait to get started? The [quickstart guide][quickstart] is the fastest way to get up and running, and building APIs with REST framework.

---

## Development

Clone the repository

```bash
$ git clone https://github.com/pkavumba/django-vectordb.git
```

Install the app in editable mode with all dev dependencies:

```bash
pip install -e .[dev]
```

This command will install the app and its dev dependencies specified in the `setup.cfg` file. The `-e` flag installs the package in editable mode, which means that any changes you make to the app's source code will be reflected immediately without needing to reinstall the package. The `[dev]` part tells `pip` to install the dependencies listed under the "dev" section in the `options.extras_require` of the `setup.cfg` file.

Run tests

```bash
pytest
```

Or

```bash
tox
```

[python]: https://www.python.org
[django]: https://www.djangoproject.com
[numpy]: https://numpy.org
[quickstart]: tutorial/quickstart.md
[sentence-transformers]: https://www.sbert.net
[hnswlib]: https://github.com/nmslib/hnswlib
[drf]: https://www.django-rest-framework.org
[django-filters]: https://pypi.org/project/django-filter/
[docs]: https://pkavumba.github.io/django-vectordb/
