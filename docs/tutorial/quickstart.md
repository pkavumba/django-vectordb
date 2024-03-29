# Quickstart

We're going to create a blogging site then add vector search to it through `django-vectordb`.

---

## Project setup

Create a new Django project named `tutorial`, then start a new app called `blog`.

```bash
# Create a virtual environment to isolate our package dependencies locally
python3 -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`

# Install Django and Django VectorDB into the virtual environment
pip install django
pip install django-vectordb[standard] # include optional dependencies

# Set up a new project with a single application
django-admin startproject tutorial
cd tutorial
django-admin startapp blog
```

The project layout should look like:

```bash
    tutorial
    ├── blog
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models.py
    │   ├── tests.py
    │   └── views.py
    ├── manage.py
    └── tutorial
        ├── __init__.py
        ├── asgi.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py
```

Now sync your database for the first time:

```bash
python manage.py makemigrations # create migrations for blog
python manage.py migrate
```

We'll also create an initial user named `admin` with a password. We'll authenticate as that user later in our example.

```bash
    python manage.py createsuperuser --username admin --email admin@example.com
```

Now lets add `blog` app and `vectordb` to the `INSTALLED_APPS` in `tutorial/settings.py`

```python hl_lines="9 10" title="tutorial/settings.py"
# settings.py
INSTALLED_APPS = [
'django.contrib.admin',
'django.contrib.auth',
'django.contrib.contenttypes',
'django.contrib.sessions',
'django.contrib.messages',
'django.contrib.staticfiles',
"blog", # add blog to here
"vectordb", # add vectordb to here. The order is not important though
]
```

Next, let's add a `POST` model to our blog app by modifying `blog/models.py`, which will enable us to save our posts. Additionally, we will include the `get_vectordb_text` method to specify the text we want to search by in `vectordb`. We will also implement the `get_vectordb_metadata` method to incorporate specific fields we wish to filter by. If we don't create our custom `get_vectordb_metadata`, `vectordb` will serialize all the fields into metadata, which could be suboptimal as we might not be interested in some of the fields added. Therefore, it is **recommended** to implement our own `get_vectordb_metadata` that contains only the fields we want to filter by. These methods will allow `vectordb` to perform additional functions for us.

```python linenums="1" hl_lines="14-27" title="blog/models.py"
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
            # so we can filter by user id
            "user_id": self.user.id,
            # so we can filter by username
            "username": self.user.username,
            # so we can filter by created_at_year
            "created_at_year": self.created_at.year,
            # so we can filter by created_at_month
            "created_at_month": self.created_at.month,
        }

    def __str__(self):
        return self.title
```

Our model has three fields, the `title`, `description`, `created_at`, and a `user` foreign key. In the metadata we include the `user_id`, `username`, `created_at_year`, and `created_at_month`. We will use these fields to filter our results later.

Now lets make migrations and make tables for the `blog` app and the `vectordb` app.

```bash
python manage.py makemigrations
python manage.py migrate
```

Run the development server now

```bash
./manage.py runserver
```

---

## Adding Sample Blogs

Lets add the Post model to the admins panel. Edit the `blog/admin.py`

```python title="blog/admin.py"
# blog/admin.py
from django.contrib import admin
from .models import Post

admin.site.register(Post)
```

Now we can visit [http://127.0.0.1:8000/admin/blog/post/][admin-post] and add a few Posts. Go ahead and add something

---

## Configuring Vector Search

First, let's synchronize all posts with the vector database. To do this, simply run the following command:

```bash
python manage.py vectordb_sync <app_name> <model_name>
```

For this example we run:

```bash
python manage.py vectordb_sync blog Post
```

Lastly, let's make sure that the Post model remains synchronized with the vector database, so that any changes, such as creating, deleting, or updating posts, are automatically registered by `vectordb`. To do this, we'll create a `signals.py` file in the blog directory and input the following code:

```python linenums="1" title="blog/signals.py"
from vectordb.shortcuts import autosync_model_to_vectordb

from .models import Post

autosync_model_to_vectordb(Post)
```

The above code is equivalent to doing the following manually:

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

Then import the signals in your `apps.py`

```python linenums="1" title="blog/apps.py"
# blog/apps.py
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    # add ready method if not defined
    def ready(self):
        # import signals
        import blog.signals
```

Now we can run the development server again

```bash
./manage.py shell
```

```python
from blog.models import Post
from django.contrib.auth import get_user_model

User = get_user_model()

user = User.objects.first()

post = Post(title="A Culinary Journey", description="A journey through France", user=user)
post.save()
```

Now run the app

```bash
./manage.py runserver
```

Now, when you visit the Django Vector Database Admin Panel at [http://127.0.0.1:8000/admin/vectordb/vector/][admin-vectordb], you'll notice that the new post has been automatically added to the vector database. Similarly, if you try to delete a post, it will be automatically removed from the vector database as well. All these features come built-in with `vectordb`, ensuring a seamless and efficient experience.

---

## Fast Vector Search

To perform a search, simply invoke the `vectordb.search()` method:

```python
from vectordb import vectordb
results = vectordb.search("A Culinary Journey", k=10) # k represents the maximum number of results desired.

