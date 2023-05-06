import time
import logging
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView

from vectordb import vectordb

from .models import Post

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        # lets measure the time it takes to search for related posts
        start = time.time()
        related = vectordb.search(obj, k=10)
        content_objects = [item.content_object for item in related]
        context["related_posts"] = content_objects
        context["search_time"] = f"{(1000 * related.search_time):.3f}ms"
        return context


class PostCreateView(CreateView):
    model = Post
    template_name = "blog/post_create.html"
    fields = ["title", "description"]
    success_url = reverse_lazy("post_list")
