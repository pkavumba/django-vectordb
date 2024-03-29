from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from vectordb import vectordb

from .forms import PostForm
from .models import Post


def post_list(request):
    posts = Post.objects.all().order_by("-created_at")
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    related_posts = vectordb.search(post, k=5)
    related_posts = [p.content_object for p in related_posts]
    return render(
        request, "blog/post_detail.html", {"post": post, "related_posts": related_posts}
    )


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