# get the search time in seconds
print(results.search_time) # only available if search is the last method called
```

Note that the search method returns a QuerySet with results ordered by the best match. The QuerySet will also have the search_time in seconds which only available when search is the last method called on the QuerySet. Each result item will contain the following fields: `id`, `content_object`, `object_id`, `content_type`, `text`, `embedding`, an annotated `distance`, and a `vector` property that returns the `np.ndarray` representation of the embedding field, which is in `bytes`. As the search provides a `QuerySet`, you can selectively display the fields you want like this:

```python
from vectordb import vectordb
results = vectordb.search("A Culinary Journey", k=10).only('text', 'content_object')
```

If `k` is not specified, the default value is 10.

Search doesn't only work for `text` you can also search for model instances:

```python
post1 = Post.objects.get(id=1)
# Limit the search scope to a user with an id of 1
results = vectordb.search(post1, k=10)
```

This is also a way to get related posts to `post1`. Thus, you can use `vectordb` for recommendations as well.

Note: Seaching by model instances will automatically scope the results to instances of that type. For example, if you search by `post1` you will only get results that are instances of `Post`.

---

## Filtering

You can apply filters on `text` or `metadata` using the full capabilities of Django QuerySet filtering:

```python
# Limit the search scope to a user with an id of 1
results = vectordb.filter(metadata__user_id=1).search("A Culinary Journey", k=10)

# Scope the results to text which contains France, belonging to user with id 1 and created in 2023
vectordb.filter(text__icontains="France", metadata__user_id=1, metadata__create_at_year=2023).search("A Culinary Journey", k=10)
```

We can also use model instances instead of text:

```python
post1 = Post.objects.get(id=1)
# Limit the search scope to a user with an id of 1
results = vectordb.filter(metadata__user_id=1).search(post1, k=10)

# Scope the results to text which contains France, belonging to user with id 1 and created in 2023
vectordb.filter(text__icontains="France", metadata__user_id=1, metadata__create_at_year=2023).search(post1, k=10)
```

For more information on filtering, refer to the [Django documentation][django-queries] on querying the `JSONField`.

---

## Manually Adding Items to the Vector Database

VectorDB also provides a way to manually add items to it. This is useful if you want to add items to the database that are not in the database yet.

VectorDB provides two utility methods for adding items to the database: `vectordb.add_instance` or `vectordb.add_text`. Note that for adding the instance, you need to provide the `get_vectordb_text` and an optional `get_vectordb_metadata` methods.

### 1. Adding Model Instances

```python
post1 = models.create(title="post1", description="post1 description", user=user1) # provide valid user

# add to vector database
vectordb.add_instance(post1)
```

### 2. Adding Text to the Model

To add text to the database, you can use `vectordb.add_text()`:

```python
vectordb.add_text(text="Hello text", id=3, metadata={"user_id": 1})
```

The `text` and `id` are required. Additionally, the `id` must be unique, or an error will occur. `metadata` can be `None` or any valid JSON.

## Settings

You can customize `vectordb` by providing your settings in the `settings.py` file of your project. The following settings are available:

```python title="settings.py"
# settings.py
DJANGO_VECTOR_DB = {
    "DEFAULT_EMBEDDING_CLASS": ..., # Default: "vectordb.embedding_functions.SentenceTransformerEncoder",
    "DEFAULT_EMBEDDING_MODEL": ..., # Default: "all-MiniLM-L6-v2",
    # Can be "cosine" or "l2"
    "DEFAULT_EMBEDDING_SPACE": ..., # Default "l2"
    "DEFAULT_EMBEDDING_DIMENSION": ..., # Default is 384 for "all-MiniLM-L6-v2"
    "DEFAULT_MAX_N_RESULTS": 10, # Number of results to return from search maximum is default is 10
    "DEFAULT_MIN_SCORE": 0.0, # Minimum score (distance) to return from search default is 0.0
    "DEFAULT_MAX_BRUTEFORCE_N": 10_000, # Maximum number of items to search using brute force default is 10_000. If the number of items is greater than this number, the search will be done using the HNSW index.
}
```

## Summary

Great! That was a quickstart to `django-vectordb`. We've created a blogging site and added extremely fast vector search to it. If you want to get a more in depth understanding of `vectordb` head on over to [the tutorial][tutorial].

[admin-post]: http://127.0.0.1:8000/admin/blog/post/
[admin-vectordb]: http://127.0.0.1:8000/admin/vectordb/vector/
[django-queries]: https://docs.djangoproject.com/en/4.2/topics/db/queries/
[tutorial]: 1-project-setup.md
