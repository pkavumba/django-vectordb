# [Django VectorDB][docs]

---

![PyPI](https://img.shields.io/pypi/v/django-vectordb?color=blue)
![GitHub](https://img.shields.io/github/license/pkavumba/django-vectordb)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-vectordb)
[![Downloads](https://static.pepy.tech/badge/django-vectordb)](https://pepy.tech/project/django-vectordb)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/django-vectordb)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

**Adding extremely fast, low-latency, and scalable vector similarity search to django applications.**

Full documentation for the project is available at [https://pkavumba.github.io/django-vectordb/][docs].

[Django Vector Database][docs] is a powerful and flexible toolkit for adding vector similarity search capabilities to your Django applications. It is built on top of the lighteningly fast nearest neighbor search library: hnswlib.

Some reasons you might want to use Django Vector DB:

- Low latency, because you don't need to call an external API.
- Scalable to a billion vectors with millisecond search results.
- Fast and accurate search.
- Native Django integration.
- Metadata filtering with the full power of the django queryset queries, e.g. `vectordb.filter(metadata__user_id=1).search("some text").only("text")`
- Automatic syncing between your models and the vector index, simply register the provided signals and you can continue about your day. Vectordb will sync the vector database whenever you create, update or delete an instance.
- Out of the box support for incremental updates, allowing you to add or update data without rebuilding the entire index.
- Extensive documentation and support for easy implementation and troubleshooting.


> **Note:**
>
> Version 0.4.0 introduces the `LOAD_EMBEDDING_MODEL_ON_STARTUP` setting, which allows you to control when the embedding model weights are loaded when using the default `sentence-transformers`. While preloading the weights is advantageous in production environments, it can add a few seconds of delay during development. This option enables you to skip reloading the model weights on every startup.
>
> To enable this option, add the following in your `settings.py`:
>
> ```diff
> # settings.py
> {
> + # Disable preloading weights when in DEBUG or dev mode
> + LOAD_EMBEDDING_MODEL_ON_STARTUP: not DEBUG,
> }
> ```



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

## Quickstart
Follow these steps to quickly get started with using `django-vectordb` in your project.

### 1. Installation

#### Installing with Optional Packages
For full functionality out-of-the-box, it's recommended to install `django-vectordb` with optional dependencies:

```bash
# This will install the optional dependencies above.
pip install "django-vectordb[standard]"
```

#### Basic Installation
If you prefer not to install the optional packages at the moment, you can go for a minimal setup:

```bash
pip install django-vectordb
```

#### Update Django Settings
Add `django-vectordb` to your Django project's settings within the `INSTALLED_APPS` configuration:

```diff
  INSTALLED_APPS = [
      ...
+     'vectordb',
  ]
```

#### Database Migration
To create the necessary `vectordb` database tables, run the migrations:

```bash
./manage.py migrate
```

### 2. Extend Your Models

In your `models.py`, extend your models to include methods for vector database integration. The following adjustments can be made to a simple blog `Post` model:

```diff
# your_app/models.py

from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Post(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

+   def get_vectordb_text(self):
+       # Use title and description for vector search
+       return f"{self.title} \n\n {self.description}"
+
+   def get_vectordb_metadata(self):
+       # Enable filtering by any of these metadata
+       return {"title": self.title, "description": self.description, "user_id": self.user.id, "model": "post"}
```

### 3. Automate Data Syncing
To automate the process of syncing your Django models with Vectordb every time data is created, updated, or deleted, adjust your `apps.py` as follows:

```diff
  # `your_app/apps.py`
  from django.apps import AppConfig


  class BlogConfig(AppConfig):
      default_auto_field = "django.db.models.BigAutoField"
      name = "blog"

      def ready(self):
+         from .models import Post
+         from vectordb.shortcuts import autosync_model_to_vectordb
+         autosync_model_to_vectordb(Post)
```

### 4. Sync Vector Database
Manually synchronize your Django models with the vector database to update their embeddings:

```bash
./manage.py vectordb_sync blog Post
```

### 5. Perform a Search
Use the `vectordb.search()` function in your views or logic to perform vector search queries:

```python
vectordb.search("Some text", k=10) # Where `k` is the max number of results.
```

If you want to get your model instances, such as `Post` model instances, simply call unwrap on the query as below
```python
vectordb.search("Some text", k=10).unwrap()
```

Note: `unwrap` terminates the queryset because it returns `Post` objects in a python list.

### 6. (Optional) Expose an API Endpoint
If you intend to use `django-vectordb` through an API, integrating `vectordb.urls` into your project’s root `urls.py` file exposes all necessary CRUD and search functionalities:

```diff
  urlpatterns = [
      ...
+     path('api/', include('vectordb.urls'))
  ]
```

This will make the vectordb accessible under the specified path, offering endpoints for CRUD operations and search functionalities.

---

## Example

Lets beging with a simple example for blog posts

```python

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

### 1. Importing

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

```diff
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Post(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

+   def get_vectordb_text(self):
+       # Use title and description for vector search
+       return f"{self.title} -- {self.description}"
+
+   def get_vectordb_metadata(self):
+       # Enable filtering by any of these metadata
+       return {"title": self.title, "description": self.description, "user_id": self.user.id, "model": "post"}
```

In an existing project, you can run the `vectordb_sync` management command to add all items to the database.

```bash
./manage.py vectordb_sync <app_name> <model_name>
```

For this example:

```bash
./manage.py vectordb_sync blog Post
```

#### Manually adding items to the vector database

VectorDB provides two utility methods for adding items to the database: `vectordb.add_instance` or `vectordb.add_text`. Note that for adding the instance, you need to provide the `get_vectordb_text` and an optional `get_vectordb_metadata` methods.

##### 1. Adding Model Instances

```python
post1 = Post.objects.create(title="post1", description="post1 description", user=user1) # provide valid user

# add to vector database
vectordb.add_instance(post1)
```

##### 2. Adding Text to the Model

To add text to the database, you can use `vectordb.add_text()`:

```python
vectordb.add_text(text="Hello text", id=3, metadata={"user_id": 1})
```

The `text` and `id` are required. Additionally, the `id` must be unique, or an error will occur. `metadata` can be `None` or any valid JSON.

### Automatically Syncing Your Model to the vector database

To enable auto sync, register the model to vectordb sync handlers in `apps.py`. The sync handlers are signals defined in `vectordb/sync_signals.py`.

```diff
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

+   def ready(self):
+       from .models import Post
+       from vectordb.shortcuts import autosync_model_to_vectordb
+       autosync_model_to_vectordb(Post)
```

This will automatically sync the vectors when you create and delete instances.

Note that signals are not called in bulk create, so you will need to sync manually when using those methods.

Ensure that your models implement the `get_vectordb_text()` and/or `get_vectordb_metadata()` methods.

### Searching

To search, simply call `vectordb.search()`:

```python
vectordb.search("Some text", k=10) # k is the maximum number of results you want.
```

Note: The `search` method returns a query whose results are order from best match. Each item will have the following fields: `id`, `content_object`, `object_id`, `content_type`, `text`, `embedding`, annotated `distance` (lower is better), and a property `vector` that returns the `np.ndarray` representation of the item. Because `search` gives us a `QuerySet` we can choose the fields we want to see like sos:

```python
vectordb.search("Some text", k=10).only('text', 'content_object')
```

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

We can also use model instances instead of text:

```py
post1 = Post.objects.get(id=1)
# Limit the search scope to a user with an id of 1
results = vectordb.filter(metadata__user_id=1).search(post1, k=10)

# Scope the results to text which contains France, belonging to user with id 1 and created in 2023
vectordb.filter(text__icontains="Apple",
    metadata__title__icontains="IPhone",
    metadata__description__icontains="2023").search(post1, k=10)
```

Refer to the [Django documentation][django-queries] on querying the `JSONField` for more information on filtering.

---

## Settings

You can provide your settings in the `settings.py` file of your project. The following settings are available:

```python
# settings.py
DJANGO_VECTOR_DB = {
    "DEFAULT_EMBEDDING_CLASS": "vectordb.embedding_functions.SentenceTransformerEncoder",
    "DEFAULT_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
    "DEFAULT_EMBEDDING_SPACE": "l2", # Can be "cosine" or "l2"
    "DEFAULT_EMBEDDING_DIMENSION": 384, # Default is 384 for "all-MiniLM-L6-v2"
    "DEFAULT_MAX_N_RESULTS": 10, # Number of results to return from search maximum is default is 10
    "DEFAULT_MIN_SCORE": 0.0, # Minimum distance to return from search default is 0.0
    "DEFAULT_MAX_BRUTEFORCE_N": 10_000, # Maximum number of items to search using brute force default is 10_000. If the number of items is greater than this number, the search will be done using the HNSW index.
}
```

### OpenAI Configuration Changes

To configure your application to use OpenAI embeddings, you will need to adjust the `settings.py` as described below. These changes specify the use of OpenAI's embedding class, an appropriate embedding dimension that aligns with your choice of model, and the model identifier itself.


```diff
# settings.py adjustments for OpenAI integration
DJANGO_VECTOR_DB = {
-    "DEFAULT_EMBEDDING_CLASS": "vectordb.embedding_functions.SentenceTransformerEncoder",
+    "DEFAULT_EMBEDDING_CLASS": "vectordb.openai_embeddings.OpenAIEmbeddings",
-    "DEFAULT_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
+    "DEFAULT_EMBEDDING_MODEL": "text-embedding-ada-002",
     "DEFAULT_EMBEDDING_SPACE": "l2",
-    "DEFAULT_EMBEDDING_DIMENSION": 384, # Default is 384 for "all-MiniLM-L6-v2"
+    "DEFAULT_EMBEDDING_DIMENSION": 1536, # Has to match the OpenAI model selected
     "DEFAULT_MAX_N_RESULTS": 10,
     "DEFAULT_MIN_SCORE": 0.0,
     "DEFAULT_MAX_BRUTEFORCE_N": 10_000,
+    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", None), # Ensure this is properly set for OpenAI usage
}
```

### Cohere Configuration Changes

Similarly, to switch your embedding provider to Cohere, you will need to make the following adjustments in the `settings.py`. These changes will set Cohere as your embedding provider by specifying its embedding class, dimension, and the model you plan to use.


```diff
# settings.py adjustments for Cohere integration
DJANGO_VECTOR_DB = {
-   "DEFAULT_EMBEDDING_CLASS": "vectordb.embedding_functions.SentenceTransformerEncoder",
+   "DEFAULT_EMBEDDING_CLASS": "vectordb.cohere.embed.CohereEmbeddings",
-   "DEFAULT_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
+   "DEFAULT_EMBEDDING_MODEL": "embed-multilingual-v3.0", # Or "embed-english-v3.0" for English only
    "DEFAULT_EMBEDDING_SPACE": "l2",
-   "DEFAULT_EMBEDDING_DIMENSION": 384, # Default is 384 for "all-MiniLM-L6-v2"
+   "DEFAULT_EMBEDDING_DIMENSION": 1024, # Has to match the Cohere model selected
    "DEFAULT_MAX_N_RESULTS": 10,
    "DEFAULT_MIN_SCORE": 0.0,
    "DEFAULT_MAX_BRUTEFORCE_N": 10_000,
+   "COHERE_API_KEY": os.environ.get("COHERE_API_KEY", None), # Ensure this is properly set for Cohere usage
}
```

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
If you're using the Zsh shell, please execute the following command (pay attention to the quotes):

```bash
pip install -e ".[dev]"
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
[quickstart]: docs/tutorial/quickstart.md
[sentence-transformers]: https://www.sbert.net
[hnswlib]: https://github.com/nmslib/hnswlib
[drf]: https://www.django-rest-framework.org
[django-filters]: https://pypi.org/project/django-filter/
[docs]: https://pkavumba.github.io/django-vectordb/
[pypi]: https://pypi.org/project/django-vectordb/
[pypi-version]: https://img.shields.io/pypi/v/django-vectordb.svg
[django-queries]: https://docs.djangoproject.com/en/4.2/topics/db/queries/
