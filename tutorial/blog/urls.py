from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("blogs/<int:pk>/", views.post_detail, name="post_detail"),
    path("blogs/create/", views.post_create, name="post_create"),
    path(
        "accounts/login/",
        LoginView.as_view(template_name="blog/login.html"),
        name="login",
    ),
]
