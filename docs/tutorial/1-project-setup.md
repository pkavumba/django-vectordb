# Tutorial 1: Project Setup

We're going to create a blogging site then add vector search to it through `django-vectordb`. We will

## Project setup

Create a new Django project named `tutorial`, then start a new app called `blog`.

```bash
    # Create a virtual environment to isolate our package dependencies locally
    python3 -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`

    # Install Django and VectorDB into the virtual environment
    pip install django
    pip install django-vectordb[standard] # include optional dependencies

    # Set up a new project with a single application
    django-admin startproject tutorial
    cd tutorial
    django-admin startapp blog
    cd ..
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

Now lets add blog to the `INSTALLED_APPS` in `tutorial/settings.py`

```python
    # settings.py
    INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "blog", # add blog to here
    ]
```

Next lets add a `POST` model to blog app `blog/models.py` for saving our posts

```python
    # blog/models.py
    from django.db import models
    from django.contrib.auth import get_user_model

    User = get_user_model()


    class Post(models.Model):
        title = models.CharField(max_length=100)
        description = models.TextField()
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return self.title
```

Our model has three fields, the `title`, `description`, `created_at`, and a `user` foreign key.

Now sync your database for the first time:

```bash
    python manage.py makemigrations # create migrations for blog
    python manage.py migrate
```

We'll also create an initial user named `admin` with a password. We'll authenticate as that user later in our example.

```bash
    python manage.py createsuperuser --username admin --email admin@example.com
```

Once you've set up a database and the initial user is created and ready to go.

Run the development server now

```bash
    ./manage.py runserver
```

---

## Adding Sample Blogs

Lets add the Post model to the admins panel. Edit the `blog/admin.py`

```python
    # blog/admin.py
    from django.contrib import admin
    from .models import Post

    admin.site.register(Post)
```

Now we can visit `http://127.0.0.1:8000/admin/blog/post/` and add a few Posts. Go ahead and add something

## Forms

In the last section we used the admin panel to add some post. Now lets add a form for post to the blogs.

Create a new file in blog directory called `forms.py`

```python
    # blog/forms.py
    from django import forms
    from .models import Post


    class PostForm(forms.ModelForm):
        class Meta:
            model = Post
            fields = ["title", "description"]
```

## Views

Lets add some views for viewing our blog posts. We will keep things simple and use function based views.

First create a directory called `templates` withing the blog app. Inside the `templates` directory create another folder called `blog`.

Lets add a basic `base.html`

```html
<!--blog/templates/blog/base.html-->
{% load static %}
<!DOCTYPE html>
<html lang="en" dir="ltr">
  <head>
    <meta charset="utf-8" />
    <title>Django Vector Database</title>
  </head>
  <body>
    <div class="container">{% block content %} {% endblock %}</div>
  </body>
</html>
```

Now lets create the list, detail, create view.

```python
    from django.shortcuts import render

    from django.contrib.auth.decorators import login_required
    from django.shortcuts import render, redirect, get_object_or_404

    from .models import Post
    from .forms import PostForm


    def post_list(request):
        posts = Post.objects.all().order_by("-created_at")
        return render(request, "blog/post_list.html", {"posts": posts})


    def post_detail(request, pk):
        post = get_object_or_404(Post, pk=pk)
        return render(request, "blog/post_detail.html", {"post": post})


    @login_required
    def post_create(request):
        if request.method == "POST":
            form = PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                return redirect("post_list")
        else:
            form = PostForm()
        return render(request, "blog/post_create.html", {"form": form})
```

And finally, lets add the templates for these views.

We will begin with a template that displays a list of blog posts with their titles as clickable links. The template extends the "blog/base.html" template. In case there are no posts, it displays the message "No posts available." At the end, we add a link to create a new blog post using the "post_create" URL pattern.

```html
<!-- blog/templates/blog/post_list.html -->
{% extends "blog/base.html" %} {% block content %}
<h1>Blog Posts</h1>
<ul>
  {% for post in posts %}
  <li>
    <a href="{% url 'post_detail' post.pk %}">{{ post.title }}</a>
  </li>
  {% empty %}
  <li>No posts available.</li>
  {% endfor %}
</ul>
<a href="{% url 'post_create' %}">Add New Post</a>
{% endblock %}
```

Next we add the template "post_detail.html" responsible for displaying the details of a single blog post.
The template also includes a link to navigate back to the list of all blog posts.

```html
<!-- blog/templates/blog/post_detail.html -->
{% extends "blog/base.html" %} {% block content %}
<h1>{{ post.title }}</h1>
<p>{{ post.description }}</p>
<a href="{% url 'post_list' %}">Back to Posts List</a>
{% endblock %}
```

```html
<!-- blog/templates/blog/post_create.html -->
{% extends "blog/base.html" %} {% block content %}
<h1>Create New Post</h1>
<form method="post">
  {% csrf_token %} {{ form.as_p }}
  <button type="submit">Save Post</button>
</form>
<a href="{% url 'post_list' %}">Back to Posts List</a>
{% endblock %}
```

This completes boilerplate we need in order to test django vector database.

## Summary

In this tutorial we create a basic project to work with Django Vector Database. We have create all the views and forms we need to create and view posts. Next lets integrated django vector database
