from django.urls import path
from . import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("blogs/<int:pk>/", views.post_detail, name="post_detail"),
    path("blogs/create/", views.post_create, name="post_create"),
]
