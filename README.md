# Django VectorDB

Django-VectorDB is a powerful tool that adds vector search capabilities to your Django applications. It offers low latency, fast search results, native Django integration, and automatic syncing between your models and the vector index. Incremental updates are also supported out of the box.

## Installation

To install Django-VectorDB, simply run:

```
pip install django-vectordb
```

Next, add `vectordb` to your `INSTALLED_APPS` in your `settings.py` file:

```python
INSTALLED_APPS = [
    ...
    'vectordb',
]
```

If you want to use the Django REST Framework and Django filters, follow their respective installation instructions.

## Usage

### Importing

First, import Django-VectorDB:

```python
from vectordb import vectordb
```

Then, get the `Vector` model from `vectordb.models`:

```python
from vectordb.models import Vector
```

### Adding Text to the Model

To add text to the model, you can use `vectordb.create()` or `Vector.objects.create()`:

```python
vectordb.create(text="Hello text", object_id=3, metadata={"user_id": 1})
```

Or:

```python
Vector.objects.create(text="Hello text", object_id=3, metadata={"user_id": 1})
```

The `object_id` must be unique, or an error will occur. `metadata` can be any valid JSON.

### Adding Objects

To add objects, you need to provide the text or implement a `get_text` method in your model. You can also define how to serialize the model. If not defined, the Django serializer will be used.

You can use `vectordb.create()` or `Vector.objects.create()`:

```python
vectordb.create(sample_object)
```

Or:

```python
Vector.objects.create(sample_object)
```

This will call the `get_text()` method of the object to get the text and attempt to call the `serialize()` method to get the metadata. If the `serialize()` method is not implemented, the Django serializer will be used.

### Searching

To search, simply call `vectordb.search()` or `Vector.objects.search()`:

```python
vectordb.search("Some text", k=10)
```

Or:

```python
Vector.objects.search("Some text", k=10)
```

You can also search using a sample object:

```python
Vector.objects.search(sample_object, k=10)
```

If `k` is not provided, the default value is 10.

### Filtering

You can filter on text or metadata using Django filtering:

```python
vectordb.filter(text__icontains="value", metadata__user_id=3)
```

Refer to the Django documentation on querying the JSONField for more information on filtering.

### Auto Sync

To enable auto sync, import the following signals and register them with your models:

```python
from vectordb.sync_signals import update_index, delete_index
```

These signals will sync the vectors when you create and delete instances. Note that signals are not called in bulk create, so you will need to sync manually when using those methods.

Ensure that your models implement the `get_text()` and/or `serialize()` methods for proper syncing.

---

By following this guide, you can easily integrate Django-VectorDB into your Django applications and leverage its powerful vector search capabilities.
